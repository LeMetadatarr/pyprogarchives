"""Example 01 — browse the A–Z band index.

Run::

    python examples/01_browse_by_letter.py
"""
import pyprogarchives as pa


def main() -> None:
    bands = pa.get_artists_by_letter("a")
    print(f"{len(bands)} bands whose name starts with A\n")
    for b in bands[:12]:
        print(f"  [{b.artist_id:>6}] {b.display_name:<32} {b.genre or '':<22} {b.country or ''}")


if __name__ == "__main__":
    main()
