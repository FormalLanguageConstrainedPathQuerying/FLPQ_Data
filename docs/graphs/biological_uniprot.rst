.. _graphs_biological_uniprot:

Biological graphs from UniProt
******************************

.. only:: html

   :Release: |release|
   :Date: |today|

Biological interaction graphs derived from the UniProt knowledgebase, where
nodes are biological entities and edges are the relations between them (e.g.
``belongs_to``, ``is_homologous_to``); they support subgraph and path queries
as in `"Subgraph queries by context-free grammars" <https://researchportal.helsinki.fi/en/publications/subgraph-queries-by-context-free-grammars/>`_.

.. toctree::
   :hidden:

   data/unigraph_1
   data/unigraph_2
   data/unigraph_3
   data/unigraph_4
   data/unigraph_5
   data/unigraph_6
   data/unigraph_7
   data/unigraph_8
   data/unigraph_9
   data/unigraph_10

.. list-table::

   * - Graph
     - Num Nodes
     - Num Edges
     - Reachable pairs
     - Size (MB)
     - Download
   * - :ref:`unigraph_1`
     - 3082
     - 11966
     - 376578
     - 0.972
     - `unigraph_1.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_1.tar.gz>`_ 📥
   * - :ref:`unigraph_2`
     - 36468
     - 168344
     - 39888347
     - 0.300
     - `unigraph_2.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_2.tar.gz>`_ 📥
   * - :ref:`unigraph_3`
     - 41333
     - 193866
     - 52471840
     - 0.344
     - `unigraph_3.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_3.tar.gz>`_ 📥
   * - :ref:`unigraph_4`
     - 215481
     - 1346130
     - 808091802
     - 2.25
     - `unigraph_4.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_4.tar.gz>`_ 📥
   * - :ref:`unigraph_5`
     - 243839
     - 1818404
     - 2303590109
     - 3.15
     - `unigraph_5.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_5.tar.gz>`_ 📥
   * - :ref:`unigraph_6`
     - 286645
     - 1708910
     - 1722963921
     - 2.94
     - `unigraph_6.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_6.tar.gz>`_ 📥
   * - :ref:`unigraph_7`
     - 285577
     - 2073268
     - 2320964134
     - 3.47
     - `unigraph_7.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_7.tar.gz>`_ 📥
   * - :ref:`unigraph_8`
     - 449237
     - 3385168
     - not available
     - 5.72
     - `unigraph_8.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_8.tar.gz>`_ 📥
   * - :ref:`unigraph_9`
     - 475479
     - 3579034
     - not available
     - 6.10
     - `unigraph_9.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_9.tar.gz>`_ 📥
   * - :ref:`unigraph_10`
     - 2055882
     - 17223588
     - not available
     - 29.27
     - `unigraph_10.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_10.tar.gz>`_ 📥

Canonical grammars
------------------

The grammar file is attached to the archive.

.. math::

   S &\to Seq \quad IsAssociated \quad IsSimilar \\
   Seq &\to IsSimilar \quad (codes\_for \quad IsSimilar)? \\
   IsSimilar &\to \varepsilon \\
             &\mid has \quad IsSimilar \quad has_{r} \\
             &\mid is\_homologous\_to \quad IsSimilar \quad is\_homologous\_to_{r} \quad IsSimilar \\
             &\mid belongs\_to \quad IsSimilar \quad belongs\_to_{r} \\
             &\mid participate\_in \quad IsSimilar \quad participate\_in_{r} \\
   IsAssociated &\to refers\_to \quad refers\_to_{r}
