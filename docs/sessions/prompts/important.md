Fix all "Important" priority items from TODOS.md in mcp-server/server.py and the repo.
Work through each item below in order. After each change, run the test suite before
proceeding to the next.

---

## Item 1: Add direct tests for MCP server tools

File: tests/test_mcp_server.py (create new)

The MCP tool functions in mcp-server/server.py can be invoked directly without
spinning up stdio. Add a test module covering the following tools:

- `list_families()` — assert it returns valid JSON, result is a list, each entry
  has "name" and "font_count" keys. Use the in-repo fonts/ directory or
  tests/fixtures/ as the source.
- `get_metrics(family, font_file)` — call against
  tests/fixtures/AtkinsonHyperlegibleNext-Regular.ttf. Assert result contains
  "glyph_count", "family", "file_size" keys.
- `_family_dir(family)` — test path-traversal rejection cases:
  - "../../etc" → returns None
  - "../../../root" → returns None
  - A valid family dir name → returns a Path inside DEFAULT_FONTS_DIR
  (Note: if the Critical path-traversal fix has already been applied, these
  tests should pass. If not, add the fix per the Critical section of TODOS.md
  before writing tests.)

Do not spin up the MCP stdio server. Call functions directly after importing
from mcp-server/server.py (it's importable — sys.path is set by conftest or
the test module itself via sys.path.insert).

---

## Item 2: Structured request/error logging

File: mcp-server/server.py

Add a minimal logging setup that activates when the server starts:
- Log destination: ~/.cache/fontforge/mcp.log (create dirs if missing; respect
  XDG_CACHE_HOME if set)
- Log format per tool call: timestamp, tool name, arguments (truncated to 200
  chars), elapsed ms, exception type+message if any
- Implementation: a decorator or wrapper applied to each @mcp.tool() function.
  Do not modify tool signatures or return types.
- Log level: INFO for normal calls, ERROR for exceptions
- The log file must not grow unboundedly — use a RotatingFileHandler
  (maxBytes=1_000_000, backupCount=3)

Add one test: verify that after calling list_families(), the log file at the
expected path contains a line with "list_families".

---

## Item 3: GitHub Actions CI

File: .github/workflows/ci.yml (create new)

Add a CI workflow that runs on push and pull_request to any branch:

- Name: CI
- Job: test
- Runner: ubuntu-latest
- Steps:
  1. Checkout
  2. Set up Python 3.14 (use actions/setup-python, try deadsnakes/action if
     3.14 isn't available on ubuntu-latest yet)
  3. Install ttfautohint: `sudo apt-get install -y ttfautohint`
  4. Create venv and install: `python -m venv venv && venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
  5. Ruff check: `venv/bin/ruff check .`
  6. Pytest (unit only, fast): `venv/bin/pytest -m "not integration"`

Do not add caching for now — keep the file simple.

---

## Constraints

- Python 3.14, venv at venv/. Use venv/bin/python for all Python commands.
- After all changes: run `venv/bin/ruff format mcp-server/server.py tests/test_mcp_server.py`
- Run full test suite: `venv/bin/pytest` — all 94+ tests must pass.
- Prefer new commits over --amend.
- Do not change any script public APIs or MCP tool signatures.
