import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from archive_sizes import (
    extract_url,
    fetch_sizes,
    header_columns,
    iter_graph_tables,
    update_table,
)

WC_URL = "https://cfpq-data.storage.yandexcloud.net/5.0.0/graph/wc.tar.gz"
BZIP_URL = "https://cfpq-data.storage.yandexcloud.net/5.0.0/graph/bzip.tar.gz"

TABLE_WITHOUT_SIZE = (
    ".. list-table::\n"
    "   :header-rows: 1\n"
    "\n"
    "   * - Graph\n"
    "     - Num Nodes\n"
    "     - Download\n"
    f"   * - :ref:`wc`\n"
    "     - 332\n"
    f"     - `wc.tar.gz <{WC_URL}>`_ 📥\n"
    f"   * - :ref:`bzip`\n"
    "     - 632\n"
    f"     - `bzip.tar.gz <{BZIP_URL}>`_ 📥\n"
)

SIZES = {WC_URL: 2472, BZIP_URL: 3601}


def test_iter_graph_tables_parses_rows_and_cells():
    tables = iter_graph_tables(TABLE_WITHOUT_SIZE)

    assert len(tables) == 1
    table = tables[0]
    assert [cell for _, cell in table.rows[0]] == ["Graph", "Num Nodes", "Download"]
    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`wc`",
        "332",
        f"`wc.tar.gz <{WC_URL}>`_ 📥",
    ]
    # Cell line indices point at the right lines of the source.
    for line_index, _ in table.rows[1]:
        assert (
            TABLE_WITHOUT_SIZE.splitlines()[line_index]
            .lstrip()
            .startswith(("* -", "- "))
        )


def test_iter_graph_tables_keeps_empty_cells_aligned():
    # rdf.rst rows have a bare ``-`` line for grammars that do not apply.
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Graph\n"
        "     - subClassOf\n"
        "     - broaderTransitive\n"
        "     - Download\n"
        f"   * - :ref:`skos`\n"
        "     - 1\n"
        "     -\n"
        f"     - `skos.tar.gz <{WC_URL}>`_ 📥\n"
    )

    table = iter_graph_tables(text)[0]

    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`skos`",
        "1",
        "",
        f"`skos.tar.gz <{WC_URL}>`_ 📥",
    ]


def test_iter_graph_tables_parses_multi_row_header():
    # A two-row header: a bare ``* -`` row start (row 2) plus the option line.
    # docutils merges the group positionally, so ``header_columns`` joins the
    # non-empty header cells of each column with " / " in row order.
    text = (
        ".. list-table::\n"
        "   :header-rows: 2\n"
        "   :align: left\n"
        "\n"
        "   * - Graph\n"
        "     - Num Nodes\n"
        "     - Reachable pairs\n"
        "     -\n"
        "     - Size (MB)\n"
        "     - Download\n"
        "   * -\n"
        "     -\n"
        "     - subClassOf\n"
        "     - type\n"
        "     -\n"
        "     -\n"
        f"   * - :ref:`skos`\n"
        "     - 144\n"
        "     - 1\n"
        "     - 2\n"
        "     - 0.002\n"
        f"     - `skos.tar.gz <{WC_URL}>`_ 📥\n"
    )

    table = iter_graph_tables(text)[0]

    assert table.header_rows == 2
    assert len(table.rows) == 3
    # docutils merges the group positionally: the row-2 subheaders land in the
    # columns after the group label, so header_columns joins them per column.
    assert header_columns(table) == [
        "Graph",
        "Num Nodes / subClassOf",
        "Reachable pairs / type",
        "",
        "Size (MB)",
        "Download",
    ]
    # Data rows start after the two header rows and keep all their cells.
    assert [cell for _, cell in table.rows[2]] == [
        ":ref:`skos`",
        "144",
        "1",
        "2",
        "0.002",
        f"`skos.tar.gz <{WC_URL}>`_ 📥",
    ]


def test_header_columns_single_row_is_flat():
    table = iter_graph_tables(TABLE_WITHOUT_SIZE)[0]
    assert table.header_rows == 1
    assert header_columns(table) == ["Graph", "Num Nodes", "Download"]


