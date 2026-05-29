# AGENTS.md — pyprogarchives

Typed Python client for Prog Archives (progarchives.com): browse the A–Z band
index, search by name, fetch full band pages (genre, country, biography, rated
discography), and a dataset row builder. Pure scraper — the metadatarr
`MetadataProvider` that consumes it lives in the **metadatarr** repo
(`metadatarr/resolve/providers/progarchives.py`), not here.

## Setup

```bash
pip install -e .
pip install -e .[stealth]   # adds curl-cffi for Chrome TLS impersonation (recommended)
pip install -e .[dev]       # adds pytest
```

## Test

```bash
pytest
```

Tests (`tests/`) parse real-markup fixtures in `tests/fixtures/` — no network.
In the shared OVOS dev venv `pytest-recording` and `pytest-vcr` clash (an
environment issue, not this package); run `pytest -p no:recording` if needed.

## Lint/Typecheck

None configured. Source is fully type-annotated with
`from __future__ import annotations`.

## Layout

- `pyprogarchives/__init__.py` — public surface: models (`Artist`,
  `ArtistDetail`, `Album`), functions (`get_artists_by_letter`, `iter_artists`,
  `get_all_artists`, `fetch_artist`, `search_artists`) and `ArtistNotFound`.
- `pyprogarchives/types.py` — the dataclasses. `_display_name` flips a single
  leading-article comma (`"BAND, THE"` → `"THE BAND"`).
- `pyprogarchives/parse.py` — **pure** HTML→model parsers (no network), so they
  unit-test against fixtures. `parse_listing` reads the `div.grid-container` of
  `div.grid-item` triples; `parse_artist` reads `h1`/`h2`, `div#artist-biography`
  (full `#moreBio` text), and `td.artist-discography-td` album cells (rating from
  the star-widget script).
- `pyprogarchives/artists.py` — fetching + client-side `search_artists`.
- `pyprogarchives/_transport.py` — `get_html()` over a shared session;
  defaults to `curl_cffi` Chrome impersonation, `PYPROGARCHIVES_TRANSPORT=requests`
  forces plain requests.
- `pyprogarchives/dataset.py` — flat HF row builders.
- `docs/`, `examples/`, `tests/fixtures/`.

## Site structure (progarchives.com)

HTML scrape (no JSON API), behind **Cloudflare**:

- `/bands-alpha.asp?letter=X` — A–Z index. `div.grid-container` → `div.grid-item`
  cells in repeating triples (artist link `artist.asp?id=`, genre, country).
- `/artist.asp?id=N` — band page. `h1` name, `h2` `"Genre • Country"`,
  `div#artist-biography` (`#shortBio` preview + `#moreBio` full), and
  `table.artist-discography-table` of `td.artist-discography-td` album cells
  (cover `img.artist-discography-cover`, `album.asp?id=` link, `nbRatings` span,
  `#777` year span, `generateReadOnlyStarbox(...)` precise rating).

Letters are `a`–`z` plus `0`.

## Conventions (Org hard rules)

- Branches: `dev` (work) / `master` (stable). NEVER `main`.
- Never edit `pyprogarchives/version.py`; gh-automations bumps semver from commit prefixes.
- New repos private by default.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- gh-automations reusable workflows referenced at `@dev`.
- No Neon / `neon-*`. No meta-commentary in docs/commits/code.

## Gotchas

- Cloudflare may serve a JS challenge from flagged IPs even with curl_cffi; the
  parsing layer is decoupled (`parse.py` takes raw HTML) so you can feed HTML
  fetched any other way.
- The bio div holds both `#shortBio` and `#moreBio`; parse only the full text or
  it duplicates.
- The discography rating comes from the JS star-widget call, not the visible
  span (which is keyed by artist id, not album id).
- `search_artists` only fetches the listings for the **initials in the query**.
