# Font Name Modification Guide

The enhanced `rename.py` script now supports modifying TTF Names and PostScript names directly in the font file. This includes:

- **Family Name** (nameID 1 and 16) — used by applications to identify the font family
- **PostScript Name** (nameID 6) — unique identifier, must be a single word with no spaces
- **Full Font Name** (nameID 4) — human-readable full name (e.g., "DuckSans Product Bold")

## Usage

### Modify Family Name across a directory
```bash
python scripts/rename.py fonts/ttf/ --modify-family "NewFamily" --verbose --apply
```
- Sets nameID 1 and 16 (both Family Name variants)
- Applies to all fonts in the directory recursively
- `--verbose` shows details of each modification
- `--apply` makes the changes permanent (omit for dry-run preview)

### Modify PostScript Name for a single font
```bash
python scripts/rename.py fonts/ttf/DuckSansDisplay-Bold.ttf --modify-psname "DuckSans-DisplayBold" --apply
```
- Sets nameID 6 (PostScript Name)
- Automatically strips invalid characters (spaces, special chars)
- PostScript names should be unique per font style

### Modify Full Font Name
```bash
python scripts/rename.py fonts/ttf/ --modify-fullname "My Font Family Bold" --apply
```
- Sets nameID 4 (Full Font Name)
- This is the "Name For Humans" — what users see in font menus

### Combine multiple modifications
```bash
python scripts/rename.py fonts/ttf/ \
  --modify-family "MyFont" \
  --modify-psname "MyFont-Bold" \
  --modify-fullname "My Font Bold" \
  --verbose \
  --apply
```

## Dry-run (Preview) Mode

All modifications support dry-run preview. Simply omit `--apply`:
```bash
python scripts/rename.py fonts/ttf/ --modify-family "TestFamily" --verbose
```

This shows what would be modified without making permanent changes.

## How It Works

The script modifies the font's internal name table (TTF name tables):
- **Locating entries**: Searches for existing nameID entries (platform Windows, language English US)
- **Removing old entries**: Clears existing nameID entries for that platform/language
- **Adding new entries**: Inserts the new name value
- **Saving**: Writes the modified font back to disk

### PostScript Name Cleaning
PostScript names are sanitized automatically:
- Input: `"My Font-Name 123"`
- Output: `"MyFont-Name123"` (spaces and special chars removed, hyphens preserved)

## Typical Workflow

When preparing fonts for web/distribution:

```bash
# 1. Inspect current names
python scripts/rename.py fonts/MyFamily/ --verbose

# 2. Preview modifications
python scripts/rename.py fonts/MyFamily/ \
  --modify-family "MyNewFamily" \
  --modify-psname "MyNewFamily-Bold"

# 3. Apply when satisfied
python scripts/rename.py fonts/MyFamily/ \
  --modify-family "MyNewFamily" \
  --modify-psname "MyNewFamily-Bold" \
  --apply

# 4. Verify changes (optional)
python scripts/rename.py fonts/MyFamily/ --verbose
```

## Technical Details

- **nameID 1**: Font Family Name
- **nameID 4**: Full Font Name
- **nameID 6**: PostScript Name (Fontname)
- **nameID 16**: Typographic Family (preferred over nameID 1 in modern systems)
- **Platform**: Windows (ID 3), Language: English US (0x0409)

The script preserves all other name table entries and only modifies the specified nameID entries.
