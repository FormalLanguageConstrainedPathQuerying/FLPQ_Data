"""Read (and write) a graph from (and to) a directory of MatrixMarket files."""

import logging
import os
import pathlib
import tempfile
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

import networkx as nx

from flpq_data.graphs.readwrite.graph import iter_edges_from_graph

__all__ = [
    "filename_to_label",
    "label_to_filename",
    "iter_edges_from_mtx_file",
    "mtx_file_header",
    "iter_edges_from_mtx_dir",
    "mtx_dir_from_edges",
    "graph_from_mtx_dir",
    "graph_to_mtx_dir",
]

#: The header lines of the Boolean MatrixMarket files of the dataset.
_MTX_HEADER = (
    "%%MatrixMarket matrix coordinate pattern general",
    "%%GraphBLAS type bool",
)


def filename_to_label(filename: Union[pathlib.Path, str]) -> str:
    """Returns the edge label of a MatrixMarket file name.

    The file name is the label itself (``load_5.mtx`` holds the edges labeled
    ``load_5``).

    Parameters
    ----------
    filename : Union[Path, str]
        The name of a MatrixMarket file.

    Examples
    --------
    >>> filename_to_label("type.mtx")
    'type'
    >>> filename_to_label("alloc_r.mtx")
    'alloc_r'
    >>> filename_to_label("load_5.mtx")
    'load_5'

    Returns
    -------
    label : str
        The edge label of the file.
    """
    label = pathlib.Path(filename).stem

    logging.info(f"Map {filename=} to {label=}")

    return label


def label_to_filename(label: str) -> str:
    """Returns the canonical MatrixMarket file name of an edge label.

    The canonical style is ``<label>.mtx``; reading it back with
    :func:`filename_to_label` returns the same label.

    Parameters
    ----------
    label : str
        The edge label.

    Examples
    --------
    >>> label_to_filename("load_5")
    'load_5.mtx'
    >>> label_to_filename("alloc_r")
    'alloc_r.mtx'

    Returns
    -------
    filename : str
        The file name of the label.
    """
    return f"{label}.mtx"


def iter_edges_from_mtx_file(
    path: Union[pathlib.Path, str],
) -> Iterator[Tuple[int, int]]:
    """Yields the entries of one Boolean MatrixMarket file as a stream.

    The file must follow the dataset format: a two-line header
    (``%%MatrixMarket matrix coordinate pattern general`` /
    ``%%GraphBLAS type bool``), a dimension line (``rows cols nnz``), and one
    ``u v`` entry per line (0-based indices, no values). The file is read line
    by line, so the memory stays O(1) in the number of entries.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the MatrixMarket file.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> p = pathlib.Path(tempfile.mkdtemp()) / "a.mtx"
    >>> _ = p.write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 2\\n0 1\\n1 2\\n"
    ... )
    >>> list(iter_edges_from_mtx_file(p))
    [(0, 1), (1, 2)]

    Returns
    -------
    entries : Iterator[Tuple[int, int]]
        The ``(u, v)`` entry tuples in file order.

    Raises
    ------
    ValueError
        If the file has an unexpected header, a malformed entry line, or its
        entry count differs from the declared nnz.
    """
    path = pathlib.Path(path)

    with open(path, "r") as f:
        if tuple(f.readline().strip() for _ in range(2)) != _MTX_HEADER:
            raise ValueError(f"Unexpected header in {path=}")
        rows, cols, nnz = map(int, f.readline().split())

        count = 0
        for line in f:
            if not line.strip():
                continue
            i, j = map(int, line.split())
            yield i, j
            count += 1

    if count != nnz:
        raise ValueError(f"{path=} declares {nnz} entries but has {count}")


def mtx_file_header(
    path: Union[pathlib.Path, str],
) -> Optional[Tuple[int, int, int]]:
    """The ``(rows, cols, nnz)`` declared by one Boolean MatrixMarket file.

    Returns ``None`` when the file does not follow the dataset format (the
    two-line header and a dimension line of three integers). Streams — only
    the first lines are read.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the MatrixMarket file.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> p = pathlib.Path(tempfile.mkdtemp()) / "a.mtx"
    >>> _ = p.write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 2\\n0 1\\n1 2\\n"
    ... )
    >>> mtx_file_header(p)
    (3, 3, 2)
    >>> _ = p.write_text("%%MatrixMarket matrix coordinate real\\n1 1 0\\n")
    >>> mtx_file_header(p) is None
    True

    Returns
    -------
    header : Optional[Tuple[int, int, int]]
        The declared ``(rows, cols, nnz)``, or ``None`` if the header does not
        match the dataset format.
    """
    path = pathlib.Path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            if f.readline().rstrip() != _MTX_HEADER[0]:
                return None
            if f.readline().rstrip() != _MTX_HEADER[1]:
                return None
            rows, cols, nnz = (int(value) for value in f.readline().split())
    except (OSError, ValueError):
        return None
    return rows, cols, nnz


