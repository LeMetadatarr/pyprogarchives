"""Offline tests for the fetch/search layer, replaying recorded fixtures.

Fixtures are real HTTP response bodies recorded once via the Wayback
Machine (see the file docstrings below for source URLs), replayed here
through a fake :class:`~pyprogarchives._transport.Transport` so no test
touches the network.
"""
import os

import pytest

import pyprogarchives as pa
from pyprogarchives._transport import Transport
from pyprogarchives.artists import ArtistNotFound

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


class FakeTransport(Transport):
    """Replays recorded fixtures keyed by (path, letter-or-id).

    Subclasses the real :class:`Transport` (rather than duck-typing it) so it
    also satisfies :class:`~pyprogarchives.artists.ProgArchives`'s
    ``isinstance(transport, Transport)`` check.
    """

    def __init__(self, by_letter=None, by_id=None):
        self.by_letter = by_letter or {}
        self.by_id = by_id or {}
        self.calls = []

    def get_html(self, path, **params):
        self.calls.append((path, params))
        if path == "/bands-alpha.asp":
            letter = params["letter"]
            if letter not in self.by_letter:
                return "<html><body>no bands</body></html>"
            return _read(self.by_letter[letter])
        if path == "/artist.asp":
            aid = params["id"]
            if aid not in self.by_id:
                return "<html><body>not found</body></html>"
            return _read(self.by_id[aid])
        raise AssertionError(f"unexpected path {path!r}")


# listing.html ("a" excerpt) and listing_digit.html ("0", recorded 2026-08-03
# via https://web.archive.org/web/2026*/https://www.progarchives.com/bands-alpha.asp?letter=0)
# both carry real digit-first bands such as 10CC, 1974, 12TWELVE.
LISTINGS = {"a": "listing.html", "0": "listing_digit.html"}
ARTISTS = {1: "artist.html"}


def test_get_artists_by_letter():
    t = FakeTransport(by_letter=LISTINGS)
    artists = pa.get_artists_by_letter("a", transport=t)
    assert len(artists) == 3
    assert t.calls == [("/bands-alpha.asp", {"letter": "a"})]


def test_get_artists_by_letter_rejects_bad_letter():
    t = FakeTransport(by_letter=LISTINGS)
    with pytest.raises(ValueError):
        pa.get_artists_by_letter("!", transport=t)


def test_iter_artists_restricted_to_letters():
    t = FakeTransport(by_letter=LISTINGS)
    names = [a.name for a in pa.iter_artists("a0", transport=t)]
    assert "A BAND, THE" in names
    assert "10CC" in names
    assert len(t.calls) == 2


def test_get_all_artists_is_eager_list():
    t = FakeTransport(by_letter=LISTINGS)
    artists = pa.get_all_artists("a", transport=t)
    assert isinstance(artists, list) and len(artists) == 3


def test_fetch_artist_happy_path():
    t = FakeTransport(by_id=ARTISTS)
    detail = pa.fetch_artist(1, transport=t)
    assert detail.name == "GENESIS"
    assert len(detail.albums) == 3


def test_fetch_artist_not_found():
    t = FakeTransport(by_id=ARTISTS)
    with pytest.raises(ArtistNotFound):
        pa.fetch_artist(999, transport=t)


def test_search_artists_matches_plain_name():
    t = FakeTransport(by_letter=LISTINGS)
    results = pa.search_artists("a band", transport=t)
    assert results and results[0].name == "A BAND, THE"


def test_search_artists_empty_query():
    t = FakeTransport(by_letter=LISTINGS)
    assert pa.search_artists("   ", transport=t) == []


def test_search_artists_respects_limit():
    t = FakeTransport(by_letter=LISTINGS)
    results = pa.search_artists("a", limit=1, transport=t)
    assert len(results) == 1


def test_search_artists_digit_first_band_regression():
    """Regression for a real bug: progarchives files every digit-first band
    (10CC, 1974, 12TWELVE, ...) under letter "0", not under its literal
    leading digit. search_artists("10cc") used to return [] because only the
    literal character "0" was recognised as a digit-initial; any other digit
    fell through and the "0" listing was never fetched.
    """
    t = FakeTransport(by_letter=LISTINGS)
    results = pa.search_artists("10cc", transport=t)
    assert [a.name for a in results] == ["10CC"]
    assert ("/bands-alpha.asp", {"letter": "0"}) in t.calls


def test_search_artists_multi_digit_tokens_all_map_to_zero():
    t = FakeTransport(by_letter=LISTINGS)
    results = pa.search_artists("1974", transport=t)
    assert [a.name for a in results] == ["1974"]


def test_progarchives_client_uses_configured_transport():
    t = FakeTransport(by_letter=LISTINGS, by_id=ARTISTS)
    client = pa.ProgArchives(transport=t)
    assert len(client.get_artists_by_letter("a")) == 3
    assert client.fetch_artist(1).name == "GENESIS"
    assert client.search_artists("10cc")[0].name == "10CC"
