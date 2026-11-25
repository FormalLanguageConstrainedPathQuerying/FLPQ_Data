"""Mirror the detailed plan onto the plan comment of a task issue.

The detailed plan lives in ``tasks/detailed_plan.md`` — the single source
of truth. The task issue carries a mirror: a comment whose first line is
the ``<!-- detailed-plan -->`` marker. This tool keeps the mirror current:
it finds the marker comment (the last one, if several exist) and replaces
its body with the marker plus the current file content.

Requires an authenticated ``gh``.

Usage (from any directory)::

    python utils/sync_plan_comment.py ISSUE [--check]

Without ``--check`` the mirror is (re)written; with it, the tool only
verifies that the comment is in sync and exits 1 on drift.
"""

import argparse
import json
import subprocess
import sys
from typing import Optional, Sequence

from config import MAIN_FOLDER

__all__ = [
    "PLAN_MARKER",
    "PLAN_FILE",
    "build_body",
    "run_gh",
    "find_plan_comment",
    "sync",
    "check",
    "main",
]

#: The first line of the plan comment on a task issue.
PLAN_MARKER = "<!-- detailed-plan -->"

#: The detailed plan — the single source of truth the comment mirrors.
PLAN_FILE = MAIN_FOLDER / "tasks" / "detailed_plan.md"


def build_body(plan_text: str) -> str:
    """Returns the plan comment body: the marker line plus the plan content.

    Parameters
    ----------
    plan_text : str
        The full content of ``tasks/detailed_plan.md``.

    Returns
    -------
    str
        ``PLAN_MARKER`` + a newline + *plan_text*, byte-identical to what
        ``echo '<!-- detailed-plan -->'; cat tasks/detailed_plan.md``
        produces.
    """
    return PLAN_MARKER + "\n" + plan_text


def run_gh(args: Sequence[str], *, input: Optional[str] = None) -> str:
    """Runs ``gh`` with *args* and returns its stdout.

    Parameters
    ----------
    args : Sequence[str]
        The ``gh`` arguments, without the program name.
    input : str, optional
        Data written to the command's stdin.

    Returns
    -------
    str
        The command's stdout.

    Raises
    ------
    RuntimeError
        If the command exits non-zero.
    """
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, input=input)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def find_plan_comment(repo: str, issue: int) -> int:
    """Returns the id of the plan comment on *issue*.

    The comment is identified by its first line being ``PLAN_MARKER``; when
    several comments match, the last one wins.

    Parameters
    ----------
    repo : str
        The repository as ``owner/name``.
    issue : int
        The task issue number.

    Returns
    -------
    int
        The id of the marker comment.

    Raises
    ------
    RuntimeError
        If no marker comment exists on the issue.
    """
    out = run_gh(
        [
            "api",
            f"repos/{repo}/issues/{issue}/comments",
            "--jq",
            f'[.[] | select(.body | startswith("{PLAN_MARKER}"))] | last.id',
        ]
    ).strip()
    if out in ("", "null"):
        raise RuntimeError(f"no {PLAN_MARKER!r} comment on issue {issue}")
    return int(out)


def sync(repo: str, issue: int) -> int:
    """Mirrors ``PLAN_FILE`` onto the plan comment of *issue*.

    Parameters
    ----------
    repo : str
        The repository as ``owner/name``.
    issue : int
        The task issue number.

    Returns
    -------
    int
        The id of the patched comment.
    """
    cid = find_plan_comment(repo, issue)
    body = build_body(PLAN_FILE.read_text(encoding="utf-8"))
    run_gh(
        [
            "api",
            "-X",
            "PATCH",
            f"repos/{repo}/issues/comments/{cid}",
            "--input",
            "-",
        ],
        input=json.dumps({"body": body}),
    )
    return cid


def check(repo: str, issue: int) -> bool:
    """Returns whether the plan comment of *issue* mirrors ``PLAN_FILE``.

    The GitHub API stores comment bodies with one extra trailing newline,
    so the comparison ignores trailing newlines on both sides.

    Parameters
    ----------
    repo : str
        The repository as ``owner/name``.
    issue : int
        The task issue number.

    Returns
    -------
    bool
        True when the stored comment body equals the marker plus the
        current plan file content, up to trailing newlines.
    """
    cid = find_plan_comment(repo, issue)
    stored = run_gh(["api", f"repos/{repo}/issues/comments/{cid}", "--jq", ".body"])
    expected = build_body(PLAN_FILE.read_text(encoding="utf-8"))
    return stored.rstrip("\n") == expected.rstrip("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Returns
    -------
    status : int
        0 when the mirror was synced (or verified in sync with ``--check``),
        1 on any failure or drift.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Mirror tasks/detailed_plan.md onto the plan comment of a task issue."
        )
    )
    parser.add_argument("issue", type=int, help="the task issue number")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the mirror is in sync instead of syncing",
    )
    args = parser.parse_args(argv)
    try:
        repo = run_gh(
            ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
        ).strip()
        if args.check:
            if check(repo, args.issue):
                print(f"issue {args.issue} plan comment in sync")
                return 0
            print(
                f"issue {args.issue} plan comment out of sync with {PLAN_FILE}",
                file=sys.stderr,
            )
            return 1
        cid = sync(repo, args.issue)
    except (RuntimeError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"synced issue {args.issue} plan comment {cid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
