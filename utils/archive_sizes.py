"""Keep the Size (MB) column of the docs graph tables in sync with S3.

Every per-category graph table has a ``Download`` column linking to the
archive on Yandex Object Storage. This tool keeps the ``Size (MB)`` column
next to it accurate:

- check mode (default): HEAD every referenced archive and report the rows
  whose size cell disagrees with the stored object;
- ``--update``: fetch all sizes first, then rewrite the tables (inserting
  the column where it is missing).

Sizes are keyed by full URL: the ``4.0.0``, ``5.0.0``, and ``6.0.0``
prefixes hold same-named archives with different content.

Usage (from any directory)::

    python utils/archive_sizes.py [--update]
"""

import argparse
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from config import MAIN_FOLDER
from sizes import format_size_mb

__all__ = [
    "SIZE_COLUMN",
    "DOWNLOAD_COLUMN",
    "GRAPH_TABLE_FILES",
    "GraphTable",
    "iter_graph_tables",
    "header_columns",
    "extract_url",
    "fetch_sizes",
    "update_table",
    "main",
]

#: The header cell of the size column in the graph tables.
SIZE_COLUMN = "Size (MB)"

#: The download-column header every graph table must have to be processed.
DOWNLOAD_COLUMN = "Download"

#: The docs files holding graph tables, as glob patterns relative to docs/.
#: ``old_graphs`` is historical data and is intentionally not maintained by
#: this tool, so its table is not scanned.
GRAPH_TABLE_FILES: tuple[str, ...] = ("graphs/*.rst",)

_ROW_RE = re.compile(r"^(\s+)\* - (.*)$")
# The space after the dash is optional: empty cells are bare ``-`` lines.
_CELL_RE = re.compile(r"^(\s+)- ?(.*)$")
_URL_RE = re.compile(r"<(https?://[^>]+)>")


@dataclass
class GraphTable:
    """A ``list-table`` with a ``Download`` column.

    Attributes
    ----------
    start_line : int
        The 0-based index of the ``.. list-table::`` line in the file text.
    header_rows : int
        The number of header rows (the ``:header-rows:`` option; 1 when the
        table declares none). ``rows[:header_rows]`` are the header rows and
        ``rows[header_rows:]`` are the data rows.
    rows : list[list[tuple[int, str]]]
        The table rows in order. Each row is a list of ``(line_index,
        cell_text)`` pairs in column order, where ``line_index`` is the
        0-based index of the cell's line.
    """

    start_line: int
    header_rows: int
    rows: list[list[tuple[int, str]]]


def iter_graph_tables(text: str) -> list[GraphTable]:
    """Returns the graph tables (list-tables with a Download column) in text.

    A table is a graph table when any of its header rows (the
    ``:header-rows:`` count, ``1`` when the table declares none) contains a
    ``Download`` cell. Tables without one are skipped, as are files'
    non-table content. Only the flat one-cell-per-line layout used by the
    docs graph tables is understood.

    Parameters
    ----------
    text : str
        The reStructuredText source of a docs page.

    Examples
    --------
    >>> text = (
    ...     ".. list-table::\\n   :header-rows: 1\\n\\n"
    ...     "   * - Graph\\n     - Download\\n"
    ...     "   * - wc\\n     - `wc.tar.gz <https://example.com/wc.tar.gz>`_ \\u2605\\n"
    ... )
    >>> tables = iter_graph_tables(text)
    >>> len(tables), [cell for _, cell in tables[0].rows[0]]
    (1, ['Graph', 'Download'])

    Returns
    -------
    tables : list[GraphTable]
        The graph tables of the text, in order.
    """
    lines = text.splitlines()
    tables: list[GraphTable] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() != ".. list-table::":
            i += 1
            continue
        # The directive content runs until the next non-blank line at column 0.
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t"):
            j += 1
        table = _parse_table(lines, i, j)
        if table is not None:
            tables.append(table)
        i = j
    return tables


