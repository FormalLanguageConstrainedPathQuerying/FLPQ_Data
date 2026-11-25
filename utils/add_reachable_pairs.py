"""Add reachable-pairs rows for the queries of one archive.

``flpq_data/dataset/reachable_pairs.csv`` is the single source of truth
behind the registry and the site's applicable-graphs renderings: every
graph x query pair needs a row. This tool derives those rows from a
validated archive instead of typing them by hand: for every
``queries/<class>/<query>/`` directory it emits one row with the query
directory name as the stem of the ``grammar`` file (the representation
file is picked in the order ``cnf > re > mcfg > rsm``) and the declared
entry count of the query's ``results.mtx`` as ``num_reachable_pairs``.

The archive must pass the structure checker first (full mode, or
``--partial`` for a partial archive); any structure problem aborts the
tool. Rows are inserted into the CSV preserving its ``(graph, grammar)``
sort order; a row that already exists, or a ``--category`` that disagrees
with the graph's existing rows, is reported and nothing is written.

Usage (from any directory)::

    python utils/add_reachable_pairs.py ARCHIVE.tar.gz --graph NAME \
        --category CAT [--partial] [--dry-run]
"""

import argparse
import csv
import pathlib
import tarfile
import tempfile
from typing import Optional, Sequence

from config import MAIN_FOLDER

from flpq_data.graphs.readwrite.mtx import mtx_file_header
from flpq_data.tools.check_archive_structure import (
    QUERY_CLASSES,
    unpack_single_dir,
    validate_archive,
)

__all__ = [
    "REACHABLE_PAIRS_CSV",
    "REPRESENTATION_PRIORITY",
    "representation_file",
    "derive_rows",
    "add_rows",
    "main",
]

REACHABLE_PAIRS_CSV = MAIN_FOLDER / "flpq_data" / "dataset" / "reachable_pairs.csv"

#: The order in which a query directory's representation files are
#: preferred for the row's ``grammar`` file (all current rows are ``.cnf``).
REPRESENTATION_PRIORITY = ("cnf", "re", "mcfg", "rsm")


def representation_file(query_dir: pathlib.Path) -> Optional[pathlib.Path]:
    """Return the query directory's preferred representation file.

    Parameters
    ----------
    query_dir : Path
        A ``queries/<class>/<query>/`` directory.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     d = pathlib.Path(tmp) / "q"
    ...     d.mkdir()
    ...     (d / "q.rsm").write_text("x")
    ...     (d / "q.cnf").write_text("x")
    ...     representation_file(d).name
    'q.cnf'

    Returns
    -------
    file : Path or None
        The alphabetically first file whose extension is in
        :data:`REPRESENTATION_PRIORITY` (a query may hold two files of one
        extension), or None when the directory holds no representation
        file.
    """
    by_ext: dict[str, pathlib.Path] = {}
    for path in sorted(query_dir.iterdir(), key=lambda p: p.name):
        if path.is_file():
            by_ext.setdefault(path.suffix.lstrip("."), path)
    for ext in REPRESENTATION_PRIORITY:
        if ext in by_ext:
            return by_ext[ext]
    return None


def derive_rows(root: pathlib.Path, graph: str, category: str) -> list[dict[str, str]]:
    """Derive the reachable-pairs rows of one validated archive.

    Parameters
    ----------
    root : Path
        The unpacked archive directory (it must have passed
        :func:`flpq_data.tools.check_archive_structure.validate_archive`, so
        every query
        directory holds a representation file and a parseable
        ``results.mtx``).
    graph : str
        The graph name the rows are recorded under.
    category : str
        The graph's category.

    Returns
    -------
    rows : list[dict[str, str]]
        One row per query directory, with the CSV's five fields as string
        values.

    Raises
    ------
    ValueError
        If a query directory lacks a representation file, holds a
        representation file not named after the query directory, or lacks a
        parseable ``results.mtx`` (all only possible for an unvalidated
        tree — the structure checker refuses such trees).
    """
    rows: list[dict[str, str]] = []
    queries_dir = root / "queries"
    for cls in sorted(QUERY_CLASSES):
        cls_dir = queries_dir / cls
        if not cls_dir.is_dir():
            continue
        for query_dir in sorted(cls_dir.iterdir()):
            if not query_dir.is_dir():
                continue
            rep = representation_file(query_dir)
            if rep is None:
                raise ValueError(
                    f"queries/{cls}/{query_dir.name}: no representation file"
                )
            expected = f"{query_dir.name}{rep.suffix}"
            if rep.name != expected:
                raise ValueError(
                    f"queries/{cls}/{query_dir.name}/{rep.name}: representation "
                    f"files must be named after the query directory "
                    f"(expected {expected})"
                )
            header = mtx_file_header(query_dir / "results.mtx")
            if header is None:
                raise ValueError(
                    f"queries/{cls}/{query_dir.name}/results.mtx: cannot be parsed"
                )
            rows.append(
                {
                    "graph": graph,
                    "grammar": rep.name,
                    "category": category,
                    "query_class": cls,
                    "num_reachable_pairs": str(header[2]),
                }
            )
    return rows


