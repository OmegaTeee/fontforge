# TODOs

## Open

From [2026-04-18 code review](docs/reviews/2026-04-18-code-review.md):

- [x] ~~**⚠️ Fix stale composite bounds in `scripts/baseline.py:78–85`**~~ — fixed 2026-04-18. `fit_win_metrics` now calls `Glyph.recalcBounds(glyf, boundsDone=…)` on every glyph before reading the bbox; the shared `bounds_done` set memoizes across the composite graph. Verified on FKGrotesk-Regular, whose `nine` is a transform-flipped `six` — `recalcBounds` falls back to `getCoordinates` for non-integer-translate components, so scaled and flipped composites are handled. Also deleted the now-redundant `_recompute_bounds` helper; `shift_glyphs` uses `recalcBounds` directly.
- [ ] **💡 Warn or hard-fail on `--shift … --no-fit-win`** (`scripts/baseline.py:156–157, 175`) — this combo silently produces a font whose win metrics no longer cover the shifted outlines, clipping descenders on Windows GDI.
- [ ] **💡 Make `--fit-win-metrics` / `--no-fit-win` mutually exclusive** via `argparse.add_mutually_exclusive_group()` (`scripts/baseline.py:175`) so conflicting flags error instead of silently preferring the explicit-on.
- [ ] **💡 Drop the `_resolve_fonts_dir` pass-through** in `mcp-server/server.py:42–44` or move the fonts-dir into a config object — the current setup mutates a module global from `main`.
- [ ] **💡 Document re-hint requirement in `CLAUDE.md:19–24`** — add a note that re-shifting an already-hinted family requires deleting `hinted/` and `web/` and rerunning from step 2 of the pipeline.
