# Detailed Plan: Task 169 — Correct the count-column name and unify the graph-table design

Issue #169: "Incorrect column name" — the count column on
`docs/graphs/biological_uniprot.rst` is labeled `grammar`, but per
`docs/graphs/index.rst` ("Contents") that column is *not* a grammar; it is the
number of vertex pairs reachable with respect to the canonical grammar's
language.

All eight per-category graph tables share the shape
`Graph | Num Nodes | Num Edges | <count col> | Size (MB) | Download`, but the
count-column header is inconsistent across categories: `c_alias`, `aa`,
`prov_derivation`, `vf`, `java_points_to`, `name_resolution`, `grammar`, and
four per-grammar names in `rdf`. The standalone `docs/reachable_pairs.rst`
page already uses the unified vocabulary **`Reachable pairs`** (rendered by
`utils/reachable_pairs_tables.py`).

## Confirmed decisions (user guidance)

- Unified header for every **single-count-column** category: **`Reachable
  pairs`**.
- The `rdf` category (four count columns, one per grammar) uses a **multi-row
  header** (`:header-rows: 2`): row 1 carries a common `Reachable pairs` group
  spanning the four count columns; row 2 carries the four grammar-specific
  subheaders (`subClassOf`, `subClassOf_type`, `type`, `broaderTransitive`).
- `old_graphs` is historical data: it is **not** maintained by the docs-table
  tools, so it is dropped from `archive_sizes.GRAPH_TABLE_FILES`.

## Source of truth

- `utils/reachable_pairs_tables.py` `GRAMMAR_COLUMNS` (line 77): the ordered
  `(column header, grammar file)` pairs per category. The header string is
  used verbatim to locate and rewrite the count cells of each category page in
  `update_category_columns` (line 400). The `None` grammar file means the
  per-graph `<graph>.cnf`.
- `utils/archive_sizes.py` `iter_graph_tables` / `_parse_table` (line 129):
  parses every graph table; `rows[0]` is treated as a **flat single-row
  header**, and `update_table` / `main` / `_table_urls` locate `Download` and
  `Size (MB)` in `rows[0]`.
- `docs/graphs/index.rst` "Contents" (lines 113–127): the human description of
  the count column.
- `tests/utils/test_reachable_pairs_tables.py` and
  `tests/utils/test_archive_sizes.py`: pin the current parsing/rendering
  behavior, including the in-sync check against the real repo
  (`test_check_mode_on_the_real_repo_is_in_sync`).

## Subtasks

### S1: Rename the single-count-column headers to `Reachable pairs` [done]

**Code:** `utils/reachable_pairs_tables.py` — in `GRAMMAR_COLUMNS`, change the
header string of the seven single-column categories (`biological_uniprot`,
`c_alias_analysis`, `context_sensitive_data_flow`, `data_provenance`,
`field_sensitive_alias`, `java_points_to`, `name_resolution`) from its current
value to `"Reachable pairs"`. Leave the `grammar` element of each tuple
unchanged. Do not touch `rdf` in this subtask.
**Tests:** `tests/utils/test_reachable_pairs_tables.py` — the existing
`test_check_mode_on_the_real_repo_is_in_sync` is the in-sync gate; after the
docs are updated it must pass. No new test is required for the rename itself.
**Docs:** `docs/graphs/biological_uniprot.rst`, `c_alias_analysis.rst`,
`context_sensitive_data_flow.rst`, `data_provenance.rst`,
`field_sensitive_alias.rst`, `java_points_to.rst`, `name_resolution.rst` —
change the count-column header cell (currently `grammar`, `c_alias`, `aa`,
`prov_derivation`, `vf`, `java_points_to`, `name_resolution` respectively) to
`Reachable pairs`. Cell values are untouched.

**Spec:**
- Only the header cell text changes in each page; the table otherwise stays
  byte-identical.
- `archive_sizes` is unaffected by this subtask (it keys on `Download` /
  `Size (MB)` only), and `reachable_pairs_tables` re-checks against the CSV by
  header name, so after the rename the in-sync check must report zero
  problems.

### S2: Teach the table parsers about multi-row headers [done]

