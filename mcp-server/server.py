#!/usr/bin/env python3
"""FontForge MCP Server.

Exposes font management operations as MCP tools for use with Claude Code
and other MCP-compatible clients.

Usage:
    python server.py                          # Start stdio server
    python server.py --fonts-dir /path/to/fonts  # Custom fonts directory
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from baseline import fit_win_metrics, shift_glyphs, shift_metrics
from build import FORMAT_EXTENSIONS, collect_fonts, convert_font, load_subset_codepoints
from fontTools.ttLib import TTFont
from hint import autohint, collect_ttfs, dehint
from kern import apply_spacing, extract_kerning, parse_spacing_rules
from mcp.server.fastmcp import FastMCP
from metrics import extract_metrics
from rename import process_path as rename_process
from strikes import BitmapStrikeGenerator
from variable import from_statics as variable_from_statics
from variable import is_variable

# Fonts directory resolution (precedence: --fonts-dir > $FONTFORGE_FONTS_DIR
# > in-repo fonts/). The env-var layer lets the same directory be shared by
# the MCP server, the per-script launch configs, and the user's shell, so
# moving fonts out of the workspace doesn't require editing config files.
_REPO_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
DEFAULT_FONTS_DIR = (
    Path(os.environ["FONTFORGE_FONTS_DIR"]).resolve()
    if os.environ.get("FONTFORGE_FONTS_DIR")
    else _REPO_FONTS_DIR
)

mcp = FastMCP(
    "fontforge",
    instructions=(
        "Font management tools for listing, analyzing, renaming, converting, and optimizing font files. "
        "Use list_families for an overview, get_metrics for detailed font info, "
        "rename_fonts to normalize filenames, build_fonts to convert formats, "
        "and build_bitmap_strikes to generate bitmap strikes for small-size rendering."
    ),
)


def _family_dir(family: str) -> Path | None:
    """Get the directory for a font family, or None if not found."""
    fonts_dir = DEFAULT_FONTS_DIR
    path = fonts_dir / family
    if path.is_dir():
        return path
    # Case-insensitive fallback
    for child in fonts_dir.iterdir():
        if child.is_dir() and child.name.lower() == family.lower():
            return child
    return None


@mcp.tool()
def list_families(detail: bool = False) -> str:
    """List all font families in the fonts directory.

    Args:
        detail: If true, include file counts and formats for each family.
    """
    fonts_dir = DEFAULT_FONTS_DIR
    families = []

    for child in sorted(fonts_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        fonts = collect_fonts(child)
        if not fonts:
            continue

        entry = {"name": child.name, "font_count": len(fonts)}
        if detail:
            formats = sorted(set(f.suffix.lstrip(".") for f in fonts))
            total_size = sum(f.stat().st_size for f in fonts)
            entry["formats"] = formats
            entry["total_size_bytes"] = total_size

        families.append(entry)

    return json.dumps(families, indent=2)


@mcp.tool()
def get_metrics(family: str, font_file: str | None = None, compare: bool = False) -> str:
    """Get detailed metrics for a font family or specific font file.

    Args:
        family: Font family name (directory name under fonts/).
        font_file: Specific font filename within the family. If omitted, returns all.
        compare: If true, return a compact comparison of all fonts in the family.
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    if font_file:
        target = family_path / font_file
        if not target.exists():
            return json.dumps({"error": f"File '{font_file}' not found in {family}"})
        return json.dumps(extract_metrics(target), indent=2)

    fonts = collect_fonts(family_path)
    metrics_list = [extract_metrics(f) for f in fonts]

    if compare:
        rows = []
        for m in sorted(metrics_list, key=lambda x: x.get("weight_class", 0)):
            if "error" in m:
                continue
            rows.append(
                {
                    "file": m["file"],
                    "weight": m.get("weight_name", "—"),
                    "glyphs": m.get("glyph_count", 0),
                    "unicode_coverage": m.get("unicode_coverage", 0),
                    "file_size": m.get("file_size", 0),
                    "variable": m.get("variable", False),
                }
            )
        return json.dumps(rows, indent=2)

    return json.dumps(metrics_list, indent=2)


