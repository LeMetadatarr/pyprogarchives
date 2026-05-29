"""Flat, tabular rows from progarchives data for Hugging Face datasets.

Two join-able streams sharing ``artist_id``:

- :func:`artist_rows` — one row per band (the headline table)
- :func:`album_rows`  — one row per album, carrying its band and ratings

See ``docs/dataset.md`` for the column dictionary and a full recipe.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator

from pyprogarchives.artists import fetch_artist, iter_artists
from pyprogarchives.types import Artist, ArtistDetail


def artist_rows(artists: Iterable[Artist]) -> Iterator[Dict[str, Any]]:
    """Yield one flat row per :class:`Artist` (list-level fields)."""
    for a in artists:
        yield {
            "artist_id": a.artist_id,
            "name": a.name,
            "display_name": a.display_name,
            "genre": a.genre,
            "country": a.country,
            "url": a.url,
        }


def artist_detail_row(detail: ArtistDetail) -> Dict[str, Any]:
    """Yield one rich row for a fetched :class:`ArtistDetail` (adds bio)."""
    return {
        "artist_id": detail.artist_id,
        "name": detail.name,
        "genre": detail.genre,
        "country": detail.country,
        "bio": detail.bio,
        "url": detail.url,
        "n_albums": len(detail.albums),
    }


def album_rows(detail: ArtistDetail) -> Iterator[Dict[str, Any]]:
    """Yield one row per album on a band page."""
    for a in detail.albums:
        yield {
            "album_id": a.album_id,
            "artist_id": detail.artist_id,
            "artist_name": detail.name,
            "title": a.title,
            "year": a.year,
            "avg_rating": a.avg_rating,
            "num_ratings": a.num_ratings,
            "cover": a.cover,
            "url": a.url,
        }


def build_dataset(
    letters: str | None = None,
    *,
    with_detail: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Stream artist rows for the whole index (or a subset of initials).

    ``with_detail=True`` fetches each band page and emits the richer
    :func:`artist_detail_row` (bio) — one HTTP request per band.
    """
    if with_detail:
        for a in iter_artists(letters):
            yield artist_detail_row(fetch_artist(a.artist_id))
    else:
        yield from artist_rows(iter_artists(letters))


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> int:
    """Write *rows* to *path* as JSON Lines; return the count written."""
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n
