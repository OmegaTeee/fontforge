# Code Conventions

## Naming
- Script functions use snake_case: `shift_glyphs`, `has_nonstandard_kern`
- Classes use PascalCase: `RotatingFileHandler`
- Module-level constants are UPPER_CASE

## Comments
- Default: no comments
- Only add when the WHY is non-obvious: hidden constraint, subtle invariant, workaround for specific bug
- Brevity: if removing the comment wouldn't confuse a reader, don't write it

## Error handling
- Validate at trust boundaries (user input, external APIs)
- Trust internal code and framework guarantees
- Don't add fallbacks for scenarios that can't happen

## Testing
- 86 unit + 8 integration tests against `tests/fixtures/AtkinsonHyperlegibleNext-Regular.ttf`
- Unit tests marked with `@pytest.mark.not integration`
- Integration tests marked with `@pytest.mark.integration`
- Run with: `pytest` (all), `pytest -m "not integration"` (unit only), `pytest -m integration` (fixture only)

## Linting
- Ruff (lint + format)
- Config in `pyproject.toml`
- Run: `ruff check .` and `ruff format .`

## Import verification
After script changes, verify imports don't break:
```bash
(cd scripts && ../venv/bin/python -c "import kern, variable, hint, baseline, build, metrics, rename, batch; print('ok')")
```

## Commit hygiene
- Prefer new commits over `--amend`
- `.claude/settings.local.json` is per-machine and gitignored
