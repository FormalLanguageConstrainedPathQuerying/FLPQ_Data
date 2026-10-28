# Detailed Plan: Task 173 — Fix broken TeX in the docs and harden the math guard

Task: #173 (bug: "Double subscripts: use braces to clarify" on the
field-sensitive-alias pages)
Linked: #174 (bug: "Misplaced &" on seven grammar pages — discovered by the
new guard during this task)
Branch: `feature/173-mathjax-guard` (from `dev`)

## Background

- The deployed site renders math with MathJax 4.1.3: `sphinx.ext.mathjax`
  (Sphinx 9.0.4) loads
  `https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js`. A snippet the
  engine cannot parse shows up as MathJax error text on the deployed page
  while the Sphinx build stays green.
- The existing guard (`utils/check_math_snippets.py`, added for #127)
  detects only one hand-crafted pattern (unescaped `_` inside text-mode
  groups) and missed the double-subscript class of #173.
- Decision (user guidance): no hand-crafted TeX parser — validate with the
  standard tooling, i.e. the MathJax engine itself, run on Node through the
  officially supported `mathjax` npm package entry point
  (`require('mathjax').init(...)` + `tex2mml`). Both sides are pinned to the
  same version (4.1.3) so the checker and the browser cannot drift apart.

## Findings (verified with mathjax 4.1.3 on Node 22)

- 11 snippets with `f_r_i` (double subscript):
  `docs/graphs/data/{cactus,imagick,leela,nab,omnetpp,parest,perlbench,povray,x264,xz}_field_sensitive_alias.rst:52`
  and `docs/graphs/field_sensitive_alias.rst:108`.
- 7 `.. math::` blocks using `&` alignment tabs in plain display math
  ("Misplaced &"): `docs/graphs/biological_uniprot.rst`,
  `docs/graphs/data_provenance.rst`, `docs/graphs/name_resolution.rst`,
  `docs/queries/cfpq/data/{c_alias,dyck,java_points_to,nested_parentheses}.rst`.
- All other 556 snippets of the docs tree compile cleanly.
- No broken math in `flpq_data` docstrings (only `mcfg.py` carries
  `:math:` roles; all valid).

## Subtasks

### S1: Fix the 18 broken math snippets in the docs [done] 823be4b

**Code:** docs only:
- 11× `f_r_i` → `f_{r\_i}` (braced subscript with escaped inner underscore,
  matching the existing `\textit{store}_{r\_f}` convention on the
  java_points_to pages):
  - `docs/graphs/field_sensitive_alias.rst` (canonical-grammar math block)
  - `docs/graphs/data/{cactus,imagick,leela,nab,omnetpp,parest,perlbench,povray,x264,xz}_field_sensitive_alias.rst`
    (Edges Statistics table row)
- 7× wrap the `&`-aligned math blocks in `\begin{aligned} ... \end{aligned}`:
  - `docs/graphs/biological_uniprot.rst`
  - `docs/graphs/data_provenance.rst`
  - `docs/graphs/name_resolution.rst`
  - `docs/queries/cfpq/data/c_alias.rst`
  - `docs/queries/cfpq/data/dyck.rst`
  - `docs/queries/cfpq/data/java_points_to.rst`
  - `docs/queries/cfpq/data/nested_parentheses.rst`

**Tests:** the existing suite stays green (the old guard passes; the new
guard lands in S2/S3). Every fixed snippet is verified to compile cleanly
in the MathJax 4.1.3 oracle during implementation.

**Docs:** the change is the docs themselves.

**Spec:**
- `f_{r\_i}` renders f with subscript "r_i" (literal underscore), the
  faithful rendering of the edge-label string `f_r_i`.
- The `aligned` wrapper keeps the visual layout: `&` becomes the alignment
  tab of the environment, `\\` line breaks are unchanged.
- No other content on the affected pages changes.

### S2: Add the MathJax Node oracle [done] 9295c6c

**Code:**
- `package.json` + `package-lock.json` at the repo root: exact pin
  `"mathjax": "4.1.3"` (the version the browser bundle serves).
- `utils/check_math_snippets_node.cjs`: reads a JSON array of
  `{file, line, display, snippet}` from stdin; compiles each with
  `tex2mml(snippet, {display})`; prints one line per failure
  `file:line: <merror message> :: snippet`; exit 0 clean, 1 on failures,
  2 on oracle malfunction.
- `docs/conf.py`: `mathjax_js =
  'https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js'` — pin the
  browser to the checker's version.
- `.github/workflows/tests.yml` + `.github/workflows/coverage.yml`: an
  `npm ci` step before the test step (Node is preinstalled on all runner
  OSes).

**Tests:** `tests/utils/test_check_math_snippets_node.py` — runs the `.cjs`
script with synthetic snippets: broken (`f_r_i`, `\textit{a_b}`, `a_{b`,
`x_`, `a^b^c`) and valid (`f_{r\_i}`, `a_{b_c}`, `a_b^c`,
`\textit{store}_{r\_f}`, an `aligned` block); asserts exit codes and the
reported messages.

**Docs:** `docs/developer.rst` "Development setup": Node.js ≥ 20 and
`npm ci` as prerequisites of the math guard.

**Spec:**
- The oracle is the only TeX validator: no hand-crafted TeX pattern code.
- The node script is a pure function of its stdin: no file access, no
  network, deterministic.
- merror messages are reported verbatim (whitespace-collapsed).
- `display` flag: `true` for `.. math::` block bodies, `false` for
  `:math:` inline roles — the engine must compile in the same mode the
  browser renders.

### S3: Rewire the checker to the oracle; scan docstrings [done] c92eacd

**Code:** `utils/check_math_snippets.py`:
- `extract_math_snippets`: keep the RST extraction; return
  `(line, snippet, display)` triples (`display=True` for `.. math::`
  bodies, `False` for `:math:` roles).
- Delete the hand-crafted TeX pattern code: `_TEXT_MODE_RE`,
  `_text_mode_groups`, `_has_unescaped_underscore`, `find_broken_snippets`.
- New `check_snippets(snippets)`: one Node subprocess per call (batched
  JSON on stdin, bounded timeout); returns one message per broken snippet.
- New `check_package(package_dir)`: ast-walks `*.py` docstrings, extracts
  math snippets with `extract_math_snippets`, validates them through the
  same oracle.
- `check_docs`: same signature, now oracle-backed.
- `main`: `--dir` (default `docs`) and `--package` (default
  `flpq_data`); runs both scans.
- Fails loudly (clear message, non-zero exit) when `node` or
  `node_modules` is missing — never silently skips.

**Tests:** `tests/utils/test_check_math_snippets.py`:
- keep the pure-Python extraction tests (updated to the triple form);
- oracle-backed broken/valid tests through `check_snippets` (synthetic);
- docstring tests: a tmp package tree with a broken `:math:` role in a
  docstring is flagged, a clean one passes;
- `test_real_docs_tree_is_clean` (now oracle-backed) + new
  `test_real_package_is_clean`;
- missing-node behavior (monkeypatched `shutil.which`) raises the clear
  error.

**Docs:** `docs/developer.rst` "Test pipeline": the guard validates every
docs-page and package-docstring math snippet with the same MathJax engine
the browser uses.

**Spec:**
- Message format: `path:line: <MathJax message> :: snippet`, sorted by
  file.
- Docstring line numbers: docstring start line + snippet offset within the
  docstring (1-based).
- One Node process per `check_docs`/`check_package` call, not per snippet.
- The hand-crafted pattern code is deleted, not kept behind a flag.

### S4: Pre-commit hook, docs, changelog [done] 0578e61

**Code:** `.pre-commit-config.yaml`: local hook `check-math-snippets`
(entry `python3 utils/check_math_snippets.py`, `language: system`,
`pass_filenames: false`, `always_run: true`).

**Tests:** none new (the hook config is exercised by pre-commit itself; the
driver is covered by the S3 tests).

**Docs:**
- `docs/developer.rst` "Quality checks": add the math guard to the
  enumerated hook list (the config file stays the source of truth).
- `CHANGELOG.md` `[Unreleased]`:
  - Fixed: the 11 double-subscript snippets (#173) and the 7 misplaced-&
    grammar blocks (#174).
  - Changed: the math-snippet guard validates with the MathJax engine
    itself (mathjax 4.1.3 on Node) instead of hand-crafted patterns; the
    browser bundle is pinned to the same version; the guard also covers
    package docstrings; pre-commit hook.

**Spec:**
- The hook runs the full driver (docs + package); ~2–3 s.
- The last commit of the task carries `Fixes #173` and `Fixes #174` as
  standalone lines.

## Out of scope

- `$...$` spans via the `texext` extension: zero occurrences in the docs;
  mirroring texext's matching rules is a follow-up if/when used.
- `README.rst`: contains no math.
