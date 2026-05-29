"""Example 08 — metadatarr provider integration.

Importing ``pyprogarchives._provider`` registers a MetadataProvider that
resolves a prog-rock band to its progarchives id and a canonical artist
entity. Requires ``metadatarr`` + ``mediavocab``.

This drives the provider directly so it is self-contained; in a pipeline you
would call ``metadatarr.resolve.base.resolve(signals)`` to fan out across all
registered providers.

Run::

    python examples/08_metadatarr.py
"""
import pyprogarchives._provider as provider_mod  # registers the provider


def main() -> None:
    from mediavocab.models.signals import Signals
    from mediavocab import PlaybackType
    from metadatarr.resolve.entities import EntityRole, allocate_entity_id

    provider = provider_mod.ProgArchivesProvider()
    signals = Signals(
        artist="Genesis",
        playback_type=PlaybackType.AUDIO,
        content_genres=["progressive rock"],
    )

    match = provider.lookup(signals)
    print(f"provider    : {match.provider}")
    print(f"confidence  : {match.confidence}")
    print(f"external ids: {match.external_ids.extra}")

    for e in match.relations.get(EntityRole.ARTIST, []):
        canonical = allocate_entity_id(EntityRole.ARTIST, name=e.name,
                                       external_ids=e.external_ids)
        print(f"\nentity: {e.name}")
        print(f"  kind         : {e.kind}")
        print(f"  external ids : {e.external_ids.extra}")
        print(f"  canonical id : {canonical}")

    print("\nMatches AUDIO+prog signal?", provider.matches(signals))


if __name__ == "__main__":
    main()
