# Code Review — 2026-04-18

**Scope:** commits `5371a20..09dbb9d` (baseline.py, MCP server, inline-docs pass, CLAUDE.md).

**Reviewer:** Claude (code-review skill).

## Summary

Solid changeset. One real bug-shaped concern (stale composite bounds in `fit_win_metrics`), two nits (`--no-fit-win` interaction, flag conflict), plus praise for the composite double-shift defense and the library/CLI layering.

---

## Praise

### `scripts/baseline.py:25–42` — composite double-shift defense

The `shift_glyphs` loop walks only `numberOfContours > 0` glyphs, which simultaneously skips empty glyphs (0) and composites (-1). The docstring explicitly names the regression — `Aacute ending up at -80u when we asked for -40u` — so future maintainers immediately see why the obvious "also touch `component.y`" fix is wrong. Exactly the kind of WHY-is-non-obvious comment CLAUDE.md endorses.

### `scripts/baseline.py:55–94` — single-purpose `shift_metrics` / `fit_win_metrics`

Keeping these as two small functions (instead of one `apply_vertical_shift`) lets `shift_baseline` in the MCP server and `process_font` in the CLI compose them differently. Worth it.

### `mcp-server/server.py:466–467` — shallow-only TTF collection

```python
ttfs = [f for f in collect_ttfs(family_path) if f.parent == family_path]
```

Correctly excludes previously-shifted/hinted derivatives. Without this, running `shift_baseline` twice would re-shift `shifted/*.ttf`. Matches the pipeline ordering rule in CLAUDE.md.

---

## Warning

### ✅ `scripts/baseline.py:78–85` — stale composite bounds in `fit_win_metrics` (**resolved 2026-04-18**)

Fixed by calling `Glyph.recalcBounds(glyf, boundsDone=…)` on every glyph before reading the bbox; `recalcBounds` handles simples, translate-only composites (via `tryRecalcBoundsComposite`), and scaled/flipped composites (via the `getCoordinates` fallback) uniformly. The helper `_recompute_bounds` was deleted; `shift_glyphs` now uses `recalcBounds` directly. Verified against FKGrotesk-Regular (whose `nine` is a transform-flipped `six`): composite bounds in memory now match what fontTools would emit at save time, so OS/2 win metrics cover the true rendered bbox.

**Original finding (for reference):**


After `shift_glyphs` runs, simple-glyph bounds are recomputed by `_recompute_bounds`, but **composite bounds in memory are stale** — the `xMin/yMin/xMax/yMax` attributes on composite `Glyph` objects still hold the pre-shift values read from the file. fontTools recomputes them at `font.save()` compile time, not when the base glyphs' coordinates mutate. The current loop reads those attributes directly.

**In practice this is usually harmless** because composites without scale transforms can't exceed their base glyphs' extents, and the font-wide `min()` / `max()` will pick the extreme from a simple anyway. But a composite with a scale transform (rare in text faces, common in icon / symbol fonts) could have a legitimately larger extent than any single base, and its stored bbox won't reflect the shift.

Two cheap fixes:

```python
# Option A — skip composites entirely; their bounds are always derived
# from bases we already processed (fails for scale-transformed composites)
if g.numberOfContours <= 0:
    continue

# Option B — force fontTools to recompute composite bounds first
glyf.compile(font)  # triggers recalcBounds on composites
```

Option B is safer. Either way, add a comment — "why is this correct for composites?" is a reasonable reviewer question.

---

## Suggestions

### ✅ `scripts/baseline.py:156–157, 175` — `--no-fit-win` leaves win metrics stale after a shift (**resolved 2026-04-20**)

`main()` now prints a stderr warning when `args.shift != 0 and args.no_fit_win`, explicitly naming the Windows-GDI clipping risk. The combo still runs (no hard-fail) because there are legitimate scripted pipelines that shift and refit elsewhere.

### ✅ `scripts/baseline.py:175` — conflicting flag resolution (**resolved 2026-04-20**)

`--fit-win-metrics` and `--no-fit-win` are now grouped via `argparse.add_mutually_exclusive_group()` — passing both yields a clean argparse error instead of silently preferring the explicit-on. Verified by CLI smoke test.

### ✅ `mcp-server/server.py:42–44, 501–503` — `_resolve_fonts_dir` is a pass-through (**resolved 2026-04-20**)

Wrapper removed. The three call sites (`_family_dir`, `list_families`, `search_fonts`) now read `DEFAULT_FONTS_DIR` directly. `main` still mutates the global when `--fonts-dir` is passed; since that mutation happens before `mcp.run()`, all subsequent tool invocations see the updated value. A `FastMCP`-bound config would be cleaner still, but that's a structural change out of scope for this pass.

### ✅ `CLAUDE.md:19–24` — pipeline-order claim (**resolved 2026-04-20**)

Added a paragraph after the pipeline-order list: re-shifting an already-hinted family requires deleting `fonts/<Family>/hinted/` and `fonts/<Family>/web/` and rerunning from step 2, so stale hinting doesn't silently ship against new outlines.

---

## Notes on the inline-docs pass (`c1b0b16`)

The annotations added in `kern.py` (flattening format-2 class matrices), `variable.py` (`(3, 1, 0x409)` = Windows/Unicode/en-US), and `hint.py` (DGW expansion) are the good kind — they encode *why* and *what the magic number means*. The `.notdef_outline` comment in `build.py:100–102` is particularly well-placed since the consequence ("zero-width blank vs. visible box") is exactly what a future reader needs to decide whether to change it.

One exception: `kern.py:26` references `resolve_glyphs` — the expansion actually happens inside `resolve_glyphs` at `kern.py:225+`. Fine today, just verify after any future refactor.
