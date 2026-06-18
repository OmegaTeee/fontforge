# Font Name Modification API Reference

## Overview

The `rename.py` script has been extended with the ability to modify TTF Names and PostScript names directly in font files. This allows you to customize:

1. **Family Name** (nameID 1 and 16) — Font family identifier used by applications
2. **PostScript Name** (nameID 6) — Unique PostScript identifier (no spaces)
3. **Full Font Name** (nameID 4) — Human-readable name shown in font menus

## API Functions

### `set_name_entry(font, name_id, value, lang_id=0x0409, platform_id=3)`

Sets a name entry in the font's name table.

**Parameters:**
- `font` (TTFont): The font object
- `name_id` (int): Name ID to modify (1=Family, 4=Full, 6=PostScript)
- `value` (str): New value
- `lang_id` (int): Language ID (default: 0x0409 = English US)
- `platform_id` (int): Platform ID (default: 3 = Windows)

**Returns:** None

**Example:**
```python
from fontTools.ttLib import TTFont
from rename import set_name_entry

font = TTFont("font.ttf")
set_name_entry(font, 1, "MyFont")  # Set Family Name
font.save("font.ttf")
```

### `modify_font_names(font_path, family=None, psname=None, fullname=None, verbose=False)`

Modifies font name table entries in a font file.

**Parameters:**
- `font_path` (Path): Path to the font file
- `family` (str | None): New Family Name (nameID 1 and 16)
- `psname` (str | None): New PostScript Name (nameID 6)
- `fullname` (str | None): New Full Font Name (nameID 4)
- `verbose` (bool): Print detailed modification info

**Returns:** `bool` — True if modifications were made

**Example:**
```python
from pathlib import Path
from rename import modify_font_names

modified = modify_font_names(
    Path("font.ttf"),
    family="MyFont",
    psname="MyFont-Bold",
    fullname="My Font Bold",
    verbose=True
)
print(f"Font modified: {modified}")
```

## CLI Usage

### Single modification
```bash
# Modify Family Name
python scripts/rename.py fonts/font.ttf --modify-family "MyFont" --apply

# Modify PostScript Name
python scripts/rename.py fonts/font.ttf --modify-psname "MyFont-Bold" --apply

# Modify Full Font Name
python scripts/rename.py fonts/font.ttf --modify-fullname "My Font Bold" --apply
```

### Multiple modifications
```bash
python scripts/rename.py fonts/font.ttf \
  --modify-family "MyFont" \
  --modify-psname "MyFont-Bold" \
  --modify-fullname "My Font Bold" \
  --apply
```

### Batch operation on directory
```bash
python scripts/rename.py fonts/MyFamily/ \
  --modify-family "NewFamily" \
  --verbose \
  --apply
```

### Dry-run preview (no --apply)
```bash
python scripts/rename.py fonts/MyFamily/ \
  --modify-family "TestFamily" \
  --verbose
```

## Name Table IDs Reference

| nameID | Field | Example | Purpose |
|--------|-------|---------|---------|
| 1 | Family Name | "DuckSans" | Application font family selector |
| 4 | Full Font Name | "DuckSans Display Bold" | UI font menu display |
| 6 | PostScript Name | "DuckSans-DisplayBold" | Unique identifier (no spaces) |
| 16 | Typographic Family | "DuckSans Display" | Modern preferred family name |

**Note:** Both nameID 1 and 16 are set when modifying Family Name to ensure compatibility across platforms.

## Key Features

✓ **Dry-run mode** — Preview changes before applying (omit `--apply`)
✓ **Batch processing** — Modify all fonts in a directory recursively
✓ **Verbose output** — See exactly what's being modified
✓ **PostScript name sanitization** — Automatically removes invalid characters
✓ **Multi-modification support** — Change family, psname, and fullname in one command
✓ **Safe file handling** — Proper exception handling and validation

## Technical Implementation

The modification process:

1. **Reads** the font file and accesses its `name` table
2. **Removes** existing nameID entries for the Windows platform
3. **Adds** new nameID entries with the provided values
4. **Saves** the modified font back to disk

### PostScript Name Cleaning

PostScript names must be single words with no spaces. The script automatically sanitizes input:

```
Input:  "My Font-Name 123"
Output: "MyFont-Name123"
```

Valid characters: A-Z, a-z, 0-9, hyphen (-)
Removed: spaces and all special characters

## Examples

### Rename a family for distribution
```bash
# Before: Various messy font files
# After: Consistent naming for all weights

python scripts/rename.py fonts/MyFamily/ \
  --modify-family "MyFamily" \
  --modify-psname "MyFamily-Regular" \
  --verbose
```

### Update PostScript names for web deployment
```bash
python scripts/rename.py fonts/web-fonts/ \
  --modify-psname "CustomFont-Regular" \
  --apply
```

### Batch rename after font redesign
```bash
python scripts/rename.py fonts/ \
  --modify-family "NewDesign" \
  --modify-fullname "New Design Collection" \
  --verbose \
  --apply
```

## Error Handling

The script includes robust error handling:
- Invalid font files are skipped with error messages
- Read/write errors are logged to stderr
- Processing continues for remaining fonts in batch operations
- Changes are only applied with `--apply` flag

## Integration with Pipeline

This feature integrates with FontForge's existing font pipeline:

```bash
# 1. Inspect current names
python scripts/rename.py fonts/MyFamily/ --verbose

# 2. Modify names for consistency
python scripts/rename.py fonts/MyFamily/ \
  --modify-family "FinalFamily" \
  --apply

# 3. Normalize filenames
python scripts/rename.py fonts/MyFamily/ --apply

# 4. Continue with other font processing
python scripts/baseline.py fonts/MyFamily/ --shift -40
python scripts/hint.py fonts/MyFamily/
python scripts/build.py fonts/MyFamily/ --format woff2
```
