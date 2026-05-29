# API reference

Everything below is re-exported from the top-level `pyprogarchives` package
(aliased `pa`).

## Functions

### `get_artists_by_letter(letter: str) -> List[Artist]`
Every band whose name starts with `letter` — `"a"`–`"z"` or `"0"` (names
starting with a digit/symbol). Raises `ValueError` otherwise.

### `iter_artists(letters: str | None = None) -> Iterator[Artist]`
Lazily iterate the full A–Z index, one initial at a time. Pass `letters` (e.g.
`"abc"`) to restrict the range.

### `get_all_artists(letters: str | None = None) -> List[Artist]`
Eager version of `iter_artists`.

### `fetch_artist(artist_id: int) -> ArtistDetail`
The full band page: genre, country, biography, and rated discography. Raises
**`ArtistNotFound`** if the page has no band.

### `search_artists(query: str, limit: int | None = None) -> List[Artist]`
Client-side search over the by-letter index. Fetches the listings for the
initials in `query`, keeps bands whose name contains every token, and ranks
exact / prefix matches first. `limit` caps the results.

## Models

All models are `@dataclass`es. Shared interface: `site_id`, `url`, `to_dict()`,
`to_external_ids_dict()`.

### `Artist` (list-level)

| Field | Type | Notes |
|---|---|---|
| `artist_id` | `int` | canonical id |
| `name` | `str` | as listed, e.g. `"BAND, THE"` |
| `genre` | `str \| None` | progarchives sub-genre, e.g. `"Symphonic Prog"` |
| `country` | `str \| None` | |

Properties: `site_id`, `display_name` (`"THE BAND"`), `url` (`/artist.asp?id=`).
External ids: `{"progarchives_artist", "progarchives_url"}`.

### `ArtistDetail` (full page)

Adds: `genre`, `country`, `bio` (plain text, de-duplicated, "read more" stripped),
and `albums: List[Album]`.

### `Album`

| Field | Type | Notes |
|---|---|---|
| `album_id` | `int` | canonical id |
| `title` | `str` | |
| `year` | `int \| None` | release year |
| `avg_rating` | `float \| None` | PA average, 0–5 (precise value from the rating widget) |
| `num_ratings` | `int \| None` | number of member ratings |
| `cover` | `str \| None` | cover image URL |
| `artist_id` | `int \| None` | back-reference |
| `artist_name` | `str \| None` | back-reference |

Properties: `site_id`, `url` (`/album.asp?id=`).
External ids: `{"progarchives_album", "progarchives_url"}`.

## Exceptions

### `ArtistNotFound`
Raised by `fetch_artist` when the requested id yields no band.

## Pages used

| Path | Wrapped by |
|---|---|
| `/bands-alpha.asp?letter=` | `get_artists_by_letter`, `iter_artists`, `search_artists` |
| `/artist.asp?id=` | `fetch_artist` |
