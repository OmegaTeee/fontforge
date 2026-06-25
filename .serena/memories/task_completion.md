# Task Completion Checklist

## For any font script changes
1. Run verification import check:
   ```bash
   (cd scripts && ../venv/bin/python -c "import kern, variable, hint, baseline, build, metrics, rename, batch; print('ok')")
   ```
2. Run full test suite:
   ```bash
   venv/bin/pytest
   ```
3. Run linting:
   ```bash
   venv/bin/ruff check .
   ```

## For font processing pipeline work
1. After baseline shifts: Delete old hinted/ and web/ directories if re-running
2. Verify metrics consistency: `venv/bin/python scripts/metrics.py <input> <output>`
3. Sanity-check file sizes before/after subsetting

## For MCP server changes
1. Verify server starts without errors
2. Test a few MCP commands via Claude Code to confirm they resolve correctly

## For font family additions
1. Inspect metrics: `venv/bin/python scripts/metrics.py fonts/<Family>/<File>.ttf`
2. Check for non-standard kern tables: `venv/bin/python scripts/kern.py fonts/<Family>/ --check`
3. Run full pipeline as dry-run to validate before committing

## Before committing
- All tests pass (`pytest`)
- No lint errors (`ruff check .`)
- Fonts are committed (they're the product)
- `.claude/settings.local.json` is NOT committed (per-machine config)
