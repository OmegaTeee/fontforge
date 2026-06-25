# Known Gotchas & Edge Cases

## Baseline shifts and hinting
**CRITICAL**: Hinting instructions are computed for specific glyph coordinates.
- If you shift a family AFTER hinting, the hinting no longer matches the outlines
- **Fix**: Delete `fonts/<Family>/hinted/` and `fonts/<Family>/web/`, then rerun hinting from step 2

## Composite glyphs inherit baseline shifts
Composite glyphs (glyphs made from other glyphs) automatically inherit vertical shifts through their base glyphs.
- `baseline.shift_glyphs()` deliberately only iterates simple glyphs; don't add `component.y += shift` (regression previously caught in AnthropicSans)

## Non-standard legacy kern tables
Older vendor fonts (Burbank and others) have non-standard kern tables that fontTools parses as `KernTable_format_unknown`.
- `kern.has_nonstandard_kern()` detects them
- `kern.strip_nonstandard_kern()` removes them
- GPOS carries modern kerning, so stripping non-standard kern loses nothing real

## Subsettable tables only
`build.convert_font()` drops these before subsetting (fontTools can't handle them):
- `morx`, `mort`, `feat` (Apple-only layout tables)
- `FFTM` (FontForge-internal build artifact)
- Harmless for web; all essential info preserved

## Windows GDI clipping
GDI clips glyphs if win metrics extend beyond the actual glyph bounding box.
- `baseline.py` refits win metrics to glyph bbox on any shift
- Keep all three metric sets (hhea, OS/2 typo, OS/2 win) synchronized

## Three vertical metric sets
Fonts carry three separate vertical metric definitions:
- `hhea` table metrics
- `OS/2` typo metrics
- `OS/2` win metrics (Windows GDI)
- `baseline.py` keeps all three consistent; don't edit them independently
