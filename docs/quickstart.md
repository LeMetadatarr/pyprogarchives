# Quickstart

From `pip install` to a band's full rated discography.

## 1. Install

```bash
pip install pyprogarchives[stealth]
```

The `stealth` extra pulls in `curl_cffi`, used by default to clear
progarchives.com's Cloudflare bot check. See [advanced.md](advanced.md) if
you still hit a challenge.

## 2. The mental model

Prog Archives catalogues **bands** and their **albums**:

```
Artist (a band) ──▶ Album, Album, Album …   (each with a member rating)
```

- An **`Artist`** is the lightweight shape from the A-Z index.
- An **`ArtistDetail`** is the full band page: genre, country, biography, and
  the rated discography.
- An **`Album`** is reached through an `ArtistDetail`. It carries the
  progarchives average rating and rating count.

## 3. Browse the index

```python
import pyprogarchives as pa

bands = pa.get_artists_by_letter("a")
print(len(bands), "bands under A")
for b in bands[:5]:
    print(b.artist_id, b.display_name, "-", b.genre, "-", b.country)
```

Or stream the whole index lazily:

```python
import itertools
for b in itertools.islice(pa.iter_artists(), 20):
    print(b.display_name)
```

> Bands with a leading article are listed comma-flipped (`"BAND, THE"`). Use
> `display_name` for the natural `"THE BAND"`.

## 4. Search

No server search exists, so the library searches the by-letter index:

```python
pa.search_artists("genesis")[0].display_name      # 'GENESIS'
pa.search_artists("king crimson", limit=1)
```

## 5. Fetch a band page

```python
genesis = pa.fetch_artist(1)
print(genesis.name, "-", genesis.genre, "-", genesis.country)
print(genesis.bio[:160])
print(len(genesis.albums), "albums")
```

Unknown ids raise `ArtistNotFound`.

## 6. The rated discography

```python
detail = pa.fetch_artist(1)
for a in sorted(detail.albums, key=lambda x: x.year or 0):
    print(a.year, f"{a.avg_rating:.2f}" if a.avg_rating else "  -  ",
          f"({a.num_ratings} ratings)", a.title)

best = max((a for a in detail.albums if a.avg_rating), key=lambda x: x.avg_rating)
print("Highest rated:", best.title, best.avg_rating)
```

## 7. Serialize and get canonical ids

```python
import json
print(json.dumps(detail.albums[0].to_dict(), indent=2))
print(detail.to_external_ids_dict())
```

## Next steps

- [api.md](api.md) - the complete reference
- [canonical_ids.md](canonical_ids.md) - canonical ids (how metadatarr consumes this)
- [dataset.md](dataset.md) - build a Hugging Face dataset
- [advanced.md](advanced.md) - Cloudflare, transport, errors

---
[Home](../README.md) · [API reference →](api.md)
