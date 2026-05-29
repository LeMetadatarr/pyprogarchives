"""Example 07 — canonical ids for dedup and cross-referencing.

Run::

    python examples/07_canonical_ids.py
"""
import pyprogarchives as pa


def main() -> None:
    band = pa.search_artists("genesis", limit=1)[0]
    print("Artist canonical id:", band.site_id)
    print("Artist external ids:", band.to_external_ids_dict())

    detail = pa.fetch_artist(band.artist_id)
    if detail.albums:
        a = detail.albums[0]
        print("\nAlbum canonical id: ", a.site_id)
        print("Album external ids: ", a.to_external_ids_dict())


if __name__ == "__main__":
    main()
