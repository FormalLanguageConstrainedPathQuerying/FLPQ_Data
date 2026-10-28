from pathlib import Path

import pytest
from check_math_snippets import (
    check_docs,
    check_package,
    check_snippets,
    extract_math_snippets,
    main,
)

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
PACKAGE_DIR = Path(__file__).resolve().parents[2] / "flpq_data"


def test_extract_inline_role():
    assert extract_math_snippets("x :math:`a_1` y") == [(1, "a_1", False)]


def test_extract_multiple_inline_roles_on_one_line():
    assert extract_math_snippets(":math:`a` and :math:`b_2`") == [
        (1, "a", False),
        (1, "b_2", False),
    ]


def test_extract_multiline_inline_role():
    text = "for :math:`\\{w \\mid\nw \\in L\\}` end"
    assert extract_math_snippets(text) == [(1, "\\{w \\mid w \\in L\\}", False)]


def test_extract_math_block():
    text = ".. math::\n\n   S \\rightarrow a_1 \\\\\n   V \\rightarrow b_2 \\\\\n"
    assert extract_math_snippets(text) == [
        (1, "S \\rightarrow a_1 \\\\ V \\rightarrow b_2 \\\\", True)
    ]


def test_extract_indented_math_block():
    assert extract_math_snippets("  .. math::\n\n     x_1\n") == [(1, "x_1", True)]


def test_extract_math_block_without_body():
    assert extract_math_snippets(".. math::\n\nNext paragraph.\n") == []


def test_extract_skips_code_blocks():
    text = ".. code-block:: latex\n\n   :math:`\\textit{a_b}`\n\nreal :math:`c_d` end\n"
    assert extract_math_snippets(text) == [(5, "c_d", False)]


def test_extract_code_block_without_body():
    text = ".. code-block:: python\nplain text :math:`a_b`\n"
    assert extract_math_snippets(text) == [(2, "a_b", False)]


def test_extract_inline_role_inside_math_block_is_not_double_counted():
    text = ".. math::\n\n   :math:`a_b`\n"
    assert extract_math_snippets(text) == [(1, ":math:`a_b`", True)]


def test_extract_no_math():
    assert extract_math_snippets("plain text\nno math here\n") == []


def test_check_snippets_reports_broken_items():
    messages = check_snippets(
        [
            ("a.rst", 1, "f_r_i", False),
            ("a.rst", 2, r"\textit{a_b}", False),
        ]
    )
    assert len(messages) == 2
    assert messages[0].startswith("a.rst:1:")
    assert "Double subscripts" in messages[0]
    assert "f_r_i" in messages[0]
    assert messages[1].startswith("a.rst:2:")
    assert "'_' allowed only in math mode" in messages[1]


def test_check_snippets_is_clean_for_valid_items():
    assert (
        check_snippets(
            [
                ("a.rst", 1, r"f_{r\_i}", False),
                ("a.rst", 2, "a_{b_c}", False),
                ("b.rst", 3, r"\begin{aligned} S &\to a \end{aligned}", True),
            ]
        )
        == []
    )


def test_check_snippets_empty_input_runs_no_oracle(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("oracle must not run for empty input")

    monkeypatch.setattr("check_math_snippets.subprocess.run", fail)
    assert check_snippets([]) == []


def test_check_snippets_missing_node_fails_loudly(monkeypatch):
    monkeypatch.setattr("check_math_snippets.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="node is not on PATH"):
        check_snippets([("a.rst", 1, "x_1", False)])


def test_check_snippets_missing_node_modules_fails_loudly(monkeypatch, tmp_path):
    import check_math_snippets as cms

    # Point the repo-root lookup at an empty tmp dir via the script location.
    script = tmp_path / "utils" / "check_math_snippets_node.cjs"
    script.parent.mkdir()
    script.write_text("", encoding="utf-8")
    monkeypatch.setattr(cms, "_oracle_script", lambda: script)
    with pytest.raises(RuntimeError, match="npm ci"):
        check_snippets([("a.rst", 1, "x_1", False)])


def test_check_docs_reports_violations(tmp_path):
    (tmp_path / "page.rst").write_text("T\n=\n\n:math:`f_r_i`\n", encoding="utf-8")
    messages = check_docs(tmp_path)
    assert len(messages) == 1
    assert "page.rst:4" in messages[0]
    assert "Double subscripts" in messages[0]
    assert "f_r_i" in messages[0]


def test_check_docs_is_clean_for_valid_pages(tmp_path):
    (tmp_path / "page.rst").write_text(
        ".. math::\n\n   \\textit{load}_f \\\\\n", encoding="utf-8"
    )
    assert check_docs(tmp_path) == []


def test_check_docs_skips_build_artifacts(tmp_path):
    build = tmp_path / "_build"
    build.mkdir()
    (build / "page.rst").write_text(":math:`f_r_i`\n", encoding="utf-8")
    assert check_docs(tmp_path) == []


def test_check_docs_empty_dir(tmp_path):
    assert check_docs(tmp_path) == []


def test_check_package_reports_broken_docstring(tmp_path):
    (tmp_path / "mod.py").write_text(
        '"""Module with :math:`f_r_i` in its docstring."""\n\n\n'
        "def f():\n"
        '    """Uses :math:`a_{b_c}`."""\n'
        "    return 1\n",
        encoding="utf-8",
    )
    messages = check_package(tmp_path)
    assert len(messages) == 1
    assert "mod.py:1" in messages[0]
    assert "Double subscripts" in messages[0]


def test_check_package_is_clean(tmp_path):
    (tmp_path / "mod.py").write_text(
        'r"""Module with :math:`f_{r\\_i}` in its docstring."""\n', encoding="utf-8"
    )
    assert check_package(tmp_path) == []


def test_check_package_skips_unparseable_modules(tmp_path):
    (tmp_path / "broken.py").write_text("def f(:\n", encoding="utf-8")
    assert check_package(tmp_path) == []


def test_check_package_empty_dir(tmp_path):
    assert check_package(tmp_path) == []


def test_main_returns_zero_when_clean(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.rst").write_text("no math\n", encoding="utf-8")
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "mod.py").write_text('"""Clean :math:`x_1`."""\n', encoding="utf-8")
    assert main(["--dir", str(docs), "--package", str(package)]) == 0
    assert "valid" in capsys.readouterr().out


def test_main_returns_one_on_violation(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.rst").write_text(":math:`f_r_i`\n", encoding="utf-8")
    package = tmp_path / "pkg"
    package.mkdir()
    assert main(["--dir", str(docs), "--package", str(package)]) == 1
    out = capsys.readouterr().out
    assert "page.rst:1" in out


def test_real_docs_tree_is_clean():
    assert check_docs(DOCS_DIR) == []


def test_real_package_is_clean():
    assert check_package(PACKAGE_DIR) == []
