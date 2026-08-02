# Advanced usage

## Cloudflare and transport

progarchives.com is fronted by Cloudflare's bot management. The shared
transport (created lazily in `pyprogarchives._transport.default_transport`)
defaults to **`curl_cffi` with Chrome TLS impersonation** when the `stealth`
extra is installed. That alone clears the check from most networks.

```bash
pip install pyprogarchives[stealth]
```

### Transport modes

`PYPROGARCHIVES_TRANSPORT` selects how pages are fetched:

| Value | Behavior |
|---|---|
| *(unset)* / `curl_cffi` | Live fetch with Chrome TLS impersonation (default). |
| `requests` | Live fetch with plain `requests`, no impersonation. |
| `wayback` | **Does not touch the live site.** Fetches the latest snapshot from the Internet Archive (Wayback Machine). |
| `flaresolverr` | Fetches through a FlareSolverr proxy that solves the Cloudflare challenge in a real browser and returns **live** HTML. |

```bash
export PYPROGARCHIVES_TRANSPORT=requests   # or: curl_cffi (default), wayback, flaresolverr
```

### Configure in code (no env vars)

Every setting is also a constructor keyword argument on the `ProgArchives`
client (and on `Transport`). Explicit keyword arguments always win over the
environment:

```python
import pyprogarchives as pa

# FlareSolverr (live): setting the URL selects the flaresolverr transport
client = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191")
genesis = client.fetch_artist(1)

# Force the Internet Archive
archived = pa.ProgArchives(wayback=True)            # == transport="wayback"

# Try live first, fall back to the archive
resilient = pa.ProgArchives(flaresolverr_url="http://192.168.1.116:8191",
                            wayback_fallback=True)

# Or build a Transport yourself and pass it to the functions
from pyprogarchives import Transport
t = Transport(mode="flaresolverr", flaresolverr_url="http://192.168.1.116:8191",
              flaresolverr_timeout_ms=90000)
bands = pa.get_artists_by_letter("a", transport=t)
```

The module-level functions (`pa.fetch_artist(...)` and similar) keep using
the environment-driven default transport.

### FlareSolverr: solve the challenge and get live data

[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) runs a headless
browser that clears the Cloudflare JS challenge. Unlike the Wayback fallback
it returns **current** pages, so it is the best option if you have an
instance (a one-container service, commonly on port `8191`). Point the
client at it:

```bash
export PYPROGARCHIVES_FLARESOLVERR_URL=http://192.168.1.116:8191
# setting the URL alone selects flaresolverr transport automatically;
# PYPROGARCHIVES_FLARESOLVERR_TIMEOUT (ms, default 60000) tunes the solve budget.
```

```python
import pyprogarchives as pa
genesis = pa.fetch_artist(1)        # fetched live, challenge solved by FlareSolverr
```

`pyprogarchives._transport.flaresolverr_html(url)` is exposed for direct use.
Combine with `PYPROGARCHIVES_WAYBACK_FALLBACK=1` to fall back to the archive
if FlareSolverr is down.

### Wayback Machine: surviving the JS challenge

If you receive a Cloudflare **JS challenge** ("Just a moment…"), your IP is
flagged and TLS impersonation alone will not help. The client can read the
site out of the **Internet Archive** instead. archive.org is not
Cloudflare-gated:

```bash
# Archive-only: every request goes to the Wayback Machine
export PYPROGARCHIVES_TRANSPORT=wayback

# Or: try live first, fall back to the archive on failure (challenge / non-2xx)
export PYPROGARCHIVES_WAYBACK_FALLBACK=1
```

It fetches the most recent capture's raw bytes (the Wayback `id_` form, no
toolbar, no link rewriting), so the parsers see the page exactly as
progarchives served it. The trade-off is **staleness**: a snapshot may be
weeks or months old, and very obscure pages may not be archived at all
(those raise `RuntimeError` in `wayback` mode, or fall through to the live
error under fallback). `pyprogarchives._transport.wayback_html(url)` is
exposed if you want to drive it directly.

Other options:

- run from a residential or unblocked network;
- front the client with a challenge-solving proxy (FlareSolverr or similar);
- fetch the HTML however you like and call the parsers in
  `pyprogarchives.parse` directly. They take a raw HTML string and need no
  network:

  ```python
  from pyprogarchives.parse import parse_artist, parse_listing
  bands  = parse_listing(open("bands-alpha-a.html").read())
  detail = parse_artist(open("genesis.html").read(), artist_id=1)
  ```

## Pagination and politeness

The index is one page per initial. Prefer the lazy iterator and slice it:

```python
import itertools, pyprogarchives as pa
head = list(itertools.islice(pa.iter_artists(), 200))
```

When you walk the whole index or fetch many band pages, throttle. A band
page is one request and the discography can be large:

```python
import time
for b in pa.iter_artists():
    detail = pa.fetch_artist(b.artist_id)
    ...
    time.sleep(1)
```

## Error handling

| Situation | What happens |
|---|---|
| Unknown band id | `fetch_artist` raises `ArtistNotFound` |
| Non-letter passed to `get_artists_by_letter` | `ValueError` |
| Network / non-2xx / Cloudflare challenge | underlying HTTP error propagates |

## Parsing notes

- The discography average rating is read from the page's rating-widget
  script, giving the **precise** value (for example `2.5569…`), rounded to
  2 decimal places on the model.
- The biography div contains both a truncated preview and the full text. The
  parser returns only the full text, with the `"X biography"` heading and
  the trailing `"read more"` removed.
- `display_name` flips a single leading-article comma (`"BAND, THE"` to
  `"THE BAND"`). Names without a comma stay unchanged.

---
[← API reference](api.md) · [Home](../README.md) · [Canonical ids →](canonical_ids.md)
