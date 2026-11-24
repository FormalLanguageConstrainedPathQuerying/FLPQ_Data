.. _reachable_pairs:

***********************
Reachable Pair Counts
***********************

.. only:: html

   :Release: |release|
   :Date: |today|

Reference counts of reachable vertex pairs for every graph x grammar pair
in the dataset. A pair :math:`(u, v)` is reachable if there exists a path
from :math:`u` to :math:`v` labeled by a string in the language of the
grammar's start symbol. The sections below follow the graph categories of
the :ref:`Graphs <graphs>` catalog; within a category, each graph gets its
own table with one row per query (the grammar file name makes the query
class self-describing).

.. note::

   Values marked "not available" have not been computed yet. The count is
   a property of the graph and grammar only; it does not depend on the
   algorithm or environment used to compute it.

Download
--------

The full table is available as a CSV file. It ships with the package
(``REACHABLE_PAIRS_CSV``), so the API works offline, and is republished —
versioned — on the dataset object storage at
``https://cfpq-data.storage.yandexcloud.net/<major>.0.0/reachable_pairs.csv``.

- **Package API**: ``from flpq_data.dataset import reachable_pairs, REACHABLE_PAIRS_CSV``.
  :func:`flpq_data.dataset.download_reachable_pairs` fetches the versioned copy
  from the object storage into the local data cache; once downloaded,
  :func:`flpq_data.dataset.reachable_pairs` reads it instead of the bundled
  table, so a table updated on the storage is used without reinstalling.
- **CSV file**: `reachable_pairs.csv <https://cfpq-data.storage.yandexcloud.net/6.0.0/reachable_pairs.csv>`_

Columns: ``graph``, ``grammar``, ``category``, ``query_class`` (one of
``cfpq``, ``rpq``, ``mcfpq`` — the names of the ``queries/<class>/``
directories in the graph archives), ``num_reachable_pairs`` (empty when not
yet available).

.. reachable-pairs-tables:begin

C alias analysis
----------------

:ref:`apache`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 92806768

:ref:`arch`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5339563

:ref:`block`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5351409

:ref:`bzip`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 315

:ref:`crypto`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5428237

:ref:`drivers`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 18825025

:ref:`fs`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 9646475

:ref:`gzip`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 1458

:ref:`init`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 3783769

:ref:`ipc`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5249389

:ref:`kernel`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 16747731

:ref:`lib`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5276303

:ref:`ls`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 854

:ref:`mm`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 3990305

:ref:`net`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 8833403

:ref:`postgre`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 90661446

:ref:`pr`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 385

:ref:`security`
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 5593387

:ref:`sound`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 6085269

:ref:`wc`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - c_alias.cnf
     - 156

RDF
---

:ref:`atom`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 2
   * - nested_parentheses_subClassOf_type.cnf
     - 6
   * - nested_parentheses_type.cnf
     - 4

:ref:`biomedical`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 43
   * - nested_parentheses_subClassOf_type.cnf
     - 47
   * - nested_parentheses_type.cnf
     - 4

:ref:`core`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 143
   * - nested_parentheses_subClassOf_type.cnf
     - 204
   * - nested_parentheses_type.cnf
     - 61

:ref:`eclass`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 90988
   * - nested_parentheses_subClassOf_type.cnf
     - 90994
   * - nested_parentheses_type.cnf
     - 6

:ref:`enzyme`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_broaderTransitive.cnf
     - 14267542
   * - nested_parentheses_subClassOf.cnf
     - 394
   * - nested_parentheses_subClassOf_type.cnf
     - 396
   * - nested_parentheses_type.cnf
     - 3

:ref:`foaf`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 7
   * - nested_parentheses_subClassOf_type.cnf
     - 36
   * - nested_parentheses_type.cnf
     - 29

:ref:`funding`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 27
   * - nested_parentheses_subClassOf_type.cnf
     - 58
   * - nested_parentheses_type.cnf
     - 31

:ref:`generations`
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 0
   * - nested_parentheses_subClassOf_type.cnf
     - 12
   * - nested_parentheses_type.cnf
     - 12

:ref:`geospecies`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_broaderTransitive.cnf
     - 226669749
   * - nested_parentheses_subClassOf.cnf
     - 0
   * - nested_parentheses_subClassOf_type.cnf
     - 85
   * - nested_parentheses_type.cnf
     - 85

:ref:`go`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 640305
   * - nested_parentheses_subClassOf_type.cnf
     - 640316
   * - nested_parentheses_type.cnf
     - 9

:ref:`go_hierarchy`
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 588976
   * - nested_parentheses_subClassOf_type.cnf
     - 588976
   * - nested_parentheses_type.cnf
     - 0

:ref:`pathways`
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 883
   * - nested_parentheses_subClassOf_type.cnf
     - 884
   * - nested_parentheses_type.cnf
     - 2

:ref:`people`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 24
   * - nested_parentheses_subClassOf_type.cnf
     - 51
   * - nested_parentheses_type.cnf
     - 29

