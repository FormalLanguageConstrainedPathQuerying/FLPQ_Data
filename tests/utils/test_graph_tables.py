import pathlib

import graph_tables
from graph_tables import (
    BEGIN_MARKER,
    END_MARKER,
    _registry_problems,
    render_category_table,
)
from flpq_data.dataset.data import DATASET_URL
from flpq_data.dataset.registry import GraphInfo


def _info(name: str, category: str, nodes: int, edges: int, size_bytes: int) -> GraphInfo:
    return GraphInfo(
        name=name,
        category=category,
        num_nodes=nodes,
        num_edges=edges,
        size_mb=round(size_bytes / 1_000_000, 3),
        size_bytes=size_bytes,
        sha256="0" * 64,
        queries=(),
    )


def _row(graph, grammar, category, query_class, count):
    return {
        "graph": graph,
        "grammar": grammar,
        "category": category,
        "query_class": query_class,
        "num_reachable_pairs": count,
    }


def test_render_category_table_golden(monkeypatch):
    monkeypatch.setitem(
        graph_tables.GRAMMAR_COLUMNS,
        "c",
        [("Reachable pairs", "g.cnf"), ("Reachable pairs / other", None)],
    )
    graphs = {
        "b": _info("b", "c", 10, 20, 10_000),
        "a": _info("a", "c", 5, 7, 5_000),
    }
    rows = [
        _row("a", "a.cnf", "c", "cfpq", 100),
        _row("a", "g.cnf", "c", "cfpq", None),
        _row("b", "g.cnf", "c", "cfpq", 200),
        # b has no b.cnf row -> the per-graph column is empty
    ]
    pages = {"a": "page_a", "b": "page_b"}

    text = render_category_table("c", graphs, rows, pages)

    expected = "\n".join(
        [
            ".. list-table::",
            "",
            "   * - Graph",
            "     - Num Nodes",
            "     - Num Edges",
            "     - Reachable pairs",
            "     - Reachable pairs / other",
            "     - Size (MB)",
            "     - Download",
            "   * - :ref:`page_a`",
            "     - 5",
            "     - 7",
            "     - not available",
            "     - 100",
            "     - 0.005",
            f"     - `a.tar.gz <{DATASET_URL}a.tar.gz>`_ \U0001F4E5",
            "   * - :ref:`page_b`",
            "     - 10",
            "     - 20",
            "     - 200",
            "     -",
            "     - 0.010",
            f"     - `b.tar.gz <{DATASET_URL}b.tar.gz>`_ \U0001F4E5",
        ]
    )
    assert text == expected


def test_render_category_table_no_count_columns(monkeypatch):
    monkeypatch.setitem(graph_tables.GRAMMAR_COLUMNS, "plain", [])
    graphs = {"a": _info("a", "plain", 3, 4, 3_000)}
    text = render_category_table("plain", graphs, [], {"a": "page_a"})
    lines = text.splitlines()
    # Header has no count columns: Graph, Num Nodes, Num Edges, Size, Download.
    assert lines[2:7] == [
        "   * - Graph",
        "     - Num Nodes",
        "     - Num Edges",
        "     - Size (MB)",
        "     - Download",
    ]
    # The single row has exactly five cells.
    assert lines[7:12] == [
        "   * - :ref:`page_a`",
        "     - 3",
        "     - 4",
        "     - 0.003",
        f"     - `a.tar.gz <{DATASET_URL}a.tar.gz>`_ \U0001F4E5",
    ]


def test_render_category_table_orders_by_nodes_then_name(monkeypatch):
    monkeypatch.setitem(graph_tables.GRAMMAR_COLUMNS, "c", [])
    # Different node count: ordered by node count. Same node count: by name.
    graphs = {
        "zeta": _info("zeta", "c", 5, 1, 1_000),
        "alpha": _info("alpha", "c", 5, 1, 1_000),
        "mid": _info("mid", "c", 3, 1, 1_000),
    }
    pages = {"zeta": "pz", "alpha": "pa", "mid": "pm"}
    text = render_category_table("c", graphs, [], pages)
    refs = [line for line in text.splitlines() if line.startswith("   * - :ref:")]
    assert refs == [
        "   * - :ref:`pm`",  # mid (3 nodes) first
        "   * - :ref:`pa`",  # alpha (5 nodes, name tie -> alpha)
        "   * - :ref:`pz`",  # zeta (5 nodes, name tie -> zeta)
    ]


def _patch_registry(monkeypatch, categories: dict, infos: dict) -> None:
    """Points graph_tables' registry lookups at synthetic data."""
    monkeypatch.setattr(graph_tables, "categories", lambda: categories)
    monkeypatch.setattr(graph_tables, "graph_names", lambda: list(infos))
    monkeypatch.setattr(graph_tables, "graph_info", lambda name: infos[name])


