"""Example 04 — fetch a full band page.

Run::

    python examples/04_fetch_artist.py
"""
import pyprogarchives as pa

GENESIS = 1


def main() -> None:
    detail = pa.fetch_artist(GENESIS)
    print(detail.name)
    print(f"  genre   : {detail.genre}")
    print(f"  country : {detail.country}")
    print(f"  page    : {detail.url}")
    print(f"  bio     : {(detail.bio or '')[:160]}")
    print(f"  albums  : {len(detail.albums)}")

    print("\nUnknown id raises ArtistNotFound:")
    try:
        pa.fetch_artist(99_999_999)
    except pa.ArtistNotFound as e:
        print(f"  {e}")


if __name__ == "__main__":
    main()
