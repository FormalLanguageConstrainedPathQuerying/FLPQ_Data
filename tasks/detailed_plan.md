# Detailed plan: #192 Plan comment mirror: sync tool + completion gate

- **Task:** [#192](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/192) — the plan comment on a task issue is a pure mirror of `tasks/detailed_plan.md`, but during #187 it was never re-synced (the comment stayed frozen at its first posting: S0–S4 unchecked, S5/S6 missing) and no gate caught the drift.
- **Branch:** `feature/192-plan-mirror-sync` (from `dev`).
- **Context:** #187 (the lapse), #185 (the mirror *was* synced there — the mechanism works; it was skipped, not broken).

## Locked decisions (confirmed with the user)

| # | Decision | Choice |
|---|---|---|
| 1 | Fix scope | Both parts: the completion-gate checkbox (option 2) **and** the sync script (option 3) |
| 2 | Immediate fix | The stale #187 comment was already synced before this branch (operational action, no commit) |
| 3 | GitHub API transport | Shell out to `gh api` — no new dependency, same auth and semantics as the proven skill snippet |
| 4 | Issue number | Explicit CLI argument (no fragile parsing of the plan file) |

Out of scope (flagged, not fixed): step 7's parenthetical "(`[done]` suffix + commit hash on the subtask heading)" describes a marking format no recent plan file uses (practice is the `## Status` checkbox section); fixing the wording is a separate consistency task.

## Why the subtasks are shaped this way

- S1 lands the tool first so S2's skill text can reference a working command; the skill change is docs-only and rides on the tool.
- The script funnels every `gh` call through one module-level `run_gh` boundary so tests monkeypatch it — the `tests/utils/` convention (patch module attributes, cf. `test_upload_to_s3.py` patching `boto3.client`).
- Body construction must match the skill snippet byte-for-byte (`echo '<!-- detailed-plan -->'; cat tasks/detailed_plan.md`), so a comment synced by the snippet and one synced by the tool are indistinguishable.

## Subtasks

### S1: `utils/sync_plan_comment.py` — mirror the plan file onto the issue comment

**Code:** new `utils/sync_plan_comment.py`:
- `PLAN_MARKER = "<!-- detailed-plan -->"`; `PLAN_FILE = MAIN_FOLDER / "tasks" / "detailed_plan.md"` (reuses `MAIN_FOLDER` from `utils/config.py`);
- `build_body(plan_text: str) -> str` — `PLAN_MARKER + "\n" + plan_text`;
- `run_gh(args: Sequence[str], *, input: str | None = None) -> str` — the single `subprocess.run(["gh", *args], ...)` boundary; raises `RuntimeError` with gh's stderr on non-zero exit;
- `find_plan_comment(repo: str, issue: int) -> int` — `gh api repos/<repo>/issues/<N>/comments` with the `--jq` filter `[.[] | select(.body | startswith("<!-- detailed-plan -->"))] | last.id`; raises when the result is `null`;
- `sync(repo: str, issue: int) -> int` — reads `PLAN_FILE`, finds the comment, PATCHes its body via `gh api -X PATCH repos/<repo>/issues/comments/<cid> --input -` with `json.dumps({"body": body})` on stdin; returns the comment id;
- `check(repo: str, issue: int) -> bool` — fetches the stored body (`gh api repos/<repo>/issues/comments/<cid> --jq .body`) and compares it against `build_body(PLAN_FILE)` ignoring trailing newlines (the GitHub API stores comment bodies with one extra trailing newline — see Design Notes);
- `main(argv: Sequence[str] | None = None) -> int` — argparse positional `issue` (int) + `--check` flag (verify instead of sync; exit 1 on drift); resolves the repo via `gh repo view --json nameWithOwner -q .nameWithOwner`; prints a one-line report; catches `RuntimeError`/`OSError` → message on stderr, exit 1.

**Tests:** new `tests/utils/test_sync_plan_comment.py` (monkeypatches `sync_plan_comment.run_gh`):
- `test_build_body_precedes_marker` — marker line + original content, byte-exact;
- `test_find_plan_comment_takes_last_marker_match` — several comments, marker on two; the last wins;
- `test_find_plan_comment_raises_when_absent` — `null` result → `RuntimeError`;
- `test_sync_patches_the_comment_body` — captured PATCH call: correct URL, JSON `{"body": marker + "\n" + content}` on stdin;
- `test_main_end_to_end` — repo resolution, sync, report line (capsys);
- `test_main_missing_plan_file` — clear error, exit 1;
- `test_check_returns_true_when_in_sync` / `test_check_returns_false_on_drift` — the stored-body fixture models the API's extra trailing newline;
- `test_main_check_mode_reports_sync_and_drift` — `--check` exits 0/1, never PATCHes.

**Docs:** `docs/utils.rst` — new section appended after the migration-tool section: `.. _sync_plan_comment:` label, title "Sync the plan comment", usage block `python utils/sync_plan_comment.py ISSUE [--check]`, bullets: the local file is the single source of truth and the comment a pure mirror; `--check` verifies (exit 0/1) and ignores trailing newlines because the API stores bodies with one extra; marker discovery (last comment whose first line is the marker); idempotent (re-running PATCHes the same body); transport is `gh api` (requires an authenticated `gh`).

**Spec:**
- `run_gh` uses `subprocess.run(["gh", *args], capture_output=True, text=True, input=input)`; on `returncode != 0` raise `RuntimeError(f"gh {' '.join(args)} failed: {stderr.strip()}")`.
- `find_plan_comment` strips the `--jq` output; `"null"` (or empty) → `RuntimeError(f"no '<!-- detailed-plan -->' comment on issue {issue}")`.
- `main` report line: `f"synced issue {issue} plan comment {cid}"`.
- Commit: `feat(192-S1): add utils/sync_plan_comment.py to mirror the detailed plan onto the task issue` — includes this plan file (replacing the #187 plan) with S1 marked done.

### S2: Point the subtask-loop skill at the tool and gate the mirror at completion

**Code:** none (skill only).
**Tests:** none (skill only); the pre-commit hooks still run on the skill file.
**Docs:** `.opencode/skills/subtask-loop/SKILL.md`:
- Step 7 "Mark Completed": replace the inline 6-line bash snippet with the one-command invocation `uv run python utils/sync_plan_comment.py <N>`; keep the closing sentence "The local file is the single source of truth; the comment is a pure mirror."
- "Task Completion Verification": add a checkbox — the plan comment on the task issue is in sync with `tasks/detailed_plan.md` (pure mirror — diff the comment body against the file; `utils/sync_plan_comment.py` performs the sync).
- Commit: `docs(192-S2): sync the plan comment via the tool and gate it at task completion` with `Closes #192` as a standalone line.

## Design Notes (discovered during implementation)

### The GitHub API appends a trailing newline to comment bodies

Discovered while dogfooding the tool against #192: PATCHing a comment with
body `X` stores `X\n`; PATCHing `X\n` stores `X\n\n` (verified with
controlled bodies). The stored body is therefore always `sent + "\n"`, so:

- The byte-exact invariant applies to the *sent* body: the tool sends
  exactly `marker + "\n" + file content`, identical to what the retired
  skill snippet sent — comments synced by either means remain
  indistinguishable.
- `--check` compares with `rstrip("\n")` on both sides — robust to the
  API's newline behavior and to the file's own trailing-newline state,
  while still catching any content drift.

## Status

- S1: [x]
- S2: [ ]
