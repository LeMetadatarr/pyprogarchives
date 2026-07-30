"""Example 09 — build flat rows for a Hugging Face dataset.

Run::

    python examples/09_build_dataset.py
"""
import pyprogarchives as pa
from pyprogarchives import dataset

GENESIS = 1


def main() -> None:
    rows = list(dataset.artist_rows(pa.get_artists_by_letter("a")))
    print(f"artist_rows(A): {len(rows)} rows")
    print("  columns:", list(rows[0].keys()))
    print("  sample :", rows[0])

    detail = pa.fetch_artist(GENESIS)
    print("\nartist_detail_row:", dataset.artist_detail_row(detail))
    albums = list(dataset.album_rows(detail))
    print(f"album_rows: {len(albums)} (sample: {albums[0]})")

    n = dataset.write_jsonl("bands_A_sample.jsonl", rows[:25])
    print(f"\nwrote {n} rows to bands_A_sample.jsonl")


if __name__ == "__main__":
    main()
