# Bitmap Strikes API Documentation

## Overview

The `strikes.py` script generates bitmap strikes (rasterized font sizes) for improved rendering at small sizes. Bitmap strikes provide pre-rasterized glyph bitmaps at specific point sizes, which can significantly improve legibility when fonts are rendered at small sizes.

## Features

✅ **Multiple size specifications:**
- Point sizes for 96 DPI displays (standard resolution)
- Point sizes for 120 DPI displays (high DPI)
- Direct pixel sizes (PPEM - Pixels per EM)

✅ **Automatic PPEM calculation:**
- Formula: `PPEM = (point_size * DPI) / 72`
- Deduplicates overlapping sizes automatically

✅ **Batch processing:**
- Process single fonts or entire directories
- Outputs to peer `strikes/` subdirectories

✅ **FreeType integration:**
- Ready for FreeType-based bitmap rasterization (when freetype-py is installed)
- Prepares font structure for bitmap data

✅ **Flexible configuration:**
- Override default sizes via CLI
- Verbose logging for debugging

## Usage

### Basic usage with defaults
```bash
python scripts/strikes.py fonts/font.ttf --verbose
```

Default configuration:
- 96 DPI: 15 points → 20 PPEM
- 120 DPI: 12 points → 20 PPEM
- Direct: 20 PPEM

### Custom 96 DPI sizes
```bash
python scripts/strikes.py fonts/font.ttf --sizes-96dpi 12 14 16 --verbose
```

### Custom 120 DPI sizes
```bash
python scripts/strikes.py fonts/font.ttf --sizes-120dpi 10 12 14 --verbose
```

### Direct pixel sizes
```bash
python scripts/strikes.py fonts/font.ttf --ppem 18 20 24 --verbose
```

### Combine all specifications
```bash
python scripts/strikes.py fonts/font.ttf \
  --sizes-96dpi 12 14 16 \
  --sizes-120dpi 10 11 13 \
  --ppem 18 22 \
  --verbose
```

### Batch process entire directory
```bash
python scripts/strikes.py fonts/MyFamily/ \
  --sizes-96dpi 15 \
  --sizes-120dpi 12 \
  --verbose
```

### Custom output directory
```bash
python scripts/strikes.py fonts/font.ttf \
  -o /output/path/ \
  --verbose
```

## CLI Arguments

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `path` | Font file or directory to process |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `-o, --output OUTPUT` | `<family>/strikes/` | Output directory for modified fonts |
| `--sizes-96dpi SIZES...` | `[15]` | Point sizes for 96 DPI screen |
| `--sizes-120dpi SIZES...` | `[12]` | Point sizes for 120 DPI screen |
| `--ppem SIZES...` | `[20]` | Pixel sizes (PPEM) |
| `-v, --verbose` | — | Show detailed operation info |
| `-h, --help` | — | Show help message |

## DPI Reference

### Common Display Resolutions

| Display Type | DPI | Typical Sizes |
|--------------|-----|---------------|
| Standard Desktop | 96 | 15-20 pt |
| Laptop/Desktop (HiDPI) | 120+ | 12-15 pt |
| Mobile Phone | 326+ | 10-12 pt |
| Print | 300+ | Varies |

### Size Calculation Examples

**96 DPI Display:**
- 15 point → 20 PPEM: `(15 * 96) / 72 = 20`
- 12 point → 16 PPEM: `(12 * 96) / 72 = 16`
- 18 point → 24 PPEM: `(18 * 96) / 72 = 24`

**120 DPI Display:**
- 12 point → 20 PPEM: `(12 * 120) / 72 = 20`
- 10 point → 16 PPEM: `(10 * 120) / 72 = 16`
- 15 point → 25 PPEM: `(15 * 120) / 72 = 25`

## Output Structure

Fonts with bitmap strikes are saved in a `strikes/` subdirectory:

