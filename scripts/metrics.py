#!/usr/bin/env python3
"""Font metrics extraction and reporting utility.

Reads font metadata, metrics, glyph counts, and character coverage
from font files using fonttools.

Usage:
    python metrics.py <font_file>           # Show metrics for a single font
    python metrics.py <directory>            # Show summary table for all fonts
    python metrics.py <font_file> --json     # Output as JSON
    python metrics.py <directory> --compare  # Side-by-side comparison table
"""

import argparse
import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.unicode import Unicode

FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".ttc"}

WEIGHT_CLASS_NAMES = {
    100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
    500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
    900: "Black",
}

WIDTH_CLASS_NAMES = {
    1: "UltraCondensed", 2: "ExtraCondensed", 3: "Condensed",
    4: "SemiCondensed", 5: "Normal", 6: "SemiExpanded",
    7: "Expanded", 8: "ExtraExpanded", 9: "UltraExpanded",
}


def get_name(name_table, name_id: int) -> str:
    for record in name_table.names:
        if record.nameID == name_id:
            try:
                return str(record).strip()
            except Exception:
                continue
    return ""


def get_cmap_codepoints(font: TTFont) -> set[int]:
    """Get all Unicode codepoints covered by the font's cmap."""
    codepoints = set()
    for table in font["cmap"].tables:
        if table.isUnicode():
            codepoints.update(table.cmap.keys())
    return codepoints


def classify_scripts(codepoints: set[int]) -> dict[str, int]:
    """Classify codepoints into script categories."""
    scripts = {
        "Basic Latin": (0x0000, 0x007F),
        "Latin-1 Supplement": (0x00A0, 0x00FF),
        "Latin Extended-A": (0x0100, 0x017F),
        "Latin Extended-B": (0x0180, 0x024F),
        "Cyrillic": (0x0400, 0x04FF),
        "Greek": (0x0370, 0x03FF),
        "Arabic": (0x0600, 0x06FF),
        "CJK Unified": (0x4E00, 0x9FFF),
        "Hangul Syllables": (0xAC00, 0xD7AF),
        "Emoji": (0x1F600, 0x1F64F),
    }
    result = {}
    for name, (start, end) in scripts.items():
        count = sum(1 for cp in codepoints if start <= cp <= end)
        if count > 0:
            result[name] = count
    return result


