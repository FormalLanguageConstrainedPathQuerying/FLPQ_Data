"""Render the per-category graph tables from the registry and the CSV.

Every per-category page (``docs/graphs/<category>.rst``) carries one
list-table with a row per graph of the category. Every cell of the table
is machine-derivable, so the table is rendered — between the
``graph-table`` markers — instead of maintained by hand:

- ``Graph`` — a ``:ref:`` to the graph's data page (the page mapping is
  derived from the site, as in :mod:`reachable_pairs_tables`);
- ``Num Nodes``/``Num Edges``/``Size (MB)`` — from the registry
  (``flpq_data/dataset/registry.json``; the size is rendered from the
  exact ``size_bytes`` with the shared MB formatting of
  ``utils/sizes.py``);
- the ``Reachable pairs`` count columns — from
  ``flpq_data/dataset/reachable_pairs.csv`` (CFPQ rows only; the
  (column, grammar) pairs per category are ``GRAMMAR_COLUMNS``);
- ``Download`` — the archive name plus the dataset URL.

Rows are sorted by (num_nodes, name).

This tool keeps the rendering accurate:

- check mode (default): report every table region that disagrees with
  the registry and the CSV and exit non-zero, so it can gate a commit;
- ``--update``: rewrite the drifted regions.

The check is offline: it reads the bundled registry and the CSV only.

Usage (from any directory)::

    python utils/graph_tables.py [--update]
"""

import argparse
import pathlib
from typing import Optional, Sequence

from reachable_pairs_tables import (
    DOCS_DIR,
    GRAMMAR_COLUMNS,
    NOT_AVAILABLE,
    REACHABLE_PAIRS_CSV,
    _validation_problems,
    category_order,
    display_path,
    graph_pages,
    graph_to_category,
    load_rows,
    replace_marked_region,
)
from sizes import format_size_mb

from flpq_data.dataset.data import DATASET_URL
from flpq_data.dataset.registry import GraphInfo, categories, graph_info, graph_names

__all__ = [
    "BEGIN_MARKER",
    "END_MARKER",
    "render_category_table",
    "_registry_problems",
    "main",
]

#: The marker lines delimiting the generated graph table of a category
#: page. Plain reST comments, so they do not render.
BEGIN_MARKER = ".. graph-table:begin"
END_MARKER = ".. graph-table:end"

#: Sentinel for a (graph, grammar) pair absent from the CSV (the grammar
#: does not apply to the graph) — distinct from a present-but-None count.
_MISSING = object()


def render_category_table(
    category: str,
    graphs: dict[str, GraphInfo],
    rows: list[dict],
    pages: dict[str, str],
) -> str:
    """Renders the graph table of one category page.

    One row per graph of ``graphs`` (the category's registry records),
    sorted by (num_nodes, name). The count columns are
    ``GRAMMAR_COLUMNS[category]`` (none when the category is absent): a
    cell is the CFPQ count of the (graph, grammar) pair,
    ``not available`` when the pair exists with no computed value yet, or
    empty when the grammar does not apply to the graph.

    Parameters
    ----------
    category : str
        The category stem; selects the count columns.
    graphs : dict[str, GraphInfo]
        The category's registry records, graph name -> record.
    rows : list[dict]
        The reachable-pairs CSV rows (see
        :func:`reachable_pairs_tables.load_rows`).
    pages : dict[str, str]
        Graph name -> data-page stem (see
        :func:`reachable_pairs_tables.graph_pages`).

    Examples
    --------
    >>> from flpq_data.dataset.registry import GraphInfo
    >>> info = GraphInfo("g", "c", 2, 3, 0.002, 2000, "x" * 64, ())
    >>> text = render_category_table(
    ...     "c", {"g": info},
    ...     [{"graph": "g", "grammar": "g.cnf", "category": "c",
    ...       "query_class": "cfpq", "num_reachable_pairs": 7}],
    ...     {"g": "page"},
    ... )
    >>> text.splitlines()[0]
    '.. list-table::'

    Returns
    -------
    region : str
        The rendered ``list-table`` text without the marker lines.

    Raises
    ------
    KeyError
        If a graph has no data page in ``pages``.
    """
    columns = GRAMMAR_COLUMNS.get(category, [])
    by_pair: dict[tuple[str, str], Optional[int]] = {
        (r["graph"], r["grammar"]): r["num_reachable_pairs"]
        for r in rows
        if r["query_class"] == "cfpq"
    }
    lines = [".. list-table::", ""]
    header = (
        ["Graph", "Num Nodes", "Num Edges"]
        + [header for header, _ in columns]
        + ["Size (MB)", "Download"]
    )
    lines.append(f"   * - {header[0]}")
    lines += [f"     - {cell}" for cell in header[1:]]
    for name in sorted(graphs, key=lambda n: (graphs[n].num_nodes, n)):
        info = graphs[name]
        cells = [f":ref:`{pages[name]}`", str(info.num_nodes), str(info.num_edges)]
        for _, grammar_file in columns:
            grammar = grammar_file if grammar_file is not None else f"{name}.cnf"
            value = by_pair.get((name, grammar), _MISSING)
            if value is _MISSING:
                cells.append("")
            elif value is None:
                cells.append(NOT_AVAILABLE)
            else:
                cells.append(str(value))
        cells.append(format_size_mb(info.size_bytes))
        cells.append(f"`{name}.tar.gz <{DATASET_URL}{name}.tar.gz>`_ 📥")
        lines.append(f"   * - {cells[0]}")
        lines += [f"     - {cell}" if cell else "     -" for cell in cells[1:]]
    return "\n".join(lines)


