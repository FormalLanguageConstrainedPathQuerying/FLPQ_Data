.. _utils:

Maintainer tools
================

.. only:: html

   :Release: |release|
   :Date: |today|

The ``utils/`` directory contains maintainer scripts for managing the dataset
stored on Yandex Object Storage (bucket ``cfpq-data``, S3 API). They are not
part of the public ``flpq_data`` package.

.. _upload_to_s3:

Upload to Yandex S3
-------------------

``utils/upload_to_s3.py`` uploads a local file to the bucket::

   python utils/upload_to_s3.py FILE \
       --access-key-id KEY_ID --secret-access-key SECRET \
       [--endpoint-url URL] [--bucket BUCKET] [--key KEY]

- ``FILE`` — path to the local file to upload.
- ``--access-key-id``, ``--secret-access-key`` — Yandex Cloud IAM service
  account credentials. They are always taken from the command line and are
  never read from environment variables or config files.
- ``--endpoint-url`` — S3 API endpoint; default
  ``https://s3.yandexcloud.net`` (the verified working endpoint for the
  cfpq-data bucket).
- ``--bucket`` — target bucket; default ``cfpq-data``.
- ``--key`` — object key in the bucket; default is the file name (e.g.
  ``6.0.0/graph/NAME.tar.gz`` to follow the dataset layout).

Before uploading any ``.tar.gz`` the tool validates it as a graph archive
(:ref:`archive_structure`) and refuses an invalid one; after the upload it
verifies that the stored object size equals the local file size and reports
an error otherwise. The verified size is then reported in bytes and
megabytes, with the same MB formatting as the ``Size (MB)`` column of the
graph tables, so a new graph's table row can be
filled directly from the upload output.

.. _archive_sizes:

Archive sizes
-------------

``utils/archive_sizes.py`` keeps the ``Size (MB)`` column of the graph tables
in sync with the stored archives::

   python utils/archive_sizes.py [--update]

