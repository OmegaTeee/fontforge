# TODOs

All items from the [2026-04-18 code review](docs/reviews/2026-04-18-code-review.md) are resolved as of 2026-04-20.

## Pending — MCP server hardening (added 2026-05-12)

The MCP server is becoming the primary interface to the toolkit (fonts now live at `~/code/fonts`, accessed via `$FONTFORGE_FONTS_DIR`). That shifts the threat and reliability model from "local script" toward "long-running service." Items below are roughly ordered by priority for productive MCP development.

### Critical

- [ ] **⚠️ Path-traversal protection in `_family_dir(family)`** — `mcp-server/server.py:42` does `fonts_dir / family` with no validation. A family name like `"../../etc"` or an absolute path would escape `DEFAULT_FONTS_DIR`. Family names flow in from MCP clients, so treat them as untrusted input. Fix: resolve the candidate path and assert `resolved.is_relative_to(DEFAULT_FONTS_DIR.resolve())` before returning; reject otherwise. Cost: ~10 lines + one test.

- [ ] **⚠️ Validate `DEFAULT_FONTS_DIR` at startup, not at first tool call** — `mcp-server/server.py:35-40` accepts whatever path the env var or flag specifies. If it points to a file, a non-existent path, or an unreadable directory, the failure only surfaces when a client invokes `list_families` and gets a cryptic traceback. Fix: in `main()`, after precedence resolution, raise a clear error if the path doesn't exist or isn't a directory. Cost: ~5 lines.

### Important

- [ ] **💡 Add direct tests for MCP server tools** — `tests/` covers `scripts/` thoroughly (94 tests) but the MCP bridging layer (`mcp-server/server.py`) has zero direct test coverage. The tool functions can be invoked directly without spinning up stdio. Suggested first batch: `list_families`, `get_metrics`, `_family_dir` (path-traversal cases). Cost: ~1 hour for a useful initial suite.

- [ ] **💡 Structured request/error logging** — `mcp-server/server.py` has no request logging, so when a client (Claude Code, etc.) hits an unexpected response, there's no trail to inspect. Add a minimal logging setup that records: tool name, arguments (truncated), elapsed ms, and any exception. Should write to a file under `~/.cache/fontforge/` or wherever `XDG_CACHE_HOME` points. Makes the "MCP Server attach" launch config much more useful in practice. Cost: ~30 lines.

- [ ] **💡 GitHub Actions CI: pytest + ruff on push** — 94 tests are easy to forget to run before pushing. Add `.github/workflows/ci.yml` that sets up Python 3.14 + venv + runs `pytest` and `ruff check`. Free for private repos at our usage volume. Cost: one workflow file (~30 lines).

- [ ] **💡 Auto-debugpy launch config for MCP server attach** — `.vscode/launch.json:240` documents a one-line command to wrap the server in `debugpy --listen 5678 --wait-for-client`, but it's manual friction. Add a `"preLaunchTask"` in `.vscode/tasks.json` that runs that command, and the "MCP Server — attach" config becomes one-click. Cost: ~15 lines across two files.

### Tightening

- [ ] **💡 Fix raw-Unicode subset arg unreachability** — `scripts/build.py:56` checks `"+" in subset_arg` before `"U+" in subset_arg.upper()` (line 66), so any `U+...` raw range is eaten by the named-range combiner. Currently documented in `tests/test_build.py::TestLoadSubsetCodepoints::test_raw_unicode_range_is_unreachable`. Fix: reorder the conditionals to check for `U+` prefix first. The test will need updating to assert the corrected behavior. Cost: 2 lines + test update.

- [ ] **💡 Resolve remaining ruff errors in `scripts/`** — `ruff check .` reports 14 errors in `scripts/`: I001 import order (4 files), E701 multi-statement lines (`scripts/baseline.py:79-82`), E741 ambiguous variable `l` (kern.py, variable.py), B905 `zip()` without `strict=` (server.py:273). 11 are auto-fixable. CLAUDE.md notes the scripts were originally downloaded, not user code — but if MCP server is becoming primary, code health matters more. Cost: `ruff check --fix` for the auto-fixable; ~10 lines of hand work for the rest.

- [ ] **💡 Large-file hygiene** — `fonts/Emojitwo/assets/fonts/emojione-apple.ttf` is 59 MB; GitHub warned on push that it exceeds the 50 MB recommended ceiling. Options: enable Git LFS for `*.ttf` larger than 25 MB, gitignore Emojitwo specifically, or remove the font. With fonts moving to `~/code/fonts` anyway this may resolve itself, but worth a decision before more big fonts land in `tests/fixtures/`.

- [ ] **💡 Parametrize the composite-shift regression test** — `tests/test_integration.py:101` tests only `Aacute`. The fixture has 174 composite glyphs; parametrizing across a handful (e.g. `["Aacute", "Egrave", "Ccedilla", "Ntilde"]`) would catch shift-bug variants that only manifest on specific transform combinations. Cost: ~5 lines.

- [ ] **💡 Wrap script imports in `mcp-server/server.py` for clearer errors** — `mcp-server/server.py:21-29` does eager bare imports of every script at module load. If one script raises during import (missing optional dep, syntax error after an edit), the server fails to start with a stack trace that doesn't name the entry-point intent. Wrapping in `try/except ImportError` with a `print("Failed to import {script}: {e}", file=sys.stderr); sys.exit(2)` would surface configuration problems faster. Cost: ~10 lines.

## Resolved

- [x] ~~**⚠️ Fix stale composite bounds in `scripts/baseline.py:78–85`**~~ — fixed 2026-04-18. `fit_win_metrics` now calls `Glyph.recalcBounds(glyf, boundsDone=…)` on every glyph before reading the bbox; the shared `bounds_done` set memoizes across the composite graph. Verified on FKGrotesk-Regular, whose `nine` is a transform-flipped `six` — `recalcBounds` falls back to `getCoordinates` for non-integer-translate components, so scaled and flipped composites are handled. Also deleted the now-redundant `_recompute_bounds` helper; `shift_glyphs` uses `recalcBounds` directly.
- [x] ~~**💡 Warn on `--shift … --no-fit-win`**~~ — resolved 2026-04-20. `main()` in `scripts/baseline.py` now prints a stderr warning when a nonzero shift is combined with `--no-fit-win`, naming the Windows-GDI clipping risk explicitly.
- [x] ~~**💡 Make `--fit-win-metrics` / `--no-fit-win` mutually exclusive**~~ — resolved 2026-04-20. Both flags now live in an `argparse.add_mutually_exclusive_group()`; passing both yields a clean argparse error instead of silently preferring the explicit-on.
- [x] ~~**💡 Drop the `_resolve_fonts_dir` pass-through**~~ — resolved 2026-04-20. The wrapper is gone; the three call sites (`_family_dir`, `list_families`, `search_fonts`) read `DEFAULT_FONTS_DIR` directly. `main` still mutates the global when `--fonts-dir` is supplied, which is fine because the mutation happens before `mcp.run()` and all tool invocations read the post-mutation value.
- [x] ~~**💡 Document re-hint requirement in `CLAUDE.md`**~~ — resolved 2026-04-20. Pipeline-order section now warns that re-shifting an already-hinted family requires deleting `fonts/<Family>/hinted/` and `fonts/<Family>/web/` and rerunning from step 2.