def _header_rows_of(lines: list[str], start: int, end: int) -> int:
    """Returns the ``:header-rows:`` count of the directive at ``lines[start]``.

    Scans the directive's option lines (the ``:name: value`` lines before any
    table row) and returns the value of ``:header-rows:``; ``1`` when the
    table declares none.
    """
    for idx in range(start + 1, end):
        line = lines[idx].strip()
        if not line:
            continue
        if line.startswith("*"):
            break
        if line.startswith(":header-rows:"):
            value = line.split(":", 2)[2].strip()
            if value.isdigit():
                return max(int(value), 1)
    return 1


def _indent_of(lines: list[str], line_index: int) -> str:
    """Returns the leading whitespace of a line."""
    line = lines[line_index]
    return line[: len(line) - len(line.lstrip())]


def _parse_table(lines: list[str], start: int, end: int) -> Optional[GraphTable]:
    """Parses the list-table at ``lines[start]`` or returns None.

    A row starts at a ``* - <first cell>`` line or at a bare ``* -`` line (a
    row whose first cell is empty, as in the leading cell of a multi-row
    header group); its remaining cells follow as indented ``- <cell>`` lines.
    """
    rows: list[list[tuple[int, str]]] = []
    current: Optional[list[tuple[int, str]]] = None
    for idx in range(start + 1, end):
        row_match = _ROW_RE.match(lines[idx])
        if row_match is not None:
            current = [(idx, row_match.group(2))]
            rows.append(current)
            continue
        if current is not None and re.match(r"^\s+\* ?-?$", lines[idx]):
            current = []
            rows.append(current)
            continue
        cell_match = _CELL_RE.match(lines[idx])
        if cell_match is not None and current is not None:
            current.append((idx, cell_match.group(2)))
    if not rows:
        return None
    header_rows = _header_rows_of(lines, start, end)
    if not any(
        DOWNLOAD_COLUMN in [cell for _, cell in row] for row in rows[:header_rows]
    ):
        return None
    return GraphTable(start_line=start, header_rows=header_rows, rows=rows)


def header_columns(table: GraphTable) -> list[str]:
    """Returns the flat per-column header keys of a table.

    The non-empty header cells of each column (across the ``header_rows``
    header rows) are joined with ``" / "`` in row order. A column that is empty
    in a header row contributes nothing to that row, so a merged group renders
    as a single key per column (e.g. ``"Reachable pairs / subClassOf"``). A
    table whose every column is empty yields one empty key.

    Parameters
    ----------
    table : GraphTable
        A parsed graph table.

    Examples
    --------
    >>> from archive_sizes import GraphTable
    >>> table = GraphTable(
    ...     start_line=0, header_rows=1,
    ...     rows=[[(0, "Graph"), (1, "Size (MB)"), (2, "Download")],
    ...           [(3, "wc"), (4, "0.002"), (5, "link")]],
    ... )
    >>> header_columns(table)
    ['Graph', 'Size (MB)', 'Download']

    Returns
    -------
    columns : list[str]
        One flat key per column, in column order.
    """
    header = table.rows[: table.header_rows]
    width = max((len(row) for row in header), default=0)
    columns: list[str] = []
    for col in range(width):
        parts = [row[col][1] for row in header if col < len(row) and row[col][1]]
        columns.append(" / ".join(parts))
    return columns


def extract_url(cell: str) -> Optional[str]:
    """Returns the URL of a download cell like `` `name.tar.gz <URL>`_ 📥 ``.

    Parameters
    ----------
    cell : str
        The text of a table cell.

    Examples
    --------
    >>> extract_url("`wc.tar.gz <https://example.com/wc.tar.gz>`_ 📥")
    'https://example.com/wc.tar.gz'
    >>> extract_url("no link here") is None
    True

    Returns
    -------
    url : str or None
        The first http(s) URL in angle brackets, if any.
    """
    match = _URL_RE.search(cell)
    return match.group(1) if match is not None else None


