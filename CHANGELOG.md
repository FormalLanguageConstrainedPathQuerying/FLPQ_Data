# Changelog

All notable changes to FLPQ_Data are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- The field-sensitive-alias pages rendered the edge label `f_r_i` as a TeX
  double subscript, which MathJax rejects with "Double subscripts: use
  braces to clarify" (#173); the label is now `f_{r\_i}` in the ten
  per-graph Edges Statistics tables and the canonical-grammar block.
- Seven grammar pages used `&` alignment tabs in plain display math, which
  MathJax rejects with "Misplaced &" (#174); the blocks are now wrapped in
  `\begin{aligned} ... \end{aligned}`.
- The eclass graph page's Source link (and the historical old_graphs
  page's Origin link) pointed to a URL the hosting university removed from
  its site; they now point to the archived original (Wayback Machine
  snapshot of the eClassOWL 5.1.4 ontology file the original page
  redirected to).

### Changed

- The math-snippet guard now validates every docs-page and package-docstring
  math snippet with the MathJax engine itself (mathjax 4.1.3 on Node,
  `utils/check_math_snippets_node.cjs`) instead of hand-crafted patterns,
  reporting the engine's own error message; the browser bundle is pinned to
  the same version (`mathjax_js` in `docs/conf.py`), and the guard also runs
  as a pre-commit hook.

## [6.1.1] - 2026-10-15

### Changed

- The contribution documentation is consolidated under the Dataset section:
  new "Contributing data" and "File structure" pages; both sections are
  removed from the Graphs page (now a pure catalog) and from the Dataset root.

## [6.1.0] - 2026-10-14

### Added

- The `flpq-check-archive` console command (installed with the package):
  validates a graph archive's structure, so contributors check their
  archives with `pip install flpq-data` alone — no script download.
- `utils/add_reachable_pairs.py`: derives the reachable-pairs rows of one
  validated archive (one row per query directory, with the declared entry
  count of its `results.mtx` as `num_reachable_pairs`) and inserts them into
  `flpq_data/dataset/reachable_pairs.csv`, preserving the file's sort order
  and refusing duplicate rows and category disagreements.

### Changed

- The archive structure checker moved from `utils/check_archive_structure.py`
  to `flpq_data/tools/` (console command `flpq-check-archive`); the S3 client
  factory and bucket constants moved to `flpq_data.dataset.s3`.

- Data contributions are issue-first: a single "CONTRIBUTE NEW DATA" issue
  carries one or more validated archives (one graph each), the per-archive
  validation output and SHA256, and the motivation; maintainers upload and
  merge the data into the dataset. The Graphs page documents the flow, the
  four contribution cases, and the consistency invariants — no graph without
  a query, no query without reference results, no item without description
  and motivation.

### Removed

- The `ADD NEW GRAPH` / `ADD NEW GRAMMAR` issue templates and the
  `new_graph` / `new_grammar` PR templates: data has no PR path, and a
  grammar is accepted only together with the archive that instantiates it as
  a query with reference results. A generic PR template covers code
  contributions.

## [6.0.0] - 2026-10-13

### Added

- Optimized WCNF grammar variants for the `java_points_to` and
  `c_alias_analysis` categories, taken from "Optimization of the Context-Free
  Language Reachability Matrix-Based Algorithm" (arXiv:2401.11029,
  optimization 5): every archive of the two categories now carries
  `java_points_to_muravev2024.cnf` / `c_alias_muravev2024.cnf` alongside the
  original grammar. Each variant follows the label convention of its archive
  (indexed `load_i` form or bare `load` family form) and was verified to
  return identical reachable-pair counts to the original with FastMatrixCFPQ
  on small graphs.
- The graph tables on the website now list the download size of every
  archive in a `Size (MB)` column — one unit (MB) for all graphs, from the
  smallest (0.002 MB) to the largest (112.65 MB) archive.
- `utils/upload_to_s3.py` reports the verified archive size (bytes and MB)
  after each upload, and the new `utils/archive_sizes.py` checks or updates
  the `Size (MB)` column of the docs graph tables against the stored
  archives on Yandex S3.
- The publish workflow now runs on every pull request targeting `master`: it
  builds the sdist and wheel and publishes them to TestPyPI (`skip-existing`),
  validating packaging before a release tag is cut.
- Ruff as the linting and formatting gate (rules `E`, `F`, `W`, `I` plus
  `ruff format`), replacing black; the codebase was brought in line in a
  one-time pass.
