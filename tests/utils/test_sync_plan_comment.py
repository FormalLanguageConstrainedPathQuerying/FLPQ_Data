import json
import subprocess

import pytest
from sync_plan_comment import (
    PLAN_MARKER,
    build_body,
    check,
    find_plan_comment,
    main,
    run_gh,
    sync,
)

REPO = "owner/name"
ISSUE = 192
COMMENT_ID = 123
PLAN_TEXT = "# Detailed plan: #192\n\n## Status\n\n- S1: [ ]\n"


def _dispatch(calls, *, comments_out="123\n", repo_out="owner/name\n", body_out=""):
    """A ``run_gh`` fake routing by the gh subcommand in *args*."""

    def fake(args, *, input=None):
        calls.append((list(args), input))
        if args[0] == "repo":
            return repo_out
        if args[0] == "api" and args[1] == f"repos/{REPO}/issues/{ISSUE}/comments":
            return comments_out
        if args[0] == "api" and args[1] == f"repos/{REPO}/issues/comments/{COMMENT_ID}":
            return body_out
        return ""

    return fake


def test_build_body_precedes_marker():
    assert build_body(PLAN_TEXT) == PLAN_MARKER + "\n" + PLAN_TEXT


def test_run_gh_raises_on_failure(monkeypatch):
    proc = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr="boom\n")
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: proc)
    with pytest.raises(RuntimeError, match="boom"):
        run_gh(["api", "x"])


def test_find_plan_comment_parses_id_and_filters_by_marker(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "sync_plan_comment.run_gh", _dispatch(calls, comments_out="123\n")
    )

    assert find_plan_comment(REPO, ISSUE) == COMMENT_ID

    ((args, _),) = calls
    assert args[:2] == ["api", f"repos/{REPO}/issues/{ISSUE}/comments"]
    # The jq filter keeps marker comments and takes the last one.
    assert PLAN_MARKER in args[args.index("--jq") + 1]
    assert "last.id" in args[args.index("--jq") + 1]


def test_find_plan_comment_raises_when_absent(monkeypatch):
    monkeypatch.setattr(
        "sync_plan_comment.run_gh", _dispatch([], comments_out="null\n")
    )
    with pytest.raises(RuntimeError, match=f"issue {ISSUE}"):
        find_plan_comment(REPO, ISSUE)


def test_sync_patches_the_comment_body(tmp_path, monkeypatch):
    plan = tmp_path / "detailed_plan.md"
    plan.write_text(PLAN_TEXT, encoding="utf-8")
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", plan)
    calls = []
    monkeypatch.setattr("sync_plan_comment.run_gh", _dispatch(calls))

    assert sync(REPO, ISSUE) == COMMENT_ID

    patch_calls = [c for c in calls if c[0][1] == "-X"]
    ((args, payload),) = patch_calls
    assert args[:4] == [
        "api",
        "-X",
        "PATCH",
        f"repos/{REPO}/issues/comments/{COMMENT_ID}",
    ]
    assert json.loads(payload) == {"body": PLAN_MARKER + "\n" + PLAN_TEXT}


def test_main_end_to_end(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "detailed_plan.md"
    plan.write_text(PLAN_TEXT, encoding="utf-8")
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", plan)
    calls = []
    monkeypatch.setattr("sync_plan_comment.run_gh", _dispatch(calls))

    assert main([str(ISSUE)]) == 0

    assert (
        capsys.readouterr().out == f"synced issue {ISSUE} plan comment {COMMENT_ID}\n"
    )
    assert any(c[0][0] == "repo" for c in calls)
    assert any(c[0][1] == "-X" for c in calls)


def test_main_missing_plan_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", tmp_path / "absent.md")
    calls = []
    monkeypatch.setattr("sync_plan_comment.run_gh", _dispatch(calls))

    assert main([str(ISSUE)]) == 1

    err = capsys.readouterr().err
    assert "absent.md" in err
    assert not any(c[0][1] == "-X" for c in calls)


def _in_sync_body_out():
    # The API stores the sent body with one extra trailing newline, and
    # the jq output appends one more.
    return build_body(PLAN_TEXT) + "\n\n"


def test_check_returns_true_when_in_sync(tmp_path, monkeypatch):
    plan = tmp_path / "detailed_plan.md"
    plan.write_text(PLAN_TEXT, encoding="utf-8")
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", plan)
    monkeypatch.setattr(
        "sync_plan_comment.run_gh", _dispatch([], body_out=_in_sync_body_out())
    )

    assert check(REPO, ISSUE) is True


def test_check_returns_false_on_drift(tmp_path, monkeypatch):
    plan = tmp_path / "detailed_plan.md"
    plan.write_text(PLAN_TEXT, encoding="utf-8")
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", plan)
    drifted = build_body(PLAN_TEXT.replace("- S1: [ ]", "- S1: [x]"))
    monkeypatch.setattr(
        "sync_plan_comment.run_gh", _dispatch([], body_out=drifted + "\n\n")
    )

    assert check(REPO, ISSUE) is False


def test_main_check_mode_reports_sync_and_drift(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "detailed_plan.md"
    plan.write_text(PLAN_TEXT, encoding="utf-8")
    monkeypatch.setattr("sync_plan_comment.PLAN_FILE", plan)
    calls = []
    monkeypatch.setattr(
        "sync_plan_comment.run_gh", _dispatch(calls, body_out=_in_sync_body_out())
    )

    assert main([str(ISSUE), "--check"]) == 0
    assert capsys.readouterr().out == f"issue {ISSUE} plan comment in sync\n"
    assert not any(c[0][1] == "-X" for c in calls)

    monkeypatch.setattr(
        "sync_plan_comment.run_gh",
        _dispatch(calls, body_out=_in_sync_body_out() + "DRIFT"),
    )
    assert main([str(ISSUE), "--check"]) == 1
    assert "out of sync" in capsys.readouterr().err
