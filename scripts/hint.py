#!/usr/bin/env python3
"""TrueType auto-hinting via ttfautohint.

Wraps the `ttfautohint` binary for batch hinting of TTF files, with support
for dehinting (stripping existing instructions) and common tuning knobs.

Usage:
    python hint.py <font>                           # Auto-hint with defaults
    python hint.py <font> --range 8-60              # Custom PPEM range
    python hint.py <font> --script latn --strong    # Latin, strong stems
    python hint.py <directory>                      # Hint all TTFs in dir
    python hint.py <font> --dehint                  # Strip all hints
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".ttf"}


def find_ttfautohint() -> str:
    """Locate the ttfautohint binary or exit with an install hint."""
    path = shutil.which("ttfautohint")
    if not path:
        print("Error: ttfautohint not found. Install via `brew install ttfautohint`.",
              file=sys.stderr)
        sys.exit(1)
    return path


def autohint(
    input_path: Path,
    output_path: Path,
    range_min: int = 8,
    range_max: int = 50,
    fallback_script: str = "latn",
    strong: bool = False,
    composites: bool = False,
    verbose: bool = False,
) -> bool:
    """Run ttfautohint with the given options. Returns True on success."""
    cmd = [
        find_ttfautohint(),
        f"--hinting-range-min={range_min}",
        f"--hinting-range-max={range_max}",
        f"--fallback-script={fallback_script}",
    ]
    if strong:
        # DGW = Default rendering, GDI ClearType, DirectWrite ClearType.
        # Strong stems snap to pixel boundaries in those modes for crisper
        # small-size rendering at the cost of shape fidelity.
        cmd.append("--strong-stem-width=DGW")
    if composites:
        cmd.append("--composites")
    cmd += [str(input_path), str(output_path)]

    if verbose:
        print(f"  $ {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  {input_path.name}: FAILED", file=sys.stderr)
        if result.stderr:
            print(f"    {result.stderr.strip()}", file=sys.stderr)
        return False

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    delta = (out_size - in_size) / in_size * 100
    print(f"  {input_path.name} -> {output_path.name} [{delta:+.1f}% size]")
    return True


def dehint(input_path: Path, output_path: Path) -> bool:
    """Strip TrueType instruction tables to produce an unhinted font."""
    font = TTFont(input_path)
    # prep = pre-program, fpgm = font program, cvt = control values;
    # hdmx/LTSH/VDMX are derived device-metric caches that only make sense
    # when hints exist. Dropping all of them yields a clean unhinted TTF.
    for tag in ("prep", "fpgm", "cvt ", "hdmx", "LTSH", "VDMX"):
        if tag in font:
            del font[tag]
    # Composite glyphs have no program attr, so the hasattr guard matters.
    if "glyf" in font:
        glyf = font["glyf"]
        for name in font.getGlyphOrder():
            glyph = glyf[name]
            if hasattr(glyph, "program"):
                glyph.program.fromBytecode(b"")
    font.save(str(output_path))
    font.close()
    print(f"  {input_path.name} -> {output_path.name} [dehinted]")
    return True


def collect_ttfs(target: Path) -> list[Path]:
    """Resolve a file or directory to a sorted list of .ttf paths."""
    if target.is_file():
        return [target] if target.suffix.lower() in FONT_EXTENSIONS else []
    return sorted(
        f for f in target.rglob("*")
        if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    )


def parse_range(spec: str) -> tuple[int, int]:
    """Parse 'min-max' PPEM range."""
    if "-" not in spec:
        raise ValueError(f"Range must be 'min-max', got {spec!r}")
    lo, hi = spec.split("-", 1)
    return int(lo), int(hi)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-hint TTF files via ttfautohint")
    parser.add_argument("input", type=Path, help="Font file or directory")
    parser.add_argument("-o", "--output-dir", type=Path, default=None,
                        help="Output directory (default: alongside input with -hinted suffix)")
    parser.add_argument("--range", dest="range_spec", default="8-50",
                        help="Hinting PPEM range, e.g. '8-50' (default)")
    parser.add_argument("--script", default="latn",
                        help="Fallback script tag (default: latn)")
    parser.add_argument("--strong", action="store_true",
                        help="Use strong stem widths for D/GDI/DirectWrite")
    parser.add_argument("--composites", action="store_true",
                        help="Hint composite glyphs as a whole (default: hint components)")
    parser.add_argument("--dehint", action="store_true",
                        help="Strip existing hints instead of adding them")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} does not exist", file=sys.stderr)
        sys.exit(1)

    fonts = collect_ttfs(args.input)
    if not fonts:
        print("No TTF files found", file=sys.stderr)
        sys.exit(1)

    range_min, range_max = parse_range(args.range_spec)

    suffix = "-dehinted" if args.dehint else "-hinted"
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    action = "Dehinting" if args.dehint else "Hinting"
    print(f"{action} {len(fonts)} font(s)")

    success = 0
    for f in fonts:
        out_dir = args.output_dir or f.parent
        out = out_dir / f"{f.stem}{suffix}{f.suffix}"
        ok = (dehint(f, out) if args.dehint
              else autohint(f, out, range_min, range_max, args.script,
                            args.strong, args.composites, args.verbose))
        if ok:
            success += 1

    print(f"\nDone: {success}/{len(fonts)} processed")


if __name__ == "__main__":
    main()
