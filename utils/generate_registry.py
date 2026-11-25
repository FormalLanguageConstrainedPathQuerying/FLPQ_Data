"""Generate flpq_data/dataset/registry.json from the dataset on S3.

The registry is the machine-readable per-graph metadata of the current
dataset version: category, node and edge counts, archive size, sha256, and
the query list of every graph (see the "Graph registry" section of
``docs/flpq.rst``). Field sources:

- the graph list and ``category`` from ``reachable_pairs.csv``;
- ``num_nodes``/``num_edges`` from the MTX headers of the archive's
  ``graph/`` dir (the declared dimension and nnz — read streaming, without
  building the networkx graph);
- ``size_mb`` and ``sha256`` of the downloaded ``.tar.gz``;
- ``queries`` from the archive's ``queries/`` tree.

The tool downloads every archive, so it runs locally only — never in CI
(no-network policy). Re-run it whenever the dataset changes (a new graph or
query), commit the result, and upload it to the bucket as
``<version>/registry.json`` with ``utils/upload_to_s3.py``.

Usage (from any directory)::

    python utils/generate_registry.py
"""

import argparse
import hashlib
import json
import pathlib
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Sequence

import requests
from config import MAIN_FOLDER
from reachable_pairs_tables import load_rows

from flpq_data.config import DATASET_VERSION
from flpq_data.dataset.data import DATASET_URL
from flpq_data.graphs.readwrite.mtx import mtx_file_header
from flpq_data.tools.check_archive_structure import (
    QUERY_CLASSES,
    _graph_dimensions,
)

__all__ = [
    "REGISTRY_CSV",
    "_sha256",
    "archive_record",
    "build_record",
    "build_registry",
    "write_registry",
    "main",
]

#: The reachable-pairs CSV the graph list and categories are read from.
REGISTRY_CSV = MAIN_FOLDER / "flpq_data" / "dataset" / "reachable_pairs.csv"


def _sha256(path: pathlib.Path) -> str:
    """Returns the sha256 hex digest of a file, streamed in 1 MiB chunks.

    Parameters
    ----------
    path : Path
        The file to hash.

    Examples
    --------
    >>> import pathlib, tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     p = pathlib.Path(tmp) / "f"
    ...     p.write_bytes(b"abc")
    ...     _sha256(p)
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

    Returns
    -------
    digest : str
        The lowercase hex sha256 of the file content.
    """
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_record(graph_dir: pathlib.Path) -> dict:
    """Returns the archive-derived fields of one registry record.

    ``graph_dir`` is an unpacked graph archive (the single top-level
    directory of a ``.tar.gz``). The node count is the declared matrix
    dimension and the edge count the sum of the declared nnz — read from
    the MTX headers only (streaming, O(1) memory: building the networkx
    graph of a large archive exhausts RAM when several run concurrently);
    the query list walks the ``queries/`` tree with the class ->
    representation mapping of the structure checker.

    Parameters
    ----------
    graph_dir : Path
        The unpacked archive directory (holds ``graph/`` and ``queries/``).

    Examples
    --------
    >>> import pathlib, tempfile
    >>> root = pathlib.Path(tempfile.mkdtemp()) / "g"
    >>> _ = (root / "graph").mkdir(parents=True)
    >>> _ = (root / "graph" / "a.mtx").write_text(
    ...     "%%MatrixMarket matrix coordinate pattern general\\n"
    ...     "%%GraphBLAS type bool\\n2 2 1\\n0 1\\n"
    ... )
    >>> _ = (root / "queries" / "cfpq" / "q").mkdir(parents=True)
    >>> _ = (root / "queries" / "cfpq" / "q" / "q.cnf").write_text("S <- a S | eps\\n")
    >>> record = archive_record(root)
    >>> record["num_nodes"], record["num_edges"]
    (2, 1)
    >>> record["queries"]
    [{'class': 'cfpq', 'name': 'q', 'representations': ['cnf']}]

    Returns
    -------
    record : dict
        ``{"num_nodes": int, "num_edges": int, "queries": list[dict]}`` with
        one query entry per query dir: ``{"class", "name",
        "representations"}``, sorted by (class, name) and with sorted
        representation names.

    Raises
    ------
    ValueError
        If the label matrices do not share one declared dimension or a MTX
        file does not follow the dataset format.
    """
    mtx_dir = graph_dir / "graph"
    dimensions = _graph_dimensions(mtx_dir)
    if len(dimensions) != 1:
        raise ValueError(
            f"All label matrices must declare the same dimensions, "
            f"found {sorted(dimensions)}"
        )
    rows, cols = dimensions.pop()
    num_edges = 0
    for mtx_file in sorted(mtx_dir.glob("*.mtx")):
        header = mtx_file_header(mtx_file)
        if header is None:
            raise ValueError(f"{mtx_file} does not follow the dataset MTX format")
        num_edges += header[2]

    queries: list[dict] = []
    queries_root = graph_dir / "queries"
    for class_name in sorted(QUERY_CLASSES):
        class_dir = queries_root / class_name
        if not class_dir.is_dir():
            continue
        representations = {ext.lstrip(".") for ext in QUERY_CLASSES[class_name]}
        for query_dir in sorted(class_dir.iterdir()):
            if not query_dir.is_dir():
                continue
            reps = sorted(
                p.suffix.lstrip(".")
                for p in query_dir.iterdir()
                if p.suffix.lstrip(".") in representations
            )
            queries.append(
                {"class": class_name, "name": query_dir.name, "representations": reps}
            )

    return {
        "num_nodes": rows,
        "num_edges": num_edges,
        "queries": queries,
    }


