#!/usr/bin/env python3
"""Kerning and spacing utilities.

Read, write, and adjust kerning pairs and glyph spacing in font files.

Usage:
    python kern.py <font> --dump                      # Dump kerning to stdout CSV
    python kern.py <font> --dump -o pairs.csv         # Dump to file
    python kern.py <font> --apply pairs.csv           # Merge CSV kerning into font
    python kern.py <font> --spacing lc:+10            # Widen lowercase advances by 10u
    python kern.py <font> --spacing "A-Z:-5,a-z:+10"  # Multiple rules
"""

import argparse
import csv
import re
import string
import sys
import tempfile
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont

# None means "every glyph in the font"; expanded lazily in resolve_glyphs.
CLASS_PRESETS = {
    "uc": list(string.ascii_uppercase),
    "lc": list(string.ascii_lowercase),
    "digits": list(string.digits),
    "all": None,
}


def has_nonstandard_kern(font: TTFont) -> bool:
    """True if the font's `kern` table has unrecognized subtable formats.

    Older vendor fonts (e.g. Burbank) ship a legacy Apple kern subtable that
    fontTools parses as `KernTable_format_unkown` without the `kernTable` /
    `version` attributes. GPOS carries the modern kerning so the legacy
    table can be safely dropped for web output and UFO extraction.
    """
    if "kern" not in font:
        return False
    for subtable in font["kern"].kernTables:
        if not hasattr(subtable, "kernTable") or not hasattr(subtable, "version"):
            return True
    return False


def strip_nonstandard_kern(font: TTFont) -> bool:
    """Delete the `kern` table if it has unrecognized subtables. Returns True if dropped."""
    if has_nonstandard_kern(font):
        del font["kern"]
        return True
    return False


def extract_kerning(font: TTFont) -> list[tuple[str, str, int]]:
    """Return flat list of (left, right, value) kerning pairs from kern + GPOS."""
    pairs: list[tuple[str, str, int]] = []

    if "kern" in font:
        for subtable in font["kern"].kernTables:
            table = getattr(subtable, "kernTable", None)
            if not table:
                continue
            for (left, right), value in table.items():
                pairs.append((left, right, value))

    if "GPOS" in font:
        gpos = font["GPOS"].table
        kern_lookups = _collect_kern_lookups(gpos)
        for lookup in kern_lookups:
            for subtable in lookup.SubTable:
                pairs.extend(_flatten_pairpos(subtable))

    return pairs


def _collect_kern_lookups(gpos) -> list:
    """Find GPOS lookups referenced by the 'kern' feature."""
    kern_lookup_indices: set[int] = set()
    if not gpos.FeatureList:
        return []
    for feature_record in gpos.FeatureList.FeatureRecord:
        if feature_record.FeatureTag == "kern":
            kern_lookup_indices.update(feature_record.Feature.LookupListIndex)
    return [gpos.LookupList.Lookup[i] for i in sorted(kern_lookup_indices)]


def _flatten_pairpos(subtable) -> list[tuple[str, str, int]]:
    """Flatten a PairPos subtable (format 1 or 2) into explicit pairs."""
    pairs: list[tuple[str, str, int]] = []

    if subtable.Format == 1:
        coverage = subtable.Coverage.glyphs
        for left, pairset in zip(coverage, subtable.PairSet, strict=False):
            for record in pairset.PairValueRecord:
                value = _read_xadvance(record.Value1)
                if value:
                    pairs.append((left, record.SecondGlyph, value))

    elif subtable.Format == 2:
        # Format 2 stores kerning as a class x class matrix; flatten by
        # taking the Cartesian product of each class pair with a nonzero value.
        class1 = _class_def_to_groups(subtable.ClassDef1, subtable.Coverage.glyphs)
        class2 = _class_def_to_groups(subtable.ClassDef2)
        for i, class1_record in enumerate(subtable.Class1Record):
            for j, class2_record in enumerate(class1_record.Class2Record):
                value = _read_xadvance(class2_record.Value1)
                if not value:
                    continue
                for left in class1.get(i, []):
                    for right in class2.get(j, []):
                        pairs.append((left, right, value))

    return pairs


def _read_xadvance(value_record) -> int:
    """Pull XAdvance off a GPOS ValueRecord, treating missing/zero as 0."""
    return getattr(value_record, "XAdvance", 0) or 0 if value_record else 0


def _class_def_to_groups(
    class_def, coverage_glyphs: list[str] | None = None
) -> dict[int, list[str]]:
    """Invert a ClassDef table into {class_index: [glyph_names]}.

    Class 0 is special: any glyph in coverage (for ClassDef1) or in the font
    (for ClassDef2) that isn't explicitly assigned falls into class 0.
    """
    groups: dict[int, list[str]] = {}
    assigned: set[str] = set()
    for glyph, class_id in class_def.classDefs.items():
        groups.setdefault(class_id, []).append(glyph)
        assigned.add(glyph)
    if coverage_glyphs is not None:
        zero = [g for g in coverage_glyphs if g not in assigned]
        if zero:
            groups.setdefault(0, []).extend(zero)
    return groups


def dump_kerning(font_path: Path, output: Path | None) -> int:
    """Write all kerning pairs to `output` (or stdout) as CSV. Returns pair count."""
    font = TTFont(font_path)
    pairs = extract_kerning(font)
    font.close()

    stream = output.open("w", newline="") if output else sys.stdout
    writer = csv.writer(stream)
    writer.writerow(["left", "right", "value"])
    for left, right, value in pairs:
        writer.writerow([left, right, value])
    if output:
        stream.close()

    print(
        f"Extracted {len(pairs)} kerning pair(s)" + (f" -> {output}" if output else ""),
        file=sys.stderr,
    )
    return len(pairs)


