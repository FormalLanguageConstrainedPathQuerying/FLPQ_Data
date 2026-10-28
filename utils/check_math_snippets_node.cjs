#!/usr/bin/env node
/**
 * MathJax oracle for the math-snippet guard.
 *
 * Compiles every snippet with the same MathJax engine (and version) the
 * deployed docs load in the browser: docs/conf.py pins mathjax_js to the
 * version this script requires from package.json. A snippet the engine
 * cannot parse yields <merror> nodes carrying the exact message shown on
 * the deployed page, so the guard and the renderer cannot disagree.
 *
 * Input: a JSON array of {file, line, display, snippet} objects on stdin.
 * Output: one line per broken snippet, `file:line: <message> :: snippet`.
 * Exit codes: 0 clean, 1 broken snippets found, 2 oracle malfunction.
 */
'use strict';

const MERROR_RE = /<merror[^>]*>([\s\S]*?)<\/merror>/g;

function collapse(s) {
  return s.replace(/\s+/g, ' ').trim();
}

function main() {
  let data = '';
  process.stdin.on('data', (chunk) => {
    data += chunk;
  });
  process.stdin.on('end', () => {
    let items;
    try {
      items = JSON.parse(data);
      if (!Array.isArray(items)) {
        throw new Error('expected a JSON array');
      }
    } catch (err) {
      console.error(`check_math_snippets_node: bad input: ${err.message}`);
      process.exit(2);
    }
    require('mathjax')
      .init({
        loader: { load: ['input/tex'] },
        startup: { typeset: false },
      })
      .then((MathJax) => {
        let broken = 0;
        for (const item of items) {
          const out = MathJax.tex2mml(item.snippet, { display: !!item.display });
          const messages = [...out.matchAll(MERROR_RE)].map((m) =>
            collapse(m[1].replace(/<[^>]+>/g, ''))
          );
          if (messages.length) {
            broken += 1;
            console.log(
              `${item.file}:${item.line}: ${messages.join('; ')} :: ${item.snippet}`
            );
          }
        }
        process.exit(broken ? 1 : 0);
      })
      .catch((err) => {
        console.error(`check_math_snippets_node: oracle failure: ${err.message}`);
        process.exit(2);
      });
  });
}

main();
