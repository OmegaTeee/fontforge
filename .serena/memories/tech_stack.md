# Tech Stack & Environment

## Language & Runtime
- **Python 3.14**, venv at `venv/`
- Always run as: `source venv/bin/activate && python …` or `venv/bin/python …` (never system Python)

## Dependencies
- `requirements.txt` pinned
- **Critical quirk**: `ufo-extractor` is `git+https://github.com/typesupply/extractor.git` (PyPI name `extractor` is squatted by unrelated keyword-extraction package)
- fontTools, fontMath, defconAppKit, ttfautohint (via shell), pytest

## External binaries
- **ttfautohint** (Homebrew) — used by `scripts/hint.py` via subprocess

## Fonts directory resolution
Priority order:
1. `--fonts-dir` CLI flag
2. `$FONTFORGE_FONTS_DIR` env var (recommended: shared across MCP server, VSCode launch configs, shell)
3. In-repo `fonts/` (default for local dev)
4. Test fixture lives separately in `tests/fixtures/` (self-contained test suite)

## MCP Server
- `mcp-server/server.py` adds `scripts/` to `sys.path` and imports by bare name
- Registered commands for all font operations (metrics, kerning, hinting, building, etc.)
- Available via `.mcp.json` in Claude Code
