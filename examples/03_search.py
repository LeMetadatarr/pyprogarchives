"""Example 03 — search bands by name (client-side over the index).

Run::

    python examples/03_search.py
"""
import pyprogarchives as pa


def main() -> None:
    for query in ["genesis", "king crimson", "camel"]:
        hits = pa.search_artists(query, limit=3)
        print(f"{query!r} -> {len(hits)} hit(s)")
        for b in hits:
            print(f"    [{b.artist_id}] {b.display_name}  ({b.genre}, {b.country})")
        print()


if __name__ == "__main__":
    main()
