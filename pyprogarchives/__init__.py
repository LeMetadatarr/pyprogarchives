"""pyprogarchives — typed Python client for Prog Archives (progarchives.com).

Prog Archives is the reference catalogue of progressive-rock bands: an A–Z
index of bands, each with a biography and a member-rated discography.

Quick start::

    import pyprogarchives as pa

    # Browse the A–Z band index
    for a in pa.get_artists_by_letter("a")[:5]:
        print(a.artist_id, a.display_name, a.genre, a.country)

    # Search by name
    genesis = pa.search_artists("genesis")[0]

    # Full band page: genre, country, bio, rated discography
    detail = pa.fetch_artist(genesis.artist_id)
    print(detail.genre, detail.country)
    for album in detail.albums:
        print(album.year, album.avg_rating, album.title)

    # Stream the whole index lazily
    import itertools
    for a in itertools.islice(pa.iter_artists(), 20):
        print(a.display_name)

    # Serialise + canonical ids
    import json
    print(json.dumps(detail.to_dict(), indent=2)[:300])
    print(detail.to_external_ids_dict())

metadatarr integration (optional)::

    import pyprogarchives._provider          # registers the provider
    from metadatarr.resolve.base import resolve
    from mediavocab.models.signals import Signals
    from mediavocab import PlaybackType

    result = resolve(Signals(
        artist="Genesis",
        playback_type=PlaybackType.AUDIO,
        content_genres=["progressive rock"],
    ))
    print(result.external_ids.extra)
"""
from pyprogarchives.types import Artist, Album, ArtistDetail
from pyprogarchives.artists import (
    ArtistNotFound,
    fetch_artist,
    get_all_artists,
    get_artists_by_letter,
    iter_artists,
    search_artists,
)
from pyprogarchives.version import __version__

__all__ = [
    "Artist",
    "Album",
    "ArtistDetail",
    "ArtistNotFound",
    "fetch_artist",
    "get_all_artists",
    "get_artists_by_letter",
    "iter_artists",
    "search_artists",
    "__version__",
]
