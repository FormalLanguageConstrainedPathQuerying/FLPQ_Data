.. _java_points-to:

Java Points-to
==============

.. contents:: Table of Contents

Info
----

.. list-table::
   :header-rows: 1

   * -
     -
   * - Full Name
     - Java Points-to Analysis Grammar
   * - Class
     - Context-Free
   * - Kind
     - Static Analysis
   * - Origin
     - `link <https://dl.acm.org/doi/10.1145/2858965.2814307>`_


Grammar Parameters
------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - :math:`\textit{fields}`
     - List of fields :math:`f` used in Java program for load/store operations


Grammar Template
----------------

.. math::
   \begin{aligned}
   \textit{PointsTo} \, &\rightarrow \, (\textit{assign} \, \mid  \, \textit{load}_f \, \textit{Alias} \, \textit{store}_f)^{*} \, \textit{alloc} \, \\
   \textit{Alias} \, &\rightarrow \, \textit{PointsTo} \, \textit{FlowsTo} \, \\
   \textit{FlowsTo} \, &\rightarrow \, \textit{alloc}_r \, (\textit{assign}_r \, \mid \, \textit{store}_{r\_f} \, \textit{Alias} \, \textit{load}_{r\_f})^* \, \\
   &\forall \, f \, \in \, \textit{fields} \, \\
   \end{aligned}


Description
-----------
Java points-to analysis grammar generates language for the field-sensitive analysis
of Java programs, which tracks the dataflow between heap objects that are stored in
and loaded from fields :math:`f \in \textit{fields}`. Introduced in
`"Giga-scale exhaustive points-to analysis for Java in under a minute" <https://dl.acm.org/doi/10.1145/2858965.2814307>`_.
The dataflow of the program is constructed from object creations, variable assignments,
and load/store operations on fields.


Example Grammars
----------------

The Java points-to analysis grammar with :math:`\textit{fields} = [0, 1]`.

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> PTh alloc
   PTh -> epsilon
   PTh -> assign PTh
   PTh -> load_0 Al store_0 PTh
   PTh -> load_1 Al store_1 PTh
   FT -> alloc_r FTh
   FTh -> epsilon
   FTh -> assign_r FTh
   FTh -> store_0_r Al load_0_r FTh
   FTh -> store_1_r Al load_1_r FTh
    Al -> S FT

Recursive State Machine
-----------------------

.. image:: /_static/img/rsm_java_points_to.svg
   :alt: Java Points-To RSM

.. code-block:: text

   start: PointsTo
   [box PointsTo]
   start: 0
   final: 1
   0 --assign--> 0
   0 --alloc--> 1
   0 --load_i--> p_i
   p_i --Alias--> q_i
   q_i --store_i--> 0
   [box FlowsTo]
   start: 0
   final: 1
   0 --alloc_r--> 1
   1 --store_r_i--> p_i
   p_i --Alias--> q_i
   q_i --load_r_i--> 1
   1 --assign_r--> 1
   [box Alias]
   start: 0
   final: 2
   0 --PointsTo--> 1
   1 --FlowsTo--> 2
