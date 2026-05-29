"""Offline tests for the transport's Wayback helpers (no network)."""
from pyprogarchives import _transport as t


def test_wayback_raw_url_inserts_id_marker():
    snap = "http://web.archive.org/web/20250817154721/https://www.progarchives.com/artist.asp?id=1"
    raw = t.wayback_raw_url(snap)
    assert raw == (
        "http://web.archive.org/web/20250817154721id_/"
        "https://www.progarchives.com/artist.asp?id=1"
    )
    # only the timestamp boundary is touched
    assert raw.count("id_/") == 1


def test_url_variants_cover_scheme_forms():
    variants = list(t._url_variants("https://www.progarchives.com/bands-alpha.asp?letter=a"))
    assert "https://www.progarchives.com/bands-alpha.asp?letter=a" in variants
    assert "http://www.progarchives.com/bands-alpha.asp?letter=a" in variants
    assert "www.progarchives.com/bands-alpha.asp?letter=a" in variants
    assert len(variants) == len(set(variants))   # de-duplicated


def test_truthy():
    assert t._truthy("1") and t._truthy("true") and t._truthy("YES")
    assert not t._truthy("") and not t._truthy("0") and not t._truthy(None)


def test_challenge_detection():
    assert t._is_challenge("<html><head><title>Just a moment...</title>")
    assert not t._is_challenge("<html><body><div class='grid-container'>")
