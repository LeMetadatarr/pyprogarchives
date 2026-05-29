"""Optional metadatarr ``MetadataProvider`` for progarchives.com.

Importing this module registers :class:`ProgArchivesProvider` with the
metadatarr resolver. No-op if metadatarr / mediavocab are absent.

Activates for ``PlaybackType.AUDIO`` signals tagged ``"rock"`` or
``"progressive rock"``. Resolves a band to its progarchives id and emits an
``EntityRole.ARTIST`` (a group), from which metadatarr derives a deterministic
canonical entity id seeded from the progarchives id.

Usage::

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
"""
from __future__ import annotations

from typing import ClassVar, Optional, Set

try:
    from metadatarr.resolve.base import MetadataProvider, ProviderMatch, register
    from metadatarr.resolve.entities import EntityRole, ProviderEntity
    from mediavocab import PlaybackType
    from mediavocab.models import ExternalIds
    from mediavocab.models.signals import Signals
    _AVAILABLE = True
except ImportError:  # pragma: no cover
    _AVAILABLE = False

import pyprogarchives as _lib


if _AVAILABLE:

    def _confidence(query: str, hit: str) -> float:
        q, h = query.lower().strip(), hit.lower().strip()
        if not q:
            return 0.0
        if q == h:
            return 0.95
        if q in h or h in q:
            return 0.75
        qt, ht = set(q.split()), set(h.split())
        return 0.4 + 0.3 * (len(qt & ht) / max(1, len(qt)))

    class ProgArchivesProvider(MetadataProvider):
        """Resolve a progressive-rock band to its progarchives id + entity."""

        name: ClassVar[str] = "progarchives"
        playback_type: ClassVar[Set["PlaybackType"]] = {PlaybackType.AUDIO}
        genre_filter: ClassVar[Set[str]] = {"rock", "progressive rock"}

        def is_available(self) -> bool:
            return True

        def lookup(self, signals: "Signals") -> Optional["ProviderMatch"]:
            query = (signals.artist or signals.title or "").strip()
            if not query:
                return None
            try:
                hits = _lib.search_artists(query, limit=1)
            except Exception:
                return None
            if not hits:
                return None
            best = hits[0]
            entity = ProviderEntity(
                role=EntityRole.ARTIST,
                name=best.display_name,
                external_ids=ExternalIds(extra={"progarchives_artist": best.site_id}),
            )
            return ProviderMatch(
                provider=self.name,
                confidence=_confidence(query, best.display_name),
                external_ids=ExternalIds(extra=best.to_external_ids_dict()),
                relations={EntityRole.ARTIST: [entity]},
            )

    register(ProgArchivesProvider())
