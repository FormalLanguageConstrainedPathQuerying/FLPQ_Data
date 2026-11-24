---
name: CONTRIBUTE NEW DATA
about: Suggest new data (graphs, queries, grammars) to this project
title: "[NEW DATA] <brief description>"
labels: new data
assignees: rustam-azimov, vadyushkins

---

<!-- ⚠ To contribute new data, you must fill in all the fields in the triangle brackets(``<>``) ⚠ -->

## Contribution type

Pick the case that applies to this issue (an issue may combine several archives of the same case):

1. **New graph(s), existing category, existing grammar(s)** — full archive(s); the queries instantiate the category's canonical grammar(s).
2. **New graph(s), existing category, new grammar** — full archive(s) plus a grammar definition (see "Queries and grammars" below).
3. **New graph(s), new category** — full archive(s) plus the category name/description and its canonical grammar(s).
4. **New queries for existing graph(s)** — partial archive(s); sub-case 4b if a query uses a new grammar.

## Info
| | |
|---|---|
| Version | ``<Current version of FLPQ_Data>`` |
| Category | ``<Existing category name, or "new: <proposed name>" (N/A for case 4)>`` |

## Archives

One row per archive. An issue may carry a **set** of archives (e.g. all graphs of a new category) — but one graph per archive: each `<name>.tar.gz` unpacks to a single directory named after it.

| Name | Kind | Target graph | Archive | SHA256 |
|---|---|---|---|---|
| ``<name>`` | ``<full or partial>`` | ``<The existing graph name (partial only; "—" for full)>`` | [link](``<Google Drive link to <name>.tar.gz>``) | ``<Output of `sha256sum <name>.tar.gz`>`` |

## Validation (mandatory, per archive)

Validate every archive **before** sharing it and paste the output below. Without cloning the repo: `pip install flpq-data` — the checker is installed with the package as the `flpq-check-archive` command.

### `<name>.tar.gz`

```
flpq-check-archive <name>.tar.gz            # full archive
flpq-check-archive <name>.tar.gz --partial  # partial archive
<archive> structure ok
```

FLPQ_Data version used: ``<version>``

(One subsection per archive.)

## Motivation (mandatory)

``<Why this graph set / grammar / category is useful to other users. Must cover every new item: why this particular graph, grammar, or category must be added to the dataset and what it enables for FLPQ research.>``

## Reference results (mandatory)

Every query directory ships one `results.mtx` with the constrained reachability facts — a Boolean pattern matrix with the graph's dimensions, where an entry `(i, j)` means some path from node `i` to node `j` satisfies the query. **Queries without reference results are not accepted.** Every new graph must ship at least one query (the structure checker refuses archives without one).

## Data format

Two kinds of archives exist (both documented on the [File structure page](https://formallanguageconstrainedpathquerying.github.io/FLPQ_Data/file_structure.html)):

- **Full archive** — a new graph: `<name>.tar.gz` unpacks to a self-contained directory with `README.md`, `graph/` (one Boolean MatrixMarket pattern file per stored edge label), and `queries/` (one directory per query in `cfpq/`, `rpq/`, or `mcfpq/`; each query directory holds every representation of the query — `.cnf`/`.rsm`, `.re`/`.rsm` (regular only), or `.mcfg`, each named after the query directory (e.g. `queries/rpq/1/1.re`) — plus one `results.mtx`).
- **Partial archive** — new queries for an existing graph: `<name>.tar.gz` unpacks to a directory named after that graph containing only `queries/` — the new query directories (same layout) plus a `README.md` fragment with one `## <class>/<query>` section per new query. Partial archives are merged into the existing graph archive by the maintainers.

The query file formats — including the recursive state machine (`.rsm`) format — are documented on the [FLPQ design page](https://formallanguageconstrainedpathquerying.github.io/FLPQ_Data/flpq.html).

## Description document

**Full archive.** The archive's `README.md` must answer all of these questions (one `##` section each):
| | |
|---|---|
| What is this graph? | ``<A short description of the domain and what the graph models>`` |
| Source | ``<Where the data comes from (paper, dataset, tool) and the full citation>`` |
| Construction | ``<How the graph was built, extracted, or generated (method, parameters)>`` |
| Nodes | ``<What a node represents and the total number of nodes>`` |
| Edges and labels | ``<What each label family means and the number of edges per label>`` |
| Query classes | ``<Which of RPQ, CFPQ, MCFPQ apply to this graph and why>`` |
| License | ``<The license of the data>`` |
| Caveats | ``<Known limitations or approximations, or "None">`` |

**Partial archive.** Instead of a full description document, the `queries/README.md` fragment carries one `## <class>/<query>` section per new query, each describing the language (in words and/or in LaTeX) and its purpose on this graph.

*New graphs only — a partial archive adds no nodes or edges.*

## Graph statistics (new graphs only)

One subsection per new graph:

### `<name>`

| Num Nodes | Num Edges |
|:---:|:---:|
| ``<The number of nodes in the new graph>`` | ``<The number of stored edges in the new graph>`` |

| Edge Label | Num Edge Label |
|---:|---:|
| ``<The type of the edge label of the new graph>`` | ``<The number of edges in the graph of this type>`` |

List the stored labels only (no `_r` reversed-edge rows). A family of indexed labels (e.g. `load_0`, ..., `load_857`) is listed once with a placeholder subscript (e.g. `load_f`) and a note listing the index set.

## Queries and grammars

Canonical grammars are documented on the category page, not on the per-graph page. Pick the case that applies:

1. **Existing grammar(s)** — name the grammar(s) from the category's "Canonical grammars" section that apply; they become the table column(s) filled in for the new row(s). No new grammar text on the site.
2. **New grammar** — provide the grammar below; it will be added to the category page and a new column to its table. The same grammar must also be instantiated as at least one query directory with `results.mtx` in a contributed archive.
3. **New category** — provide the canonical grammar(s) below plus the category name and description; a new category page will be created with them.

Every query you provide must ship inside an archive (a full archive ships all queries of the graph; a partial archive ships the new ones): one directory per query in `queries/cfpq/`, `queries/rpq/`, or `queries/mcfpq/`, holding every representation of the query plus one `results.mtx`. Each query directory is described in a `## <class>/<query>` section of `queries/README.md`. A query may only use labels of its graph.

<LaTeX format of grammar (only for cases 2 and 3)>

<File-format text of the grammar — .cnf, .rsm, .re, or .mcfg (only for cases 2 and 3)>

<Category name and description (only for case 3)>

## Not accepted via this flow

- A grammar or query provided outside an archive — without reference results.
- Updates to an existing graph (a new version of the source dataset).
- A new representation of an existing query (e.g. adding `.rsm` next to a `.cnf`-only query).
- More than one graph inside a single archive (use several archives in one issue instead).
