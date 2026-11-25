# Detailed Plan: Task 194 — Eliminate the manual sync of the docs Size (MB) column

## Design (confirmed with the user)

Render the **whole** per-category graph table (`docs/graphs/<category>.rst`)
from machine sources instead of maintaining any cell by hand:

- `Num Nodes`, `Num Edges`, `Size (MB)` ← `flpq_data/dataset/registry.json`
  (the registry gains an exact `size_bytes` field — the 3-decimal `size_mb`
  is provably insufficient: 4 of 115 archives sit on a `.xx5` tie and
  double-rounding shifts their rendered cell by 0.01 MB);
- the `Reachable pairs` count columns ← `flpq_data/dataset/reachable_pairs.csv`
  (the existing `GRAMMAR_COLUMNS` spec, CFPQ rows only);
- rows ← the registry's per-category graph set, sorted by
  `(num_nodes, name)` (canonical order; 7 of 9 tables already use it — the
  first `--update` reorders exactly 2 rows: rdf `eclass`, biological_uniprot
  `unigraph_6`/`unigraph_7`);
- `:ref:` targets ← the site (existing `page_to_graph` mapping);
- `Download` links ← graph name + `DATASET_URL`.

Mechanism: the project's marked-region pattern — each table is wrapped in
`.. graph-table:begin` / `.. graph-table:end` and replaced wholesale by the
existing generic `replace_marked_region` helper. Check mode renders and
compares (no RST parsing needed); `--update` rewrites.

Consequences:

- `utils/archive_sizes.py` is **retired** (its parser, in-place updater, and
  S3 HEAD code all become dead; the S3 link stays guarded by download-time
  sha256 + registry regeneration on every archive change).
- `reachable_pairs_tables.update_category_columns` is **retired** (absorbed
  into the renderer — one owner per table).
- The gate is an **offline** in-sync test in the standard suite (no network,
  no tolerance) covering every column.

Verified before planning (all 9 tables, 115 rows): tables are structurally
uniform (single-row header, no directive options); Size cells match the exact
S3 bytes; count columns match the CSV; row sets are identical across site,
registry, and CSV.

