"""Dataset row builders produce flat, join-able rows."""
import os

from pyprogarchives import dataset
from pyprogarchives.parse import parse_artist, parse_listing

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


def test_artist_rows():
    artists = parse_listing(_read("listing.html"))
    rows = list(dataset.artist_rows(artists))
    assert len(rows) == 3
    assert set(rows[0]) == {"artist_id", "name", "display_name", "genre", "country", "url"}


def test_album_rows_carry_artist():
    detail = parse_artist(_read("artist.html"), 1)
    rows = list(dataset.album_rows(detail))
    assert len(rows) == 3
    for r in rows:
        assert r["artist_id"] == 1
        assert r["artist_name"] == "GENESIS"
        assert "avg_rating" in r and "num_ratings" in r


def test_detail_row_has_bio():
    detail = parse_artist(_read("artist.html"), 1)
    row = dataset.artist_detail_row(detail)
    assert row["n_albums"] == 3
    assert "Formed in 1967" in row["bio"]


def test_write_jsonl(tmp_path):
    artists = parse_listing(_read("listing.html"))
    path = tmp_path / "out.jsonl"
    n = dataset.write_jsonl(str(path), dataset.artist_rows(artists))
    assert n == 3
    assert path.read_text().count("\n") == 3
