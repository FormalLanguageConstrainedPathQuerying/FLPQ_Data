import pathlib

import pytest
import reachable_pairs_tables
from reachable_pairs_tables import (
    BEGIN_MARKER,
    END_MARKER,
    category_order,
    graph_to_category,
    load_rows,
    page_to_graph,
    render_tables_region,
    update_reachable_pairs_page,
)


def make_docs(tmp_path: pathlib.Path) -> pathlib.Path:
    docs = tmp_path / "docs"
    (docs / "graphs" / "data").mkdir(parents=True)
    (docs / "graphs" / "index.rst").write_text(
        ".. _graphs:\n\nGraphs\n******\n\n"
        ".. toctree::\n   :maxdepth: 1\n\n   cat_a\n   cat_b\n"
    )
    (docs / "graphs" / "cat_a.rst").write_text(
        ".. _graphs_cat_a:\n\nCat A\n*****\n\n"
        ".. toctree::\n   :hidden:\n\n   data/g1\n   data/g2\n"
    )
    (docs / "graphs" / "cat_b.rst").write_text(
        ".. _graphs_cat_b:\n\nCat B\n*****\n\n.. toctree::\n   :hidden:\n\n   data/g3\n"
    )
    for page, name in [("g1", "alpha"), ("g2", "beta"), ("g3", "gamma")]:
        (docs / "graphs" / "data" / f"{page}.rst").write_text(
            f".. _{page}:\n\n{name}\n====\n\n"
            f"- `x.tar.gz <https://cfpq-data.storage.yandexcloud.net/"
            f"5.0.0/graph/{name}.tar.gz>`_\n"
        )
    return docs


def test_category_order(tmp_path):
    assert category_order(make_docs(tmp_path)) == ["cat_a", "cat_b"]


def test_page_to_graph_and_graph_to_category(tmp_path):
    docs = make_docs(tmp_path)
    assert page_to_graph(docs) == {"g1": "alpha", "g2": "beta", "g3": "gamma"}
    assert graph_to_category(docs) == {
        "alpha": "cat_a",
        "beta": "cat_a",
        "gamma": "cat_b",
    }


def test_graph_to_category_duplicate_raises(tmp_path):
    docs = make_docs(tmp_path)
    (docs / "graphs" / "data" / "g3.rst").write_text(
        ".. _g3:\n\ngamma\n=====\n\n"
        "- `x.tar.gz <https://cfpq-data.storage.yandexcloud.net/"
        "5.0.0/graph/alpha.tar.gz>`_\n"
    )
    with pytest.raises(ValueError, match="listed in both"):
        graph_to_category(docs)


def test_page_to_graph_missing_link_raises(tmp_path):
    docs = make_docs(tmp_path)
    (docs / "graphs" / "data" / "g3.rst").write_text(".. _g3:\n\ngamma\n=====\n")
    with pytest.raises(ValueError, match="no Yandex download link"):
        page_to_graph(docs)


ROWS = [
    {
        "graph": "alpha",
        "grammar": "a.cnf",
        "category": "cat_a",
        "query_class": "cfpq",
        "num_reachable_pairs": 3,
    },
    {
        "graph": "alpha",
        "grammar": "b.cnf",
        "category": "cat_a",
        "query_class": "cfpq",
        "num_reachable_pairs": None,
    },
    {
        "graph": "beta",
        "grammar": "a.cnf",
        "category": "cat_a",
        "query_class": "cfpq",
        "num_reachable_pairs": 5,
    },
    {
        "graph": "beta",
        "grammar": "b.cnf",
        "category": "cat_a",
        "query_class": "cfpq",
        "num_reachable_pairs": 9,
    },
    {
        "graph": "gamma",
        "grammar": "g.cnf",
        "category": "cat_b",
        "query_class": "cfpq",
        "num_reachable_pairs": 7,
    },
]


def test_render_tables_region(tmp_path):
    docs = make_docs(tmp_path)
    region = render_tables_region(ROWS, docs)

    # Sections in category order, titled like the category pages.
    assert region.index("Cat A") < region.index("Cat B")
    assert "Cat A\n-----" in region
    assert "Cat B\n-----" in region

    # One :ref: subheading per graph (targeting the data page), underlined
    # with tildes.
    assert ":ref:`g1`\n~~~~" in region
    assert ":ref:`g2`\n~~~~" in region
    assert ":ref:`g3`\n~~~~" in region

    # Graphs sorted within a section; rows sorted by grammar file name.
    cat_a = region[region.index("Cat A") : region.index("Cat B")]
    assert cat_a.index(":ref:`g1`") < cat_a.index(":ref:`g2`")
    assert cat_a.index("- a.cnf") < cat_a.index("- b.cnf")
    # The other category's graphs do not leak into this section.
    assert "g3" not in cat_a