def iter_edges_from_mtx_dir(
    path: Union[pathlib.Path, str],
) -> Iterator[Tuple[int, str, int]]:
    """Yields the edges of a directory of MatrixMarket files as a stream.

    Each ``*.mtx`` file is a Boolean pattern matrix with one entry per edge
    of a single label (0-based indices, no values); the label is derived from
    the file name by :func:`filename_to_label`. The files are read line by
    line, so the memory stays O(1) in the number of edges.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the directory with the MatrixMarket files.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> d = pathlib.Path(tempfile.mkdtemp()) / "graph"
    >>> _ = d.mkdir(parents=True)
    >>> _ = (d / "a.mtx").write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 2\\n0 1\\n1 2\\n"
    ... )
    >>> _ = (d / "b_5.mtx").write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 1\\n2 0\\n"
    ... )
    >>> list(iter_edges_from_mtx_dir(d))
    [(0, 'a', 1), (1, 'a', 2), (2, 'b_5', 0)]

    Returns
    -------
    edges : Iterator[Tuple[int, str, int]]
        The ``(u, label, v)`` edge tuples in file order.

    Raises
    ------
    ValueError
        If a file has an unexpected header or its entry count differs from
        the declared nnz.
    """
    path = pathlib.Path(path)

    for mtx_file in sorted(path.glob("*.mtx")):
        label = filename_to_label(mtx_file.name)
        for u, v in iter_edges_from_mtx_file(mtx_file):
            yield u, label, v

    logging.info(f"Stream edges from {path=}")


def _node_index(node: Any) -> int:
    """Returns the matrix index of a node id.

    Parameters
    ----------
    node : Any
        A node id — a non-negative integer or its string form.

    Returns
    -------
    index : int
        The matrix index of the node.

    Raises
    ------
    TypeError
        If the node id is not a non-negative integer (or digit string).
    """
    if isinstance(node, int):
        index = node
    elif isinstance(node, str):
        try:
            index = int(node)
        except ValueError as e:
            raise TypeError(
                f"The node ids must be non-negative integers (got {node!r})"
            ) from e
    else:
        raise TypeError(f"The node ids must be non-negative integers (got {node!r})")

    if index < 0:
        raise TypeError(f"The node ids must be non-negative integers (got {node!r})")

    return index


def mtx_dir_from_edges(
    edges: Iterable[Tuple[Any, str, Any]],
    path: Union[pathlib.Path, str],
    *,
    dimension: Optional[int] = None,
) -> pathlib.Path:
    """Writes an edge stream to a directory of MatrixMarket files.

    One Boolean pattern matrix per label (the canonical name from
    :func:`label_to_filename`), 0-based indices and no values — the layout of
    :func:`iter_edges_from_mtx_dir`. The stream is consumed in a single pass:
    each label's edges are appended to its own temporary file (at most one of
    which is open at a time, so the number of labels is unbounded), and after
    the stream ends every file is finalized with its three-line header. The
    memory stays O(1) in the number of edges; the disk holds one extra copy
    of the edge data until the files are finalized.

    Parameters
    ----------
    edges : Iterable[Tuple[Any, str, Any]]
        The ``(u, label, v)`` edge tuples to write; node ids must be
        non-negative integers (digit strings are accepted).

    path : Union[Path, str]
        The path to the directory where the MatrixMarket files will be saved.

    dimension : int, optional
        The matrix dimensions to declare in every file header. Defaults to
        the largest node index plus one; give it explicitly when the graph
        has isolated nodes that carry no edges (e.g. an in-memory graph).

    Examples
    --------
    >>> import pathlib, tempfile
    >>> d = pathlib.Path(tempfile.mkdtemp()) / "graph"
    >>> _ = mtx_dir_from_edges([(0, "a", 1)], d)
    >>> (d / "a.mtx").read_text().splitlines()[2:]
    ['2 2 1', '0 1']

    Returns
    -------
    path : Path
        Path to the directory where the MatrixMarket files will be saved.

    Raises
    ------
    TypeError
        If a node id is not a non-negative integer (or digit string).

    ValueError
        If ``dimension`` is given but smaller than the largest node index
        plus one.
    """
    dest = pathlib.Path(path)
    dest.mkdir(parents=True, exist_ok=True)

    max_node = -1
    counts: Dict[str, int] = {}
    temps: Dict[str, pathlib.Path] = {}
    finals: List[pathlib.Path] = []
    current: Optional[Tuple[str, Any]] = None  # (label, open handle)

    def _cleanup() -> None:
        for temp in temps.values():
            temp.unlink(missing_ok=True)
        for final in finals:
            final.unlink(missing_ok=True)

    try:
        for u, label, v in edges:
            i = _node_index(u)
            j = _node_index(v)
            max_node = max(max_node, i, j)

            if current is not None and current[0] != label:
                current[1].close()
                current = None
            if current is None:
                if label not in temps:
                    fd, name = tempfile.mkstemp(dir=dest, prefix=".mtx-", suffix=".tmp")
                    os.close(fd)
                    temps[label] = pathlib.Path(name)
                    counts[label] = 0
                current = (label, open(temps[label], "a"))

            current[1].write(f"{i} {j}\n")
            counts[label] += 1

        if current is not None:
            current[1].close()

        if dimension is not None and dimension < max_node + 1:
            raise ValueError(
                f"{dimension=} is smaller than the largest node index plus one "
                f"({max_node + 1})"
            )

        dim = dimension if dimension is not None else max_node + 1
        for label in sorted(counts):
            final = dest / label_to_filename(label)
            finals.append(final)
            with open(temps[label], "r") as src, open(final, "w") as dst:
                dst.write(f"{_MTX_HEADER[0]}\n{_MTX_HEADER[1]}\n")
                dst.write(f"{dim} {dim} {counts[label]}\n")
                for line in src:
                    dst.write(line)
            temps[label].unlink()
    except Exception:
        # Close the open handle first: Windows cannot unlink a file that is
        # still open (the exception may have fired before close-on-switch).
        if current is not None:
            current[1].close()
        # All-or-nothing: no temp or partially written final file survives.
        _cleanup()
        raise

    dest = dest.resolve()

    logging.info(f"Save edges to {dest=}")

    return dest


