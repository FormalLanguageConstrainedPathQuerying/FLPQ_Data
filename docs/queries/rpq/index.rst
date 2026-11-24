.. _rpq_queries:

***
RPQ
***

.. only:: html

   :Release: |release|
   :Date: |today|

Regular path queries (RPQ) constrain the paths of a labeled graph by a
regular language. A query is specified by a regular expression template
instantiated per graph from its stored labels; an RPQ may also be represented
by a regular RSM. The graph catalog is shared across all query classes — the
"Applicable graphs" list below cross-links the per-graph pages without
duplicating them.

.. toctree::
   :hidden:
   :glob:

   data/*

Query templates
---------------

.. list-table::
   :header-rows: 1

   * - Template
     - Class
     - Kind
   * - :ref:`reachability`
     - Regular
     - General
   * - :ref:`label_star`
     - Regular
     - General

Both templates are designed stubs: no real-world RPQ data exists yet. When the
data is provided, a query lives inside the self-contained graph archive under
``queries/rpq/`` (see :ref:`file_structure`).

Applicable graphs
-----------------

Graphs from the shared :ref:`catalog <graphs>` that carry at least one RPQ
query.

.. applicable-graphs:begin

Social Networks
^^^^^^^^^^^^^^^

* :ref:`pokec`
* :ref:`yago2s`

.. applicable-graphs:end