**Code:** `utils/archive_sizes.py` — make `_parse_table` read the
`:header-rows: N` option and emit the first `N` rows as header rows
(`rows[0..N-1]`) with the rest as data rows (`rows[N:]`); a table is a graph
table when any header row contains `Download`. Add a helper
`header_columns(table) -> list[str]` returning the flat per-column header key
(the non-empty header cells of a column joined by `" / "`, in row order); a
column that is empty in a row contributes nothing (so a merged group yields
`"Reachable pairs / subClassOf"`). Update `update_table`, `main`, and
`_table_urls` to locate `Download` / `Size (MB)` via `header_columns` instead
of `rows[0]`. Keep the doctests of `iter_graph_tables` and `update_table`
valid (single-row tables must still round-trip).
`utils/reachable_pairs_tables.py` — `update_category_columns` locates each
count column by its flat key (from the new `header_columns` helper) instead of
a bare `rows[0]` membership test; the table is selected as the one containing
any of the wanted keys.
**Tests:** `tests/utils/test_archive_sizes.py` — add a `:header-rows: 2`
fixture: `iter_graph_tables` still returns one table, `header_columns`
yields `[..., "Reachable pairs / subClassOf", ..., "Size (MB)", "Download"]`,
and `update_table` fills the Size cell (the column left of `Download`) without
touching the four count cells; idempotent on a second pass. Add a
single-row regression case asserting behavior is unchanged.
`tests/utils/test_reachable_pairs_tables.py` — add a multi-row-header category
table and assert `update_category_columns` matches a count column by its flat
key and reports "missing from the table header" when the key is absent.
**Docs:** none (behavior for existing single-row tables is preserved).

**Spec:**
- Single-row tables (`:header-rows: 1`) produce the same flat keys as before,
  so `old_graphs` (if still scanned) and all current single-row category pages
  are byte-identical on a no-op run.
- The change is additive: the flat key for a single-row table equals the old
  `rows[0]` cell, so no existing assertion's meaning changes.

### S3: Give `rdf.rst` the unified `Reachable pairs / <grammar>` headers [done]

**Code:** none (pure docs).
**Tests:** `tests/utils/test_reachable_pairs_tables.py`
`test_check_mode_on_the_real_repo_is_in_sync` must pass after S2's parser
handles the 2-row `rdf` table.
**Docs:** `docs/graphs/rdf.rst` — set `:header-rows: 2` and add the second
header row: row 1 = `Graph | Num Nodes | Num Edges | (Reachable pairs group
over the 4 count columns) | Size (MB) | Download`; row 2 = the four grammar
subheaders under the group. The data rows keep all eight cells.
**Spec:**
- The merged `Reachable pairs` must span exactly the four count columns. The
  exact reST list-table layout that renders a merged group over sub-columns
  must be confirmed against the **real Sphinx build** (the docs gate), because
  the docutils list-table parser is position-based and cannot be validated in
  isolation. If the merged layout cannot be expressed cleanly, fall back to a
  2-row header in which row 1 holds `Reachable pairs` in the first count
  column and empty cells in the other three, and record the decision in Design
  Notes.

### S4: Drop `old_graphs` from the archive-size tool [done]