def _head_size(url: str, timeout: float) -> int:
    """Returns the Content-Length of a single HEAD request to url."""
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        length = response.headers.get("Content-Length")
    if length is None:
        raise RuntimeError(f"no Content-Length header in the HEAD response of {url}")
    return int(length)


def _fetch_one(url: str, timeout: float) -> int:
    """Fetches one size, retrying once."""
    last_error: Optional[Exception] = None
    for _ in range(2):
        try:
            return _head_size(url, timeout)
        except Exception as error:
            last_error = error
    raise RuntimeError(f"HEAD request to {url} failed: {last_error}")


def fetch_sizes(
    urls: Iterable[str], *, timeout: float = 30.0, workers: int = 8
) -> dict[str, int]:
    """Returns the stored size in bytes of every URL (HEAD requests).

    Parameters
    ----------
    urls : Iterable[str]
        The archive URLs; duplicates are fetched once.
    timeout : float, optional
        Per-request timeout in seconds. Default: 30.
    workers : int, optional
        Number of concurrent HEAD requests. Default: 8.

    Examples
    --------
    >>> fetch_sizes([])
    {}

    Returns
    -------
    sizes : dict[str, int]
        Mapping URL -> Content-Length in bytes.

    Raises
    ------
    RuntimeError
        If any URL cannot be fetched (after one retry); nothing is returned,
        so callers can treat updates as all-or-nothing.
    """
    unique = sorted(set(urls))
    sizes: dict[str, int] = {}
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_one, url, timeout): url for url in unique}
        for future in as_completed(futures):
            url = futures[future]
            try:
                sizes[url] = future.result()
            except Exception as error:
                failures.append(str(error))
    if failures:
        raise RuntimeError(
            "could not fetch the stored size of:\n  " + "\n  ".join(sorted(failures))
        )
    return sizes


def update_table(text: str, sizes: dict[str, int]) -> tuple[str, int]:
    """Returns text with every graph table's Size (MB) column filled in.

    Where the column is missing it is inserted before the Download column
    (header and all rows); where it exists, rows whose value disagrees with
    ``sizes`` are fixed in place. Lines of tables that need no change keep
    their exact text.

    Parameters
    ----------
    text : str
        The reStructuredText source of a docs page.
    sizes : dict[str, int]
        Mapping archive URL -> stored size in bytes (see :func:`fetch_sizes`).

    Examples
    --------
    >>> text = (
    ...     ".. list-table::\n   :header-rows: 1\n\n"
    ...     "   * - Graph\n     - Download\n"
    ...     "   * - wc\n     - `wc.tar.gz <https://example.com/wc.tar.gz>`_ 📥\n"
    ... )
    >>> updated, changed = update_table(text, {"https://example.com/wc.tar.gz": 2472})
    >>> changed
    1
    >>> "Size (MB)" in updated and "0.002" in updated
    True

    Returns
    -------
    updated : str
        The new text.
    changed : int
        The number of data rows inserted or fixed.
    """
    lines = text.splitlines()
    insertions: list[tuple[int, str]] = []
    replacements: list[tuple[int, str]] = []
    changed = 0
    for table in iter_graph_tables(text):
        columns = header_columns(table)
        download_index = next(
            i for i, cell in enumerate(columns) if cell == DOWNLOAD_COLUMN
        )
        has_size = SIZE_COLUMN in columns
        if not has_size:
            last_header = table.rows[table.header_rows - 1]
            line_index, _ = last_header[download_index]
            indent = _indent_of(lines, line_index)
            insertions.append((line_index, f"{indent}- {SIZE_COLUMN}"))
        for row in table.rows[table.header_rows :]:
            if len(row) <= download_index:
                continue
            url = extract_url(row[download_index][1])
            if url is None or url not in sizes:
                value = ""
            else:
                value = format_size_mb(sizes[url])
            if has_size:
                cell_index, current = row[download_index - 1]
                if value and current != value:
                    indent = _indent_of(lines, cell_index)
                    replacements.append((cell_index, f"{indent}- {value}"))
                    changed += 1
            else:
                # A bare '-' line keeps the row aligned when no value is known.
                line_index, _ = row[download_index]
                indent = _indent_of(lines, line_index)
                cell = f"{indent}- {value}" if value else f"{indent}-"
                insertions.append((line_index, cell))
                changed += 1

    for line_index, new_line in sorted(replacements, key=lambda p: p[0]):
        lines[line_index] = new_line
    for line_index, new_line in sorted(insertions, key=lambda p: p[0], reverse=True):
        lines.insert(line_index, new_line)

    updated = "\n".join(lines)
    if text.endswith("\n"):
        updated += "\n"
    return updated, changed


