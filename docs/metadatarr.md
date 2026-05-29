# metadatarr integration — canonical ids & entity lookup

Two questions: **what are the canonical identifiers**, and **how do you do
entity/media lookup with them?**

## Canonical identifiers

progarchives assigns a stable integer id to every band and album. Those are the
canonical keys this library exposes:

| Entity | `site_id` | Canonical URL | `to_external_ids_dict()` keys |
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

These live under `ExternalIds.extra` in [mediavocab](../../mediavocab) — a
free-form string→string namespace. Two records sharing `progarchives_artist`
are the same band: that's your **dedup / join key**.

## Entity lookup

A band is a **group entity**. The provider emits a `ProviderEntity` under
`EntityRole.ARTIST`, and metadatarr turns it into a deterministic **canonical
entity id** via `allocate_entity_id`:

```python
from metadatarr.resolve.entities import EntityRole, ProviderEntity, allocate_entity_id
from mediavocab.models import ExternalIds

entity = ProviderEntity(
    role=EntityRole.ARTIST,                       # → EntityKind.GROUP
    name="GENESIS",
    external_ids=ExternalIds(extra={"progarchives_artist": "1"}),
)
canonical = allocate_entity_id(EntityRole.ARTIST, name=entity.name,
                               external_ids=entity.external_ids)
# stable sha1 seeded from the progarchives id — same band ⇒ same entity id,
# however the name is spelled across providers.
```

## The resolver provider

Importing `pyprogarchives._provider` registers a `MetadataProvider` (no-op
without metadatarr/mediavocab). It activates for `PlaybackType.AUDIO` signals
tagged `"rock"` or `"progressive rock"`, resolves the band (preferring
`signals.artist`, then `signals.title`), and returns the external ids plus the
artist entity.

```python
import pyprogarchives._provider
from metadatarr.resolve.base import resolve
from mediavocab.models.signals import Signals
from mediavocab import PlaybackType

result = resolve(Signals(
    artist="Genesis",
    playback_type=PlaybackType.AUDIO,
    content_genres=["progressive rock"],
))
print(result.external_ids.extra)
```

### Confidence

| Match | Confidence |
|---|---|
| exact band name | 0.95 |
| one contains the other | 0.75 |
| token overlap | 0.40–0.70 |

### Driving the provider directly

`resolve()` fans out across all registered providers. To exercise just this one:

```python
import pyprogarchives._provider as p
prov = p.ProgArchivesProvider()
match = prov.lookup(Signals(artist="King Crimson",
                            playback_type=PlaybackType.AUDIO,
                            content_genres=["progressive rock"]))
print(match.external_ids.extra, match.confidence)
```

See `examples/08_metadatarr.py` for a runnable script.

## Scope

The provider resolves **bands** (the entity prog is catalogued by). Album ids
are exposed on `ArtistDetail.albums` for you to join on, but the resolver match
anchors on the band. Combine with MusicBrainz / Discogs providers for
recording-level cross-references.
