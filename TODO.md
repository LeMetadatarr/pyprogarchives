# TODO — pyprogarchives

## Open issues

None open.

## Gaps

- [ ] No CI workflows. Add gh-automations reusable workflows (`build-tests`,
      `coverage`, `license-check`, `release_workflow`, `publish_stable`) at `@dev`.
- [ ] No `.github/` directory.
- [ ] No linter/type checker configured (mypy/ruff).
- [ ] No live smoke test — the suite parses saved fixtures only (the live site
      is Cloudflare-gated, so live verification needs an unblocked network).

## Possible enhancements

- [ ] Album detail pages (`album.asp?id=`) — tracklist, lineup, reviews — could
      back a `fetch_album()`.
- [ ] The artist page lists only studio albums in the main discography table;
      live/compilation/boxset sections (if present) are not yet parsed.
- [ ] `to_mediavocab()` helpers building `Release`/`Entity` objects.

## Code TODOs

None found.
