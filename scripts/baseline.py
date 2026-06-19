#!/usr/bin/env python3
"""Baseline shift and vertical metric adjustments.

Translates all glyph outlines vertically and keeps every vertical metric
(OS/2 typo, OS/2 win, hhea) consistent with the shift. Also fixes win
metrics to cover the full glyph bbox so Windows GDI doesn't clip.

Usage:
    python baseline.py <font> --shift -40                   # Move glyphs 40u down
    python baseline.py <font> --shift +30 -o out.ttf        # Move up, custom output
    python baseline.py <directory> --shift -40              # Batch shift a family
    python baseline.py <font> --fit-win-metrics             # Only refit win metrics
    python baseline.py <font> --shift -40 --no-fit-win      # Skip auto-fit
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".ttf"}


def shift_glyphs(font: TTFont, shift: int) -> None:
    """Translate all glyf contours by `shift` y-units.

    Composites inherit the shift automatically because their base glyphs'
    coordinates have already moved. Adding `shift` to `component.y` on top
    of that would double-shift the composite (e.g. Aacute ending up at
    -80u when we asked for -40u), so composites are deliberately skipped.
    """
    if "glyf" not in font:
        raise ValueError("Only TTF (glyf) fonts are supported; got CFF/OTF")

    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.numberOfContours > 0:
            for i, (x, y) in enumerate(glyph.coordinates):
                glyph.coordinates[i] = (x, y + shift)
            glyph.recalcBounds(glyf)


def shift_metrics(font: TTFont, shift: int) -> None:
    """Move vertical metrics by the same amount as the glyph shift."""
    hhea = font["hhea"]
    hhea.ascender += shift
    hhea.descender += shift

    os2 = font["OS/2"]
    os2.sTypoAscender += shift
    os2.sTypoDescender += shift
    # usWin* are unsigned magnitudes; we refit them below, so leave as-is here.


def fit_win_metrics(font: TTFont) -> tuple[int, int]:
    """Set usWinAscent/Descent to cover the full glyph bbox.

    Returns the (ascent, descent) applied. Without this, any glyph whose
    extent exceeds the current win metrics gets clipped on Windows GDI.
    """
    # Refresh every glyph's cached bounds before reading. Composites' stored
    # xMin/yMin/xMax/yMax stay pinned to the pre-shift values they were loaded
    # with — fontTools only recomputes them at save time — so reading them raw
    # would miss any extreme that only propagates through a scaled component.
    # recalcBounds handles simples and composites uniformly; boundsDone memoizes
    # across the composite graph so a shared base is only measured once.
    head = font["head"]
    glyf = font["glyf"]
    bounds_done: set[str] = set()
    xMin = yMin = 1 << 31
    xMax = yMax = -(1 << 31)
    for name in font.getGlyphOrder():
        g = glyf[name]
        g.recalcBounds(glyf, boundsDone=bounds_done)
        if g.numberOfContours == 0:
            continue
        if g.xMin < xMin:
            xMin = g.xMin
        if g.yMin < yMin:
            yMin = g.yMin
        if g.xMax > xMax:
            xMax = g.xMax
        if g.yMax > yMax:
            yMax = g.yMax
    head.xMin, head.yMin, head.xMax, head.yMax = xMin, yMin, xMax, yMax

    os2 = font["OS/2"]
    # usWinAscent/Descent are unsigned magnitudes: descent below the baseline
    # is stored as a positive number, so we negate yMin. We only grow the
    # values (via max) so an already-generous clip region isn't tightened.
    os2.usWinAscent = max(os2.usWinAscent, yMax)
    os2.usWinDescent = max(os2.usWinDescent, -yMin)
    return os2.usWinAscent, os2.usWinDescent


def process_font(
    input_path: Path,
    output_path: Path,
    shift: int,
    do_fit_win: bool,
    verbose: bool,
) -> bool:
    """Apply shift and/or win-metrics refit to one font, save to output. Returns True on success."""
    try:
        font = TTFont(input_path)
    except Exception as e:
        print(f"  {input_path.name}: failed to open ({e})", file=sys.stderr)
        return False

    if shift != 0:
        try:
            shift_glyphs(font, shift)
            shift_metrics(font, shift)
        except ValueError as e:
            print(f"  {input_path.name}: {e}", file=sys.stderr)
            font.close()
            return False

    if do_fit_win:
        win_asc, win_desc = fit_win_metrics(font)
        if verbose:
            print(f"    fit win: ascent={win_asc} descent={win_desc}")

    font.save(str(output_path))
    font.close()

    note = []
    if shift != 0:
        note.append(f"shift {shift:+d}u")
    if do_fit_win:
        note.append("win-fit")
    print(f"  {input_path.name} -> {output_path.name} [{', '.join(note) or 'no-op'}]")
    return True


def collect_ttfs(target: Path) -> list[Path]:
    """Resolve a file or directory to a sorted list of .ttf paths."""
    if target.is_file():
        return [target] if target.suffix.lower() in FONT_EXTENSIONS else []
    return sorted(
        f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline shift + vertical metric tuning")
    parser.add_argument("input", type=Path, help="Font file or directory")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: alongside input with -shifted suffix)",
    )
    parser.add_argument(
        "--shift",
        type=int,
        default=0,
        help="Y-translation in font units. Negative = down, positive = up",
    )
    # --fit-win-metrics and --no-fit-win are mutually exclusive: one asks to
    # force the refit, the other asks to skip it. argparse raises cleanly on
    # both-supplied rather than silently letting the explicit-on win.
    win_group = parser.add_mutually_exclusive_group()
    win_group.add_argument(
        "--fit-win-metrics",
        action="store_true",
        help="Refit OS/2 win metrics to cover the glyph bbox (prevents Windows clipping)",
    )
    win_group.add_argument(
        "--no-fit-win",
        action="store_true",
        help="Skip auto-fit of win metrics (by default fit runs whenever --shift is nonzero)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.shift == 0 and not args.fit_win_metrics:
        print("Error: nothing to do — pass --shift N or --fit-win-metrics", file=sys.stderr)
        sys.exit(2)

    if args.shift != 0 and args.no_fit_win:
        # Outlines move but usWinAscent/Descent stay pinned to pre-shift
        # magnitudes, so any descender that crossed the old clip region is
        # now invisible on Windows GDI. Warn loudly — this combo is only
        # correct when the caller is about to refit win metrics elsewhere.
        print(
            f"Warning: --shift {args.shift:+d} with --no-fit-win leaves OS/2 "
            "usWinAscent/Descent unchanged. Descenders that now extend past "
            "the original win clip region will render truncated on Windows GDI.",
            file=sys.stderr,
        )

    if not args.input.exists():
        print(f"Error: {args.input} does not exist", file=sys.stderr)
        sys.exit(1)

    fonts = collect_ttfs(args.input)
    if not fonts:
        print("No TTF files found", file=sys.stderr)
        sys.exit(1)

    do_fit_win = args.fit_win_metrics or (args.shift != 0 and not args.no_fit_win)

    action = f"shift {args.shift:+d}u" if args.shift else "win-metrics refit"
    print(f"Processing {len(fonts)} font(s) [{action}]")

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for f in fonts:
        out_dir = args.output_dir or f.parent
        suffix = "-shifted" if args.shift else "-winfit"
        out = out_dir / f"{f.stem}{suffix}{f.suffix}"
        if process_font(f, out, args.shift, do_fit_win, args.verbose):
            success += 1

    print(f"\nDone: {success}/{len(fonts)} processed")


if __name__ == "__main__":
    main()
