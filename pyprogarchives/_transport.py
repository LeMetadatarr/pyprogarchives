"""HTTP transport for pyprogarchives.

progarchives.com sits behind a Cloudflare challenge, so the default session
uses ``curl_cffi`` with Chrome TLS impersonation when available (install the
``stealth`` extra), falling back to plain ``requests`` otherwise. Set
``PYPROGARCHIVES_TRANSPORT=requests`` to force plain requests.

> Cloudflare may still serve a JS challenge from some IPs. When that happens,
> run from a residential/unblocked network or front the client with a
> challenge-solving proxy. The parsing layer is independent of how the HTML
> was fetched — see ``parse.py``.
"""
from __future__ import annotations

import os
from typing import Any

BASE = "https://www.progarchives.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_session: Any = None


def default_session() -> Any:
    """Return the process-global HTTP session, creating it on first use."""
    global _session
    if _session is None:
        forced = os.environ.get("PYPROGARCHIVES_TRANSPORT", "").strip().lower()
        if forced != "requests":
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


def get_html(path: str, **params: Any) -> str:
    """GET ``{BASE}{path}`` and return the response text.

    Args:
        path:   Site path beginning with ``/`` (e.g. ``/bands-alpha.asp``).
        params: Query-string parameters.

    Raises:
        requests.HTTPError / curl_cffi error on a non-2xx response.
    """
    s = default_session()
    url = path if path.startswith("http") else f"{BASE}{path}"
    r = s.get(url, params=params or None, timeout=30)
    r.raise_for_status()
    return r.text
