Fix all "Tightening" priority items from TODOS.md. These are small, surgical
code-quality changes. Work through each item in order.

---

## Item 1: Fix raw-Unicode subset arg unreachability

File: scripts/build.py line ~56

The conditional order in load_subset_codepoints() checks `"+" in subset_arg`
before `"U+" in subset_arg.upper()`, making raw Unicode range inputs (e.g.
"U+0041-U+007A") unreachable — they get consumed by the named-range combiner.

Fix: reorder the conditionals so the `U+` prefix check comes first.
Update tests/test_build.py — the test currently marked
`test_raw_unicode_range_is_unreachable` should be updated to assert the
corrected behavior (i.e. the raw range IS now reachable and returns the
expected codepoints).

---

## Item 2: Resolve remaining ruff errors

Run: `venv/bin/ruff check .`

Expected: 14 errors across scripts/. Fix them:
- I001 import order (4 files) — auto-fixable: `venv/bin/ruff check --fix .`
- E701 multi-statement lines in scripts/baseline.py:79-82 — split to one
  statement per line
- E741 ambiguous variable name `l` in kern.py and variable.py — rename to
  `left` or `pair_left` (check usage context)
- B905 zip() without strict= in server.py:273 — add strict=False (the zip
  is intentionally non-strict; document why in a comment if not obvious)
- After auto-fix, hand-fix the remaining 3 and verify: `venv/bin/ruff check .`
  reports zero errors

---

## Item 3: Wrap script imports in mcp-server/server.py for clearer errors

File: mcp-server/server.py lines 21-29

The current eager bare imports fail silently with a hard-to-read stack trace
if a script raises during import. Wrap each import in a try/except:

```python
try:
    from baseline import fit_win_metrics, shift_glyphs, shift_metrics
except ImportError as e:
    print(f"Failed to import baseline: {e}", file=sys.stderr)
    sys.exit(2)
```

Apply the same pattern to all script imports (baseline, build, hint, kern,
metrics, rename, strikes, variable). Keep fontTools and mcp imports outside
the try/except — those are proper installed packages.

---

## Item 4: Parametrize the composite-shift regression test

File: tests/test_integration.py line ~101

The test currently only covers Aacute. Parametrize it across:
["Aacute", "Egrave", "Ccedilla", "Ntilde"]

Use @pytest.mark.parametrize. Ensure the test still passes for all four
glyphs against tests/fixtures/AtkinsonHyperlegibleNext-Regular.ttf.

---

## Item 5: Remove empty docs/.claude/ tree

Run: `rm -rf docs/.claude/`

This is an orphaned directory from a prior skill-creation session that produced
no files. Commit the deletion.

---

## Constraints

- Python 3.14, venv at venv/. Use venv/bin/python for all commands.
- After all changes: `venv/bin/ruff check .` must report zero errors.
- Run full test suite: `venv/bin/pytest` — all tests must pass.
- Run `venv/bin/ruff format .` before committing.
- Prefer new commits over --amend.
- Do not change any public script CLI interfaces or MCP tool signatures.
- Large-file hygiene (Emojitwo font) and the local-config cleanup items
  (settings.local.json, global Claude settings) are out of scope for this run —
  those are personal-machine edits, not version-controlled changes.
