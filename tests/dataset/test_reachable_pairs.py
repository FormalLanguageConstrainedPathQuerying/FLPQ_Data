import io
from importlib import import_module

from flpq_data.dataset import (
    REACHABLE_PAIRS_CSV,
    REACHABLE_PAIRS_KEY_PREFIX,
    REACHABLE_PAIRS_URL,
    download_reachable_pairs,
    reachable_pairs,
)

rp = import_module("flpq_data.dataset.reachable_pairs")


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` for the download tests."""

    def __init__(self, content: bytes) -> None:
        self.raw = io.BytesIO(content)

    def raise_for_status(self) -> None:
        pass

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        pass


def test_versioned_url_constants():
    assert REACHABLE_PAIRS_KEY_PREFIX == "6.0.0"
    assert (
        REACHABLE_PAIRS_URL
        == "https://cfpq-data.storage.yandexcloud.net/6.0.0/reachable_pairs.csv"
    )


def test_download_reachable_pairs(tmp_path, monkeypatch):
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path))
    content = b"graph,grammar\nwc,c_alias.cnf\n"
    monkeypatch.setattr(rp.requests, "get", lambda **kwargs: _FakeResponse(content))

    destination = download_reachable_pairs()

    assert destination == tmp_path / "6.0.0" / "reachable_pairs.csv"
    assert destination.read_bytes() == content


def test_reachable_pairs_reads_downloaded_copy(tmp_path, monkeypatch):
    version_dir = tmp_path / "6.0.0"
    version_dir.mkdir()
    (version_dir / "reachable_pairs.csv").write_text(
        "graph,grammar,category,query_class,num_reachable_pairs\n"
        "g,c_alias.cnf,c_alias_analysis,cfpq,7\n"
    )
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path))

    rows = reachable_pairs()

    assert len(rows) == 1
    assert rows[0]["graph"] == "g"
    assert rows[0]["num_reachable_pairs"] == 7


def test_reachable_pairs_falls_back_to_bundled(tmp_path, monkeypatch):
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path / "empty"))

    assert rp._csv_path() == REACHABLE_PAIRS_CSV


def test_csv_exists():
    assert REACHABLE_PAIRS_CSV.exists()


def test_total_count():
    rows = reachable_pairs()
    assert len(rows) == 195


def test_all_rows_have_keys():
    for row in reachable_pairs():
        assert set(row.keys()) == {
            "graph",
            "grammar",
            "category",
            "query_class",
            "num_reachable_pairs",
        }


def test_query_class_values():
    assert {r["query_class"] for r in reachable_pairs()} == {"cfpq", "rpq"}


def test_query_class_filter():
    assert len(reachable_pairs(query_class="cfpq")) == 155
    rpq = reachable_pairs(query_class="rpq")
    assert len(rpq) == 40
    assert {r["graph"] for r in rpq} == {"pokec", "yago2s"}
    assert all(r["category"] == "social_networks" for r in rpq)
    # Spot checks: the single pokec query and one yago2s query.
    by_pair = {(r["graph"], r["grammar"]): r for r in rpq}
    assert by_pair[("pokec", "1.re")]["num_reachable_pairs"] == 30622564
    assert by_pair[("yago2s", "1.re")]["num_reachable_pairs"] == 4904


CATEGORIES = {
    "biological_uniprot": 10,
    "c_alias_analysis": 20,
    "context_sensitive_data_flow": 10,
    "data_provenance": 18,
    "field_sensitive_alias": 10,
    "java_points_to": 21,
    "name_resolution": 4,
    "rdf": 62,
    "social_networks": 40,
}


def test_categories_are_valid():
    rows = reachable_pairs()
    assert {r["category"] for r in rows} == set(CATEGORIES)


def test_row_counts_per_category():
    for category, count in CATEGORIES.items():
        assert len(reachable_pairs(category=category)) == count


def test_every_graph_has_one_category():
    rows = reachable_pairs()
    by_graph: dict[str, set[str]] = {}
    for row in rows:
        by_graph.setdefault(row["graph"], set()).add(row["category"])
    assert all(len(cats) == 1 for cats in by_graph.values())


def test_available_and_unavailable():
    # A pair has a count iff its results.mtx is computed in the archive;
    # the rest are stubs. The 4 remaining stubs are documented infeasible on
    # the compute host (see utils/stub_results_record.json, issue #130).
    rows = reachable_pairs()
    available = [r for r in rows if r["num_reachable_pairs"] is not None]
    unavailable = [r for r in rows if r["num_reachable_pairs"] is None]
    assert len(available) == 191
    assert len(unavailable) == 4
    # Spot checks: a computed pair and a stubbed one.
    by_pair = {(r["graph"], r["grammar"]): r for r in rows}
    assert by_pair[("wc", "c_alias.cnf")]["num_reachable_pairs"] == 156
    assert (
        by_pair[("unigraph_7", "unigraph_7.cnf")]["num_reachable_pairs"] == 2320964134
    )
    assert by_pair[("libgdx", "name_resolution.cnf")]["num_reachable_pairs"] is None


def test_filter_by_graph():
    rows = reachable_pairs(graph="gson")
    assert len(rows) == 1
    assert rows[0]["grammar"] == "java_points_to.cnf"
    assert rows[0]["num_reachable_pairs"] == 56325


def test_filter_by_grammar():
    rows = reachable_pairs(grammar="c_alias.cnf")
    assert len(rows) == 20
    assert all(r["grammar"] == "c_alias.cnf" for r in rows)


def test_filter_by_graph_and_grammar():
    rows = reachable_pairs(graph="wc", grammar="c_alias.cnf")
    assert len(rows) == 1
    assert rows[0]["num_reachable_pairs"] == 156


def test_filter_by_category():
    rows = reachable_pairs(category="rdf")
    assert len(rows) == 62
    assert all(r["category"] == "rdf" for r in rows)


def test_filter_by_category_and_graph():
    rows = reachable_pairs(graph="enzyme", category="rdf")
    assert len(rows) == 4
    assert reachable_pairs(graph="enzyme", category="c_alias_analysis") == []


def test_no_match_returns_empty():
    assert reachable_pairs(graph="nonexistent") == []
    assert reachable_pairs(grammar="nonexistent.cnf") == []
    assert reachable_pairs(category="nonexistent") == []


def test_rdf_graph_has_multiple_grammars():
    rows = reachable_pairs(graph="generations")
    assert len(rows) == 3
    grammars = {r["grammar"] for r in rows}
    assert grammars == {
        "nested_parentheses_subClassOf.cnf",
        "nested_parentheses_subClassOf_type.cnf",
        "nested_parentheses_type.cnf",
    }


def test_enzyme_has_broader_transitive():
    rows = reachable_pairs(graph="enzyme")
    assert len(rows) == 4
    grammars = {r["grammar"] for r in rows}
    assert "nested_parentheses_broaderTransitive.cnf" in grammars


def test_values_are_positive_ints():
    for row in reachable_pairs():
        val = row["num_reachable_pairs"]
        if val is not None:
            assert isinstance(val, int)
            assert val >= 0
