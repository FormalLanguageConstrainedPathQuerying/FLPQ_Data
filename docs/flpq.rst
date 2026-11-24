.. _flpq:

FLPQ: Formal-Language-Constrained Path Querying
===============================================

.. only:: html

   :Release: |release|
   :Date: |today|

Formal-language-constrained path querying (FLPQ) studies reachability in
labeled directed graphs where a path from :math:`u` to :math:`v` counts only
if its edge-label string belongs to a given formal language. FLPQ_Data
provides data for context-free path queries (CFPQ) and regular path queries
(RPQ); it is being extended to multiple context-free path queries (MCFPQ).
This page records the design decisions —
the query-class taxonomy, the grammar formalisms and file formats, and the
target structure of the site, the package, and the dataset. The RPQ
extension reuses the existing CFPQ data and interfaces unchanged.

Query classes
-------------

.. list-table::
   :header-rows: 1

   * - Query class
     - Language class
     - Formalism
     - Status in the dataset
   * - RPQ
     - Regular
     - Regular expressions, NFA/DFA
     - current
   * - CFPQ
     - Context-free
     - CFG/CNF (incl. indexed grammars)
     - current
   * - MCFPQ
     - Multiple context-free
     - MCFG, :math:`d`-MCFG(:math:`r`)
     - planned

All three classes use the same query pattern: a language :math:`L` constrains
the paths of a labeled graph, and a pair :math:`(u, v)` is reachable if some
string of :math:`L` labels a path from :math:`u` to :math:`v`. The classes
differ only in the language class used for the constraint and in the
formalism that specifies it. The existing data — the :ref:`graphs <graphs>`
catalog, the :ref:`query templates <cfpq_queries>`, and the
:ref:`reachable pair counts <reachable_pairs>` — is CFPQ and RPQ data; the
shared graph catalog is reused by all classes.

Regular path queries
--------------------

RPQ constraints are regular languages over the graph's edge labels. The
design decision for this class:

- **Format.** An RPQ query is a regular expression in the dataset's
  canonical regular expression syntax, stored as a ``.re`` file and read by
  :obj:`regex_from_text <flpq_data.queries.rpq.readwrite.regex.regex_from_text>`:

  - a **symbol** is a maximal run of characters outside the metacharacter
    set (an edge label or a nonterminal);
  - **concatenation** is whitespace, **union** is ``|``, **grouping** is
    parentheses;
  - ``*`` and ``+`` are postfix Kleene star and Kleene plus (``X+`` is
    sugar for ``X X*``);
  - ``$`` is the empty word (epsilon).

  Precedence: postfix operators > concatenation > union. The same syntax is
  used for the EBNF-style RSM bodies (see :ref:`below <rsm_format>`).
- **No named templates.** Unlike CFPQ, RPQ has no named, parameterized
  templates: every query is a per-graph regular expression stored in the
  graph archive. The two designed seed stubs (``reachability``,
  ``label_star``) were retired when the first real-world RPQ data arrived
  (the ``social_networks`` category).
- **Placement.** Query files live inside the self-contained graph archive
  under ``queries/rpq/`` (see :ref:`file_structure`); there are no standalone
  query or example archives. An
  RPQ may also be represented by a regular RSM (``.rsm``, see below).
- **Conversion.** :obj:`regex_to_rsa
  <flpq_data.queries.rpq.converters.rsa.regex_to_rsa>` derives a single-box
  regular RSM from a regular expression, and :obj:`rsa_to_regex
  <flpq_data.queries.rpq.converters.rsa.rsa_to_regex>` performs the inverse
  for a single-box regular RSM. These are one-way derivation aids: the RSM
  remains a first-class, independently specifiable representation — the
  archive checker couples ``.re`` and ``.rsm`` files only at terminal-set
  consistency and regularity, so an RSM that is not an exact copy of the
  regex-derived one remains fully valid.
- **Data status.** Real-world RPQ data exists: the ``social_networks``
  category (``pokec``, ``yago2s``), entered via the graph archives
  (migration, task 48).

Recursive state machines
------------------------

