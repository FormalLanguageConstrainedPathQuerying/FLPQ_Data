#!/usr/bin/env python3
"""Validate the math snippets of the docs pages and package docstrings.

Sphinx passes math content verbatim to MathJax, which renders it in the
browser; a snippet the engine cannot parse shows up as an error message on
the deployed page while the Sphinx build stays green (issues #127, #173).
This tool therefore validates every snippet with the MathJax engine itself
(``utils/check_math_snippets_node.cjs``, the same version the browser loads
— see ``mathjax_js`` in ``docs/conf.py``): it scans every ``.rst`` file
under ``docs`` and every docstring under the package, extracts the
``:math:`` roles and ``.. math::`` bodies, and reports each snippet the
engine rejects with the engine's own error message.

Usage::

    python utils/check_math_snippets.py [--dir docs] [--package flpq_data]
"""

import argparse
import ast
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Optional, Sequence

__all__ = [
    "check_docs",
    "check_package",
    "check_snippets",
    "extract_math_snippets",
    "main",
]

#: Upper bound for one oracle run (the engine starts up once per run).
_ORACLE_TIMEOUT = 120

_INLINE_MATH_RE = re.compile(r":math:`([^`]+)`", re.DOTALL)
_MATH_BLOCK_RE = re.compile(r"^\s*\.\.\s+math::\s*$")
_CODE_BLOCK_RE = re.compile(r"^\s*\.\.\s+(?:code-block|literalinclude|sourcecode)::")


def _directive_body(lines: list[str], i: int) -> tuple[int, list[str]]:
    """Returns the (end index, body lines) of the indented block after ``lines[i]``.

    The end index is the first line index past the block (trailing blank
    lines are included in the span); body lines are stripped of their
    indentation.
    """
    base = len(lines[i]) - len(lines[i].lstrip())
    j = i + 1
    n = len(lines)
    body_indent: Optional[int] = None
    body: list[str] = []
    while j < n:
        line = lines[j]
        if not line.strip():
            j += 1
            continue
        indent = len(line) - len(line.lstrip())
        if body_indent is None:
            if indent <= base:
                break
            body_indent = indent
        elif indent < body_indent:
            break
        body.append(line.strip())
        j += 1
    return j, body


