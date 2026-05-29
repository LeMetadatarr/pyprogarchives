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


def test_flaresolverr_extract_ok():
    data = {"status": "ok", "solution": {"status": 200, "response": "<html>live</html>"}}
    assert t._flaresolverr_extract(data) == "<html>live</html>"


def test_flaresolverr_extract_error():
    import pytest
    with pytest.raises(RuntimeError):
        t._flaresolverr_extract({"status": "error", "message": "timeout"})


# --- Transport / client configuration (kwargs, no network) ---------------

def _clear_env(monkeypatch):
    for k in ("PYPROGARCHIVES_TRANSPORT", "PYPROGARCHIVES_FLARESOLVERR_URL",
              "PYPROGARCHIVES_WAYBACK_FALLBACK"):
        monkeypatch.delenv(k, raising=False)


def test_transport_mode_from_kwargs(monkeypatch):
    _clear_env(monkeypatch)
    assert t.Transport()._resolved_mode() == "curl_cffi"
    assert t.Transport(mode="wayback")._resolved_mode() == "wayback"
    assert t.Transport(flaresolverr_url="http://x:8191")._resolved_mode() == "flaresolverr"


def test_transport_kwarg_beats_env(monkeypatch):
    monkeypatch.setenv("PYPROGARCHIVES_TRANSPORT", "requests")
    assert t.Transport(mode="wayback")._resolved_mode() == "wayback"   # explicit wins
    assert t.Transport()._resolved_mode() == "requests"                # falls back to env


def test_transport_rejects_bad_mode():
    import pytest
    with pytest.raises(ValueError):
        t.Transport(mode="nonsense")


def test_client_kwargs(monkeypatch):
    _clear_env(monkeypatch)
    import pyprogarchives as pa
    assert pa.ProgArchives(wayback=True).transport._resolved_mode() == "wayback"
    c = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191")
    assert c.transport._resolved_mode() == "flaresolverr"
    assert c.transport._fs_url() == "http://192.168.1.116:8191"
