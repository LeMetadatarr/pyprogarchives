"""Example 06 — serialise to plain dicts / JSON.

Run::

    python examples/06_to_dict_json.py
"""
import json

import pyprogarchives as pa

GENESIS = 1


def main() -> None:
    detail = pa.fetch_artist(GENESIS)
    d = detail.to_dict()
    d["albums"] = d["albums"][:2]        # trim for readability
    if d.get("bio"):
        d["bio"] = d["bio"][:80] + "…"
    print(json.dumps(d, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
