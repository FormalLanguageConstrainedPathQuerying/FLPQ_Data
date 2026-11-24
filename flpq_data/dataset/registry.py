"""Per-graph registry and the network-free metadata API."""

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

__all__ = [
    "GraphInfo",
    "QueryInfo",
    "graph_names",
    "graph_info",
    "categories",
]

#: The per-graph registry bundled with the package (the current dataset
#: version; see the "Graph registry" section of ``docs/flpq.rst``).
REGISTRY_JSON = pathlib.Path(__file__).parent / "registry.json"


@lru_cache(maxsize=1)
def _load_registry() -> dict:
    """Loads (and caches) the bundled registry JSON."""
    return json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class QueryInfo:
    """One query of a graph (a ``queries/`` dir of its archive).

    Attributes
    ----------
    query_class : str
        The query class (``cfpq``, ``rpq``, or ``mcfpq``).
    name : str
        The query name (the directory name under ``queries/<class>/``).
    representations : tuple[str, ...]
        The representation formats present for the query (e.g.
        ``("cnf", "rsm")``), sorted.
    """

    query_class: str
    name: str
    representations: tuple[str, ...]


@dataclass(frozen=True)
class GraphInfo:
    """The registry record of one graph.

    Attributes
    ----------
    name : str
        The graph name (the archive is ``<name>.tar.gz``).
    category : str
        The dataset category the graph belongs to.
    num_nodes : int
        The number of vertices (the declared MTX dimension).
    num_edges : int
        The number of stored edges (the sum of the MTX nnz).
    size_mb : float
        The archive size in MB (three decimals).
    sha256 : str
        The sha256 hex digest of the ``<name>.tar.gz`` archive.
    queries : tuple[QueryInfo, ...]
        The queries shipped with the graph, sorted by (class, name).
    """

    name: str
    category: str
    num_nodes: int
    num_edges: int
    size_mb: float
    sha256: str
    queries: tuple[QueryInfo, ...]


def _to_graph_info(name: str, record: dict) -> GraphInfo:
    """Maps one registry JSON record to a :class:`GraphInfo`."""
    return GraphInfo(
        name=name,
        category=record["category"],
        num_nodes=record["num_nodes"],
        num_edges=record["num_edges"],
        size_mb=record["size_mb"],
        sha256=record["sha256"],
        queries=tuple(
            QueryInfo(
                query_class=query["class"],
                name=query["name"],
                representations=tuple(query["representations"]),
            )
            for query in record["queries"]
        ),
    )


def graph_names() -> list[str]:
    """Returns the names of all downloadable graphs, sorted.

    Examples
    --------
    >>> from flpq_data import *
    >>> len(graph_names())
    114
    >>> graph_names()[0]
    'airflow'

    Returns
    -------
    names : list[str]
        The graph names of the current dataset version.
    """
    return sorted(_load_registry()["graphs"])


def graph_info(name: str) -> GraphInfo:
    """Returns the registry record of one graph.

    Parameters
    ----------
    name : str
        The graph name (see :func:`graph_names`).

    Examples
    --------
    >>> from flpq_data import *
    >>> info = graph_info("skos")
    >>> info.category, info.num_nodes, info.num_edges
    ('rdf', 144, 252)

    Returns
    -------
    info : GraphInfo
        The metadata of the graph.

    Raises
    ------
    FileNotFoundError
        If no graph with this name exists in the dataset.
    """
    records = _load_registry()["graphs"]
    if name not in records:
        raise FileNotFoundError(f"No graph with {name=} found")
    return _to_graph_info(name, records[name])


def categories() -> dict[str, list[str]]:
    """Returns the dataset categories mapped to their graph names.

    Examples
    --------
    >>> from flpq_data import *
    >>> "skos" in categories()["rdf"]
    True

    Returns
    -------
    mapping : dict[str, list[str]]
        Category -> sorted graph names; categories in sorted order.
    """
    records = _load_registry()["graphs"]
    by_category: dict[str, list[str]] = {}
    for name in sorted(records):
        by_category.setdefault(records[name]["category"], []).append(name)
    return {category: by_category[category] for category in sorted(by_category)}
