# FontForge User Manual

A Python toolkit for managing, analyzing, renaming, and converting font files.

## Setup

The project is ready to use at `~/fontforge/`. All dependencies are pre-installed in the virtual environment.

```bash
cd ~/fontforge
source venv/bin/activate    # Optional — or use venv/bin/python directly
```

**Dependencies:** fonttools, brotli, zopfli, mcp, ufoLib2, defcon, ufo-extractor (from GitHub — PyPI `extractor` is a squatted unrelated package). Python 3.14.

**External binary:** `ttfautohint` from Homebrew (`brew install ttfautohint`) — used by [scripts/hint.py](../../scripts/hint.py) via subprocess.

---

## Scripts

All scripts are in `~/fontforge/scripts/` and support `--help` for full usage.

### metrics.py — Font Analysis

Inspect any font file for metadata, metrics, glyph coverage, and OpenType features.

**Single font (detailed view):**
```bash
python scripts/metrics.py fonts/Burbank/BurbankText-Bold.ttf
```

Output includes: family/subfamily names, designer, version, weight/width class, glyph count, Unicode coverage by script (Latin, Cyrillic, etc.), ascender/descender/cap height/x-height, variable font axes, and OpenType feature tags.

**Family comparison table:**
```bash
python scripts/metrics.py fonts/Burbank --compare
```

Shows a sortable table with weight, glyph count, Unicode coverage, file size, and variable font status for each font in the family.

**JSON output (for scripting):**
```bash
python scripts/metrics.py fonts/Burbank --json
```

### rename.py — Filename Normalization

Normalizes messy font filenames to the standard `FamilyName-Weight.ext` convention.

**How it works:**
1. Reads the font's internal OpenType name table for canonical family/subfamily names
2. If multiple files would get the same name (collision), falls back to filename parsing
3. Handles patterns like `(Bold) Font Name.ttf`, `Font Name - Bold.ttf`, and `fontname-bold.ttf`

**Always preview first:**
```bash
python scripts/rename.py fonts/Samsung
```

Output shows what *would* be renamed without changing anything.

**Apply renames:**
```bash
python scripts/rename.py fonts/Samsung --apply
```

**Verbose mode** (shows name table details):
```bash
python scripts/rename.py fonts/Samsung --verbose
```

### build.py — Format Conversion

Convert fonts between TTF, OTF, WOFF, and WOFF2 formats with optional Unicode subsetting.

**Convert to WOFF2 (default):**
```bash
python scripts/build.py fonts/Burbank
```

**Convert to a specific format:**
```bash
python scripts/build.py fonts/Burbank --format otf
```

**Subset to Latin characters only:**
```bash
python scripts/build.py fonts/Burbank --subset latin
```

This dramatically reduces file size (typically 80-85% smaller than full TTF) by removing glyphs outside the specified Unicode range.

**Available named subsets:** `latin`, `latin-ext`, `cyrillic`, `greek`, `vietnamese`

**Combine subsets:**
```bash
python scripts/build.py fonts/Burbank --subset "latin+cyrillic"
```

**Custom Unicode ranges:**
```bash
python scripts/build.py fonts/Burbank --subset "U+0041-005A,U+0061-007A"
```

**Custom output directory:**
```bash
python scripts/build.py fonts/Burbank --output-dir ~/web/fonts
```

### kern.py — Kerning & Spacing

Read and write kerning pairs, and adjust advance widths by glyph class.

**Dump all kerning pairs as CSV:**
```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --dump -o pairs.csv
```

Flattens both the legacy `kern` table and modern GPOS `PairPos` lookups (including class-based kerning) into explicit `left,right,value` rows.

**Apply a CSV of kerning pairs to a font:**
```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --apply pairs.csv -o out.ttf
```

Synthesizes a `.fea` snippet and compiles it with `feaLib.builder.addOpenTypeFeatures` — pairs whose glyphs don't exist in the font are skipped with a count.

**Adjust advance widths (spacing):**
```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --spacing "lc:+10,uc:-5"
```