:ref:`pizza`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 1334
   * - nested_parentheses_subClassOf_type.cnf
     - 1356
   * - nested_parentheses_type.cnf
     - 20

:ref:`skos`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 1
   * - nested_parentheses_subClassOf_type.cnf
     - 30
   * - nested_parentheses_type.cnf
     - 29

:ref:`taxonomy`
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 151703
   * - nested_parentheses_subClassOf_type.cnf
     - 151706
   * - nested_parentheses_type.cnf
     - 4

:ref:`taxonomy_hierarchy`
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 5351657
   * - nested_parentheses_subClassOf_type.cnf
     - 5351657
   * - nested_parentheses_type.cnf
     - 0

:ref:`travel`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 33
   * - nested_parentheses_subClassOf_type.cnf
     - 52
   * - nested_parentheses_type.cnf
     - 19

:ref:`univ`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 17
   * - nested_parentheses_subClassOf_type.cnf
     - 25
   * - nested_parentheses_type.cnf
     - 6

:ref:`wine`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - nested_parentheses_subClassOf.cnf
     - 499
   * - nested_parentheses_subClassOf_type.cnf
     - 565
   * - nested_parentheses_type.cnf
     - 65

Java points-to graphs
---------------------

:ref:`avrora`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 21532

:ref:`batik`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 45968

:ref:`commons_io`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 24020

:ref:`commons_lang3`
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 27553

:ref:`eclipse`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 21830

:ref:`fop`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 76615

:ref:`gson`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 56325

:ref:`guava`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 26384496

:ref:`h2`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 92038

:ref:`jackson`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 3108775

:ref:`junit5`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 129598

:ref:`jython`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 561720

:ref:`luindex`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 9677

:ref:`lusearch`
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 9242

:ref:`mockito`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 16169

:ref:`pmd`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 60518

:ref:`sunflow`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 16354

:ref:`tomcat`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 82424

:ref:`tradebeans`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 696316

:ref:`tradesoap`
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 698567

:ref:`xalan`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - java_points_to.cnf
     - 52382

Field-Sensitive Alias
---------------------

:ref:`cactus_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 37625324

:ref:`imagick_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 369956094

:ref:`leela_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 3968276

:ref:`nab_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 262566

:ref:`omnetpp_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 158255766

:ref:`parest_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 49415038

:ref:`perlbench_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 851737865

:ref:`povray_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 27219043

:ref:`x264_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 5246565

:ref:`xz_field_sensitive_alias`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - vf.cnf
     - 205164

Context-Sensitive Data-Flow
---------------------------

:ref:`cactus`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 47806209

:ref:`imagick`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 12687034

:ref:`leela`
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 662466

:ref:`nab`
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 739646

:ref:`omnetpp`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 8424500

:ref:`parest`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 1342540

:ref:`perlbench`
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 297504186

:ref:`povray`
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 34599413

:ref:`x264`
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 20259480

:ref:`xz`
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - aa.cnf
     - 358834

Data Provenance
---------------

:ref:`provenance_airflow`
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 91350

:ref:`provenance_celery`
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 25306

:ref:`provenance_click`
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 2710

:ref:`provenance_django`
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 615946

:ref:`provenance_fastapi`
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 8814

:ref:`provenance_flask`
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 8062

:ref:`provenance_httpx`
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 4408

:ref:`provenance_itsdangerous`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 2912

:ref:`provenance_jinja`
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 7436

:ref:`provenance_pandas`
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 154646

:ref:`provenance_pluggy`
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 880

:ref:`provenance_requests`
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 2524

:ref:`provenance_sampleproject`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 342

:ref:`provenance_scikit_learn`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 217728

:ref:`provenance_sphinx`
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 304084

:ref:`provenance_superset`
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 97460

:ref:`provenance_wikipedia_provenance`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 1732

:ref:`provenance_zulip`
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - prov_derivation.cnf
     - 209908

Name Resolution
---------------

:ref:`name_resolution_jiaozi`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - name_resolution.cnf
     - 14435

:ref:`name_resolution_jsonpath`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - name_resolution.cnf
     - 59764

:ref:`name_resolution_libgdx`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - name_resolution.cnf
     - not available

:ref:`name_resolution_shattered_pixel_dungeon`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - name_resolution.cnf
     - 971998

Biological graphs from UniProt
------------------------------

:ref:`unigraph_1`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_1.cnf
     - 376578

:ref:`unigraph_10`
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_10.cnf
     - not available

:ref:`unigraph_2`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_2.cnf
     - 39888347

:ref:`unigraph_3`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_3.cnf
     - 52471840

:ref:`unigraph_4`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_4.cnf
     - 808091802

:ref:`unigraph_5`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_5.cnf
     - 2303590109

:ref:`unigraph_6`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_6.cnf
     - 1722963921

:ref:`unigraph_7`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_7.cnf
     - 2320964134

:ref:`unigraph_8`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_8.cnf
     - not available

:ref:`unigraph_9`
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - unigraph_9.cnf
     - not available

.. reachable-pairs-tables:end
