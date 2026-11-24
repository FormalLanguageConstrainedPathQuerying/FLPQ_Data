.. _rpq_queries:

***
RPQ
***

.. only:: html

   :Release: |release|
   :Date: |today|

Regular path queries (RPQ) constrain the paths of a labeled graph by a
regular language. Unlike CFPQ, RPQ has no named, parameterized templates: an
RPQ query is a regular expression in the dataset's canonical syntax, stored
per graph inside the self-contained graph archive under ``queries/rpq/`` (see
:ref:`file_structure`); an RPQ may also be represented by a regular RSM. The
graph catalog is shared across all query classes — the "Applicable graphs"
list below cross-links the per-graph pages without duplicating them.

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