```
fonts/
├── MyFamily/
│   ├── MyFamily-Regular.ttf
│   ├── MyFamily-Bold.ttf
│   └── strikes/
│       ├── MyFamily-Regular.ttf    (with bitmap strikes)
│       └── MyFamily-Bold.ttf       (with bitmap strikes)
```

## Current Implementation Status

### ✅ Complete
- Size calculation and deduplication
- DPI-based point size conversion
- Batch directory processing
- CLI argument handling
- Output directory management
- FreeType detection and warnings

### 📋 TODO: FreeType Integration

Full bitmap strike generation requires FreeType:

```python
# Future implementation will:
# 1. Use FreeType to render each glyph at the specified PPEM
# 2. Create EBDT (Embedded Bitmap Data) table with bitmap data
# 3. Create EBLC (Embedded Bitmap Location) table with strike metrics
# 4. Properly format bitmap data according to TTF specification
```

## Installation & Dependencies

### Current Requirements
```bash
fontTools          # Already installed
```

### For Full Bitmap Generation
```bash
pip install freetype-py
```

## FreeType Integration (Future)

When `freetype-py` is installed, the script will automatically:

1. **Render glyphs** at each specified PPEM size using FreeType's rasterization engine
2. **Create bitmap data** with anti-aliasing and proper metrics
3. **Add EBDT/EBLC tables** to the font file
4. **Save modified fonts** with embedded bitmap strikes

This will significantly improve rendering quality at small sizes while maintaining compatibility with systems that don't support bitmap strikes.

## Typical Workflow

```bash
# 1. Inspect what strikes would be created
python scripts/strikes.py fonts/MyFamily/ --verbose

# 2. Generate strikes (once FreeType integration is complete)
python scripts/strikes.py fonts/MyFamily/ \
  --sizes-96dpi 12 14 16 \
  --sizes-120dpi 10 11 13 \
  --verbose

# 3. Verify the output
ls -la fonts/MyFamily/strikes/

# 4. Continue with other font processing
python scripts/baseline.py fonts/MyFamily/strikes/
python scripts/hint.py fonts/MyFamily/strikes/
python scripts/build.py fonts/MyFamily/strikes/ --format woff2
```

## Technical Details

### Bitmap Strike Tables

Bitmap strikes are stored in two TTF tables:

- **EBLC (Embedded Bitmap Location Table)**
  - Contains metrics and location information for bitmap strikes
  - Defines which glyphs have bitmaps at each size
  - Specifies PPEM range and properties

- **EBDT (Embedded Bitmap Data Table)**
  - Contains actual bitmap data for glyphs
  - Format depends on bit depth and compression

### PPEM (Pixels Per EM)

PPEM is the fundamental unit for bitmap strikes:
- Represents the size of the font in pixels at the current resolution
- Not the same as point size (which is DPI-dependent)
- Must be calculated from point size and DPI

### Deduplication

The script automatically deduplicates strikes:
```
Input:
  96 DPI: 15pt → 20 PPEM
  120 DPI: 12pt → 20 PPEM
  Direct: 20 PPEM

Output: [20 PPEM] (single strike, used by all three)
```

## Troubleshooting

### Warning: "freetype2 not available"

Install FreeTree support:
```bash
pip install freetype-py
```

### Font not being saved

The script only saves fonts when FreeTree is available (actual bitmap data generated). Install `freetype-py` to enable bitmap generation.

### Output files not in `strikes/` directory

Use the `-o/--output` flag to specify a custom output directory:
```bash
python scripts/strikes.py fonts/font.ttf -o /my/output/path/
```

## References

- [TTF Font Format Specification](https://docs.microsoft.com/en-us/typography/opentype/spec/)
- [fontTools Documentation](https://fonttools.readthedocs.io/)
- [FreeType Documentation](https://freetype.org/documentation.html)
- [PPEM Explanation](https://en.wikipedia.org/wiki/Font_size#In_digital_typesetting)
