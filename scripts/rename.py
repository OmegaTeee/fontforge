#!/usr/bin/env python3
"""Font file renaming utility.

Normalizes font filenames to the standard FamilyName-Weight.ext convention
by reading the font's internal name table, falling back to filename parsing
when the font can't be read.

Usage:
    python rename.py <path>              # Preview renames (dry run)
    python rename.py <path> --apply      # Apply renames
    python rename.py <path> --verbose    # Show detailed name table info
    python rename.py <path> --modify-family <new>     # Modify Family Name (nameID 1)
    python rename.py <path> --modify-psname <new>     # Modify PostScript Name (nameID 6)
    python rename.py <path> --modify-fullname <new>   # Modify Full Name (nameID 4)
"""

import argparse
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".ttc"}

# OpenType weight class to name mapping
WEIGHT_CLASS_MAP = {
    100: "Thin",
    200: "ExtraLight",
    250: "ExtraLight",
    300: "Light",
    350: "SemiLight",
    400: "Regular",
    500: "Medium",
    600: "SemiBold",
    650: "SemiBold",
    700: "Bold",
    800: "ExtraBold",
    900: "Black",
    950: "UltraBlack",
}

# Patterns for extracting weight from messy filenames
WEIGHT_ALIASES = {
    "thin": "Thin",
    "extralight": "ExtraLight",
    "ultralight": "ExtraLight",
    "light": "Light",
    "semilight": "SemiLight",
    "regular": "Regular",
    "normal": "Regular",
    "medium": "Medium",
    "semibold": "SemiBold",
    "demibold": "SemiBold",
    "bold": "Bold",
    "extrabold": "ExtraBold",
    "ultrabold": "ExtraBold",
    "black": "Black",
    "heavy": "Black",
    "ultrablack": "UltraBlack",
}


def get_name_entry(name_table, name_id: int) -> str | None:
    """Extract a name entry from the font's name table."""
    for record in name_table.names:
        if record.nameID == name_id:
            try:
                return str(record).strip()
            except Exception:
                continue
    return None


def get_font_names(font_path: Path) -> dict:
    """Read family name, subfamily, and weight from font's internal tables."""
    result = {"family": None, "subfamily": None, "weight_class": None}
    try:
        font = TTFont(font_path, fontNumber=0)
    except Exception:
        return result

    try:
        name_table = font["name"]
        # nameID 1 = Font Family, nameID 2 = Subfamily (style)
        # nameID 16 = Typographic Family, nameID 17 = Typographic Subfamily
        result["family"] = get_name_entry(name_table, 16) or get_name_entry(name_table, 1)
        result["subfamily"] = get_name_entry(name_table, 17) or get_name_entry(name_table, 2)

        if "OS/2" in font:
            result["weight_class"] = font["OS/2"].usWeightClass
    except Exception:
        pass
    finally:
        font.close()

    return result


def set_name_entry(
    font: "TTFont", name_id: int, value: str, lang_id: int = 0x0409, platform_id: int = 3
) -> None:
    """Set a name entry in the font's name table.

    Args:
        font: TTFont object
        name_id: Name ID to set (1=Family, 4=Full name, 6=PostScript name, etc.)
        value: New value for the name entry
        lang_id: Language ID (default 0x0409 = English US)
        platform_id: Platform ID (default 3 = Windows)
    """
    if "name" not in font:
        return

    name_table = font["name"]
    # Remove existing entries for this nameID on Windows platform
    name_table.names = [
        record
        for record in name_table.names
        if not (record.nameID == name_id and record.platformID == platform_id)
    ]
    # Add the new entry using positional arguments: nameID, platformID, platEncID, langID, string
    name_table.setName(value, name_id, platform_id, 1, lang_id)


def modify_font_names(
    font_path: Path,
    family: str | None = None,
    psname: str | None = None,
    fullname: str | None = None,
    verbose: bool = False,
) -> bool:
    """Modify font name table entries (TTF Names and PostScript name).

    Args:
        font_path: Path to the font file
        family: New Family Name (nameID 1)
        psname: New PostScript Name (nameID 6)
        fullname: New Full Font Name (nameID 4)
        verbose: Print detailed info

    Returns:
        True if modifications were made, False otherwise
    """
    try:
        font = TTFont(font_path, fontNumber=0)
    except Exception as e:
        print(f"Error reading font {font_path}: {e}", file=sys.stderr)
        return False

    try:
        modified = False

        if family:
            set_name_entry(font, 1, family)  # nameID 1 = Family Name
            set_name_entry(font, 16, family)  # nameID 16 = Typographic Family
            modified = True
            if verbose:
                print(f"  Set Family Name (ID 1, 16) to: {family}")

        if psname:
            # PostScript name must be a single, unique word with no spaces
            psname_clean = re.sub(r"[^A-Za-z0-9\-]", "", psname)
            set_name_entry(font, 6, psname_clean)  # nameID 6 = PostScript Name
            modified = True
            if verbose:
                print(f"  Set PostScript Name (ID 6) to: {psname_clean}")

        if fullname:
            set_name_entry(font, 4, fullname)  # nameID 4 = Full Font Name
            modified = True
            if verbose:
                print(f"  Set Full Font Name (ID 4) to: {fullname}")

        if modified:
            font.save(font_path)
            if verbose:
                print(f"  Saved modifications to {font_path}")

        return modified
    except Exception as e:
        print(f"Error modifying font {font_path}: {e}", file=sys.stderr)
        return False
    finally:
        font.close()


