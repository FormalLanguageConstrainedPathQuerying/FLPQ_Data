import pathlib
import shutil
import sys
import tarfile
from unittest import mock

from archive_helpers import (
    README,
    RESULTS,
    _partial_tree,
    _query_dir,
    _tarball,
    _valid_tree,
)

from flpq_data.tools.check_archive_structure import _audit, main, validate_archive


def test_valid_directory_passes(tmp_path):
    assert validate_archive(_valid_tree(tmp_path)) == []


def test_valid_tarball_passes(tmp_path):
    tree = _valid_tree(tmp_path)
    assert validate_archive(_tarball(tree, tmp_path / "g.tar.gz")) == []


def test_validate_streams_the_graph_dir(tmp_path):
    # Regression for #188: the graph/ format check must stream the edges
    # (iter_edges_from_mtx_dir) rather than materialize a MultiDiGraph.
    import flpq_data.tools.check_archive_structure as cas
    from flpq_data.graphs.readwrite.mtx import iter_edges_from_mtx_dir

    tree = _valid_tree(tmp_path)
    graph_dir = tree / "graph"

    with mock.patch.object(
        cas, "iter_edges_from_mtx_dir", wraps=iter_edges_from_mtx_dir
    ) as spy:
        assert validate_archive(tree) == []

    spy.assert_called_once_with(graph_dir)


def test_tarball_top_level_must_match_name(tmp_path):
    tree = _valid_tree(tmp_path, name="other")
    tarball = _tarball(tree, tmp_path / "g.tar.gz")

    problems = validate_archive(tarball)

    assert any("must be named after the archive" in p for p in problems)


def test_extra_top_level_entry(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "notes.txt").write_text("extra")

    problems = validate_archive(tree)

    assert any("'notes.txt'" in p for p in problems)


def test_single_class_dir_missing_is_ok(tmp_path):
    tree = _valid_tree(tmp_path)
    shutil.rmtree(tree / "queries" / "rpq")

    assert validate_archive(tree) == []


def test_all_class_dirs_missing(tmp_path):
    tree = _valid_tree(tmp_path)
    for cls in ("cfpq", "rpq", "mcfpq"):
        shutil.rmtree(tree / "queries" / cls)

    problems = validate_archive(tree)

    assert any("at least one class directory is required" in p for p in problems)


def test_non_mtx_file_in_graph(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "b.txt").write_text("not a matrix")

    problems = validate_archive(tree)

    assert any("graph/b.txt" in p for p in problems)