def add_rows(csv_path: pathlib.Path, rows: list[dict[str, str]]) -> list[str]:
    """Insert ``rows`` into the reachable-pairs CSV.

    The file's ``(graph, grammar)`` sort order is preserved. Nothing is
    written when any problem is found.

    Parameters
    ----------
    csv_path : Path
        The reachable_pairs.csv file to update in place.
    rows : list[dict[str, str]]
        The rows to add (the CSV's five fields as string values).

    Returns
    -------
    problems : list[str]
        Every duplicate row and category disagreement found; an empty list
        means the rows were written.
    """
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        existing = [row for row in reader]

    problems: list[str] = []
    keys = {(row[0], row[3], pathlib.Path(row[1]).stem) for row in existing}
    categories = {row[0]: row[2] for row in existing}
    for row in rows:
        key = (row["graph"], row["query_class"], pathlib.Path(row["grammar"]).stem)
        if key in keys:
            problems.append(
                f"{row['graph']},{row['grammar']}: row already exists in the CSV"
            )
        elif row["graph"] in categories and categories[row["graph"]] != row["category"]:
            problems.append(
                f"{row['graph']}: category {row['category']!r} disagrees with "
                f"the existing rows' {categories[row['graph']]!r}"
            )
    if problems:
        return problems

    merged = sorted(
        existing + [list(row.values()) for row in rows], key=lambda r: (r[0], r[1])
    )
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(merged)
    return []


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Validates one archive, derives its reachable-pairs rows, and inserts
    them into ``flpq_data/dataset/reachable_pairs.csv`` (or prints them
    with ``--dry-run``).

    Returns
    -------
    status : int
        0 when the rows were added (or printed), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Add the reachable-pairs rows of one validated archive to "
            "flpq_data/dataset/reachable_pairs.csv."
        )
    )
    parser.add_argument(
        "path", help="path to a .tar.gz archive or an unpacked archive directory"
    )
    parser.add_argument(
        "--graph", required=True, help="the graph name the rows are recorded under"
    )
    parser.add_argument("--category", required=True, help="the graph's category")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="treat the archive as a partial one (new queries for an existing graph)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the rows instead of writing the CSV",
    )
    args = parser.parse_args(argv)

    path = pathlib.Path(args.path)
    if path.is_dir():
        return _run(path, args)
    if path.suffix != ".gz" or not tarfile.is_tarfile(path):
        print(f"error: {path.name}: not a .tar.gz archive")
        return 1
    if path.name[: -len(".tar.gz")] != args.graph:
        print(f"error: {path.name} must be named after the graph ({args.graph}.tar.gz)")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        try:
            root = unpack_single_dir(path, pathlib.Path(tmp))
        except ValueError as error:
            print(f"error: {error}")
            return 1
        return _run(root, args)


def _run(root: pathlib.Path, args: argparse.Namespace) -> int:
    """Validate ``root`` and add (or print) its rows."""
    if root.name != args.graph:
        print(
            f"error: top-level directory {root.name!r} "
            f"does not match --graph {args.graph!r}"
        )
        return 1

    problems = validate_archive(root, partial=args.partial)
    if problems:
        for problem in problems:
            print(f"error: {problem}")
        return 1

    rows = derive_rows(root, args.graph, args.category)
    if args.dry_run:
        for row in rows:
            print(",".join(row.values()))
        return 0

    problems = add_rows(REACHABLE_PAIRS_CSV, rows)
    if problems:
        for problem in problems:
            print(f"error: {problem}")
        return 1
    for row in rows:
        print(
            f"added {row['graph']},{row['grammar']} ({row['query_class']}, "
            f"{row['num_reachable_pairs']} pairs)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
