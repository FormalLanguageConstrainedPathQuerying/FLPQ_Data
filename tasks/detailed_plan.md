# Detailed plan: #189 Stream the `graph/` validation in `flpq-check-archive`

- **Task:** [#189](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/189) — `flpq-check-archive` OOMs on large archives because `_validate_root` materializes the whole graph via `graph_from_mtx_dir` purely for its `ValueError` side effect.
- **Branch:** `feature/189-stream-graph-validation` (from `dev`).
- **Closes:** #189 (own task); **Fixes** #188 (the defect it resolves).
- **Context:** the streaming decision (#153, from #138) scoped to format conversion left the archive *validation* path materializing. The fix is centralized in `validate_archive`, so it repairs every archive-lifecycle tool at once (`flpq-check-archive`, `upload_to_s3`, `merge_archive` ×3, `add_reachable_pairs`, `strip_reverse_edges`).

## Locked decisions (confirmed with the user)

| # | Decision | Choice |
|---|---|---|
| 1 | Fix scope | **Minimal + reuse cleanup** — stream the format check (D1) *and* fold the checker's local `_mtx_entries`/`_mtx_header` onto the shared MTX reader so there is one source of truth for MTX parsing (D2) |
| 2 | Shared reader | A new single-file streaming reader `iter_edges_from_mtx_file` in `mtx.py` (the single source of truth for MTX file parsing); `iter_edges_from_mtx_dir` delegates to it |
| 3 | Header reader | Move the checker's `_mtx_header` to `mtx.py` as `mtx_file_header` (the single source of truth for MTX header reading) |
| 4 | Error-message change | Accepted: a `results.mtx` nnz mismatch now reports "cannot be parsed as a Boolean MatrixMarket file" (unified with the other format problems) instead of "declares N entries but has M". No test pins the old wording. |
| 5 | Latent-bug fix | Accepted: a 1-value entry line now raises `ValueError` (caught) instead of `IndexError` (previously uncaught in the range/results checks) — a robustness improvement that falls out of D2 |

## Why the subtasks are shaped this way

- **S1** lands the shared single-file reader + header in `mtx.py` first (self-contained: the directory reader keeps its exact behavior, the new functions are tested). **S2** then rewires the checker onto them and removes the materialization. S2 depends on S1; each is a compilable, testable increment.

---

### S1: Add the shared single-file MTX streaming reader and header to `mtx.py`

**Code:** `flpq_data/graphs/readwrite/mtx.py`
- New `iter_edges_from_mtx_file(path) -> Iterator[Tuple[int, int]]` — streams the `(u, v)` entries of **one** Boolean MatrixMarket file; validates the two-line header, yields one tuple per non-blank entry line, and validates the entry count against the declared nnz on exhaustion. Raises `ValueError` on an unexpected header, a malformed entry line, or an nnz mismatch. This is the single source of truth for MTX file parsing.
- New `mtx_file_header(path) -> Optional[Tuple[int, int, int]]` — returns the `(rows, cols, nnz)` declared by one file, or `None` when the two-line header does not match the dataset format (or the dimension line is not three integers). Reads only the first lines (streams). Moved verbatim from the checker's `_mtx_header`.
- Refactor `iter_edges_from_mtx_dir` to delegate to `iter_edges_from_mtx_file` (it keeps yielding `(u, label, v)` in file order and keeps its exact error behavior).
- Add `iter_edges_from_mtx_file` and `mtx_file_header` to `__all__`.

**Reuse:** generalizes the existing `iter_edges_from_mtx_dir` (no new parser is invented — the per-file loop body moves into `iter_edges_from_mtx_file`); `mtx_file_header` is the checker's `_mtx_header` relocated next to the `_MTX_HEADER` constant it depends on.

**Tests:** `tests/graphs/readwrite/test_mtx.py`
- `test_iter_edges_from_mtx_file` — yields the expected `(u, v)` pairs for a known file.
- `test_iter_edges_from_mtx_file_is_lazy` — `inspect.isgenerator(...)`, first `next()` is correct.
- `test_iter_edges_from_mtx_file_rejects_bad_header` — `ValueError` matching "Unexpected header".
- `test_iter_edges_from_mtx_file_rejects_malformed_entry` — `ValueError` for a non-numeric line **and** for a 1-value line (locks in the IndexError→ValueError fix).
- `test_iter_edges_from_mtx_file_rejects_bad_nnz` — `ValueError` matching "declares N entries but has M".
- `test_mtx_file_header` — returns `(rows, cols, nnz)` for a valid file.
- `test_mtx_file_header_returns_none` — `None` for a wrong header line and for a non-numeric dimension line.

**Docs:** the two new public functions are added to `__all__`, so the git-ignored autosummary page `docs/reference/graphs/generated/flpq_data.graphs.readwrite.mtx.rst` picks them up on a fresh build; write numpydoc docstrings with self-contained doctest `Examples`. Verify with a fresh docs build (no warnings).

**Spec:**
- `iter_edges_from_mtx_file(path)`:
  - Open `path` text; read two lines; if `tuple(line.strip() for _ in range(2)) != _MTX_HEADER` raise `ValueError(f"Unexpected header in {path=}")`.
  - Read the dimension line; `rows, cols, nnz = map(int, line.split())` (a non-numeric / wrong-arity line raises `ValueError`, matching `iter_edges_from_mtx_dir`).
  - For each subsequent line: skip blank lines; `i, j = map(int, line.split())`; `yield i, j`; increment a running count.
  - After the loop (file exhausted): `if count != nnz: raise ValueError(f"{path=} declares {nnz} entries but has {count}")`.
  - Must be a generator (lazy); the nnz check fires on exhaustion, so a consumer that breaks early does not trigger it.
- `mtx_file_header(path)`:
  - `try:` open text; if `readline().rstrip() != _MTX_HEADER[0]` or `!= _MTX_HEADER[1]` return `None`; `rows, cols, nnz = (int(v) for v in readline().split())`; `except (OSError, ValueError): return None`; else `return rows, cols, nnz`.
  - Preserve the current `_mtx_header` semantics exactly (`.rstrip()` on the header lines; exactly-three-integers dimension line).
- `iter_edges_from_mtx_dir(path)`: `for mtx_file in sorted(path.glob("*.mtx")): label = filename_to_label(mtx_file.name); for u, v in iter_edges_from_mtx_file(mtx_file): yield u, label, v`; keep the trailing `logging.info`. Behavior (order, laziness, error classes/messages) is unchanged.

---

### S2: Stream the `graph/` format check and consolidate the checker's MTX helpers

**Code:** `flpq_data/tools/check_archive_structure.py`
- Import: replace `from flpq_data.graphs.readwrite.mtx import _MTX_HEADER, graph_from_mtx_dir` with `from flpq_data.graphs.readwrite.mtx import iter_edges_from_mtx_dir, iter_edges_from_mtx_file, mtx_file_header`.
- Delete the local `_mtx_header` and `_mtx_entries` (now provided by `mtx.py`).
- `_graph_dimensions`: call `mtx_file_header` instead of `_mtx_header`.
- `_mtx_range_problems`: call `mtx_file_header` + `iter_edges_from_mtx_file` instead of `_mtx_header` + `_mtx_entries`; reword the three "a format problem `graph_from_mtx_dir` already reports" comments to "…the streaming format check already reports".
- `_results_problems`: call `mtx_file_header` + `iter_edges_from_mtx_file`; drop the now-dead `count`/`done` bookkeeping and the `count != nnz` branch (an nnz mismatch surfaces as the `ValueError` from `iter_edges_from_mtx_file`, reported as "cannot be parsed as a Boolean MatrixMarket file" — decision 4).
- `_validate_root`: replace `graph_from_mtx_dir(root / "graph")` with a full streaming consumption `for _ in iter_edges_from_mtx_dir(root / "graph"): pass` inside the same `try/except (ValueError, OSError)` and the same `problems.append(f"graph/: {error}")`. The loop must run to completion so the per-file nnz check fires.

**Reuse:** the checker no longer carries its own MTX parser — it reuses `iter_edges_from_mtx_dir` / `iter_edges_from_mtx_file` / `mtx_file_header` from `mtx.py` (single source of truth).

**Tests:** `tests/tools/test_check_archive_structure.py`
- New `test_validate_streams_the_graph_dir` — monkeypatch `flpq_data.tools.check_archive_structure.iter_edges_from_mtx_dir` with a spy wrapping the real one; assert `validate_archive(_valid_tree(...)) == []` **and** the spy was called with the `graph/` directory (regression: the format check streams rather than materializing).
- All existing tests must pass unchanged (behavior is preserved: format problems still reported as `graph/: …`, range/dimension/results messages unchanged except decision 4).

**Docs:** no change to the documented behavior — `docs/reference/tools/index.rst` ("Archive structure checker") describes the checks at a level that stays accurate ("Every MTX file parses as a Boolean pattern matrix, every edge endpoint fits the declared dimensions, and all label matrices declare the same dimensions"). The module docstring of `check_archive_structure.py` does not describe the mechanism. No doc edit required; verified against the documentation mapping.

**Spec:**
- The format check in `_validate_root` must raise-and-report exactly the same three error classes as before (unexpected header, malformed entry line, nnz mismatch) with the same `graph/: {error}` prefix, now sourced from `iter_edges_from_mtx_dir` (O(1) in edges) instead of `graph_from_mtx_dir` (O(V+E)).
- `_mtx_range_problems` and `_results_problems` keep their skip-on-format-problem semantics (a file whose header is `None`, or whose entry stream raises `ValueError`, is skipped for the range check because the format check already reported it).
- Net effect: `validate_archive` never builds a `networkx.MultiDiGraph`; peak memory for the `graph/` checks is O(1) in the number of edges.

---

## Status

- [x] S1: shared single-file MTX reader + header in `mtx.py`
- [ ] S2: stream the `graph/` format check + consolidate the checker's helpers