The tool covers every list-table with a ``Download`` column in
``docs/graphs/*.rst`` and ``docs/old_graphs/index.rst`` — currently the nine
per-category tables (115 archives at the ``6.0.0/graph/`` prefix) and the
old-graphs table (54 archives at the ``4.0.0/graph/`` prefix). For every
referenced archive it issues an S3 ``HEAD`` request and compares the
``Content-Length`` with the table cell, formatted in MB (three decimals below
one megabyte, two from one up — the rule lives in ``utils/sizes.py`` and is
shared with :ref:`upload_to_s3`).

Behavior:

- **Check mode (default).** Reports every row whose size cell disagrees with
  the stored object (or a missing column or link) and exits non-zero, so it
  can gate a commit.
- **``--update``.** Fetches all sizes first, then rewrites the tables —
  inserting the ``Size (MB)`` column before ``Download`` where it is missing
  and fixing drifted cells. All-or-nothing: if any archive cannot be fetched,
  nothing is written.
- **URL keying.** Sizes are keyed by full URL, not archive name: the
  ``4.0.0``, ``5.0.0``, and ``6.0.0`` prefixes hold same-named archives with
  different content.

When adding a new graph, upload it first (:ref:`upload_to_s3` prints the
verified size), add the table row with that value, and run this tool before
committing so every row — including the new one — matches S3.

.. _strip_reverse_edges:

Strip stored reverse edges
--------------------------

``utils/strip_reverse_edges.py`` normalizes a legacy archive that still stores
reverse matrices (the unindexed ``L_r.mtx`` or the indexed
``<base>_r_<n>.mtx``) — both are rejected by :ref:`archive_structure`::

   python utils/strip_reverse_edges.py ARCHIVE.tar.gz -o STRIPPED.tar.gz

The tool removes the reverse matrices, drops their bullet lines from the
archive ``README.md`` ("Edges and labels") and recomputes the stored-edge
total, then re-validates the result with the archive-structure checks. The
precomputed ``results.mtx`` are left untouched: reachability does not depend
on the redundant reverse matrices (they are exact transposes of forward
labels, and the reference solver derives reverses from every forward edge).
The output must be named after the graph (``<graph>.tar.gz``) so that
:ref:`upload_to_s3` stores it under the same name, replacing the previous
archive.

.. _merge_archive:

Merge partial archives
----------------------

``utils/merge_archive.py`` merges a partial archive into the existing graph
archive it extends::

   python utils/merge_archive.py EXISTING.tar.gz PARTIAL.tar.gz -o MERGED.tar.gz

The partial source may also be an unpacked directory or a Google Drive URL /
file ID (the archive is downloaded first). The tool validates both inputs
(full mode for the existing archive, ``--partial`` mode for the partial
one), copies the new query directories into the existing tree, appends the
fragment's sections to the existing ``queries/README.md``, re-validates the
merged tree in full mode, and writes the result. Any problem — a query that
already exists, a section already described, a top-level directory named
after another graph, or a failed re-validation — is reported and the output
is not written; both inputs are left untouched.

Every new query directory must also have a row in the reachable-pairs
registry (``flpq_data/dataset/reachable_pairs.csv``): the same graph, the
same query class, and the query directory name as the stem of the row's
``grammar`` file. This keeps the registry — the single source of truth behind
the :ref:`reachable_pairs_tables` and :ref:`applicable_graphs` renderings — in
step with the archives; an unregistered query aborts the merge.

The output file must be named after the graph (``<graph>.tar.gz``): the
upload tool stores it under that name, replacing the previous archive.

.. _add_reachable_pairs:

Add reachable-pairs rows
------------------------

``utils/add_reachable_pairs.py`` derives the reachable-pairs rows of one
validated archive and inserts them into
``flpq_data/dataset/reachable_pairs.csv``::

   python utils/add_reachable_pairs.py ARCHIVE.tar.gz --graph NAME \
       --category CAT [--partial] [--dry-run]

For every ``queries/<class>/<query>/`` directory the tool emits one row:
the query directory name as the stem of the ``grammar`` file (the
representation is picked in the order ``cnf > re > mcfg > rsm``) and the
declared entry count of the query's ``results.mtx`` as
``num_reachable_pairs``. The archive must pass the structure checker first
(full mode, or ``--partial`` for a partial archive), and a tarball must be
named after the graph. The CSV's ``(graph, grammar)`` sort order is
preserved; a row that already exists, or a category that disagrees with the
graph's existing rows, is reported and nothing is written. ``--dry-run``
prints the rows instead of writing them.

.. _reachable_pairs_tables:

Reachable pair counts
---------------------

``utils/reachable_pairs_tables.py`` keeps the reachable-pairs renderings in
sync with ``flpq_data/dataset/reachable_pairs.csv``, the single source of
truth for the reference counts (:ref:`reachable_pairs`)::

   python utils/reachable_pairs_tables.py [--update]

The tool covers two renderings: the per-graph tables of
``docs/reachable_pairs.rst`` (one section per graph category, one table
per graph, every query class rendered, between the
``reachable-pairs-tables`` markers) and the count columns of the eight
per-category graph tables in ``docs/graphs/*.rst``. The graph-to-category
mapping is derived from the site itself: each category page's toctree lists
its data pages, and the archive name in a data page's download URL is the
graph name (page titles are not reliable).

Behavior:

- **Check mode (default).** Reports every drifted cell or table region —
  plus CSV rows with an unknown ``query_class``, whose graph is unknown,
  whose category disagrees with the docs, or which has no count column in
  its category — and exits non-zero, so it can gate a commit. The
  count-column check applies to CFPQ rows only: the graph tables render
  CFPQ counts only, while the other classes are rendered in the per-graph
  tables of ``docs/reachable_pairs.rst``.
- **``--update``.** Rewrites the reachable-pairs region and fixes the
  drifted cells in place; lines that need no change keep their exact text.

On the category pages a cell is a number (the count), ``not available``
(a pair without a computed value yet), or empty (the grammar does not apply
to that graph) — the convention explained on the :ref:`graphs` page.

When a new count is computed, add the row to the CSV with the graph's
category and query class and run this tool with ``--update`` before
committing.

.. _applicable_graphs:

Applicable graphs
-----------------

``utils/applicable_graphs.py`` keeps the per-class "Applicable graphs" lists
of ``docs/queries/{cfpq,rpq,mcfpq}/index.rst`` in sync with the same CSV
registry::

   python utils/applicable_graphs.py [--update]

For each query class the tool lists the graphs that carry at least one query
of that class, grouped by graph category and cross-linking the shared
per-graph pages (``:ref:`` to ``docs/graphs/data/*.rst``), so no graph page
is duplicated. The lists are delimited by the ``applicable-graphs`` markers.
The graph-to-category and graph-to-page mappings and the CSV validation are
reused from :ref:`reachable_pairs_tables`.

Behavior:

- **Check mode (default).** Reports every drifted region — plus CSV rows the
  site cannot account for — and exits non-zero, so it can gate a commit.
- **``--update``.** Rewrites the drifted regions in place.
- **Empty class.** A class with no registered graphs renders a placeholder
  sentence instead of an empty list.

When a query is added for a graph, add its row to the CSV first and run this
tool with ``--update`` before committing.

.. _generate_registry:

Graph registry
--------------

``utils/generate_registry.py`` regenerates
``flpq_data/dataset/registry.json`` — the machine-readable per-graph metadata
bundled with the package (the "Graph registry" section of :ref:`flpq`) — from
the live dataset::

   python utils/generate_registry.py

For every graph in ``reachable_pairs.csv`` the tool downloads the archive
from the current dataset prefix and records: the category (from the CSV),
the node and edge counts (loaded with the package's own MTX reader), the
exact archive size in bytes, the archive size in MB, and its sha256, and the
query list from the archive's ``queries/`` tree (class, name,
representations — the class-to-representation mapping is reused from
:ref:`archive_structure`). The result is written as deterministic JSON.

Behavior:

- **All-or-nothing.** If any archive cannot be downloaded or processed,
  nothing is written and the failures are listed.
- **Local only.** The tool downloads every archive, so it never runs in CI
  (no-network policy). Re-run it whenever the dataset changes (a new graph
  or query), commit the result, and upload it to the bucket as
  ``<version>/registry.json`` with :ref:`upload_to_s3`.

.. _migrate_gdrive_to_s3:

Migrate from Google Drive
-------------------------

``utils/migrate_gdrive_to_s3.py`` moves graph archives from Google Drive to
the bucket, one item at a time::

   python utils/migrate_gdrive_to_s3.py \
       --access-key-id KEY_ID --secret-access-key SECRET \
       [--endpoint-url URL] [--bucket BUCKET] \
       [--docs-dir DIR] [--workdir DIR] [--mapping FILE] \
       [--limit N] [--dry-run]

The item list is discovered from the docs: every "Direct download" link in
``docs/graphs/data/*.rst`` and ``docs/old_graphs/data/*.rst`` that points to
Google Drive becomes a migration item (the object key name is the graph
name). For each item the tool downloads the archive, uploads it with the
verified upload from :ref:`upload_to_s3` (``5.0.0/graph/<name>.tar.gz``),
removes the local copy, and replaces the Drive link(s) in the docs with the
new Yandex URL. At most one item is on disk at any time.

Behavior:

- **Idempotent.** Before downloading, the tool checks the public bucket URL;
  items already on Yandex are skipped. Re-running after an interruption
  resumes where it stopped.
- **Name collisions.** Ten graph names appear in two collections with
  different content, so both archives are kept: the item whose docs page stem
  equals the name keeps ``<name>.tar.gz``, the other is stored under its docs
  page stem (e.g. ``cactus_field_sensitive_alias.tar.gz``). If two items
  resolve to the same key the run stops with an error. Re-uploading an
  existing key is guarded by a SHA-256 comparison of the downloaded bytes; a
  mismatch stops the run and keeps the local copy for inspection.
- **Mapping.** After every item the tool saves
  ``utils/migration_mapping.json`` with the mapping graph name → new Yandex
  URL (plus the Drive file ID and SHA-256) so the migration record survives
  interruptions.
- **Conservative.** Any per-item error stops the run; fix the cause and
  re-run.

Use ``--dry-run`` to preview which items would be uploaded without any
side effects, and ``--limit N`` to migrate only the first N items (for
testing).

.. _sync_plan_comment:

Sync the plan comment
---------------------

``utils/sync_plan_comment.py`` mirrors the detailed plan onto the task
issue::

   python utils/sync_plan_comment.py ISSUE [--check]

The detailed plan lives in ``tasks/detailed_plan.md`` — the single source
of truth. The task issue carries a mirror: a comment whose first line is
the ``<!-- detailed-plan -->`` marker. The tool finds that comment (the
last one, if several exist) and replaces its body with the marker plus the
current file content.

Behavior:

- **Pure mirror.** The comment is derived from the file, never edited by
  hand; re-running the tool is idempotent.
- **``--check``.** Verifies the mirror instead of writing it: exits 0 when
  the comment is in sync, 1 on drift. The comparison ignores trailing
  newlines because the GitHub API stores comment bodies with one extra
  trailing newline.
- **Marker discovery.** Comments are matched by their first line; the
  marker is the first line of the comment the plan is posted as.
- **Transport.** The tool shells out to ``gh api`` and requires an
  authenticated ``gh``; it never stores credentials.
