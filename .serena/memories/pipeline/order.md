# Font Processing Pipeline

**Rigid sequence for web preparation:**

1. **Baseline / spacing adjustments** (`baseline.py`, optional `kern.py --spacing`)
   - Shifts glyphs vertically, adjusts all three metric sets (hhea, OS/2 typo, OS/2 win)
   - Composite glyphs inherit shifts through base glyphs automatically
   - Output: `fonts/<Family>/shifted/`

2. **Hinting** (`hint.py`)
   - Computes hinting instructions for current glyph coordinates
   - MUST run AFTER baseline shifts (instructions are coordinate-sensitive)
   - Output: `fonts/<Family>/hinted/`

3. **Subsetting + format conversion** (`build.py --format woff2 --subset …`)
   - Strips non-subsettable tables (morx, mort, feat, FFTM, non-standard kern)
   - Converts to WOFF2
   - Runs last because subsetting destroys some tables
   - Output: `fonts/<Family>/web/`

## Re-shipping a shifted family
If you re-shift an already-hinted family:
1. Delete `fonts/<Family>/hinted/` and `fonts/<Family>/web/`
2. Rerun from step 2 (hinting) with new shifted source
3. Old artifacts were hinted against pre-shift coordinates; leaving them ships mismatched hinting

## Metric invariants
- `baseline.py` keeps hhea, OS/2 typo, OS/2 win synchronized on any shift
- Refits win metrics to glyph bbox to prevent Windows GDI clipping
