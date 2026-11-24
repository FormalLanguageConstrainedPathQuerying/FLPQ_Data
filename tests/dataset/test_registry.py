import csv
import dataclasses
import json
import pathlib

import pytest

from flpq_data import GraphInfo, QueryInfo, categories, graph_info, graph_names
from flpq_data.dataset.registry import REGISTRY_JSON

CSV = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "flpq_data"
    / "dataset"
    / "reachable_pairs.csv"
)


def _csv_rows() -> list[dict]:
    with CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_registry_file_shape():
    reg = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    assert reg["version"] == "6.0.0"
    assert list(reg["graphs"]) == sorted(reg["graphs"])
    for record in reg["graphs"].values():
        assert set(record) == {
            "category",
            "num_nodes",
            "num_edges",
            "size_mb",
            "sha256",
            "queries",
        }


def test_graph_names_count_and_sorted():
    assert len(graph_names()) == 115
    assert graph_names() == sorted(graph_names())


def test_graph_names_match_csv():
    assert set(graph_names()) == {row["graph"] for row in _csv_rows()}


def test_graph_info_skos():
    info = graph_info("skos")
    assert isinstance(info, GraphInfo)
    assert info.name == "skos"
    assert info.category == "rdf"
    assert info.num_nodes == 144
    assert info.num_edges == 252
    assert len(info.sha256) == 64


def test_graph_info_unknown():
    with pytest.raises(FileNotFoundError, match="No graph with name='nope' found"):
        graph_info("nope")


def test_categories_match_csv():
    expected: dict[str, set] = {}
    for row in _csv_rows():
        expected.setdefault(row["category"], set()).add(row["graph"])
    actual = categories()
    assert set(actual) == set(expected)
    for category, names in actual.items():
        assert names == sorted(expected[category])
    assert sum(len(names) for names in actual.values()) == len(graph_names())


def test_categories_sorted():
    actual = categories()
    assert list(actual) == sorted(actual)
    for names in actual.values():
        assert names == sorted(names)


def test_queries_structure():
    for name in graph_names():
        info = graph_info(name)
        assert info.queries
        for query in info.queries:
            assert isinstance(query, QueryInfo)
            assert query.query_class in {"cfpq", "rpq", "mcfpq"}
            assert query.name
            assert query.representations == tuple(sorted(query.representations))
    skos = graph_info("skos")
    cfpq = [query for query in skos.queries if query.query_class == "cfpq"]
    assert any({"cnf", "rsm"} <= set(query.representations) for query in cfpq)


def test_info_is_frozen():
    info = graph_info("skos")
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(info, "category", "other")
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(info.queries[0], "name", "other")