A recursive state machine (RSM) [1]_ is a way to specify context-free
languages that resembles finite automata: it is a set of **boxes**, each box
being a deterministic finite automaton without ε-transitions over the union
alphabet of terminals and nonterminals, with a start state and final states.
There is no stack in the representation — recursion happens during
computation, when a transition labelled by a nonterminal invokes the
respective box. A grammar in Extended Backus-Naur Form (EBNF) — productions
``N -> E`` where ``E`` is a regular expression over terminals and
nonterminals — maps to an RSM with one box per production.

RSMs are the query formalism of the GLL-based CFPQ algorithm [2]_, which
evaluates EBNF queries natively and was evaluated on this dataset.

Every RSM defines a context-free language, and
:obj:`cfg_from_rsa <flpq_data.queries.cfpq.converters.cfg.cfg_from_rsa>` converts
it to a CFG (each box state becomes a nonterminal, each transition a
production). An RSM is therefore a valid alternative representation of a
CFPQ query — and of an RPQ when it is regular: no box transition is labelled
by a nonterminal.

.. _rsm_format:

Format
^^^^^^

A ``.rsm`` file uses one of two description styles, selected automatically by
:obj:`rsa_from_text <flpq_data.queries.rpq.readwrite.rsa.rsa_from_text>`:

- **EBNF style** — one production per line; each production becomes one
  box. The body ``E`` follows the canonical regular expression syntax of
  the RPQ format (above), over terminals and nonterminals alike; an empty
  body is the empty word (epsilon)::

    start: S
    S -> a* b S c
    B -> (x | y)+

- **Transition-system style** — explicit boxes as labelled graphs with start
  and final states (a ``[box <name>]`` section header selects this style)::

    start: S
    [box S]
    start: 0
    final: 2, 3
    0 --a--> 1
    1 --b--> 2
    1 --c--> 3
    [box B]
    start: 0
    final: 1
    0 --x--> 1

In both styles an optional ``start: <N>`` line names the start box (``S`` by
default). Boxes are deterministic — a repeated ``(state, label)`` transition
is an error. :obj:`rsa_to_text
<flpq_data.queries.rpq.readwrite.rsa.rsa_to_text>` emits the EBNF style as the
canonical form — each body is the canonical regular expression of the box's
language, and a ``start:`` line when the initial box is not the default
``S`` — so a transition-system file round-trips to EBNF-style text and
``rsa_from_text(rsa_to_text(rsa))`` preserves the language of every box and
the initial box.

Placement
^^^^^^^^^

``.rsm`` representation files are allowed in the ``queries/cfpq/`` and
``queries/rpq/`` query directories of a graph archive (see
:ref:`file_structure`). In ``rpq/`` the RSM must be regular — no box
transition may be labelled by a nonterminal.

.. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
   State Machines. In: Berry G., Comon H., Finkel A. (eds) Computer Aided
   Verification. CAV 2001. Lecture Notes in Computer Science, vol 2102.
   Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
.. [2] Abzalov V., Pogozhelskaya V., Kutuev V., Grigorev S. (2023) GLL-based
   Context-Free Path Querying for Neo4j. arXiv:2312.11925.

Multiple context-free languages
-------------------------------

MCFPQ constraints are multiple context-free languages (MCFLs), generated by
multiple context-free grammars (MCFGs)
(`Seki et al., 1991 <https://doi.org/10.1016/0304-3975(91)90374-B>`_). An
MCFL is a class of languages strictly wider than the context-free languages:
an MCFG performs simultaneous context-free parsing on several substrings of a
word and can thus express bounded context-sensitivity between them. MCFLs are
mildly context-sensitive: membership is decidable, and the classes form an
infinite hierarchy parameterized by two integers.

A multiple context-free grammar of dimension :math:`d` and rank :math:`r`,
written :math:`d`-MCFG(:math:`r`), is a tuple
:math:`\mathcal{G} = (\mathcal{N}, \Sigma, \mathcal{R}, \mathcal{S})`:

- :math:`\mathcal{N}` — nonterminals, each denoted as a predicate
  :math:`A(x_1, \dots, x_k)` of arity :math:`k \leq d`;
