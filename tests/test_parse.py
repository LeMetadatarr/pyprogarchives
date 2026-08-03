"""Offline parser tests against real-markup fixtures (no network)."""
import os

from pyprogarchives.parse import parse_artist, parse_listing
from pyprogarchives.types import Album, Artist, ArtistDetail

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


def test_parse_listing():
    artists = parse_listing(_read("listing.html"))
    assert len(artists) == 3
    assert all(isinstance(a, Artist) for a in artists)
    band = next(a for a in artists if a.name == "A BAND, THE")
    assert band.artist_id == 7277
    assert band.display_name == "THE A BAND"
    assert band.genre == "RIO/Avant-Prog"
    assert band.country == "United Kingdom"
    assert band.url == "https://www.progarchives.com/artist.asp?id=7277"
    assert band.to_external_ids_dict()["progarchives_artist"] == "7277"


def test_parse_artist():
    d = parse_artist(_read("artist.html"), 1)
    assert isinstance(d, ArtistDetail)
    assert d.name == "GENESIS"
    assert d.genre == "Symphonic Prog"
    assert d.country == "United Kingdom"
    assert d.bio and "Formed in 1967" in d.bio
    assert not d.bio.lower().startswith("genesis biography")
    assert d.bio.count("Formed in 1967") == 1      # no short/full duplication
    assert not d.bio.lower().endswith("read more")
    assert d.url == "https://www.progarchives.com/artist.asp?id=1"


def test_parse_artist_albums():
    d = parse_artist(_read("artist.html"), 1)
    assert len(d.albums) == 3
    assert all(isinstance(a, Album) for a in d.albums)
    first = d.albums[0]
    assert first.album_id == 6
    assert first.title == "From Genesis to Revelation"
    assert first.year == 1969
    assert first.avg_rating == 2.56
    assert first.num_ratings == 1395
    assert first.cover and first.cover.startswith("http")
    assert first.artist_id == 1 and first.artist_name == "GENESIS"
    assert first.to_external_ids_dict()["progarchives_album"] == "6"


def test_empty_listing():
    assert parse_listing("<html><body>nothing</body></html>") == []


def test_parse_listing_digit_letter():
    """The '0' listing groups every digit-first band (real page, recorded
    2026-08-03 via the Wayback Machine)."""
    artists = parse_listing(_read("listing_digit.html"))
    assert len(artists) == 70
    names = {a.name for a in artists}
    assert {"10CC", "1974", "12TWELVE", "10000 RUSSOS"} <= names
