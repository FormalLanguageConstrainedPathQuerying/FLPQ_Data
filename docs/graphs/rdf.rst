.. _graphs_rdf:

RDF
***

.. only:: html

   :Release: |release|
   :Date: |today|

Labeled directed graphs built from RDF / OWL datasets, where nodes are
resources and edges are predicates; they support studying context-free path
queries over RDF as in `"Context-Free Path Queries on RDF Graphs" <https://arxiv.org/abs/1506.00743>`_.

.. toctree::
   :hidden:

   data/generations
   data/travel
   data/skos
   data/univ
   data/foaf
   data/atom
   data/people
   data/biomedical
   data/pizza
   data/wine
   data/funding
   data/core
   data/pathways
   data/go_hierarchy
   data/enzyme
   data/geospecies
   data/go
   data/eclass
   data/taxonomy_hierarchy
   data/taxonomy

.. list-table::

   * - Graph
     - Num Nodes
     - Num Edges
     - Reachable pairs / subClassOf
     - Reachable pairs / subClassOf_type
     - Reachable pairs / type
     - Reachable pairs / broaderTransitive
     - Size (MB)
     - Download
   * - :ref:`generations`
     - 129
     - 273
     - 0
     - 12
     - 12
     -
     - 0.003
     - `generations.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/generations.tar.gz>`_ 📥
   * - :ref:`travel`
     - 131
     - 277
     - 33
     - 52
     - 19
     -
     - 0.004
     - `travel.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/travel.tar.gz>`_ 📥
   * - :ref:`skos`
     - 144
     - 252
     - 1
     - 30
     - 29
     -
     - 0.003
     - `skos.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/skos.tar.gz>`_ 📥
   * - :ref:`univ`
     - 179
     - 293
     - 17
     - 25
     - 6
     -
     - 0.003
     - `univ.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/univ.tar.gz>`_ 📥
   * - :ref:`foaf`
     - 256
     - 631
     - 7
     - 36
     - 29
     -
     - 0.004
     - `foaf.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/foaf.tar.gz>`_ 📥
   * - :ref:`atom`
     - 291
     - 425
     - 2
     - 6
     - 4
     -
     - 0.004
     - `atom.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/atom.tar.gz>`_ 📥
   * - :ref:`people`
     - 337
     - 640
     - 24
     - 51
     - 29
     -
     - 0.005
     - `people.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/people.tar.gz>`_ 📥
   * - :ref:`biomedical`
     - 341
     - 459
     - 43
     - 47
     - 4
     -
     - 0.004
     - `biomedical.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/biomedical.tar.gz>`_ 📥
   * - :ref:`pizza`
     - 671
     - 1980
     - 1334
     - 1356
     - 20
     -
     - 0.013
     - `pizza.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pizza.tar.gz>`_ 📥
   * - :ref:`wine`
     - 733
     - 1839
     - 499
     - 565
     - 65
     -
     - 0.012
     - `wine.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/wine.tar.gz>`_ 📥
   * - :ref:`funding`
     - 778
     - 1086
     - 27
     - 58
     - 31
     -
     - 0.007
     - `funding.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/funding.tar.gz>`_ 📥
   * - :ref:`core`
     - 1323
     - 2752
     - 143
     - 204
     - 61
     -
     - 0.014
     - `core.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/core.tar.gz>`_ 📥
   * - :ref:`pathways`
     - 6238
     - 12363
     - 883
     - 884
     - 2
     -
     - 0.052
     - `pathways.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pathways.tar.gz>`_ 📥
   * - :ref:`go_hierarchy`
     - 45007
     - 490109
     - 588976
     - 588976
     - 0
     -
     - 4.97
     - `go_hierarchy.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/go_hierarchy.tar.gz>`_ 📥
   * - :ref:`enzyme`
     - 48815
     - 86543
     - 394
     - 396
     - 3
     - 14267542
     - 0.360
     - `enzyme.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/enzyme.tar.gz>`_ 📥
   * - :ref:`geospecies`
     - 450609
     - 2201532
     - 0
     - 85
     - 85
     - 226669749
     - 7.95
     - `geospecies.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/geospecies.tar.gz>`_ 📥
   * - :ref:`go`
     - 582929
     - 1437437
     - 640305
     - 640316
     - 9
     -
     - 11.23
     - `go.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/go.tar.gz>`_ 📥
   * - :ref:`eclass`
     - 239111
     - 360248
     - 90988
     - 90994
     - 6
     -
     - 2.10
     - `eclass.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/eclass.tar.gz>`_ 📥
   * - :ref:`taxonomy_hierarchy`
     - 2112625
     - 32876289
     - 5351657
     - 5351657
     - 0
     -
     - 99.65
     - `taxonomy_hierarchy.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/taxonomy_hierarchy.tar.gz>`_ 📥
   * - :ref:`taxonomy`
     - 5728398
     - 14922125
     - 151703
     - 151706
     - 4
     -
     - 59.52
     - `taxonomy.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/taxonomy.tar.gz>`_ 📥

Canonical grammars
------------------

Nested parentheses grammars introduced in `"Context-Free Path Queries on RDF Graphs" <https://arxiv.org/abs/1506.00743>`_.
Template for these grammars is described on the :ref:`nested_parentheses` page.

.. math::

   S \, \rightarrow \, subClassOf_r \, S \, subClassOf \, \mid \, subClassOf_r \, subClassOf \, \\
   S \, \rightarrow \, type_r \, S \, type \, \mid \, type_r \, type \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> subClassOf_r S subClassOf | subClassOf_r subClassOf
   S -> type_r S type | type_r type

----

.. math::

   S \, \rightarrow \, subClassOf_r \, S \, subClassOf \, \mid \, subClassOf_r \, subClassOf \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> subClassOf_r S subClassOf | subClassOf_r subClassOf

----

.. math::

   S \, \rightarrow \, type_r \, S \, type \, \mid \, type_r \, type \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> type_r S type | type_r type

----

.. math::

   S \, \rightarrow \, broaderTransitive \, S \, broaderTransitive_r \, \mid \, broaderTransitive \, broaderTransitive_r \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> broaderTransitive S broaderTransitive_r | broaderTransitive broaderTransitive_r