def test_render_tables_region_per_graph_tables(tmp_path):
    docs = make_docs(tmp_path)
    region = render_tables_region(ROWS, docs)

    # One table per graph with the Query | Reachable pairs header.
    assert region.count(".. list-table::") == 3
    assert region.count("* - Query") == 3
    assert region.count("- Reachable pairs") == 3

    # A row without a computed value renders as "not available".
    alpha = region[region.index(":ref:`g1`") : region.index(":ref:`g2`")]
    assert "* - a.cnf\n     - 3" in alpha
    assert "* - b.cnf\n     - not available" in alpha


def test_render_tables_region_empty_category(tmp_path):
    docs = make_docs(tmp_path)
    region = render_tables_region(ROWS[:4], docs)
    cat_b = region[region.index("Cat B") :]
    assert "No reachable-pair counts have been computed" in cat_b


RPQ_ROW = {
    "graph": "alpha",
    "grammar": "r.re",
    "category": "cat_a",
    "query_class": "rpq",
    "num_reachable_pairs": 100,
}


def test_load_rows_parses_query_class(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text(
        "graph,grammar,category,query_class,num_reachable_pairs\n"
        "g1,a.cnf,cat_a,cfpq,42\n"
        "g2,r.re,cat_a,rpq,\n",
        encoding="utf-8",
    )
    rows = load_rows(p)
    assert [r["query_class"] for r in rows] == ["cfpq", "rpq"]
    assert [r["num_reachable_pairs"] for r in rows] == [42, None]


def test_render_tables_region_renders_all_classes(tmp_path):
    docs = make_docs(tmp_path)
    region = render_tables_region(ROWS + [RPQ_ROW], docs)

    # The rpq row is rendered in alpha's table alongside the cfpq rows,
    # sorted by grammar file name (the extension makes the class
    # self-describing).
    alpha = region[region.index(":ref:`g1`") : region.index(":ref:`g2`")]
    assert alpha.index("- a.cnf") < alpha.index("- b.cnf") < alpha.index("- r.re")
    assert "* - r.re\n     - 100" in alpha


def test_update_reachable_pairs_page():
    text = f"intro\n{BEGIN_MARKER}\nold content\n{END_MARKER}\noutro\n"
    updated, changed = update_reachable_pairs_page(text, "new content")
    assert changed
    assert updated.splitlines() == [
        "intro",
        BEGIN_MARKER,
        "",
        "new content",
        "",
        END_MARKER,
        "outro",
    ]
    # Idempotent: replacing with the same region changes nothing.
    again, changed_again = update_reachable_pairs_page(updated, "new content")
    assert not changed_again
    assert again == updated


def test_update_reachable_pairs_page_missing_markers():
    with pytest.raises(ValueError, match="not found"):
        update_reachable_pairs_page("no markers here\n", "x")


def test_validation_problems_unknown_query_class():
    row = {**RPQ_ROW, "query_class": "x"}
    problems = reachable_pairs_tables._validation_problems([row], {"alpha": "cat_a"})
    assert any("unknown query_class" in p for p in problems)


def test_validation_problems_non_cfpq_row_needs_no_count_column(monkeypatch):
    site_map = {"gamma": "cat_b"}
    row = {
        "graph": "gamma",
        "grammar": "reachability.re",
        "category": "cat_b",
        "query_class": "rpq",
        "num_reachable_pairs": 1,
    }
    # An rpq row has no count column yet — that is not a problem.
    assert reachable_pairs_tables._validation_problems([row], site_map) == []
    # The same row as cfpq must have a count column in its category.
    monkeypatch.setitem(
        reachable_pairs_tables.GRAMMAR_COLUMNS, "cat_b", [("g_col", "g.cnf")]
    )
    problems = reachable_pairs_tables._validation_problems(
        [{**row, "query_class": "cfpq"}], site_map
    )
    assert len(problems) == 1
    assert "no count column" in problems[0]


def test_check_mode_on_the_real_repo_is_in_sync():
    # Guards against drift between the CSV and the per-graph tables.
    assert reachable_pairs_tables.main([]) == 0
