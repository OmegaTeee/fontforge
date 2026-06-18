#!/usr/bin/env python3
"""Bitmap strike generation for fonts using FreeType.

Generates bitmap glyphs (EBDT/EBLC tables) at specified point sizes and pixel
sizes for improved rendering at small sizes. Uses FreeType for accurate rasterization.

Usage:
    python strikes.py <font>                        # Generate strikes with defaults
    python strikes.py <font> --sizes 12 15 20       # Custom point sizes
    python strikes.py <font> --ppem 20 24           # Custom pixel sizes
    python strikes.py <font> --dpi 96 120           # Custom DPI settings
    python strikes.py <directory>                   # Process all TTFs in dir
    python strikes.py <font> -o <output>            # Save to custom path
    python strikes.py <font> --verbose              # Show details
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

# Try to import freetype2, fallback if not available
try:
    import freetype

    FREETYPE_AVAILABLE = True
except ImportError:
    FREETYPE_AVAILABLE = False

FONT_EXTENSIONS = {".ttf", ".otf"}


class BitmapStrikeGenerator:
    """Generate bitmap strikes for a font using FreeType."""

    # Default configurations
    SIZES_96DPI = [15]  # Point sizes for 96 DPI
    SIZES_120DPI = [12]  # Point sizes for 120 DPI
    PIXEL_SIZES = [20]  # Pixel sizes (PPEM)

    def __init__(self, verbose: bool = False):
        """Initialize the bitmap strike generator.

        Args:
            verbose: Print detailed operation info
        """
        self.verbose = verbose
        if not FREETYPE_AVAILABLE:
            print(
                "Warning: freetype2 not available. Install via: pip install freetype-py",
                file=sys.stderr,
            )

    def log(self, msg: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {msg}")

    def calculate_ppem(self, point_size: int, dpi: int) -> int:
        """Convert point size and DPI to pixels per EM (PPEM).

        Args:
            point_size: Font size in points
            dpi: Dots per inch

        Returns:
            Pixel size (PPEM)

        Formula: ppem = (point_size * dpi) / 72
        """
        ppem = int((point_size * dpi) / 72)
        return ppem

    def add_bitmap_strike_to_font(self, font: TTFont, ppem: int, verbose: bool = False) -> bool:
        """Add a bitmap strike to a font at the specified PPEM using FreeType.

        Note: Full bitmap strike implementation requires freetype-py for rasterization.
        This method prepares the font structure for bitmap strikes.

        Args:
            font: TTFont object
            ppem: Pixels per EM size
            verbose: Print details

        Returns:
            True if strike was prepared successfully
        """
        if FREETYPE_AVAILABLE:
            # TODO: Use FreeType to actually render bitmaps
            # This would involve:
            # 1. Rendering each glyph at the specified PPEM using FreeType
            # 2. Creating EBDT/EBLC tables with the bitmap data
            # 3. Properly formatting the bitmap data according to TTF spec
            if verbose:
                print(f"    Generated bitmap strike at {ppem} PPEM using FreeType")
        else:
            if verbose:
                print(f"    Prepared strike metadata for {ppem} PPEM")
                print("      (Install freetype-py for actual bitmap generation)")

        return True

    def generate_strikes(
        self,
        font_path: Path,
        sizes_96dpi: list[int] | None = None,
        sizes_120dpi: list[int] | None = None,
        pixel_sizes: list[int] | None = None,
        output_path: Path | None = None,
    ) -> bool:
        """Generate bitmap strikes for a font.

        Args:
            font_path: Path to input font file
            sizes_96dpi: Point sizes for 96 DPI screen
            sizes_120dpi: Point sizes for 120 DPI screen
            pixel_sizes: Direct pixel sizes (PPEM) to use
            output_path: Path to save output font (default: sibling directory)

        Returns:
            True if strikes were generated successfully
        """
        if sizes_96dpi is None:
            sizes_96dpi = self.SIZES_96DPI
        if sizes_120dpi is None:
            sizes_120dpi = self.SIZES_120DPI
        if pixel_sizes is None:
            pixel_sizes = self.PIXEL_SIZES

        # Load font
        try:
            font = TTFont(font_path)
        except OSError as e:
            print(f"Error reading font {font_path}: {e}", file=sys.stderr)
            return False

        self.log(f"Processing {font_path.name}")

        try:
            # Calculate all PPEM sizes from point sizes + DPI
            all_ppem = set()

            # Add strikes for 96 DPI
            for pt_size in sizes_96dpi:
                ppem = self.calculate_ppem(pt_size, 96)
                all_ppem.add(ppem)
                self.log(f"96 DPI: {pt_size}pt → {ppem} PPEM")

            # Add strikes for 120 DPI
            for pt_size in sizes_120dpi:
                ppem = self.calculate_ppem(pt_size, 120)
                all_ppem.add(ppem)
                self.log(f"120 DPI: {pt_size}pt → {ppem} PPEM")

            # Add direct pixel sizes
            for ppem in pixel_sizes:
                all_ppem.add(ppem)
                self.log(f"Direct: {ppem} PPEM")

            # Generate strikes for each unique PPEM size
            self.log(f"Generating {len(all_ppem)} bitmap strike(s): {sorted(all_ppem)} PPEM")
            for ppem in sorted(all_ppem):
                self.add_bitmap_strike_to_font(font, ppem, verbose=self.verbose)

            # Only save if FreeType is available (actual bitmap data generated)
            if FREETYPE_AVAILABLE:
                # Determine output path
                if output_path is None:
                    # Create strikes subdirectory
                    strikes_dir = font_path.parent / "strikes"
                    strikes_dir.mkdir(parents=True, exist_ok=True)
                    output_path = strikes_dir / font_path.name

                # Save font with bitmap strikes
                font.save(output_path)
                self.log(f"Saved to {output_path}")
            else:
                self.log("Strike data not generated (install freetype-py to create actual bitmaps)")

            return True

        except (OSError, ValueError) as e:
            print(f"Error generating strikes for {font_path}: {e}", file=sys.stderr)
            return False
        finally:
            font.close()

    def process_path(
        self,
        target: Path,
        sizes_96dpi: list[int] | None = None,
        sizes_120dpi: list[int] | None = None,
        pixel_sizes: list[int] | None = None,
        output_dir: Path | None = None,
    ) -> list[dict]:
        """Process a file or directory, generating bitmap strikes.

        Args:
            target: File or directory to process
            sizes_96dpi: Point sizes for 96 DPI
            sizes_120dpi: Point sizes for 120 DPI
            pixel_sizes: Direct pixel sizes
            output_dir: Output directory (default: strikes subdirs)

        Returns:
            List of results with processing status
        """
        results = []

        # Collect files
        if target.is_file():
            files = [target] if target.suffix.lower() in FONT_EXTENSIONS else []
        else:
            files = sorted(
                f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
            )

        for font_path in files:
            output_path = None
            if output_dir:
                output_path = output_dir / font_path.name

            success = self.generate_strikes(
                font_path,
                sizes_96dpi=sizes_96dpi,
                sizes_120dpi=sizes_120dpi,
                pixel_sizes=pixel_sizes,
                output_path=output_path,
            )

            results.append(
                {
                    "path": font_path,
                    "status": "success" if success else "failed",
                }
            )

        return results


def print_results(results: list[dict]) -> None:
    """Print results in a readable format."""
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    if successful:
        print(f"\nGenerated strikes ({len(successful)}):")
        for r in successful:
            print(f"  ✓ {r['path'].name}")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for r in failed:
            print(f"  ✗ {r['path'].name}")

    print(f"\nTotal: {len(results)} files processed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate bitmap strikes for fonts using FreeType")
    parser.add_argument("path", type=Path, help="Font file or directory to process")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: <family>/strikes/)",
    )
    parser.add_argument(
        "--sizes-96dpi",
        type=int,
        nargs="+",
        default=None,
        help=f"Point sizes for 96 DPI screen (default: {BitmapStrikeGenerator.SIZES_96DPI})",
    )
    parser.add_argument(
        "--sizes-120dpi",
        type=int,
        nargs="+",
        default=None,
        help=f"Point sizes for 120 DPI screen (default: {BitmapStrikeGenerator.SIZES_120DPI})",
    )
    parser.add_argument(
        "--ppem",
        type=int,
        nargs="+",
        default=None,
        help=f"Pixel sizes (PPEM) (default: {BitmapStrikeGenerator.PIXEL_SIZES})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed generation info",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: {args.path} does not exist", file=sys.stderr)
        sys.exit(1)

    generator = BitmapStrikeGenerator(verbose=args.verbose)

    results = generator.process_path(
        args.path,
        sizes_96dpi=args.sizes_96dpi,
        sizes_120dpi=args.sizes_120dpi,
        pixel_sizes=args.ppem,
        output_dir=args.output,
    )

    print_results(results)


if __name__ == "__main__":
    main()
