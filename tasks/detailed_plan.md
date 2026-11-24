# Detailed plan: #185 Fix the flaky eclass linkcheck failure in the docs build

- **Task:** [#185](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/185) — the eclass Wayback Machine snapshot intermittently fails the docs link check from GitHub's datacenter runners (429 rate-limit on `master` run 43561420918, 2026-11-14; connection refusal on `feature/184-rpq-infrastructure` run 45374247328, 2026-11-24) while the snapshot is valid for human readers (HTTP 200 from a residential connection, verified 2026-11-24).
- **Branch:** `feature/185-eclass-linkcheck` (from `dev`).
- **Related:** the "Dependabot Updates" failure on `master` (run 43515039804) is a separate finding — stale GitHub-backend state, not fixable from the repo; tracked in [#186](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/186).

## Subtasks

### S1: Exclude the eclass Wayback snapshot from the link check

**Code:** `docs/conf.py` — add the eclass snapshot URL to the existing `linkcheck_ignore` list and extend the list's comment to cover the new failure class. Reuse: the existing `linkcheck_ignore` mechanism and its dated-verification comment convention (the two existing entries, `dl.acm.org` and `dacapobench.sourceforge.net`, are the model) — no new mechanism.

**Tests:** no unit tests cover `docs/conf.py` (verified by grep); the link check itself is network-bound and CI-only (the "Check links" step of `.github/workflows/docs.yml`, see "Docs build and deploy" in `docs/developer.rst`). Local verification: confirm the new regex matches the eclass URL (both occurrences) and no other URL in the docs.

**Docs:** `docs/developer.rst` — the "Full link check" bullet says "two documented exceptions in `docs/conf.py`"; the hardcoded count is a fact derivable from `conf.py` and goes stale with every added exception, so it is dropped (the bullet keeps the pointer to `conf.py` as the source of truth). No CHANGELOG entry: linkcheck config changes have never carried one (precedent: `docs(42-S6)`, `docs(43-S5)`).

**Spec:**
- Append to `linkcheck_ignore` the capture-scoped regex
  `r"https?://web\.archive\.org/web/20160309143952/http://ebusiness-unibw\.org/.*"`
  — the timestamp `20160309143952` pins the exact frozen 2016 capture of the
  removed original host (repointed there by `fix(173-S5)`), so nothing under
  it can rot, while other `web.archive.org` captures/hosts stay checked.
  (Capture-scoped rather than the full URL because the full-URL regex exceeds
  the 88-char line limit.)
- The comment records: the failure mode (429 / connection refusal from
  datacenter IPs despite the descriptive User-Agent, sequential workers, 5
  retries, and the 120 s 429 back-off — the master run exhausted ~4.5 minutes
  of back-off and still got 429), both observed runs with dates, the validity
  verification (HTTP 200 from a residential connection, 2026-11-24), and the
  re-verify-before-removing instruction, matching the existing entries' style.
- `docs/developer.rst`: "two documented exceptions" → "the documented
  exceptions" (count dropped; `conf.py` is the source of truth).

## Status

- S1: [x]
