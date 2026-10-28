.. _dyck:

Dyck
====

.. contents:: Table of Contents

Info
----

.. list-table::
   :header-rows: 1

   * -
     -
   * - Full Name
     - Dyck Grammar
   * - Class
     - Context-Free
   * - Kind
     - Hierarchical
   * - Origin
     - `link <https://en.wikipedia.org/wiki/Dyck_language>`_


Grammar Parameters
------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - :math:`\textit{types}`
     - List of pairs :math:`(\textit{op}_i, \textit{cp}_i)` with opening and closing parentheses for each type
   * - :math:`\textit{eps}`
     - :math:`\textit{True}` if empty string is in the language and :math:`\textit{False}` otherwise


Grammar Template
----------------

.. math::

   \begin{aligned}
   S \, &\rightarrow \, \varepsilon \, \qquad \qquad &\textit{if } \textit{eps} = \textit{True} \, \\
   S \, &\rightarrow \, \textit{op}_i \, \textit{cp}_i \qquad \qquad &\textit{if } \textit{eps} = \textit{False} \, \\
   S \, &\rightarrow \, \textit{op}_i \, S \, \textit{cp}_i \, S \, &\\
   &\forall \, (\textit{op}_i, \textit{cp}_i) \, \in \, \textit{types} \, &\\
   \end{aligned}


Description
-----------
Dyck grammars generate Dyck languages of the balanced strings with parentheses of :math:`|\textit{types}|` types.
For example, such a grammar with :math:`\textit{types} = \{(a, b)\}`
and :math:`\textit{eps} = \textit{True}` generates the language :math:`\{\varepsilon, a b, ab ab, aabb, \ldots\}`.


Example Grammars
----------------
The Dyck grammar with :math:`\textit{types} = \{(a, b)\}` and :math:`\textit{eps} = \textit{True}`.

.. math::

   S \, \rightarrow \, \varepsilon \, \mid \, a \, S \, b \, S \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> epsilon | a S b S

----

The Dyck grammar with :math:`\textit{types} = \{(a, b)\}` and :math:`\textit{eps} = \textit{False}`.

.. math::

   S \, \rightarrow \, a \, b \, \mid \, a \, S \, b \, S \, \\

`Pyformlang CFG <https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html>`_:

.. code-block:: python

   S -> a b | a S b S
