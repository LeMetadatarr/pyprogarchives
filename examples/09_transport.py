"""Example 09 — configuring the transport (Cloudflare workarounds).

progarchives.com is behind Cloudflare. You can pick how pages are fetched
either with **constructor kwargs** on the ``ProgArchives`` client (shown here)
or with environment variables (``PYPROGARCHIVES_TRANSPORT`` etc.).

Run::

    python examples/09_transport.py
"""
import pyprogarchives as pa


def main() -> None:
    # 1. Solve Cloudflare live via a FlareSolverr instance (best — fresh data).
    #    Setting flaresolverr_url alone selects the flaresolverr transport.
    live = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191")
    print("transport:", live.transport._resolved_mode())
    # detail = live.fetch_artist(1)   # uncomment with a reachable FlareSolverr

    # 2. Force the Internet Archive explicitly — no live request, no extra infra.
    archived = pa.ProgArchives(wayback=True)
    print("transport:", archived.transport._resolved_mode())
    detail = archived.fetch_artist(1)        # GENESIS, from the archived snapshot
    print(f"  {detail.name} — {detail.genre} — {detail.country}")
    best = max((a for a in detail.albums if a.avg_rating), key=lambda a: a.avg_rating)
    print(f"  highest rated: {best.title} ({best.year}) — {best.avg_rating}")

    # 3. Try live first, fall back to the archive on failure.
    resilient = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191",
                                wayback_fallback=True)
    print("transport:", resilient.transport._resolved_mode(), "(+ wayback fallback)")


if __name__ == "__main__":
    main()