def _download(url: str, archive: pathlib.Path) -> None:
    """Downloads url to archive, streaming with a timeout and one retry.

    A stalled connection must not hang the run: both the connect and the
    read phases are bounded, and a failed attempt is retried once before
    the error propagates (the partial file is overwritten on the retry).

    Parameters
    ----------
    url : str
        The public URL of the archive.
    archive : Path
        The destination file (overwritten).

    Raises
    ------
    RuntimeError
        If the download fails twice.
    """
    last_error: Optional[Exception] = None
    for _ in range(2):
        try:
            with requests.get(url, stream=True, timeout=(30.0, 60.0)) as r:
                r.raise_for_status()
                with archive.open("wb") as f:
                    shutil.copyfileobj(r.raw, f)
            return
        except Exception as error:
            last_error = error
    raise RuntimeError(f"download of {url} failed: {last_error}")


def build_record(name: str, url: str, workdir: pathlib.Path) -> dict:
    """Downloads one archive and returns its full registry record fields.

    The archive is streamed to ``workdir`` (see :func:`_download`), hashed
    and sized while on disk, then unpacked for :func:`archive_record`; the
    temp files are removed again, so ``workdir`` may be shared between
    concurrent calls (one per graph name).

    Parameters
    ----------
    name : str
        The graph name (the archive is ``<name>.tar.gz``).
    url : str
        The public URL of the archive.
    workdir : Path
        A writable directory for the temp archive and extraction.

    Returns
    -------
    record : dict
        The fields of :func:`archive_record` plus ``size_mb`` (the stored
        size in MB, three decimals), ``size_bytes`` (the exact stored size
        in bytes), and ``sha256`` (of the ``.tar.gz``).

    Raises
    ------
    ValueError
        If the archive does not contain a single top-level directory.
    """
    archive = workdir / f"{name}.tar.gz"
    _download(url, archive)

    size = archive.stat().st_size
    sha256 = _sha256(archive)

    extract_dir = pathlib.Path(tempfile.mkdtemp(dir=workdir))
    try:
        shutil.unpack_archive(archive, extract_dir)
        entries = list(extract_dir.iterdir())
        if len(entries) != 1 or not entries[0].is_dir():
            raise ValueError(
                f"Archive {name} must contain a single top-level directory, "
                f"found {entries=}"
            )
        record = archive_record(entries[0])
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
        archive.unlink()

    record["size_mb"] = round(size / 1_000_000, 3)
    record["size_bytes"] = size
    record["sha256"] = sha256
    return record


