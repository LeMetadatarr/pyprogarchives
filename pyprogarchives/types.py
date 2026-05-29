"""Typed dataclass models for pyprogarchives.

Shared interface on every model:

- ``site_id`` — the canonical progarchives identifier;
- ``url`` — the canonical web page;
- ``to_dict()`` — a JSON-serialisable plain ``dict``;
- ``to_external_ids_dict()`` — keys for metadatarr's ``ExternalIds(extra=...)``.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

BASE = "https://www.progarchives.com"


def _display_name(listed: str) -> str:
    """``"BAND, THE"`` → ``"THE BAND"``; otherwise unchanged."""
    if "," in listed:
        head, tail = listed.split(",", 1)
        return f"{tail.strip()} {head.strip()}".strip()
    return listed


@dataclass
class Artist:
    """A band/artist as it appears in the A–Z listing.

    Example::

        import pyprogarchives as pa
        for a in pa.get_artists_by_letter("A")[:3]:
            print(a.artist_id, a.display_name, a.genre, a.country)
    """

    artist_id: int
    name: str                      # as listed, e.g. "BAND, THE"
    genre: Optional[str] = None    # progarchives sub-genre, e.g. "Symphonic Prog"
    country: Optional[str] = None

    @property
    def site_id(self) -> str:
        return str(self.artist_id)

    @property
    def display_name(self) -> str:
        return _display_name(self.name)

    @property
    def url(self) -> str:
        return f"{BASE}/artist.asp?id={self.artist_id}"

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["display_name"] = self.display_name
        d["url"] = self.url
        return d

    def to_external_ids_dict(self) -> Dict[str, str]:
        return {"progarchives_artist": self.site_id, "progarchives_url": self.url}


@dataclass
class Album:
    """A release from a band's discography, with progarchives ratings.

    Example::

        detail = pa.fetch_artist(1)         # GENESIS
        a = detail.albums[0]
        print(a.title, a.year, a.avg_rating, f"({a.num_ratings} ratings)")
    """

    album_id: int
    title: str
    year: Optional[int] = None
    avg_rating: Optional[float] = None     # PA average rating, 0–5
    num_ratings: Optional[int] = None
    cover: Optional[str] = None
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None

    @property
    def site_id(self) -> str:
        return str(self.album_id)

    @property
    def url(self) -> str:
        return f"{BASE}/album.asp?id={self.album_id}"

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["url"] = self.url
        return d

    def to_external_ids_dict(self) -> Dict[str, str]:
        return {"progarchives_album": self.site_id, "progarchives_url": self.url}


@dataclass
class ArtistDetail:
    """Full band page: genre, country, biography and discography.

    Obtain via :func:`pyprogarchives.fetch_artist`.

    Example::

        detail = pa.fetch_artist(1)
        print(detail.name, detail.genre, detail.country)
        print(detail.bio[:120])
        for a in detail.albums:
            print(a.year, a.avg_rating, a.title)
    """

    artist_id: int
    name: str                      # display form, e.g. "GENESIS"
    genre: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    albums: List[Album] = field(default_factory=list)

    @property
    def site_id(self) -> str:
        return str(self.artist_id)

    @property
    def display_name(self) -> str:
        return _display_name(self.name)

    @property
    def url(self) -> str:
        return f"{BASE}/artist.asp?id={self.artist_id}"

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["url"] = self.url
        return d

    def to_external_ids_dict(self) -> Dict[str, str]:
        return {"progarchives_artist": self.site_id, "progarchives_url": self.url}
