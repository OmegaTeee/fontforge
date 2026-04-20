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

### `scripts/baseline.py:156–157, 175` — `--no-fit-win` leaves win metrics stale after a shift

If the user passes `--shift -40 --no-fit-win`, outlines move down 40u but `usWinDescent` stays at its original magnitude. On Windows GDI the font will now clip descenders that just moved below the old clip region. Unusual flag combo, but the current code silently produces a subtly broken font. Either warn, or document in `--no-fit-win` help that it's meant for no-shift workflows only.

### `scripts/baseline.py:175` — conflicting flag resolution

```python
do_fit_win = args.fit_win_metrics or (args.shift != 0 and not args.no_fit_win)
```

If the user passes both `--fit-win-metrics` and `--no-fit-win`, the explicit-on wins silently. `argparse.add_mutually_exclusive_group()` would error cleanly. Low-priority nit.

### `mcp-server/server.py:42–44, 501–503` — `_resolve_fonts_dir` is a pass-through

`_resolve_fonts_dir` just returns `DEFAULT_FONTS_DIR`, and `main` mutates that global. Drop the wrapper and read the global directly (four call sites, all in this file), or hold the path on the `FastMCP` instance / a small `Config` dataclass so the global mutation disappears. Not blocking.

### `CLAUDE.md:19–24` — pipeline-order claim

The doc says shift/spacing must happen before hinting. True and worth preserving. But the second commit's snapshot (`fonts/Burbank/hinted/BurbankText-*-shifted-hinted.ttf`) only works because you *did* re-hint after shifting. If a future maintainer shifts without re-hinting, the existing `-hinted` artifacts silently become wrong. Consider adding one sentence: "If you re-shift an already-hinted family, delete `hinted/` and `web/` and re-run the pipeline from step 2."

---

## Notes on the inline-docs pass (`c1b0b16`)

The annotations added in `kern.py` (flattening format-2 class matrices), `variable.py` (`(3, 1, 0x409)` = Windows/Unicode/en-US), and `hint.py` (DGW expansion) are the good kind — they encode *why* and *what the magic number means*. The `.notdef_outline` comment in `build.py:100–102` is particularly well-placed since the consequence ("zero-width blank vs. visible box") is exactly what a future reader needs to decide whether to change it.

One exception: `kern.py:26` references `resolve_glyphs` — the expansion actually happens inside `resolve_glyphs` at `kern.py:225+`. Fine today, just verify after any future refactor.