**Code:** `utils/archive_sizes.py` — remove `"old_graphs/index.rst"` from
`GRAPH_TABLE_FILES` and update the module docstring (it currently says "the
old-graphs table") so it describes only the per-category graph tables.
**Tests:** none reference `GRAPH_TABLE_FILES` or `old_graphs` in
`archive_sizes`; no test change is required.
**Docs:** none.

**Spec:**
- `old_graphs/index.rst` keeps rendering as before; it is simply no longer
  size-checked by the tool. Verified: `old_graphs/index.rst` is a single-row
  `Graph | Num Nodes | Num Edges | Size (MB) | Download` table (no count
  column), touched only by `archive_sizes.py`, and no test pins the file list.

### S5: Update the "Contents" description of the graph catalog

**Docs:** `docs/graphs/index.rst` "Contents" (lines 113–127) — restate that
the count column is titled **`Reachable pairs`** across all categories, and
that in categories with several grammars (e.g. RDF) the header is two rows:
a `Reachable pairs` group with one subheader per grammar. Keep the existing
explanation of "not available" / empty cells and the `Size (MB)` column.
**Code:** none.
**Tests:** none (docs-only).

**Spec:**
- No duplication: the page keeps being the single description of the column
  semantics; the category pages only show the table.

## Verification commands (per docs/developer.rst)

- Tests: `uv run pytest --cov=flpq_data --cov-report=term-missing --cov-report=json && uv run python utils/check_coverage.py`
- Style/lint: `uv run pre-commit run --all-files`
- Type check: `uv run ty check`
- Docs build (fresh, `-W`): see `docs/README.md`
- In-sync gate: `uv run python utils/reachable_pairs_tables.py`

## Design Notes (discovered during planning)

### Multi-row list-table header RST is unverified in isolation

Design rationale, as confirmed by the user: a common `Reachable pairs` group
header over the per-grammar subcolumns.

- The docutils `list-table` parser is **position-based**: the k-th `* -` line
  in a row is the k-th column; a merged cell is an empty cell in the rows
  below it within the same column. `publish_doctree` on hand-built
  multi-row tables collapsed to a single column in my tests, so the exact
  layout that renders a merged group over four subcolumns could not be
  confirmed outside the real Sphinx build.
- What was attempted: several 2-row header layouts (empty cells in the group
  columns in row 1, `Reachable pairs` in row 2; and the reverse). All
  collapsed to one cell under isolated docutils parsing.
- Remaining work: author the `rdf.rst` 2-row header (S3) and validate the
  rendered HTML in the docs gate; adjust the RST until the merge renders as
  intended, or fall back to the non-merged 2-row header and record it here.

### `archive_sizes` and `reachable_pairs_tables` share a table parser

- Root cause of the cross-cutting need: `iter_graph_tables` (in
  `archive_sizes.py`) is imported by `reachable_pairs_tables.py`, and both
  treat `rows[0]` as a flat header. A 2-row header moves `Size (MB)` /
  `Download` out of `rows[0]`, which would make the rdf table invisible to
  both tools.
- Resolution: `header_columns` (S2) is the single place that flattens
  header rows into per-column keys; both tools use it, so the multi-row case
  is handled once.

### docutils list-table cannot render a column-aligned merged group (BLOCKER for S3)

Confirmed by direct experiments against the project's docutils (0.22.4):

- A reST **list-table** merges a group *positionally*: when the group label
  `Reachable pairs` sits in one cell and its sub-cells (`subClassOf`,
  `subClassOf_type`, `type`, `broaderTransitive`) sit in the next header row,
  docutils concatenates them into *consecutive* cells, shifting the group left
  relative to the `Size (MB)` / `Download` columns. The group cannot be
  aligned over its four data columns. (The `:colspan:` / `:colwidths:`
  "colgroup" options that would express a true merge are Sphinx-only —
  docutils rejects them — and cannot be validated in this docutils-only
  environment.)
- A **grid-table** (the `+===+` / `===+` syntax) *does* support merged header
  cells via colgroups, which is the mechanism that would render the requested
  design. But every graph table in the dataset is a list-table, so switching
  the rdf table to a grid-table would (a) change its layout and (b) make the
  S2 parser (`_parse_table`, which reads the list-table `* -` / `- ` rows)
  unable to process it.
- Consequence: the user's requested "common `Reachable pairs` header over the
  four grammar subheaders, as a multi-row header" cannot be expressed in a
  list-table, and expressing it in a grid-table breaks the maintenance tools
  that the other seven categories rely on.

**Resolved (user decision):** the rdf table stays a single-row **list-table**;
each count column is headed `Reachable pairs / <grammar>` (a per-column
prefix, not a merged group), and the page renders the prefix and grammar on
two visual lines to keep the columns narrow. The S2 `header_columns` parser
resolves these flat keys; the S2 multi-row tests cover the `header_rows`
mechanism in general. **Superseded options:**
  1. (chosen) Keep the rdf table a **list-table** and use a single-row header
     with a unified prefix per column, `Reachable pairs / <grammar>`
     (distinct, self-describing, no merge). No parser change beyond S2.
  2. **Revert S2's multi-row support** and ship the unified single-column
     design for the seven categories only; leave rdf as-is.
  3. Convert **all** graph tables to grid-tables and teach the parsers the
     grid syntax (large, touches every category page).
