# Building a Hugging Face dataset

progarchives data is a small graph (band → albums). For HF you want flat
tables. `pyprogarchives.dataset` emits two streams sharing `artist_id`.

## What columns and rows?

### Table 1 — `bands` (headline table)

**One row per band.** Cheap version (`artist_rows`, from the index — no
per-band fetch):

| Column | Type | Example |
|---|---|---|
| `artist_id` | int64 | `1` |
| `name` | string | `"GENESIS"` |
| `display_name` | string | `"GENESIS"` (article-flipped) |
| `genre` | string | `"Symphonic Prog"` |
| `country` | string | `"United Kingdom"` |
| `url` | string | canonical page |

Rich version (`artist_detail_row`, one fetch per band) adds **`bio`** (the
substantial free-text biography — the headline NLP feature) and `n_albums`.

**Rows:** ~thousands of bands (the whole A–Z index; letter A alone is ~1,100).

### Table 2 — `albums`

**One row per album**, via `album_rows(detail)`:

| Column | Type | Notes |
|---|---|---|
| `album_id` | int64 | canonical id |
| `artist_id` | int64 | **join key** |
| `artist_name` | string | denormalised |
| `title` | string | |
| `year` | int64 | release year |
| `avg_rating` | float64 | PA average, 0–5 — a ready-made quality label |
| `num_ratings` | int64 | sample size / popularity weight |
| `cover` | string | image URL |
| `url` | string | |

## Why this shape

- **`artist_id` everywhere** joins the two tables and gives every row a stable
  canonical key (not a row index).
- **`avg_rating` + `num_ratings`** are an out-of-the-box regression/ranking
  target with a confidence weight — ideal for "predict album rating from text"
  or popularity studies.
- **`genre` / `country`** are clean categorical labels (prog sub-genres are a
  rich taxonomy).
- **`bio`** is the long free-text field for classification / retrieval /
  summarisation.

## Recipe

```python
import itertools, pyprogarchives as pa
from pyprogarchives import dataset

# Headline table for one initial (cheap)
rows = list(dataset.artist_rows(pa.get_artists_by_letter("a")))

# Whole index to JSONL (cheap rows)
dataset.write_jsonl("bands.jsonl", dataset.build_dataset())
# Rich variant (slow: one request per band — throttle yourself)
# dataset.write_jsonl("bands_rich.jsonl", dataset.build_dataset(with_detail=True))

# Albums table for a set of bands
albums = []
for b in itertools.islice(pa.iter_artists(), 100):
    albums.extend(dataset.album_rows(pa.fetch_artist(b.artist_id)))
dataset.write_jsonl("albums.jsonl", albums)
```

## Load into 🤗 `datasets`

```python
from datasets import Dataset, DatasetDict
ds = DatasetDict({
    "bands":  Dataset.from_json("bands.jsonl"),
    "albums": Dataset.from_json("albums.jsonl"),
})
ds.push_to_hub("your-org/prog-archives")
```

> Be polite when scraping the full index for the rich/album tables — throttle
> requests. See [advanced.md](advanced.md).

See `examples/09_build_dataset.py` for a runnable version.