Pattern forms:
- **Preset classes:** `lc`, `uc`, `digits`, `all`
- **Character ranges:** `A-Z`, `0-9`
- **Regex:** `/\\.captab$/` (any glyph matching the regex on its name)
- **Literal list:** `A,B,C`

### variable.py — Variable Fonts

Inspect, instance, build, and decompile variable fonts.

**Show axes and named instances:**
```bash
python scripts/variable.py fonts/Anthropic/AnthropicSansVariable-TextLight.ttf --info
```

**Extract a named instance as a static TTF:**
```bash
python scripts/variable.py path/to/vf.ttf --instance "Bold"
python scripts/variable.py path/to/vf.ttf --instance "wght=700,wdth=100"
```

**Build a VF by interpolating static masters:**
```bash
python scripts/variable.py --from-statics \
  fonts/Anthropic/AnthropicSans-Light.ttf \
  fonts/Anthropic/AnthropicSans.ttf \
  fonts/Anthropic/AnthropicSans-Bold.ttf \
  -o Anthropic-VF.ttf
```

Masters are ordered by `OS/2.usWeightClass`. Incompatible glyphs are skipped with warnings; the build succeeds on the compatible subset. Works best when the masters were designed from a shared source.

**Decompile a compiled TTF back into a UFO source:**
```bash
python scripts/variable.py fonts/Burbank/BurbankText-Regular.ttf --to-ufo
```

Useful for reverse-engineering a vendor TTF into an editable UFO (outlines, advances, kerning, name table). Non-standard legacy `kern` tables are stripped automatically before extraction since GPOS carries the modern kerning.

### hint.py — Auto-Hinting

Add or strip TrueType hinting instructions via `ttfautohint`.

**Auto-hint a single font:**
```bash
python scripts/hint.py fonts/Burbank/BurbankText-Regular.ttf -o fonts/Burbank/hinted
```

**Auto-hint an entire family with strong stems (recommended for web):**
```bash
python scripts/hint.py fonts/Burbank/ -o fonts/Burbank/hinted --strong
```

**Custom PPEM range and fallback script:**
```bash
python scripts/hint.py fonts/Cyrillic/ --range 6-72 --script cyrl
```

Defaults: `--range 8-50 --script latn`. Hinting typically adds 40–60% to file size (all instruction tables) — this is recovered by WOFF2 compression downstream.

**Strip existing hints:**
```bash
python scripts/hint.py fonts/Burbank/ --dehint
```

Removes `prep`, `fpgm`, `cvt `, `hdmx`, `LTSH`, `VDMX` tables plus per-glyph instruction programs. Useful before re-hinting with different settings, or for debugging rendering issues attributable to bad hints.

### batch.py — Multi-Family Operations

Run any operation across all (or selected) font families.

**Summary report:**
```bash
python scripts/batch.py fonts/
```

Shows family name, font count, glyph count, formats, and total size for every family.

**Filter to specific families:**
```bash
python scripts/batch.py fonts/ --families Burbank,GGSans,Anthropic
```

**Batch rename (preview):**
```bash
python scripts/batch.py fonts/ --rename
```

**Batch rename (apply):**
```bash
python scripts/batch.py fonts/ --rename --apply
```

**Batch convert to WOFF2:**
```bash
python scripts/batch.py fonts/ --build --format woff2
```

**Batch metrics with per-family comparison:**
```bash
python scripts/batch.py fonts/ --metrics --compare
```

**Chain operations (rename then convert):**
```bash
python scripts/batch.py fonts/ --rename --build --apply
```

---

## MCP Server

The MCP server at `mcp-server/server.py` exposes font operations as tools for Claude Code and other MCP clients.

### Configuration

