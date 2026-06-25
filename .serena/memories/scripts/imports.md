# Scripts: Structure & Imports

## Dual-purpose design
Each script in `scripts/` is BOTH:
- A standalone CLI tool (`python scripts/kern.py --help`)
- An importable library (`from kern import …` when `scripts/` is on sys.path)

**Critical: Use bare-name imports, NOT package-relative imports.** The MCP server adds `scripts/` to `sys.path` at startup; scripts can import each other the same way.

## Key scripts
- `kern.py` — analyze/modify kerning, detect non-standard kern tables
- `baseline.py` — shift glyphs vertically, keep metrics consistent
- `hint.py` — apply hinting via ttfautohint
- `build.py` — subset and convert to WOFF2
- `variable.py` — handle variable fonts
- `metrics.py` — inspect font metrics
- `rename.py` — normalize font filenames
- `batch.py` — batch operations on font families

## Imports across scripts
Scripts import each other for shared utilities:
```python
from kern import has_nonstandard_kern, strip_nonstandard_kern
from baseline import shift_glyphs
```

When refactoring, use `rename_symbol` to update all callers across all scripts atomically.

## MCP server integration
`mcp-server/server.py` imports scripts the same way; adds `scripts/` to `sys.path` before import.
