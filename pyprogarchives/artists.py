"""Band/artist lookup functions backed by progarchives.com.

The site is organised as an A–Z band index plus per-band pages carrying the
biography and rated discography. There is no JSON API, so this scrapes the
HTML (see :mod:`pyprogarchives.parse`).
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional

from pyprogarchives._transport import Transport, default_transport
from pyprogarchives.parse import parse_artist, parse_listing
from pyprogarchives.types import Artist, ArtistDetail

# A–Z plus "0" (bands whose name starts with a digit/symbol).
LETTERS = "abcdefghijklmnopqrstuvwxyz0"


class ArtistNotFound(Exception):
    """Raised by :func:`fetch_artist` when a page has no band on it."""


def _t(transport: Optional[Transport]) -> Transport:
    return transport or default_transport()


def get_artists_by_letter(letter: str, *, transport: Optional[Transport] = None) -> List[Artist]:
    """Return every band whose name starts with *letter* (``a``–``z`` or ``0``).

    Example::

        import pyprogarchives as pa
        bands = pa.get_artists_by_letter("a")
        print(len(bands), "bands under A")
    """
    letter = letter.strip().lower()[:1]
    if letter not in LETTERS:
        raise ValueError(f"letter must be a-z or '0', got {letter!r}")
    return parse_listing(_t(transport).get_html("/bands-alpha.asp", letter=letter))


def iter_artists(letters: Optional[str] = None, *,
                 transport: Optional[Transport] = None) -> Iterator[Artist]:
    """Lazily iterate the full A–Z band index.

    Args:
        letters: Restrict to these initials (e.g. ``"abc"``). Defaults to all.

    Example::

        import itertools, pyprogarchives as pa
        first = list(itertools.islice(pa.iter_artists(), 50))
    """
    for letter in (letters or LETTERS):
        yield from get_artists_by_letter(letter, transport=transport)


def get_all_artists(letters: Optional[str] = None, *,
                    transport: Optional[Transport] = None) -> List[Artist]:
    """Eagerly collect the full band index. Prefer :func:`iter_artists`."""
    return list(iter_artists(letters, transport=transport))


def fetch_artist(artist_id: int, *, transport: Optional[Transport] = None) -> ArtistDetail:
    """Fetch a band page (genre, country, biography, rated discography).

    Args:
        artist_id: progarchives band id (the ``id`` in ``artist.asp?id=``).

    Raises:
        ArtistNotFound: when the page carries no band name.

    Example::

        import pyprogarchives as pa
        genesis = pa.fetch_artist(1)
        print(genesis.name, genesis.genre, genesis.country)
        print(len(genesis.albums), "albums")
    """
    detail = parse_artist(_t(transport).get_html("/artist.asp", id=artist_id), int(artist_id))
    if not detail.name:
        raise ArtistNotFound(f"no band found for id={artist_id}")
    return detail


def search_artists(query: str, limit: Optional[int] = None, *,
                   transport: Optional[Transport] = None) -> List[Artist]:
    """Search the band index for *query* by name (client-side).

    progarchives has no search API, so this fetches the listing for the
    query's initial and keeps bands whose name contains every query token,
    ranking exact and prefix matches first.

    Example::

        import pyprogarchives as pa
        pa.search_artists("genesis")[0].display_name      # 'GENESIS'
        pa.search_artists("king crimson", limit=1)
    """
    tokens = [t for t in query.lower().split() if t]
    if not tokens:
        return []
    # progarchives files every digit-first band under letter "0" (e.g. "10CC",
    # "1974"), not under its literal leading digit.
    initials = {("0" if t[0].isdigit() else t[0]) for t in tokens if t[0].isdigit() or t[0] in LETTERS}
    seen: Dict[int, Artist] = {}
    for letter in sorted(initials):
        for a in get_artists_by_letter(letter, transport=transport):
            seen.setdefault(a.artist_id, a)

    phrase = query.lower().strip()

    def matches(a: Artist) -> bool:
        hay = f"{a.name} {a.display_name}".lower()
        return all(t in hay for t in tokens)

    def score(a: Artist) -> tuple:
        name = a.display_name.lower()
        if name == phrase:
            tier = 0
        elif name.startswith(phrase) or phrase in name:
            tier = 1
        else:
            tier = 2
        return (tier, len(a.name))

    results = sorted((a for a in seen.values() if matches(a)), key=score)
    return results[:limit] if limit else results


class ProgArchives:
    """High-level client with a configurable transport.

    Mirrors the module-level functions, but every call uses the transport you
    configure here — no environment variables required.

    Args:
        transport:            ``"requests"`` / ``"curl_cffi"`` / ``"wayback"`` /
                              ``"flaresolverr"``, or a ready :class:`Transport`.
        flaresolverr_url:     FlareSolverr base URL (e.g.
                              ``"http://192.168.1.116:8191"``); setting it
                              selects the ``flaresolverr`` transport.
        flaresolverr_timeout_ms: per-request solve budget.
        wayback:              force the Internet Archive (same as
                              ``transport="wayback"``).
        wayback_fallback:     fall back to the archive on any live failure.

    Example::

        import pyprogarchives as pa

        # Solve Cloudflare live via a FlareSolverr box:
        pa_client = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191")
        genesis = pa_client.fetch_artist(1)

        # Or force the Wayback Machine explicitly:
        archived = pa.ProgArchives(wayback=True)
        bands = archived.get_artists_by_letter("a")
    """

    def __init__(self, transport=None, *, flaresolverr_url: Optional[str] = None,
                 flaresolverr_timeout_ms: Optional[int] = None,
                 wayback: bool = False,
                 wayback_fallback: Optional[bool] = None) -> None:
        if isinstance(transport, Transport):
            self.transport = transport
        else:
            mode = "wayback" if wayback else transport
            self.transport = Transport(
                mode=mode,
                flaresolverr_url=flaresolverr_url,
                flaresolverr_timeout_ms=flaresolverr_timeout_ms,
                wayback_fallback=wayback_fallback,
            )

    def get_artists_by_letter(self, letter: str) -> List[Artist]:
        return get_artists_by_letter(letter, transport=self.transport)

    def iter_artists(self, letters: Optional[str] = None) -> Iterator[Artist]:
        return iter_artists(letters, transport=self.transport)

    def get_all_artists(self, letters: Optional[str] = None) -> List[Artist]:
        return get_all_artists(letters, transport=self.transport)

    def fetch_artist(self, artist_id: int) -> ArtistDetail:
        return fetch_artist(artist_id, transport=self.transport)

    def search_artists(self, query: str, limit: Optional[int] = None) -> List[Artist]:
        return search_artists(query, limit, transport=self.transport)
