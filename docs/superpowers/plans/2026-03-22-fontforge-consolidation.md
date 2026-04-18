# FontForge Project Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate all font files into `~/fontforge/`, create Python automation scripts, an MCP server, and a Claude Code skill for font optimization.

**Architecture:** Monorepo at `~/fontforge/` with shared venv (`--system-site-packages` to bridge FontForge). Scripts export importable functions. MCP server imports from scripts. Skill orchestrates MCP tools.

**Tech Stack:** Python 3.14, FontForge Python module (system), fonttools, brotli, zopfli, MCP SDK (`mcp` Python package)

**Spec:** `docs/superpowers/specs/2026-03-22-fontforge-consolidation-design.md`

---

### Task 1: Create Directory Structure & Python Environment

**Files:**
- Create: `~/fontforge/requirements.txt`
- Create: `~/fontforge/venv/` (via python3 -m venv)

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p ~/fontforge/{fonts,scripts,mcp-server,docs/guides}
```

- [ ] **Step 2: Create requirements.txt**

Create `~/fontforge/requirements.txt`:

```
fonttools>=4.47.0
brotli>=1.1.0
zopfli>=0.2.0
mcp>=1.0.0
```

- [ ] **Step 3: Create and configure the venv**

```bash
python3 -m venv --system-site-packages ~/fontforge/venv
source ~/fontforge/venv/bin/activate
pip install -r ~/fontforge/requirements.txt
```

- [ ] **Step 4: Verify fontforge module is accessible**

```bash
source ~/fontforge/venv/bin/activate
python3 -c 'import fontforge; print(fontforge.version())'
```

Expected: prints `20251009` (or similar version string)

- [ ] **Step 5: Verify fonttools and brotli installed**

```bash
source ~/fontforge/venv/bin/activate
python3 -c 'import fontTools; import brotli; print("OK")'
```

Expected: `OK`

---

### Task 2: Migrate Font Files from ~/Documents/FontForge/

**Files:**
- Move: 16 family directories + 2 loose font files from `~/Documents/FontForge/` → `~/fontforge/fonts/`

- [ ] **Step 1: Move family directories**

```bash
cd ~/Documents/FontForge
for dir in Anthropic Berkeley Burbank Discord EggRoll Emojitwo FKGroteskNeue Monofonto OneUI OpenAISans PPLX Samsung Screens Square Tests TicToc; do
  mv "$dir" ~/fontforge/fonts/
done
```

- [ ] **Step 2: Move loose font files into new family directories**

```bash
mkdir -p ~/fontforge/fonts/Blokna ~/fontforge/fonts/YWFT-Modulan
mv ~/Documents/FontForge/Blokna-Regular-Demo.otf ~/fontforge/fonts/Blokna/
mv ~/Documents/FontForge/YWFT-Modulan-Regular-Demo.otf ~/fontforge/fonts/YWFT-Modulan/
```

- [ ] **Step 3: Verify migration**

```bash
ls ~/fontforge/fonts/ | wc -l
```

Expected: 18 directories

- [ ] **Step 4: Delete remaining ~/Documents/FontForge/ directory**

```bash
rm -rf ~/Documents/FontForge/
```

Confirm: only `.DS_Store` and `Scripts/` (downloaded references) remain before deleting.

---

### Task 3: Migrate Font Files from ~/Desktop/woff2/

**Files:**
- Move: ~70 font files from `~/Desktop/woff2/` → `~/fontforge/fonts/` grouped by family

- [ ] **Step 1: Create new family directories for files without existing homes**

```bash
mkdir -p ~/fontforge/fonts/{Affinity,BerkeleyMono,CanvaSans,CohereMono,GGSans,GoogleSans,InstrumentSerif,PPEditorialNew,SuperCasual,TTText,iASans}
```

- [ ] **Step 2: Move files grouped by family prefix**

```bash
cd ~/Desktop/woff2

# New families
mv Affinity.woff2 ~/fontforge/fonts/Affinity/
mv BerkeleyMono-* ~/fontforge/fonts/BerkeleyMono/
mv CanvaSans-* ~/fontforge/fonts/CanvaSans/
mv CohereMono-* ~/fontforge/fonts/CohereMono/
mv GGSans-* ~/fontforge/fonts/GGSans/
mv GoogleSans* ~/fontforge/fonts/GoogleSans/
mv InstrumentSerif-* ~/fontforge/fonts/InstrumentSerif/
mv PPEditorialNew-* ~/fontforge/fonts/PPEditorialNew/
mv SuperCasual-* ~/fontforge/fonts/SuperCasual/
mv TTText-* ~/fontforge/fonts/TTText/
mv iASans-* ~/fontforge/fonts/iASans/

