---
name: add-graph
description: Use when adding a new graph to FLPQ_Data. Covers the mtx-per-label archive format, accepting external contributions (the issue-first pipeline), and the registry.json wiring.
---

# Add a graph to the dataset

## Source of truth

The required fields and metadata live in the GitHub issue template — do
**not** duplicate them here:

- `.github/ISSUE_TEMPLATE/new-data-template.md` (data contributions are
  issue-first; there is no PR path for data)

Fill in every field in the triangle brackets (`<>`) of that template.

## Data format

The archive layout and the label conventions are documented once in
`docs/file_structure.rst` — follow it exactly.
Pack every query of the graph into the archive per the "Queries and
grammars" section of the issue template, then validate with
`flpq-check-archive <archive>.tar.gz` (the upload tool runs the same check
and refuses invalid archives).

New queries for an existing graph ship as a **partial archive** instead —
see the "Data format" section of the issue template; it is validated with
`--partial` and merged into the existing archive with
`python utils/merge_archive.py EXISTING.tar.gz PARTIAL.tar.gz -o <name>.tar.gz`.

## Accepting an external contribution

Data arrives as a CONTRIBUTE NEW DATA issue carrying one or more archives.
Per archive, in order:

1. Download it from the Drive link in the issue.
2. Verify its SHA256 against the value in the issue — a mismatch means the
   shared file is not the validated one; stop and ask the contributor.
3. Re-run `flpq-check-archive <name>.tar.gz` (add `--partial` for partial
   archives) — it must pass.
4. Check the graph name against `flpq_data/dataset/registry.json` and
   `flpq_data/dataset/reachable_pairs.csv`: a full archive's name must be
   new, a partial archive's target must exist.
5. Add its reachable-pairs rows with
   `python utils/add_reachable_pairs.py <name>.tar.gz --graph NAME --category CAT [--partial]`
   (it re-validates the archive and refuses duplicates).
6. Put it in place: a full archive is uploaded to the dataset URL (see
   "Wiring a new graph into the code"); a partial archive is merged with
   `python utils/merge_archive.py EXISTING.tar.gz PARTIAL.tar.gz -o <name>.tar.gz`
   and the result uploaded under the graph's name.

Once per issue, after every archive is in: regenerate the registry
(`python utils/generate_registry.py`), do the "Documentation" steps (per-graph
pages, canonical grammars, new category page), then run
`python utils/reachable_pairs_tables.py --update` and
`python utils/graph_tables.py --update`.

## Wiring a new graph into the code

1. The graph archive must be uploaded under the dataset URL
   `https://cfpq-data.storage.yandexcloud.net/{VERSION[0]}.0.0/graph/<name>.tar.gz`.
2. Regenerate `flpq_data/dataset/registry.json` with
   `python utils/generate_registry.py` (it picks up the new graph from S3 and
   adds its row to the metadata API).
3. Loading happens via `graph_dir(name)` (which returns the self-contained
   graph directory — graph plus queries) and `graph_from_mtx_dir(path / "graph")`
   (`flpq_data/graphs/readwrite/mtx.py`).

## Documentation

1. Create the per-graph page `docs/graphs/data/<name>.rst`, following the
   structure of an existing page (description, statistics tables). The page
    carries **no** grammar section: canonical grammars are documented once on
    the category page. Statistics conventions: the issue template is the
    source of truth.
2. Handle the grammar case from the issue template's "Queries and grammars"
    section:
   - *existing category, existing grammar(s)* — nothing to add; the new table
     row fills in the matching column(s);
   - *new grammar for an existing category* — append the grammar to the
     category page's "Canonical grammars" section and add a column to its
     table;
   - *new category* — create `docs/graphs/<category>.rst` with the category
     description, the graph table (one column per grammar), and the
     "Canonical grammars" section.
3. Register the data page in the category page's toctree
   (`docs/graphs/<category>.rst`) — the per-category table row is rendered
   by `graph_tables.py` — and bump the category's graph count in the
   Contents table of `docs/graphs/index.rst`. For a new category, also add
   its page to the `docs/graphs/index.rst` toctree and a row to the
   Contents table.
 4. Run `python utils/graph_tables.py --update` before committing so the
   new row — including its `Size (MB)` cell — is rendered from the registry
   (see the "Graph tables" section of `docs/utils.rst`).

Note: a `data/*.rst` page missing from all toctrees produces only a Sphinx
*warning*, not an error, so the docs quality gate will not catch it — check
the build log for "not included in any toctree".

See also `.opencode/skills/run-tests` to verify, and the Graphs page of the
docs for the full list of names.