def extract_metrics(font_path: Path) -> dict:
    """Extract comprehensive metrics from a font file."""
    try:
        font = TTFont(font_path, fontNumber=0)
    except Exception as e:
        return {"error": str(e), "file": font_path.name}

    info = {"file": font_path.name, "path": str(font_path)}

    # Name table entries
    name_table = font["name"]
    info["family"] = get_name(name_table, 16) or get_name(name_table, 1)
    info["subfamily"] = get_name(name_table, 17) or get_name(name_table, 2)
    info["full_name"] = get_name(name_table, 4)
    info["version"] = get_name(name_table, 5)
    info["copyright"] = get_name(name_table, 0)
    info["designer"] = get_name(name_table, 9)
    info["license"] = get_name(name_table, 13)

    # Format info
    info["format"] = font_path.suffix.lstrip(".").upper()
    info["flavor"] = font.flavor or "none"
    info["file_size"] = font_path.stat().st_size
    info["tables"] = sorted(font.keys())

    # Glyph info
    info["glyph_count"] = len(font.getGlyphOrder())

    # OS/2 table metrics
    if "OS/2" in font:
        os2 = font["OS/2"]
        info["weight_class"] = os2.usWeightClass
        info["weight_name"] = WEIGHT_CLASS_NAMES.get(os2.usWeightClass, str(os2.usWeightClass))
        info["width_class"] = os2.usWidthClass
        info["width_name"] = WIDTH_CLASS_NAMES.get(os2.usWidthClass, str(os2.usWidthClass))
        info["ascender"] = os2.sTypoAscender
        info["descender"] = os2.sTypoDescender
        info["line_gap"] = os2.sTypoLineGap
        info["cap_height"] = getattr(os2, "sCapHeight", None)
        info["x_height"] = getattr(os2, "sxHeight", None)
        info["avg_char_width"] = os2.xAvgCharWidth
        # Panose
        if hasattr(os2, "panose") and os2.panose:
            info["panose_family"] = os2.panose.bFamilyType

    # head table
    if "head" in font:
        head = font["head"]
        info["units_per_em"] = head.unitsPerEm
        info["bbox"] = [head.xMin, head.yMin, head.xMax, head.yMax]
        info["is_bold"] = bool(head.macStyle & 0x1)
        info["is_italic"] = bool(head.macStyle & 0x2)

    # hhea table
    if "hhea" in font:
        hhea = font["hhea"]
        info["hhea_ascent"] = hhea.ascent
        info["hhea_descent"] = hhea.descent

    # Character coverage
    codepoints = get_cmap_codepoints(font)
    info["unicode_coverage"] = len(codepoints)
    info["scripts"] = classify_scripts(codepoints)

    # OpenType features
    if "GPOS" in font:
        info["gpos_features"] = sorted(set(
            r.FeatureTag for r in font["GPOS"].table.FeatureList.FeatureRecord
        )) if font["GPOS"].table.FeatureList else []
    if "GSUB" in font:
        info["gsub_features"] = sorted(set(
            r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord
        )) if font["GSUB"].table.FeatureList else []

    # Variable font axes
    if "fvar" in font:
        info["variable"] = True
        info["axes"] = [
            {"tag": a.axisTag, "min": a.minValue, "default": a.defaultValue, "max": a.maxValue}
            for a in font["fvar"].axes
        ]
    else:
        info["variable"] = False

    font.close()
    return info


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def print_detail(info: dict) -> None:
    """Print detailed metrics for a single font."""
    if "error" in info:
        print(f"Error reading {info['file']}: {info['error']}")
        return

    print(f"{'=' * 60}")
    print(f"  {info.get('full_name', info['file'])}")
    print(f"{'=' * 60}")
    print(f"  Family:          {info.get('family', '—')}")
    print(f"  Subfamily:       {info.get('subfamily', '—')}")
    print(f"  Version:         {info.get('version', '—')}")
    print(f"  Designer:        {info.get('designer', '—')}")
    print(f"  Format:          {info['format']} (flavor: {info.get('flavor', '—')})")
    print(f"  File size:       {_fmt_size(info['file_size'])}")
    print(f"  Variable:        {'Yes' if info.get('variable') else 'No'}")

    if info.get("axes"):
        for ax in info["axes"]:
            print(f"    Axis {ax['tag']}: {ax['min']}..{ax['default']}..{ax['max']}")

    print()
    print(f"  Glyphs:          {info.get('glyph_count', '—')}")
    print(f"  Unicode coverage:{info.get('unicode_coverage', '—')} codepoints")
    print(f"  Units/EM:        {info.get('units_per_em', '—')}")
    print(f"  Weight:          {info.get('weight_name', '—')} ({info.get('weight_class', '—')})")
    print(f"  Width:           {info.get('width_name', '—')}")
    print(f"  Bold/Italic:     {'Bold ' if info.get('is_bold') else ''}{'Italic' if info.get('is_italic') else ''}" or "  Bold/Italic:     Neither")

    print()
    print(f"  Ascender:        {info.get('ascender', '—')}")
    print(f"  Descender:       {info.get('descender', '—')}")
    print(f"  Line gap:        {info.get('line_gap', '—')}")
    print(f"  Cap height:      {info.get('cap_height', '—')}")
    print(f"  x-height:        {info.get('x_height', '—')}")

    if info.get("scripts"):
        print()
        print("  Script coverage:")
        for script, count in sorted(info["scripts"].items(), key=lambda x: -x[1]):
            print(f"    {script:25s} {count:5d} chars")

    features = info.get("gsub_features", []) + info.get("gpos_features", [])
    if features:
        print()
        print(f"  OpenType features: {', '.join(sorted(set(features)))}")

    print()


def print_comparison(metrics_list: list[dict]) -> None:
    """Print a comparison table for multiple fonts."""
    valid = [m for m in metrics_list if "error" not in m]
    if not valid:
        print("No valid fonts to compare")
        return

    # Table header
    name_width = max(len(m.get("file", "")) for m in valid)
    name_width = max(name_width, 8)

    header = (f"{'File':<{name_width}}  {'Weight':>8}  {'Glyphs':>6}  "
              f"{'Unicode':>7}  {'Size':>8}  {'Variable':>8}")
    print(header)
    print("─" * len(header))

    for m in sorted(valid, key=lambda x: x.get("weight_class", 0)):
        var_str = "Yes" if m.get("variable") else "No"
        print(f"{m['file']:<{name_width}}  {m.get('weight_name', '—'):>8}  "
              f"{m.get('glyph_count', 0):>6}  "
              f"{m.get('unicode_coverage', 0):>7}  "
              f"{_fmt_size(m['file_size']):>8}  "
              f"{var_str:>8}")


def collect_fonts(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in FONT_EXTENSIONS else []
    return sorted(
        f for f in target.rglob("*")
        if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    )


def main():
    parser = argparse.ArgumentParser(description="Extract font metrics")
    parser.add_argument("path", type=Path, help="Font file or directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Show comparison table (for directories)")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: {args.path} does not exist", file=sys.stderr)
        sys.exit(1)

    fonts = collect_fonts(args.path)
    if not fonts:
        print("No font files found", file=sys.stderr)
        sys.exit(1)

    metrics_list = [extract_metrics(f) for f in fonts]

    if args.json:
        print(json.dumps(metrics_list if len(metrics_list) > 1 else metrics_list[0], indent=2))
    elif args.compare or (args.path.is_dir() and len(metrics_list) > 1):
        print_comparison(metrics_list)
    else:
        for m in metrics_list:
            print_detail(m)


if __name__ == "__main__":
    main()
