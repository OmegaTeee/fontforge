"""Direct tests for mcp-server/server.py tool functions."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def fixture_family_dir(tmp_path: Path, fixture_font_path: Path) -> Path:
    fonts_dir = tmp_path / "fonts"
    family_dir = fonts_dir / "Atkinson"
    family_dir.mkdir(parents=True)
    (family_dir / fixture_font_path.name).write_bytes(fixture_font_path.read_bytes())
    return fonts_dir


@pytest.fixture
def mcp_server_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_dir))

    module_path = Path(__file__).resolve().parent.parent / "mcp-server" / "server.py"
    spec = importlib.util.spec_from_file_location("fontforge_mcp_server_under_test", module_path)
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not load MCP server module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_list_families_returns_valid_json(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    result = json.loads(mcp_server_module.list_families())

    assert isinstance(result, list)
    assert result == [{"name": "Atkinson", "font_count": 1}]
    assert all("name" in entry and "font_count" in entry for entry in result)


def test_get_metrics_returns_expected_fields(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    fixture_font_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    result = json.loads(mcp_server_module.get_metrics("Atkinson", fixture_font_path.name))

    assert result["family"].startswith("Atkinson")
    assert result["glyph_count"] > 0
    assert result["file_size"] > 0


def test_font_file_tools_reject_path_traversal(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    for tool in (
        mcp_server_module.get_metrics,
        mcp_server_module.dump_kerning,
        mcp_server_module.variable_info,
    ):
        result = json.loads(tool("Atkinson", "../outside.ttf"))
        assert "path traversal" in result["error"]


def test_build_variable_rejects_output_name_path_traversal(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    result = json.loads(mcp_server_module.build_variable("Atkinson", "../outside.ttf"))

    assert "path traversal" in result["error"]


def test_family_dir_rejects_path_traversal(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    assert mcp_server_module._family_dir("../../etc") is None
    assert mcp_server_module._family_dir("../../../root") is None

    valid = mcp_server_module._family_dir("Atkinson")
    assert valid is not None
    assert valid.relative_to(fixture_family_dir.resolve())


def test_tool_call_writes_structured_log(
    mcp_server_module: ModuleType,
    fixture_family_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_server_module, "DEFAULT_FONTS_DIR", fixture_family_dir)

    mcp_server_module.list_families()

    log_path = tmp_path / "cache" / "fontforge" / "mcp.log"
    assert log_path.exists()
    assert "list_families" in log_path.read_text(encoding="utf-8")

    logger = mcp_server_module._configure_logging()
    assert logger.handlers
    assert logger.handlers[0].encoding == "utf-8"
