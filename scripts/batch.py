#!/usr/bin/env python3
"""Batch font operations utility.

Runs rename, build, and metrics operations across multiple font families
with summary reporting.

Usage:
    python batch.py fonts/                           # Full report of all families
    python batch.py fonts/ --rename --apply           # Rename all fonts
    python batch.py fonts/ --build --format woff2     # Convert all to WOFF2
    python batch.py fonts/ --metrics --json            # Metrics for all as JSON
    python batch.py fonts/ --rename --build --apply    # Rename then build
    python batch.py fonts/ --families Burbank,GGSans   # Only specific families
"""

import argparse
import json
import sys
import time
from pathlib import Path

from rename import process_path as rename_process, FONT_EXTENSIONS
from build import convert_font, load_subset_codepoints, FORMAT_EXTENSIONS, collect_fonts
from metrics import extract_metrics, print_comparison, _fmt_size


def discover_families(fonts_dir: Path, filter_names: list[str] | None = None) -> dict[str, Path]:
    """Discover font families as top-level subdirectories."""
    families = {}
    for child in sorted(fonts_dir.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            if filter_names and child.name not in filter_names:
                continue
            # Check if directory has any font files
            has_fonts = any(
                f.suffix.lower() in FONT_EXTENSIONS
                for f in child.rglob("*") if f.is_file()
            )
            if has_fonts:
                families[child.name] = child
    return families


def batch_report(families: dict[str, Path]) -> None:
    """Print a summary report of all font families."""
    print(f"{'Family':<25} {'Fonts':>5} {'Glyphs':>7} {'Formats':>15} {'Size':>10}")
    print("─" * 65)

    total_files = 0
    total_size = 0

    for name, family_dir in families.items():
        fonts = collect_fonts(family_dir)
        if not fonts:
            continue

        formats = set()
        family_size = 0
        glyph_count = 0

        for f in fonts:
            formats.add(f.suffix.lstrip(".").upper())
            family_size += f.stat().st_size

        # Get glyph count from first font
        info = extract_metrics(fonts[0])
        glyph_count = info.get("glyph_count", 0)

        fmt_str = ", ".join(sorted(formats))
        print(f"{name:<25} {len(fonts):>5} {glyph_count:>7} {fmt_str:>15} {_fmt_size(family_size):>10}")

        total_files += len(fonts)
        total_size += family_size

    print("─" * 65)
    print(f"{'Total':<25} {total_files:>5} {'':>7} {'':>15} {_fmt_size(total_size):>10}")


def batch_rename(families: dict[str, Path], apply: bool = False, verbose: bool = False) -> dict:
    """Run rename across all families."""
    summary = {"renamed": 0, "skipped": 0, "conflicts": 0, "errors": 0}

    action = "Renaming" if apply else "Previewing renames for"

    for name, family_dir in families.items():
        print(f"\n[{name}] {action}...")
        results = rename_process(family_dir, apply=apply, verbose=verbose)

        for r in results:
            if r["action"] in ("renamed", "preview"):
                summary["renamed"] += 1
                print(f"  {r['path'].name} -> {r['new_name']}")
            elif r["action"] == "skip":
                summary["skipped"] += 1
            elif r["action"] == "conflict":
                summary["conflicts"] += 1
                print(f"  CONFLICT: {r['path'].name} -> {r['new_name']}")

    return summary


def batch_build(
    families: dict[str, Path],
    target_format: str = "woff2",
    output_dir: Path | None = None,
    subset: str | None = None,
    subset_file: Path | None = None,
    verbose: bool = False,
) -> dict:
    """Run build/convert across all families."""
    summary = {"converted": 0, "failed": 0, "skipped": 0}
    codepoints = load_subset_codepoints(subset, subset_file)
    target_ext = FORMAT_EXTENSIONS[target_format]

    for name, family_dir in families.items():
        fonts = collect_fonts(family_dir)
        # Skip fonts already in target format
        to_convert = [f for f in fonts if f.suffix.lower() != target_ext]
        if not to_convert:
            summary["skipped"] += len(fonts)
            continue

        out = output_dir / name if output_dir else family_dir
        out.mkdir(parents=True, exist_ok=True)

        print(f"\n[{name}] Converting {len(to_convert)} font(s) to {target_format}...")

        for font_path in to_convert:
            result = convert_font(font_path, out, target_format, codepoints, verbose)
            if result:
                summary["converted"] += 1
            else:
                summary["failed"] += 1

    return summary


def batch_metrics(
    families: dict[str, Path],
    as_json: bool = False,
    compare: bool = False,
) -> None:
    """Run metrics across all families."""
    all_metrics = {}

    for name, family_dir in families.items():
        fonts = collect_fonts(family_dir)
        metrics_list = [extract_metrics(f) for f in fonts]
        all_metrics[name] = metrics_list

    if as_json:
        print(json.dumps(all_metrics, indent=2))
    elif compare:
        for name, metrics_list in all_metrics.items():
            print(f"\n{'=' * 60}")
            print(f"  {name}")
            print(f"{'=' * 60}")
            print_comparison(metrics_list)
    else:
        # Summary view
        batch_report({n: families[n] for n in all_metrics})


def main():
    parser = argparse.ArgumentParser(description="Batch font operations")
    parser.add_argument("path", type=Path, help="Fonts directory")
    parser.add_argument("--families", "-f", default=None,
                        help="Comma-separated list of family names to process")

    # Operations
    parser.add_argument("--rename", action="store_true", help="Run rename operation")
    parser.add_argument("--build", action="store_true", help="Run build/convert operation")
    parser.add_argument("--metrics", action="store_true", help="Run metrics extraction")

    # Shared options
    parser.add_argument("--apply", action="store_true", help="Apply changes (rename/build)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Build options
    parser.add_argument("--format", default="woff2",
                        choices=list(FORMAT_EXTENSIONS.keys()),
                        help="Target format for build (default: woff2)")
    parser.add_argument("--output-dir", "-o", type=Path, default=None,
                        help="Output directory for build")
    parser.add_argument("--subset", "-s", default=None,
                        help="Subset specification for build")
    parser.add_argument("--subset-file", type=Path, default=None,
                        help="File with characters to keep")

    # Metrics options
    parser.add_argument("--json", action="store_true", help="Output metrics as JSON")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Show per-family comparison tables")

    args = parser.parse_args()

    if not args.path.exists() or not args.path.is_dir():
        print(f"Error: {args.path} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    filter_names = args.families.split(",") if args.families else None
    families = discover_families(args.path, filter_names)

    if not families:
        print("No font families found", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(families)} font families")

    # If no operation specified, show summary report
    if not (args.rename or args.build or args.metrics):
        batch_report(families)
        return

    start = time.time()

    if args.rename:
        if not args.apply:
            print("\nDRY RUN — use --apply to rename files")
        summary = batch_rename(families, apply=args.apply, verbose=args.verbose)
        would = "Renamed" if args.apply else "Would rename"
        print(f"\nRename summary: {would} {summary['renamed']}, "
              f"skipped {summary['skipped']}, conflicts {summary['conflicts']}")

    if args.build:
        summary = batch_build(
            families, args.format, args.output_dir,
            args.subset, args.subset_file, args.verbose,
        )
        print(f"\nBuild summary: converted {summary['converted']}, "
              f"failed {summary['failed']}, skipped {summary['skipped']}")

    if args.metrics:
        batch_metrics(families, as_json=args.json, compare=args.compare)

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
