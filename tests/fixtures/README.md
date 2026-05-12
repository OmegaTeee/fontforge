# Test fixtures

Static font fixtures used by integration tests. Kept here (not in the
project's `fonts/` directory) so the test suite stays self-contained even
if `fonts/` is moved out of the workspace.

## Files

### AtkinsonHyperlegibleNext-Regular.ttf

Single TTF used as the canonical test font.

- **License:** SIL Open Font License 1.1 (see `OFL.txt`)
- **Source:** https://github.com/googlefonts/atkinson-hyperlegible-next
- **Size:** ~64 KB · 392 glyphs

**Why this font:** it exercises nearly every code path in `scripts/` with
a single fixture:

| Code path | Feature in the font |
|-----------|---------------------|
| `metrics.extract_metrics`     | Full `OS/2`, `hhea`, `name` tables |
| `baseline.shift_glyphs`       | Simple `glyf` contours |
| **Composite-shift regression** | **174 composite glyphs** (Aacute, Egrave, …) — would catch the AnthropicSans double-shift bug noted in CLAUDE.md |
| `kern.extract_kerning`        | Modern GPOS kerning (no legacy `kern` table) |
| `kern.has_nonstandard_kern`   | Negative test: returns `False` for this font |
| `rename.get_font_names`       | Standard name table with IDs 1, 2, 4, 16, 17 |
| `build.convert_font`          | Subsettable; converts cleanly to WOFF2 |

### OFL.txt

The SIL Open Font License terms. Required to be distributed alongside
any redistribution of the font (which includes checking it into this
repo).
