#!/usr/bin/env python3
"""Variable font operations.

Inspect, instance, build, and decompile variable fonts.

Usage:
    python variable.py <vf.ttf> --info                       # Axes + named instances
    python variable.py <vf.ttf> --instance "Bold"            # Named instance -> static TTF
    python variable.py <vf.ttf> --instance wght=700,wdth=100 # Coord instance -> static
    python variable.py --from-statics <a.ttf> <b.ttf> ...    # Build VF from statics
    python variable.py <static.ttf> --to-ufo                 # Decompile TTF -> UFO
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import build as varLib_build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument


def is_variable(font: TTFont) -> bool:
    return "fvar" in font


def info(font_path: Path) -> None:
    font = TTFont(font_path)
    if not is_variable(font):
        print(f"{font_path.name}: not a variable font (no fvar table)")
        font.close()
        return

    fvar = font["fvar"]
    name = font["name"]

    print(f"{font_path.name}")
    print(f"  Axes ({len(fvar.axes)}):")
    for axis in fvar.axes:
        tag = axis.axisTag
        print(f"    {tag}  min={axis.minValue}  default={axis.defaultValue}  max={axis.maxValue}")

    print(f"  Instances ({len(fvar.instances)}):")
    for inst in fvar.instances:
        record = name.getName(inst.subfamilyNameID, 3, 1, 0x409)
        label = str(record) if record else f"#{inst.subfamilyNameID}"
        coords = ", ".join(f"{k}={v:g}" for k, v in inst.coordinates.items())
        print(f"    {label}: {coords}")

    font.close()


def _parse_coords(spec: str) -> dict[str, float]:
    """Parse 'wght=700,wdth=100' into {'wght': 700.0, 'wdth': 100.0}."""
    coords: dict[str, float] = {}
    for part in spec.split(","):
        if "=" not in part:
            raise ValueError(f"Expected tag=value in {part!r}")
        tag, val = part.split("=", 1)
        coords[tag.strip()] = float(val.strip())
    return coords


def _resolve_instance(font: TTFont, spec: str) -> tuple[dict[str, float], str]:
    """Resolve a spec (coords or instance name) to (coords, label)."""
    if "=" in spec:
        return _parse_coords(spec), spec.replace(",", "-").replace("=", "")

    name = font["name"]
    target = spec.lower()
    for inst in font["fvar"].instances:
        record = name.getName(inst.subfamilyNameID, 3, 1, 0x409)
        if record and str(record).lower() == target:
            return dict(inst.coordinates), str(record).replace(" ", "")
    raise ValueError(f"No named instance {spec!r}; try --info to list them")


def instance(font_path: Path, spec: str, output: Path | None) -> Path:
    font = TTFont(font_path)
    if not is_variable(font):
        raise ValueError(f"{font_path.name} is not a variable font")

    coords, label = _resolve_instance(font, spec)
    static = instantiateVariableFont(font, coords)
    out = output or font_path.with_stem(f"{font_path.stem}-{label}")
    static.save(str(out))
    font.close()
    print(f"Instanced {coords} -> {out}")
    return out


def from_statics(static_paths: list[Path], output: Path, axis_tag: str = "wght") -> Path:
    """Build a VF from static TTFs whose usWeightClass defines their wght position."""
    if len(static_paths) < 2:
        raise ValueError("Need at least 2 static masters")

    masters: list[tuple[Path, int]] = []
    for p in static_paths:
        font = TTFont(p)
        weight = font["OS/2"].usWeightClass
        masters.append((p, weight))
        font.close()

    masters.sort(key=lambda m: m[1])
    weights = [w for _, w in masters]
    default_weight = _pick_default(weights)

    doc = DesignSpaceDocument()
    doc.addAxisDescriptor(
        tag=axis_tag,
        name="Weight",
        minimum=weights[0],
        maximum=weights[-1],
        default=default_weight,
    )
    for path, weight in masters:
        doc.addSourceDescriptor(
            path=str(path.resolve()),
            location={"Weight": weight},
            styleName=f"{axis_tag}{weight}",
        )

    vf, _, _ = varLib_build(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    vf.save(str(output))
    print(f"Built VF from {len(masters)} master(s) [wght {weights[0]}..{weights[-1]}] -> {output}")
    return output


def _pick_default(weights: list[int]) -> int:
    """Pick the closest weight to 400 (Regular) as the default master."""
    return min(weights, key=lambda w: abs(w - 400))


def to_ufo(font_path: Path, output: Path | None) -> Path:
    """Decompile a compiled TTF/OTF into a UFO source directory."""
    import shutil
    import extractor
    import ufoLib2

    from kern import strip_nonstandard_kern

    # extractor chokes on legacy Apple kern subtables; strip them first.
    # GPOS holds the modern kerning, so nothing real is lost.
    font = TTFont(font_path)
    sanitized_path = font_path
    if strip_nonstandard_kern(font):
        sanitized_path = Path(f"/tmp/{font_path.stem}-nokern{font_path.suffix}")
        font.save(str(sanitized_path))
    font.close()

    ufo = ufoLib2.Font()
    extractor.extractUFO(str(sanitized_path), ufo)
    out = output or font_path.with_suffix(".ufo")
    if out.exists():
        shutil.rmtree(out)
    ufo.save(out, overwrite=True)

    if sanitized_path != font_path:
        sanitized_path.unlink(missing_ok=True)
    print(f"Extracted {font_path.name} -> {out} ({len(ufo)} glyphs)")
    return out


def main():
    parser = argparse.ArgumentParser(description="Variable font operations")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output path (derived from input by default)")
    parser.add_argument("--axis-tag", default="wght",
                        help="Axis tag for --from-statics (default: wght)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--info", action="store_true",
                       help="Print axes and named instances of a variable font")
    group.add_argument("--instance", metavar="SPEC",
                       help="Extract an instance: 'Bold' or 'wght=700,wdth=100'")
    group.add_argument("--from-statics", nargs="+", type=Path, metavar="TTF",
                       help="Build a VF by interpolating static masters")
    group.add_argument("--to-ufo", action="store_true",
                       help="Decompile a compiled font into a UFO source")

    parser.add_argument("font", type=Path, nargs="?",
                        help="Font file (not needed for --from-statics)")

    args = parser.parse_args()

    try:
        if args.from_statics:
            out = args.output or Path(f"{args.from_statics[0].stem.split('-')[0]}-VF.ttf")
            from_statics(args.from_statics, out, args.axis_tag)
            return

        if args.font is None or not args.font.exists():
            print("Error: font file required", file=sys.stderr)
            sys.exit(1)

        if args.info:
            info(args.font)
        elif args.instance:
            instance(args.font, args.instance, args.output)
        elif args.to_ufo:
            to_ufo(args.font, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
