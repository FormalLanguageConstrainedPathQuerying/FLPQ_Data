# ## Tutorial
#
# Release
#
# :   6.1.2
#
# Date
#
# :   Oct 28, 2026
#
# This guide can help you start working with FLPQ_Data.
#
# **You can download this tutorial as a Jupyter Notebook from the link at the end of the page.**
#
# **NetworkX.** We use the NetworkX [MultiDiGraph](https://networkx.org/documentation/latest/reference/classes/multidigraph.html) to represent the labeled graph.
# To familiarize yourself with this representation and find useful functions, see [NetworkX tutorial](https://networkx.org/documentation/latest/tutorial.html).
#
# **Pyformlang.** We use the Pyformlang [Regex](https://pyformlang.readthedocs.io/en/latest/modules/regular_expression.html) to represent regular grammars.
# Also, we use the Pyformlang [CFG](https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html) and [RSA](https://pyformlang.readthedocs.io/en/latest/modules/rsa.html) to represent context-free grammars.
# To familiarize yourself with this representations and find useful functions, see [Pyformlang usage](https://pyformlang.readthedocs.io/en/latest/usage.html).
#
# All functions are documented on the Reference page.
#
# ### Import
#
# First you need to import the package.

import flpq_data

# # Load graph
#
# After the package is imported, we can load the graphs.
#
# ## Load graph archive from Dataset
#
# We can load the archive with the graph using function `graph_dir`: it returns the local directory of the graph and downloads it into the machine-global cache only when it is not there yet.

bzip_path = flpq_data.graph_dir("bzip")

# # Load graph by path
#
# The archive unpacks to a directory with one MatrixMarket file per edge
# label in its `graph` subdirectory (see File structure). We
# can load the graph along the specified path using function
# `graph_from_mtx_dir`.

bzip = flpq_data.graph_from_mtx_dir(bzip_path / "graph")

# Create graph
#
# We can also create a synthetic graph using one of the generators in module Graph generators.
#
# # Create a one cycle graph
#
# For example, let’s create a one cycle graph, with 5 nodes, the edges of which are marked with the letter `a`.

cycle = flpq_data.labeled_cycle_graph(5, label="a")

# Change edges
#
# We can change the specified graph labels by using function `change_edges`
# from Graph utilities.

new_cycle = flpq_data.change_edges(cycle, {"a": "b"})

# Now the labels `a` have changed to `b`.
#
# # Add reverse edges
#
# In addition, we can add reverse edges to the graph by using function `add_reverse_edges`
# from Graph utilities. This is extremely useful if graph analysis is formulated using such reverse edges.

new_cycle_with_reversed = flpq_data.add_reverse_edges(new_cycle)

# Now, for each edge with label `a` this graph contains the reversed edge with label `a_r`.
#
# # Convert graph format
#
# Graphs can be converted between the supported formats — `mtx` (a directory
# of MatrixMarket files), `txt`, `rdf`, and the FastMatrixCFPQ `.g` text
# — with function `convert_graph`:
# the conversion runs over a streaming edge iterator without building an
# in-memory graph, so even large archives convert in constant memory (see the
# Format conversion section).

txt_path = flpq_data.convert_graph(
    bzip_path / "graph", "bzip.txt", src_format="mtx", dst_format="txt"
)

# # Load grammar
#
# Graph archives from the dataset are self-contained: besides the graph they carry the
# queries that apply to the graph under `queries/` — one directory per query with its
# grammar template and a precomputed `results.mtx` (see File structure).
# The grammar templates themselves are described in the CFPQ section.
#
# A grammar template may use indexed symbols (e.g. `load_i`); we materialize it over a
# concrete graph with functions `cnf_template_from_text`
# and `materialize`,
# which expand every index present in the graph edge labels:

import networkx as nx
g = nx.MultiDiGraph()
_ = g.add_edges_from(
    [(0, 1, {"label": "load_0"}), (1, 2, {"label": "store_0"}),
     (0, 3, {"label": "alloc"})]
)
text = ("PT\tPTh\talloc\n"
        "PT\talloc\n"
        "PTh\tload_i\tAl_st_PTh_i\n"
        "Al_st_PTh_i\tAl\tst_PTh_i\n"
        "st_PTh_i\tstore_i\tPTh\n"
        "Al\tPT\n"
        "\n"
        "Count:\n"
        "PT")
template = flpq_data.cnf_template_from_text(text)
cfg = flpq_data.materialize(template, g)

# # Regular grammars
#
# Currently, we have one representation of regular grammars:
#
# 1. [Regular expression](https://en.wikipedia.org/wiki/Regular_expression#Formal_definition)
#
# ## Create a regular expression
#
# For example, a regular expression can be created by using function `regex_from_text`
# from Reading and writing grammars.

regex = flpq_data.regex_from_text("a (bc|d*)")

# # Load regular expression by path
#
# We can load the regular expression along the specified path using function `regex_from_txt`.

path = flpq_data.regex_to_txt(regex, "test.txt")
regex_by_path = flpq_data.regex_from_txt(path)

# Сontext-free grammars
#
# Currently, we have three representations of context-free grammars (CFGs):
#
# 1. [Classic](https://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions)
#
# 1. [Chomsky Normal Form](https://en.wikipedia.org/wiki/Chomsky_normal_form)
#
# 1. [Recursive State Machine](https://link.springer.com/chapter/10.1007/978-3-030-54832-2_6)
#
# # Create a classic context-free grammar
#
# A classic context-free grammar can be created by using function `cfg_from_text`
# from Reading and writing grammars.

cfg = flpq_data.cfg_from_text("S -> a S b S | a b")

# # Load context-free grammar by path
#
# We can load the classic context-free grammar along the specified path using function `cfg_from_txt`.

path = flpq_data.cfg_to_txt(cfg, "test.txt")
cfg_by_path = flpq_data.cfg_from_txt(path)

# Generate grammar
#
# We can also generate a grammar for specified template using one of the generators in module Grammar generators.
#
# # Generate a Dyck grammar
#
# For example, let’s generate a Dyck grammar of the balanced strings with `a` as an opening parenthesis, `b` as a closing parenthesis, and without the empty string.

dyck_cfg = flpq_data.dyck_grammar([("a", "b")], eps=False)

# # Generate a Java Points-to grammar
#
# Also, let’s generate a Java Points-to grammar for the field-sensitive analysis of Java programs with field names `f0` and `f1`.

java_pt_cfg = flpq_data.java_points_to_grammar(["f0", "f1"])
