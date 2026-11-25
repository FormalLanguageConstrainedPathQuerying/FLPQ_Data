---
name: release
description: Use when cutting an FLPQ_Data release — bumping the version, finalizing the changelog, tagging, publishing to PyPI — or recovering from a failed publish. Covers the procedure, the automated publish workflow, and recovery.
---

# Release

Cut a release of the `flpq-data` package. The model, versioning policy,
prerequisites, and packaging constraints are documented in `docs/release.rst`
— do not duplicate them here. Publishing is automated by
`.github/workflows/publish.yml`: on a `v*` tag push it builds, publishes to
PyPI, and creates the GitHub Release; on every PR targeting `master` it
pre-publishes to TestPyPI as a packaging check.

## Procedure

History is kept **linear**: no merge commits on `master`. Before the
release PR, rebase `dev` onto `origin/master` (resolving conflicts, e.g.
`uv.lock`, by regenerating with `uv lock`), run the quality gate, and push
`dev` (`--force-with-lease` when the rebase rewrote published commits).
Merge the PR with **rebase or fast-forward** — never a merge commit, never
squash.

1. Bump the version and finalize the changelog:

   ```bash
   python utils/bump_version.py X.Y.Z
   ```

   Sets `config.py` + `pyproject.toml` to `X.Y.Z` and promotes the
   `[Unreleased]` changelog section to `## [X.Y.Z] - <today>`.
2. Verify the version guard passes:

   ```bash
    uv run pre-commit run check-version-sync --all-files
   ```
3. Commit the bump (message: `chore: release X.Y.Z`).
4. Merge `dev` into `master` via a pull request (`master` is protected; do
   not squash). This also deploys the docs. Wait for the PR's **Publish**
   check (the TestPyPI pre-publish) to pass — it validates packaging for
   exactly the code that will be released. The user reviews and merges the
   PR manually; proceed only after they confirm the merge.
5. Tag the merged commit and push the tag:

   ```bash
   git fetch origin
   git tag -a vX.Y.Z -m "Release vX.Y.Z" origin/master
   git push origin vX.Y.Z
   ```
6. The `publish` workflow builds, publishes to PyPI (Trusted Publishing),
   and creates the GitHub Release. Verify both: the package is live on
   <https://pypi.org/project/flpq-data/> and the GitHub Release carries the
   `[X.Y.Z]` changelog section with the dist artifacts as assets.

## Recovery

Use the `gh` CLI (installed and authenticated on this machine; if a new
machine is not, run `gh auth login` first).

### Workflow failed before the PyPI publish

Nothing reached PyPI, so the tag can simply be replaced:

```bash
git push origin :refs/tags/vX.Y.Z   # delete the tag
```

Fix the failure, merge the fix to `master` (PR + user merge), then re-tag
the new `origin/master` and push again.

### Workflow failed after the PyPI publish (e.g. the GitHub Release step)

PyPI already has the files for this version and rejects re-uploads — an
owner must delete the release on PyPI before the tag can be re-pushed (see
`docs/release.rst`). In the meantime, create the GitHub Release manually so
the release is complete:

1. Extract the changelog section (same logic as the workflow):

   ```bash
   awk -v v="X.Y.Z" 'index($0, "## [" v "]") == 1 {insec=1; next} /^## / && insec {exit} insec {print}' CHANGELOG.md > release_notes.md
   ```

2. Create the release for the existing tag with the extracted notes:

   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file release_notes.md
   ```

3. Upload the dist artifacts — download them from PyPI first so the release
   assets are byte-identical to what was published
   (`flpq_data-X.Y.Z-py3-none-any.whl`, `flpq_data-X.Y.Z.tar.gz`):

   ```bash
   gh release upload vX.Y.Z flpq_data-X.Y.Z-py3-none-any.whl flpq_data-X.Y.Z.tar.gz
   ```

## Notes

- **Major version bumps** also move the dataset prefix (`<major>.0.0/graph/`):
  upload/copy all archives with `utils/upload_to_s3.py` before pushing the tag.
  Minor/patch releases do not touch the dataset.
- Releasing is the deliberate exception to the "no push" convention (it merges
  to `master` and pushes a tag).
- First-time publishing needs PyPI access set up by an owner (Trusted
  Publishing or a token) — see `docs/release.rst`.