@mcp.tool()
def rename_fonts(family: str, apply: bool = False) -> str:
    """Preview or apply filename normalization for a font family.

    Normalizes filenames to FamilyName-Weight.ext convention using
    the font's internal name table, falling back to filename parsing.

    Args:
        family: Font family name.
        apply: If true, actually rename files. Otherwise dry run.
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    results = rename_process(family_path, apply=apply)

    output = []
    for r in results:
        entry = {"file": r["path"].name, "action": r["action"]}
        if "new_name" in r:
            entry["new_name"] = r["new_name"]
        if "reason" in r:
            entry["reason"] = r["reason"]
        output.append(entry)

    return json.dumps(
        {
            "family": family,
            "applied": apply,
            "results": output,
        },
        indent=2,
    )


@mcp.tool()
def build_fonts(
    family: str,
    target_format: str = "woff2",
    subset: str | None = None,
) -> str:
    """Convert fonts in a family to a target format.

    Args:
        family: Font family name.
        target_format: Output format — woff2, woff, ttf, or otf.
        subset: Unicode subset — 'latin', 'cyrillic', 'latin+cyrillic', or U+XXXX ranges.
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    if target_format not in FORMAT_EXTENSIONS:
        return json.dumps(
            {"error": f"Invalid format '{target_format}'. Use: {list(FORMAT_EXTENSIONS.keys())}"}
        )

    fonts = collect_fonts(family_path)
    target_ext = FORMAT_EXTENSIONS[target_format]
    fonts = [f for f in fonts if f.suffix.lower() != target_ext]

    if not fonts:
        return json.dumps({"message": f"All fonts already in {target_format} format"})

    codepoints = load_subset_codepoints(subset, None)

    results = []
    for font_path in fonts:
        output = convert_font(font_path, family_path, target_format, codepoints, verbose=False)
        if output:
            results.append(
                {
                    "input": font_path.name,
                    "output": output.name,
                    "input_size": font_path.stat().st_size,
                    "output_size": output.stat().st_size,
                }
            )
        else:
            results.append({"input": font_path.name, "error": "conversion failed"})

    return json.dumps(
        {
            "family": family,
            "format": target_format,
            "subset": subset,
            "results": results,
        },
        indent=2,
    )


@mcp.tool()
def search_fonts(query: str) -> str:
    """Search for fonts by name, weight, or designer.

    Args:
        query: Search term (matches against family name, subfamily, designer, full name).
    """
    fonts_dir = DEFAULT_FONTS_DIR
    query_lower = query.lower()
    matches = []

    for family_dir in sorted(fonts_dir.iterdir()):
        if not family_dir.is_dir() or family_dir.name.startswith("."):
            continue
        fonts = collect_fonts(family_dir)
        for font_path in fonts:
            info = extract_metrics(font_path)
            if "error" in info:
                continue

            searchable = " ".join(
                [
                    info.get("family", ""),
                    info.get("subfamily", ""),
                    info.get("full_name", ""),
                    info.get("designer", ""),
                    font_path.name,
                ]
            ).lower()

            if query_lower in searchable:
                matches.append(
                    {
                        "family_dir": family_dir.name,
                        "file": font_path.name,
                        "full_name": info.get("full_name", ""),
                        "weight": info.get("weight_name", ""),
                        "designer": info.get("designer", ""),
                    }
                )

    return json.dumps(matches, indent=2)


@mcp.tool()
def dump_kerning(family: str, font_file: str) -> str:
    """Extract kerning pairs from a specific font as CSV rows.

    Reads both the legacy `kern` table and modern GPOS pair-adjustment lookups
    and flattens class-based kerning into explicit pairs.

    Args:
        family: Font family name.
        font_file: Specific font filename within the family (.ttf or .otf).
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})
    target = family_path / font_file
    if not target.exists():
        return json.dumps({"error": f"File '{font_file}' not found in {family}"})

    font = TTFont(target)
    pairs = extract_kerning(font)
    font.close()

    return json.dumps(
        {
            "family": family,
            "font": font_file,
            "pair_count": len(pairs),
            "pairs": [{"left": l, "right": r, "value": v} for l, r, v in pairs],
        },
        indent=2,
    )


@mcp.tool()
def adjust_spacing(family: str, spec: str, suffix: str = "-spaced") -> str:
    """Adjust advance widths across a font family by glyph class.

    Args:
        family: Font family name.
        spec: Rules like 'lc:+10,uc:-5'. Classes: lc/uc/digits/all; or 'A-Z'
            ranges; or /regex/ patterns; or literal comma lists.
        suffix: Suffix for the output filenames (default: -spaced).
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    try:
        parse_spacing_rules(spec)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    fonts = [f for f in collect_fonts(family_path) if f.suffix.lower() in {".ttf", ".otf"}]
    results = []
    for f in fonts:
        out = f.with_stem(f.stem + suffix)
        touched = apply_spacing(f, spec, out)
        results.append({"input": f.name, "output": out.name, "adjusted": touched})

    return json.dumps({"family": family, "spec": spec, "results": results}, indent=2)


