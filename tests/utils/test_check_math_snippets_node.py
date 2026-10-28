"""Tests for the MathJax oracle script (utils/check_math_snippets_node.cjs).

The oracle is the only TeX validator of the math-snippet guard: it compiles
snippets with the same MathJax engine and version the deployed docs load in
the browser, so these tests pin the observable contract (exit codes, message
format) of that engine integration.
"""

import json
import pathlib
import shutil
import subprocess

SCRIPT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "utils"
    / "check_math_snippets_node.cjs"
)
TIMEOUT = 60


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        raise AssertionError(
            "node is not on PATH; install Node.js (>= 20) and run `npm ci` "
            "at the repository root (see docs/developer.rst, Development setup)"
        )
    return node


def run_oracle(payload) -> subprocess.CompletedProcess:
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [_node(), str(SCRIPT)],
        input=data,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def test_oracle_flags_broken_snippets():
    result = run_oracle(
        [
            {"file": "a.rst", "line": 1, "display": False, "snippet": "f_r_i"},
            {"file": "a.rst", "line": 2, "display": False, "snippet": r"\textit{a_b}"},
            {"file": "b.rst", "line": 3, "display": False, "snippet": "a_{b"},
            {"file": "b.rst", "line": 4, "display": False, "snippet": "x_"},
            {"file": "c.rst", "line": 5, "display": False, "snippet": "a^b^c"},
        ]
    )
    assert result.returncode == 1
    lines = result.stdout.splitlines()
    assert len(lines) == 5
    assert lines[0].startswith("a.rst:1:")
    assert "Double subscripts" in lines[0]
    assert "f_r_i" in lines[0]
    assert "'_' allowed only in math mode" in lines[1]
    assert "brace" in lines[2]
    assert "Missing superscript or subscript argument" in lines[3]
    assert "Double exponent" in lines[4]


def test_oracle_accepts_valid_snippets():
    result = run_oracle(
        [
            {"file": "a.rst", "line": 1, "display": False, "snippet": r"f_{r\_i}"},
            {"file": "a.rst", "line": 2, "display": False, "snippet": "a_{b_c}"},
            {"file": "a.rst", "line": 3, "display": False, "snippet": "a_b^c"},
            {
                "file": "b.rst",
                "line": 4,
                "display": False,
                "snippet": r"\textit{store}_{r\_f}",
            },
            {
                "file": "b.rst",
                "line": 5,
                "display": True,
                "snippet": r"\begin{aligned} S &\to a \\ T &\to b \end{aligned}",
            },
        ]
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_alignment_tab_requires_an_alignment_environment():
    broken = run_oracle(
        [
            {
                "file": "a.rst",
                "line": 1,
                "display": True,
                "snippet": "S &\\to a \\\\ T &\\to b",
            }
        ]
    )
    assert broken.returncode == 1
    assert "Misplaced &" in broken.stdout

    fixed = run_oracle(
        [
            {
                "file": "a.rst",
                "line": 1,
                "display": True,
                "snippet": r"\begin{aligned} S &\to a \\ T &\to b \end{aligned}",
            }
        ]
    )
    assert fixed.returncode == 0


def test_bad_input_exits_two():
    result = run_oracle("not json")
    assert result.returncode == 2
    assert "bad input" in result.stderr