def _registry_problems(rows: list[dict], site_map: dict[str, str]) -> list[str]:
    """Returns the registry/CSV/docs disagreements the renderer cannot account for.

    Every registry graph must be listed in the docs (in its registry
    category) and carry at least one reachable-pairs row; every CSV row
    must name a registry graph; every docs category must have at least
    one registry graph. Together with
    :func:`reachable_pairs_tables._validation_problems` (CSV vs docs),
    the three sources are cross-checked pairwise.
    """
    problems: list[str] = []
    registry = categories()
    registry_names = {name for names in registry.values() for name in names}
    csv_graphs = {r["graph"] for r in rows}
    for name in graph_names():
        info = graph_info(name)
        expected = site_map.get(name)
        if expected is None:
            problems.append(f"registry graph {name} is not listed in any docs category")
        elif expected != info.category:
            problems.append(
                f"registry says {name} is in {info.category}, the docs say {expected}"
            )
        if name not in csv_graphs:
            problems.append(f"registry graph {name} has no reachable-pairs row")
    for row in rows:
        if row["graph"] not in registry_names:
            problems.append(f"CSV graph {row['graph']} is not in the registry")
    for category in sorted(set(site_map.values())):
        if not registry.get(category):
            problems.append(f"docs category {category} has no registry graphs")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Check mode (default) exits with code 1 when any table region disagrees
    with the registry and the CSV; ``--update`` rewrites the regions
    instead.

    Returns
    -------
    status : int
        0 when all graph tables are in sync (or were updated), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check or update the per-category graph tables "
            "(docs/graphs/*.rst) against the registry and the "
            "reachable-pairs CSV."
        )
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the tables from the registry and the CSV",
    )
    args = parser.parse_args(argv)

    rows = load_rows(REACHABLE_PAIRS_CSV)

    try:
        site_map = graph_to_category(DOCS_DIR)
        pages = graph_pages(DOCS_DIR)
    except ValueError as error:
        print(f"error: {error}")
        return 1

    # Validation problems block any update (all-or-nothing, like
    # reachable_pairs_tables.py): a record the other sources cannot
    # account for must be fixed before anything is rewritten.
    problems = _validation_problems(rows, site_map) + _registry_problems(rows, site_map)
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1

    registry = categories()
    updates: list[tuple[pathlib.Path, str, str]] = []
    for category in category_order(DOCS_DIR):
        path = DOCS_DIR / "graphs" / f"{category}.rst"
        text = path.read_text(encoding="utf-8")
        graphs = {name: graph_info(name) for name in registry.get(category, [])}
        region = render_category_table(category, graphs, rows, pages)
        try:
            updated, _ = replace_marked_region(text, region, BEGIN_MARKER, END_MARKER)
        except ValueError as error:
            print(f"error: {display_path(path)}: {error}")
            return 1
        updates.append((path, text, updated))

    if args.update:
        for path, text, updated in updates:
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                print(f"{display_path(path)}: table updated")
        print("OK: graph tables are in sync with the registry and the CSV.")
        return 0

    problems = [
        f"{display_path(path)}: the graph table is out of sync "
        "with the registry and the CSV"
        for path, text, updated in updates
        if updated != text
    ]
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s).")
        return 1
    print(f"OK: {len(updates)} graph table(s) in sync with the registry and the CSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