def _table_urls(text: str) -> list[str]:
    """Returns the archive URLs referenced by the graph tables of text."""
    urls: list[str] = []
    for table in iter_graph_tables(text):
        columns = header_columns(table)
        download_index = next(
            i for i, cell in enumerate(columns) if cell == DOWNLOAD_COLUMN
        )
        for row in table.rows[table.header_rows :]:
            if len(row) <= download_index:
                continue
            url = extract_url(row[download_index][1])
            if url is not None:
                urls.append(url)
    return urls


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Check mode (default) exits with code 1 when any table row disagrees with
    the stored object size; ``--update`` rewrites the tables instead.

    Returns
    -------
    status : int
        0 when all graph tables are in sync (or were updated), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check or update the Size (MB) column of the docs graph tables "
            "against the stored archive sizes."
        )
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the tables from the stored object sizes",
    )
    args = parser.parse_args(argv)

    docs_dir = MAIN_FOLDER / "docs"
    files = sorted(
        path for pattern in GRAPH_TABLE_FILES for path in docs_dir.glob(pattern)
    )
    texts = {path: path.read_text(encoding="utf-8") for path in files}

    urls = [url for text in texts.values() for url in _table_urls(text)]
    if not urls:
        print("No graph tables with download links found; nothing to do.")
        return 1

    try:
        sizes = fetch_sizes(urls)
    except RuntimeError as error:
        print(f"error: {error}")
        return 1

    if args.update:
        for path in files:
            updated, changed = update_table(texts[path], sizes)
            if changed:
                path.write_text(updated, encoding="utf-8")
                print(f"{path.relative_to(MAIN_FOLDER)}: updated {changed} row(s)")
        print(f"Checked {len(urls)} archive(s); tables are in sync.")
        return 0

    problems: list[str] = []
    rows_checked = 0
    for path in files:
        rel_path = path.relative_to(MAIN_FOLDER)
        text = texts[path]
        for table in iter_graph_tables(text):
            columns = header_columns(table)
            download_index = columns.index(DOWNLOAD_COLUMN)
            has_size = SIZE_COLUMN in columns
            if not has_size:
                problems.append(
                    f"{rel_path}:{table.start_line + 1}: no {SIZE_COLUMN} column"
                )
            for row in table.rows[table.header_rows :]:
                rows_checked += 1
                name = row[0][1]
                if len(row) <= download_index:
                    problems.append(
                        f"{rel_path}:{row[0][0] + 1}: {name}: no download link"
                    )
                    continue
                url = extract_url(row[download_index][1])
                if url is None or url not in sizes:
                    line_no = row[download_index][0] + 1
                    problems.append(
                        f"{rel_path}:{line_no}: {name}: no fetchable download URL"
                    )
                    continue
                expected = format_size_mb(sizes[url])
                if has_size and row[download_index - 1][1] != expected:
                    size_cell = row[download_index - 1]
                    problems.append(
                        f"{rel_path}:{size_cell[0] + 1}: {name}: "
                        f"table says {size_cell[1]}, stored is {expected}"
                    )
    if problems:
        print("\n".join(problems))
        print(f"FAILED: {len(problems)} problem(s) in {rows_checked} row(s).")
        return 1
    print(f"OK: {rows_checked} row(s) in sync with the stored archive sizes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