def build_registry(workdir: pathlib.Path) -> dict:
    """Builds the full registry of the current dataset version.

    The graph list and categories come from :data:`REGISTRY_CSV` (one
    category per graph — a conflict is an error); every archive is fetched
    concurrently from ``DATASET_URL``. All-or-nothing: if any archive fails,
    nothing is returned and the failures are listed in the error.

    Parameters
    ----------
    workdir : Path
        A writable directory for the per-graph temp files.

    Returns
    -------
    registry : dict
        ``{"version": DATASET_VERSION, "graphs": {<name>: {"category",
        "num_nodes", "num_edges", "size_mb", "size_bytes", "sha256",
        "queries"}}}`` with graph names in sorted order.

    Raises
    ------
    ValueError
        If a graph has conflicting categories in the CSV.
    RuntimeError
        If any archive cannot be downloaded or processed; nothing is
        returned, so callers can treat generation as all-or-nothing.
    """
    rows = load_rows(REGISTRY_CSV)
    category: dict[str, str] = {}
    for row in rows:
        existing = category.setdefault(row["graph"], row["category"])
        if existing != row["category"]:
            raise ValueError(
                f"Graph {row['graph']} has conflicting categories: "
                f"{existing} and {row['category']}"
            )

    names = sorted(category)
    records: dict[str, dict] = {}
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        for name in names:
            url = DATASET_URL + f"{name}.tar.gz"
            futures[pool.submit(build_record, name, url, workdir)] = name
        for future in as_completed(futures):
            name = futures[future]
            try:
                records[name] = future.result()
            except Exception as error:
                failures.append(f"{name}: {error}")

    if failures:
        raise RuntimeError(
            "could not build the registry for:\n  " + "\n  ".join(sorted(failures))
        )

    graphs = {
        name: {
            "category": category[name],
            "num_nodes": records[name]["num_nodes"],
            "num_edges": records[name]["num_edges"],
            "size_mb": records[name]["size_mb"],
            "size_bytes": records[name]["size_bytes"],
            "sha256": records[name]["sha256"],
            "queries": records[name]["queries"],
        }
        for name in names
    }
    return {"version": DATASET_VERSION, "graphs": graphs}


def write_registry(registry: dict, path: pathlib.Path) -> None:
    """Writes the registry as deterministic JSON (2-space indent, newline).

    Parameters
    ----------
    registry : dict
        The registry as returned by :func:`build_registry`.
    path : Path
        The destination file (overwritten).

    Examples
    --------
    >>> import pathlib, tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     p = pathlib.Path(tmp) / "registry.json"
    ...     write_registry({"version": "6.0.0", "graphs": {}}, p)
    ...     p.read_text()
    '{\\n  "version": "6.0.0",\\n  "graphs": {}\\n}\\n'
    """
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Builds the registry of the current dataset version and writes it to
    ``flpq_data/dataset/registry.json``.

    Returns
    -------
    status : int
        0 on success, 1 when the registry cannot be built.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate flpq_data/dataset/registry.json from the dataset on "
            "object storage (downloads every archive)."
        )
    )
    parser.parse_args(argv)

    try:
        with tempfile.TemporaryDirectory() as workdir:
            registry = build_registry(pathlib.Path(workdir))
    except RuntimeError as error:
        print(f"error: {error}")
        return 1

    path = MAIN_FOLDER / "flpq_data" / "dataset" / "registry.json"
    write_registry(registry, path)
    total_mb = sum(g["size_mb"] for g in registry["graphs"].values())
    print(
        f"Wrote {path.relative_to(MAIN_FOLDER)}: {len(registry['graphs'])} "
        f"graph(s), version {registry['version']}, {total_mb:.1f} MB total."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
