# FontForge Project Consolidation — Design Spec

**Date:** 2026-03-22
**Status:** Approved

## Overview

Consolidate all font development work into a single `~/fontforge/` monorepo containing fonts, Python scripts, an MCP server, and a Claude Code skill. Eliminate scattered font files across `~/Documents/FontForge/`, `~/Desktop/woff2/`, and `~/Downloads/`.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Directory structure | By family | Mirrors mental model of font projects |
| MCP server scope | Full read-write | Maximum automation; glyph design stays in FontForge GUI |
| MCP server location | `~/prompthub/mcps` (symlink) | Fits existing MCP infrastructure |
| Skill workflow | Audit + fix pipeline | Catches issues before blindly rebuilding |
| Python venv | `--system-site-packages` | Bridges system `fontforge` module |
| Old directories | Delete after migration | Clean break, no duplicates |
| Script style | Fresh idiomatic Python | Existing scripts were downloaded, not user-authored |

## 1. Directory Structure

```
~/fontforge/
├── venv/                          # Python 3 venv (--system-site-packages)
├── requirements.txt
├── fonts/
│   ├── Affinity/
│   ├── Anthropic/
│   ├── Berkeley/
│   ├── BerkeleyMono/
│   ├── Blokna/
│   ├── Burbank/
│   ├── CanvaSans/
│   ├── CohereMono/
│   ├── Discord/
│   ├── EggRoll/
│   ├── Emojitwo/
│   ├── FKGroteskNeue/
│   ├── GGSans/
│   ├── GoogleSans/
│   ├── InstrumentSerif/
│   ├── Monofonto/
│   ├── OneUI/
│   ├── OpenAISans/
│   ├── PPLX/
│   ├── PPEditorialNew/
│   ├── PPRightGrotesk/
│   ├── Samsung/
│   ├── Screens/
│   ├── Square/
│   ├── SuperCasual/
│   ├── TTText/
│   ├── Tests/
│   ├── TicToc/
│   ├── YWFT-Modulan/
│   └── iASans/
├── scripts/
│   ├── build.py
│   ├── metrics.py
│   ├── batch.py
│   └── rename.py
├── mcp-server/
│   └── server.py
└── docs/
    └── guides/
        └── user-manual.md
```

## 2. File Migration

### Source → Destination Mapping

**From `~/Documents/FontForge/`:**

| Source | Destination |
|--------|-------------|
| `Anthropic/` | `fonts/Anthropic/` |
| `Berkeley/` | `fonts/Berkeley/` |
| `Burbank/` | `fonts/Burbank/` |
| `Discord/` | `fonts/Discord/` |
| `EggRoll/` | `fonts/EggRoll/` |
| `Emojitwo/` | `fonts/Emojitwo/` |
| `FKGroteskNeue/` | `fonts/FKGroteskNeue/` |
| `Monofonto/` | `fonts/Monofonto/` |
| `OneUI/` | `fonts/OneUI/` |
| `OpenAISans/` | `fonts/OpenAISans/` |
| `PPLX/` | `fonts/PPLX/` |
| `Samsung/` | `fonts/Samsung/` |
| `Screens/` | `fonts/Screens/` |
| `Square/` | `fonts/Square/` |
| `Tests/` | `fonts/Tests/` |
| `TicToc/` | `fonts/TicToc/` |
| `Blokna-Regular-Demo.otf` | `fonts/Blokna/Blokna-Regular-Demo.otf` |
| `YWFT-Modulan-Regular-Demo.otf` | `fonts/YWFT-Modulan/YWFT-Modulan-Regular-Demo.otf` |
| `Scripts/` | Not migrated (downloaded references only) |

**From `~/Desktop/woff2/`:**

Files grouped by family name prefix:

| Prefix | Destination |
|--------|-------------|
| `Affinity.*` | `fonts/Affinity/` |
| `BerkeleyMono-*` | `fonts/BerkeleyMono/` |
| `CanvaSans-*` | `fonts/CanvaSans/` |
| `CohereMono-*` | `fonts/CohereMono/` |
| `FKGrotesk*` | `fonts/FKGroteskNeue/` (merge with existing) |
| `GGSans-*` | `fonts/GGSans/` |
| `GoogleSans*` | `fonts/GoogleSans/` |
| `InstrumentSerif-*` | `fonts/InstrumentSerif/` |
| `One UI Sans*` | `fonts/OneUI/` (merge with existing) |
| `PPEditorialNew-*` | `fonts/PPEditorialNew/` |
| `PPLX*` | `fonts/PPLX/` (merge with existing) |
| `Samsung Sharp Sans*` | `fonts/Samsung/` (merge with existing) |
| `SuperCasual-*` | `fonts/SuperCasual/` |
| `TTText-*` | `fonts/TTText/` |
| `iASans-*` | `fonts/iASans/` |

Metadata files discarded: `fonts.dir`, `fonts.scale`, `fonts.list`, `encodings.dir`.

**From `~/Downloads/`:**

| Source | Destination |
|--------|-------------|
| `Burbank/BurbankText-Regular.sfd` | `fonts/Burbank/BurbankText-Regular.sfd` |
| `PPRightGrotesk-CompactDark.otf.dfont` | `fonts/PPRightGrotesk/PPRightGrotesk-CompactDark.otf.dfont` |

**Post-migration cleanup:**
- Delete `~/Documents/FontForge/`
- Delete `~/Desktop/woff2/`
- Delete `~/Downloads/Burbank/`

## 3. Python Environment

```bash
# Verify FontForge module is available on the target Python first:
python3 -c 'import fontforge; print(fontforge.version())'

# Create venv using the same Python that has fontforge:
python3 -m venv --system-site-packages ~/fontforge/venv
source ~/fontforge/venv/bin/activate
pip install -r requirements.txt
```

**requirements.txt:**
```
fonttools>=4.47.0
brotli>=1.1.0
zopfli>=0.2.0
```

The `fontforge` module is inherited from the system Python (Homebrew/system install). All scripts and the MCP server share this single venv.

## 4. Standalone Scripts

All scripts use `argparse` for CLI and export importable functions for the MCP server.

### `scripts/build.py` — Web Build Pipeline

Takes a font source file and produces hinted TTF + compressed WOFF2.

**Pipeline steps:**
1. Open source file (SFD/TTF/OTF)
2. Configure blue zones if absent — detect via `font.private["BlueValues"]`; if missing, derive from OS/2 metrics (cap height, x-height, ascender, descender, baseline) and set automatically
3. Select all glyphs (`font.selection.all()`), then auto-hint per glyph
4. Auto-instruct for TrueType grid-fitting (`font.autoInstr()`)
5. Set `gasp` table with thresholds:
   - 0–8 ppem: grid-fit only
   - 9–16 ppem: grid-fit + anti-alias
   - 17+ ppem: anti-alias + grid-fit + symmetric smoothing
6. Generate TTF with `opentype` and `round` flags
7. Compress to WOFF2 using `fonttools` + `brotli`

**CLI:**
```bash
python scripts/build.py fonts/Burbank/BurbankText-Regular.sfd
python scripts/build.py fonts/Burbank/BurbankText-Regular.sfd --output fonts/Burbank/web/
```

### `scripts/metrics.py` — Spacing & Metrics

**Subcommands:**

- `report <path>` — Display side bearings, kerning classes, spacing statistics for a font or family directory
- `adjust <path>` — Modify side bearings: `--lsb +10`, `--rsb -5`, `--glyph A`, `--category uppercase`
- `kern <path>` — Run auto-kerning: `--threshold 50`
- `compare <dir>` — Compare metrics across weights in a family directory

**CLI:**
```bash
python scripts/metrics.py report fonts/Burbank/BurbankText-Regular.sfd
python scripts/metrics.py adjust fonts/Burbank/BurbankText-Regular.sfd --lsb +10
python scripts/metrics.py kern fonts/Burbank/BurbankText-Regular.sfd --threshold 50
python scripts/metrics.py compare fonts/Burbank/
```

### `scripts/batch.py` — Batch Processing

Discovers SFD files and runs the build pipeline on each.

**CLI:**
```bash
python scripts/batch.py                          # all families
python scripts/batch.py --filter "Burbank*"       # filter by glob
python scripts/batch.py --dry-run                 # preview what would be built
```

