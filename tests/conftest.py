"""Pytest configuration and shared fixtures.

`scripts/` is added to sys.path via `pythonpath` in pyproject.toml, so test
modules can `import rename`, `import kern`, etc. just like mcp-server does.
"""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_font_path() -> Path:
    """Path to the canonical test fixture (AtkinsonHyperlegibleNext-Regular).

    See tests/fixtures/README.md for why this specific font was chosen.
    """
    path = FIXTURES_DIR / "AtkinsonHyperlegibleNext-Regular.ttf"
    if not path.exists():
        pytest.fail(
            f"Fixture font missing: {path}. The test suite ships with "
            "AtkinsonHyperlegibleNext-Regular.ttf under tests/fixtures/ — "
            "see tests/fixtures/README.md."
        )
    return path