@mcp.tool()
def hint_family(
    family: str,
    range_min: int = 8,
    range_max: int = 50,
    script: str = "latn",
    strong: bool = False,
    dehint_mode: bool = False,
    suffix: str = "-hinted",
) -> str:
    """Auto-hint (or dehint) all TTFs in a family via ttfautohint.

    Args:
        family: Font family name.
        range_min: Minimum PPEM for hinting (default 8).
        range_max: Maximum PPEM for hinting (default 50).
        script: Fallback script tag (default 'latn').
        strong: Use strong stem widths for GDI/DirectWrite.
        dehint_mode: If true, strip existing hints instead of adding them.
        suffix: Output filename suffix (default: -hinted or -dehinted).
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    ttfs = collect_ttfs(family_path)
    if not ttfs:
        return json.dumps({"error": f"No TTF files in {family}"})

    if dehint_mode and suffix == "-hinted":
        suffix = "-dehinted"

    results = []
    for f in ttfs:
        out = f.with_stem(f.stem + suffix)
        ok = (
            dehint(f, out)
            if dehint_mode
            else autohint(f, out, range_min, range_max, script, strong)
        )
        results.append(
            {
                "input": f.name,
                "output": out.name if ok else None,
                "success": ok,
                "input_size": f.stat().st_size,
                "output_size": out.stat().st_size if ok and out.exists() else None,
            }
        )

    return json.dumps(
        {
            "family": family,
            "mode": "dehint" if dehint_mode else "hint",
            "results": results,
        },
        indent=2,
    )


@mcp.tool()
def variable_info(family: str, font_file: str) -> str:
    """Report axes and named instances of a variable font.

    Args:
        family: Font family name.
        font_file: Variable font filename (.ttf).
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})
    target = family_path / font_file
    if not target.exists():
        return json.dumps({"error": f"File '{font_file}' not found in {family}"})

    font = TTFont(target)
    if not is_variable(font):
        font.close()
        return json.dumps({"variable": False, "font": font_file})

    fvar = font["fvar"]
    name = font["name"]
    axes = [
        {
            "tag": a.axisTag,
            "min": a.minValue,
            "default": a.defaultValue,
            "max": a.maxValue,
        }
        for a in fvar.axes
    ]

    instances = []
    for inst in fvar.instances:
        record = name.getName(inst.subfamilyNameID, 3, 1, 0x409)
        instances.append(
            {
                "name": str(record) if record else None,
                "coordinates": dict(inst.coordinates),
            }
        )
    font.close()

    return json.dumps(
        {
            "variable": True,
            "font": font_file,
            "axes": axes,
            "instances": instances,
        },
        indent=2,
    )


