"""Keep the reachable-pairs tables in sync with the CSV.

The reference counts live once, in
``flpq_data/dataset/reachable_pairs.csv`` (the single source of truth for
automatic processing); each row carries a ``query_class`` (``cfpq``,
``rpq``, or ``mcfpq`` — the names of the ``queries/<class>/`` directories
in the graph archives). This tool renders the per-graph tables of
``docs/reachable_pairs.rst`` (one section per graph category, one table
per graph, every query class rendered, between the
``reachable-pairs-tables`` markers); the count columns of the per-category
graph tables in ``docs/graphs/*.rst`` are rendered by
``utils/graph_tables.py`` (CFPQ rows only).

This tool keeps the rendering accurate:

- check mode (default): report every table region that disagrees with the
  CSV and exit non-zero, so it can gate a commit;
- ``--update``: rewrite the region.

The graph-to-category mapping is derived from the site itself: each
category page's toctree lists its data pages, and the archive name in a
data page's download URL is the graph name (page titles are not reliable).

Usage (from any directory)::

    python utils/reachable_pairs_tables.py [--update]
"""

import argparse
import csv
import pathlib
import re
from typing import Optional, Sequence

from config import MAIN_FOLDER

from flpq_data.tools.check_archive_structure import QUERY_CLASSES

__all__ = [
    "BEGIN_MARKER",
    "END_MARKER",
    "NOT_AVAILABLE",
    "GRAMMAR_COLUMNS",
    "toctree_entries",
    "category_order",
    "category_pages",
    "display_path",
    "page_to_graph",
    "graph_pages",
    "graph_to_category",
    "load_rows",
    "render_tables_region",
    "replace_marked_region",
    "update_reachable_pairs_page",
    "main",
]

REACHABLE_PAIRS_CSV = MAIN_FOLDER / "flpq_data" / "dataset" / "reachable_pairs.csv"
DOCS_DIR = MAIN_FOLDER / "docs"
REACHABLE_PAIRS_PAGE = DOCS_DIR / "reachable_pairs.rst"

#: The marker lines delimiting the generated region of reachable_pairs.rst.
#: They are plain reST comments, so they do not render.
BEGIN_MARKER = ".. reachable-pairs-tables:begin"
END_MARKER = ".. reachable-pairs-tables:end"

#: The cell text for a (graph, grammar) pair that is in the CSV but has no
#: computed value yet.
NOT_AVAILABLE = "not available"

#: Per category, the ordered (column header, grammar file) pairs of the
#: count columns of its graph table; a None grammar file means the per-graph
#: ``<graph>.cnf``.
GRAMMAR_COLUMNS: dict[str, list[tuple[str, Optional[str]]]] = {
    "biological_uniprot": [("Reachable pairs", None)],
    "c_alias_analysis": [("Reachable pairs", "c_alias.cnf")],
    "context_sensitive_data_flow": [("Reachable pairs", "aa.cnf")],
    "data_provenance": [("Reachable pairs", "prov_derivation.cnf")],
    "field_sensitive_alias": [("Reachable pairs", "vf.cnf")],
    "java_points_to": [("Reachable pairs", "java_points_to.cnf")],
    "name_resolution": [("Reachable pairs", "name_resolution.cnf")],
    "rdf": [
        ("Reachable pairs / subClassOf", "nested_parentheses_subClassOf.cnf"),
        ("Reachable pairs / subClassOf_type", "nested_parentheses_subClassOf_type.cnf"),
        ("Reachable pairs / type", "nested_parentheses_type.cnf"),
        (
            "Reachable pairs / broaderTransitive",
            "nested_parentheses_broaderTransitive.cnf",
        ),
    ],
}

_URL_RE = re.compile(
    r"https://cfpq-data\.storage\.yandexcloud\.net/"
    r"\d+\.\d+\.\d+/graph/([^.]+)\.tar\.gz"
)
_REF_RE = re.compile(r"^:ref:`([^`]+)`")


def display_path(path: pathlib.Path) -> str:
    """A short display path when possible, the full path otherwise.

    Paths under the repo root are shown relative to it; anything else
    (e.g. a test fixture in a temp dir) is shown as-is.
    """
    try:
        return str(path.relative_to(MAIN_FOLDER))
    except ValueError:
        return str(path)


