.. _developer:

Developer guide
===============

.. only:: html

   :Release: |release|
   :Date: |today|

How to set up a development environment, run the checks that continuous
integration runs, and contribute to FLPQ_Data. If you only want to *use*
the package, start with :doc:`/getting_started` instead.

.. _developer-ci:

CI as source of truth
---------------------

The CI workflows under :file:`.github/workflows/` are the source of truth
for every command they run: this page and the agent skills reference the
workflow file and step name instead of restating such a command, so a
command changes in exactly one place. Commands with non-trivial arguments
(flags, paths, multi-part pipelines) always take that reference form; bare
tool invocations (``uv run ty check``, ``uv run pyright``) may stay inline
where they name a gate step, because they carry no drift risk. What this
page still documents is what CI does not cover: local-only commands
(environment setup, installing the git hook, running a single test module)
and the policies behind the checks — the no-warnings build, the 95/95
coverage gate, doctests as tests.

.. _developer-setup:

Development setup
-----------------

FLPQ_Data requires Python 3.11–3.13 (``pyproject.toml`` declares
``>=3.11,<3.14``). The canonical development environment is **uv** — all CI
workflows install their dependencies through it. Install uv once (see the
`uv installation guide <https://docs.astral.sh/uv/getting-started/installation/>`_),
then from the repository root::

   uv sync --all-groups

- ``--all-groups`` pulls the three PEP 735 dependency groups from
  ``pyproject.toml``: developer tools (``ruff``, ``ty``, ``pyright``,
  ``pre-commit``, ``boto3``), test extras (``pytest``, ``pytest-cov``), and
  the Sphinx docs stack. The full environment is needed because every check
  must resolve imports from any dependency group — ty/pyright type-check
  ``tests/``, ``docs/conf.py`` and ``utils/``, which import pytest, sphinx
  and boto3.
- ``uv sync`` also installs ``flpq_data`` itself (editable) into the project
  environment, so no separate install step is needed; ``uv run ...`` executes
  commands inside that environment.
- The committed :file:`uv.lock` pins every dependency; CI passes ``--frozen``
  to fail on a lockfile that is out of sync with ``pyproject.toml``.

The math-snippet guard (see "Test pipeline") validates docs math with the
MathJax engine itself, which runs on Node.js (>= 20). Install Node.js once,
then from the repository root::

   npm ci

The committed :file:`package-lock.json` pins the engine version; it must
match the ``mathjax_js`` URL in :file:`docs/conf.py`, so the guard and the
browser render with the same MathJax version.

.. _developer-quality:

Quality checks
--------------

Linting, formatting, and type checking are managed by uv and run through
``pre-commit``. The hook list — hygiene checks, the official ``uv-lock`` and
ruff hooks (check with autofix plus format), a version-sync check that fails
when :file:`flpq_data/config.py` and :file:`pyproject.toml` declare different
versions, and a local ty type check — is defined in
:file:`.pre-commit-config.yaml`, which is the source of truth; do not
maintain a copy of it elsewhere.

The ``ruff-pre-commit`` hook revision must match the ruff version locked in
:file:`uv.lock`; bump both together when upgrading ruff.

Install the git hook once so the checks run on every commit::

   uv run pre-commit install

Run the full pass manually — it is exactly the "Run pre-commit" step of
:file:`.github/workflows/lint.yml`.

The individual tools can also be run directly::

   uv run ruff check .
   uv run ruff format .
   uv run ty check

CI additionally runs Pyright, the stricter of the two type checkers; ty is
the fast local check. The full pass runs on every push and pull request
(:file:`.github/workflows/lint.yml`).

The package ships a PEP 561 :file:`py.typed` marker, so type checkers in
downstream projects use the inline annotations of ``flpq_data`` instead of
treating it as untyped.

.. _developer-tests:

Test pipeline
-------------

The test suite is ``pytest`` with **doctests enabled**: the ``Examples``
sections of public docstrings are executed as tests, so the documented
behavior and the tested behavior are the same code. The canonical command
is exactly what CI runs — the "Test FLPQ_Data with coverage (line and
branch >= 95%)" step of :file:`.github/workflows/coverage.yml`.

Coverage is part of the pipeline: branch coverage is always on
(``[tool.coverage.run]`` in ``pyproject.toml``), and the check fails unless
**both** line and branch coverage are at least 95%. The threshold lives in
``utils/check_coverage.py`` because the combined ``--cov-fail-under`` cannot
enforce each metric separately. A single module or function runs without the
coverage gate::

   uv run pytest tests/graphs/utils/test_add_reverse_edges.py

The suite also validates the math snippets of the docs pages and of the
package docstrings (rendered on the reference pages): Sphinx passes math
verbatim to MathJax, which renders it in the browser, so a broken snippet
sails through the Sphinx build and shows up only as an error on the
deployed site. The guard therefore validates every snippet with the MathJax
engine itself — ``utils/check_math_snippets.py`` extracts the ``:math:``
roles and ``.. math::`` bodies and compiles them with
``utils/check_math_snippets_node.cjs`` (the same engine version the browser
loads, see "Development setup") — and fails the suite on any snippet the
engine rejects, reporting the engine's own error message.

- Doctest discovery and test paths are configured in ``pyproject.toml``
  (``[tool.pytest.ini_options]``).
- ``tests/`` mirrors the package layout (e.g. ``tests/graphs/generators/``
  for ``flpq_data/graphs/generators/``).

Continuous integration:

- :file:`.github/workflows/tests.yml` — runs the suite on every push and pull
  request across a matrix of Linux, macOS, and Windows with Python 3.11.
