# Building docs

We use Sphinx for generating the API and reference documentation. The build
and link-check commands are exactly what CI runs — the "Build" and
"Check links" steps of `.github/workflows/docs.yml` (the project keeps CI
workflows as the source of truth for the commands they run; see the
"Developer guide"). This page keeps only the local setup command.

## Instructions

Install the Python packages needed to build the documentation from the uv
`docs` dependency group — the same one the CI workflows install::

    uv sync --only-group docs

in the root directory.

The build generates a ``docs/_build/html`` subdirectory containing the
built documentation. It runs with the no-warnings policy (``-W --keep-going``
in ``docs/Makefile``): any Sphinx warning — including an unresolved
cross-reference under ``nitpicky = True`` — fails the build and lists every
warning in one run. Fix the warnings; do not suppress them.

A plain rebuild reuses cached doctrees and git-ignored autosummary stubs
from previous builds, so it is not CI-equivalent (see the "Fresh-state
verification" policy in the developer guide). The fresh build wipes them
first::

    uv run make -C docs/ fresh

## Check links

The link check verifies that all links in the documentation resolve (local
targets against the filesystem, external URLs over HTTP). It runs in full —
no URL classes are skipped by default; see ``linkcheck_ignore`` in
``docs/conf.py`` for the documented exceptions. The command exits
non-zero if any link is broken or times out; redirects are reported but do
not fail the check. It is network-bound and slow locally (rate-limited
retries), so it runs in CI only — the "Check links" step of
`.github/workflows/docs.yml` — and is not part of the local quality gate.
