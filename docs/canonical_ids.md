# Canonical identifiers (for dedup and cross-referencing)

This client's job is to expose progarchives' **stable identifiers** so a
downstream resolver can de-duplicate and cross-reference. The resolver
itself, the metadatarr `MetadataProvider`, lives in the
**[metadatarr](../../metadatarr)** repo, not here. This package is a pure
scraper. metadatarr consumes it.

## What this client exposes

progarchives assigns a stable integer id to every band and album. Each model
surfaces them two ways:

| Entity | `site_id` | Canonical web URL | `to_external_ids_dict()` keys |
|---|---|---|---|
| Artist (band) | band id | `/artist.asp?id=<id>` | `progarchives_artist`, `progarchives_url` |
| Album | album id | `/album.asp?id=<id>` | `progarchives_album`, `progarchives_url` |

```python
import pyprogarchives as pa

g = pa.search_artists("genesis")[0]
g.site_id                    # '1'
g.to_external_ids_dict()
# {'progarchives_artist': '1', 'progarchives_url': 'https://www.progarchives.com/artist.asp?id=1'}
```

`to_external_ids_dict()` returns exactly the shape metadatarr stores under
`ExternalIds.extra` (a free-form string-to-string namespace). Two records
that share `progarchives_artist` are the same band. That is your **dedup /
join key**.

## How metadatarr consumes this

metadatarr ships a provider (`metadatarr/resolve/providers/progarchives.py`)
that imports this library, resolves a band for `PlaybackType.AUDIO` and
`"rock"`/`"progressive rock"` signals, and emits the external ids above plus
an `EntityRole.ARTIST` (group) entity. From that entity metadatarr derives a
deterministic canonical entity id (`allocate_entity_id`), so the same band
collapses to one entity across providers.

You do not import or configure anything here for that to work. Installing
both `pyprogarchives` and `metadatarr` is enough. metadatarr auto-discovers
the provider and self-disables it if this library is not installed. See the
metadatarr repo for resolver usage.

---
[← Advanced usage](advanced.md) · [Home](../README.md) · [Dataset →](dataset.md)