def normalize_family(name: str) -> str:
    """Normalize a family name: remove spaces, ensure PascalCase."""
    # Remove anything in parentheses
    name = re.sub(r"\([^)]*\)", "", name)
    # Remove extra whitespace and dashes used as separators
    name = name.strip().strip("-").strip()
    # Split on spaces, dashes, or camelCase boundaries
    parts = re.split(r"[\s\-_]+", name)
    # PascalCase each part
    return "".join(p.capitalize() if p.islower() and len(p) > 2 else p for p in parts if p)


def normalize_subfamily(subfamily: str, weight_class: int | None) -> str:
    """Normalize a subfamily/style name to standard weight-style format."""
    if not subfamily:
        if weight_class and weight_class in WEIGHT_CLASS_MAP:
            return WEIGHT_CLASS_MAP[weight_class]
        return "Regular"

    # Clean up the subfamily string
    sub_lower = subfamily.lower().replace(" ", "").replace("-", "")

    # Check for italic
    is_italic = "italic" in sub_lower
    sub_lower = sub_lower.replace("italic", "")

    # Try to match a weight name
    weight = None
    for alias, canonical in sorted(WEIGHT_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in sub_lower:
            weight = canonical
            break

    if not weight:
        if weight_class and weight_class in WEIGHT_CLASS_MAP:
            weight = WEIGHT_CLASS_MAP[weight_class]
        else:
            weight = "Regular"

    if is_italic:
        return f"{weight}Italic" if weight != "Regular" else "Italic"
    return weight


def parse_weight_from_filename(filename: str) -> str:
    """Fallback: extract weight from filename patterns like '(Bold) Name' or 'Name - Bold'."""
    stem = Path(filename).stem

    # Pattern: (Weight) FamilyName
    paren_match = re.match(r"\((\w+)\)\s*(.*)", stem)
    if paren_match:
        weight_str = paren_match.group(1).lower()
        if weight_str in WEIGHT_ALIASES:
            return WEIGHT_ALIASES[weight_str]

    # Pattern: FamilyName - Weight
    dash_match = re.search(r"\s*-\s*(\w+)$", stem)
    if dash_match:
        weight_str = dash_match.group(1).lower()
        if weight_str in WEIGHT_ALIASES:
            return WEIGHT_ALIASES[weight_str]

    return "Regular"


def parse_family_from_filename(filename: str) -> str:
    """Fallback: extract family name from filename."""
    stem = Path(filename).stem

    # Remove (Weight) prefix
    stem = re.sub(r"^\([^)]*\)\s*", "", stem)
    # Remove - Weight suffix
    for alias in WEIGHT_ALIASES:
        stem = re.sub(rf"\s*-\s*{alias}\s*$", "", stem, flags=re.IGNORECASE)
    # Remove trailing weight words
    for alias in WEIGHT_ALIASES:
        stem = re.sub(rf"\s*{alias}\s*$", "", stem, flags=re.IGNORECASE)

    return normalize_family(stem)


def compute_new_name(font_path: Path, verbose: bool = False) -> str | None:
    """Compute the normalized filename for a font file."""
    names = get_font_names(font_path)

    if verbose:
        print(
            f"  Name table: family={names['family']}, "
            f"subfamily={names['subfamily']}, "
            f"weight_class={names['weight_class']}"
        )

    if names["family"]:
        family = normalize_family(names["family"])
        subfamily = normalize_subfamily(names["subfamily"], names["weight_class"])
    else:
        family = parse_family_from_filename(font_path.name)
        subfamily = parse_weight_from_filename(font_path.name)

    new_name = f"{family}-{subfamily}{font_path.suffix}"

    if new_name == font_path.name:
        return None

    return new_name


def compute_new_name_from_filename(font_path: Path) -> str:
    """Compute normalized name using only the filename (no font tables)."""
    family = parse_family_from_filename(font_path.name)
    subfamily = parse_weight_from_filename(font_path.name)
    return f"{family}-{subfamily}{font_path.suffix}"


def process_path(target: Path, apply: bool = False, verbose: bool = False) -> list[dict]:
    """Process a file or directory, computing renames."""
    results = []

    if target.is_file():
        files = [target] if target.suffix.lower() in FONT_EXTENSIONS else []
    else:
        files = sorted(
            f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
        )

    # First pass: compute names and detect conflicts
    planned: dict[str, list[tuple[Path, str]]] = {}
    for font_path in files:
        new_name = compute_new_name(font_path, verbose=verbose)
        if new_name is None:
            new_name = font_path.name  # keep as-is
        key = str(font_path.parent / new_name)
        planned.setdefault(key, []).append((font_path, new_name))

    # Find which target names have collisions
    collision_targets = {k for k, v in planned.items() if len(v) > 1}

    # Second pass: resolve collisions by falling back to filename parsing
    final_names: dict[Path, str] = {}
    for key, entries in planned.items():
        if key in collision_targets:
            for font_path, _ in entries:
                fallback = compute_new_name_from_filename(font_path)
                final_names[font_path] = fallback
                if verbose:
                    print(f"  Collision fallback: {font_path.name} -> {fallback}")
        else:
            font_path, new_name = entries[0]
            final_names[font_path] = new_name

    for font_path in files:
        new_name = final_names[font_path]
        if new_name == font_path.name:
            results.append({"path": font_path, "action": "skip", "reason": "already normalized"})
            continue

        new_path = font_path.parent / new_name
        if new_path.exists() and new_path != font_path:
            results.append({"path": font_path, "action": "conflict", "new_name": new_name})
            continue

        if apply:
            font_path.rename(new_path)
            results.append({"path": font_path, "action": "renamed", "new_name": new_name})
        else:
            results.append({"path": font_path, "action": "preview", "new_name": new_name})

    return results


def print_results(results: list[dict]) -> None:
    """Print rename results in a readable format."""
    renamed = [r for r in results if r["action"] in ("renamed", "preview")]
    skipped = [r for r in results if r["action"] == "skip"]
    conflicts = [r for r in results if r["action"] == "conflict"]

    if renamed:
        action_word = "Renamed" if renamed[0]["action"] == "renamed" else "Would rename"
        print(f"\n{action_word} ({len(renamed)}):")
        for r in renamed:
            print(f"  {r['path'].name} -> {r['new_name']}")

    if conflicts:
        print(f"\nConflicts ({len(conflicts)}):")
        for r in conflicts:
            print(f"  {r['path'].name} -> {r['new_name']} (target exists)")

    if skipped:
        print(f"\nAlready normalized: {len(skipped)}")

    print(f"\nTotal: {len(results)} files processed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize font filenames and modify font names")
    parser.add_argument("path", type=Path, help="Font file or directory to process")
    parser.add_argument("--apply", action="store_true", help="Apply renames (default is dry run)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show name table details")
    parser.add_argument(
        "--modify-family",
        metavar="NAME",
        help="Set Family Name (nameID 1 and 16) for all fonts in the path",
    )
    parser.add_argument(
        "--modify-psname",
        metavar="NAME",
        help="Set PostScript Name (nameID 6) for all fonts in the path",
    )
    parser.add_argument(
        "--modify-fullname",
        metavar="NAME",
        help="Set Full Font Name (nameID 4) for all fonts in the path",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: {args.path} does not exist", file=sys.stderr)
        sys.exit(1)

    # Handle name modifications
    if args.modify_family or args.modify_psname or args.modify_fullname:
        if args.path.is_file():
            files = [args.path] if args.path.suffix.lower() in FONT_EXTENSIONS else []
        else:
            files = sorted(
                f
                for f in args.path.rglob("*")
                if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
            )

        print(f"Modifying {len(files)} font(s)...\n")
        modified_count = 0
        for font_path in files:
            if modify_font_names(
                font_path,
                family=args.modify_family,
                psname=args.modify_psname,
                fullname=args.modify_fullname,
                verbose=args.verbose,
            ):
                modified_count += 1
                print(f"✓ Modified {font_path.name}")

        print(f"\nTotal: {modified_count}/{len(files)} fonts modified")
        return

    # Handle filename normalization (original behavior)
    if not args.apply:
        print("DRY RUN (use --apply to rename files)\n")

    results = process_path(args.path, apply=args.apply, verbose=args.verbose)
    print_results(results)


if __name__ == "__main__":
    main()
