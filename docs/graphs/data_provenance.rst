.. _graphs_data_provenance:

Data Provenance
***************

.. only:: html

   :Release: |release|
   :Date: |today|

Data-provenance graphs recording the lineage of data artifacts in a set of
Python projects, following the W3C PROV model (``Entity``, ``Activity``,
``wasDerivedFrom``) as studied in `"Understanding Data Science Lifecycle Provenance via Graph Segmentation and Summarization" <https://ieeexplore.ieee.org/document/8731467>`_.

.. toctree::
   :hidden:

   data/provenance_sampleproject
   data/provenance_wikipedia_provenance
   data/provenance_pluggy
   data/provenance_itsdangerous
   data/provenance_requests
   data/provenance_httpx
   data/provenance_click
   data/provenance_jinja
   data/provenance_flask
   data/provenance_fastapi
   data/provenance_celery
   data/provenance_scikit_learn
   data/provenance_sphinx
   data/provenance_pandas
   data/provenance_django
   data/provenance_zulip
   data/provenance_superset
   data/provenance_airflow

.. list-table::
   :header-rows: 1

   * - Graph
      - Num Nodes
      - Num Edges
      - Reachable pairs
      - Size (MB)
      - Download
   * - :ref:`provenance_sampleproject`
     - 148
     - 763
     - 342
     - 0.004
     - `sampleproject.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/sampleproject.tar.gz>`_ 📥
   * - :ref:`provenance_wikipedia_provenance`
     - 316
     - 1284
     - 1732
     - 0.009
     - `wikipedia-provenance.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/wikipedia-provenance.tar.gz>`_ 📥
   * - :ref:`provenance_pluggy`
     - 353
     - 1818
     - 880
     - 0.008
     - `pluggy.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pluggy.tar.gz>`_ 📥
   * - :ref:`provenance_itsdangerous`
     - 425
     - 2210
     - 2912
     - 0.014
     - `itsdangerous.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/itsdangerous.tar.gz>`_ 📥
   * - :ref:`provenance_requests`
     - 682
     - 3369
     - 2524
     - 0.016
     - `requests.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/requests.tar.gz>`_ 📥
   * - :ref:`provenance_httpx`
     - 826
     - 4247
     - 4408
     - 0.011
     - `httpx.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/httpx.tar.gz>`_ 📥
   * - :ref:`provenance_click`
     - 944
     - 4654
     - 2710
     - 0.020
     - `click.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/click.tar.gz>`_ 📥
   * - :ref:`provenance_jinja`
     - 1202
     - 6277
     - 7436
     - 0.036
     - `jinja.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/jinja.tar.gz>`_ 📥
   * - :ref:`provenance_flask`
     - 1517
     - 7728
     - 8062
     - 0.041
     - `flask.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/flask.tar.gz>`_ 📥
   * - :ref:`provenance_fastapi`
     - 6455
     - 26528
     - 8814
     - 0.094
     - `fastapi.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/fastapi.tar.gz>`_ 📥
   * - :ref:`provenance_celery`
     - 6880
     - 35874
     - 25306
     - 0.158
     - `celery.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/celery.tar.gz>`_ 📥
   * - :ref:`provenance_scikit_learn`
     - 11706
     - 60181
     - 217728
     - 0.725
     - `scikit-learn.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/scikit-learn.tar.gz>`_ 📥
   * - :ref:`provenance_sphinx`
     - 13431
     - 72692
     - 304084
     - 0.974
     - `sphinx.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/sphinx.tar.gz>`_ 📥
   * - :ref:`provenance_pandas`
     - 13696
     - 70959
     - 154646
     - 0.601
     - `pandas.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/pandas.tar.gz>`_ 📥
   * - :ref:`provenance_django`
     - 23749
     - 113137
     - 615946
     - 1.94
     - `django.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/django.tar.gz>`_ 📥
   * - :ref:`provenance_zulip`
     - 59854
     - 310032
     - 209908
     - 1.21
     - `zulip.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/zulip.tar.gz>`_ 📥
   * - :ref:`provenance_superset`
     - 76348
     - 394708
     - 97460
     - 1.03
     - `superset.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/superset.tar.gz>`_ 📥
   * - :ref:`provenance_airflow`
     - 90673
     - 454738
     - 91350
     - 1.15
     - `airflow.tar.gz <https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/airflow.tar.gz>`_ 📥

Canonical grammars
------------------

The grammar file is attached to the archive.

.. math::

   S &\to Entity \quad Core \quad Entity \\
   Core &\to wasDerivedFrom \\
        &\mid wasDerivedFrom_{r} \\
        &\mid specializationOf \\
        &\mid specializationOf_{r} \\
        &\mid wasGeneratedBy \quad Activity \quad used \\
        &\mid used_{r} \quad Activity \quad wasGeneratedBy_{r} \\
        &\mid wasGeneratedBy \quad Activity \quad Core \\
        &\quad Activity \quad wasGeneratedBy_{r} \\
        &\mid used_{r} \quad Activity \quad Core \\
        &\quad Activity \quad used \\
        &\mid wasDerivedFrom \quad Entity \quad Core \\
        &\quad Entity \quad wasDerivedFrom_{r} \\
        &\mid specializationOf \quad Entity \quad Core \\
        &\quad Entity \quad specializationOf_{r}
