# FontForge Project

Python toolkit for organizing, analyzing, and producing font files. 30+ font families in `fonts/`; scripts read/convert/hint/shift/kern them; MCP server exposes capabilities to Claude Code.

## Navigation
- `mem:tech_stack` — Python, venv, dependencies, external binaries
- `mem:pipeline/order` — kern/baseline/hint/build sequence and dependencies
- `mem:scripts/imports` — how scripts import each other, sys.path magic
- `mem:fonts/structure` — family organization, derivative output dirs
- `mem:gotchas` — non-standard kern tables, composite glyphs, hinting coordinates
- `mem:conventions` — naming, code style, when to use scripts vs MCP server
- `mem:task_completion` — verification commands

## Project-wide invariants
1. **Scripts are dual-purpose**: CLI tools AND importable library (no package-relative imports)
2. **Fonts never overwritten**: vendor source in `fonts/<Family>/`, outputs in peer subdirs (`.../hinted/`, `.../web/`, etc.)
3. **Pipeline order is rigid**: baseline/spacing → hinting → subsetting (reverse order = bugs)
4. **Hinting is coordinate-sensitive**: must happen AFTER any shifts; if re-shifting, delete `.../hinted/` and `.../web/` and rerun
5. **fontTools preserves only subsettable tables**: non-standard kern, morx, mort, feat, FFTM dropped before build
6. **Three vertical metric sets**: hhea, OS/2 typo, OS/2 win; baseline.py keeps all consistent

## Key gotchas
- Composite glyphs inherit baseline shifts through base glyphs (don't add `component.y += shift`)
- Non-standard legacy kern tables in Burbank and others parse as `KernTable_format_unknown`
- GDI clipping on Windows if win metrics not refitted to bbox
