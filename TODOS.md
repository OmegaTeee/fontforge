# TODOs

All items from the [2026-04-18 code review](docs/reviews/2026-04-18-code-review.md) are resolved as of 2026-04-20.

## Pending — MCP server hardening (added 2026-05-12)

The MCP server is becoming the primary interface to the toolkit (fonts now live at `~/code/fonts`, accessed via `$FONTFORGE_FONTS_DIR`). That shifts the threat and reliability model from "local script" toward "long-running service." Items below are roughly ordered by priority for productive MCP development.

### Critical

- [x] **⚠️ Path-traversal protection in `_family_dir(family)`** — RESOLVED 2026-06-19. Implemented path validation using `Path.relative_to()` to ensure all family paths stay within `DEFAULT_FONTS_DIR`. Rejects escape attempts like `"../../etc"` and absolute paths. All path-traversal test cases pass.

- [x] **⚠️ Validate `DEFAULT_FONTS_DIR` at startup, not at first tool call** — RESOLVED 2026-06-19. Added startup validation in `main()` that checks if the fonts directory exists and is a directory, exiting with clear error message if not.

### Important

- [x] **💡 Add direct tests for MCP server tools** — RESOLVED 2026-06-22. Added `tests/test_mcp_server.py` with direct coverage for `list_families`, `get_metrics`, `_family_dir` path-traversal rejection, and MCP log creation against a fixture-backed temporary fonts directory.

- [x] **💡 Structured request/error logging** — RESOLVED 2026-06-22. Added rotating MCP tool-call logging to `~/.cache/fontforge/mcp.log` or `$XDG_CACHE_HOME/fontforge/mcp.log`, recording tool name, truncated arguments, elapsed time, and exception details.

- [x] **💡 GitHub Actions CI: pytest + ruff on push** — RESOLVED 2026-06-22. Added `.github/workflows/ci.yml` for push and pull request checks on Ubuntu with Python 3.14, `ttfautohint`, `ruff check .`, and unit pytest.

- [x] **💡 Auto-debugpy launch config for MCP server attach** — RESOLVED 2026-06-22. Added `.vscode/tasks.json` with an `MCP Server — debugpy wait` task and wired it into the existing attach launch config.

### Tightening

- [x] **💡 Resolve remaining ruff errors in `scripts/`** — RESOLVED 2026-06-19. Fixed:
  - `mcp-server/server.py:303`: E741 ambiguous variable `l` → renamed to `left`, `right`, `value`
  - `scripts/baseline.py:79-82`: E701 multi-statement lines → split to separate lines
  - `scripts/kern.py:170`: E741 ambiguous variable `l` → renamed to `left`, `right`, `value`
  All targeted ruff checks now pass.

- [x] **💡 Fix raw-Unicode subset arg unreachability** — RESOLVED 2026-06-22. `load_subset_codepoints()` now checks raw `U+...` ranges before named-range combinations, and `tests/test_build.py::TestLoadSubsetCodepoints::test_raw_unicode_range_is_reachable` asserts the corrected behavior.

- [x] **💡 Large-file hygiene** — RESOLVED 2026-06-22. The large Emojitwo font is no longer present in the repository, and the local `fonts` symlink has been removed from Git tracking while `fonts` remains ignored for local development.

- [x] **💡 Parametrize the composite-shift regression test** — RESOLVED 2026-06-22. The regression now covers `["Aacute", "Egrave", "Cacute", "Ntilde"]`; `Cacute` is used because `Ccedilla` is a simple outline in the Atkinson fixture.

- [x] **💡 Wrap script imports in `mcp-server/server.py` for clearer errors** — RESOLVED 2026-06-22. Script imports now fail fast with `Failed to import <script>: <error>` and exit code 2.

## Pending — local config cleanup (added 2026-05-12 from /hygiene)