- :file:`.github/workflows/coverage.yml` — runs the same suite with coverage,
  enforces the 95/95 line+branch gate with ``utils/check_coverage.py``, and
  uploads the report to Codecov.

.. _developer-docs:

Docs build and deploy
---------------------

The documentation is built with Sphinx from the :file:`docs/` directory.
The build and link-check commands are exactly what CI runs — the "Build"
and "Check links" steps of :file:`.github/workflows/docs.yml`; the local
setup command lives in :file:`docs/README.md`. Two policies matter:

- **No-warnings policy.** The build runs with ``-W --keep-going`` (set in
  :file:`docs/Makefile`), so any Sphinx warning — including an unresolved
  cross-reference under ``nitpicky = True`` — fails the build. Fix warnings;
  do not suppress them.
- **Full link check.** ``sphinx-build -b linkcheck`` verifies every local
  target and external URL (two documented exceptions in
  :file:`docs/conf.py`); it exits non-zero on broken or timed-out links. It
  is network-bound and slow locally (rate-limited retries), so it runs in CI
  only — the "Check links" step of :file:`.github/workflows/docs.yml` — and
  is not part of the local quality gate (see "Quality gate").
- **Resilient inventory fetches.** Intersphinx inventories are fetched with
  retries on transient connection errors (:file:`docs/conf.py`); a persistent
  failure still warns and fails the build.
- **Fresh-state verification.** CI builds from a fresh checkout; locally two
  artifact classes survive a plain rebuild and can mask failures — cached
  doctrees (references in unchanged documents are not re-resolved) and the
  git-ignored autosummary stubs under ``docs/*/generated/`` (parsed as
  ordinary documents, registering objects of an older build state). After
  adding or removing reference targets, autosummary entries, or automodule
  directives, verify with the fresh build (the ``fresh`` target of
  :file:`docs/Makefile`; the local command in :file:`docs/README.md`).

**Deployment.** Pushing to ``master`` deploys the site:
:file:`.github/workflows/deploy_docs.yml` builds the HTML and publishes
:file:`docs/_build/html` to the ``gh-pages`` branch, which GitHub serves as
the project website (https://formallanguageconstrainedpathquerying.github.io/FLPQ_Data).
The workflow skips forks — it runs only for the owning repository.

.. _developer-release:

Package deploy
--------------

Cutting a release — version bump, changelog, ``vX.Y.Z`` tag, and the
automated PyPI publish (Trusted Publishing) plus dataset publishing — is
documented in :doc:`release`.

.. _developer-guidelines:

Contribution guidelines
-----------------------

Branching model
~~~~~~~~~~~~~~~

- ``dev`` — the stable development branch; all work merges here first.
- ``master`` — the protected release branch. A release merges ``dev`` into
  ``master`` via a pull request and then pushes a ``vX.Y.Z`` tag matching the
  package version (see :doc:`release`).
- ``feature/XXX-short-description`` — one feature branch per task; never
  combine multiple tasks in a single branch.

Commits
~~~~~~~

Conventional Commits with exactly one subtask identifier, one commit per
atomic subtask::

   feat(XXX-SN): description
   fix(XXX-SN): description
   docs(XXX-SN): description

``XXX`` is the task's GitHub issue number and ``SN`` a single subtask
identifier (ranges or lists are not allowed). Commit messages must explain
*why* the change was made, not only what it does.

Issue references
~~~~~~~~~~~~~~~~

Every task is itself a GitHub issue (label ``task``; the working loop lives
in the ``workflow-management`` skill). GitHub closes an issue automatically
once a commit containing a closing keyword (``close``, ``closes``, ``closed``,
``fixes``, ``fixed``) reaches the repository's default branch (`mechanism
<https://github.blog/news-insights/product-news/closing-issues-via-commit-messages/>`_).
This project relies on that mechanism:

- A completed task carries the closing keyword for its own issue — and for
  every linked issue it fully resolves — in exactly one commit: by
  convention, the last subtask's commit. Each keyword is a standalone line in
  the message body: ``Fixes #N`` when the work fixes a reported defect,
  ``Closes #N`` otherwise. No other commit of the task repeats a keyword::

     docs(XXX-S3): final subtask — verify and clean up

     Closes #XXX
     Fixes #127

- A task that only partially addresses a linked issue references it without a
  closing keyword (bare ``#N``); GitHub links the issue but leaves it open.

Because the keywords live in the last subtask's commit, an incomplete or
blocked task — whose branch never merges — carries no keyword and can never
close its issue by accident.

Since feature branches merge to ``dev`` and only releases merge ``dev`` into
``master``, the default branch, a task's issue closes when the release
containing the task lands on ``master`` — not when the task merges to ``dev``.

Quality gate
~~~~~~~~~~~~

Before a feature branch merges to ``dev``, all of the following must pass —
no exceptions:

1. The full test suite: 0 failures, 0 skipped.
2. The full pre-commit pass: no errors.
3. Type checking: ``uv run ty check`` and Pyright both report no errors.
4. The docs build: exit 0 under the no-warnings policy.
5. The link check (CI only): the "Check links" step of
   :file:`.github/workflows/docs.yml` reports no broken or timed-out links.
   It is network-bound and slow locally (rate-limited retries), so it is not
   part of the local gate — the branch's CI run must be green before merge.

Merge strategy
~~~~~~~~~~~~~~

Rebase the feature branch onto ``dev`` and fast-forward ``dev`` to it —
linear history, no squash, so every subtask commit keeps its own message.

Adding graphs and grammars
~~~~~~~~~~~~~~~~~~~~~~~~~~

New dataset entries — graphs, queries, grammars — enter through a single
CONTRIBUTE NEW DATA issue; the full flow is documented in
:doc:`contributing_data`.
