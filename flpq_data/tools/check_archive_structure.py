"""Validate the structure of a graph archive.

Every graph archive must have the same fixed, self-contained structure
(documented in ``docs/file_structure.rst``):
a description document answering the mandatory questions, one Boolean
MatrixMarket file per stored edge label, and all queries of the graph as
directories grouped by class — each query directory holding every
representation of the query plus one ``results.mtx`` with the constrained
reachability facts — described in a common document.

A partial archive provides new queries for an existing graph: it contains
only ``queries/`` (the new query directories plus a ``README.md`` fragment
with their sections) and is validated with ``--partial``.

The command-line entry point is installed with the package::

    flpq-check-archive ARCHIVE.tar.gz
    flpq-check-archive UNPACKED_DIR
    flpq-check-archive PARTIAL.tar.gz --partial
"""

import argparse
import pathlib
import re
import shutil
import tarfile
import tempfile
from typing import Optional, Sequence, Set, Union

from pyformlang.rsa import RecursiveAutomaton as RSA

from flpq_data.graphs.readwrite.mtx import _MTX_HEADER, graph_from_mtx_dir
from flpq_data.queries.cfpq.converters.cfg import cfg_from_rsa
from flpq_data.queries.cfpq.readwrite.cnf_template import cnf_template_from_text
from flpq_data.queries.mcfpq.readwrite.mcfg import mcfg_from_text
from flpq_data.queries.rpq.readwrite.regex import regex_from_text
from flpq_data.queries.rpq.readwrite.rsa import rsa_from_text

__all__ = [
    "MANDATORY_README_SECTIONS",
    "QUERY_CLASSES",
    "stored_reverse_forward",
    "parse_readme_sections",
    "unpack_single_dir",
    "validate_archive",
    "main",
]

#: The questions the archive ``README.md`` must answer (one ``##`` section each).
MANDATORY_README_SECTIONS = (
    "What is this graph?",
    "Source",
    "Construction",
    "Nodes",
    "Edges and labels",
    "Query classes",
    "License",
    "Caveats",
)

#: Query class -> file extensions of the representation files in a query directory.
QUERY_CLASSES = {"cfpq": (".cnf", ".rsm"), "rpq": (".re", ".rsm"), "mcfpq": (".mcfg",)}

_VARIABLE = re.compile(r"[a-z][0-9]+")