def apply_kerning(font_path: Path, csv_path: Path, output: Path | None) -> int:
    """Compile CSV kerning into the font via a synthesized .fea snippet."""
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = [(r["left"], r["right"], int(r["value"])) for r in reader]

    font = TTFont(font_path)
    glyph_set = set(font.getGlyphOrder())
    valid = [
        (left, right, value)
        for left, right, value in rows
        if left in glyph_set and right in glyph_set
    ]
    skipped = len(rows) - len(valid)

    # Synthesize a minimal .fea and let feaLib compile it into GPOS. Going
    # through .fea (rather than writing GPOS structs directly) handles class
    # building, lookup indexing, and script/language registration for us.
    fea_lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
    for left, right, value in valid:
        fea_lines.append(f"  pos {_fea_glyph(left)} {_fea_glyph(right)} {value};")
    fea_lines.append("} kern;")

    with tempfile.NamedTemporaryFile("w", suffix=".fea", delete=False) as tmp:
        tmp.write("\n".join(fea_lines))
        fea_path = Path(tmp.name)

    try:
        addOpenTypeFeatures(font, str(fea_path))
    finally:
        fea_path.unlink(missing_ok=True)

    out = output or font_path.with_stem(font_path.stem + "-kerned")
    font.save(str(out))
    font.close()

    print(
        f"Applied {len(valid)} pair(s)"
        + (f" ({skipped} skipped: glyph not in font)" if skipped else "")
        + f" -> {out}"
    )
    return len(valid)


def _fea_glyph(name: str) -> str:
    """Quote glyph names that contain characters invalid in .fea identifiers."""
    if re.match(r"^[A-Za-z_][\w.]*$", name):
        return name
    return f"\\{name}"


def parse_spacing_rules(spec: str) -> list[tuple[str, int]]:
    """Parse 'lc:+10,A-Z:-5' into [('lc', 10), ('A-Z', -5)]."""
    rules = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(f"Spacing rule missing ':': {chunk!r}")
        pattern, delta = chunk.split(":", 1)
        rules.append((pattern.strip(), int(delta.strip())))
    return rules


def resolve_glyphs(pattern: str, glyph_order: list[str]) -> list[str]:
    """Expand a pattern into glyph names.

    Patterns:
        'lc' / 'uc' / 'digits' / 'all'  -> preset class
        'A-Z'                           -> character range
        '/regex/'                       -> regex match on glyph name
        'A,B,C'                         -> literal list
    """
    if pattern in CLASS_PRESETS:
        preset = CLASS_PRESETS[pattern]
        if preset is None:
            return list(glyph_order)
        return [g for g in glyph_order if g in preset]

    if pattern.startswith("/") and pattern.endswith("/"):
        rx = re.compile(pattern[1:-1])
        return [g for g in glyph_order if rx.search(g)]

    if re.match(r"^.-.$", pattern):
        start, end = pattern[0], pattern[2]
        chars = [chr(c) for c in range(ord(start), ord(end) + 1)]
        return [g for g in glyph_order if g in chars]

    return [g.strip() for g in pattern.split(",") if g.strip() in glyph_order]


def apply_spacing(font_path: Path, spec: str, output: Path | None) -> int:
    """Apply `spec` ('lc:+10,A-Z:-5') to hmtx advance widths and save. Returns count touched."""
    font = TTFont(font_path)
    hmtx = font["hmtx"]
    glyph_order = font.getGlyphOrder()
    rules = parse_spacing_rules(spec)

    touched = 0
    for pattern, delta in rules:
        glyphs = resolve_glyphs(pattern, glyph_order)
        for g in glyphs:
            advance, lsb = hmtx[g]
            # Clamp to >=0: hmtx advance width is uint16, negative advances
            # would wrap to a huge positive value and wreck layout.
            hmtx[g] = (max(0, advance + delta), lsb)
            touched += 1
        print(f"  {pattern}: {len(glyphs)} glyph(s), advance {delta:+d}")

    out = output or font_path.with_stem(font_path.stem + "-spaced")
    font.save(str(out))
    font.close()

    print(f"Adjusted {touched} advance(s) -> {out}")
    return touched


def main() -> None:
    parser = argparse.ArgumentParser(description="Kerning and spacing utilities")
    parser.add_argument("font", type=Path, help="Font file (.ttf/.otf)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: derived from input, or stdout for --dump)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dump", action="store_true", help="Extract kerning pairs as CSV")
    group.add_argument(
        "--apply", type=Path, metavar="CSV", help="Merge kerning pairs from a CSV into the font"
    )
    group.add_argument(
        "--spacing",
        metavar="SPEC",
        help="Adjust advance widths: 'lc:+10,A-Z:-5' "
        "(classes: lc/uc/digits/all, ranges, /regex/, or A,B,C)",
    )

    args = parser.parse_args()

    if not args.font.exists():
        print(f"Error: {args.font} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.dump:
        dump_kerning(args.font, args.output)
    elif args.apply:
        if not args.apply.exists():
            print(f"Error: {args.apply} does not exist", file=sys.stderr)
            sys.exit(1)
        apply_kerning(args.font, args.apply, args.output)
    elif args.spacing:
        apply_spacing(args.font, args.spacing, args.output)


if __name__ == "__main__":
    main()
