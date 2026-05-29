"""HTTP transport for pyprogarchives.

progarchives.com sits behind a Cloudflare challenge. Three transport modes are
available via the ``PYPROGARCHIVES_TRANSPORT`` environment variable:

- *(unset)* / ``curl_cffi`` — live fetch with ``curl_cffi`` Chrome TLS
  impersonation when available (install the ``stealth`` extra), else plain
  ``requests``. Clears the bot check from most networks.
- ``requests`` — live fetch with plain ``requests`` (no impersonation).
- ``wayback`` — do not touch the live site at all; fetch the most recent
  snapshot from the Internet Archive (Wayback Machine). Useful from networks
  where Cloudflare serves an unsolvable JS challenge. Archived HTML can be
  weeks/months stale.

Independently, set ``PYPROGARCHIVES_WAYBACK_FALLBACK=1`` to transparently fall
back to the Wayback Machine whenever a live fetch fails (non-2xx or a detected
Cloudflare challenge). Off by default, so behaviour is predictable.

The parsing layer (``parse.py``) is independent of how the HTML was fetched.
"""
from __future__ import annotations

import os
import re
from typing import Any, Optional

BASE = "https://www.progarchives.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_WAYBACK_AVAILABLE_API = "http://archive.org/wayback/available"
_session: Any = None


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def default_session() -> Any:
    """Return the process-global live HTTP session, creating it on first use."""
    global _session
    if _session is None:
        forced = os.environ.get("PYPROGARCHIVES_TRANSPORT", "").strip().lower()
        if forced not in {"requests", "wayback"}:
            try:
                from curl_cffi import requests as cffi  # type: ignore[import]
                s = cffi.Session(impersonate="chrome")
                s.headers.update(_HEADERS)
                _session = s
                return _session
            except ImportError:
                pass
        import requests
        _session = requests.Session()
        _session.headers.update(_HEADERS)
    return _session


def _is_challenge(text: str) -> bool:
    """Heuristically detect a Cloudflare interstitial in a 2xx body."""
    head = text[:1500].lower()
    return "just a moment" in head or "cf-mitigated" in head or "challenge-platform" in head


def wayback_raw_url(snapshot_url: str) -> str:
    """Turn a Wayback snapshot URL into its raw (unrewritten) ``id_`` form.

    ``.../web/<timestamp>/<original>`` → ``.../web/<timestamp>id_/<original>``,
    which returns the original captured bytes with no Wayback toolbar or link
    rewriting — i.e. the page exactly as progarchives served it.
    """
    return re.sub(r"(/web/\d+)/", r"\1id_/", snapshot_url, count=1)


def _url_variants(url: str):
    """Yield URL forms to try against the Wayback availability API.

    The archive may have indexed a capture under ``http://`` even when the live
    site is ``https://`` (and vice-versa), and the API also matches a
    scheme-less form. Try the original first, then those fallbacks.
    """
    seen = set()
    bare = re.sub(r"^https?://", "", url)
    for candidate in (url, "http://" + bare, "https://" + bare, bare):
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def wayback_html(url: str, *, timeout: float = 30.0) -> Optional[str]:
    """Fetch the latest Wayback Machine snapshot of *url* as raw HTML.

    Returns ``None`` when the archive has no usable capture. Uses plain
    ``requests`` against archive.org (which is not Cloudflare-gated). Tries
    a few URL forms because the archive's index is scheme-sensitive.
    """
    import requests
    snap = None
    for candidate in _url_variants(url):
        try:
            meta = requests.get(_WAYBACK_AVAILABLE_API, params={"url": candidate},
                                headers=_HEADERS, timeout=timeout).json()
        except Exception:
            continue
        snap = (meta.get("archived_snapshots", {}) or {}).get("closest")
        if snap and snap.get("available") and snap.get("url"):
            break
        snap = None
    if not snap:
        return None
    try:
        r = requests.get(wayback_raw_url(snap["url"]), headers=_HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception:
        return None
    return r.text


def get_html(path: str, **params: Any) -> str:
    """GET ``{BASE}{path}`` and return the response text.

    Honours ``PYPROGARCHIVES_TRANSPORT`` (``requests`` / ``curl_cffi`` /
    ``wayback``) and ``PYPROGARCHIVES_WAYBACK_FALLBACK``. See the module
    docstring.

    Raises:
        the underlying HTTP error on a live non-2xx response (unless a Wayback
        fallback succeeds), or ``RuntimeError`` if a ``wayback``-mode lookup
        finds no snapshot.
    """
    url = path if path.startswith("http") else f"{BASE}{path}"
    # Wayback needs the full query string baked into the URL it looks up.
    if params:
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(params)}"

    mode = os.environ.get("PYPROGARCHIVES_TRANSPORT", "").strip().lower()
    if mode == "wayback":
        html = wayback_html(url)
        if html is None:
            raise RuntimeError(f"no Wayback Machine snapshot available for {url}")
        return html

    try:
        s = default_session()
        r = s.get(url, timeout=30)
        r.raise_for_status()
        if _is_challenge(r.text):
            raise RuntimeError("Cloudflare challenge served")
        return r.text
    except Exception:
        if _truthy(os.environ.get("PYPROGARCHIVES_WAYBACK_FALLBACK")):
            html = wayback_html(url)
            if html is not None:
                return html
        raise