def test_empty_graph_dir(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").unlink()

    problems = validate_archive(tree)

    assert any("at least one .mtx file" in p for p in problems)


def test_malformed_mtx(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text("garbage")

    problems = validate_archive(tree)

    assert any(p.startswith("graph/:") for p in problems)


def test_out_of_range_edge(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 1\n0 5\n"
    )

    problems = validate_archive(tree)

    assert any("outside the declared" in p for p in problems)


def test_inconsistent_graph_dimensions(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "b.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n3 3 0\n"
    )

    problems = validate_archive(tree)

    assert any("same dimensions" in p for p in problems)


def test_flat_query_file_is_rejected(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "x.cnf").write_text("S -> a")

    problems = validate_archive(tree)

    assert any("must be a query directory" in p for p in problems)


def test_missing_results_mtx(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").unlink()

    problems = validate_archive(tree)

    assert any("missing results.mtx" in p for p in problems)


def test_query_dir_without_representation(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").unlink()

    problems = validate_archive(tree)

    assert any("no cfpq representation file" in p for p in problems)


def test_stray_file_in_query_dir(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "notes.txt").write_text("extra")

    problems = validate_archive(tree)

    assert any(
        "representation files and results.mtx are allowed" in p for p in problems
    )


def test_representation_not_named_after_query_dir(tmp_path):
    tree = _valid_tree(tmp_path)
    query = tree / "queries" / "cfpq" / "s"
    (query / "s.cnf").rename(query / "other.cnf")

    problems = validate_archive(tree)

    assert any("must be named after the query directory" in p for p in problems)


def test_results_mtx_wrong_dimensions(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n3 3 1\n0 1\n"
    )

    problems = validate_archive(tree)

    assert any("must be a 2x2 matrix" in p for p in problems)


def test_results_mtx_out_of_range(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 1\n0 5\n"
    )

    problems = validate_archive(tree)

    assert any("results.mtx: entry (0, 5) is outside" in p for p in problems)


def test_results_mtx_unparseable(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").write_text("garbage")

    problems = validate_archive(tree)

    assert any("cannot be parsed as a Boolean MatrixMarket file" in p for p in problems)


def test_unparseable_cnf(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("not a grammar")

    problems = validate_archive(tree)

    assert any("cannot be parsed as a cfpq query" in p for p in problems)


def test_inert_label_is_accepted(tmp_path):
    # A terminal matching no stored label stays inert on materialization;
    # the query is legal and yields an empty result.
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("S\tz\n\nCount:\nS")

    assert validate_archive(tree) == []


def test_reversed_label_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("S\ta_r\n\nCount:\nS")

    assert validate_archive(tree) == []


def _write_mtx(path, entries="0 1\n"):
    path.write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        f"%%GraphBLAS type bool\n2 2 {len(entries.split()) // 2}\n{entries}"
    )


def test_stored_unindexed_reversed_label_is_rejected(tmp_path):
    tree = _valid_tree(tmp_path)
    _write_mtx(tree / "graph" / "a_r.mtx")

    problems = validate_archive(tree)

    assert any(
        "graph/a_r.mtx: reversed edge is stored but must be auto-generated "
        "from a.mtx" in p
        for p in problems
    )


def test_stored_indexed_reversed_label_is_rejected(tmp_path):
    tree = _valid_tree(tmp_path)
    _write_mtx(tree / "graph" / "load_0.mtx")
    _write_mtx(tree / "graph" / "load_r_0.mtx")

    problems = validate_archive(tree)

    assert any(
        "graph/load_r_0.mtx: reversed edge is stored but must be auto-generated "
        "from load_0.mtx" in p
        for p in problems
    )


def test_indexed_reversed_label_without_forward_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    _write_mtx(tree / "graph" / "load_r_0.mtx")

    assert validate_archive(tree) == []


def test_indexed_placeholder_label_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").unlink()
    (tree / "graph" / "load_0.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 1\n0 1\n"
    )
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("S\tload_i\n\nCount:\nS")

    assert validate_archive(tree) == []


def test_query_without_terminals(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("S\tN1\nN1\tS\n\nCount:\nS")

    problems = validate_archive(tree)

    assert any("uses no terminal" in p for p in problems)


def test_rsm_representation_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "cfpq", "t", ".rsm")
    (query / "t.rsm").write_text(
        "start: S\n[box S]\nstart: 0\nfinal: 2\n0 --a--> 1\n1 --a--> 2"
    )
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## cfpq/t\n- Language: aa.\n"
    )

    assert validate_archive(tree) == []


def test_rsm_inert_label_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "cfpq", "t", ".rsm")
    (query / "t.rsm").write_text("S -> z*")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## cfpq/t\n- Language: z*.\n"
    )

    assert validate_archive(tree) == []


def test_unparseable_rsm(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.rsm").write_text("garbage")

    problems = validate_archive(tree)

    assert any("cannot be parsed as a cfpq query" in p for p in problems)


def test_rpq_and_mcfpq_queries_parse(tmp_path):
    tree = _valid_tree(tmp_path)
    _query_dir(tree, "rpq", "p", ".re")
    _query_dir(tree, "mcfpq", "m", ".mcfg")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n"
        "\n## mcfpq/m\n- Language: a*.\n"
        "\n## rpq/p\n- Language: a*.\n"
    )

    assert validate_archive(tree) == []


def test_rpq_regular_rsm_is_accepted(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "rpq", "p", ".rsm")
    (query / "p.rsm").write_text("[box S]\nstart: 0\nfinal: 1\n0 --a--> 1")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## rpq/p\n- Language: a*.\n"
    )

    assert validate_archive(tree) == []


def test_rpq_recursive_rsm_is_rejected(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "rpq", "p", ".rsm")
    (query / "p.rsm").write_text("S -> a S b | a b")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## rpq/p\n- Language: a*b*.\n"
    )

    problems = validate_archive(tree)

    assert any("must be regular" in p for p in problems)


def test_re_kleene_plus_passes_consistency(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "rpq", "p", ".re")
    (query / "p.re").write_text("a+")
    (query / "p.rsm").write_text("[box S]\nstart: 0\nfinal: 1\n0 --a--> 1\n1 --a--> 1")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## rpq/p\n- Language: a+.\n"
    )

    assert validate_archive(tree) == []


def test_re_multi_char_symbol_passes_consistency(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "rpq", "p", ".re")
    (query / "p.re").write_text("ab*")
    (query / "p.rsm").write_text("[box S]\nstart: 0\nfinal: 0\n0 --ab--> 0")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n"
        "\n## rpq/p\n- Language: (ab)*.\n"
    )

    assert validate_archive(tree) == []