- :math:`\Sigma` — terminals;
- :math:`\mathcal{R}` — rules. A *basic rule* is a nonterminal
  :math:`A(s_1, \dots, s_k)` with each :math:`s_i` a string of terminals
  (possibly empty). A *production rule* has the form

  .. math::

     A_0(s_1, \dots, s_{k_0}) \leftarrow
     A_1(x_1^1, \dots, x_{k_1}^1), \dots, A_\ell(x_1^\ell, \dots, x_{k_\ell}^\ell)

  with :math:`\ell \leq r`, each head template
  :math:`s_i \in (\Sigma \cup X)^*` over the rule's variables
  :math:`X = \{x_j^i\}`, and each variable appearing at most once in
  :math:`s_1 \cdots s_{k_0}`;
- :math:`\mathcal{S}` — the start nonterminal, of arity 1.

A nonterminal of arity :math:`k` derives a *tuple* of :math:`k` strings
simultaneously; the language of the grammar is
:math:`\mathcal{L}(\mathcal{G}) = \{w \in \Sigma^* : \mathcal{S} \Rightarrow w\}`.

The hierarchy contains the familiar classes as special levels: context-free
languages are exactly the 1-MCFLs, and tree adjoining languages (and head
languages) fall in dimension 2. Membership of a word of length :math:`n` is
decidable in :math:`O(n^{d(r+1)})` time.

In the path-querying setting, MCFL reachability generalizes CFPQ directly
(`Conrado et al., POPL 2025 <https://arxiv.org/abs/2411.06383>`_,
`ACM <https://dl.acm.org/doi/10.1145/3704854>`_). On a labeled graph, an
arity-:math:`k` nonterminal denotes :math:`k` independent paths:
:math:`A[(u_1, v_1), \dots, (u_k, v_k)]` holds iff there exist paths
:math:`P_i : u_i \leadsto v_i` such that
:math:`A \Rightarrow (\lambda(P_1), \dots, \lambda(P_k))`. Because the start
symbol always has arity 1, the reachable *pairs*
:math:`\{(u, v) : \mathcal{S}[(u, v)]\}` are defined exactly as for CFPQ, so
the reference-answer data of this dataset extends to MCFPQ without changing
its meaning. All-pairs reachability is computable in
:math:`O(n^{2d+1})` time for :math:`r = 1` and
:math:`O(n^{d(r+1)})` for :math:`r > 1`. The paper's motivating application
is static program analysis: the MCFLs underapproximate interleaved Dyck
reachability — the undecidable language behind combined call-context and
field sensitivity — with tunable precision as the dimension grows.

MCFG grammar format (.mcfg)
---------------------------

MCFPQ grammars are stored in text files with the ``.mcfg`` extension, one
rule per line, in a Datalog-like syntax that follows the predicate notation
of `Conrado et al. <https://arxiv.org/abs/2411.06383>`_. The syntax was
chosen deliberately: it reads like logic-programming rules, it subsumes CFGs
as the dimension-1 special case, and it matches the formalism used by the
reachability literature.

Lexical conventions
^^^^^^^^^^^^^^^^^^^

- Blank lines and lines starting with ``#`` are ignored.
- **Nonterminals** — identifiers starting with an uppercase letter
  (``S``, ``A``, ``P1``), consistent with the CFG convention of this
  dataset.
- **Terminals** — edge labels verbatim (``0``, ``#``, ``subClassOf``,
  ``load_5``).
- **Variables** — a lowercase letter followed by one or more digits
  (``x1``, ``y2``, ...), mirroring the :math:`x^i`, :math:`y^j` notation of
  the literature. A terminal must never match this pattern; the reader
  rejects such grammars.
- **Empty string** — the token ``eps``.
- **Arrow** — ``<-`` between the head and the body of a production rule.

Rule forms
^^^^^^^^^^

A *basic rule* names a nonterminal with terminal-string arguments, each
argument a space-separated sequence of terminals or ``eps``::

   A(eps, eps)

