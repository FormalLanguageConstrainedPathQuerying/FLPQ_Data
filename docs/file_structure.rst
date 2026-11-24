.. _file_structure:

**************
File structure
**************

.. only:: html

   :Release: |release|
   :Date: |today|

A graph is distributed as a self-contained archive ``<name>.tar.gz`` that
unpacks to a directory named after the graph. Every archive has the same
fixed structure::

   <name>/
   ├── README.md              description of the graph and of its files
   ├── graph/                 one MatrixMarket file per stored edge label
   │   └── <label>.mtx
   └── queries/               all queries for this graph, one directory each
       ├── README.md          describes every query
       ├── cfpq/              .cnf and/or .rsm representations
       ├── rpq/               .re and/or .rsm representations (regular only)
       └── mcfpq/             .mcfg representations (Datalog-like MCFG syntax)

- ``README.md`` answers the mandatory questions of the contribution
  templates — the templates are the source of truth for the fields, as with
  the statistics conventions.
- ``graph/`` is never empty; ``queries/`` always carries the three class
  directories (possibly empty) and its ``README.md``.
- A query is a directory ``queries/<class>/<query>/`` holding every
  representation of the language — at least one file with a class extension
  (``.cnf`` / ``.rsm`` for CFPQ, ``.re`` / ``.rsm`` for RPQ, ``.mcfg`` for
  MCFPQ), each named after the query directory (e.g. ``queries/rpq/1/1.re``)
  — plus exactly one ``results.mtx`` and nothing else. The same query may be
  represented in several ways (e.g. a CFG and an RSM); all representations
  must define the same language.
- ``results.mtx`` is a Boolean pattern matrix with the same dimensions as
  the graph matrices: entry ``(i, j)`` is present iff some path from node
  ``i`` to node ``j`` satisfies the query. It depends on the language, not
  on the representation.
- ``queries/README.md`` has one ``## <class>/<query>`` section per query
  directory (path relative to ``queries/``), each with a non-empty
  description.
- A query's terminals resolve against its own graph's labels: a stored label
  or the reverse of one (see "Reversed edges" below). A terminal matching no
  stored label is legal but inert — materialization keeps it as-is and the
  query yields an empty result; the RDF category ships such non-applicable
  variants (e.g. ``generations`` has no ``subClassOf`` edges, so its
  ``nested_parentheses_subClassOf`` query is trivially empty). An RPQ
  representation in ``.rsm`` must be regular — no box transition may be
  labelled by a nonterminal.

A **partial archive** provides new queries for an existing graph: it unpacks
to a directory named after that graph and contains only ``queries/`` — the
new query directories (same layout) plus a ``README.md`` fragment with one
section per new query. It is validated with
``flpq-check-archive <name>.tar.gz --partial`` and merged into the existing
archive with :ref:`merge_archive`.

The pre-migration graphs on the :ref:`old_graphs` page use the old CSV
format instead.

Each file ``graph/<label>.mtx`` is a Boolean pattern matrix that holds
exactly the edges with that label::

   %%MatrixMarket matrix coordinate pattern general
   %%GraphBLAS type bool
   <num_nodes> <num_nodes> <num_edges>
   <tail> <head>
   ...

Node ids are 0-based integers, and the matrix dimensions equal the number of
nodes. A whole directory is loaded by
:obj:`graph_from_mtx_dir <flpq_data.graphs.readwrite.mtx.graph_from_mtx_dir>`.

Indexed labels
--------------

Some graphs have families of labels that differ only in a numeric suffix,
e.g. ``load_0``, ``load_1``, ..., ``load_857``. In the per-graph pages and
in grammars such a family is written once with a placeholder subscript
(``load_f`` or ``load_i``) and a note that lists the index set. Each stored
label has its own file named after the label itself (``load_5.mtx`` holds
the edges labeled ``load_5``).

Reversed edges
--------------

For every edge label ``L`` there is a reversed label ``L_r``: an edge ``(u, v)`` labeled
``L`` corresponds to an edge ``(v, u)`` labeled ``L_r``. Reversed edges are
not stored in the archives; they are derived by
:obj:`add_reverse_edges <flpq_data.graphs.utils.add_reverse_edges>`, and the
"Edges Statistics" tables of the per-graph pages list the stored labels
only.
