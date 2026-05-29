"""Band/artist lookup functions backed by progarchives.com.

The site is organised as an A–Z band index plus per-band pages carrying the
biography and rated discography. There is no JSON API, so this scrapes the
HTML (see :mod:`pyprogarchives.parse`).
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional

from pyprogarchives._transport import get_html
from pyprogarchives.parse import parse_artist, parse_listing
from pyprogarchives.types import Artist, ArtistDetail

# A–Z plus "0" (bands whose name starts with a digit/symbol).
LETTERS = "abcdefghijklmnopqrstuvwxyz0"


class ArtistNotFound(Exception):
    """Raised by :func:`fetch_artist` when a page has no band on it."""


def get_artists_by_letter(letter: str) -> List[Artist]:
    """Return every band whose name starts with *letter* (``a``–``z`` or ``0``).

    Example::

        import pyprogarchives as pa
        bands = pa.get_artists_by_letter("a")
        print(len(bands), "bands under A")
    """
    letter = letter.strip().lower()[:1]
    if letter not in LETTERS:
        raise ValueError(f"letter must be a-z or '0', got {letter!r}")
    return parse_listing(get_html("/bands-alpha.asp", letter=letter))


def iter_artists(letters: Optional[str] = None) -> Iterator[Artist]:
    """Lazily iterate the full A–Z band index.

    Args:
        letters: Restrict to these initials (e.g. ``"abc"``). Defaults to all.

    Example::

        import itertools, pyprogarchives as pa
        first = list(itertools.islice(pa.iter_artists(), 50))
    """
    for letter in (letters or LETTERS):
        yield from get_artists_by_letter(letter)


def get_all_artists(letters: Optional[str] = None) -> List[Artist]:
    """Eagerly collect the full band index. Prefer :func:`iter_artists`."""
    return list(iter_artists(letters))


def fetch_artist(artist_id: int) -> ArtistDetail:
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
    detail = parse_artist(get_html("/artist.asp", id=artist_id), int(artist_id))
    if not detail.name:
        raise ArtistNotFound(f"no band found for id={artist_id}")
    return detail


def search_artists(query: str, limit: Optional[int] = None) -> List[Artist]:
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
    initials = {t[0] for t in tokens if t[0] in LETTERS}
    seen: Dict[int, Artist] = {}
    for letter in sorted(initials):
        for a in get_artists_by_letter(letter):
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
