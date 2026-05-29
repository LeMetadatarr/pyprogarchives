"""Example 05 — a band's rated discography.

Run::

    python examples/05_discography.py
"""
import pyprogarchives as pa

GENESIS = 1


def main() -> None:
    detail = pa.fetch_artist(GENESIS)
    print(f"{detail.name} discography (by year):\n")
    for a in sorted(detail.albums, key=lambda x: x.year or 0):
        stars = f"{a.avg_rating:.2f}" if a.avg_rating is not None else "  -  "
        print(f"  {a.year or '????'}  {stars} ({a.num_ratings or 0:>5} ratings)  {a.title}")

    rated = [a for a in detail.albums if a.avg_rating is not None]
    if rated:
        best = max(rated, key=lambda x: x.avg_rating)
        print(f"\nHighest rated: {best.title} ({best.avg_rating:.2f})")


if __name__ == "__main__":
    main()
