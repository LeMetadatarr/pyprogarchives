# Advanced usage

## Cloudflare and transport

progarchives.com is fronted by Cloudflare's bot management. The shared session
(created lazily in `pyprogarchives._transport.default_session`) therefore
defaults to **`curl_cffi` with Chrome TLS impersonation** when the `stealth`
extra is installed — that alone clears the check from most networks.

```bash
pip install pyprogarchives[stealth]
```

Force plain `requests` (no impersonation) with:

```bash
export PYPROGARCHIVES_TRANSPORT=requests
```

If you still receive a Cloudflare **JS challenge** ("Just a moment…"), your IP is
flagged. Options:

- run from a residential / unblocked network;
- front the client with a challenge-solving proxy (FlareSolverr, etc.) and point
  the session at it;
- fetch the HTML however you like and call the parsers in
  `pyprogarchives.parse` directly — they take a raw HTML string and need no
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

When walking the whole index or fetching many band pages, throttle — a band
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

- The discography average rating is read from the page's rating-widget script,
  giving the **precise** value (e.g. `2.5569…`), rounded to 2 dp on the model.
- The biography div contains both a truncated preview and the full text; the
  parser returns only the full text, with the `"X biography"` heading and the
  trailing `"read more"` removed.
- `display_name` flips a single leading-article comma (`"BAND, THE"` →
  `"THE BAND"`); names without a comma are unchanged.
