# Ephemera Atlas

An expandable browser archive explorer for NYPL historical menus, postcards, pamphlets and cigarette cards. Search the complete selected metadata locally, filter by recorded place, genre, collection and overlapping year range, inspect original records, compare two items, and export results or a dated record receipt.

<!-- coolcode:guide -->
Search a word such as **railroad** or use **Canadian traces** to find mentions in titles, subjects and notes. The separate place filter searches only recorded geographic subjects and publication places, which many items lack. Open a title for its original dates, source notes, rights and NYPL scan link. **Compare** keeps two records side by side; **Save record JSON** downloads the evidence. Optional scan previews contact NYPL; all searches stay in this tab. This is a selected edition of NYPL’s **30 December 2015** public-domain metadata release, not a live search or a complete inventory of its collections. The download date is separate from the original item date. Year filters overlap recorded ranges; the chart counts each item by its earliest recorded year. Missing dates remain explicitly undated.
<!-- /coolcode:guide -->

## Sources and coverage

- [Official NYPL public-domain data and field definitions](https://github.com/NYPL-publicdomain/data-and-utilities)
- [Pinned source revision](https://github.com/NYPL-publicdomain/data-and-utilities/tree/cb1332fcdc58b7a06917d013de63a4b915629530)
- [NYPL metadata CC0 licence](https://github.com/NYPL-publicdomain/data-and-utilities/blob/master/LICENSE)
- [NYPL API retirement notice](https://api.repo.nypl.org/) — the Repo API was retired from 1 August 2026; no public replacement is planned. This app uses the publisher’s downloadable archive instead, without an account or key.

NYPL identifies the release as a snapshot of its metadata on **2015-12-30**. Its repository is now archived. Source file URLs, SHA-256 digests, selected genres, coverage counts and retrieval time are published in `web/data/status.json`. The selected metadata is `web/data/catalogue.json.gz`; the compressed JSON includes an explicit column schema and collection-name dictionary. Current records are filtered from both complete source CSV files. No fixed-size starter sample or synthetic records appear in production.

The first configuration includes the exact genres **Menus**, **Postcards**, **Pamphlets** and **Cigarette cards**, including items that also have other genres. It does not promise trade-card coverage: those labels were not present in the inspected source release. There are no geocoded places or inferred coordinates. Geographic subjects and publication places are grouped under “Recorded place”; this is not necessarily the place an item depicts or where a menu was used. Title text can provide further clues.

Source title, dates, notes and subjects retain their original wording. Four selected records in the initial edition have a blank title, displayed as **Title not recorded**. Missing years are not zero; a reversed source year range discards the invalid end and retains the recorded date text. The chart uses earliest year, not an estimate of how much material existed in a period. Digitization choices, survival and cataloguing gaps strongly affect counts. Searches are metadata searches, not full-text OCR or menu-dish searches.

## Rights and privacy

The publisher describes items in this release as having no known **U.S.** copyright restrictions. Metadata is CC0 1.0. Each detail view repeats the release’s scope and links to the original record for current information. Image links come from the item’s `First Image` field and use NYPL’s documented preview size; images are not copied into this repository. No present-day global public-domain guarantee is made. Credit: **From The New York Public Library**.

Search terms and comparison choices stay in tab memory. No user input is saved by default. Optional scan previews and original-record links contact NYPL; source pages can carry additional rights information. The decorative paper arrangement is original CSS illustration, not a historical scan. The shared CoolCode counter records aggregate tool opens, not queries.

## Expand or customize

Edit **`web/config.json`**:

```json
{
  "genres": ["Menus", "Postcards", "Pamphlets", "Cigarette cards", "Posters"],
  "collectionIds": ["e5114e30-c52f-012f-993c-58d385a7bc34"],
  "maxRecords": 100000,
  "pageSize": 12,
  "presets": [
    {"label": "Canadian traces", "query": "canada", "genre": ""}
  ]
}
```

Genre matching is case-insensitive and exact against the individual pipe-separated genre terms. `collectionIds` adds all items from any chosen collection UUID. Genres and collection IDs are an **OR** selection. The example includes Posters, beyond the initial four genres. The existing source commit and source filenames remain in the complete configuration. `sourceCommit` must be a full upstream Git SHA; `sourceFiles` are the publisher’s `pd_items_N.csv` files. If adopting a different upstream release, review its schema, rights and actual source edition date before changing `sourceEdition`.

Counts and filter options derive from the selected records. The collector rejects an empty selection, missing schema, duplicate UUIDs or selection above `maxRecords` (configurable up to 200,000), instead of silently truncating. The compressed browser dataset has a 15 MB transport and 60 MB expanded bound. Narrow large selections if needed. Change `pageSize` (1–60) and `presets` without recollecting; ordinary pushes are offline builds of the bundled capture.

To collect and publish expanded coverage:

1. Edit and commit the configuration.
2. Open **Actions → Ephemera Atlas · Check and publish → Run workflow**, leave **Rebuild the selected NYPL archive** checked, and run on `main`.
3. The workflow downloads the pinned source files, validates the new selection, runs tests/browser checks, commits the checked `web/data/` edition and deploys it. A failed refresh never publishes over the last good site.
4. Reload the app and check the displayed count and download date. Existing downloaded receipts retain their original source and retrieval dates; a new edition does not rewrite them.

Or run locally:

```sh
python3 scripts/refresh.py
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

The collector only writes public normalized metadata and provenance. Bulky upstream CSVs stay in ignored `.cache/`. `--use-cache` is a developer convenience only when that cache belongs to the configured revision. Git history retains prior committed editions; use a revision or save the metadata download to keep a particular selection.

No recurring schedule is enabled: the upstream is a fixed archived release. A manual workflow or local collector refresh is sufficient. This avoids describing a new retrieval as newly published historical data.

## Implementation and verification

- `web/model.mjs`: validation, local search, date-overlap rules, chronology, safe source links and exports.
- `web/app.mjs`: bounded gzip loading with SHA-256 verification, accessible controls, pagination, detail dialog and two-record comparison.
- `scripts/refresh.py`: standard-library CSV selection and atomic staged dataset creation; no dependencies or key.
- `scripts/build.py`: offline static build, reporting hooks and metadata escaping.
- Tests cover interval dates, undated records, blank fields, safe record links, duplicate IDs, expansion beyond original genres, selection bounds, malformed source rejection and capture integrity. Browser CI exercises search, no-result recovery, details, comparison, export and mobile layout at a project subpath.

For a local preview, serve `dist/` through an HTTP server. Browsers need gzip `DecompressionStream` support; current Chrome, Edge, Firefox and Safari support this. The app reports an unsupported browser rather than showing invented or empty results. The raw `.json.gz` download remains accessible from the sources section.

Related tools: [Art Timeline](https://coolcode.ca/arttimeline/), [Headline Vault](https://coolcode.ca/headlinevault/) and [Book Graveyard](https://coolcode.ca/bookgraveyard/).
