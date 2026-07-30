"""HTTP transport for pyprogarchives.

progarchives.com sits behind a Cloudflare challenge. Transport is configurable
two ways — **constructor kwargs** on :class:`Transport` (or the high-level
:class:`pyprogarchives.ProgArchives` client), or **environment variables** as
fallback defaults. Explicit kwargs always win over the environment.

Modes:

- ``curl_cffi`` *(default)* — live fetch with Chrome TLS impersonation when
  available (install the ``stealth`` extra), else plain ``requests``.
- ``requests`` — live fetch with plain ``requests``.
- ``wayback`` — never touch the live site; fetch the latest Internet Archive
  (Wayback Machine) snapshot. Stale but dependency-free.
- ``flaresolverr`` — fetch through a FlareSolverr proxy (a headless browser
  that clears the Cloudflare challenge) and return **live** HTML.

Environment fallbacks: ``PYPROGARCHIVES_TRANSPORT``,
``PYPROGARCHIVES_FLARESOLVERR_URL``, ``PYPROGARCHIVES_FLARESOLVERR_TIMEOUT``
(ms), ``PYPROGARCHIVES_WAYBACK_FALLBACK``.

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
_VALID_MODES = {"requests", "curl_cffi", "wayback", "flaresolverr"}


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _build_session(prefer_curl: bool) -> Any:
    """Create a live HTTP session (curl_cffi Chrome impersonation if asked and
    available, else plain requests)."""
    if prefer_curl:
        try:
            from curl_cffi import requests as cffi  # type: ignore[import]
            s = cffi.Session(impersonate="chrome")
            s.headers.update(_HEADERS)
            return s
        except ImportError:
            pass
    import requests
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


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


def _flaresolverr_extract(data: dict) -> str:
    """Pull the solved HTML out of a FlareSolverr ``/v1`` response."""
    if data.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr error: {data.get('message') or data.get('status')}")
    return (data.get("solution") or {}).get("response", "")


def flaresolverr_html(url: str, endpoint: Optional[str] = None,
                      *, timeout_ms: int = 60000) -> str:
    """Fetch *url* through a FlareSolverr proxy, returning the solved HTML.

    FlareSolverr (https://github.com/FlareSolverr/FlareSolverr) drives a real
    headless browser that clears the Cloudflare JS challenge and returns the
    fully-rendered page — so this yields **live** data, unlike the Wayback
    fallback.
    """
    import requests
    endpoint = (endpoint or "http://localhost:8191").rstrip("/")
    resp = requests.post(
        f"{endpoint}/v1",
        json={"cmd": "request.get", "url": url, "maxTimeout": timeout_ms},
        timeout=timeout_ms / 1000 + 30,
    )
    resp.raise_for_status()
    return _flaresolverr_extract(resp.json())


class Transport:
    """Resolves *how* a page is fetched, from explicit kwargs with environment
    fallbacks.

    Args:
        mode:                 ``"requests"`` / ``"curl_cffi"`` / ``"wayback"`` /
                              ``"flaresolverr"``. ``None`` → resolve from the
                              environment, then auto (FlareSolverr if a URL is
                              configured, else curl_cffi).
        flaresolverr_url:     FlareSolverr base URL, e.g.
                              ``"http://192.168.1.116:8191"``. Setting this
                              alone selects the ``flaresolverr`` mode.
        flaresolverr_timeout_ms: per-request solve budget (default 60000).
        wayback_fallback:     fall back to the Wayback Machine on any live
                              failure. ``None`` → read the env flag.

    Example::

        from pyprogarchives import Transport
        t = Transport(flaresolverr_url="http://192.168.1.116:8191")
        t = Transport(mode="wayback")          # force the Internet Archive
    """

    def __init__(self, *, mode: Optional[str] = None,
                 flaresolverr_url: Optional[str] = None,
                 flaresolverr_timeout_ms: Optional[int] = None,
                 wayback_fallback: Optional[bool] = None) -> None:
        if mode is not None and mode.lower() not in _VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(_VALID_MODES)} or None, got {mode!r}")
        self.mode = mode.lower() if mode else None
        self.flaresolverr_url = flaresolverr_url
        self.flaresolverr_timeout_ms = flaresolverr_timeout_ms
        self.wayback_fallback = wayback_fallback
        self._session: Any = None

    # -- resolution (explicit kwarg > env > default) -----------------------

    def _fs_url(self) -> str:
        return (self.flaresolverr_url
                or os.environ.get("PYPROGARCHIVES_FLARESOLVERR_URL", "").strip())

    def _fs_timeout(self) -> int:
        if self.flaresolverr_timeout_ms is not None:
            return self.flaresolverr_timeout_ms
        return int(os.environ.get("PYPROGARCHIVES_FLARESOLVERR_TIMEOUT", "60000"))

    def _resolved_mode(self) -> str:
        if self.mode:
            return self.mode
        env = os.environ.get("PYPROGARCHIVES_TRANSPORT", "").strip().lower()
        if env:
            return env
        if self._fs_url():
            return "flaresolverr"
        return "curl_cffi"

    def _wayback_fallback(self) -> bool:
        if self.wayback_fallback is not None:
            return self.wayback_fallback
        return _truthy(os.environ.get("PYPROGARCHIVES_WAYBACK_FALLBACK"))

    def _session_for(self, mode: str) -> Any:
        if self._session is None:
            self._session = _build_session(prefer_curl=(mode != "requests"))
        return self._session

    # -- fetch -------------------------------------------------------------

    def get_html(self, path: str, **params: Any) -> str:
        """GET ``{BASE}{path}`` (with query *params*) and return the HTML."""
        url = path if path.startswith("http") else f"{BASE}{path}"
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        mode = self._resolved_mode()
        if mode == "wayback":
            html = wayback_html(url)
            if html is None:
                raise RuntimeError(f"no Wayback Machine snapshot available for {url}")
            return html

        try:
            if mode == "flaresolverr":
                html = flaresolverr_html(url, self._fs_url() or None,
                                         timeout_ms=self._fs_timeout())
                if _is_challenge(html):
                    raise RuntimeError("Cloudflare challenge not solved by FlareSolverr")
                return html
            r = self._session_for(mode).get(url, timeout=30)
            r.raise_for_status()
            if _is_challenge(r.text):
                raise RuntimeError("Cloudflare challenge served")
            return r.text
        except Exception:
            if self._wayback_fallback():
                html = wayback_html(url)
                if html is not None:
                    return html
            raise


_DEFAULT_TRANSPORT: Optional[Transport] = None


def default_transport() -> Transport:
    """Return the shared, environment-driven :class:`Transport`."""
    global _DEFAULT_TRANSPORT
    if _DEFAULT_TRANSPORT is None:
        _DEFAULT_TRANSPORT = Transport()
    return _DEFAULT_TRANSPORT


def get_html(path: str, **params: Any) -> str:
    """Module-level fetch using the shared env-driven transport (back-compat)."""
    return default_transport().get_html(path, **params)
