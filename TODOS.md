# TODOs

All items from the [2026-04-18 code review](docs/reviews/2026-04-18-code-review.md) are resolved as of 2026-04-20.

## Resolved

- [x] ~~**⚠️ Fix stale composite bounds in `scripts/baseline.py:78–85`**~~ — fixed 2026-04-18. `fit_win_metrics` now calls `Glyph.recalcBounds(glyf, boundsDone=…)` on every glyph before reading the bbox; the shared `bounds_done` set memoizes across the composite graph. Verified on FKGrotesk-Regular, whose `nine` is a transform-flipped `six` — `recalcBounds` falls back to `getCoordinates` for non-integer-translate components, so scaled and flipped composites are handled. Also deleted the now-redundant `_recompute_bounds` helper; `shift_glyphs` uses `recalcBounds` directly.
- [x] ~~**💡 Warn on `--shift … --no-fit-win`**~~ — resolved 2026-04-20. `main()` in `scripts/baseline.py` now prints a stderr warning when a nonzero shift is combined with `--no-fit-win`, naming the Windows-GDI clipping risk explicitly.
- [x] ~~**💡 Make `--fit-win-metrics` / `--no-fit-win` mutually exclusive**~~ — resolved 2026-04-20. Both flags now live in an `argparse.add_mutually_exclusive_group()`; passing both yields a clean argparse error instead of silently preferring the explicit-on.
- [x] ~~**💡 Drop the `_resolve_fonts_dir` pass-through**~~ — resolved 2026-04-20. The wrapper is gone; the three call sites (`_family_dir`, `list_families`, `search_fonts`) read `DEFAULT_FONTS_DIR` directly. `main` still mutates the global when `--fonts-dir` is supplied, which is fine because the mutation happens before `mcp.run()` and all tool invocations read the post-mutation value.
- [x] ~~**💡 Document re-hint requirement in `CLAUDE.md`**~~ — resolved 2026-04-20. Pipeline-order section now warns that re-shifting an already-hinted family requires deleting `fonts/<Family>/hinted/` and `fonts/<Family>/web/` and rerunning from step 2.
