"""Render the per-class applicable-graphs lists from the reachable-pairs CSV.

The registry ``flpq_data/dataset/reachable_pairs.csv`` has one row per
applicable graph x query pair; its ``query_class`` column names the
``queries/<class>/`` directory in the graph archives. For each query class
the class section page (``docs/queries/<class>/index.rst``) renders, between
the ``applicable-graphs`` markers, the graphs that carry at least one query
of that class — grouped by graph category and cross-linking the shared
per-graph pages, so no graph page is duplicated.

The tool follows the pattern of :mod:`reachable_pairs_tables` and reuses its
helpers:

- check mode (default): report every page whose region disagrees with the
  CSV and exit non-zero, so it can gate a commit;
- ``--update``: rewrite the drifted regions.

Usage (from any directory)::

    python utils/applicable_graphs.py [--update]
"""

import argparse
import pathlib
from typing import Optional, Sequence

from config import MAIN_FOLDER
from reachable_pairs_tables import (
    _section_title,
    _validation_problems,
    category_order,
    display_path,
    graph_pages,
    graph_to_category,
    load_rows,
    replace_marked_region,
)

__all__ = [
    "BEGIN_MARKER",
    "END_MARKER",
    "REACHABLE_PAIRS_CSV",
    "CLASS_PAGES",
    "graph_pages",
    "render_class_region",
    "main",
]

REACHABLE_PAIRS_CSV = MAIN_FOLDER / "flpq_data" / "dataset" / "reachable_pairs.csv"
DOCS_DIR = MAIN_FOLDER / "docs"

#: The marker lines delimiting the generated applicable-graphs region of a
#: class page. Plain reST comments, so they do not render.
BEGIN_MARKER = ".. applicable-graphs:begin"
END_MARKER = ".. applicable-graphs:end"

#: Query class -> the class section page that lists its applicable graphs.
CLASS_PAGES: dict[str, pathlib.Path] = {
    "cfpq": DOCS_DIR / "queries" / "cfpq" / "index.rst",
    "rpq": DOCS_DIR / "queries" / "rpq" / "index.rst",
    "mcfpq": DOCS_DIR / "queries" / "mcfpq" / "index.rst",
}


def render_class_region(
    rows: list[dict], docs_dir: pathlib.Path, query_class: str
) -> str:
    """Renders one class's applicable-graphs region.

    The graphs that carry at least one query of ``query_class`` are grouped
    by graph category (in :func:`reachable_pairs_tables.category_order`
    order) and rendered as a ``^^^^`` subsection per category with a sorted
    list of ``:ref:`` links to the shared per-graph pages. A class without
    any registered graph renders a placeholder sentence.

    Parameters
    ----------
    rows : list[dict]
        The CSV rows (see :func:`reachable_pairs_tables.load_rows`).
    docs_dir : pathlib.Path
        The docs directory (for category order, titles, and page mapping).
    query_class : str
        The query class (``cfpq``, ``rpq``, or ``mcfpq``).

    Returns
    -------
    region : str
        The rendered region without the marker lines.

    Raises
    ------
    ValueError
        If a graph of ``query_class`` is not listed in any docs category.
    """
    graphs = sorted({r["graph"] for r in rows if r["query_class"] == query_class})
    if not graphs:
        return (
            f"No {query_class.upper()} queries have been added to the graph "
            "catalog yet."
        )

    pages = graph_pages(docs_dir)
    category_of = graph_to_category(docs_dir)

    sections: list[str] = []
    for category in category_order(docs_dir):
        in_category = [g for g in graphs if category_of.get(g) == category]
        if not in_category:
            continue
        title = _section_title(docs_dir, category)
        lines = [title, "^" * len(title), ""]
        for graph in in_category:
            page = pages.get(graph)
            if page is None:
                raise ValueError(f"graph {graph} is not listed in any docs category")
            lines.append(f"* :ref:`{page}`")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Check mode (default) exits with code 1 when any class page disagrees with
    the CSV; ``--update`` rewrites the regions instead.

    Returns
    -------
    status : int
        0 when everything is in sync (or was updated), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check or update the per-class applicable-graphs lists "
            "(the regions of docs/queries/*/index.rst) against the CSV."
        )
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the applicable-graphs regions from the CSV",
    )
    args = parser.parse_args(argv)

    rows = load_rows(REACHABLE_PAIRS_CSV)

    # Validation problems block any update (all-or-nothing, like
    # reachable_pairs_tables.py): a CSV row the site cannot account for must
    # be fixed in the CSV before anything is rewritten.
    try:
        site_map = graph_to_category(DOCS_DIR)
        render = {cls: render_class_region(rows, DOCS_DIR, cls) for cls in CLASS_PAGES}
    except ValueError as error:
        print(f"error: {error}")
        return 1

    problems = _validation_problems(rows, site_map)
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1

    updates: list[tuple[pathlib.Path, str, str]] = []
    for cls, path in CLASS_PAGES.items():
        text = path.read_text(encoding="utf-8")
        try:
            updated, _ = replace_marked_region(
                text, render[cls], BEGIN_MARKER, END_MARKER
            )
        except ValueError as error:
            print(f"error: {display_path(path)}: {error}")
            return 1
        updates.append((path, text, updated))

    if args.update:
        for path, text, updated in updates:
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                print(f"{display_path(path)}: region updated")
        print("OK: applicable-graphs lists are in sync with the CSV.")
        return 0

    problems = [
        f"{display_path(path)}: the applicable-graphs list is out of sync with the CSV"
        for path, text, updated in updates
        if updated != text
    ]
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1
    print("OK: applicable-graphs lists are in sync with the CSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
