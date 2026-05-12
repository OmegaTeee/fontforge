# FontForge

Python toolkit for organizing, analyzing, and producing font files. 30+ font families in `fonts/`; the scripts read/convert/hint/shift/kern them; an MCP server (`mcp-server/server.py`) exposes all capabilities to Claude Code.

## Environment

- Python 3.14, venv at `venv/`. Always run Python as `source venv/bin/activate && python …` or `venv/bin/python …` — never the system Python.
- Dependencies in `requirements.txt`. Note: `ufo-extractor` is pinned to `git+https://github.com/typesupply/extractor.git` because the PyPI name `extractor` is squatted by an unrelated keyword-extraction package.
- External binary: `ttfautohint` (Homebrew). `scripts/hint.py` shells out to it.

## Architecture

- `scripts/*.py` are **both** standalone CLI tools and an importable library. `mcp-server/server.py` adds `scripts/` to `sys.path` and imports by bare name (`from kern import …`). Scripts may import each other the same way. Don't change to package-relative imports.
- Fonts are organized by family in `fonts/<Family>/`. Derivative outputs always go in **peer subdirectories** of the family: `fonts/<Family>/kerning/`, `.../shifted/`, `.../hinted/`, `.../web/`. Never overwrite vendor source files.
- Two nested font repos (`fonts/GoogleSans-Code/`, `fonts/Schibsted-Grotesk/`) are gitignored — they have their own upstream git history. Manage separately.
- **Fonts directory location** resolves in this order: `--fonts-dir` CLI flag → `$FONTFORGE_FONTS_DIR` env var → in-repo `fonts/`. Set the env var to share one location between the MCP server, VSCode launch configs, and the shell. The repo `fonts/` directory is the default for local development; the test fixture lives separately in `tests/fixtures/` so the test suite stays self-contained even if `fonts/` is moved out of the workspace.

## Pipeline order

When preparing a family for web, always in this order:

1. **Baseline / spacing** adjustments (`baseline.py`, optional `kern.py --spacing`)
2. **Hinting** (`hint.py`)
3. **Subsetting + format conversion** (`build.py --format woff2 --subset …`)

Hinting instructions are computed for specific glyph coordinates, so any shift/spacing must happen before hinting. Subsetting strips tables fontTools can't preserve, so it runs last.

**If you re-shift an already-hinted family**, delete `fonts/<Family>/hinted/` and `fonts/<Family>/web/` and rerun from step 2. The existing artifacts were hinted against the pre-shift coordinates; leaving them in place ships a font whose hinting no longer matches its outlines.

## Known gotchas (baked into the scripts)

- **Non-standard legacy `kern` tables** appear in older vendor fonts (Burbank and others). fontTools parses them as `KernTable_format_unkown`. `kern.has_nonstandard_kern` / `kern.strip_nonstandard_kern` detect/drop them. GPOS carries modern kerning so nothing real is lost.
- **Composite glyphs inherit baseline shifts automatically** through their base glyphs. `baseline.shift_glyphs` deliberately only iterates simple glyphs; don't reintroduce `component.y += shift` (regression previously caught in AnthropicSans).
- **Subsettable tables only**: `build.convert_font` drops `morx`, `mort`, `feat`, `FFTM` before subsetting since fontTools can't handle them. They're Apple-only layout or FontForge-internal build artifacts; harmless for web.
- **Font has three vertical metric sets** (`hhea`, `OS/2` typo, `OS/2` win). `baseline.py` keeps all three consistent on any shift and refits win metrics to the glyph bbox to prevent Windows GDI clipping.

## Commit hygiene

- `fonts/*.ttf` and `.woff2` ARE tracked — they're the product. Keep it that way.
- `.claude/settings.local.json` is per-machine and gitignored. Don't re-add.
- Prefer new commits over `--amend`.

## Quick reference

```bash
# Inspect any font
venv/bin/python scripts/metrics.py fonts/<Family>/<File>.ttf

# Full web pipeline for a family (after sanity-checking metrics)
venv/bin/python scripts/baseline.py fonts/<F>/ --shift -40 -o fonts/<F>/shifted
venv/bin/python scripts/hint.py     fonts/<F>/shifted/  -o fonts/<F>/hinted --strong
venv/bin/python scripts/build.py    fonts/<F>/hinted/   -o fonts/<F>/web --format woff2 --subset "latin+latin-ext"

# Verify imports haven't broken after edits
(cd scripts && ../venv/bin/python -c "import kern, variable, hint, baseline, build, metrics, rename, batch; print('ok')")

# Tests (86 unit + 8 integration against tests/fixtures/AtkinsonHyperlegibleNext-Regular.ttf)
venv/bin/pytest                       # everything
venv/bin/pytest -m "not integration"  # unit tests only (fast)
venv/bin/pytest -m integration        # fixture-font tests only

# Lint / format (configured in pyproject.toml)
venv/bin/ruff check .
venv/bin/ruff format .
```

## Docs

- [docs/guides/user-manual.md](docs/guides/user-manual.md) — complete technical reference (for developers).
- [docs/guides/quickstart.md](docs/guides/quickstart.md) — plain-language guide (for designers / hobbyists).