# Merge into existing families
mv FKGrotesk* ~/fontforge/fonts/FKGroteskNeue/
mv "One UI Sans"* ~/fontforge/fonts/OneUI/
mv PPLX* ~/fontforge/fonts/PPLX/
mv "Samsung Sharp Sans"* ~/fontforge/fonts/Samsung/
```

- [ ] **Step 3: Verify no font files remain (only metadata to discard)**

```bash
ls ~/Desktop/woff2/
```

Expected: only `fonts.dir`, `fonts.scale`, `fonts.list`, `encodings.dir`, `.DS_Store`

- [ ] **Step 4: Delete ~/Desktop/woff2/**

```bash
rm -rf ~/Desktop/woff2/
```

---

### Task 4: Migrate Font Files from ~/Downloads/

**Files:**
- Move: `~/Downloads/Burbank/BurbankText-Regular.sfd` → `~/fontforge/fonts/Burbank/`
- Move: `~/Downloads/PPRightGrotesk-CompactDark.otf.dfont` → `~/fontforge/fonts/PPRightGrotesk/`

- [ ] **Step 1: Move Burbank SFD (merge with existing family)**

```bash
mv ~/Downloads/Burbank/BurbankText-Regular.sfd ~/fontforge/fonts/Burbank/
```

Note: `~/fontforge/fonts/Burbank/` already exists from Task 2 (moved from `~/Documents/FontForge/Burbank/`). This SFD merges in.

- [ ] **Step 2: Move PPRightGrotesk**

```bash
mkdir -p ~/fontforge/fonts/PPRightGrotesk
mv ~/Downloads/PPRightGrotesk-CompactDark.otf.dfont ~/fontforge/fonts/PPRightGrotesk/
```

- [ ] **Step 3: Delete ~/Downloads/Burbank/**

```bash
rm -rf ~/Downloads/Burbank/
```

- [ ] **Step 4: Final font count verification**

```bash
ls ~/fontforge/fonts/ | sort
```

Expected: 18 directories (family directories from ~/Documents/FontForge/):
```
Affinity, Anthropic, Berkeley, BerkeleyMono, Blokna, Burbank, CanvaSans,
CohereMono, Discord, EggRoll, Emojitwo, FKGroteskNeue, GGSans, GoogleSans,
InstrumentSerif, Monofonto, OneUI, OpenAISans, PPLX, PPEditorialNew,
PPRightGrotesk, Samsung, Screens, Square, SuperCasual, TTText, Tests,
TicToc, YWFT-Modulan, iASans
```

---

### Task 5: Write scripts/rename.py

**Files:**
- Create: `~/fontforge/scripts/rename.py`

- [ ] **Step 1: Write rename.py**

Create `~/fontforge/scripts/rename.py`:

```python
"""Font renaming — set family, full, font, and preferred family names."""

import argparse
import sys
from pathlib import Path

import fontforge


def rename_font(
    path: str,
    family: str | None = None,
    fullname: str | None = None,
    fontname: str | None = None,
    preferred_family: str | None = None,
) -> dict:
    """Rename a font's identity fields. Returns old and new values."""
    font = fontforge.open(path)
    old = {
        "family": font.familyname,
        "fullname": font.fullname,
        "fontname": font.fontname,
    }

    if family:
        font.familyname = family
    if fullname:
        font.fullname = fullname
    if fontname:
        font.fontname = fontname
    if preferred_family:
        font.appendSFNTName("English (US)", "Preferred Family", preferred_family)

    font.save(path)
    font.close()

    new = {
        "family": family or old["family"],
        "fullname": fullname or old["fullname"],
        "fontname": fontname or old["fontname"],
        "preferred_family": preferred_family,
    }
    return {"old": old, "new": new}