Add to your Claude Code MCP settings (`.claude/settings.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "fontforge": {
      "command": "/Users/visualval/fontforge/venv/bin/python",
      "args": ["/Users/visualval/fontforge/mcp-server/server.py"],
      "env": {}
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list_families` | List all font families with optional detail (formats, sizes) |
| `get_metrics` | Detailed metrics for a family or specific font file |
| `rename_fonts` | Preview or apply filename normalization |
| `build_fonts` | Convert fonts to target format with optional subsetting |
| `search_fonts` | Search fonts by name, weight, or designer |
| `dump_kerning` | Extract kerning pairs from a font (GPOS + legacy kern, flattened) |
| `adjust_spacing` | Apply advance-width rules across a family by glyph class |
| `hint_family` | Auto-hint (or dehint) all TTFs in a family via ttfautohint |
| `variable_info` | Report axes and named instances of a variable font |
| `build_variable` | Interpolate a family's static masters into a variable font |

### Example MCP Usage

Once configured, Claude Code can call these tools directly:

- "List all my font families" → calls `list_families`
- "What metrics does Burbank Bold have?" → calls `get_metrics(family="Burbank", font_file="BurbankText-Bold.ttf")`
- "Convert all Burbank fonts to WOFF2" → calls `build_fonts(family="Burbank", target_format="woff2")`
- "Find all bold fonts" → calls `search_fonts(query="bold")`

---

## Claude Code Skill

The `fontforge` skill is installed at `~/.claude/skills/fontforge/SKILL.md`. It automatically activates when you work with font files in Claude Code, providing guided workflows for common font tasks.

**Trigger phrases:** Any mention of font files, font metrics, font conversion, WOFF2, font renaming, or font management.

---

## Font Library

Fonts are organized by family in `~/fontforge/fonts/`:

```
fonts/
├── Anthropic/       # AnthropicSans, AnthropicSerif
├── Burbank/         # BurbankText (8 weights)
├── Circular/        # CircularXXWeb (WOFF2)
├── GGSans/          # Discord's GG Sans
├── OpenAISans/      # OpenAI Sans
├── ...              # 29 families total
```

**Supported formats:** TTF, OTF, WOFF, WOFF2, TTC (TrueType Collection)

### Adding New Fonts

1. Create a directory under `fonts/` named after the family
2. Place font files in the directory
3. Run `python scripts/rename.py fonts/NewFamily` to preview normalization
4. Run `python scripts/metrics.py fonts/NewFamily --compare` to verify

---

## Pipeline Example: Ship a Family to Web

The canonical "hint → compress → subset" order applied to Burbank:

```bash
# 1. Snapshot the vendor kerning (for future editing)
for f in fonts/Burbank/BurbankText-*.ttf; do
  python scripts/kern.py "$f" --dump -o "fonts/Burbank/kerning/$(basename "$f" .ttf).csv"
done

# 2. Auto-hint all 8 statics with strong stems for Windows rendering
python scripts/hint.py fonts/Burbank/ -o fonts/Burbank/hinted --strong

# 3. Build latin+latin-ext WOFF2s from the hinted sources
python scripts/build.py fonts/Burbank/hinted/ \
  --format woff2 --subset "latin+latin-ext" \
  --output-dir fonts/Burbank/web
```

Result: 8 WOFF2 files at ~29–31KB each (~248KB for the whole family, ~81% smaller than the hinted TTFs).

---

## Tips

- **Always dry-run renames** before applying — some fonts have surprising internal names
- **WOFF2 is the web standard** — use `build.py --format woff2` for web deployment
- **Subsetting saves bandwidth** — a Latin-only WOFF2 is typically 85% smaller than the full TTF
- **Hint before compressing** — WOFF2's Brotli gets better ratios on hinted output than subset-then-hint
- **TTC files** contain multiple fonts bundled together — metrics.py reads the first font
- **Duplicate files** (like OneUI having both `(Bold)` and `- Bold` variants) are detected as conflicts during rename

### Known Gotchas

- **Non-standard legacy `kern` tables** (Burbank and other older vendor fonts) parse as `KernTable_format_unkown` with no `kernTable`/`version` attrs. `kern.py` and `variable.py --to-ufo` handle this defensively — GPOS still carries the modern kerning so nothing real is lost.
- **`morx` table is dropped on subset** — Apple-only legacy layout table; fontTools doesn't know how to subset it and emits a warning. Harmless for web output.
- **`ufo-extractor` PyPI name is squatted** by an unrelated keyword-extraction package. The real typesupply/extractor must be installed from GitHub (see `requirements.txt`).
