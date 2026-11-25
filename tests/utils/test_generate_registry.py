import io
import pathlib

import pytest
from generate_registry import (
    _download,
    _sha256,
    archive_record,
    build_registry,
    write_registry,
)


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


MTX = "%%MatrixMarket matrix coordinate pattern general\n%%GraphBLAS type bool\n"


def _make_archive(root: pathlib.Path) -> None:
    """Builds a synthetic unpacked archive under root."""
    (root / "graph").mkdir(parents=True)
    (root / "graph" / "a.mtx").write_text(MTX + "3 3 2\n0 1\n1 2\n")
    (root / "graph" / "b.mtx").write_text(MTX + "3 3 1\n2 0\n")
    for query, files in {
        "cfpq/q1": ["q.cnf", "q.rsm", "results.mtx"],
        "cfpq/q2": ["q.cnf", "results.mtx"],
        "rpq/r1": ["r.re", "results.mtx"],
    }.items():
        (root / "queries" / query).mkdir(parents=True)
        for name in files:
            (root / "queries" / query / name).write_text("")


def test_sha256(tmp_path):
    p = tmp_path / "f"
    p.write_bytes(b"abc")
    assert _sha256(p) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_archive_record(tmp_path):
    root = tmp_path / "g"
    _make_archive(root)
    record = archive_record(root)
    assert record["num_nodes"] == 3
    assert record["num_edges"] == 3
    assert record["queries"] == [
        {"class": "cfpq", "name": "q1", "representations": ["cnf", "rsm"]},
        {"class": "cfpq", "name": "q2", "representations": ["cnf"]},
        {"class": "rpq", "name": "r1", "representations": ["re"]},
    ]


def test_archive_record_mixed_dimensions(tmp_path):
    root = tmp_path / "g"
    (root / "graph").mkdir(parents=True)
    (root / "graph" / "a.mtx").write_text(MTX + "3 3 1\n0 1\n")
    (root / "graph" / "b.mtx").write_text(MTX + "2 2 1\n0 1\n")
    with pytest.raises(ValueError, match="same dimensions"):
        archive_record(root)


def test_archive_record_without_queries_dir(tmp_path):
    root = tmp_path / "g"
    (root / "graph").mkdir(parents=True)
    (root / "graph" / "a.mtx").write_text(MTX + "2 2 1\n0 1\n")
    record = archive_record(root)
    assert record["num_nodes"] == 2
    assert record["num_edges"] == 1
    assert record["queries"] == []


def test_write_registry(tmp_path):
    p = tmp_path / "registry.json"
    write_registry({"version": "6.0.0", "graphs": {}}, p)
    assert p.read_text() == '{\n  "version": "6.0.0",\n  "graphs": {}\n}\n'


def _rows(graph_categories: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "graph": graph,
            "grammar": "g.cnf",
            "category": category,
            "query_class": "cfpq",
            "num_reachable_pairs": 1,
        }
        for graph, category in graph_categories
    ]


def test_build_registry_success(monkeypatch, tmp_path):
    import generate_registry

    monkeypatch.setattr(
        generate_registry, "load_rows", lambda path: _rows([("g2", "c2"), ("g1", "c1")])
    )

    def fake_build_record(name, url, workdir):
        assert url.endswith(f"{name}.tar.gz")
        return {
            "num_nodes": 1,
            "num_edges": 0,
            "size_mb": 0.001,
            "size_bytes": 1000,
            "sha256": "x" * 64,
            "queries": [],
        }

    monkeypatch.setattr(generate_registry, "build_record", fake_build_record)
    registry = build_registry(tmp_path)
    assert registry["version"] == generate_registry.DATASET_VERSION
    assert list(registry["graphs"]) == ["g1", "g2"]
    assert registry["graphs"]["g1"]["category"] == "c1"
    assert registry["graphs"]["g2"]["category"] == "c2"
    assert registry["graphs"]["g1"]["size_bytes"] == 1000


def test_build_registry_category_conflict(monkeypatch, tmp_path):
    import generate_registry

    monkeypatch.setattr(
        generate_registry,
        "load_rows",
        lambda path: _rows([("g1", "c1"), ("g1", "c2")]),
    )
    with pytest.raises(ValueError, match="conflicting categories"):
        build_registry(tmp_path)


def test_build_registry_all_or_nothing(monkeypatch, tmp_path):
    import generate_registry

    monkeypatch.setattr(
        generate_registry, "load_rows", lambda path: _rows([("g1", "c1"), ("g2", "c2")])
    )

    def fake_build_record(name, url, workdir):
        if name == "g2":
            raise RuntimeError("boom")
        return {
            "num_nodes": 1,
            "num_edges": 0,
            "size_mb": 0.001,
            "size_bytes": 1000,
            "sha256": "x" * 64,
            "queries": [],
        }

    monkeypatch.setattr(generate_registry, "build_record", fake_build_record)
    with pytest.raises(RuntimeError, match="g2: boom"):
        build_registry(tmp_path)


def test_download_retries_once(monkeypatch, tmp_path):
    import generate_registry

    calls = []

    def fake_get(url, stream=None, timeout=None):
        calls.append((url, timeout))
        if len(calls) == 1:
            raise ConnectionError("stalled")
        return _FakeResponse(b"abc")

    monkeypatch.setattr(generate_registry.requests, "get", fake_get)
    archive = tmp_path / "a.tar.gz"
    _download("https://example.com/a.tar.gz", archive)
    assert archive.read_bytes() == b"abc"
    assert len(calls) == 2
    assert calls[0][1] == (30.0, 60.0)


def test_download_failure_raises(monkeypatch, tmp_path):
    import generate_registry

    def fake_get(url, stream=None, timeout=None):
        raise ConnectionError("stalled")

    monkeypatch.setattr(generate_registry.requests, "get", fake_get)
    with pytest.raises(RuntimeError, match="download of .* failed"):
        _download("https://example.com/a.tar.gz", tmp_path / "a.tar.gz")
