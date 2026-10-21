.. _graphs_name_resolution:

Name Resolution
***************

.. only:: html

   :Release: |release|
   :Date: |today|

Stack graphs capturing the scoping structure of source code for name
resolution, as in `"Stack Graphs: Name Resolution at Scale" <https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.EVCS.2023.8>`_. Edges are the
stack-graph transitions (push, pop, branch, epsilon) that carry names through
scopes.

.. toctree::
   :hidden:

   data/name_resolution_jiaozi
   data/name_resolution_jsonpath
   data/name_resolution_shattered_pixel_dungeon
   data/name_resolution_libgdx

.. list-table::

   * - Graph
     - Num Nodes
     - Num Edges
     - Reachable pairs
     - Size (MB)
     - Download
   * - :ref:`name_resolution_jiaozi`
     - 54952
     - 46322
     - 14435
     - 0.252
     - `jiaozi.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/jiaozi.tar.gz>`_ 📥
   * - :ref:`name_resolution_jsonpath`
     - 185421
     - 161488
     - 59764
     - 1.03
     - `jsonpath.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/jsonpath.tar.gz>`_ 📥
   * - :ref:`name_resolution_shattered_pixel_dungeon`
     - 1179205
     - 1017798
     - 971998
     - 5.13
     - `shattered_pixel_dungeon.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/shattered_pixel_dungeon.tar.gz>`_ 📥
   * - :ref:`name_resolution_libgdx`
     - 2571363
     - 2321366
     - not available
     - 11.54
     - `libgdx.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/libgdx.tar.gz>`_ 📥

Canonical grammars
------------------

The grammar file is attached to the archive.

.. math::

   S &\to \varepsilon \\
     &\mid eps \quad S \\
     &\mid Q \quad S \\
     &\mid V \quad S \\
   S\#psh_{i} &\to psh_{i} \quad S \\
   S\#vpsh_{i} &\to vpsh_{i} \quad S \\
   V &\to S\#vpsh_{i} \quad vpp_{i} \\
   Q &\to S\#psh_{i} \quad pp_{i}