def test_registry_problems_clean(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    assert _registry_problems([_row("a", "a.cnf", "c", "cfpq", 1)], {"a": "c"}) == []


def test_registry_problem_graph_not_in_site(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    problems = _registry_problems([_row("a", "a.cnf", "c", "cfpq", 1)], {})
    assert any(
        "registry graph a is not listed in any docs category" in p for p in problems
    )


def test_registry_problem_category_mismatch(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    problems = _registry_problems([_row("a", "a.cnf", "c", "cfpq", 1)], {"a": "other"})
    assert any("registry says a is in c, the docs say other" in p for p in problems)


def test_registry_problem_graph_without_csv_row(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    problems = _registry_problems([], {"a": "c"})
    assert any("registry graph a has no reachable-pairs row" in p for p in problems)


def test_registry_problem_csv_graph_not_in_registry(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    problems = _registry_problems(
        [_row("ghost", "ghost.cnf", "c", "cfpq", 1)], {"a": "c", "ghost": "c"}
    )
    assert any("CSV graph ghost is not in the registry" in p for p in problems)


def test_registry_problem_docs_category_without_registry_graphs(monkeypatch):
    _patch_registry(monkeypatch, {"c": ["a"]}, {"a": _info("a", "c", 1, 1, 1)})
    problems = _registry_problems(
        [_row("a", "a.cnf", "c", "cfpq", 1)], {"a": "c", "b": "empty_cat"}
    )
    assert any("docs category empty_cat has no registry graphs" in p for p in problems)


def _make_docs(tmp_path: pathlib.Path) -> pathlib.Path:
    docs = tmp_path / "docs"
    (docs / "graphs" / "data").mkdir(parents=True)
    (docs / "graphs" / "index.rst").write_text(
        ".. _graphs:\n\nGraphs\n******\n\n"
        ".. toctree::\n   :maxdepth: 1\n\n   c_alias_analysis\n"
    )
    (docs / "graphs" / "c_alias_analysis.rst").write_text(
        ".. _graphs_c_alias_analysis:\n\nC alias analysis\n****************\n\n"
        ".. toctree::\n   :hidden:\n\n   data/g1\n   data/g2\n\n"
        f"{BEGIN_MARKER}\nold\n{END_MARKER}\n"
    )
    for page, name in [("g1", "alpha"), ("g2", "beta")]:
        (docs / "graphs" / "data" / f"{page}.rst").write_text(
            f".. _{page}:\n\n{name}\n====\n\n"
            f"- `x.tar.gz <{DATASET_URL}{name}.tar.gz>`_\n"
        )
    return docs


def _make_csv(tmp_path: pathlib.Path) -> pathlib.Path:
    csv = tmp_path / "reachable_pairs.csv"
    csv.write_text(
        "graph,grammar,category,query_class,num_reachable_pairs\n"
        "alpha,c_alias.cnf,c_alias_analysis,cfpq,3\n"
        "beta,c_alias.cnf,c_alias_analysis,cfpq,4\n",
        encoding="utf-8",
    )
    return csv


def test_main_check_update_check(tmp_path, monkeypatch, capsys):
    docs = _make_docs(tmp_path)
    csv = _make_csv(tmp_path)
    monkeypatch.setattr(graph_tables, "DOCS_DIR", docs)
    monkeypatch.setattr(graph_tables, "REACHABLE_PAIRS_CSV", csv)
    monkeypatch.setattr(
        graph_tables, "categories", lambda: {"c_alias_analysis": ["alpha", "beta"]}
    )
    monkeypatch.setattr(graph_tables, "graph_names", lambda: ["alpha", "beta"])
    monkeypatch.setattr(
        graph_tables,
        "graph_info",
        lambda name: {
            "alpha": _info("alpha", "c_alias_analysis", 5, 7, 5_000),
            "beta": _info("beta", "c_alias_analysis", 10, 20, 10_000),
        }[name],
    )

    page = docs / "graphs" / "c_alias_analysis.rst"

    # Out of sync (the region still says "old") -> exit 1.
    assert graph_tables.main([]) == 1
    assert "out of sync" in capsys.readouterr().out

    # --update rewrites the region from the registry and the CSV.
    assert graph_tables.main(["--update"]) == 0
    text = page.read_text(encoding="utf-8")
    assert ":ref:`g1`" in text and ":ref:`g2`" in text
    assert "old" not in text
    # alpha (5 nodes) precedes beta (10 nodes); counts and sizes rendered.
    assert text.index(":ref:`g1`") < text.index(":ref:`g2`")
    assert "     - 3\n" in text and "     - 4\n" in text
    capsys.readouterr()

    # Now in sync.
    assert graph_tables.main([]) == 0
    assert "in sync" in capsys.readouterr().out


def test_main_missing_marker(tmp_path, monkeypatch, capsys):
    docs = _make_docs(tmp_path)
    # Keep the toctree (so the site maps resolve) but drop the markers.
    (docs / "graphs" / "c_alias_analysis.rst").write_text(
        ".. _graphs_c_alias_analysis:\n\nC alias analysis\n****************\n\n"
        ".. toctree::\n   :hidden:\n\n   data/g1\n   data/g2\n\n"
        "no markers here\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(graph_tables, "DOCS_DIR", docs)
    monkeypatch.setattr(graph_tables, "REACHABLE_PAIRS_CSV", _make_csv(tmp_path))
    monkeypatch.setattr(
        graph_tables, "categories", lambda: {"c_alias_analysis": ["alpha", "beta"]}
    )
    monkeypatch.setattr(graph_tables, "graph_names", lambda: ["alpha", "beta"])
    monkeypatch.setattr(
        graph_tables,
        "graph_info",
        lambda name: {
            "alpha": _info("alpha", "c_alias_analysis", 5, 7, 5_000),
            "beta": _info("beta", "c_alias_analysis", 10, 20, 10_000),
        }[name],
    )

    assert graph_tables.main([]) == 1
    assert "not found" in capsys.readouterr().out


def test_check_mode_on_the_real_repo_is_in_sync():
    # Offline gate: every category table matches the registry and the CSV.
    assert graph_tables.main([]) == 0