def _code_block_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Returns the (start, end) line-index spans of code-block directives."""
    spans: list[tuple[int, int]] = []
    i, n = 0, len(lines)
    while i < n:
        if not _CODE_BLOCK_RE.match(lines[i]):
            i += 1
            continue
        j, _ = _directive_body(lines, i)
        spans.append((i, j))
        i = j
    return spans


def _mask_code_blocks(text: str) -> str:
    """Returns the text with code-block directives blanked out.

    The line count is preserved so that the line numbers of the remaining
    content stay valid.
    """
    lines = text.splitlines()
    for start, end in _code_block_spans(lines):
        for k in range(start, end):
            lines[k] = ""
    return "\n".join(lines)


def extract_math_snippets(text: str) -> list[tuple[int, str, bool]]:
    """Returns the (start line, snippet, display) triples of every math snippet.

    Collects inline ``:math:`` roles (``display=False``, which may span
    several lines) and the bodies of ``.. math::`` directives
    (``display=True``); code-block directives are ignored. Line numbers are
    1-based and whitespace inside a snippet is collapsed to single spaces.

    Parameters
    ----------
    text : str
        The reStructuredText source to scan.

    Examples
    --------
    >>> extract_math_snippets("a :math:`x_1` b\\n\\n.. math::\\n\\n   y_2\\n")
    [(1, 'x_1', False), (3, 'y_2', True)]

    Returns
    -------
    snippets : list[tuple[int, str, bool]]
        The (start line, snippet, display) triples, in document order.
    """
    masked = _mask_code_blocks(text)
    lines = masked.splitlines()

    snippets: list[tuple[int, str, bool]] = []
    block_lines: set[int] = set()
    for i, line in enumerate(lines):
        if not _MATH_BLOCK_RE.match(line):
            continue
        j, body = _directive_body(lines, i)
        block_lines.update(range(i, j))
        if body:
            snippets.append((i + 1, " ".join(body), True))

    for match in _INLINE_MATH_RE.finditer(masked):
        line_no = masked.count("\n", 0, match.start()) + 1
        if line_no - 1 in block_lines:
            continue
        snippet = " ".join(match.group(1).split())
        snippets.append((line_no, snippet, False))

    snippets.sort()
    return snippets


def _oracle_script() -> pathlib.Path:
    """Returns the path of the MathJax oracle script."""
    return pathlib.Path(__file__).resolve().parent / "check_math_snippets_node.cjs"


def _require_oracle() -> str:
    """Returns the node executable, failing loudly when the oracle is unusable."""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError(
            "node is not on PATH; install Node.js (>= 20) to run the "
            "math-snippet guard (see docs/developer.rst, Development setup)"
        )
    repo_root = _oracle_script().resolve().parents[1]
    if not (repo_root / "node_modules" / "mathjax").is_dir():
        raise RuntimeError(
            "node_modules/mathjax is missing; run `npm ci` at the "
            "repository root to run the math-snippet guard"
        )
    return node


def check_snippets(items: list[tuple[str, int, str, bool]]) -> list[str]:
    """Validates (file, line, snippet, display) items with the MathJax oracle.

    Runs the oracle once for all items and returns one message per broken
    snippet, ``file:line: <MathJax message> :: snippet``, in input order.

    Parameters
    ----------
    items : list[tuple[str, int, str, bool]]
        The (file, line, snippet, display) tuples to validate.

    Returns
    -------
    messages : list[str]
        One message per broken snippet, in input order.
    """
    if not items:
        return []
    node = _require_oracle()
    payload = json.dumps(
        [
            {"file": file, "line": line, "display": display, "snippet": snippet}
            for file, line, snippet, display in items
        ]
    )
    proc = subprocess.run(
        [node, str(_oracle_script())],
        input=payload,
        capture_output=True,
        text=True,
        timeout=_ORACLE_TIMEOUT,
    )
    if proc.returncode == 2:
        raise RuntimeError(f"math oracle failed: {proc.stderr.strip()}")
    return proc.stdout.splitlines()


def check_docs(docs_dir: pathlib.Path) -> list[str]:
    """Returns one message per broken math snippet under docs_dir.

    Parameters
    ----------
    docs_dir : pathlib.Path
        The directory to scan recursively for ``.rst`` pages (``_build``
        directories are skipped).

    Returns
    -------
    messages : list[str]
        One ``file:line: <MathJax message> :: snippet`` message per
        violation, sorted by file and line.
    """
    items: list[tuple[str, int, str, bool]] = []
    for path in sorted(pathlib.Path(docs_dir).rglob("*.rst")):
        if "_build" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for line, snippet, display in extract_math_snippets(text):
            items.append((str(path), line, snippet, display))
    items.sort(key=lambda item: (item[0], item[1]))
    return check_snippets(items)


def _docstrings(source: str) -> list[tuple[int, str]]:
    """Returns the (start line, docstring) pairs of every docstring in a module source.

    The start line is the 1-based line of the docstring's opening quotes.
    """
    tree = ast.parse(source)
    result: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring is None:
            continue
        result.append((node.body[0].lineno, docstring))
    return result


def check_package(package_dir: pathlib.Path) -> list[str]:
    """Returns one message per broken math snippet in the docstrings under package_dir.

    Docstrings are rendered on the autodoc reference pages, so broken math
    there fails the same way as broken math in the docs pages.

    Parameters
    ----------
    package_dir : pathlib.Path
        The package directory to scan recursively for ``.py`` modules.

    Returns
    -------
    messages : list[str]
        One ``file:line: <MathJax message> :: snippet`` message per
        violation, sorted by file and line.
    """
    items: list[tuple[str, int, str, bool]] = []
    for path in sorted(pathlib.Path(package_dir).rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            docstring_items = _docstrings(source)
        except SyntaxError:
            continue
        for start, docstring in docstring_items:
            for line, snippet, display in extract_math_snippets(docstring):
                items.append((str(path), start + line - 1, snippet, display))
    items.sort(key=lambda item: (item[0], item[1]))
    return check_snippets(items)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Checks docs pages and package docstrings; returns 0 if clean, 1 otherwise."""
    parser = argparse.ArgumentParser(
        description="Validate the math snippets of the docs and package docstrings."
    )
    parser.add_argument(
        "--dir", default="docs", help="directory to scan for .rst pages"
    )
    parser.add_argument(
        "--package",
        default="flpq_data",
        help="package directory to scan for docstrings",
    )
    args = parser.parse_args(argv)

    messages = check_docs(pathlib.Path(args.dir)) + check_package(
        pathlib.Path(args.package)
    )
    if messages:
        for message in messages:
            print(message)
        print(f"\n{len(messages)} broken math snippet(s) found.")
        return 1
    print("All math snippets are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
