# FontForge User Manual

A Python toolkit for managing, analyzing, renaming, and converting font files.

## Setup

The project is ready to use at `~/fontforge/`. All dependencies are pre-installed in the virtual environment.

```bash
cd ~/fontforge
source venv/bin/activate    # Optional — or use venv/bin/python directly
```

**Dependencies:** fonttools 4.62, brotli, zopfli, mcp 1.26 (Python 3.14)

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

## Tips

- **Always dry-run renames** before applying — some fonts have surprising internal names
- **WOFF2 is the web standard** — use `build.py --format woff2` for web deployment
- **Subsetting saves bandwidth** — a Latin-only WOFF2 is typically 85% smaller than the full TTF
- **TTC files** contain multiple fonts bundled together — metrics.py reads the first font
- **Duplicate files** (like OneUI having both `(Bold)` and `- Bold` variants) are detected as conflicts during rename
