"""Example 09 — fetch via the Wayback Machine when Cloudflare blocks you.

progarchives.com is behind Cloudflare. From a flagged network the live fetch
may hit an unsolvable JS challenge. Two escape hatches, both set by environment
variable (no code change):

- ``PYPROGARCHIVES_TRANSPORT=wayback``  — fetch only from the Internet Archive.
- ``PYPROGARCHIVES_WAYBACK_FALLBACK=1`` — try live first, fall back to the
  archive on failure.

Archived HTML can be stale, but the parsers are identical either way.

Run::

    PYPROGARCHIVES_TRANSPORT=wayback python examples/09_wayback.py
"""
import os

# Force archive-only mode for this demo (normally you'd set the env var yourself).
os.environ.setdefault("PYPROGARCHIVES_TRANSPORT", "wayback")

import pyprogarchives as pa


def main() -> None:
    print(f"transport = {os.environ['PYPROGARCHIVES_TRANSPORT']}\n")
    detail = pa.fetch_artist(1)        # GENESIS, from the archived snapshot
    print(detail.name, "—", detail.genre, "—", detail.country)
    print(f"{len(detail.albums)} albums; highest rated:")
    best = max((a for a in detail.albums if a.avg_rating), key=lambda a: a.avg_rating)
    print(f"  {best.title} ({best.year}) — {best.avg_rating}")


if __name__ == "__main__":
    main()