Audit findings deferred from the 2026-05-12 hygiene pass (Group A — HIGH — was applied; these MEDIUM/LOW items remain). All touch local-only files (`.claude/settings.local.json` is gitignored), so fixes are personal-machine edits rather than version-controlled changes.

### Medium

- [x] **💡 Broaden pinned Homebrew Python path** — RESOLVED 2026-06-22. The stale version-pinned global Claude permission was removed; `Read(//opt/homebrew/Cellar/python@3.14/**)` remains.

### Low

- [x] **💡 Consolidate redundant bash permissions** — RESOLVED 2026-06-22. The previously listed project-local `.claude/settings.local.json` entries are not present in the current repo or global local settings:
  - `Bash(/Users/visualval/fontforge/venv/bin/python --version)` — specific single command
  - `Bash(/Users/visualval/fontforge/venv/bin/python -m json.tool:*)` — specific subcommand
  - `Bash(venv/bin/python mcp-server/*:*)` — narrower than `venv/bin/python *`
  - `Bash(/Users/visualval/fontforge/venv/bin/python -c "import json; d=json.load(open('/Users/visualval/.claude.json'))...")` — 198-char one-off command
  - Plus the absolute-vs-relative duplicate pair: `Bash(/Users/visualval/fontforge/venv/bin/python *)` and `Bash(venv/bin/python *)` — keep one.
  Fix: collapse to just `Bash(venv/bin/python *)` + `Bash(python3 *)`. Cost: 5 entries to remove.

- [x] **💡 Remove empty `docs/.claude/` tree** — RESOLVED 2026-06-22. `docs/.claude/` is absent.

- [x] **💡 Drop duplicate `/private/tmp` from global additionalDirectories** — RESOLVED 2026-06-22. Removed `/private/tmp` from `~/.claude/settings.json`; `/tmp` remains.

- [x] **💡 Review global `mcp__fetch__fetch` permission** — RESOLVED 2026-06-22. The permission is not present in current `~/.claude/settings.json`, so there is nothing to remove.

## Resolved

- [x] ~~**⚠️ Fix stale composite bounds in `scripts/baseline.py:78–85`**~~ — fixed 2026-04-18. `fit_win_metrics` now calls `Glyph.recalcBounds(glyf, boundsDone=…)` on every glyph before reading the bbox; the shared `bounds_done` set memoizes across the composite graph. Verified on FKGrotesk-Regular, whose `nine` is a transform-flipped `six` — `recalcBounds` falls back to `getCoordinates` for non-integer-translate components, so scaled and flipped composites are handled. Also deleted the now-redundant `_recompute_bounds` helper; `shift_glyphs` uses `recalcBounds` directly.
- [x] ~~**💡 Warn on `--shift … --no-fit-win`**~~ — resolved 2026-04-20. `main()` in `scripts/baseline.py` now prints a stderr warning when a nonzero shift is combined with `--no-fit-win`, naming the Windows-GDI clipping risk explicitly.
- [x] ~~**💡 Make `--fit-win-metrics` / `--no-fit-win` mutually exclusive**~~ — resolved 2026-04-20. Both flags now live in an `argparse.add_mutually_exclusive_group()`; passing both yields a clean argparse error instead of silently preferring the explicit-on.
- [x] ~~**💡 Drop the `_resolve_fonts_dir` pass-through**~~ — resolved 2026-04-20. The wrapper is gone; the three call sites (`_family_dir`, `list_families`, `search_fonts`) read `DEFAULT_FONTS_DIR` directly. `main` still mutates the global when `--fonts-dir` is supplied, which is fine because the mutation happens before `mcp.run()` and all tool invocations read the post-mutation value.
- [x] ~~**💡 Document re-hint requirement in `CLAUDE.md`**~~ — resolved 2026-04-20. Pipeline-order section now warns that re-shifting an already-hinted family requires deleting `fonts/<Family>/hinted/` and `fonts/<Family>/web/` and rerunning from step 2.