**Corrected during S2:** the pre-planning "Num Edges match" check was
vacuous (its download-cell regex silently failed on every row, so the
registry comparison never ran). The real state: **39 `Num Edges` cells are
stale** — they list the *logical* edge count (forward + reverse) while the
registry lists the *stored* count (forward only; reverse edges are
auto-generated at load and must not be stored). The registry is correct (the
contribution template defines `Num Edges` as "the number of stored edges";
the archive READMEs state the stored count; the `java_points_to` category —
stripped in #136 — has docs matching the registry). The stale cells:
biological_uniprot (10), data_provenance (18), field_sensitive_alias (10),
rdf `geospecies` (1, off by 14 — a separate smaller drift). The per-graph
data pages of these categories are stale too (they still list `_r` reverse
labels). Confirmed with the user: render from the registry (correcting the
39 cells), also fix the stale data pages, and document the reverse-edge
policy canonically (new S3).

## Reuse analysis (per the `reusing` skill)

- `flpq_data/dataset/registry.py` — `GraphInfo`/`_to_graph_info`/
  `graph_info`/`graph_names`/`categories` (extended with `size_bytes`).
- `flpq_data/dataset/data.py` — `DATASET_URL` (download links).
- `utils/reachable_pairs_tables.py` — `load_rows`, `category_order`,
  `page_to_graph`, `graph_to_category`, `GRAMMAR_COLUMNS`, `NOT_AVAILABLE`,
  `replace_marked_region`, `_validation_problems`, `REACHABLE_PAIRS_CSV`,
  `DOCS_DIR` (all reused by the new renderer).
- `utils/applicable_graphs.py::graph_pages` — **moved** to
  `reachable_pairs_tables.py` (next to `page_to_graph`, its inverse);
  `applicable_graphs` imports it from there.
- `utils/sizes.py::format_size_mb` — the exact formatter of the Size cells.
- `utils/archive_sizes.py::fetch_sizes` — reused **once** for the S1
  backfill (headers-only HEADs), then retired with the module.
- Test pattern: `test_check_mode_on_the_real_repo_is_in_sync`
  (real-repo in-sync test, offline).

## Subtasks

### S1: Add exact `size_bytes` to the registry (generator, API, bundled data) [done] faf95f9

**Code:**
- `utils/generate_registry.py` — `build_record`: store
  `record["size_bytes"] = size` (the exact byte count is already computed as
  `size = archive.stat().st_size`); update the Returns docstring.
- `flpq_data/dataset/registry.py` — `GraphInfo`: new field
  `size_bytes: int` (after `size_mb`); `_to_graph_info` maps it (strict,
  like the other fields); docstring Attributes.
- `flpq_data/dataset/registry.json` — backfill `size_bytes` for all 115
  records via a one-time throwaway script that reuses
  `archive_sizes.fetch_sizes` (headers-only HEADs of the 115 `DATASET_URL`
  archives) and rewrites the JSON in the existing deterministic format.

**Tests:**
- `tests/dataset/test_registry.py` — `test_registry_file_shape`: add
  `"size_bytes"` to the expected key set; `test_graph_info_skos`: assert the
  exact `size_bytes`; new test: for every graph,
  `round(info.size_bytes / 10**6, 3) == info.size_mb`.
- `tests/dataset/test_data.py` — `_fake_info`: add `size_bytes=1000`.
- `tests/utils/test_generate_registry.py` — the two `fake_build_record`
  dicts gain `"size_bytes": 1000`; `test_build_registry_success` asserts the
  field passes through.

**Docs:**
- `docs/flpq.rst` "Graph registry" — schema example gains `"size_bytes"`;
  field-sources line: `size_bytes` is the exact stored size in bytes,
  `size_mb` is derived from it (three decimals).
- `docs/utils.rst` "Graph registry" — the recorded-fields list gains the
  exact byte size.

**Spec:**
- JSON record key order is additive: `category, num_nodes, num_edges,
  size_mb, size_bytes, sha256, queries` (no reordering of existing keys).
- `size_bytes` = exact stored `.tar.gz` size in bytes (int); `size_mb`
  stays `round(size_bytes / 10**6, 3)`.
- `_to_graph_info` stays strict (KeyError on a missing field); the bundled
  data is backfilled in the same commit, so the package never sees a record
  without the field.
- Backfill verification (before committing): for every record,
  `round(size_bytes / 10**6, 3) == size_mb`, and
  `format_size_mb(size_bytes)` equals the current docs cell (115/115).

### S2: `utils/graph_tables.py` — render the category tables from registry + CSV [done]

**Code:**
- New `utils/graph_tables.py`:
  - `BEGIN_MARKER = ".. graph-table:begin"`, `END_MARKER =
    ".. graph-table:end"` (plain reST comments, like the existing markers).
  - `render_category_table(category, graphs, rows, pages) -> str` — pure
    rendering: header `Graph | Num Nodes | Num Edges | [count columns from
    GRAMMAR_COLUMNS.get(category, [])] | Size (MB) | Download`; rows sorted
    by `(num_nodes, name)`; cells: `:ref:`<page>``; `str(num_nodes)`;
    `str(num_edges)`; per count column `str(count)` / `NOT_AVAILABLE` /
    empty (grammar not applicable); `format_size_mb(size_bytes)`;
    `` `<name>.tar.gz <DATASET_URL><name>.tar.gz>`_ 📥 ``. Layout:
    `.. list-table::` + blank line + `   * - ` row starts / `     - `
    continuations; an empty cell is a bare `     -` line.
  - `_registry_problems(rows, site_map) -> list[str]` — cross-checks the
    registry against the CSV and the site: every registry graph is listed in
    the docs with a matching category and has at least one CSV row; every
    CSV graph is in the registry; every docs category has at least one
    registry graph.
  - `main(argv)` — check/--update, modeled on `applicable_graphs.main`:
    load CSV rows, site maps (`graph_to_category`, `graph_pages`), validate
    (`_validation_problems` + `_registry_problems`, all-or-nothing), render
    each category page's region, `replace_marked_region`; check mode exits 1
    on any drift or validation problem.
- `utils/reachable_pairs_tables.py` — add `graph_pages` (moved from
  `applicable_graphs.py`, next to `page_to_graph`); `applicable_graphs.py`
  imports it from there (its local definition is removed). Also add
  `display_path` (moved from `applicable_graphs._rel`, made public): a short
  display path when the path is under the repo root, the full path otherwise
  (needed so the check-mode reporting works for both the real repo and the
  tmp_path test fixtures). `applicable_graphs` and `graph_tables` both use it.
- One-time marker insertion into the 9 category pages (throwaway script
  using the existing `iter_graph_tables` to locate each table):
  `.. graph-table:begin` before the `.. list-table::` line,
  `.. graph-table:end` after the last cell line, blank-line separated per
  the existing marker convention.
- Run `python utils/graph_tables.py --update` once: the diff is the 39 stale
  `Num Edges` corrections (logical → stored count; see the corrected
  verification note above) plus 2 reordered rows (rdf: `eclass` before
  `geospecies`/`go`; biological_uniprot: `unigraph_7` before `unigraph_6`);
  every other cell unchanged.

**Tests:**
- New `tests/utils/test_graph_tables.py`:
  - golden rendering test (synthetic `GraphInfo`s, CSV rows, pages,
    monkeypatched `GRAMMAR_COLUMNS`): exact text incl. header, order,
    `not available`, empty cell (bare `-`), size formatting, download URL;
  - no-count-columns category (absent from `GRAMMAR_COLUMNS`);
  - ordering: `(num_nodes, name)` with a node-count tie;
  - `_registry_problems`: registry graph missing from the site, category
    mismatch, registry graph without a CSV row, CSV graph missing from the
    registry, docs category without registry graphs (registry functions
    monkeypatched);
  - `test_check_mode_on_the_real_repo_is_in_sync`:
    `assert graph_tables.main([]) == 0`.

**Docs:**
- `docs/utils.rst` — new "Graph tables" section (anchor
  `.. _graph_tables:`): the tool, its sources (registry + CSV), check/
  `--update` behavior, the canonical row order, and the workflow (run
  `--update` after any registry or CSV change, before committing).

**Spec:**
- The renderer is the **sole writer** of the category tables; it never
  parses RST (check = render + compare).
- Row set per category = the registry's `categories()[category]`; the CSV
  supplies only the count values; the site supplies only the `:ref:`
  targets. Validation (all-or-nothing, blocks any update) guarantees the
  three agree.
- Count-column semantics are ported unchanged from
  `update_category_columns`: CFPQ rows only; `(graph, grammar)` key with
  `grammar = grammar_file or f"{graph}.cnf"`; missing pair → empty cell,
  present-but-None → `not available`.
- The rendered region text starts at `.. list-table::` and ends at the last
  cell line (no surrounding blank lines — `replace_marked_region` adds them).

### S3: Fix the stale data pages + document the reverse-edge policy canonically

**Context:** 39 data pages (biological_uniprot 10, data_provenance 18,
field_sensitive_alias 10, rdf `geospecies` 1) list the *logical* edge count
(forward + reverse) and `_r` reverse-label rows, but the archives store only
forward edges (reverse edges are auto-generated at load and must not be
stored). The registry and the (now-rendered) category tables use the stored
count; the data pages must match.

**Code:** n/a (docs only).

**Docs:**
- The 39 stale data pages (`docs/graphs/data/*.rst`):
  - "Graph Statistics" `Num Edges` → the registry's `num_edges` (stored).
  - "Edges Statistics": drop the reverse-label rows (the `_r` / `r_i`
    variants); the remaining forward-label rows sum to the stored count.
- Canonical reverse-edge policy statement in the right shared place
  (`docs/graphs/index.rst`, the graph-data conventions): reverse edges are
  not stored in the archives, are auto-generated at load time
  (`add_reverse_edges`), and are **not** counted in `Num Edges` — the
  registry, the category tables, and the data pages all count stored edges
  only.

**Verification:**
- For each fixed data page: the "Edges Statistics" rows sum to the registry
  `num_edges`, and no reverse-style label remains.
- The canonical statement is the single source of truth; the issue template
  ("stored edges", "no `_r` rows") and the data pages align with it.

**Spec:**
- After this subtask, every data page's `Num Edges` and `Edges Statistics`
  match the registry (stored edges only), and the reverse-edge policy is
  stated once in a canonical place.

### S4: Retire `archive_sizes.py` and `update_category_columns`

**Code:**
- Delete `utils/archive_sizes.py` and `tests/utils/test_archive_sizes.py`.
- `utils/reachable_pairs_tables.py` — remove `update_category_columns`
  (and the `header_columns`/`iter_graph_tables` import from
  `archive_sizes`), remove the category-column loop and `pages_map` from
  `main()`, update the module docstring (the tool now covers only the
  reachable_pairs.rst region) and `__all__`; fix the comment that cites
  `archive_sizes.py`.

**Tests:**
- `tests/utils/test_reachable_pairs_tables.py` — remove the
  `update_category_columns` tests; the region tests and the real-repo
  in-sync test stay and pass unchanged.

**Docs:**
- `docs/utils.rst` — remove the "Archive sizes" section (anchor
  `.. _archive_sizes:`; it also carries a stale claim that the tool covers
  `old_graphs`); update the "Reachable pair counts" section: the tool
  covers only the per-graph tables — the category tables (incl. the count
  columns) are rendered by :ref:`graph_tables`.
- `docs/flpq.rst` — "Reachable pair counts" section: drop the
  "(following the pattern of ``utils/archive_sizes.py``)" reference and
  state that the category tables are rendered whole from the CSV and the
  registry; "Graph registry" section: drop the "(pattern of
  ``utils/archive_sizes.py``)" parenthetical.
