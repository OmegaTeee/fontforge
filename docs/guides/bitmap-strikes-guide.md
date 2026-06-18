# Bitmap Strikes Quick Reference

## Installation

The `strikes.py` script is ready to use. For full bitmap generation, install FreeType:

```bash
pip install freetype-py
```

## Quick Commands

### View configuration for a font
```bash
python scripts/strikes.py fonts/font.ttf -v
```

### Generate strikes with defaults
```bash
python scripts/strikes.py fonts/font.ttf
# 96 DPI: 15pt (→ 20 PPEM)
# 120 DPI: 12pt (→ 20 PPEM)
```

### Batch process a family
```bash
python scripts/strikes.py fonts/MyFamily/ -v
```

### Custom point sizes
```bash
# Standard screens
python scripts/strikes.py fonts/ --sizes-96dpi 12 14 16

# High-DPI displays
python scripts/strikes.py fonts/ --sizes-120dpi 10 11 13

# Combined
python scripts/strikes.py fonts/ \
  --sizes-96dpi 12 14 16 \
  --sizes-120dpi 10 11 13 \
  --ppem 18 22 24
```

## DPI Quick Guide

| Display | DPI | Recommended Sizes |
|---------|-----|-------------------|
| Desktop | 96 | 12-18 pt |
| Laptop/HiDPI | 120 | 10-15 pt |
| Mobile | 326+ | 8-12 pt |

## Size Conversion

```
PPEM = (Point Size × DPI) ÷ 72

Examples:
• 15pt @ 96 DPI  = 20 PPEM
• 12pt @ 120 DPI = 20 PPEM
• 10pt @ 120 DPI = 16 PPEM
• 18pt @ 96 DPI  = 24 PPEM
```

## Integration with Font Pipeline

```bash
# 1. Generate strikes
python scripts/strikes.py fonts/MyFamily/ \
  --sizes-96dpi 12 14 16 \
  --sizes-120dpi 10 11 13

# 2. Process strikes
python scripts/baseline.py fonts/MyFamily/strikes/ --shift -40
python scripts/hint.py fonts/MyFamily/strikes/
python scripts/build.py fonts/MyFamily/strikes/ --format woff2
```

## Output

Results are saved to `fonts/<Family>/strikes/`:

```
fonts/
├── MyFamily-Regular.ttf
├── MyFamily-Bold.ttf
└── strikes/
    ├── MyFamily-Regular.ttf  ← with bitmap strikes
    └── MyFamily-Bold.ttf     ← with bitmap strikes
```

## FreeType Status

- ❌ Not installed: Script shows what strikes would be created
- ✅ Installed: Automatically generates actual bitmap data

Check status:
```bash
python scripts/strikes.py fonts/font.ttf -v
```

If you see "Prepared strike metadata" → FreeType not installed
If you see "Generated bitmap strike" → FreeType working

## Default Sizes Explained

The script defaults prepare fonts for common use cases:

| Setting | Size | Reason |
|---------|------|--------|
| 96 DPI | 15pt | Common desktop size |
| 120 DPI | 12pt | Same screen size, higher DPI |
| Direct | 20 PPEM | Fallback pixel size |

All three resolve to **20 PPEM** (same rendering size across displays).

## Verbose Output Example

```
$ python scripts/strikes.py fonts/font.ttf -v

  Processing font.ttf
  96 DPI: 15pt → 20 PPEM
  120 DPI: 12pt → 20 PPEM
  Direct: 20 PPEM
  Generating 1 bitmap strike(s): [20] PPEM
    Prepared strike metadata for 20 PPEM
      (Install freetype-py for actual bitmap generation)
  Strike data not generated (install freetype-py to create actual bitmaps)
```

## Common Workflows

### Screen-optimized strikes
```bash
# Create strikes for both standard and HiDPI displays
python scripts/strikes.py fonts/ \
  --sizes-96dpi 12 14 16 18 \
  --sizes-120dpi 10 11 13 15
```

### Web font strikes
```bash
# For web use with progressive enhancement
python scripts/strikes.py fonts/ \
  --ppem 14 16 18 20 24
```

### All-purpose strikes
```bash
# Coverage for most use cases
python scripts/strikes.py fonts/ \
  --sizes-96dpi 11 13 15 17 19 \
  --sizes-120dpi 9 11 13 15 16 \
  --ppem 16 20 24
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No `strikes/` folder created | Install `freetype-py` for actual generation |
| "FreeType not available" warning | `pip install freetype-py` |
| Font not saved | Ensure `freetype-py` is installed for bitmap data |
| Wrong output location | Use `-o/--output` to specify directory |

## See Also

- [Full API Documentation](../references/strikes-api.md)
- [Font Pipeline Guide](user-manual.md)
- [Baseline Adjustment](../../scripts/baseline.py)
- [Font Hinting](../../scripts/hint.py)
- [Font Building](../../scripts/build.py)