@mcp.tool()
def build_variable(family: str, output_name: str | None = None, axis_tag: str = "wght") -> str:
    """Build a variable font by interpolating the static masters in a family.

    Static TTFs are ordered by usWeightClass. Incompatible glyphs are skipped
    with warnings; the build succeeds on the compatible subset.

    Args:
        family: Font family name.
        output_name: Output filename (default: '<Family>-VF.ttf').
        axis_tag: Axis tag for the variation (default 'wght').
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    ttfs = [f for f in collect_ttfs(family_path) if "-VF" not in f.stem]
    if len(ttfs) < 2:
        return json.dumps({"error": f"Need >=2 static TTFs in {family}, found {len(ttfs)}"})

    out = family_path / (output_name or f"{family}-VF.ttf")
    try:
        variable_from_statics(ttfs, out, axis_tag)
    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps(
        {
            "family": family,
            "masters": [f.name for f in ttfs],
            "output": out.name,
            "output_size": out.stat().st_size,
        },
        indent=2,
    )


@mcp.tool()
def shift_baseline(
    family: str,
    shift: int,
    fit_win_metrics_flag: bool = True,
    suffix: str = "-shifted",
) -> str:
    """Translate all glyphs vertically and sync every vertical metric.

    Moves glyph outlines by `shift` font units and adjusts hhea + OS/2 typo
    metrics to match. Also refits OS/2 win metrics to cover the full glyph
    bbox so Windows GDI doesn't clip descenders (on by default).

    Args:
        family: Font family name.
        shift: Y-translation in font units. Negative = down, positive = up.
        fit_win_metrics_flag: Refit win metrics to glyph bbox (default True).
        suffix: Output filename suffix (default '-shifted').
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    ttfs = [
        f for f in collect_ttfs(family_path) if f.parent == family_path
    ]  # shallow only — skip derivative subdirs
    if not ttfs:
        return json.dumps({"error": f"No TTF files directly under {family}"})

    results = []
    for f in ttfs:
        try:
            font = TTFont(f)
            if shift != 0:
                shift_glyphs(font, shift)
                shift_metrics(font, shift)
            if fit_win_metrics_flag:
                fit_win_metrics(font)
            out = f.with_stem(f.stem + suffix)
            font.save(str(out))
            font.close()
            results.append({"input": f.name, "output": out.name, "shift": shift})
        except Exception as e:
            results.append({"input": f.name, "error": str(e)})

    return json.dumps(
        {
            "family": family,
            "shift": shift,
            "fit_win_metrics": fit_win_metrics_flag,
            "results": results,
        },
        indent=2,
    )


@mcp.tool()
def build_bitmap_strikes(
    family: str,
    sizes_96dpi: list[int] | None = None,
    sizes_120dpi: list[int] | None = None,
    ppem: list[int] | None = None,
) -> str:
    """Generate bitmap strikes for a font family using FreeType.

    Bitmap strikes provide pre-rasterized glyphs at specific sizes for improved
    rendering at small point sizes.

    Args:
        family: Font family name.
        sizes_96dpi: Point sizes for 96 DPI displays. Defaults to [15].
        sizes_120dpi: Point sizes for 120 DPI displays. Defaults to [12].
        ppem: Direct pixel sizes (PPEM). Defaults to [20].
    """
    family_path = _family_dir(family)
    if not family_path:
        return json.dumps({"error": f"Family '{family}' not found"})

    ttfs = [f for f in collect_fonts(family_path) if f.suffix.lower() in {".ttf", ".otf"}]
    if not ttfs:
        return json.dumps({"error": f"No fonts found in {family}"})

    generator = BitmapStrikeGenerator(verbose=False)

    # Use defaults if not specified
    if sizes_96dpi is None:
        sizes_96dpi = generator.SIZES_96DPI
    if sizes_120dpi is None:
        sizes_120dpi = generator.SIZES_120DPI
    if ppem is None:
        ppem = generator.PIXEL_SIZES

    results = []
    for font_path in ttfs:
        success = generator.generate_strikes(
            font_path,
            sizes_96dpi=sizes_96dpi,
            sizes_120dpi=sizes_120dpi,
            pixel_sizes=ppem,
            output_path=None,  # Use default strikes/ subdirectory
        )
        results.append(
            {
                "input": font_path.name,
                "success": success,
                "sizes_96dpi": sizes_96dpi,
                "sizes_120dpi": sizes_120dpi,
                "ppem": ppem,
            }
        )

    return json.dumps(
        {
            "family": family,
            "results": results,
            "note": "For actual bitmap generation, install freetype-py: pip install freetype-py",
        },
        indent=2,
    )


def main():
    parser = argparse.ArgumentParser(description="FontForge MCP Server")
    parser.add_argument(
        "--fonts-dir", type=Path, default=None, help="Override default fonts directory"
    )
    args = parser.parse_args()

    if args.fonts_dir:
        global DEFAULT_FONTS_DIR
        DEFAULT_FONTS_DIR = args.fonts_dir.resolve()

    mcp.run()


if __name__ == "__main__":
    main()
