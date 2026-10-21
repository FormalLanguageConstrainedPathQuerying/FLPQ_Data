.. _graphs_c_alias_analysis:

C alias analysis
****************

.. only:: html

   :Release: |release|
   :Date: |today|

Points-to (alias) graphs for a suite of C programs, built by demand-driven
alias analysis as in `"Demand-driven alias analysis for C" <https://dl.acm.org/doi/10.1145/1328897.1328464>`_.
Nodes are program entities and edges are the aliasing and flow relations
discovered for each program.

.. toctree::
   :hidden:

   data/wc
   data/bzip
   data/pr
   data/ls
   data/gzip
   data/apache
   data/init
   data/mm
   data/ipc
   data/lib
   data/block
   data/arch
   data/crypto
   data/security
   data/sound
   data/net
   data/fs
   data/drivers
   data/postgre
   data/kernel

.. list-table::

   * - Graph
     - Num Nodes
     - Num Edges
     - Reachable pairs
     - Size (MB)
     - Download
   * - :ref:`wc`
     - 332
     - 269
     - 156
     - 0.003
     - `wc.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/wc.tar.gz>`_ 📥
   * - :ref:`bzip`
     - 632
     - 556
     - 315
     - 0.005
     - `bzip.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/bzip.tar.gz>`_ 📥
   * - :ref:`pr`
     - 815
     - 692
     - 385
     - 0.006
     - `pr.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pr.tar.gz>`_ 📥
   * - :ref:`ls`
     - 1687
     - 1453
     - 854
     - 0.011
     - `ls.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/ls.tar.gz>`_ 📥
   * - :ref:`gzip`
     - 2687
     - 2293
     - 1458
     - 0.017
     - `gzip.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/gzip.tar.gz>`_ 📥
   * - :ref:`apache`
     - 1721418
     - 1510411
     - 92806768
     - 9.05
     - `apache.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/apache.tar.gz>`_ 📥
   * - :ref:`init`
     - 2446224
     - 2112809
     - 3783769
     - 12.84
     - `init.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/init.tar.gz>`_ 📥
   * - :ref:`mm`
     - 2538243
     - 2191079
     - 3990305
     - 13.33
     - `mm.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/mm.tar.gz>`_ 📥
   * - :ref:`ipc`
     - 3401022
     - 2931498
     - 5249389
     - 18.01
     - `ipc.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/ipc.tar.gz>`_ 📥
   * - :ref:`lib`
     - 3401355
     - 2931880
     - 5276303
     - 18.01
     - `lib.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/lib.tar.gz>`_ 📥
   * - :ref:`block`
     - 3423234
     - 2951393
     - 5351409
     - 18.14
     - `block.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/block.tar.gz>`_ 📥
   * - :ref:`arch`
     - 3448422
     - 2970242
     - 5339563
     - 18.25
     - `arch.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/arch.tar.gz>`_ 📥
   * - :ref:`crypto`
     - 3464970
     - 2988387
     - 5428237
     - 18.38
     - `crypto.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/crypto.tar.gz>`_ 📥
   * - :ref:`security`
     - 3479982
     - 3003326
     - 5593387
     - 18.47
     - `security.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/security.tar.gz>`_ 📥
   * - :ref:`sound`
     - 3528861
     - 3049732
     - 6085269
     - 18.77
     - `sound.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/sound.tar.gz>`_ 📥
   * - :ref:`net`
     - 4039470
     - 3500141
     - 8833403
     - 21.66
     - `net.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/net.tar.gz>`_ 📥
   * - :ref:`fs`
     - 4177416
     - 3609373
     - 9646475
     - 22.34
     - `fs.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/fs.tar.gz>`_ 📥
   * - :ref:`drivers`
     - 4273803
     - 3707769
     - 18825025
     - 22.99
     - `drivers.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/drivers.tar.gz>`_ 📥
   * - :ref:`postgre`
     - 5203419
     - 4678543
     - 90661446
     - 29.37
     - `postgre.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/postgre.tar.gz>`_ 📥
   * - :ref:`kernel`
     - 11254434
     - 9484213
     - 16747731
     - 59.99
     - `kernel.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/kernel.tar.gz>`_ 📥

Canonical grammars
------------------

.. note::

   In order to get the original graph you must apply function :obj:`change_edges <flpq_data.graphs.utils.change_edges>` with ``mapping={"a": "A", "d": "D"}`` to this graph. In this case these grammars must be updated.

Grammars for the alias analysis of C programs introduced in `"Demand-driven alias analysis for C" <https://dl.acm.org/doi/10.1145/1328897.1328464>`_.
Template for these grammars is described on the :ref:`c_alias` page.

.. math::

   S \, \rightarrow \, d_r \, V \, d \, \\
   V \, \rightarrow \, V_1 \, V_2 \, V_3 \, \\
   V_1 \, \rightarrow \, \varepsilon \, \\
   V_1 \, \rightarrow \, V_2 \, a_r \, V_1 \, \\
   V_2 \, \rightarrow \, \varepsilon \, \\
   V_2 \, \rightarrow \, S \, \\
   V_3 \, \rightarrow \, \varepsilon \, \\
   V_3 \, \rightarrow \, a \, V_2 \, V_3 \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> d_r V d
   V -> V1 V2 V3
   V1 -> epsilon
   V1 -> V2 a_r V1
   V2 -> epsilon
   V2 -> S
   V3 -> epsilon
   V3 -> a V2 V3

----

.. math::

   S \, \rightarrow \, d_r \, V \, d \, \\
   V \, \rightarrow \, ((S \mid \varepsilon) \, a_r)^{*} \, (S \mid \varepsilon) \, (a \, (S \mid \varepsilon))^{*} \, \\

`Pyformlang RSA <https://github.com/Aunsiels/pyformlang/tree/master/pyformlang/rsa>`_:

.. code-block:: python

   S -> d_r V d
   V -> ((S|epsilon) a_r)* (S|epsilon) (a (S|epsilon))*

Optimized variant
^^^^^^^^^^^^^^^^^

An equivalent WCNF grammar introduced as optimization (5) in `"Optimization of the Context-Free Language Reachability Matrix-Based Algorithm" <https://arxiv.org/abs/2401.11029>`_ (Fig. 2(b)) is stored in each archive as ``c_alias_muravev2024.cnf``. It generates the same language and returns identical reachable-pair counts (verified with FastMatrixCFPQ on small graphs).

.. code-block:: text

   M	N1	N3
   M	N2	N3
   N1	d_r
   N1	N1	a_r
   N1	N2	a_r
   N2	N1	M
   N3	d
   N3	a	N3
   N3	AM	N3
   AM	a	M

   Count:
   M