def main():
    parser = argparse.ArgumentParser(description="Rename font identity fields")
    parser.add_argument("path", help="Path to font file (SFD/TTF/OTF)")
    parser.add_argument("--family", help="Set family name")
    parser.add_argument("--fullname", help="Set full name")
    parser.add_argument("--fontname", help="Set PostScript font name")
    parser.add_argument("--preferred-family", help="Set preferred family (SFNT)")
    args = parser.parse_args()

    if not any([args.family, args.fullname, args.fontname, args.preferred_family]):
        parser.error("At least one of --family, --fullname, --fontname, --preferred-family required")

    result = rename_font(
        args.path,
        family=args.family,
        fullname=args.fullname,
        fontname=args.fontname,
        preferred_family=args.preferred_family,
    )
    print(f"Old: {result['old']}")
    print(f"New: {result['new']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it loads without errors**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/rename.py --help
```

Expected: prints usage with `--family`, `--fullname`, `--fontname`, `--preferred-family` options

- [ ] **Step 3: Test with a real font**

```bash
source ~/fontforge/venv/bin/activate
cp ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd /tmp/test-rename.sfd
python3 ~/fontforge/scripts/rename.py /tmp/test-rename.sfd --family "TestFamily"
rm /tmp/test-rename.sfd
```

Expected: prints old and new values, old family should be "BurbankText" or similar

---

### Task 6: Write scripts/build.py

**Files:**
- Create: `~/fontforge/scripts/build.py`

- [ ] **Step 1: Write build.py**

Create `~/fontforge/scripts/build.py`:

```python
"""Web build pipeline — hint, instruct, gasp, generate TTF, compress WOFF2."""

import argparse
import os
from pathlib import Path

import fontforge
from fontTools.ttLib import TTFont


GASP_TABLE = {
    0: 0x0001,      # 0-8 ppem: grid-fit only
    9: 0x0003,      # 9-16 ppem: grid-fit + anti-alias
    17: 0x000F,      # 17+ ppem: all smoothing
}


def detect_blue_zones(font) -> list:
    """Derive blue zone values from font vertical metrics."""
    ascent = font.ascent
    descent = -abs(font.descent)
    os2 = font.os2_typoascent
    cap_height = getattr(font, "os2_capheight", 0) or int(ascent * 0.7)
    x_height = getattr(font, "os2_xheight", 0) or int(ascent * 0.5)

    # BlueValues: pairs of (overshoot-bottom, zone-top) for baseline and top zones
    blue_values = [
        descent - 10, descent,    # descender zone
        -10, 0,                    # baseline zone
        x_height - 10, x_height,  # x-height zone
        cap_height - 10, cap_height,  # cap-height zone
        ascent - 10, ascent,      # ascender zone
    ]
    return blue_values


def configure_blue_zones(font):
    """Set blue zones if not already present."""
    try:
        existing = font.private["BlueValues"]
        if existing:
            return False  # already configured
    except (KeyError, TypeError):
        pass

    blues = detect_blue_zones(font)
    # FontForge auto-creates private dict on first key assignment
    font.private["BlueValues"] = tuple(blues)
    font.private["BlueFuzz"] = (1,)
    return True


def build_font(path: str, output_dir: str | None = None) -> dict:
    """Run the full web build pipeline on a font file.

    Returns dict with output paths and stats.
    """
    path = os.path.abspath(path)
    src = Path(path)
    out_dir = Path(output_dir) if output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = src.stem
    ttf_path = out_dir / f"{stem}.ttf"
    woff2_path = out_dir / f"{stem}.woff2"

    font = fontforge.open(path)

    # Step 1: Blue zones
    blues_set = configure_blue_zones(font)

    # Step 2: Auto-hint
    font.selection.all()
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            glyph.autoHint()

    # Step 3: Auto-instruct
    font.autoInstr()

    # Step 4: Set gasp table
    font.gasp = tuple(
        (ppem, flags) for ppem, flags in sorted(GASP_TABLE.items())
    )

    # Step 5: Generate TTF
    font.generate(str(ttf_path), flags=("opentype", "round"))
    font.close()

    # Step 6: Compress to WOFF2
    tt = TTFont(str(ttf_path))
    tt.flavor = "woff2"
    tt.save(str(woff2_path))
    tt.close()

    ttf_size = ttf_path.stat().st_size
    woff2_size = woff2_path.stat().st_size

    return {
        "source": path,
        "ttf": str(ttf_path),
        "woff2": str(woff2_path),
        "ttf_size": ttf_size,
        "woff2_size": woff2_size,
        "blues_configured": blues_set,
    }


def main():
    parser = argparse.ArgumentParser(description="Build web-optimized font from source")
    parser.add_argument("path", help="Path to font source file (SFD/TTF/OTF)")
    parser.add_argument("--output", help="Output directory (default: same as source)")
    args = parser.parse_args()

    result = build_font(args.path, output_dir=args.output)
    print(f"Source:  {result['source']}")
    print(f"TTF:    {result['ttf']} ({result['ttf_size']:,} bytes)")
    print(f"WOFF2:  {result['woff2']} ({result['woff2_size']:,} bytes)")
    if result["blues_configured"]:
        print("Blue zones: auto-configured from metrics")
    else:
        print("Blue zones: already present")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it loads without errors**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/build.py --help
```

Expected: prints usage with `path` and `--output` options

- [ ] **Step 3: Test with Burbank**

```bash
source ~/fontforge/venv/bin/activate
mkdir -p /tmp/fontforge-test
python3 ~/fontforge/scripts/build.py ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd --output /tmp/fontforge-test/
ls -la /tmp/fontforge-test/
rm -rf /tmp/fontforge-test/
```

Expected: produces `BurbankText-Regular.ttf` and `BurbankText-Regular.woff2`, prints sizes

---

### Task 7: Write scripts/metrics.py

**Files:**
- Create: `~/fontforge/scripts/metrics.py`

- [ ] **Step 1: Write metrics.py**

Create `~/fontforge/scripts/metrics.py`:

```python
"""Font spacing and metrics — report, adjust, kern, compare."""

import argparse
import json
import os
from pathlib import Path

import fontforge


def report_metrics(path: str) -> dict:
    """Report spacing metrics for a single font file."""
    font = fontforge.open(path)

    bearings = []
    for glyph in font.glyphs():
        if glyph.isWorthOutputting() and glyph.unicode > 0:
            bearings.append({
                "name": glyph.glyphname,
                "unicode": glyph.unicode,
                "lsb": glyph.left_side_bearing,
                "rsb": glyph.right_side_bearing,
                "width": glyph.width,
            })

    kern_count = 0
    for lookup in font.gpos_lookups:
        for subtable in font.getLookupSubtables(lookup):
            if font.isKerningClass(subtable):
                kern_count += 1

    lsb_values = [g["lsb"] for g in bearings if g["lsb"] is not None]
    rsb_values = [g["rsb"] for g in bearings if g["rsb"] is not None]

    result = {
        "path": path,
        "family": font.familyname,
        "weight": font.weight,
        "glyph_count": len(bearings),
        "em_size": font.em,
        "ascent": font.ascent,
        "descent": font.descent,
        "kern_subtables": kern_count,
        "lsb_min": min(lsb_values) if lsb_values else 0,
        "lsb_max": max(lsb_values) if lsb_values else 0,
        "lsb_avg": round(sum(lsb_values) / len(lsb_values)) if lsb_values else 0,
        "rsb_min": min(rsb_values) if rsb_values else 0,
        "rsb_max": max(rsb_values) if rsb_values else 0,
        "rsb_avg": round(sum(rsb_values) / len(rsb_values)) if rsb_values else 0,
    }

    font.close()
    return result


def adjust_spacing(
    path: str,
    lsb: int = 0,
    rsb: int = 0,
    glyph: str | None = None,
    category: str | None = None,
) -> dict:
    """Adjust side bearings. Returns count of modified glyphs."""
    font = fontforge.open(path)
    modified = 0

    for g in font.glyphs():
        if not g.isWorthOutputting():
            continue

        if glyph and g.glyphname != glyph:
            continue

        if category:
            if category == "uppercase" and not (65 <= g.unicode <= 90):
                continue
            elif category == "lowercase" and not (97 <= g.unicode <= 122):
                continue
            elif category == "digits" and not (48 <= g.unicode <= 57):
                continue

        if lsb:
            g.left_side_bearing += lsb
        if rsb:
            g.right_side_bearing += rsb
        modified += 1

    font.save(path)
    font.close()
    return {"path": path, "modified": modified, "lsb_delta": lsb, "rsb_delta": rsb}


def auto_kern(path: str, threshold: int = 50) -> dict:
    """Run auto-kerning on a font."""
    font = fontforge.open(path)
    font.selection.all()

    # Find or create kern lookup
    kern_lookups = [l for l in font.gpos_lookups if "kern" in l.lower()]
    if not kern_lookups:
        font.addLookup("kern", "gpos_pair", None,
                        (("kern", (("DFLT", ("dflt",)),("latn", ("dflt",)),)),))
        font.addLookupSubtable("kern", "kern-1")
        lookup_name = "kern-1"
    else:
        subtables = font.getLookupSubtables(kern_lookups[0])
        lookup_name = subtables[0] if subtables else None

    if lookup_name:
        font.autoKern(lookup_name, threshold)

    font.save(path)
    font.close()
    return {"path": path, "threshold": threshold}


def compare_family(directory: str) -> list[dict]:
    """Compare metrics across all fonts in a family directory."""
    results = []
    for f in sorted(Path(directory).glob("*.sfd")):
        results.append(report_metrics(str(f)))
    for f in sorted(Path(directory).glob("*.ttf")):
        results.append(report_metrics(str(f)))
    return results


def main():
    parser = argparse.ArgumentParser(description="Font spacing and metrics tools")
    sub = parser.add_subparsers(dest="command", required=True)

    # report
    rpt = sub.add_parser("report", help="Report metrics for a font")
    rpt.add_argument("path", help="Font file path")

    # adjust
    adj = sub.add_parser("adjust", help="Adjust side bearings")
    adj.add_argument("path", help="Font file path")
    adj.add_argument("--lsb", type=int, default=0, help="Left side bearing delta")
    adj.add_argument("--rsb", type=int, default=0, help="Right side bearing delta")
    adj.add_argument("--glyph", help="Target specific glyph by name")
    adj.add_argument("--category", choices=["uppercase", "lowercase", "digits"],
                     help="Target glyph category")

    # kern
    krn = sub.add_parser("kern", help="Run auto-kerning")
    krn.add_argument("path", help="Font file path")
    krn.add_argument("--threshold", type=int, default=50, help="Kerning separation threshold")

    # compare
    cmp = sub.add_parser("compare", help="Compare metrics across family weights")
    cmp.add_argument("directory", help="Family directory path")

    args = parser.parse_args()

    if args.command == "report":
        result = report_metrics(args.path)
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif args.command == "adjust":
        result = adjust_spacing(args.path, lsb=args.lsb, rsb=args.rsb,
                                glyph=args.glyph, category=args.category)
        print(f"Modified {result['modified']} glyphs (LSB {result['lsb_delta']:+d}, RSB {result['rsb_delta']:+d})")

    elif args.command == "kern":
        result = auto_kern(args.path, threshold=args.threshold)
        print(f"Auto-kerned with threshold {result['threshold']}")

    elif args.command == "compare":
        results = compare_family(args.directory)
        if not results:
            print("No font files found")
            return
        print(f"{'File':<40} {'Weight':<12} {'Glyphs':>7} {'LSB avg':>8} {'RSB avg':>8} {'Kern':>5}")
        print("-" * 85)
        for r in results:
            name = Path(r["path"]).name
            print(f"{name:<40} {r['weight']:<12} {r['glyph_count']:>7} {r['lsb_avg']:>8} {r['rsb_avg']:>8} {r['kern_subtables']:>5}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it loads**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/metrics.py --help
python3 ~/fontforge/scripts/metrics.py report --help
```

Expected: prints subcommands and report usage

- [ ] **Step 3: Test report on Burbank**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/metrics.py report ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd
```

Expected: prints family name, glyph count, bearing stats, kern count

---

### Task 8: Write scripts/batch.py

**Files:**
- Create: `~/fontforge/scripts/batch.py`

- [ ] **Step 1: Write batch.py**

Create `~/fontforge/scripts/batch.py`:

```python
"""Batch build — discover and process all font sources."""

import argparse
import fnmatch
import sys
import traceback
from pathlib import Path

# Allow importing sibling scripts
sys.path.insert(0, str(Path(__file__).parent))
from build import build_font


FONTS_DIR = Path.home() / "fontforge" / "fonts"


def discover_sources(base: Path, pattern: str = "*") -> list[Path]:
    """Find all SFD files under base, optionally filtered by family glob."""
    sources = []
    for family_dir in sorted(base.iterdir()):
        if not family_dir.is_dir():
            continue
        if not fnmatch.fnmatch(family_dir.name, pattern):
            continue
        for sfd in sorted(family_dir.glob("*.sfd")):
            sources.append(sfd)
    return sources


def batch_build(
    base: Path = FONTS_DIR,
    pattern: str = "*",
    dry_run: bool = False,
) -> list[dict]:
    """Run build pipeline on all discovered sources."""
    sources = discover_sources(base, pattern)
    results = []

    for src in sources:
        if dry_run:
            results.append({"source": str(src), "status": "skipped (dry run)"})
            print(f"  [dry-run] {src}")
            continue

        try:
            result = build_font(str(src))
            result["status"] = "success"
            results.append(result)
            print(f"  [ok] {src.name} -> TTF ({result['ttf_size']:,}B) + WOFF2 ({result['woff2_size']:,}B)")
        except Exception as e:
            results.append({"source": str(src), "status": "error", "error": str(e)})
            print(f"  [FAIL] {src.name}: {e}")
            traceback.print_exc()

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch build web fonts from all sources")
    parser.add_argument("--filter", default="*", help="Family name glob (e.g. 'Burbank*')")
    parser.add_argument("--dry-run", action="store_true", help="Preview without building")
    parser.add_argument("--fonts-dir", type=Path, default=FONTS_DIR,
                        help=f"Fonts directory (default: {FONTS_DIR})")
    args = parser.parse_args()

    print(f"Scanning {args.fonts_dir} (filter: {args.filter})...")
    results = batch_build(args.fonts_dir, args.filter, args.dry_run)

    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if "dry run" in r.get("status", ""))
    total = len(results)

    print(f"\nDone: {total} sources — {success} built, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it loads**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/batch.py --help
```

Expected: prints usage with `--filter`, `--dry-run` options

- [ ] **Step 3: Test dry-run**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/batch.py --filter "Burbank*" --dry-run
```

Expected: lists Burbank SFD files with `[dry-run]` prefix

---

### Task 9: Write MCP Server

**Files:**
- Create: `~/fontforge/mcp-server/server.py`

- [ ] **Step 1: Write server.py**

Create `~/fontforge/mcp-server/server.py`:

```python
"""FontForge MCP Server — stdio-based server for font manipulation."""

import json
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from build import build_font, configure_blue_zones
from metrics import report_metrics, adjust_spacing, auto_kern, compare_family
from rename import rename_font

FONTS_DIR = Path.home() / "fontforge" / "fonts"

mcp = FastMCP("fontforge", description="FontForge font manipulation tools")


@mcp.tool()
def font_list() -> str:
    """List all font families in ~/fontforge/fonts/."""
    families = sorted(
        d.name for d in FONTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    return json.dumps({"families": families, "count": len(families)})


@mcp.tool()
def font_open(path: str) -> str:
    """Open a font file and return a metadata summary."""
    import fontforge
    path = _resolve_path(path)
    font = fontforge.open(path)
    result = {
        "path": path,
        "family": font.familyname,
        "fullname": font.fullname,
        "fontname": font.fontname,
        "weight": font.weight,
        "version": font.version,
        "em_size": font.em,
        "ascent": font.ascent,
        "descent": font.descent,
        "glyph_count": sum(1 for g in font.glyphs() if g.isWorthOutputting()),
    }
    font.close()
    return json.dumps(result)


@mcp.tool()
def font_info(path: str) -> str:
    """Get detailed font metadata including OS/2 metrics."""
    import fontforge
    path = _resolve_path(path)
    font = fontforge.open(path)
    result = {
        "path": path,
        "family": font.familyname,
        "fullname": font.fullname,
        "fontname": font.fontname,
        "weight": font.weight,
        "em_size": font.em,
        "ascent": font.ascent,
        "descent": font.descent,
        "os2_typoascent": font.os2_typoascent,
        "os2_typodescent": font.os2_typodescent,
        "os2_capheight": getattr(font, "os2_capheight", None),
        "os2_xheight": getattr(font, "os2_xheight", None),
        "glyph_count": sum(1 for g in font.glyphs() if g.isWorthOutputting()),
        "copyright": font.copyright,
        "has_blue_zones": _has_blue_zones(font),
        "has_gasp": bool(font.gasp),
        "gpos_lookups": list(font.gpos_lookups),
    }
    font.close()
    return json.dumps(result)


@mcp.tool()
def font_metrics(path: str) -> str:
    """Report side bearings, kerning classes, and spacing stats."""
    path = _resolve_path(path)
    result = report_metrics(path)
    return json.dumps(result)


@mcp.tool()
def font_adjust_spacing(
    path: str,
    lsb: int = 0,
    rsb: int = 0,
    glyph: str | None = None,
    category: str | None = None,
) -> str:
    """Modify left/right side bearings. Saves a .bak backup first."""
    path = _resolve_path(path)
    _backup(path)
    result = adjust_spacing(path, lsb=lsb, rsb=rsb, glyph=glyph, category=category)
    return json.dumps({"success": True, **result})


@mcp.tool()
def font_autohint(path: str) -> str:
    """Run auto-hint and auto-instruct on a font."""
    import fontforge
    path = _resolve_path(path)
    _backup(path)
    font = fontforge.open(path)
    configure_blue_zones(font)
    font.selection.all()
    for g in font.glyphs():
        if g.isWorthOutputting():
            g.autoHint()
    font.autoInstr()
    font.save(path)
    font.close()
    return json.dumps({"success": True, "path": path, "message": "Auto-hinted and auto-instructed"})


@mcp.tool()
def font_set_gasp(path: str, thresholds: dict | None = None) -> str:
    """Configure the gasp table for optimal screen rendering.

    thresholds: optional dict mapping ppem -> flags (e.g. {0: 1, 9: 3, 17: 15}).
    If None, uses standard web defaults.
    """
    import fontforge
    path = _resolve_path(path)
    _backup(path)
    font = fontforge.open(path)
    if thresholds:
        font.gasp = tuple((int(k), v) for k, v in sorted(thresholds.items()))
    else:
        font.gasp = ((0, 0x0001), (9, 0x0003), (17, 0x000F))
    font.save(path)
    font.close()
    return json.dumps({"success": True, "path": path, "message": "gasp table configured"})


@mcp.tool()
def font_autokern(path: str, threshold: int = 50) -> str:
    """Run auto-kerning with configurable separation threshold."""
    path = _resolve_path(path)
    _backup(path)
    result = auto_kern(path, threshold=threshold)
    return json.dumps({"success": True, **result})


@mcp.tool()
def font_rename(
    path: str,
    family: str | None = None,
    fullname: str | None = None,
    fontname: str | None = None,
    preferred_family: str | None = None,
) -> str:
    """Set font identity names."""
    path = _resolve_path(path)
    _backup(path)
    result = rename_font(path, family=family, fullname=fullname,
                         fontname=fontname, preferred_family=preferred_family)
    return json.dumps({"success": True, **result})


@mcp.tool()
def font_generate(path: str, format: str = "ttf", output: str | None = None) -> str:
    """Export font to TTF, OTF, or WOFF2."""
    import fontforge
    from fontTools.ttLib import TTFont

    path = _resolve_path(path)
    src = Path(path)
    out_dir = Path(output) if output else src.parent
    stem = src.stem

    font = fontforge.open(path)

    if format in ("ttf", "woff2"):
        out_path = out_dir / f"{stem}.ttf"
        font.generate(str(out_path), flags=("opentype", "round"))
        font.close()

        if format == "woff2":
            woff2_path = out_dir / f"{stem}.woff2"
            tt = TTFont(str(out_path))
            tt.flavor = "woff2"
            tt.save(str(woff2_path))
            tt.close()
            return json.dumps({"success": True, "path": str(woff2_path),
                              "size": woff2_path.stat().st_size})

        return json.dumps({"success": True, "path": str(out_path),
                          "size": out_path.stat().st_size})

    elif format == "otf":
        out_path = out_dir / f"{stem}.otf"
        font.generate(str(out_path), flags=("opentype",))
        font.close()
        return json.dumps({"success": True, "path": str(out_path),
                          "size": out_path.stat().st_size})

    font.close()
    return json.dumps({"success": False, "message": f"Unknown format: {format}"})


@mcp.tool()
def font_build(path: str, output: str | None = None) -> str:
    """Full web build pipeline: hint, instruct, gasp, TTF, WOFF2."""
    path = _resolve_path(path)
    result = build_font(path, output_dir=output)
    return json.dumps({"success": True, **result})


@mcp.tool()
def font_audit(path: str) -> str:
    """Audit a font or family directory for web-readiness issues."""
    import fontforge

    path = _resolve_path(path)
    p = Path(path)
    issues = []

    # If directory, audit all fonts in it
    files = sorted(p.glob("*.sfd")) + sorted(p.glob("*.ttf")) if p.is_dir() else [p]

    for f in files:
        font = fontforge.open(str(f))
        name = f.name

        # Check hinting
        hinted = sum(1 for g in font.glyphs() if g.isWorthOutputting() and (g.hhints or g.vhints))
        total = sum(1 for g in font.glyphs() if g.isWorthOutputting())
        if hinted == 0:
            issues.append({"file": name, "severity": "error",
                          "issue": "No glyphs are hinted"})
        elif hinted < total * 0.5:
            issues.append({"file": name, "severity": "warning",
                          "issue": f"Only {hinted}/{total} glyphs hinted"})

        # Check gasp
        if not font.gasp:
            issues.append({"file": name, "severity": "warning",
                          "issue": "No gasp table — screen rendering not optimized"})

        # Check blue zones
        if not _has_blue_zones(font):
            issues.append({"file": name, "severity": "warning",
                          "issue": "No blue zones configured"})

        font.close()

        # Check file sizes
        size = f.stat().st_size
        if f.suffix == ".ttf" and size > 500_000:
            issues.append({"file": name, "severity": "info",
                          "issue": f"TTF is {size:,} bytes (>500KB web threshold)"})

        # Check for missing WOFF2
        woff2 = f.with_suffix(".woff2")
        if f.suffix in (".ttf", ".otf") and not woff2.exists():
            issues.append({"file": name, "severity": "info",
                          "issue": "No WOFF2 export found"})

    # Check spacing consistency if directory
    if p.is_dir():
        sfd_files = sorted(p.glob("*.sfd"))
        if len(sfd_files) > 1:
            metrics = [report_metrics(str(f)) for f in sfd_files]
            lsb_avgs = [m["lsb_avg"] for m in metrics]
            if lsb_avgs and max(lsb_avgs) - min(lsb_avgs) > 50:
                issues.append({"file": p.name, "severity": "warning",
                              "issue": "LSB averages vary >50 units across weights"})

    return json.dumps({"path": str(path), "issues": issues,
                       "issue_count": len(issues)})


@mcp.tool()
def font_batch_build(filter: str = "*", dry_run: bool = False) -> str:
    """Run build pipeline across multiple font families."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from batch import batch_build
    results = batch_build(FONTS_DIR, filter, dry_run)
    return json.dumps({"results": results, "count": len(results)})


def _resolve_path(path: str) -> str:
    """Resolve a path, checking fonts dir for relative family paths."""
    p = Path(path)
    if p.is_absolute() and p.exists():
        return str(p)
    # Try relative to fonts dir
    candidate = FONTS_DIR / path
    if candidate.exists():
        return str(candidate)
    # Try expanding ~
    expanded = p.expanduser()
    if expanded.exists():
        return str(expanded)
    return str(p)


def _backup(path: str):
    """Create a .bak backup of a file before modification."""
    src = Path(path)
    if src.exists():
        bak = src.with_suffix(src.suffix + ".bak")
        import shutil
        shutil.copy2(src, bak)


def _has_blue_zones(font) -> bool:
    """Check if a font has blue zones configured."""
    try:
        return bool(font.private["BlueValues"])
    except (KeyError, TypeError):
        return False


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

- [ ] **Step 2: Verify it loads**

```bash
source ~/fontforge/venv/bin/activate
python3 -c "import sys; sys.path.insert(0, '$HOME/fontforge/mcp-server'); from server import mcp; print('Server loaded:', mcp.name)"
```

Expected: `Server loaded: fontforge`

- [ ] **Step 3: Register MCP server with PromptHub config**

Edit `~/.local/share/prompthub/.mcp.json` to add the `fontforge` entry. The complete file should be:

```json
{
  "mcpServers": {
    "prompthub": {
      "type": "stdio",
      "command": "node",
      "args": [
        "/Users/visualval/prompthub/mcps/prompthub-bridge.js"
      ],
      "env": {
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "AUTHORIZATION": "Bearer sk-prompthub-claude-code-001",
        "CLIENT_NAME": "claude-code",
        "SERVERS": "sequential-thinking,desktop-commander,context7",
        "EXCLUDE_TOOLS": "duckduckgo,perplexity"
      }
    },
    "skills-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "skills-mcp",
        "-s",
        "/Users/visualval/.claude/skills"
      ]
    },
    "fontforge": {
      "type": "stdio",
      "command": "/Users/visualval/fontforge/venv/bin/python3",
      "args": ["/Users/visualval/fontforge/mcp-server/server.py"]
    }
  }
}
```

Also create the symlink for discoverability:

```bash
ln -s ~/fontforge/mcp-server ~/prompthub/mcps/fontforge-mcp
```

**Note:** After editing the MCP config, restart Claude Code for the new server to be discovered.

- [ ] **Step 4: Test MCP server responds to initialization**

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | ~/fontforge/venv/bin/python3 ~/fontforge/mcp-server/server.py 2>/dev/null | head -1
```

Expected: JSON response with server capabilities

---

### Task 10: Write Claude Code Skill

**Files:**
- Create: `~/.claude/skills/font-optimize/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Create `~/.claude/skills/font-optimize/SKILL.md`:

```markdown
---
name: font-optimize
description: Audit and optimize fonts for web deployment — checks hinting, gasp tables, spacing, file sizes, and generates optimized TTF/WOFF2. Use when user wants to optimize fonts, check web-readiness, or build web font files.
---

# Font Optimize

Audit a font or font family for web-readiness issues, then fix them.

## Usage

`/font-optimize <family-name-or-path>`

Examples:
- `/font-optimize Burbank`
- `/font-optimize ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd`

## Workflow

### Phase 1: Audit

Call the `font_audit` MCP tool on the target path.

If the argument is a family name (no path separators), resolve it to `~/fontforge/fonts/<name>/`.

Present the audit results grouped by severity:
- **Errors** (red) — blocks web deployment
- **Warnings** (yellow) — degrades rendering quality
- **Info** (blue) — optimization opportunities

### Phase 2: Report

Display a summary table:

```
File                          Issue                              Severity
─────────────────────────────────────────────────────────────────────────
BurbankText-Regular.sfd       No glyphs are hinted               ERROR
BurbankText-Regular.sfd       No gasp table configured            WARNING
BurbankText-Regular.ttf       No WOFF2 export found               INFO
```

### Phase 3: Fix

For each issue, offer to fix it using the appropriate MCP tool:

| Issue | Fix Tool | Action |
|-------|----------|--------|
| No hinting | `font_autohint` | Auto-hint + auto-instruct all glyphs |
| No gasp table | `font_set_gasp` | Set standard web gasp thresholds |
| No blue zones | `font_autohint` | Configures blue zones as part of hinting |
| Spacing inconsistency | `font_adjust_spacing` | Ask user for target values |
| No WOFF2 export | `font_build` | Run full build pipeline |
| Large file size | `font_build` | Rebuild with optimization |

Ask user which fixes to apply (all, specific ones, or none).

### Phase 4: Summary

After applying fixes, report:
- What was fixed
- Output file paths
- Before/after file sizes for generated files

## Dependencies

Requires the `fontforge` MCP server to be running (registered in PromptHub MCP config).
```

- [ ] **Step 2: Verify skill is discoverable**

```bash
ls ~/.claude/skills/font-optimize/SKILL.md
```

Expected: file exists

---

### Task 11: Write User Manual

**Files:**
- Create: `~/fontforge/docs/guides/user-manual.md`

- [ ] **Step 1: Write user-manual.md**

Create `~/fontforge/docs/guides/user-manual.md`:

```markdown
# FontForge Toolchain — User Manual

## Getting Started

### Directory Layout

```
~/fontforge/
├── venv/          Python virtual environment (bridges system fontforge module)
├── fonts/         All font families, one directory per family
├── scripts/       Standalone Python scripts for font automation
├── mcp-server/    MCP server for Claude integration
└── docs/          Documentation
```

### Setup

The venv is pre-configured. To activate:

```bash
source ~/fontforge/venv/bin/activate
```

Verify everything works:

```bash
python3 -c 'import fontforge; print(fontforge.version())'
python3 -c 'import fontTools; import brotli; print("OK")'
```

---

## Managing Fonts

### Adding a New Font Family

1. Create a directory under `~/fontforge/fonts/`:

```bash
mkdir ~/fontforge/fonts/MyNewFont
```

2. Copy font files (SFD, TTF, OTF, WOFF2) into it:

```bash
cp MyNewFont-Regular.sfd ~/fontforge/fonts/MyNewFont/
```

### Directory Conventions

- One directory per font family
- All weights and formats for a family live together
- Source files (SFD) and exports (TTF, WOFF2) coexist in the same directory

---

## Scripts Reference

All scripts are in `~/fontforge/scripts/`. Always activate the venv first.

### build.py — Web Build Pipeline

Produces hinted TTF + compressed WOFF2 from a source file.

```bash
# Build with output alongside source
python3 scripts/build.py fonts/Burbank/BurbankText-Regular.sfd

# Build to a specific output directory
python3 scripts/build.py fonts/Burbank/BurbankText-Regular.sfd --output fonts/Burbank/web/
```

**What it does:**
1. Configures blue zones (if not already set)
2. Auto-hints all glyphs
3. Auto-instructs for TrueType grid-fitting
4. Sets gasp table for screen rendering
5. Generates TTF
6. Compresses to WOFF2

### metrics.py — Spacing & Metrics

Four subcommands for inspecting and adjusting font spacing.

```bash
# Report metrics for a font
python3 scripts/metrics.py report fonts/Burbank/BurbankText-Regular.sfd

# Adjust side bearings globally
python3 scripts/metrics.py adjust fonts/Burbank/BurbankText-Regular.sfd --lsb +10 --rsb +10

# Adjust only uppercase letters
python3 scripts/metrics.py adjust fonts/Burbank/BurbankText-Regular.sfd --lsb -5 --category uppercase

# Adjust a single glyph
python3 scripts/metrics.py adjust fonts/Burbank/BurbankText-Regular.sfd --lsb +20 --glyph A

# Auto-kern with custom threshold
python3 scripts/metrics.py kern fonts/Burbank/BurbankText-Regular.sfd --threshold 40

# Compare metrics across family weights
python3 scripts/metrics.py compare fonts/Burbank/
```

### batch.py — Batch Processing

Discovers all SFD source files and runs the build pipeline.

```bash
# Build all families
python3 scripts/batch.py

# Build only Burbank
python3 scripts/batch.py --filter "Burbank*"

# Preview what would be built
python3 scripts/batch.py --dry-run

# Use a different fonts directory
python3 scripts/batch.py --fonts-dir /path/to/other/fonts/
```

### rename.py — Font Renaming

Set font identity fields (family name, PostScript name, etc.).

```bash
python3 scripts/rename.py fonts/Burbank/BurbankText-Regular.sfd \
  --family "BurbankText" \
  --fullname "BurbankText Regular" \
  --fontname "BurbankTextRegular" \
  --preferred-family "Burbank Text"
```

---

## MCP Server Reference

The FontForge MCP server allows Claude to manipulate fonts directly. It's registered in the PromptHub MCP config and runs via stdio.

### Tools

| Tool | Description |
|------|-------------|
| `font_list` | List all font families |
| `font_open` | Open a font, get metadata summary |
| `font_info` | Detailed metadata including OS/2 metrics |
| `font_metrics` | Side bearings, kerning, spacing stats |
| `font_adjust_spacing` | Modify side bearings (backs up first) |
| `font_autohint` | Auto-hint + auto-instruct |
| `font_set_gasp` | Configure gasp table |
| `font_autokern` | Run auto-kerning |
| `font_rename` | Set font identity names |
| `font_generate` | Export to TTF, OTF, or WOFF2 |
| `font_build` | Full pipeline: hint → instruct → gasp → TTF → WOFF2 |
| `font_audit` | Check web-readiness issues |
| `font_batch_build` | Batch build across families |

### Path Resolution

All tools accept paths in three forms:
- **Absolute:** `/Users/you/fontforge/fonts/Burbank/BurbankText-Regular.sfd`
- **Relative to fonts dir:** `Burbank/BurbankText-Regular.sfd`
- **Family directory:** `Burbank/` (for audit and compare operations)

### Backups

Tools that modify font files (`font_adjust_spacing`, `font_autohint`, `font_set_gasp`, `font_autokern`, `font_rename`) create a `.bak` backup before writing.

---

## Skill Reference

### /font-optimize

Audit and optimize a font or font family for web deployment.

```
/font-optimize Burbank
/font-optimize ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd
```

**Workflow:**
1. **Audit** — scans for hinting, gasp, spacing, and size issues
2. **Report** — presents findings with severity levels
3. **Fix** — offers to fix each issue using MCP tools
4. **Summary** — reports what changed with before/after sizes

---

## Common Workflows

### Building a Font for Web

```bash
source ~/fontforge/venv/bin/activate
python3 scripts/build.py fonts/Burbank/BurbankText-Regular.sfd
```

Or via Claude: `/font-optimize Burbank`

### Adjusting Spacing Across a Family

```bash
source ~/fontforge/venv/bin/activate

# First, compare current metrics
python3 scripts/metrics.py compare fonts/Burbank/

# Then adjust as needed
python3 scripts/metrics.py adjust fonts/Burbank/BurbankText-Regular.sfd --lsb +10
python3 scripts/metrics.py adjust fonts/Burbank/BurbankText-Bold.sfd --lsb +10
```

### Batch Building All Fonts

```bash
source ~/fontforge/venv/bin/activate

# Preview
python3 scripts/batch.py --dry-run

# Build everything
python3 scripts/batch.py
```

### Adding a New Font Family

1. Create directory: `mkdir ~/fontforge/fonts/NewFamily/`
2. Add source files: `cp *.sfd ~/fontforge/fonts/NewFamily/`
3. Build: `python3 scripts/build.py fonts/NewFamily/NewFamily-Regular.sfd`
4. Or audit + fix: `/font-optimize NewFamily`
```

- [ ] **Step 2: Verify doc exists**

```bash
cat ~/fontforge/docs/guides/user-manual.md | head -5
```

Expected: shows the title and first section

---

### Task 12: Final Verification

- [ ] **Step 1: Verify complete directory structure**

```bash
find ~/fontforge -maxdepth 3 -not -path '*/venv/*' -not -name '.DS_Store' -not -name '__pycache__' | sort
```

Expected: shows fonts/, scripts/, mcp-server/, docs/ with all expected files

- [ ] **Step 2: Verify all scripts run --help without errors**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/build.py --help
python3 ~/fontforge/scripts/metrics.py --help
python3 ~/fontforge/scripts/batch.py --help
python3 ~/fontforge/scripts/rename.py --help
```

Expected: all print usage without errors

- [ ] **Step 3: Verify old directories are deleted**

```bash
ls ~/Documents/FontForge/ 2>&1
ls ~/Desktop/woff2/ 2>&1
ls ~/Downloads/Burbank/ 2>&1
```

Expected: all three report "No such file or directory"

- [ ] **Step 4: Verify font count**

```bash
ls ~/fontforge/fonts/ | wc -l
```

Expected: 30 family directories

- [ ] **Step 5: Run a full integration test — build Burbank for web**

```bash
source ~/fontforge/venv/bin/activate
python3 ~/fontforge/scripts/build.py ~/fontforge/fonts/Burbank/BurbankText-Regular.sfd --output /tmp/fontforge-integration-test/
ls -la /tmp/fontforge-integration-test/
rm -rf /tmp/fontforge-integration-test/
```

Expected: TTF and WOFF2 files produced with reported sizes
