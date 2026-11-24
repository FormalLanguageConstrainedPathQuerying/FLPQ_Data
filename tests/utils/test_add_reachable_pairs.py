import csv
import pathlib

import add_reachable_pairs
import pytest
from add_reachable_pairs import add_rows, derive_rows, main, representation_file
from archive_helpers import _partial_tree, _tarball, _valid_tree

HEADER = ["graph", "grammar", "category", "query_class", "num_reachable_pairs"]


def _write_csv(path: pathlib.Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)


def _read_rows(path: pathlib.Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        return [row for row in reader]


def test_derive_rows_full_archive(tmp_path):
    tree = _valid_tree(tmp_path)
    rows = derive_rows(tree, "g", "cat")
    assert rows == [
        {
            "graph": "g",
            "grammar": "s.cnf",
            "category": "cat",
            "query_class": "cfpq",
            "num_reachable_pairs": "1",
        }
    ]


def test_derive_rows_partial_archive(tmp_path):
    tree = _partial_tree(tmp_path)
    rows = derive_rows(tree, "g", "cat")
    assert rows == [
        {
            "graph": "g",
            "grammar": "s.cnf",
            "category": "cat",
            "query_class": "cfpq",
            "num_reachable_pairs": "1",
        }
    ]


def test_derive_rows_refuses_misnamed_representation(tmp_path):
    tree = _valid_tree(tmp_path)
    query = tree / "queries" / "cfpq" / "s"
    (query / "s.cnf").rename(query / "other.cnf")

    with pytest.raises(ValueError, match="named after the query directory"):
        derive_rows(tree, "g", "cat")


def test_representation_file_prefers_cnf_over_rsm(tmp_path):
    d = tmp_path / "q"
    d.mkdir()
    (d / "q.rsm").write_text("S -> a*")
    (d / "q.cnf").write_text("S\ta\tN1\nN1\ta\n\nCount:\nS")
    rep = representation_file(d)
    assert rep is not None
    assert rep.name == "q.cnf"


def test_representation_file_falls_back_to_rsm(tmp_path):
    d = tmp_path / "q"
    d.mkdir()
    (d / "q.rsm").write_text("S -> a*")
    rep = representation_file(d)
    assert rep is not None
    assert rep.name == "q.rsm"


def test_representation_file_none_without_representations(tmp_path):
    d = tmp_path / "q"
    d.mkdir()
    (d / "results.mtx").write_text("x")
    assert representation_file(d) is None


def test_add_rows_inserts_sorted(tmp_path):
    csv_path = tmp_path / "r.csv"
    _write_csv(
        csv_path,
        [
            ["b", "q.cnf", "cat", "cfpq", "1"],
            ["d", "q.cnf", "cat", "cfpq", "2"],
        ],
    )
    row = {
        "graph": "c",
        "grammar": "q.cnf",
        "category": "cat",
        "query_class": "cfpq",
        "num_reachable_pairs": "3",
    }
    problems = add_rows(csv_path, [row])
    assert problems == []
    assert _read_rows(csv_path) == [
        ["b", "q.cnf", "cat", "cfpq", "1"],
        ["c", "q.cnf", "cat", "cfpq", "3"],
        ["d", "q.cnf", "cat", "cfpq", "2"],
    ]


def test_add_rows_keeps_lf_line_endings(tmp_path):
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [["b", "q.cnf", "cat", "cfpq", "1"]])
    row = {
        "graph": "c",
        "grammar": "q.cnf",
        "category": "cat",
        "query_class": "cfpq",
        "num_reachable_pairs": "3",
    }
    problems = add_rows(csv_path, [row])
    assert problems == []
    # The bundled CSV is LF; csv.writer's default CRLF terminator would
    # rewrite every line and bloat the diff.
    assert b"\r" not in csv_path.read_bytes()


def test_add_rows_refuses_duplicate(tmp_path):
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [["g", "s.cnf", "cat", "cfpq", "1"]])
    row = {
        "graph": "g",
        "grammar": "s.rsm",
        "category": "cat",
        "query_class": "cfpq",
        "num_reachable_pairs": "9",
    }
    problems = add_rows(csv_path, [row])
    assert len(problems) == 1
    assert "already exists" in problems[0]
    assert _read_rows(csv_path) == [["g", "s.cnf", "cat", "cfpq", "1"]]


def test_add_rows_refuses_category_mismatch(tmp_path):
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [["g", "other.cnf", "old_cat", "cfpq", "1"]])
    row = {
        "graph": "g",
        "grammar": "s.cnf",
        "category": "new_cat",
        "query_class": "cfpq",
        "num_reachable_pairs": "2",
    }
    problems = add_rows(csv_path, [row])
    assert len(problems) == 1
    assert "disagrees" in problems[0]
    assert _read_rows(csv_path) == [["g", "other.cnf", "old_cat", "cfpq", "1"]]


def test_main_full_archive(tmp_path, monkeypatch):
    tree = _valid_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat"])
    assert status == 0
    assert _read_rows(csv_path) == [["g", "s.cnf", "cat", "cfpq", "1"]]


def test_main_partial_archive(tmp_path, monkeypatch):
    tree = _partial_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [["g", "old.cnf", "cat", "cfpq", "5"]])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat", "--partial"])
    assert status == 0
    assert _read_rows(csv_path) == [
        ["g", "old.cnf", "cat", "cfpq", "5"],
        ["g", "s.cnf", "cat", "cfpq", "1"],
    ]


def test_main_refuses_invalid_archive(tmp_path, monkeypatch):
    tree = _partial_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat"])
    assert status == 1
    assert _read_rows(csv_path) == []


def test_main_refuses_graph_name_mismatch(tmp_path, monkeypatch):
    tree = _valid_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "other", "--category", "cat"])
    assert status == 1
    assert _read_rows(csv_path) == []


def test_main_dry_run_writes_nothing(tmp_path, monkeypatch):
    tree = _valid_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat", "--dry-run"])
    assert status == 0
    assert _read_rows(csv_path) == []


def test_main_refuses_archive_not_named_after_graph(tmp_path, monkeypatch):
    tree = _valid_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "other.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat"])
    assert status == 1
    assert _read_rows(csv_path) == []


def test_main_refuses_non_tar_gz(tmp_path, monkeypatch):
    not_an_archive = tmp_path / "g.tar.gz"
    not_an_archive.write_text("plain text")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(not_an_archive), "--graph", "g", "--category", "cat"])
    assert status == 1
    assert _read_rows(csv_path) == []


def test_main_refuses_existing_row(tmp_path, monkeypatch):
    tree = _valid_tree(tmp_path)
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    csv_path = tmp_path / "r.csv"
    _write_csv(csv_path, [["g", "s.cnf", "cat", "cfpq", "1"]])
    monkeypatch.setattr(add_reachable_pairs, "REACHABLE_PAIRS_CSV", csv_path)
    status = main([str(tarball), "--graph", "g", "--category", "cat"])
    assert status == 1
