# Detailed plan: #184 RPQ infrastructure readiness

- **Task:** [#184](https://github.com/FormalLanguageConstrainedPathQuerying/FLPQ_Data/issues/184) — RPQ infrastructure readiness: canonical regex/RSM syntax, `regex_to_rsa`, per-graph reachable-pairs tables.
- **Branch:** `feature/184-rpq-infrastructure` (from `dev`).
- **Blocks:** #183 (social_networks data integration) starts after this task merges.
- **Refinement of the issue's subtasks:** issue S1 → plan S1+S2+S3; issue S2 → plan S4; issue S3 → plan S5; issue S4 → plan S6.

## Subtasks

### S1: Canonical regex parser and printer

**Code:** `flpq_data/queries/rpq/readwrite/regex.py` — rewrite `regex_from_text` (recursive-descent parser) and `regex_to_text` (AST printer); `regex_from_txt`/`regex_to_txt` unchanged (they delegate). Reuse: pyformlang `Regex` construction API (`Regex(sym)`, `.concatenate`, `.union`, `.kleene_star()`) — no automaton logic reimplemented.

**Tests:** rewrite/extend `tests/queries/rpq/readwrite/test_regex_readwrite.py` (membership, canonical `regex_to_text` expectations, precedence, `+`, `$`, every error path, round-trip/idempotence battery, data-safety case from #183).

**Docs:** `docs/flpq.rst` RPQ "Format" bullet (precise canonical syntax definition, replacing "the pyformlang `Regex` text syntax"); numpydoc docstrings with doctests; `CHANGELOG.md` `[Unreleased]` `Changed` entry.

**Spec:**
- Canonical syntax (one syntax for `.re` files and EBNF RSM bodies):
  - symbol — maximal run of characters outside the metacharacter set (edge label or nonterminal; generic over symbol names);
  - metacharacters — whitespace (separates), `|` (union), `*` (Kleene star, postfix), `+` (Kleene plus, postfix), `$` (epsilon), `(` `)` (grouping);
  - precedence — postfix > concatenation (whitespace) > union.
- Grammar: `expr := term ('|' term)*`; `term := factor+`; `factor := atom postfix*`; `atom := SYMBOL | '$' | '(' expr ')'`; `postfix := '*' | '+'`.
- Construction: SYMBOL → `Regex(sym)`; `$` → `Regex('$')` (pyformlang-native ε, dedicated `Epsilon` AST node); `atom *` → `atom.kleene_star()`; `atom +` → `atom.concat(atom.kleene_star())`; `term` → left-fold `.concatenate()`; `expr` → left-fold `.union()`. Stacked postfix (`a**`) composes.
- Errors (clear `ValueError` messages): empty/whitespace-only input; unbalanced `)`; unclosed `(`; dangling `|` (leading, trailing, consecutive); dangling `*`/`+` with no preceding atom.
- Printer: walk `head`/`sons`; precedence Union=0 < Concatenation=1 < Star/Symbol/Epsilon=2; a child is parenthesized iff its precedence is lower than the parent operator's; `Epsilon` node → `$`; concatenation joined with `" "`, union with `" | "`, star = child + `"*"`. Idempotent; `regex_from_text(regex_to_text(r))` ≡ `r`.
- Data safety: every existing dataset `.re`/`.rsm` expression parses to the same language (the shipped #183 files use only symbols, whitespace, `*`, `|`, `()` — a strict subset).

### S2: Canonical RSM text format

**Code:** `flpq_data/queries/rpq/readwrite/rsa.py` — EBNF bodies parsed via `regex_from_text` (replaces raw `Regex(body)` at line 122); empty production → `body = "$"` (replaces the `Epsilon().to_text()` = `'epsilon'` hack); `rsa_to_text` body = `box.dfa.to_regex().replace(".", " ")` via a new private helper `_box_body(box) -> str` (reused by S4); drop the pyformlang `Regex` import if unused. Reuse: S1 parser; pyformlang `to_regex()` (verified to emit only symbols, `|`, `*`, `()`, `.`, `$` — never `+`).

**Tests:** extend `tests/queries/rpq/readwrite/test_rsa_readwrite.py` — EBNF body with `+` (Kleene-plus semantics); empty production `S ->` (language {ε}, no phantom `epsilon` terminal in `cfg_from_rsa`); round-trip `rsa_from_text(rsa_to_text(rsa))` preserves every box's language (battery incl. ε-languages, unions, recursive multi-box); `rsa_to_text` output is parseable canonical text.

**Docs:** `docs/flpq.rst` RSM Format section (EBNF bodies follow the canonical regex syntax — cross-reference; empty production = ε; update the "canonical form" sentence; the `B -> (x | y)+` example now means what readers assume); docstrings; `CHANGELOG.md` `Changed` entry.

**Spec:**
- EBNF style: `N -> E` where `E` is a canonical regex over terminals and nonterminals (both are plain symbols to the parser); empty body = ε.
- Transition-system style: unchanged.
- `rsa_to_text` keeps the EBNF style and the production ordering (initial box first, then alphabetical); bodies are canonical.
- Documented constraint: box names/labels must not contain `.` (the `to_regex().replace(".", " ")` transformation); consistent with the identifier-like label convention.

### S3: Route the archive checker through the canonical syntax

**Code:** `flpq_data/tools/check_archive_structure.py` — `_query_terminals` `.re` branch uses `regex_from_text` (import from `flpq_data.queries.rpq.readwrite.regex`); drop the pyformlang `Regex` import if unused. Reuse: S1 parser.

**Tests:** extend the checker's test file (locate under `tests/tools/`) — a `.re` using `+` (Kleene-plus) passes the terminal-set consistency check against a matching `.rsm`; a malformed `.re` (unbalanced parens) is reported as "cannot be parsed". Existing tests stay green.

**Docs:** `_query_terminals` docstring if it references the format; `CHANGELOG.md` `Changed` entry.

**Spec:**
- Terminal extraction for `.re` goes through the canonical parser, so `+` yields the Kleene-plus language's alphabet (same symbols, correct language for any downstream use).
- No change to the checker's other policies (inert terminals legal, terminal-set consistency, RPQ regularity).

### S4: `regex_to_rsa` / `rsa_to_regex` converters

**Code:** new `flpq_data/queries/rpq/converters/` package (mirrors the CFPQ layout): `__init__.py` + `rsa.py` with `regex_to_rsa(regex, *, box_name="S") -> RSA` and `rsa_to_regex(rsa) -> Regex`; `flpq_data/queries/rpq/__init__.py` gains `from flpq_data.queries.rpq.converters import *`. Reuse: pyformlang `RSA`/`Box`/`Symbol`; the `_box_body` helper from S2; the CFPQ converters module layout.

**Tests:** new `tests/queries/rpq/converters/test_rsa_converters.py` (mirrors `tests/queries/cfpq/converters/test_cfg_converters.py`) — language-preservation battery (symbols, concatenation, union, star, plus, ε, nesting; positive + negative words); single-box shape and `box_name` parameter; `rsa_to_regex` round-trip; error paths (multi-box RSA, recursive RSA, non-DFA box).

**Docs:** new `docs/reference/queries/rpq/rpq_converters.rst` (automodule + autosummary, mirroring the CFPQ converters page) + generated stub + toctree entry in `docs/reference/queries/rpq/index.rst`; `docs/flpq.rst` RPQ section note (derivation aid; the RSM remains independently specifiable — the checker couples `.re`/`.rsm` only at terminal-set consistency + regularity, no equivalence requirement); numpydoc docstrings with doctests; `CHANGELOG.md` `Added` entry.

**Spec:**
- `regex_to_rsa`: `dfa = regex.to_epsilon_nfa().minimize()` (verified to determinize); `label = Symbol(box_name)`; return `RSA(labels={label}, initial_label=label, boxes={Box(dfa, label)})`. The produced box language must equal the input regex's language.
- `rsa_to_regex`: require exactly one box and that it is the initial label (else `ValueError`); require the box's dfa to be a `DeterministicFiniteAutomaton` (else `ValueError`); return `regex_from_text(_box_body(box))`.
- One-way derivation aids: neither function is used by the checker; an independently authored RSM that is not an exact copy of the RE-derived one remains fully valid.

### S5: Per-graph reachable-pairs tables

**Code:** `utils/reachable_pairs_tables.py` — `render_tables_region` rewritten to the per-graph layout (all query classes rendered); `_rendered_rows` renamed to `_cfpq_rows` and kept only for the graph-table count columns (`update_category_columns` `by_pair`) and the count-column loop of `_validation_problems`; `update_category_columns` returns `(text, [])` for categories absent from `GRAMMAR_COLUMNS` (nothing to sync) instead of raising; module docstring refreshed. Then run `python utils/reachable_pairs_tables.py --update` to regenerate the `docs/reachable_pairs.rst` region. Reuse: existing `category_order`, `_section_title`, `NOT_AVAILABLE`, `replace_marked_region`, `archive_sizes.header_columns`/`iter_graph_tables`.

**Tests:** rewrite `test_render_tables_region*` in `tests/utils/test_reachable_pairs_tables.py` for the per-graph layout (subheadings, per-graph tables, row order, `NOT_AVAILABLE`, empty-category fallback); new coverage: RPQ rows rendered, mixed-class graph (cfpq + rpq rows in one table), `:ref:` subheadings; replace `test_update_category_columns_unknown_category_raises` with a no-op test (unchanged text, no problems); `test_update_category_columns_ignores_other_classes` stays; the real-repo check-mode test stays green (region regenerated in the same commit).

**Docs:** `docs/reachable_pairs.rst` intro wording (grouped by graph; one row per query) + regenerated region; `docs/utils.rst` tool wording (the region renders all classes; the graph tables render CFPQ counts only); `CHANGELOG.md` `Changed` entry.

**Spec (exact layout, per D4 of the issue):**
```
<category title>
----------------

:ref:`<graph>`
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :align: left

   * - Query
     - Reachable pairs
   * - <grammar file>
     - <count | "not available">
```
- Categories in `category_order`; graphs sorted; rows sorted by the CSV `grammar` filename (the extension makes the class self-describing).
- Graph subheading is a `:ref:` targeting the graph name — all 113 per-graph pages carry a `.. _<graph>:` label (verified); underline = tildes, length of the heading line.
- The "No reachable-pair counts have been computed for this category yet." fallback is kept for categories with no rows of any class.
- The CFPQ count columns of the per-category graph tables are unchanged.

### S6: Count-less category convention

**Code:** none (documentation-only subtask).

**Tests:** skipped (no code).

**Docs:** `docs/graphs/index.rst` Contents intro — a sentence defining when a category table omits the "Reachable pairs" column (no single category-wide canonical grammar, e.g. per-graph RPQ queries; per-query counts live in `docs/reachable_pairs.rst` and the per-graph pages); `CHANGELOG.md` entry.

**Spec:**
- The convention must match what S5 implements (categories absent from `GRAMMAR_COLUMNS` are skipped by the tool).
- This is the last subtask: its commit carries `Closes #184`.

## Status

- S1: [x]
- S2: [x]
- S3: [ ]
- S4: [ ]
- S5: [ ]
- S6: [ ]
