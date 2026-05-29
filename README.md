# pyprogarchives

Typed Python client for [Prog Archives](https://www.progarchives.com) — the
reference catalogue of progressive-rock bands and their member-rated
discographies.

It scrapes the site's HTML behind clean dataclasses: browse the A–Z band index,
search by name, and fetch a band's full page (genre, country, biography, and a
rated discography). Every model exposes canonical ids for de-duplication and an
optional [metadatarr](../metadatarr) provider for cross-referencing.

## Install

```bash
pip install pyprogarchives
pip install pyprogarchives[stealth]   # adds curl-cffi — recommended (see below)
pip install pyprogarchives[dev]       # adds pytest
```

> **Cloudflare:** progarchives.com is fronted by Cloudflare. The client defaults
> to `curl_cffi` Chrome TLS impersonation (the `stealth` extra) which clears the
> bot check from most networks. From flagged IPs you may still hit a JS
> challenge — run from a residential/unblocked network or a challenge-solving
> proxy. The parsing layer is independent of how the HTML is fetched.

## 30-second tour

```python
import pyprogarchives as pa

# Browse the A–Z band index
for b in pa.get_artists_by_letter("a")[:5]:
    print(b.artist_id, b.display_name, b.genre, b.country)

# Search by name
genesis = pa.search_artists("genesis")[0]

# Full band page: genre, country, bio, rated discography
detail = pa.fetch_artist(genesis.artist_id)
print(detail.genre, detail.country)
for album in detail.albums:
    print(album.year, album.avg_rating, album.title)

# Canonical ids for dedup / cross-referencing
print(detail.to_external_ids_dict())
# {'progarchives_artist': '1', 'progarchives_url': '.../artist.asp?id=1'}
```

## What you can fetch

| Function | Returns | Source |
|---|---|---|
| `get_artists_by_letter("a")` | `List[Artist]` | `bands-alpha.asp?letter=` |
| `iter_artists()` | `Iterator[Artist]` | the whole A–Z index (lazy) |
| `get_all_artists()` | `List[Artist]` | eager full index |
| `search_artists("genesis")` | `List[Artist]` | client-side over the index |
| `fetch_artist(id)` | `ArtistDetail` | `artist.asp?id=` |

An `ArtistDetail` carries `albums: List[Album]`, each with progarchives' average
rating, number of ratings, year, and cover.

## Documentation

Start with **[docs/quickstart.md](docs/quickstart.md)**, then:

- [docs/api.md](docs/api.md) — every function and model field
- [docs/advanced.md](docs/advanced.md) — Cloudflare/transport, pagination, errors
- [docs/canonical_ids.md](docs/canonical_ids.md) — canonical ids (how metadatarr consumes this)
- [docs/dataset.md](docs/dataset.md) — building a Hugging Face dataset

Runnable, numbered scripts live in [examples/](examples/).

## Canonical ids & metadatarr

This package is a **pure scraper**. It exposes progarchives' stable ids via
`site_id` and `to_external_ids_dict()`:

```python
g = pa.search_artists("genesis")[0]
g.to_external_ids_dict()
# {'progarchives_artist': '1', 'progarchives_url': 'https://www.progarchives.com/artist.asp?id=1'}
```

The metadatarr resolver **consumes** these — the `MetadataProvider` lives in the
[metadatarr](../metadatarr) repo (`metadatarr/resolve/providers/progarchives.py`),
not here, so integration code isn't scattered across client repos. Install both
packages and metadatarr auto-discovers the provider. See
[docs/canonical_ids.md](docs/canonical_ids.md).