def _query_terminals(path: pathlib.Path) -> set[str]:
    """Return the terminals used by one query representation file.

    Parameters
    ----------
    path : Path
        The representation file to read (its extension selects the format).

    Returns
    -------
    terminals : set[str]
        The edge labels the query uses.

    Raises
    ------
    Exception
        If the file cannot be parsed as a query of its class.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".cnf":
        cfg = cnf_template_from_text(text)
        return {symbol.value for symbol in cfg.terminals}
    if path.suffix == ".rsm":
        rsa = rsa_from_text(text)
        cfg = cfg_from_rsa(rsa)
        return {symbol.value for symbol in cfg.terminals}
    if path.suffix == ".re":
        regex = regex_from_text(text)
        nfa = regex.to_epsilon_nfa()
        if nfa is None:
            return set()
        return {symbol.value for symbol in nfa.symbols}
    mcfg = mcfg_from_text(text)
    terminals = set()
    for rule in mcfg.rules:
        for arg in rule.head_args:
            for item in arg:
                if item != "eps" and not _VARIABLE.fullmatch(item):
                    terminals.add(item)
    return terminals


def _skeleton_problems(root: pathlib.Path) -> list[str]:
    """Check the fixed archive skeleton under ``root``."""
    problems = []
    entries = {path.name for path in root.iterdir()}
    expected = {"README.md", "graph", "queries"}
    for name in sorted(entries - expected):
        problems.append(f"unexpected entry {name!r} (expected only {sorted(expected)})")
    for name in sorted(expected - entries):
        problems.append(f"missing entry {name!r}")
    if problems:
        return problems

    graph_dir = root / "graph"
    if not any(
        path.suffix == ".mtx" and path.is_file() for path in graph_dir.iterdir()
    ):
        problems.append("graph/ must contain at least one .mtx file")
    for path in sorted(graph_dir.iterdir()):
        if not path.is_file() or path.suffix != ".mtx":
            problems.append(f"graph/{path.name}: only .mtx files are allowed in graph/")

    queries_dir = root / "queries"
    query_entries = {path.name for path in queries_dir.iterdir()}
    allowed = {"README.md", *QUERY_CLASSES}
    for name in sorted(query_entries - allowed):
        problems.append(
            f"queries/{name}: unexpected entry (expected only README.md and "
            f"class directories {sorted(QUERY_CLASSES)})"
        )
    if "README.md" not in query_entries:
        problems.append("queries/README.md: missing")
    present_classes = query_entries & set(QUERY_CLASSES)
    if not present_classes:
        problems.append(
            f"queries/: at least one class directory is required "
            f"({sorted(QUERY_CLASSES)})"
        )
    for cls, exts in QUERY_CLASSES.items():
        cls_dir = queries_dir / cls
        if not cls_dir.is_dir():
            continue
        for path in sorted(cls_dir.iterdir()):
            if not path.is_dir():
                problems.append(
                    f"queries/{cls}/{path.name}: must be a query directory "
                    "(flat query files are no longer allowed)"
                )
                continue
            problems.extend(_query_dir_problems(path, cls, exts))
    return problems


def _partial_skeleton_problems(root: pathlib.Path) -> list[str]:
    """Check the skeleton of a partial archive under ``root``."""
    problems = []
    entries = {path.name for path in root.iterdir()}
    for name in sorted(entries - {"queries"}):
        problems.append(
            f"unexpected entry {name!r} (a partial archive contains only queries/)"
        )
    if "queries" not in entries:
        problems.append("missing entry 'queries'")
    if problems:
        return problems

    queries_dir = root / "queries"
    query_entries = {path.name for path in queries_dir.iterdir()}
    for name in sorted(query_entries - {"README.md", *QUERY_CLASSES}):
        problems.append(
            f"queries/{name}: unexpected entry (expected only README.md and "
            f"the class directories {sorted(QUERY_CLASSES)})"
        )
    if "README.md" not in query_entries:
        problems.append("queries/README.md: missing")
    for cls in sorted(query_entries & set(QUERY_CLASSES)):
        cls_dir = queries_dir / cls
        if not any(path.is_dir() for path in cls_dir.iterdir()):
            problems.append(
                f"queries/{cls}/: a partial archive must add at least one query"
            )
        for path in sorted(cls_dir.iterdir()):
            if not path.is_dir():
                problems.append(
                    f"queries/{cls}/{path.name}: must be a query directory "
                    "(flat query files are no longer allowed)"
                )
                continue
            problems.extend(_query_dir_problems(path, cls, QUERY_CLASSES[cls]))
    if not (query_entries & set(QUERY_CLASSES)):
        problems.append(
            f"queries/: at least one class directory is required "
            f"({sorted(QUERY_CLASSES)})"
        )
    return problems


def _query_dir_problems(
    query_dir: pathlib.Path, cls: str, exts: tuple[str, ...]
) -> list[str]:
    """Check one ``queries/<class>/<query>/`` directory."""
    problems = []
    rel = f"queries/{cls}/{query_dir.name}"
    has_representation = False
    for path in sorted(query_dir.iterdir()):
        if not path.is_file():
            problems.append(f"{rel}/{path.name}: only files are allowed")
            continue
        if path.name == "results.mtx":
            continue
        if path.suffix not in exts:
            problems.append(
                f"{rel}/{path.name}: only {' '.join(exts)} representation files "
                "and results.mtx are allowed"
            )
            continue
        has_representation = True
    if not has_representation:
        problems.append(f"{rel}/: no {cls} representation file ({' or '.join(exts)})")
    if not (query_dir / "results.mtx").is_file():
        problems.append(f"{rel}/: missing results.mtx")
    return problems


def _mtx_header(path: pathlib.Path) -> Optional[tuple[int, int, int]]:
    """The (rows, cols, nnz) declared by one Boolean MatrixMarket file.

    Returns None when the file does not follow the dataset format (the
    two-line header and a dimension line). Streams — only the first lines
    are read.
    """
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


def _mtx_entries(path: pathlib.Path):
    """Yields the (tail, head) entry pairs of one Boolean MatrixMarket file,
    streaming line by line (O(1) memory).

    Raises ValueError on a malformed entry line.
    """
    with open(path, "r", encoding="utf-8") as f:
        for _ in range(3):  # the two header lines and the dimension line
            f.readline()
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            yield int(parts[0]), int(parts[1])


def _graph_dimensions(graph_dir: pathlib.Path) -> set[tuple[int, int]]:
    """The declared dimensions of every parseable graph label matrix."""
    dimensions = set()
    for mtx_file in sorted(graph_dir.glob("*.mtx")):
        header = _mtx_header(mtx_file)
        if header is not None:
            dimensions.add((header[0], header[1]))
    return dimensions


def _mtx_range_problems(graph_dir: pathlib.Path) -> list[str]:
    """Check that edge endpoints fit the declared matrix dimensions."""
    problems = []
    for mtx_file in sorted(graph_dir.glob("*.mtx")):
        header = _mtx_header(mtx_file)
        if header is None:
            continue  # a format problem graph_from_mtx_dir already reports
        rows, cols, nnz = header
        count = 0
        try:
            for tail, head in _mtx_entries(mtx_file):
                count += 1
                if not 0 <= tail < rows or not 0 <= head < cols:
                    problems.append(
                        f"graph/{mtx_file.name}: edge ({tail}, {head}) is outside "
                        f"the declared {rows}x{cols} matrix"
                    )
                    break
        except ValueError:
            continue  # a format problem graph_from_mtx_dir already reports
        if count != nnz:
            continue  # a format problem graph_from_mtx_dir already reports
    dimensions = _graph_dimensions(graph_dir)
    if len(dimensions) > 1:
        problems.append(
            "graph/: all label matrices must declare the same dimensions "
            f"(found {sorted(dimensions)})"
        )
    return problems


# --------------------------------------------------------------------------- #
# Naming consistency rules
# --------------------------------------------------------------------------- #

_FORBIDDEN_COMPONENTS = ("bar", "rev")
_INDEXED_REV_RE = re.compile(r"^(.*)_r_(\d+)$")


def stored_reverse_forward(stem: str, stems: Set[str]) -> Optional[str]:
    """Return the forward label of a stored reversed matrix ``stem``, if any.

    A matrix stem is a stored reverse when its forward label is also stored:
    the unindexed form ``L_r`` (forward ``L``) or the indexed form
    ``<base>_r_<n>`` (forward ``<base>_<n>``). Reversed edges must not be
    stored — they are auto-generated (see
    :func:`flpq_data.graphs.utils.add_reverse_edges`).

    Parameters
    ----------
    stem : str
        The file stem (name without the ``.mtx`` suffix).
    stems : Set[str]
        The stems of all label matrices stored in the ``graph/`` directory.

    Examples
    --------
    >>> stored_reverse_forward("a_r", {"a", "a_r"})
    'a'
    >>> stored_reverse_forward("load_r_0", {"load_0", "load_r_0"})
    'load_0'
    >>> stored_reverse_forward("load_r_0", {"load_r_0"}) is None
    True

    Returns
    -------
    forward : str or None
        The forward label ``stem`` reverses, or None when ``stem`` is not a
        stored reverse.
    """
    if stem.endswith("_r"):
        forward: Optional[str] = stem[:-2]
    else:
        indexed = _INDEXED_REV_RE.fullmatch(stem)
        forward = f"{indexed.group(1)}_{indexed.group(2)}" if indexed else None
    return forward if forward is not None and forward in stems else None


def _label_problems(graph_dir: pathlib.Path) -> list[str]:
    """Check edge-label naming conventions in ``graph/``."""
    problems = []
    stems = {path.stem for path in graph_dir.glob("*.mtx")}

    for stem in sorted(stems):
        # No forbidden components (bar, rev)
        parts = stem.replace("_", " ").split()
        for part in parts:
            if part in _FORBIDDEN_COMPONENTS:
                problems.append(
                    f"graph/{stem}.mtx: label contains forbidden component "
                    f"{part!r} (use '_r' for reversed edges)"
                )
                break

    # No stored reverses — if the forward label is stored, neither its
    # unindexed reverse (L_r) nor its indexed reverse (B_r_<n>) may be stored.
    for stem in sorted(stems):
        forward = stored_reverse_forward(stem, stems)
        if forward is not None:
            problems.append(
                f"graph/{stem}.mtx: reversed edge is stored but must be "
                f"auto-generated from {forward}.mtx"
            )
    return problems


def _same_dir_consistency_problems(queries_dir: pathlib.Path) -> list[str]:
    """Check that all representations in one query directory use the same
    terminal set (they must define the same language)."""
    problems = []
    if not queries_dir.is_dir():
        return problems
    for cls_dir in sorted(queries_dir.iterdir()):
        if not cls_dir.is_dir() or cls_dir.name not in QUERY_CLASSES:
            continue
        for query_dir in sorted(cls_dir.iterdir()):
            if not query_dir.is_dir():
                continue
            term_sets: dict[str, frozenset[str]] = {}
            for path in sorted(query_dir.iterdir()):
                if path.suffix not in (".cnf", ".rsm", ".re", ".mcfg"):
                    continue
                try:
                    terminals = _query_terminals(path)
                except Exception:
                    continue
                term_sets[path.name] = frozenset(terminals)
            # Compare all pairs
            names = list(term_sets)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    if term_sets[names[i]] != term_sets[names[j]]:
                        only_i = term_sets[names[i]] - term_sets[names[j]]
                        only_j = term_sets[names[j]] - term_sets[names[i]]
                        detail = ""
                        if only_i:
                            detail += f" {names[i]} has extra {sorted(only_i)}"
                        if only_j:
                            detail += f" {names[j]} has extra {sorted(only_j)}"
                        problems.append(
                            f"queries/{cls_dir.name}/{query_dir.name}/: "
                            f"{names[i]} and {names[j]} use different terminal "
                            f"sets (must represent the same language){detail}"
                        )
    return problems


def _naming_problems(root: pathlib.Path) -> list[str]:
    """Run all naming-consistency checks on the unpacked archive."""
    problems = []
    graph_dir = root / "graph"
    queries_dir = root / "queries"
    if graph_dir.is_dir():
        problems.extend(_label_problems(graph_dir))
    if queries_dir.is_dir():
        problems.extend(_same_dir_consistency_problems(queries_dir))
    return problems


def _results_problems(root: pathlib.Path) -> list[str]:
    """Check every per-query results.mtx against the graph."""
    problems = []
    dimensions = _graph_dimensions(root / "graph")
    if len(dimensions) != 1:
        return problems  # the matrix shape is undefined; already reported
    expected = next(iter(dimensions))

    queries_dir = root / "queries"
    for cls in QUERY_CLASSES:
        cls_dir = queries_dir / cls
        if not cls_dir.is_dir():
            continue
        for query_dir in sorted(cls_dir.iterdir()):
            if not query_dir.is_dir():
                continue
            results = query_dir / "results.mtx"
            rel = f"queries/{cls}/{query_dir.name}/results.mtx"
            header = _mtx_header(results)
            if header is None:
                problems.append(
                    f"{rel}: cannot be parsed as a Boolean MatrixMarket file"
                )
                continue
            rows, cols, nnz = header
            if (rows, cols) != expected:
                problems.append(
                    f"{rel}: must be a {expected[0]}x{expected[1]} matrix "
                    f"(the graph declares {expected[0]}x{expected[1]})"
                )
                continue
            count = 0
            done = False
            try:
                for tail, head in _mtx_entries(results):
                    count += 1
                    if not 0 <= tail < rows or not 0 <= head < cols:
                        problems.append(
                            f"{rel}: entry ({tail}, {head}) is outside the "
                            f"declared {rows}x{cols} matrix"
                        )
                        done = True
                        break
            except ValueError:
                problems.append(
                    f"{rel}: cannot be parsed as a Boolean MatrixMarket file"
                )
                done = True
            if not done and count != nnz:
                problems.append(f"{rel}: declares {nnz} entries but has {count}")
    return problems


def _readme_problems(root: pathlib.Path) -> list[str]:
    """Check that README.md answers all the mandatory questions."""
    text = (root / "README.md").read_text(encoding="utf-8")
    headers = {line[3:].strip() for line in text.splitlines() if line.startswith("## ")}
    return [
        f"README.md: missing mandatory section '## {question}'"
        for question in MANDATORY_README_SECTIONS
        if question not in headers
    ]


def parse_readme_sections(text: str) -> dict[str, list[str]]:
    """Parse the ``## <name>`` sections of a queries README into an ordered
    mapping section name -> body lines."""
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def _rsm_recurses(rsa: RSA) -> bool:
    """Whether any box transition is labelled by a nonterminal (box name)."""
    names = {label.value for label in rsa.labels}
    for label in rsa.labels:
        box = rsa.get_box(label)
        if box is not None and any(symbol.value in names for symbol in box.dfa.symbols):
            return True
    return False


def _query_problems(root: pathlib.Path) -> list[str]:
    """Check that queries parse, use at least one terminal, and are all
    described. A terminal matching no stored label is legal: it stays inert
    on materialization (see :func:`flpq_data.materialize`) and the query
    yields an empty result — the RDF category ships such non-applicable
    variants."""
    problems = []
    queries_dir = root / "queries"

    existing: dict[str, tuple[str, list[pathlib.Path]]] = {}
    for cls, exts in QUERY_CLASSES.items():
        cls_dir = queries_dir / cls
        if not cls_dir.is_dir():
            continue
        for query_dir in sorted(cls_dir.iterdir()):
            if not query_dir.is_dir():
                continue  # reported by the skeleton check
            representations = [
                path
                for path in sorted(query_dir.iterdir())
                if path.is_file() and path.suffix in exts
            ]
            existing[f"{cls}/{query_dir.name}"] = (cls, representations)

    for rel, (cls, representations) in sorted(existing.items()):
        for path in representations:
            where = f"queries/{rel}/{path.name}"
            try:
                terminals = _query_terminals(path)
            except Exception as error:
                problems.append(f"{where}: cannot be parsed as a {cls} query ({error})")
                continue
            if not terminals:
                problems.append(
                    f"{where}: uses no terminal (an empty query is meaningless)"
                )
            if cls == "rpq" and path.suffix == ".rsm":
                try:
                    rsa = rsa_from_text(path.read_text(encoding="utf-8"))
                except Exception:
                    continue  # already reported above
                if _rsm_recurses(rsa):
                    problems.append(
                        f"{where}: an rpq query must be regular (no box "
                        "transition may be labelled by a nonterminal)"
                    )

    doc = (queries_dir / "README.md").read_text(encoding="utf-8")
    sections = parse_readme_sections(doc)

    for name in sorted(set(sections) - set(existing)):
        problems.append(
            f"queries/README.md: section {name!r} does not match any query directory"
        )
    for name in sorted(set(existing) - set(sections)):
        problems.append(f"queries/README.md: no section describing {name!r}")
    for name, body in sections.items():
        if name in existing and not any(line.strip() for line in body):
            problems.append(f"queries/README.md: the section for {name!r} is empty")
    return problems


def _validate_root(root: pathlib.Path, partial: bool = False) -> list[str]:
    """Validate the unpacked archive directory ``root``."""
    if partial:
        problems = _partial_skeleton_problems(root)
        if problems:
            return problems  # the deeper checks are meaningless without the skeleton
        problems.extend(_query_problems(root))
        return problems
    problems = _skeleton_problems(root)
    if problems:
        return problems  # the deeper checks are meaningless without the skeleton
    try:
        graph_from_mtx_dir(root / "graph")
    except (ValueError, OSError) as error:
        problems.append(f"graph/: {error}")
    problems.extend(_mtx_range_problems(root / "graph"))
    problems.extend(_results_problems(root))
    problems.extend(_readme_problems(root))
    problems.extend(_query_problems(root))
    problems.extend(_naming_problems(root))
    return problems


def unpack_single_dir(path: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    """Unpack ``path`` (a ``.tar.gz``) into ``dest`` and return its single
    top-level directory.

    Raises
    ------
    ValueError
        If the archive does not contain a single top-level directory.
    """
    shutil.unpack_archive(path, dest)
    entries = list(dest.iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        raise ValueError(f"{path.name}: must contain a single top-level directory")
    return entries[0]


def validate_archive(
    path: Union[str, pathlib.Path], *, partial: bool = False
) -> list[str]:
    """Validate one graph archive (a ``.tar.gz`` or an unpacked directory).

    Parameters
    ----------
    path : Union[str, Path]
        The archive to validate.
    partial : bool
        Validate a partial archive (new queries for an existing graph:
        ``queries/`` only) instead of a full graph archive.

    Returns
    -------
    problems : list[str]
        All structure violations found; an empty list means the archive is
        valid.
    """
    path = pathlib.Path(path)
    if path.is_dir():
        return _validate_root(path, partial=partial)
    try:
        is_tar = tarfile.is_tarfile(path)
    except OSError:
        is_tar = False
    if path.suffix != ".gz" or not is_tar:
        return [f"{path.name}: not a .tar.gz archive or an unpacked directory"]

    with tempfile.TemporaryDirectory() as tmp:
        try:
            root = unpack_single_dir(path, pathlib.Path(tmp))
        except ValueError as error:
            return [str(error)]
        problems = []
        expected_name = path.name[: -len(".tar.gz")]
        if root.name != expected_name:
            problems.append(
                f"top-level directory {root.name!r} must be named after the "
                f"archive ({expected_name!r})"
            )
        problems.extend(_validate_root(root, partial=partial))
        return problems


def _audit(client, bucket: str, prefix: str) -> list[str]:
    """Validate every ``.tar.gz`` object stored under the bucket prefix."""
    problems = []
    key_prefix = f"{prefix.rstrip('/')}/" if prefix else ""
    objects = []
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=key_prefix
    ):
        objects.extend(
            obj["Key"]
            for obj in page.get("Contents", [])
            if obj["Key"].endswith(".tar.gz")
        )
    if not objects:
        problems.append(f"no .tar.gz objects found under s3://{bucket}/{key_prefix}")
        return problems

    with tempfile.TemporaryDirectory() as tmp:
        for object_key in sorted(objects):
            # A per-key sandbox keeps the original file name, which the
            # top-level-directory check depends on.
            sandbox = pathlib.Path(tmp) / object_key.replace("/", "__")
            sandbox.mkdir()
            local = sandbox / pathlib.Path(object_key).name
            client.download_file(bucket, object_key, str(local))
            problems.extend(
                f"{object_key}: {problem}" for problem in validate_archive(local)
            )
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Validates one local graph archive, or — with ``--audit`` — every
    ``.tar.gz`` object under a bucket prefix, and prints every structure
    violation found.

    Returns
    -------
    status : int
        0 when everything is valid, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Validate the fixed self-contained structure of a graph archive."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="path to a .tar.gz archive or an unpacked archive directory",
    )
    parser.add_argument(
        "--partial",
        action="store_true",
        help=(
            "validate a partial archive (queries/ only — new queries for an "
            "existing graph) instead of a full graph archive"
        ),
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help=(
            "validate every .tar.gz object under --prefix in the bucket "
            "instead of a local path"
        ),
    )
    parser.add_argument(
        "--prefix", default="", help="bucket prefix to audit (with --audit)"
    )
    parser.add_argument(
        "--access-key-id", default=None, help="Yandex Cloud IAM key ID (with --audit)"
    )
    parser.add_argument(
        "--secret-access-key",
        default=None,
        help="Yandex Cloud IAM secret key (with --audit)",
    )
    parser.add_argument(
        "--endpoint-url",
        default=None,
        help="S3 API endpoint (with --audit; default: the upload tool's)",
    )
    parser.add_argument(
        "--bucket",
        default=None,
        help="target bucket (with --audit; default: the upload tool's)",
    )
    args = parser.parse_args(argv)

    if args.audit:
        from flpq_data.dataset.s3 import (
            DEFAULT_BUCKET,
            DEFAULT_ENDPOINT_URL,
            create_s3_client,
        )

        if not args.access_key_id or not args.secret_access_key:
            print(
                "error: --access-key-id and --secret-access-key are "
                "required for --audit"
            )
            return 1
        try:
            client = create_s3_client(
                args.access_key_id,
                args.secret_access_key,
                args.endpoint_url or DEFAULT_ENDPOINT_URL,
            )
        except ImportError:
            print("error: --audit requires boto3 (pip install boto3)")
            return 1
        problems = _audit(client, args.bucket or DEFAULT_BUCKET, args.prefix)
    elif args.path is None:
        print("error: give a path to validate or use --audit")
        return 1
    else:
        problems = validate_archive(args.path, partial=args.partial)

    if problems:
        for problem in problems:
            print(f"error: {problem}")
        print(f"{len(problems)} structure violation(s) found")
        return 1
    kind = "partial archive" if args.partial else "archive"
    print(f"{kind} structure ok")
    return 0