A *production rule* has a head — a nonterminal whose arguments are
templates mixing terminals and variables — and a body of comma-separated
atoms carrying variables only::

   S(x1 y1 # y2 x2) <- A(x1, x2), A(y1, y2)

Validation constraints
^^^^^^^^^^^^^^^^^^^^^^

The reader enforces, beyond parsing:

- **Arity consistency** — every occurrence of a nonterminal carries the
  same number of arguments.
- **Variable uniqueness** — all body variables of a rule are pairwise
  distinct.
- **No dangling variables** — each body variable appears exactly once
  across the head templates (stricter than the minimal definition, which
  allows at most one appearance; every published example satisfies the
  stricter form).
- **Start symbol** — defaults to ``S``, must have arity 1, and is
  overridable via an API parameter, consistent with the existing
  ``cnf``/``cfg``/``rsa`` readers.

The dimension :math:`d` (maximum nonterminal arity) and the rank :math:`r`
(maximum number of body atoms) are computed from the rules and reported by
the reader; the file carries no header to keep in sync.

Examples
^^^^^^^^

The 2-MCFG(2) for :math:`\mathcal{L} = \{w_1 w_2 \# w_2 w_1 \mid
w_1, w_2 \in \{0, 1\}^*\}` from the literature (``A`` parses equal pairs of
binary strings; ``S`` interleaves two such pairs around ``#``)::

   A(eps, eps)
   A(x1 0, x2 0) <- A(x1, x2)
   A(x1 1, x2 1) <- A(x1, x2)
   S(x1 y1 # y2 x2) <- A(x1, x2), A(y1, y2)

The same format subsumes CFGs: the dimension-1 grammar for
:math:`\{0^n 1^n 1^m 0^m \mid n, m \geq 0\}`::

   A(eps)
   B(eps)
   A(0 x1 1) <- A(x1)
   B(1 x2 0) <- B(x2)
   S(x1 x2) <- A(x1), B(x2)

Parser and relationship to existing formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No off-the-shelf library parses this syntax: the PyPI ``datalog`` package is
a hardware data-logger driver, ``pyDatalog`` is a Datalog engine without a
documented text parser (and standard Datalog heads take variables and
constants only, so MCFG head templates are outside its grammar), and no
MCFG/MCFL library exists on PyPI. The reader therefore uses `lark
<https://github.com/lark-parser/lark>`_ (MIT license, actively maintained,
no required dependencies); its EBNF grammar doubles as executable
documentation of the format, and the semantic constraints above are checked
on the parse tree.

Existing formats are kept: CFPQ queries stay ``.cnf`` (the pyformlang
ecosystem), RPQ queries are regular-expression ``.re`` text files, and
MCFPQ uses ``.mcfg``; all of them live inside the self-contained graph
archives (see "Dataset layout and migration" below). A ``.cnf <-> .mcfg``
converter is a follow-up task.

Site structure
--------------

The Dataset section has one sub-section per query class next to the shared
graph catalog: each class reuses the existing layout — an index page with its
"Applicable graphs" list, plus one page per named template where the class
has them — while the graph catalog stays shared. RPQ has no named templates:
its queries are per-graph regular expressions documented on the per-graph
pages.

.. code-block:: text

   Dataset
   ├── Graphs           shared catalog (9 categories, 115 pages)
   ├── CFPQ             grammar templates (4 + indexed grammars) | applicable graphs
   ├── RPQ              per-graph queries (regular expressions)  | applicable graphs
   ├── MCFPQ            grammar templates (MCFG)                 | applicable graphs
   └── Reachable pairs  per-graph tables; flat CSV download

There is no separate benchmarks section: benchmarking data and results are
not part of the dataset site. The per-class "applicable graphs" lists are
rendered from the reachable-pairs registry (``reachable_pairs.csv``) by a
``utils/`` generator and cross-link the shared per-graph pages — no graph page
is duplicated. The sidebar navigation depth (``navigation_depth = 3`` in
``docs/conf.py``) accommodates the section -> class -> template pages without
change.

Reachable pair counts
^^^^^^^^^^^^^^^^^^^^^

The single flat table currently rendered on the
:ref:`reachable pairs <reachable_pairs>` page is removed; it is too large to
scan. The page renders one table per graph instead (columns: Query,
Reachable pairs; one row per query, grouped by category), so every table
stays small. The flat table survives as a downloadable CSV — the single
source of truth for automatic processing — which gains a ``category`` and a
``query_class`` column so it is self-describing. A generator script in
``utils/`` (following the pattern of ``utils/archive_sizes.py``) renders
both the per-graph tables and the count columns of the category pages from
that CSV, so no count is hand-maintained in two places.

Package structure
-----------------

The package is renamed from ``cfpq_data`` to ``flpq_data`` (PyPI
distribution ``flpq-data``) at version 6.0.0, and the grammar module gains
the same query-class level as the site::

   flpq_data/
   ├── config.py        version
   ├── dataset/         registry + metadata API, machine-global cache with lazy access (graph_dir), reachable pairs
    ├── graphs/          class-agnostic I/O (mtx/rdf/txt), streaming format conversion, generators, utils
   └── queries/         renamed from grammars/
       ├── cfpq/        existing generators/, readwrite/{cfg,cnf,cnf_template}, converters/, utils/
       ├── rpq/         readwrite/{regex,rsa} moved here; new regex-template generators
       └── mcfpq/       new lark-based mcfg readwrite; generators

API changes
^^^^^^^^^^^

- ``download(name)`` becomes ``graph_dir(name)`` and returns the
  self-contained directory — the graph plus its ``queries/`` tree — from the
  machine-global cache, downloading only on a miss (see "Core API: metadata,
  lazy access, and cache"); ``download_graph(name)`` and ``download(name)``
  stay as deprecated aliases;
- ``download_grammars(template, graph_name=None)`` is deprecated: queries
  come with the graph archive (the example archives it downloaded for
  ``graph_name=None`` are dropped);
- the old names stay in ``flpq_data`` as deprecated aliases;
- the graph registry list is replaced by the per-graph ``registry.json``
  and the ``graph_names()`` function (see "Core API: metadata, lazy access,
  and cache"), and ``GRAMMAR_TEMPLATES`` becomes the per-class
  ``CFPQ_TEMPLATES`` / ``RPQ_TEMPLATES`` / ``MCFPQ_TEMPLATES`` — they name
  the query files inside the archives, not downloadable archives;
- ``reachable_pairs()`` gains the category and query_class fields.

Distribution
^^^^^^^^^^^^

The new PyPI project ``flpq-data`` carries version 6.0.0. The existing
``cfpq-data`` distribution is published at 6.0.0 as a thin shim that
depends on ``flpq-data`` and re-exports the old names with
``DeprecationWarning``, so scripts importing ``cfpq_data`` keep working
through one more release.

Dataset layout and migration
----------------------------

The dataset on object storage moves to the 6.0.0 key prefix::

    6.0.0/
    └── graph/<name>.tar.gz                self-contained — repackaged from 5.0.0

Graphs are large and class-agnostic, so they live under one shared prefix.
Queries no longer have their own archives: every graph archive is
self-contained and carries all queries that apply to the graph — the layout
is documented once in :ref:`file_structure` (``README.md``, ``graph/*.mtx``,
and ``queries/{cfpq,rpq,mcfpq}/`` with one directory per query — its
representations plus a ``results.mtx`` — and a common description document).

Migration path:

- Repackage every graph archive into the self-contained structure: move the
  per-graph grammars from the legacy ``4.0.0/grammar/`` archives into one
  ``queries/cfpq/<query>/`` directory each, add the per-query
  ``results.mtx`` (the constrained reachability facts), write the
  mandatory-question ``README.md``, and validate with
  ``flpq-check-archive`` (:ref:`archive_structure`).
- The example query archives (``4.0.0/grammar/example/``) are dropped —
  every query file lives inside a graph archive.
- Re-point ``DATASET_URL`` at the new prefix as part of the version bump
  (the rename task); ``GRAMMARS_URL`` disappears with the separate grammar
  archives.
- The upload tool validates the structure before uploading
  (:ref:`upload_to_s3`, :ref:`archive_structure`).

Core API: metadata, lazy access, and cache
------------------------------------------

The package core is for end users — dataset utilisation for benchmarks and
statistical analysis. Dataset maintenance (archive validation, upload, merge,
registry generation) lives in the repo-only ``utils/`` scripts and is never
installed with the wheel; nothing in ``flpq_data/`` performs maintenance
work, and the maintenance scripts consume the package as a library. This
design responds to #140 (the graph archive was re-downloaded on every call)
and #147 (no way to get the category of a graph from the package); it is
tracked in hub issue #148.

Graph registry
^^^^^^^^^^^^^^

``flpq_data/dataset/registry.json`` is the machine-readable per-graph
registry, bundled with the wheel for the current dataset version and
published to object storage as ``<version>/registry.json``::

   { "version": "6.0.0",
     "graphs": { "skos": { "category": "rdf", "num_nodes": 144,
                           "num_edges": 252, "size_mb": 0.003,
                           "sha256": "...",
                           "queries": [ {"class": "cfpq",
                                         "name": "nested_parentheses_subClassOf",
                                         "representations": ["cnf", "rsm"]} ] } } }

Field sources: the graph list and ``category`` from
``reachable_pairs.csv``; ``num_nodes``/``num_edges`` from the MTX headers of
the archive's ``graph/`` dir; ``size_mb`` from the stored object size;
``sha256`` of the ``.tar.gz``; ``queries`` from the archive's ``queries/``
tree. The repo-only ``utils/generate_registry.py`` (pattern of
``utils/archive_sizes.py``) regenerates the file; it runs locally, never in
CI (no-network policy).

The metadata API never touches the network: ``graph_names() ->
list[str]`` (named to avoid clashing with the ``flpq_data.graphs``
subpackage),
``graph_info(name) -> GraphInfo`` (a frozen dataclass mirroring one registry
record), and ``categories() -> dict[str, list[str]]`` — the category-to-
graphs mapping of #147. The never-released ``GRAPHS``/``DATASET`` constants
are dropped; the future ``cfpq-data`` shim maps ``DATASET ->
graph_names()``.

Machine-global cache
^^^^^^^^^^^^^^^^^^^^

Downloaded data lives outside the package in a machine-global, per-user
cache shared across projects: the ``FLPQ_DATA_CACHE`` environment variable,
or the OS default from ``platformdirs.user_cache_dir("flpq-data")`` when it
is unset (``~/.cache/flpq-data`` on Linux, ``~/Library/Caches/flpq-data`` on
macOS, ``%LOCALAPPDATA%\flpq-data\Cache`` on Windows). The in-package data
dir (the old ``config.DATA``/``GRAPHS_DIR``) is removed.

The cache mirrors the dataset layout; the dataset version is the root, so
several versions coexist::

   <root>/6.0.0/
   ├── reachable_pairs.csv
   └── graph/<name>/<name>.tar.gz   plus the unpacked contents in the same
                                     folder (README.md, graph/*.mtx, queries/)

Lazy access
^^^^^^^^^^^

``graph_dir(name)`` is the single data accessor and is lazy: it returns the
local graph folder and downloads only when the cache is missing or invalid.

- The name is validated against the bundled registry.
- Hit: ``<root>/<v>/graph/<name>/`` exists and the archive's sha256 (sidecar
  ``.sha256`` written at install) matches the registry — return the path,
  zero network. ``verify=True`` re-hashes the archive instead of trusting
  the sidecar.
- Miss: download to a temp file (``raise_for_status``), stream-verify the
  sha256 against the registry, extract, check the single top-level dir, and
  move the folder into the cache atomically; any failure leaves the cache
  untouched.

``download_graph``/``download`` remain as deprecated aliases of
``graph_dir``. ``reachable_pairs.csv`` resolves to the per-version cache copy
when present, else the bundled file; ``download_reachable_pairs()`` writes
into the cache.

Cache manipulation
^^^^^^^^^^^^^^^^^^

- ``cache_root() -> Path`` — the effective cache root (env var or OS
  default).
- ``cached_versions() -> list[str]`` — dataset versions present in the
  cache.
- ``clear_cache(keep: str | None = None)`` — remove version directories under
  the root except ``keep`` (``None`` removes all); returns the removed
  paths.