### `scripts/rename.py` — Font Renaming

Sets font identity fields for a source file.

**CLI:**
```bash
python scripts/rename.py fonts/Burbank/BurbankText-Regular.sfd \
  --family "BurbankText" \
  --fullname "BurbankText Regular" \
  --fontname "BurbankTextRegular" \
  --preferred-family "Burbank Text"
```

## 5. MCP Server

### Location

Source lives at `~/fontforge/mcp-server/server.py`. Symlinked into `~/prompthub/mcps/fontforge-mcp` for discovery.

### Protocol

Stdio-based MCP server. Imports functions from `~/fontforge/scripts/` to avoid logic duplication.

### Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `font_list` | — | List all font families in `~/fontforge/fonts/` |
| `font_open` | `path` | Open a font file, return metadata summary |
| `font_info` | `path` | Detailed metadata: family, weight, glyph count, em size, ascent/descent |
| `font_metrics` | `path` | Side bearings, kerning classes, spacing stats |
| `font_adjust_spacing` | `path`, `lsb?`, `rsb?`, `glyph?`, `category?` | Modify side bearings |
| `font_autohint` | `path` | Run auto-hint + auto-instruct |
| `font_set_gasp` | `path`, `thresholds?` | Configure gasp table |
| `font_autokern` | `path`, `threshold?` | Run auto-kerning |
| `font_rename` | `path`, `family?`, `fullname?`, `fontname?`, `preferred_family?` | Set font identity |
| `font_generate` | `path`, `format`, `output?` | Export to TTF, OTF, or WOFF2 |
| `font_build` | `path`, `output?` | Full pipeline: hint → instruct → gasp → TTF → WOFF2 |
| `font_audit` | `path` | Check web-readiness: hinting, gasp, size, spacing |
| `font_batch_build` | `filter?`, `dry_run?` | Run build pipeline across families |

### Error Handling

All tools return structured results with `success: bool`, `message: str`, and tool-specific data. Font file operations that modify files save a backup (`.bak`) before writing.

## 6. Claude Code Skill (`/font-optimize`)

### Location

`~/.claude/skills/font-optimize/SKILL.md`

### Trigger

Invoked via `/font-optimize <family-or-path>`.

### Workflow

**Phase 1 — Audit:**
Calls `font_audit` on the target. Checks:
- Missing or incomplete hinting
- No gasp table configured
- File size exceeding web thresholds (TTF > 500KB, WOFF2 > 150KB)
- Inconsistent spacing across weights in a family
- Missing WOFF2 exports

**Phase 2 — Report:**
Presents findings with severity levels:
- **Error** — blocks web deployment (e.g., no hinting at all)
- **Warning** — degrades quality (e.g., no gasp table)
- **Info** — optimization opportunity (e.g., could reduce file size)

**Phase 3 — Fix:**
Offers to fix each issue using MCP server tools:
- Apply auto-hinting → `font_autohint`
- Set gasp table → `font_set_gasp`
- Adjust spacing → `font_adjust_spacing`
- Generate web fonts → `font_build`

**Phase 4 — Summary:**
Reports what was fixed, output file locations, and before/after file sizes.

### Dependencies

Requires the FontForge MCP server to be running. The skill orchestrates MCP tools rather than running scripts directly.

## 7. Documentation

### `~/fontforge/docs/guides/user-manual.md`

Comprehensive user manual covering:

1. **Getting Started** — Directory layout, venv setup, verifying FontForge module
2. **Managing Fonts** — Adding new families, directory conventions
3. **Scripts Reference** — CLI usage for each script with examples
4. **MCP Server Reference** — All tools with parameter docs and example calls
5. **Skill Reference** — `/font-optimize` usage and workflow
6. **Common Workflows:**
   - Adding a new font family to the library
   - Building a font for web deployment
   - Adjusting spacing across a family
   - Auditing and fixing web-readiness issues
   - Batch building all fonts

## Non-Goals

- Glyph design/drawing (stays in FontForge GUI)
- Font subsetting for specific character sets (future enhancement)
- Variable font / design space manipulation (future enhancement)
- CI/CD or automated publishing
