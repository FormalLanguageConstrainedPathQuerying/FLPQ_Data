# Detailed plan: #187 Integrate the #183 social_networks data (pokec + yago2s) and retire the RPQ stub templates

- **Task:** [#187](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/187) — integrate the real-world RPQ data of [#183](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/183) (new `social_networks` category: `pokec` + `yago2s`, RPQ-only) and retire the RPQ demo/stub material it replaces.
- **Branch:** `feature/187-social-networks-rpq` (from `dev`).
- **Resolves:** #183 (data contribution, Case 3 — new graphs, new category).
- **Depends on:** #184 (merged) — per-graph reachable-pairs tables, the count-less category convention, the canonical regex syntax. The integration is a pure data task riding on that infrastructure; no new mechanism is introduced.

## Locked decisions (confirmed with the user)

| # | Decision | Choice |
|---|---|---|
| 1 | Task scope | One task: data integration + stub retirement on a single branch |
| 2 | Query documentation | Per-graph **Queries** section on each per-graph page (pokec: 1 query; yago2s: 39 with their regexes), sourced from the archive's `queries/README.md` + the `query.re` files |
| 3 | "Query templates" section | Removed from `docs/queries/rpq/index.rst` (the page becomes intro + Applicable graphs) |
| 4 | `query.re` naming (discovered during the prerequisite) | The contributed archives name every representation file `query.re` instead of after the query directory, breaking CSV `(graph, grammar)` uniqueness, the per-query site tables, and the grammar filter. Resolution: **rename the files in the archives** to the directory names (repack + re-upload + new SHA256s on #183) **and** enforce the naming in the tooling (S0) so contributors hit it at validation time |

## Prerequisite (operational, no commit)

1. Download both archives from the Drive links of #183 into `/tmp/opencode/flpq-187/`:
   - `pokec.tar.gz` — Drive id `1L3QbMgQ3GsC2-I2NZYpGkD6QfQPiT2Nh`
   - `yago2s.tar.gz` — Drive id `16N0jIeWYzkLeCJ_M9mJZz8TnIdSVXc9Y`
2. Verify SHA256 against #183 — `b0aa476050475567af3a3c79809a448132b5958df1af3ccfe98b71443f4b1224` (pokec), `7800fa3b22ee83efe25d89a27713583bffbd56bbc3d1f803baea6ed424770e37` (yago2s). A mismatch means the shared file is not the validated one: stop and ask the contributor.
3. Re-run `uv run flpq-check-archive <name>.tar.gz` on both — both must pass (the contributor validated with 6.1.2, our current version).
4. Confirm both names are new: absent from `flpq_data/dataset/registry.json` and `flpq_data/dataset/reachable_pairs.csv`.
5. Upload both to S3 (user-provided Yandex credentials, CLI-only, never stored):
   `uv run python utils/upload_to_s3.py <name>.tar.gz --key 6.0.0/graph/<name>.tar.gz --access-key-id ... --secret-access-key ...`
   Record the verified size (MB) each upload reports — it fills the `Size (MB)` cell.
6. **Repackage both archives** (after S0 lands, so the stricter checker is in
   place): rename every representation file to the query directory name
   (`queries/rpq/1/query.re` → `queries/rpq/1/1.re`, `query.rsm` → `1.rsm`;
   yago2s: 39 dirs), re-tar with the same top-level layout, re-hash, re-validate
   (streaming wrapper — see #188 for why the plain checker OOMs here), re-upload
   over the same S3 keys, and comment the new SHA256s on #183 (the old ones
   refer to the superseded files). Content is byte-identical; only file names
   change.

## Why the subtasks are shaped this way

- `tests/dataset/test_registry.py` compares the bundled `registry.json` against the CSV
  (`test_graph_names_match_csv`, `test_categories_match_csv`) and pins the graph count
  (`test_graph_names_count_and_sorted`, currently 113). A CSV row without a registry
  record breaks the suite, so **each graph subtask lands its CSV row, its docs, and its
  registry regeneration in one commit**.
- `utils/generate_registry.py` downloads **every** archive from S3 (all-or-nothing,
  local-only, never CI). It therefore runs once per graph subtask (114 archives in S1,
  115 in S2) — a known one-time cost.
- The two real-repo check-mode tests (`tests/utils/test_reachable_pairs_tables.py::test_check_mode_on_the_real_repo_is_in_sync`,
  `tests/utils/test_applicable_graphs.py::test_check_mode_on_the_real_repo_is_in_sync`)
  force the CSV, the docs wiring, and the regenerated regions to land in the same commit.
- `utils/reachable_pairs_tables.py` derives the site map from the toctrees: the
  `docs/graphs/index.rst` toctree must list `social_networks`, the category page's
  toctree must list the data page, and the data page must carry the Yandex download URL
  (matched by `_URL_RE`) **before** the tool is run.
- A category absent from `GRAMMAR_COLUMNS` is left untouched by
  `reachable_pairs_tables.py --update` (no count columns to sync) — exactly the
  count-less convention of `docs/graphs/index.rst` lines 124–127.

## Subtasks

### S0: Enforce the representation-file naming convention

**Code:** `flpq_data/tools/check_archive_structure.py` — `_query_dir_problems`
reports a representation file whose stem is not the query directory name
(`queries/rpq/1/query.re` → "must be named after the query directory
(expected 1.re)"); `utils/add_reachable_pairs.py` — `derive_rows` raises
`ValueError` on the same condition (defense of the CSV invariant; the
docstring's "query directory name as the stem" intent now matches the code).
**Tests:** `tests/tools/test_check_archive_structure.py` —
`test_representation_not_named_after_query_dir` (rename `s.cnf` → `other.cnf`
in the valid tree, expect the naming problem);
`tests/utils/test_add_reachable_pairs.py` —
`test_derive_rows_refuses_misnamed_representation` (same rename, expect
`ValueError`). All existing fixtures already name files after their
directories, so no other test changes.
**Docs:** `docs/file_structure.rst` — the query bullet states the naming rule
explicitly (it was de-facto only); `.github/ISSUE_TEMPLATE/new-data-template.md`
— the "Data format" section carries the same rule with the same example.

**Spec:**
- Checker: in `_query_dir_problems`, after a file is accepted as a
  representation (suffix in `exts`), add
  `if path.stem != query_dir.name: problems.append(f"{rel}/{path.name}: "
  f"representation files must be named after the query directory (expected "
  f"{query_dir.name}{path.suffix})")`. Applies to full and partial archives
  alike (both routes call `_query_dir_problems`).
- Tool: in `derive_rows`, after `representation_file` returns, raise
  `ValueError` when `rep.name != f"{query_dir.name}{rep.suffix}"` with the
  same message shape; update the `Raises` docstring.
- Docs: one sentence each, same example (`queries/rpq/1/1.re`), no new page.
- Commit: `feat(187-S0): reject query representation files not named after
  the query directory` — includes this plan file (replacing the #185 plan)
  with S0 marked done.

### S1: Integrate pokec

**Code:** `flpq_data/dataset/reachable_pairs.csv` (via `utils/add_reachable_pairs.py`),
`flpq_data/dataset/registry.json` (via `utils/generate_registry.py`)
**Tests:** `tests/dataset/test_registry.py` — `test_graph_names_count_and_sorted` count
113 → 114; the two real-repo check-mode tests must pass; full suite green.
**Docs:** new `docs/graphs/social_networks.rst` (category page), new
`docs/graphs/data/pokec.rst` (per-graph page with a Queries section),
`docs/graphs/index.rst` (Contents row + toctree entry), `docs/reachable_pairs.rst`
(regenerated), `docs/queries/rpq/index.rst` (regenerated Applicable-graphs region).

**Spec:**
- CSV row: `uv run python utils/add_reachable_pairs.py /tmp/opencode/flpq-187/pokec.tar.gz --graph pokec --category social_networks`
  (re-validates the archive, refuses duplicates; appends `pokec,1.re,social_networks,rpq,30622564`).
- Category page `docs/graphs/social_networks.rst` (ref `graphs_social_networks`, title
  "Social Networks", modeled on `docs/graphs/rdf.rst`): the category description of #183
  (large directed graphs of social and family relations; nodes are entities — people,
  places, works; edges are social/family/affiliation relationships; queries are RPQs over
  those relations); hidden toctree with `data/pokec` (the `data/yago2s` entry is added in
  S2); graph table `Graph | Num Nodes | Num Edges | Size (MB) | Download` — **no**
  `Reachable pairs` column (count-less convention); **no** "Canonical grammars" section
  (no category-wide canonical grammar — the queries are per-graph RPQs).
- Per-graph page `docs/graphs/data/pokec.rst` (ref `pokec`, modeled on
  `docs/graphs/data/generations.rst`): Info (Full Name per the archive's README; Direct
  download `.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pokec.tar.gz>`_
  — must match `_URL_RE`; Source: SNAP soc-Pokec,
  `https://snap.stanford.edu/data/soc-Pokec.html`), Graph Statistics (1632803 / 30622564),
  Edges Statistics (`friend` | 30622564), plus a new **Queries** section: one list-table
  row per query — Query (`rpq/1`), the canonical regex from the archive's `query.re`
  (`friend`), and the description from the archive's `queries/README.md`.
- `docs/graphs/index.rst`: Contents row `:ref:`graphs_social_networks` | 1` (bumped to 2
  in S2) + `social_networks` toctree entry — appended, same order in both.
- Regenerate, in order: `uv run python utils/reachable_pairs_tables.py --update` (adds the
  "Social Networks" section with the pokec per-graph table to `docs/reachable_pairs.rst`;
  the social_networks category table is untouched), `uv run python utils/applicable_graphs.py --update`
  (replaces the "No RPQ queries have been added" placeholder in
  `docs/queries/rpq/index.rst`), `uv run python utils/archive_sizes.py --update`
  (verifies/fills the `Size (MB)` cell from S3).
- Registry: `uv run python utils/generate_registry.py` (downloads all 114 archives from
  S3; adds the pokec record) + bump the test count 113 → 114.
- Commit: `feat(187-S1): integrate the pokec graph (social_networks category)` — with
  S1 marked done in this plan file.

### S2: Integrate yago2s

**Code:** `flpq_data/dataset/reachable_pairs.csv` (39 rows, via
`utils/add_reachable_pairs.py`), `flpq_data/dataset/registry.json` (via
`utils/generate_registry.py`)
**Tests:** `tests/dataset/test_registry.py` — count 114 → 115; the two real-repo
check-mode tests; full suite green.
**Docs:** `docs/graphs/social_networks.rst` (toctree entry + table row), new
`docs/graphs/data/yago2s.rst` (per-graph page with a 39-query Queries section),
`docs/graphs/index.rst` (Contents count 1 → 2), `docs/reachable_pairs.rst` (regenerated),
`docs/queries/rpq/index.rst` (regenerated Applicable-graphs region).

**Spec:**
- CSV rows: `uv run python utils/add_reachable_pairs.py /tmp/opencode/flpq-187/yago2s.tar.gz --graph yago2s --category social_networks`
  (appends the 39 rows `yago2s,N.re,social_networks,rpq,<count>` for N = 1..39).
- Per-graph page `docs/graphs/data/yago2s.rst` (ref `yago2s`): Info (Full Name per the
  archive's README; Direct download
  `.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/yago2s.tar.gz>`_;
  Source: YAGO2s, `https://yago-knowledge.org/downloads/yago-2s`), Graph Statistics
  (25314540 / 77869864), Edges Statistics (the 88 stored labels with their edge counts,
  from the archive's MTX headers / README — cross-checked against the statistics table of
  #183), plus the **Queries** section: one row per query `rpq/1`…`rpq/39` — the canonical
  regex from each `query.re` and the description from `queries/README.md`.
- Category page: `data/yago2s` toctree entry + table row (25314540 / 77869864 / size from
  the upload / download link).
- `docs/graphs/index.rst`: Contents count 1 → 2.
- Regenerate the three tools as in S1; `archive_sizes.py --update` verifies both rows.
- Registry: `uv run python utils/generate_registry.py` (115 archives) + bump the test
  count 114 → 115.
- Commit: `feat(187-S2): integrate the yago2s graph (social_networks category)`.

### S3: Retire the RPQ stub templates

**Code:** none (docs only).
**Tests:** none (docs only); the docs build must pass — a dangling `:ref:` to a deleted
page fails the no-warnings build.
**Docs:**
- Delete `docs/queries/rpq/data/reachability.rst` and
  `docs/queries/rpq/data/label_star.rst` (and the now-empty `docs/queries/rpq/data/`
  directory).
- `docs/queries/rpq/index.rst`: remove the "Query templates" section and the now-empty
  `data/*` glob toctree; rework the intro — "A query is specified by a regular expression
  template instantiated per graph from its stored labels" becomes: an RPQ query is a
  regular expression in the dataset's canonical syntax, stored per graph inside the graph
  archive under `queries/rpq/` (see :ref:`file_structure`); an RPQ may also be represented
  by a regular RSM.
- `docs/flpq.rst` (every stub-era statement):
  - intro: "currently provides data for context-free path queries (CFPQ); it is being
    extended to all classes of FLPQ: regular path queries (RPQ) and multiple
    context-free path queries (MCFPQ)" → provides CFPQ and RPQ data; being extended to
    MCFPQ.
  - Query-class table: RPQ status "designed, no data" → "current".
  - "The existing data … is CFPQ data" → the data is CFPQ and RPQ.
  - "Templates." bullet → RPQ queries are per-graph regular expressions stored in the
    graph archives (no named templates); the two designed stubs are retired.
  - "Data status." bullet → real-world RPQ data exists: the `social_networks` category
    (`pokec`, `yago2s`).
  - Site-structure sketch: "RPQ query templates (regular expressions)" → "RPQ per-graph
    queries (regular expressions)".
- Commit: `docs(187-S3): retire the RPQ stub templates`.

### S4: CHANGELOG + republish the versioned dataset files

**Code:** none.
**Tests:** none.
**Docs:** `CHANGELOG.md` — `[Unreleased]`:
- **Added** — the `social_networks` category with `pokec` (1,632,803 nodes, 30,622,564
  edges, 1 RPQ query) and `yago2s` (25,314,540 nodes, 77,869,864 edges, 39 RPQ queries) —
  the first real-world RPQ data (#183, #187).
- **Removed** — the RPQ stub template pages (`reachability`, `label_star`) and the
  "Query templates" section of the RPQ query page.
- **Changed** — the RPQ docs describe per-graph queries instead of named templates.
- Republish the versioned copies to S3 (user-provided credentials):
  `flpq_data/dataset/reachable_pairs.csv` → key `6.0.0/reachable_pairs.csv`,
  `flpq_data/dataset/registry.json` → key `6.0.0/registry.json`.
- Commit: `docs(187-S4): changelog for the social_networks integration` with
  `Closes #183` as a standalone line.

### S5: Refresh stale Size (MB) cells (discovered during S1)

**Code:** none (docs only).
**Tests:** none (docs only); the docs build must pass.
**Docs:** the eight category pages whose `Size (MB)` cells `archive_sizes.py
--update` (an S1 step) corrected: `biological_uniprot.rst`,
`c_alias_analysis.rst`, `context_sensitive_data_flow.rst`,
`data_provenance.rst`, `field_sensitive_alias.rst`, `java_points_to.rst`,
`name_resolution.rst`, `rdf.rst`.

**Spec:**
- Discovery: S1's `uv run python utils/archive_sizes.py --update` rewrote Size
  cells in those eight pages (e.g. `enzyme` 0.360 → 38.43 MB, `geospecies`
  7.95 → 593.14 MB) — pre-existing drift, not caused by this task. The last
  Size refresh was task 133; the archives grew afterward and the registry was
  regenerated but the docs were not. `archive_sizes` is not a CI gate, so the
  drift was never caught.
- Verification (before committing): the changed lines are Size cells only; an
  independent `curl -sI` HEAD of a drifted object (e.g. `enzyme.tar.gz`,
  38,430,229 bytes) matches the corrected cell; the bundled `registry.json`
  already carried the correct `size_mb` values (docs-only staleness).
- Committed before S1 (the fix is ready and verified; keeping it out of S1
  keeps the pokec commit scoped to pokec).
- Commit: `fix(187-S5): refresh stale Size (MB) cells against the 6.0.0
  archives`.

### S6: Keep the reachable-pairs CSV on LF line endings (discovered during S1)

**Code:** `utils/add_reachable_pairs.py` — `add_rows` writes the CSV through
`csv.writer`, whose default line terminator is CRLF; the first production run
(S1's `add-rows`) rewrote the whole bundled CSV (committed as LF) with CRLF
line endings, turning a one-row append into a whole-file diff.
**Tests:** `tests/utils/test_add_reachable_pairs.py` —
`test_add_rows_keeps_lf_line_endings` (after `add_rows`, the file's bytes
contain no `\r`); the `_write_csv` fixture helper gets the same
`lineterminator="\n"` so fixtures mirror the bundled file.
**Docs:** none.

**Spec:**
- `csv.writer(f, lineterminator="\n")` in `add_rows` (one line).
- Restore the CSV to its committed LF state (`git checkout`), re-run S1's
  `add-rows` after this fix so the landed row comes from the fixed tool.
- Committed before S1 (S1's CSV output depends on the fix).
- Commit: `fix(187-S6): keep the reachable-pairs CSV on LF line endings`.

## Design Notes (discovered during implementation)

### Representation-file naming (the `query.re` incident)

The #183 archives name every representation file `query.re` (pokec also
`query.rsm`) regardless of the query directory (`queries/rpq/1/`,
`queries/rpq/2/`, …). The format spec imposed no naming rule, so the archives
were valid — but every downstream consumer keys queries by the grammar file
name: the CSV's `(graph, grammar)` uniqueness, the per-query tables of
`docs/reachable_pairs.rst`, the `reachable_pairs(grammar=…)` filter, and the
duplicate guard of `add_reachable_pairs.py` (a fourth yago2s query would have
been refused as a duplicate of `query.re`). All 113 pre-existing archives name
the file after the directory; the tool's own docstring ("the query directory
name as the stem of the grammar file") confirms the intent — the code
(`rep.name`) only matched it for convention-following archives.

User guidance (verbatim, comment on #187):

> Option 2. Rename files in the archives. And improve tool for contributor to
> prevent such problems. So, looks similar to  your option 3, am I right.

Resolution: S0 enforces the rule in the checker (contributors see it at
`flpq-check-archive` time) and in `derive_rows` (the CSV invariant is
defended directly); the prerequisite repacks both archives with
convention-compliant names and re-uploads them (new SHA256s commented on
#183).

## Status

- S0: [x]
- S1: [ ]
- S2: [ ]
- S3: [ ]
- S4: [ ]
- S5: [x]
- S6: [x]