def toctree_entries(path: pathlib.Path) -> list[str]:
    """Returns the entries of the first toctree in path, in order.

    Options (``:maxdepth:``, ``:hidden:``) are skipped; the toctree ends at
    the first non-blank line at column 0 or at end of file.

    Parameters
    ----------
    path : pathlib.Path
        A reStructuredText docs page.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     p = pathlib.Path(tmp) / "t.rst"
    ...     n = p.write_text(
    ...         ".. toctree::\\n   :hidden:\\n\\n"
    ...         "   data/a\\n   data/b\\n\\nNext section\\n"
    ...     )
    ...     toctree_entries(p)
    ['data/a', 'data/b']
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[str] = []
    in_toc = False
    for line in lines:
        if line.strip() == ".. toctree::":
            in_toc = True
            continue
        if in_toc:
            if line.strip() and line[0] not in " \t":
                break
            entry = line.strip()
            if entry and not entry.startswith(":"):
                entries.append(entry)
    return entries


def category_order(docs_dir: pathlib.Path) -> list[str]:
    """Returns the ordered category stems from ``docs/graphs/index.rst``."""
    return toctree_entries(docs_dir / "graphs" / "index.rst")


def category_pages(docs_dir: pathlib.Path) -> dict[str, list[str]]:
    """Maps each category to the ordered data-page stems of its toctree."""
    pages: dict[str, list[str]] = {}
    for category in category_order(docs_dir):
        entries = toctree_entries(docs_dir / "graphs" / f"{category}.rst")
        pages[category] = [e[len("data/") :] for e in entries if e.startswith("data/")]
    return pages


def page_to_graph(docs_dir: pathlib.Path) -> dict[str, str]:
    """Maps every data-page stem to its graph name.

    The graph name is the archive name in the page's Yandex download URL;
    page titles are not reliable (e.g. ``xz_field_sensitive_alias.rst`` is
    titled "xz").

    Raises
    ------
    ValueError
        If a data page has no Yandex download link.
    """
    mapping: dict[str, str] = {}
    for pages in category_pages(docs_dir).values():
        for page in pages:
            text = (docs_dir / "graphs" / "data" / f"{page}.rst").read_text(
                encoding="utf-8"
            )
            match = _URL_RE.search(text)
            if match is None:
                raise ValueError(f"no Yandex download link in data/{page}.rst")
            mapping[page] = match.group(1)
    return mapping


def graph_pages(docs_dir: pathlib.Path) -> dict[str, str]:
    """Maps every graph name to its shared docs page stem.

    The inverse of :func:`page_to_graph`.

    Parameters
    ----------
    docs_dir : pathlib.Path
        The docs directory.

    Returns
    -------
    mapping : dict[str, str]
        Graph name -> data-page stem.
    """
    return {graph: page for page, graph in page_to_graph(docs_dir).items()}


def graph_to_category(docs_dir: pathlib.Path) -> dict[str, str]:
    """Maps every graph name to its category (derived from the site).

    Raises
    ------
    ValueError
        If a graph is listed in two categories.
    """
    page_graph = page_to_graph(docs_dir)
    mapping: dict[str, str] = {}
    for category, pages in category_pages(docs_dir).items():
        for page in pages:
            name = page_graph[page]
            if name in mapping:
                raise ValueError(
                    f"graph {name} is listed in both {mapping[name]} and {category}"
                )
            mapping[name] = category
    return mapping


def load_rows(csv_path: pathlib.Path) -> list[dict]:
    """Returns the CSV rows with ``num_reachable_pairs`` as int or None.

    Parameters
    ----------
    csv_path : pathlib.Path
        The reachable_pairs.csv file.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     p = pathlib.Path(tmp) / "r.csv"
    ...     n = p.write_text(
    ...         "graph,grammar,category,query_class,num_reachable_pairs\\n"
    ...         "g1,c_alias.cnf,c_alias_analysis,cfpq,42\\n"
    ...         "g2,c_alias.cnf,c_alias_analysis,cfpq,\\n"
    ...     )
    ...     rows = load_rows(p)
    ...     [r["num_reachable_pairs"] for r in rows]
    [42, None]
    """
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            val = row["num_reachable_pairs"]
            rows.append(
                {
                    "graph": row["graph"],
                    "grammar": row["grammar"],
                    "category": row["category"],
                    "query_class": row["query_class"],
                    "num_reachable_pairs": int(val) if val else None,
                }
            )
    return rows


def _cfpq_rows(rows: list[dict]) -> list[dict]:
    """Returns the CFPQ rows.

    The graph tables render CFPQ counts only; rows of other query classes
    are validated but not rendered there (their counts live in the
    per-graph tables of ``docs/reachable_pairs.rst``).
    """
    return [r for r in rows if r["query_class"] == "cfpq"]


def _section_title(docs_dir: pathlib.Path, category: str) -> str:
    """Returns the title line of a category page."""
    lines = (
        (docs_dir / "graphs" / f"{category}.rst")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    return lines[2].strip()


def render_tables_region(rows: list[dict], docs_dir: pathlib.Path) -> str:
    """Renders the per-category, per-graph table sections of reachable_pairs.rst.

    One section per category in :func:`category_order` order, titled like
    the category page; within a section, one subheading per graph (a
    ``:ref:`` targeting the graph's data page) followed by a list-table
    with the header Query | Reachable pairs and that graph's rows sorted
    by grammar file name (the extension makes the query class
    self-describing). A row without a computed value renders as
    ``not available``.

    Parameters
    ----------
    rows : list[dict]
        The CSV rows (see :func:`load_rows`); every row's graph must be
        listed in the docs (guaranteed by :func:`_validation_problems` in
        the CLI flow).
    docs_dir : pathlib.Path
        The docs directory (for the category order and titles).

    Returns
    -------
    region : str
        The section text without the marker lines.
    """
    graph_page = {graph: page for page, graph in page_to_graph(docs_dir).items()}
    sections: list[str] = []
    for category in category_order(docs_dir):
        title = _section_title(docs_dir, category)
        cat_rows = [r for r in rows if r["category"] == category]
        lines = [title, "-" * len(title), ""]
        if not cat_rows:
            lines.append("No reachable-pair counts have been computed for this")
            lines.append("category yet.")
        else:
            by_graph: dict[str, list[dict]] = {}
            for row in cat_rows:
                by_graph.setdefault(row["graph"], []).append(row)
            for i, graph in enumerate(sorted(by_graph)):
                if i:
                    lines.append("")
                heading = f":ref:`{graph_page[graph]}`"
                lines += [heading, "~" * len(heading), ""]
                lines += [
                    ".. list-table::",
                    "   :header-rows: 1",
                    "   :align: left",
                    "",
                    "   * - Query",
                    "     - Reachable pairs",
                ]
                for row in sorted(by_graph[graph], key=lambda r: r["grammar"]):
                    value = (
                        NOT_AVAILABLE
                        if row["num_reachable_pairs"] is None
                        else str(row["num_reachable_pairs"])
                    )
                    lines += [
                        f"   * - {row['grammar']}",
                        f"     - {value}",
                    ]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def replace_marked_region(
    text: str, region: str, begin_marker: str, end_marker: str
) -> tuple[str, bool]:
    """Returns text with the region between two marker lines replaced.

    The content strictly between the BEGIN and END marker lines is
    replaced; the markers themselves stay in place, separated from the
    region by blank lines. This is the generic helper behind
    :func:`update_reachable_pairs_page` and the applicable-graphs generator.

    Parameters
    ----------
    text : str
        The current source text.
    region : str
        The rendered region.
    begin_marker : str
        The line that opens the replaced region.
    end_marker : str
        The line that closes the replaced region.

    Returns
    -------
    updated : str
        The new text.
    changed : bool
        Whether anything was replaced.

    Raises
    ------
    ValueError
        If either marker is missing or out of order.

    Examples
    --------
    >>> text = "intro\\n<!--b-->\\nold\\n<!--e-->\\noutro\\n"
    >>> replace_marked_region(text, "new", "<!--b-->", "<!--e-->")[0].splitlines()
    ['intro', '<!--b-->', '', 'new', '', '<!--e-->', 'outro']
    """
    lines = text.splitlines()

    def marker_index(marker: str) -> int:
        for i, line in enumerate(lines):
            if line.strip() == marker:
                return i
        raise ValueError(f"markers {begin_marker!r}/{end_marker!r} not found")

    begin = marker_index(begin_marker)
    end = marker_index(end_marker)
    if begin > end:
        raise ValueError("markers are out of order")
    new_lines = lines[: begin + 1] + [""] + region.splitlines() + [""] + lines[end:]
    updated = "\n".join(new_lines)
    if text.endswith("\n"):
        updated += "\n"
    return updated, updated != text


def update_reachable_pairs_page(text: str, region: str) -> tuple[str, bool]:
    """Returns text with the reachable-pairs marker region replaced.

    The content strictly between the BEGIN and END marker lines is
    replaced; the markers themselves stay in place, separated from the
    region by blank lines.

    Parameters
    ----------
    text : str
        The current source of reachable_pairs.rst.
    region : str
        The rendered sections (see :func:`render_tables_region`).

    Returns
    -------
    updated : str
        The new text.
    changed : bool
        Whether anything was replaced.

    Raises
    ------
    ValueError
        If either marker is missing or out of order.
    """
    return replace_marked_region(text, region, BEGIN_MARKER, END_MARKER)


def _grammar_has_column(
    columns: list[tuple[str, Optional[str]]], graph: str, grammar: str
) -> bool:
    """Returns whether a (column header, grammar file) pair covers grammar.

    A None grammar file means the per-graph ``<graph>.cnf``.
    """
    return any(
        (g is None and grammar == f"{graph}.cnf") or g == grammar for _, g in columns
    )


def _validation_problems(rows: list[dict], site_map: dict[str, str]) -> list[str]:
    """Returns the CSV rows the site cannot account for.

    Every row must have a known ``query_class`` and a graph that the docs
    list in the row's category. The count-column check applies to the CFPQ
    rows only (the graph tables render CFPQ counts only); the other classes
    are rendered in the per-graph tables of ``docs/reachable_pairs.rst``,
    which need no per-category registration.
    """
    problems: list[str] = []
    for row in rows:
        if row["query_class"] not in QUERY_CLASSES:
            problems.append(
                f"CSV row {row['graph']}/{row['grammar']} has unknown "
                f"query_class {row['query_class']!r} "
                f"(expected one of {sorted(QUERY_CLASSES)})"
            )
        expected = site_map.get(row["graph"])
        if expected is None:
            problems.append(
                f"CSV graph {row['graph']} is not listed in any docs category"
            )
        elif expected != row["category"]:
            problems.append(
                f"CSV says {row['graph']} is in {row['category']}, "
                f"the docs say {expected}"
            )
    for row in _cfpq_rows(rows):
        columns = GRAMMAR_COLUMNS.get(row["category"])
        if columns is None:
            problems.append(
                f"CSV category {row['category']} has no count columns "
                "in GRAMMAR_COLUMNS"
            )
        elif not _grammar_has_column(columns, row["graph"], row["grammar"]):
            problems.append(
                f"CSV row {row['graph']}/{row['grammar']} has no count column "
                f"in category {row['category']}"
            )
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Check mode (default) exits with code 1 when any rendering disagrees
    with the CSV; ``--update`` rewrites them instead.

    Returns
    -------
    status : int
        0 when everything is in sync (or was updated), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check or update the per-graph reachable-pairs tables "
            "(docs/reachable_pairs.rst) against the CSV."
        )
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the tables from the CSV",
    )
    args = parser.parse_args(argv)

    rows = load_rows(REACHABLE_PAIRS_CSV)

    try:
        site_map = graph_to_category(DOCS_DIR)
    except ValueError as error:
        print(f"error: {error}")
        return 1

    # Validation problems block any update (all-or-nothing): a CSV row the
    # site cannot account for must be fixed in the CSV before anything is
    # rewritten.
    problems = _validation_problems(rows, site_map)
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1

    # Compute every update before writing anything.
    region = render_tables_region(rows, DOCS_DIR)
    page_text = REACHABLE_PAIRS_PAGE.read_text(encoding="utf-8")
    try:
        updated_page, _ = update_reachable_pairs_page(page_text, region)
    except ValueError as error:
        print(f"error: {error}")
        return 1

    if args.update:
        if updated_page != page_text:
            REACHABLE_PAIRS_PAGE.write_text(updated_page, encoding="utf-8")
            print(f"{REACHABLE_PAIRS_PAGE.relative_to(MAIN_FOLDER)}: region updated")
        print("OK: reachable-pairs tables are in sync with the CSV.")
        return 0

    problems = []
    if updated_page != page_text:
        problems.append(
            f"{REACHABLE_PAIRS_PAGE.relative_to(MAIN_FOLDER)}: the per-graph "
            "tables are out of sync with the CSV"
        )
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1
    print("OK: reachable-pairs tables are in sync with the CSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
