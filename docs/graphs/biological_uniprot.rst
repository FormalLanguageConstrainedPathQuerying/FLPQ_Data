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

.. graph-table:begin

.. list-table::

   * - Graph
     - Num Nodes
     - Num Edges
     - Reachable pairs
     - Size (MB)
     - Download
   * - :ref:`unigraph_1`
     - 3082
     - 6033
     - 376578
     - 0.972
     - `unigraph_1.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_1.tar.gz>`_ 📥
   * - :ref:`unigraph_2`
     - 36468
     - 88353
     - 39888347
     - 106.10
     - `unigraph_2.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_2.tar.gz>`_ 📥
   * - :ref:`unigraph_3`
     - 41333
     - 101718
     - 52471840
     - 138.87
     - `unigraph_3.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_3.tar.gz>`_ 📥
   * - :ref:`unigraph_4`
     - 215481
     - 691906
     - 808091802
     - 2163.03
     - `unigraph_4.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_4.tar.gz>`_ 📥
   * - :ref:`unigraph_5`
     - 243839
     - 942263
     - 2303590109
     - 6007.86
     - `unigraph_5.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_5.tar.gz>`_ 📥
   * - :ref:`unigraph_7`
     - 285577
     - 1069173
     - 2320964134
     - 6098.27
     - `unigraph_7.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_7.tar.gz>`_ 📥
   * - :ref:`unigraph_6`
     - 286645
     - 881565
     - 1722963921
     - 4603.69
     - `unigraph_6.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_6.tar.gz>`_ 📥
   * - :ref:`unigraph_8`
     - 449237
     - 1749604
     - not available
     - 5.72
     - `unigraph_8.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_8.tar.gz>`_ 📥
   * - :ref:`unigraph_9`
     - 475479
     - 1851322
     - not available
     - 6.10
     - `unigraph_9.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_9.tar.gz>`_ 📥
   * - :ref:`unigraph_10`
     - 2055882
     - 8948375
     - not available
     - 29.27
     - `unigraph_10.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/unigraph_10.tar.gz>`_ 📥

.. graph-table:end

Canonical grammars
------------------

The grammar file is attached to the archive.

.. math::

   \begin{aligned}
   S &\to Seq \quad IsAssociated \quad IsSimilar \\
   Seq &\to IsSimilar \quad (codes\_for \quad IsSimilar)? \\
   IsSimilar &\to \varepsilon \\
             &\mid has \quad IsSimilar \quad has_{r} \\
             &\mid is\_homologous\_to \quad IsSimilar \quad is\_homologous\_to_{r} \quad IsSimilar \\
             &\mid belongs\_to \quad IsSimilar \quad belongs\_to_{r} \\
             &\mid participate\_in \quad IsSimilar \quad participate\_in_{r} \\
   IsAssociated &\to refers\_to \quad refers\_to_{r}
   \end{aligned}