- Type checking with [ty](https://docs.astral.sh/ty/) for fast local checks
  and Pyright in CI; the package, tests, and utility scripts are now fully
  type-checked.
- A math-snippet guard in the test suite (`utils/check_math_snippets.py`): it
  scans every docs page and rejects math that MathJax cannot render — an
  unescaped underscore inside a text-mode command group (e.g.
  `\textit{a_b}`) — which previously surfaced only as an error on the
  deployed site while the Sphinx build stayed green.
- The MCFG readwrite module `flpq_data/queries/mcfpq/readwrite/mcfg.py`: a
  data model for multiple context-free grammars, lark-based parsing of the
  Datalog-like `.mcfg` format specified in `docs/flpq.rst`, semantic
  validation (start symbol, dimension and rank), and `mcfg_from_text` /
  `mcfg_to_text` with round-trip guarantees plus `mcfg_from_txt` /
  `mcfg_to_txt` for file I/O.
- The `category` and `query_class` columns of `reachable_pairs.csv` and the
  matching filters and row fields of the `reachable_pairs()` API: reference
  counts are now keyed per graph category and query class (`cfpq`, `rpq`,
  `mcfpq`).
- The transition-system description style of the `.rsm` format: a query may
  be written as an explicit labelled transition system in addition to the
  CFG (EBNF) style, and `rsa_from_text` accepts both.
- Partial graph archives: `utils/check_archive_structure.py --partial`
  validates an archive that carries only new queries for an existing graph,
  and `utils/merge_archive.py` merges such a partial archive into the
  existing full one.
- The reachable-pairs table is republished, versioned, on the dataset object
  storage (`6.0.0/reachable_pairs.csv`), exposed as `REACHABLE_PAIRS_URL` and
  fetched into the local data cache by `download_reachable_pairs()`; once
  downloaded, `reachable_pairs()` reads it instead of the bundled copy, so an
  updated table is consumed without reinstalling the package.
- The per-class "Applicable graphs" lists of the new query sections: a new
  `utils/applicable_graphs.py` renders each class's list from
  `reachable_pairs.csv`, grouped by graph category and cross-linking the
  shared per-graph pages, in check or `--update` mode.
- The end-user core rework design is documented in `docs/flpq.rst` (hub
  #148): the core/maintenance boundary — `flpq_data/` is the end-user core
  for dataset utilisation (benchmarks, statistical analysis), and dataset
  maintenance (archive validation, upload, merge, registry generation) stays
  in repo-only `utils/` scripts that are never installed with the wheel —
  plus the per-graph registry, the machine-global versioned cache, the lazy
  `graph_dir()` accessor, and the cache manipulation API. Implementation
  follows in #150–#152.
- A per-graph `registry.json` bundled with the package (and to be published
  to object storage as `<version>/registry.json`): for every graph — its
  category, node and edge counts, archive size in MB, sha256, and the query
  list with representations. It is generated by the repo-only
  `utils/generate_registry.py`. The network-free metadata API exposes it:
  `graph_names()` (all names), `graph_info(name) -> GraphInfo`, and
  `categories() -> dict[str, list[str]]` — the category of each graph
  (#147).
- The machine-global cache API: `cache_root()` (the effective root — the
  `FLPQ_DATA_CACHE` environment variable or the OS default from
  `platformdirs`), `cached_versions()` (the dataset versions present in the
  cache), and `clear_cache(keep=None)` (remove the cached version
  directories, optionally keeping one).
- Streaming format conversion: `convert_graph(src, dst, *, src_format,
  dst_format)` converts between `mtx` (a directory of MatrixMarket files),
  `txt`, `rdf`, and the FastMatrixCFPQ `.g` text (write-only) — plus an
  in-memory `nx.MultiDiGraph` as source — over a lazy edge stream without
  materializing a graph, so converting the largest archive (`fs`, 3.6M edges)
  from MTX to TXT or `.g` runs in ~0.1 GiB of RAM instead of ~4 GiB (#138).
  The streaming primitives: `iter_edges_from_mtx_dir` / `mtx_dir_from_edges`,
  `iter_edges_from_text` / `iter_edges_from_txt`, `iter_edges_from_rdf` /
  `rdf_from_edges`, `iter_edges_from_graph`, and `g_text_from_edges`.

### Changed

- Filled 56 of the 60 previously "not available" reachable-pair reference
  counts in `reachable_pairs.csv` (issue #130): the in-archive `results.mtx`
  stubs of the affected graphs now carry the full Boolean reachability matrix,
  computed with FastMatrixCFPQ using the language-equivalent low-memory
  grammars where they exist (`c_alias_muravev2024.cnf`,
  `java_points_to_muravev2024.cnf`, and the sparse uniprot grammar of issue
  #157). 48 counts match independent reference values exactly; the 8
  `java_points_to` pairs with stale references were confirmed by the dataset
  maintainer. The 4 pairs that exceed the 124 GB RAM compute host (libgdx /
  name_resolution, unigraph_8/9/10) remain "not available"; per-pair run data
  and the infeasibility rationale are recorded in
  `utils/stub_results_record.json`.
- The `publish` workflow gives every pull request targeting `master` a unique
  `X.Y.Z.dev<run number>` version on the runner before building, so each push
  publishes a distinct TestPyPI pre-release instead of being skipped as an
  existing file; the commit SHA is recorded in the run's step summary. The
  committed version and the tag/PyPI release path are unchanged.
- **Breaking:** the package is renamed `cfpq_data` -> `flpq_data` (PyPI
  distribution `flpq-data`) and `grammars/` is restructured into
  `queries/{cfpq,rpq,mcfpq}/` — the module tree gains the same query-class
  level as the site, per the FLPQ design in `docs/flpq.rst`. The flat
  top-level API is unchanged apart from the renames below; import the new
  names (`from flpq_data import *`).
- `download(name)` becomes `graph_dir(name)`, which is lazy: it returns the
  local graph folder from a machine-global, per-user cache (the
  `FLPQ_DATA_CACHE` environment variable or the OS default from
  `platformdirs`) keyed by dataset version, and downloads only on a cache
  miss — the archive is sha256-verified against the registry before it is
  installed. `download_graph(name)` and `download(name)` remain as deprecated
  aliases. The `DATASET` registry list is replaced by the `graph_names()`
  function backed by the per-graph `registry.json`; `DATASET_URL` now serves
  the `6.0.0/graph/` prefix.
- Development tooling migrated from Poetry to [uv](https://docs.astral.sh/uv/):
  PEP 621 project metadata with hatchling as the build backend, PEP 735
  dependency groups (`dev`, `test`, `docs`) instead of Poetry groups and the
  `setup.py` extras, a committed `uv.lock`, and all CI workflows on
  `astral-sh/setup-uv`.
- The labeled graph generators type their `labels` parameter as
  `Sequence[str]`, correctly accepting both a single label string and a
  sequence of labels (previously annotated `List[str]` despite the string
  default).
- The dataset on object storage moved to the 6.0.0 self-contained archive
  layout: each graph archive carries its queries under
  `queries/<class>/<query>/` (every representation plus one `results.mtx`)
  instead of a separate top-level `grammar/` directory, and the website's
  download links and `Size (MB)` tables point at the new prefix.
- The website's Dataset section is restructured into per-class query sections
  (CFPQ, RPQ, MCFPQ): the flat Grammars section is replaced by one section per
  class with its templates and an "Applicable graphs" list, and the "How to
  add a new grammar?" pointer moves to the Dataset page.
- `utils/merge_archive.py` refuses to merge a partial archive whose new query
  directory has no row in `reachable_pairs.csv` (same graph and query class,
  with the query directory name as the stem of the row's grammar file), so the
  registry cannot drift.
- **Breaking:** the RDF output of `graph_to_rdf` is now valid RDF 1.1 Turtle
  — IRI nodes `urn:flpq:node:<id>` and IRI predicates `urn:flpq:label:<label>`,
  streamed line by line without an in-memory store; files written by older
  versions (blank-node endpoints with a Literal predicate) remain readable.
  RDF is a set of triples, so parallel edges with identical `(u, label, v)`
  collapse on write — as before.
- `graph_to_text` emits one line per edge using the edge's `label` attribute
  (the convention `graph_to_mtx_dir` already required) instead of one line
  per value in the edge data dict.
- The per-graph docs pages no longer carry a `Version` row in their Info
  table: it was a manually maintained duplicate of the dataset version —
  stale on the current pages (`5.0.0` against the `6.0.0` dataset) and
  already visible in each page's own download URL and in `DATASET_VERSION`
  of `flpq_data/config.py`.

### Deprecated

- `download_graph()` and `download()`: deprecated aliases of
  `graph_dir()`; both emit a `DeprecationWarning` on every call. The
  `cfpq-data` PyPI distribution gets one final shim release depending on
  `flpq-data`, mapping the old names (`DATASET -> graph_names()`), so scripts
  importing `cfpq_data` keep working through one more release.

### Removed

- The legacy packaging layer: `setup.py`, `MANIFEST.in`, `requirements.txt`,
  and `requirements/` (dependencies now live in `pyproject.toml`).
- The unused `codecov` dev dependency (CI uploads coverage via the Codecov
  GitHub Action).
- The broken utility scripts `utils/fetch_dataset.py` and
  `utils/update_dataset_tables.py` (both failed at import time against the
  5.0.0 package layout).
- `download_grammars()` and `download_benchmark()`: queries now ship inside
  the graph archives, so the separate `grammar/` and `benchmark/` paths were
  removed from the S3 bucket, the docs, and the package. Benchmark data is out
  of scope for the dataset and is not reworked.
- The benchmark page and the separate `benchmarks` category: benchmarking data
  and results are not part of the dataset site, so no query-class section
  reserves a benchmarks page (#129).
- The `DATASET` registry constant (replaced by the `graph_names()` function
  and the per-graph `registry.json`) and the in-package data directory
  (`flpq_data/data/`, replaced by the machine-global cache).
- `graph_from_csv` / `graph_to_csv` and the CSV graph format: redundant with
  TXT (the same line-per-edge format, only the column order differed), and no
  dataset archive uses it (archives are MTX-only). Use `txt` instead.
- The `pandas` dependency (its only user was the CSV readwrite module).

### Fixed

- The 7 `java_points_to` archives that still stored reverse edges
  (`load_r_<n>.mtx`, `store_r_<n>.mtx`) after the 6.0.0 migration were
  stripped, so `add_reverse_edges()` no longer double-reverses them. Reversed
  edges are auto-generated and must not be stored, but these archives had
  passed validation because the checker rejected only the unindexed
  `L_r.mtx` form; it now rejects indexed stored reverses too, and the new
  `utils/strip_reverse_edges.py` normalizes an archive that carries them
  (#136).
- `reachable_pairs.csv` is shipped in the installed wheel and the
  documentation download link points at the versioned object-storage URL
  instead of an unpinned `dev`-branch URL that returned 404, so
  `reachable_pairs("wc", "c_alias.cnf")` no longer fails on a fresh install
  (#139).
- The C Alias grammar page rendered the MathJax error "'_' allowed only in
  math mode" instead of the parameter names and the example grammars: the
  page wrapped identifiers containing underscores in `\textit{...}` inside
  math, where an underscore is illegal. Parameter names now use the literal
  style and the reverse labels are plain subscripts (#127).
- The canonical-grammar math block on the Field-Sensitive Alias category
  page described a different language than the `vf.cnf`/`vf.rsm` shipped in
  every archive: its `a`-part accepted and rejected different strings (a
  single reverse `a` edge is in the dataset language but not in the docs'
  one). The block now reproduces the archive's productions, verified
  language-identical by exhaustive CYK membership comparison (#131).

## [5.0.0] - 2026-09-16

### Added

- Expanded the graph dataset to **113 labeled directed graphs** across eight
  families: C alias analysis (from "Demand-driven Alias Analysis for C", #2),
  RDF/OWL, Java points-to, field-sensitive alias, context-sensitive data-flow,
  data provenance (#16), name resolution (stack graphs), and biological graphs
  from UniProt for subgraph queries by context-free grammars (#26).
- `download_grammars()` to fetch per-graph and example grammars for the
  `c_alias`, `dyck`, `java_points_to`, and `nested_parentheses` templates.
- `download_benchmark()` to fetch benchmark data (e.g. `MS_Reachability`).
- `graph_to_mtx_dir()`, a writer for the per-label MatrixMarket format.
- A developer guide covering pre-commit, the test pipeline, docs build and
  deploy, package deploy, and contribution guidelines (#76).
- Release process documentation and a tag-triggered PyPI publish workflow
  (Trusted Publishing) with a manual TestPyPI validation run (#75, #33).
- A docs prebuild for pull requests: the no-warnings docs build and the full
  link check now run in CI on every push and PR (#74).
- Reference reachable-pair counts for graph × grammar pairs, computed with the
  FastMatrixCFPQ reference implementation and exposed via `reachable_pairs()`
  and a downloadable CSV (#32).

### Changed

- **Breaking:** graph archives are now distributed in the **mtx-per-label**
  format (one Boolean MatrixMarket file per edge label) instead of CSV.
  `download(name)` returns a directory; load a graph with
  `graph_from_mtx_dir(path / "graph")`.
- **Breaking:** the minimum Python version is now **3.11** (was 3.8).
- The whole dataset is served from a single versioned prefix (`5.0.0/graph/`);
  indexed-label files use the bare `<label>.mtx` name.
- Updated dependencies: networkx 3.6, pandas 2.3, rdflib 7.6, pyformlang 1.0.1,
  requests 2.33.

### Fixed

- Broken function documentation links on the Graphs page; unresolved
  cross-references now fail the docs build (nitpicky mode, no-warnings policy),
  and the full link check runs in CI and the pre-merge quality gate (#122).

### Notes

- This release completes most of the long-standing "Make CFPQ_Data better"
  backlog (#28): its earlier sub-items (networkx-based graph generators #27,
  updated synthetic graphs #30, graph size information #20) shipped in previous
  releases and remain in effect. The static-analysis data item (#2) is only
  partially complete: the "Demand-driven Alias Analysis for C" graphs are now
  documented with their source, while the "Batch Alias Analysis" data is still
  missing.