- `docs/graphs/index.rst` — the table-conventions paragraph: note that the
  per-category tables are machine-rendered (see :ref:`graph_tables`).

**Spec:**
- After this subtask: the category tables have exactly one writer
  (`graph_tables.py`), the reachable_pairs.rst region exactly one writer
  (`reachable_pairs_tables.py`), and no module in the repo references
  `archive_sizes` (grep gate: `grep -rn archive_sizes --exclude-dir=.git
  --exclude-dir=.venv --exclude-dir=node_modules` matches nothing outside
  `CHANGELOG.md` history and `tasks/global_plan.md`, which are historical
  records and stay untouched).

### S5: Point the workflows at the rendered tables + changelog

**Code:**
- `utils/upload_to_s3.py` — docstring: the verified size is recorded in the
  registry (by `generate_registry.py`) and the table row is rendered by
  `graph_tables.py` (replaces "so a new graph's table row can be filled
  directly from the upload output").

**Tests:** n/a (docstring/docs only; the suite and math-snippet guard stay
green).

**Docs:**
- `.opencode/skills/add-graph/SKILL.md` — "Once per issue" step:
  `archive_sizes.py --update` → `graph_tables.py --update`; "Documentation"
  step 4: the row (incl. the `Size (MB)` cell) is rendered — run
  `python utils/graph_tables.py --update` before committing (see the "Graph
  tables" section of `docs/utils.rst`); the manual "fill the cell from the
  upload output" step is gone.
- `docs/utils.rst` "Upload to Yandex S3" — same rewording as the
  `upload_to_s3.py` docstring.
- `CHANGELOG.md` — `[Unreleased]` entry: the per-category graph tables are
  rendered from the registry and the reachable-pairs CSV (new
  `utils/graph_tables.py`); the registry gains an exact `size_bytes` field
  (exposed as `GraphInfo.size_bytes`); `utils/archive_sizes.py` and the
  in-place count-column sync are retired; the in-sync check is now an
  offline test covering every table column.

**Spec:**
- After this subtask, no workflow (add-graph, release, docs) contains a
  manual size-refresh step; the only step is the mechanical
  `graph_tables.py --update` after a registry/CSV change.

## Execution notes

- S1 → S2 → S3 → S4 → S5 strictly in order (S2 needs `size_bytes`; S3 fixes
  the stale data pages and documents the reverse-edge policy; S4 retires the
  old writers only after the new one is in place and green; S5 documents the
  final state).
- One commit per subtask: `feat(194-S1)`, `feat(194-S2)`, `docs(194-S3)`,
  `refactor(194-S4)`, `docs(194-S5)`; the last carries `Closes #194`.
- The S2 `--update` run produced the expected diff: the 39 stale `Num Edges`
  corrections (logical → stored count) plus the 2 row reorders (rdf `eclass`,
  biological_uniprot `unigraph_6`/`unigraph_7`); every other cell unchanged.
