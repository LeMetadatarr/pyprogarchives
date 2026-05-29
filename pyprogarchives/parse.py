"""Pure HTML → model parsers for progarchives.com.

These functions take raw HTML strings and return typed models, with no
network access — so they can be unit-tested against saved fixtures. The
fetching layer (:mod:`pyprogarchives.artists`) wires them to HTTP.

Verified against the live markup:

- **Listing** (``bands-alpha.asp``): a ``div.grid-container`` of
  ``div.grid-item`` cells in repeating triples — (artist link, genre, country).
- **Artist page** (``artist.asp?id=``): ``h1`` name, ``h2`` ``"Genre • Country"``,
  ``div#artist-biography`` bio, and a ``table.artist-discography-table`` whose
  ``td.artist-discography-td`` cells each hold a cover, an album link, a rating
  star-box script (precise average), a ratings count and a release year.
"""
from __future__ import annotations

import re
from typing import List, Optional

from bs4 import BeautifulSoup

from pyprogarchives.types import Artist, Album, ArtistDetail

_ID_RE = re.compile(r"id=(\d+)")
_STARBOX_RE = re.compile(
    r"generateReadOnlyStarbox\('readOnlyRating_\d+_(\d+)',\s*([\d.]+)\)"
)


def _int(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"\d[\d,]*", text)
    return int(m.group(0).replace(",", "")) if m else None


def parse_listing(html: str) -> List[Artist]:
    """Parse a ``bands-alpha.asp`` page into :class:`Artist` objects."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_="grid-container")
    if not container:
        return []
    cells = container.find_all("div", class_="grid-item", recursive=False)
    artists: List[Artist] = []
    # cells come in repeating triples: (artist link, genre, country)
    for i in range(0, len(cells) - 2, 3):
        link = cells[i].find("a", href=_ID_RE)
        if not link:
            continue
        m = _ID_RE.search(link.get("href", ""))
        if not m:
            continue
        artists.append(Artist(
            artist_id=int(m.group(1)),
            name=link.get_text(strip=True),
            genre=cells[i + 1].get_text(strip=True) or None,
            country=cells[i + 2].get_text(strip=True) or None,
        ))
    return artists


def _parse_album_cell(td, artist_id: int, artist_name: str) -> Optional[Album]:
    anchors = td.find_all("a", href=re.compile(r"album\.asp\?id=\d+"))
    if not anchors:
        return None
    aid = _ID_RE.search(anchors[0]["href"])
    if not aid:
        return None
    title_a = next((a for a in anchors if a.get_text(strip=True)), None)
    title = title_a.get_text(strip=True) if title_a else ""
    year_span = td.find("span", style=re.compile("#777"))
    nb = td.find("span", id=re.compile("nbRatings"))
    cover = td.find("img", class_="artist-discography-cover")
    star = _STARBOX_RE.search(td.decode())
    return Album(
        album_id=int(aid.group(1)),
        title=title,
        year=_int(year_span.get_text(strip=True)) if year_span else None,
        avg_rating=round(float(star.group(2)), 2) if star else None,
        num_ratings=_int(nb.get_text(strip=True)) if nb else None,
        cover=cover.get("src") if cover else None,
        artist_id=artist_id,
        artist_name=artist_name,
    )


def parse_artist(html: str, artist_id: int) -> ArtistDetail:
    """Parse an ``artist.asp?id=`` page into an :class:`ArtistDetail`."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else ""

    genre = country = None
    h2 = soup.find("h2")
    if h2 and "•" in h2.get_text():
        genre, country = (p.strip() for p in h2.get_text().split("•", 1))

    bio = None
    bio_div = soup.find(id="artist-biography")
    if bio_div:
        # The div holds a truncated #shortBio and the full #moreBio (plus a
        # "read more" link and a "X biography" heading). Prefer the full text.
        full = bio_div.find(id="moreBio") or bio_div.find(id="shortBio")
        bio = (full or bio_div).get_text(" ", strip=True)
        prefix = f"{name} biography"
        if bio.lower().startswith(prefix.lower()):
            bio = bio[len(prefix):].strip()
        bio = re.sub(r"\s*read more\s*$", "", bio, flags=re.I).strip() or None

    albums: List[Album] = []
    for td in soup.find_all("td", class_="artist-discography-td"):
        album = _parse_album_cell(td, artist_id, name)
        if album:
            albums.append(album)

    return ArtistDetail(
        artist_id=artist_id, name=name, genre=genre, country=country,
        bio=bio, albums=albums,
    )