def test_unparseable_re(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "rpq", "p", ".re")
    (query / "p.re").write_text("(a")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## rpq/p\n- Language: a*.\n"
    )

    problems = validate_archive(tree)

    assert any("cannot be parsed as a rpq query" in p for p in problems)


def test_unparseable_mcfg(tmp_path):
    tree = _valid_tree(tmp_path)
    query = _query_dir(tree, "mcfpq", "m", ".mcfg")
    (query / "m.mcfg").write_text("S(x1 x2) <- A(x1)")
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n"
        "\n## mcfpq/m\n- Language: broken.\n"
    )

    problems = validate_archive(tree)

    assert any("cannot be parsed as a mcfpq query" in p for p in problems)


def test_missing_mandatory_section(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "README.md").write_text(README.replace("## License\nApache-2.0.\n", ""))

    problems = validate_archive(tree)

    assert any("'## License'" in p for p in problems)


def test_orphan_query_section(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n"
        "\n## cfpq/missing\n- Language: nowhere.\n"
    )

    problems = validate_archive(tree)

    assert any("does not match any query directory" in p for p in problems)


def test_undocumented_query(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "README.md").write_text("# Queries for g\n")

    problems = validate_archive(tree)

    assert any("no section describing 'cfpq/s'" in p for p in problems)


def test_empty_query_section(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n\n## cfpq/other\n- Language: a*.\n"
    )

    problems = validate_archive(tree)

    assert any("the section for 'cfpq/s' is empty" in p for p in problems)


def test_not_an_archive(tmp_path):
    file = tmp_path / "g.tar.gz"
    file.write_text("not a tarball")

    problems = validate_archive(file)

    assert any("not a .tar.gz archive" in p for p in problems)


def test_main_reports_problems(tmp_path, capsys):
    tree = _valid_tree(tmp_path)
    (tree / "README.md").write_text(README.replace("## License\nApache-2.0.\n", ""))

    assert main([str(tree)]) == 1
    out = capsys.readouterr().out
    assert "error:" in out and "structure violation" in out


def test_main_passes_valid_archive(tmp_path, capsys):
    tree = _valid_tree(tmp_path)

    assert main([str(tree)]) == 0
    assert "archive structure ok" in capsys.readouterr().out


def test_valid_partial_passes(tmp_path):
    assert validate_archive(_partial_tree(tmp_path), partial=True) == []


def test_valid_partial_tarball_passes(tmp_path):
    tree = _partial_tree(tmp_path)
    assert validate_archive(_tarball(tree, tmp_path / "g.tar.gz"), partial=True) == []


def test_partial_tarball_top_level_must_match_name(tmp_path):
    tree = _partial_tree(tmp_path, name="other")
    tarball = _tarball(tree, tmp_path / "g.tar.gz")

    problems = validate_archive(tarball, partial=True)

    assert any("must be named after the archive" in p for p in problems)


def test_partial_rejects_graph_dir(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "graph").mkdir()

    problems = validate_archive(tree, partial=True)

    assert any("'graph'" in p and "unexpected entry" in p for p in problems)


def test_partial_missing_queries(tmp_path):
    tree = tmp_path / "g"
    tree.mkdir()

    problems = validate_archive(tree, partial=True)

    assert any("missing entry 'queries'" in p for p in problems)


def test_partial_requires_class_dir(tmp_path):
    tree = _partial_tree(tmp_path)
    shutil.rmtree(tree / "queries" / "cfpq")

    problems = validate_archive(tree, partial=True)

    assert any("at least one class directory is required" in p for p in problems)


def test_partial_empty_class_dir(tmp_path):
    tree = _partial_tree(tmp_path)
    shutil.rmtree(tree / "queries" / "cfpq" / "s")

    problems = validate_archive(tree, partial=True)

    assert any("must add at least one query" in p for p in problems)


def test_partial_flat_file_rejected(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "cfpq" / "x.cnf").write_text("S -> a")

    problems = validate_archive(tree, partial=True)

    assert any("must be a query directory" in p for p in problems)