def graph_from_mtx_dir(path: Union[pathlib.Path, str]) -> nx.MultiDiGraph:
    """Loads a graph from a directory of MatrixMarket files.

    Each ``*.mtx`` file in the directory is a Boolean pattern matrix with one
    entry per edge of a single label (0-based indices, no values); the label
    is derived from the file name by :func:`filename_to_label`.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the directory with the MatrixMarket files.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> d = pathlib.Path(tempfile.mkdtemp()) / "graph"
    >>> _ = d.mkdir(parents=True)
    >>> _ = (d / "a.mtx").write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 2\\n0 1\\n1 2\\n"
    ... )
    >>> _ = (d / "b_5.mtx").write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n3 3 1\\n2 0\\n"
    ... )
    >>> g = graph_from_mtx_dir(d)
    >>> sorted((u, v, e["label"]) for u, v, e in g.edges(data=True))
    [(0, 1, 'a'), (1, 2, 'a'), (2, 0, 'b_5')]

    Returns
    -------
    g : MultiDiGraph
        Loaded graph.
    """
    path = pathlib.Path(path)
    graph = nx.MultiDiGraph()

    for u, label, v in iter_edges_from_mtx_dir(path):
        graph.add_edge(u, v, label=label)

    logging.info(f"Load {graph=} from {path=}")

    return graph


def graph_to_mtx_dir(
    graph: nx.MultiDiGraph, path: Union[pathlib.Path, str]
) -> pathlib.Path:
    """Saves the ``graph`` to a directory of MatrixMarket files by ``path``.

    One file per edge label (the canonical name from
    :func:`label_to_filename`); each file is a Boolean pattern matrix with
    0-based indices and no values. The node ids must be non-negative integers
    (the matrix dimensions are the largest node id plus one).

    Parameters
    ----------
    graph : MultiDiGraph
        Graph to save.

    path : Union[Path, str]
        The path to the directory where the MatrixMarket files will be saved.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> g = nx.MultiDiGraph()
    >>> _ = g.add_edges_from(
    ...     [(0, 1, {"label": "a"}), (1, 2, {"label": "a"}),
    ...      (2, 0, {"label": "b_5"})]
    ... )
    >>> d = pathlib.Path(tempfile.mkdtemp())
    >>> path = graph_to_mtx_dir(g, d / "graph")
    >>> g2 = graph_from_mtx_dir(path)
    >>> sorted((u, v, e["label"]) for u, v, e in g2.edges(data=True)) == \\
    ...     sorted((u, v, e["label"]) for u, v, e in g.edges(data=True))
    True

    Returns
    -------
    path : Path
        Path to the directory where the graph will be saved.
    """
    nodes = list(graph.nodes())
    if any(not isinstance(node, int) or node < 0 for node in nodes):
        raise TypeError(f"The node ids of {graph=} must be non-negative integers")

    # The explicit dimension preserves isolated nodes that carry no edges.
    dest = mtx_dir_from_edges(
        iter_edges_from_graph(graph),
        path,
        dimension=max(nodes, default=-1) + 1,
    )

    logging.info(f"Save {graph=} to {dest=}")

    return dest
