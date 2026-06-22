#!/usr/bin/env python3
"""Font build and conversion utility.

Converts font files between formats (TTF/OTF -> WOFF2), applies subsetting,
and handles compression using fonttools with brotli/zopfli backends.

Usage:
    python build.py <input>                        # Convert to WOFF2
    python build.py <input> --format ttf           # Convert to TTF
    python build.py <input> --output-dir ./out      # Specify output directory
    python build.py <input> --subset "latin"        # Subset to Latin characters
    python build.py <input> --subset-file chars.txt # Subset from character list file
    python build.py <directory>                     # Convert all fonts in directory
"""

import argparse
import sys
from pathlib import Path

from fontTools.subset import Options as SubsetOptions
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}
FORMAT_EXTENSIONS = {"woff2": ".woff2", "woff": ".woff", "ttf": ".ttf", "otf": ".otf"}

# Named Unicode ranges for common subsets
UNICODE_RANGES = {
    "latin": "U+0000-007F,U+00A0-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
    "latin-ext": "U+0100-024F,U+0259,U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20CF,U+2113,U+2C60-2C7F,U+A720-A7FF",
    "cyrillic": "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116",
    "greek": "U+0370-03FF",
    "vietnamese": "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+1EA0-1EF9,U+20AB",
}


def parse_unicode_ranges(range_str: str) -> list[int]:
    """Parse Unicode range strings like 'U+0041-005A,U+0061' into codepoints."""
    codepoints = set()
    for part in range_str.split(","):
        part = part.strip().replace("U+", "").replace("u+", "")
        if "-" in part:
            start, end = part.split("-", 1)
            codepoints.update(range(int(start, 16), int(end, 16) + 1))
        else:
            codepoints.add(int(part, 16))
    return sorted(codepoints)


def load_subset_codepoints(subset_arg: str | None, subset_file: Path | None) -> list[int] | None:
    """Resolve subset specification to a list of codepoints."""
    if subset_arg:
        # Check if it's a named range
        if subset_arg.lower() in UNICODE_RANGES:
            return parse_unicode_ranges(UNICODE_RANGES[subset_arg.lower()])
        # Raw Unicode range string. Check before "+" because "U+0041"
        # contains plus signs but is not a named-range combination.
        if "U+" in subset_arg.upper():
            return parse_unicode_ranges(subset_arg)
        # Multiple named ranges separated by +
        if "+" in subset_arg:
            codepoints = set()
            for name in subset_arg.split("+"):
                name = name.strip().lower()
                if name in UNICODE_RANGES:
                    codepoints.update(parse_unicode_ranges(UNICODE_RANGES[name]))
                else:
                    print(f"Warning: unknown range '{name}', skipping", file=sys.stderr)
            return sorted(codepoints) if codepoints else None

    if subset_file:
        text = subset_file.read_text(encoding="utf-8")
        return sorted(set(ord(c) for c in text if not c.isspace()))

    return None


def convert_font(
    input_path: Path,
    output_dir: Path,
    target_format: str = "woff2",
    codepoints: list[int] | None = None,
    verbose: bool = False,
) -> Path | None:
    """Convert a single font file to the target format, optionally subsetting."""
    try:
        font = TTFont(input_path)
    except Exception as e:
        print(f"Error reading {input_path.name}: {e}", file=sys.stderr)
        return None

    # Apply subsetting if requested
    if codepoints:
        # Drop tables fontTools can't subset. They'd otherwise emit a
        # "NOT subset; dropped" warning on every font. None are useful for
        # web output: morx/mort/feat are Apple-only layout, FFTM is a
        # FontForge-internal build timestamp.
        for tag in ("morx", "mort", "feat", "FFTM"):
            if tag in font:
                del font[tag]

        options = SubsetOptions()
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        # Preserve the .notdef outline so the subset font still renders a
        # visible box for missing glyphs instead of a zero-width blank.
        options.notdef_outline = True
        subsetter = Subsetter(options=options)
        subsetter.populate(unicodes=codepoints)
        try:
            subsetter.subset(font)
        except Exception as e:
            print(f"Error subsetting {input_path.name}: {e}", file=sys.stderr)
            font.close()
            return None

    # Determine output path
    ext = FORMAT_EXTENSIONS[target_format]
    output_path = output_dir / (input_path.stem + ext)

    # Set flavor for web formats
    if target_format == "woff2":
        font.flavor = "woff2"
    elif target_format == "woff":
        font.flavor = "woff"
    else:
        font.flavor = None

    try:
        font.save(str(output_path))
    except Exception as e:
        print(f"Error saving {output_path.name}: {e}", file=sys.stderr)
        font.close()
        return None

    font.close()

    input_size = input_path.stat().st_size
    output_size = output_path.stat().st_size
    ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0

    if verbose:
        print(
            f"  {input_path.name} ({_fmt_size(input_size)}) -> "
            f"{output_path.name} ({_fmt_size(output_size)}) "
            f"[{ratio:+.1f}%]"
        )
    else:
        print(f"  {input_path.name} -> {output_path.name} [{ratio:+.1f}%]")

    return output_path


def _fmt_size(n: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def collect_fonts(target: Path) -> list[Path]:
    """Collect font files from a path."""
    if target.is_file():
        return [target] if target.suffix.lower() in FONT_EXTENSIONS else []
    return sorted(
        f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/convert font files")
    parser.add_argument("input", type=Path, help="Font file or directory")
    parser.add_argument(
        "--format",
        "-f",
        default="woff2",
        choices=list(FORMAT_EXTENSIONS.keys()),
        help="Target format (default: woff2)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Output directory (default: same as input)",
    )
    parser.add_argument(
        "--subset",
        "-s",
        default=None,
        help="Subset: named range (latin, cyrillic, etc.), "
        "combined (latin+cyrillic), or U+XXXX ranges",
    )
    parser.add_argument(
        "--subset-file", type=Path, default=None, help="File containing characters to keep"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show file sizes")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} does not exist", file=sys.stderr)
        sys.exit(1)

    fonts = collect_fonts(args.input)
    if not fonts:
        print("No font files found", file=sys.stderr)
        sys.exit(1)

    # Skip fonts already in target format
    target_ext = FORMAT_EXTENSIONS[args.format]
    fonts = [f for f in fonts if f.suffix.lower() != target_ext]
    if not fonts:
        print(f"All fonts are already in {args.format} format")
        return

    codepoints = load_subset_codepoints(args.subset, args.subset_file)

    output_dir = args.output_dir or (args.input if args.input.is_dir() else args.input.parent)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Converting {len(fonts)} font(s) to {args.format}"
        + (f" (subset: {args.subset or 'custom'})" if codepoints else "")
    )

    success = 0
    for font_path in fonts:
        result = convert_font(font_path, output_dir, args.format, codepoints, args.verbose)
        if result:
            success += 1

    print(f"\nDone: {success}/{len(fonts)} converted")


if __name__ == "__main__":
    main()