def test_partial_missing_results(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").unlink()

    problems = validate_archive(tree, partial=True)

    assert any("missing results.mtx" in p for p in problems)


def test_partial_unparseable_representation(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "s.cnf").write_text("not a grammar")

    problems = validate_archive(tree, partial=True)

    assert any("cannot be parsed as a cfpq query" in p for p in problems)


def test_partial_readme_orphan_section(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n"
        "\n## cfpq/missing\n- Language: nowhere.\n"
    )

    problems = validate_archive(tree, partial=True)

    assert any("does not match any query directory" in p for p in problems)


def test_partial_readme_undocumented_query(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "README.md").write_text("# Queries for g\n")

    problems = validate_archive(tree, partial=True)

    assert any("no section describing 'cfpq/s'" in p for p in problems)


def test_partial_readme_empty_section(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n\n## cfpq/other\n- Language: a*.\n"
    )

    problems = validate_archive(tree, partial=True)

    assert any("the section for 'cfpq/s' is empty" in p for p in problems)


def test_full_mode_rejects_partial_tree(tmp_path):
    tree = _partial_tree(tmp_path)

    problems = validate_archive(tree)

    assert any("missing entry 'graph'" in p for p in problems)


def test_main_partial_passes(tmp_path, capsys):
    tree = _partial_tree(tmp_path)

    assert main([str(tree), "--partial"]) == 0
    assert "partial archive structure ok" in capsys.readouterr().out


def test_main_partial_reports_problems(tmp_path, capsys):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "results.mtx").unlink()

    assert main([str(tree), "--partial"]) == 1
    out = capsys.readouterr().out
    assert "error:" in out and "structure violation" in out


def test_unexpected_entry_in_queries(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "notes.txt").write_text("extra")

    problems = validate_archive(tree)

    assert any("queries/notes.txt: unexpected entry" in p for p in problems)


def test_missing_queries_readme(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "README.md").unlink()

    problems = validate_archive(tree)

    assert any("queries/README.md: missing" in p for p in problems)


def test_partial_unexpected_entry_in_queries(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "notes.txt").write_text("extra")

    problems = validate_archive(tree, partial=True)

    assert any("queries/notes.txt: unexpected entry" in p for p in problems)


def test_partial_missing_queries_readme(tmp_path):
    tree = _partial_tree(tmp_path)
    (tree / "queries" / "README.md").unlink()

    problems = validate_archive(tree, partial=True)

    assert any("queries/README.md: missing" in p for p in problems)


def test_subdirectory_in_query_dir(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "queries" / "cfpq" / "s" / "sub").mkdir()

    problems = validate_archive(tree)

    assert any("only files are allowed" in p for p in problems)


def test_second_header_line_mismatch(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "wrong second line\n2 2 1\n0 1\n"
    )

    problems = validate_archive(tree)

    assert any(p.startswith("graph/:") for p in problems)


def test_non_numeric_dimension_line(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\nx y z\n0 1\n"
    )

    problems = validate_archive(tree)

    assert any(p.startswith("graph/:") for p in problems)


def test_blank_line_in_mtx_body_is_skipped(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 1\n0 1\n\n"
    )

    assert validate_archive(tree) == []


def test_graph_mtx_entry_count_mismatch(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 2\n0 1\n"
    )

    problems = validate_archive(tree)

    assert any(p.startswith("graph/:") for p in problems)


def test_graph_mtx_malformed_entry_line(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "graph" / "a.mtx").write_text(
        "%%MatrixMarket matrix coordinate pattern general\n"
        "%%GraphBLAS type bool\n2 2 1\nx y\n"
    )

    problems = validate_archive(tree)

    assert any(p.startswith("graph/:") for p in problems)


def test_forbidden_label_component(tmp_path):
    tree = _valid_tree(tmp_path)
    _write_mtx(tree / "graph" / "a_bar.mtx")

    problems = validate_archive(tree)

    assert any("forbidden component 'bar'" in p for p in problems)


def test_same_dir_different_terminals(tmp_path):
    tree = _valid_tree(tmp_path)
    query = tree / "queries" / "cfpq" / "t"
    query.mkdir(parents=True)
    (query / "t.cnf").write_text("S\tb\tN1\nN1\tb\n\nCount:\nS")
    (query / "t.rsm").write_text("S -> c*")
    (query / "results.mtx").write_text(RESULTS)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## cfpq/t\n- Language: b*.\n"
    )

    problems = validate_archive(tree)

    assert any("use different terminal sets" in p for p in problems)


def test_same_dir_subset_terminals(tmp_path):
    tree = _valid_tree(tmp_path)
    query = tree / "queries" / "cfpq" / "t"
    query.mkdir(parents=True)
    (query / "t.cnf").write_text("S\ta\tN1\nN1\ta\nS\tb\tN2\nN2\tb\n\nCount:\nS")
    (query / "t.rsm").write_text("S -> a*")
    (query / "results.mtx").write_text(RESULTS)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## cfpq/t\n- Language: ab.\n"
    )

    problems = validate_archive(tree)

    assert any("use different terminal sets" in p for p in problems)


