# Common Commands

## Inspection
```bash
# Inspect any font
venv/bin/python scripts/metrics.py fonts/<Family>/<File>.ttf
```

## Full web pipeline (after sanity-checking metrics)
```bash
# 1. Baseline/spacing (example: shift by -40)
venv/bin/python scripts/baseline.py fonts/<F>/ --shift -40 -o fonts/<F>/shifted

# 2. Hinting (example: strong hinting)
venv/bin/python scripts/hint.py fonts/<F>/shifted/ -o fonts/<F>/hinted --strong

# 3. Build for web (example: latin subset to WOFF2)
venv/bin/python scripts/build.py fonts/<F>/hinted/ -o fonts/<F>/web --format woff2 --subset "latin+latin-ext"
```

## Verification
```bash
# Verify imports haven't broken
(cd scripts && ../venv/bin/python -c "import kern, variable, hint, baseline, build, metrics, rename, batch; print('ok')")

# Run all tests
venv/bin/pytest

# Unit tests only (fast)
venv/bin/pytest -m "not integration"

# Integration tests only
venv/bin/pytest -m integration

# Lint & format
venv/bin/ruff check .
venv/bin/ruff format .
```

## MCP server
```bash
# Test startup
/opt/homebrew/bin/uvx --from "git+https://github.com/oraios/serena" serena start-mcp-server --project-from-cwd --context vscode
```