def test_update_table_fills_size_with_multi_row_header():
    text = (
        ".. list-table::\n"
        "   :header-rows: 2\n"
        "   :align: left\n"
        "\n"
        "   * - Graph\n"
        "     - Num Nodes\n"
        "     - Reachable pairs\n"
        "     -\n"
        "     - Size (MB)\n"
        "     - Download\n"
        "   * -\n"
        "     -\n"
        "     - subClassOf\n"
        "     - type\n"
        "     -\n"
        "     -\n"
        f"   * - :ref:`skos`\n"
        "     - 144\n"
        "     - 1\n"
        "     - 2\n"
        "     - 9.99\n"
        f"     - `skos.tar.gz <{WC_URL}>`_ 📥\n"
    )

    updated, changed = update_table(text, SIZES)

    # Size (MB) is located via header_columns (column index 4); the size cell
    # is the one before Download (index 5 -> data index 4).
    assert changed == 1
    table = iter_graph_tables(updated)[0]
    assert header_columns(table)[4] == "Size (MB)"
    assert header_columns(table)[5] == "Download"
    assert [cell for _, cell in table.rows[2]] == [
        ":ref:`skos`",
        "144",
        "1",
        "2",
        "0.002",
        f"`skos.tar.gz <{WC_URL}>`_ 📥",
    ]
    # Idempotent: the size column is now correct, nothing else to change.
    again, changed_again = update_table(updated, SIZES)
    assert changed_again == 0
    assert again == updated


def test_iter_graph_tables_skips_tables_without_download_column():
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Source area\n"
        "     - Number of graphs\n"
        "   * - rdf\n"
        "     - 20\n"
    )

    assert iter_graph_tables(text) == []


def test_extract_url():
    assert extract_url(f"`wc.tar.gz <{WC_URL}>`_ 📥") == WC_URL
    assert extract_url("no link here") is None


def test_update_table_inserts_missing_size_column():
    updated, changed = update_table(TABLE_WITHOUT_SIZE, SIZES)

    assert changed == 2
    # Re-parse the result: the column sits right before Download in every row.
    table = iter_graph_tables(updated)[0]
    assert [cell for _, cell in table.rows[0]] == [
        "Graph",
        "Num Nodes",
        "Size (MB)",
        "Download",
    ]
    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`wc`",
        "332",
        "0.002",
        f"`wc.tar.gz <{WC_URL}>`_ 📥",
    ]
    assert [cell for _, cell in table.rows[2]] == [
        ":ref:`bzip`",
        "632",
        "0.004",
        f"`bzip.tar.gz <{BZIP_URL}>`_ 📥",
    ]


def test_update_table_is_idempotent():
    updated, _ = update_table(TABLE_WITHOUT_SIZE, SIZES)

    again, changed = update_table(updated, SIZES)

    assert changed == 0
    assert again == updated


def test_update_table_fixes_wrong_values_in_place():
    wrong = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Graph\n"
        "     - Num Nodes\n"
        "     - Size (MB)\n"
        "     - Download\n"
        f"   * - :ref:`wc`\n"
        "     - 332\n"
        "     - 9.99\n"
        f"     - `wc.tar.gz <{WC_URL}>`_ 📥\n"
        f"   * - :ref:`bzip`\n"
        "     - 632\n"
        "     - 0.004\n"
        f"     - `bzip.tar.gz <{BZIP_URL}>`_ 📥\n"
    )

    updated, changed = update_table(wrong, SIZES)

    assert changed == 1  # only the wc row was wrong
    table = iter_graph_tables(updated)[0]
    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`wc`",
        "332",
        "0.002",
        f"`wc.tar.gz <{WC_URL}>`_ 📥",
    ]
    # The already-correct bzip row is untouched.
    assert [cell for _, cell in table.rows[2]] == [
        ":ref:`bzip`",
        "632",
        "0.004",
        f"`bzip.tar.gz <{BZIP_URL}>`_ 📥",
    ]