def test_same_dir_equal_terminals_pass(tmp_path):
    tree = _valid_tree(tmp_path)
    query = tree / "queries" / "cfpq" / "t"
    query.mkdir(parents=True)
    (query / "t.cnf").write_text("S\ta\tN1\nN1\ta\n\nCount:\nS")
    (query / "t.rsm").write_text("S -> a*")
    (query / "results.mtx").write_text(RESULTS)
    (tree / "queries" / "README.md").write_text(
        "# Queries for g\n\n## cfpq/s\n- Language: a*.\n\n## cfpq/t\n- Language: a*.\n"
    )

    assert validate_archive(tree) == []


def test_tarball_with_two_top_level_dirs(tmp_path):
    tree = _valid_tree(tmp_path, name="g")
    (tmp_path / "other").mkdir()
    dest = tmp_path / "g.tar.gz"
    with tarfile.open(dest, "w:gz") as tarball:
        tarball.add(tree, arcname="g")
        tarball.add(tmp_path / "other", arcname="other")

    problems = validate_archive(dest)

    assert any("must contain a single top-level directory" in p for p in problems)


def test_broken_symlink_is_rejected(tmp_path):
    link = tmp_path / "g.tar.gz"
    link.symlink_to(tmp_path / "nowhere")

    problems = validate_archive(link)

    assert any("not a .tar.gz archive" in p for p in problems)


def test_main_without_path_reports_it(capsys):
    assert main([]) == 1
    assert "give a path to validate or use --audit" in capsys.readouterr().out


def _mock_s3(archives: dict[str, bytes]) -> mock.Mock:
    client = mock.Mock()
    client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": key} for key in sorted(archives)]}
    ]

    def download(bucket, key, dest):
        pathlib.Path(dest).write_bytes(archives[key])

    client.download_file.side_effect = download
    return client


def test_audit_passes_valid_archives(tmp_path):
    tarball = _tarball(_valid_tree(tmp_path), tmp_path / "g.tar.gz")
    client = _mock_s3({"5.0.0/graph/g.tar.gz": tarball.read_bytes()})

    assert _audit(client, "cfpq-data", "5.0.0/graph") == []


def test_audit_reports_invalid_archive_with_its_key(tmp_path):
    tree = _valid_tree(tmp_path)
    (tree / "README.md").write_text(README.replace("## License\nApache-2.0.\n", ""))
    tarball = _tarball(tree, tmp_path / "g.tar.gz")
    client = _mock_s3({"5.0.0/graph/g.tar.gz": tarball.read_bytes()})

    problems = _audit(client, "cfpq-data", "5.0.0/graph")

    assert any(
        p.startswith("5.0.0/graph/g.tar.gz:") and "'## License'" in p for p in problems
    )


def test_audit_without_archives_reports_it(tmp_path):
    client = _mock_s3({})

    problems = _audit(client, "cfpq-data", "5.0.0/graph")

    assert any("no .tar.gz objects found" in p for p in problems)


def test_main_audit_requires_credentials(capsys):
    assert main(["--audit"]) == 1
    assert "required for --audit" in capsys.readouterr().out


def test_main_audit_validates_bucket(tmp_path, monkeypatch, capsys):
    tarball = _tarball(_valid_tree(tmp_path), tmp_path / "g.tar.gz")
    client = _mock_s3({"5.0.0/graph/g.tar.gz": tarball.read_bytes()})
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    status = main(
        [
            "--audit",
            "--prefix",
            "5.0.0/graph",
            "--access-key-id",
            "key-id",
            "--secret-access-key",
            "secret",
        ]
    )

    assert status == 0
    assert "archive structure ok" in capsys.readouterr().out


def test_main_audit_without_boto3_reports_it(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "boto3", None)

    status = main(
        [
            "--audit",
            "--access-key-id",
            "key-id",
            "--secret-access-key",
            "secret",
        ]
    )

    assert status == 1
    assert "--audit requires boto3" in capsys.readouterr().out


def test_console_entry_point_is_registered():
    from importlib.metadata import entry_points

    eps = entry_points(group="console_scripts", name="flpq-check-archive")

    assert [ep.value for ep in eps] == ["flpq_data.tools.check_archive_structure:main"]
