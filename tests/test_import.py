"""Public surface is importable and stable."""
import pyprogarchives as pa


def test_version():
    assert isinstance(pa.__version__, str)


def test_exports():
    for name in [
        "Artist", "Album", "ArtistDetail", "ArtistNotFound",
        "fetch_artist", "get_all_artists", "get_artists_by_letter",
        "iter_artists", "search_artists",
    ]:
        assert hasattr(pa, name), name