def test_update_table_multi_grammar_column_alignment():
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Graph\n"
        "     - Num Nodes\n"
        "     - subClassOf\n"
        "     - subClassOf_type\n"
        "     - type\n"
        "     - Download\n"
        f"   * - :ref:`skos`\n"
        "     - 144\n"
        "     - 1\n"
        "     - 30\n"
        "     - 29\n"
        f"     - `skos.tar.gz <{WC_URL}>`_ 📥\n"
    )

    updated, changed = update_table(text, SIZES)

    assert changed == 1
    table = iter_graph_tables(updated)[0]
    assert [cell for _, cell in table.rows[0]] == [
        "Graph",
        "Num Nodes",
        "subClassOf",
        "subClassOf_type",
        "type",
        "Size (MB)",
        "Download",
    ]


def test_update_table_with_empty_cells():
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Graph\n"
        "     - subClassOf\n"
        "     - broaderTransitive\n"
        "     - Download\n"
        f"   * - :ref:`skos`\n"
        "     - 1\n"
        "     -\n"
        f"     - `skos.tar.gz <{WC_URL}>`_ 📥\n"
    )

    updated, changed = update_table(text, SIZES)

    assert changed == 1
    table = iter_graph_tables(updated)[0]
    assert [cell for _, cell in table.rows[0]] == [
        "Graph",
        "subClassOf",
        "broaderTransitive",
        "Size (MB)",
        "Download",
    ]
    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`skos`",
        "1",
        "",
        "0.002",
        f"`skos.tar.gz <{WC_URL}>`_ 📥",
    ]


def test_update_table_keeps_rows_without_url_aligned():
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Graph\n"
        "     - Download\n"
        "   * - :ref:`wc`\n"
        f"     - `wc.tar.gz <{WC_URL}>`_ 📥\n"
        "   * - :ref:`broken`\n"
        "     - no link here\n"
    )

    updated, changed = update_table(text, SIZES)

    assert changed == 2
    table = iter_graph_tables(updated)[0]
    # The broken row gets a bare '-' cell so the columns stay aligned.
    assert [cell for _, cell in table.rows[1]] == [
        ":ref:`wc`",
        "0.002",
        f"`wc.tar.gz <{WC_URL}>`_ 📥",
    ]
    assert [cell for _, cell in table.rows[2]] == [":ref:`broken`", "", "no link here"]


def test_update_table_leaves_non_graph_tables_untouched():
    text = (
        ".. list-table::\n"
        "   :header-rows: 1\n"
        "\n"
        "   * - Source area\n"
        "     - Number of graphs\n"
        "   * - rdf\n"
        "     - 20\n"
    )

    updated, changed = update_table(text, SIZES)

    assert changed == 0
    assert updated == text


def test_update_table_preserves_trailing_newline():
    no_trailing = TABLE_WITHOUT_SIZE.rstrip("\n")

    updated, _ = update_table(no_trailing, SIZES)

    assert not updated.endswith("\n")

    updated, _ = update_table(TABLE_WITHOUT_SIZE, SIZES)

    assert updated.endswith("\n")
    assert not updated.endswith("\n\n")


class _HeadHandler(BaseHTTPRequestHandler):
    sizes: dict[str, int] = {}

    def do_HEAD(self):
        size = self.sizes.get(self.path)
        if size is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", str(size))
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture()
def head_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HeadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def test_fetch_sizes_returns_content_lengths(head_server):
    base = f"http://127.0.0.1:{head_server.server_address[1]}"
    _HeadHandler.sizes = {"/a.tar.gz": 100, "/b.tar.gz": 2_000_000}

    sizes = fetch_sizes([f"{base}/a.tar.gz", f"{base}/b.tar.gz", f"{base}/a.tar.gz"])

    assert sizes == {f"{base}/a.tar.gz": 100, f"{base}/b.tar.gz": 2_000_000}


def test_fetch_sizes_empty_input(head_server):
    assert fetch_sizes([]) == {}


def test_fetch_sizes_raises_when_object_is_missing(head_server):
    base = f"http://127.0.0.1:{head_server.server_address[1]}"
    _HeadHandler.sizes = {}

    with pytest.raises(RuntimeError, match="could not fetch the stored size"):
        fetch_sizes([f"{base}/nope.tar.gz"])
