"""Unit tests for scripts/kern.py pure functions.

Covers spec parsing and glyph-pattern resolution without loading fonts.
"""

import pytest
from kern import _fea_glyph, parse_spacing_rules, resolve_glyphs


class TestParseSpacingRules:
    def test_single_rule(self) -> None:
        assert parse_spacing_rules("lc:+10") == [("lc", 10)]

    def test_negative_delta(self) -> None:
        assert parse_spacing_rules("A-Z:-5") == [("A-Z", -5)]

    def test_multiple_rules(self) -> None:
        assert parse_spacing_rules("A-Z:-5,a-z:+10") == [("A-Z", -5), ("a-z", 10)]

    def test_whitespace_tolerated(self) -> None:
        assert parse_spacing_rules("  lc : +10 ,  uc : -5  ") == [
            ("lc", 10),
            ("uc", -5),
        ]

    def test_empty_string_returns_empty_list(self) -> None:
        assert parse_spacing_rules("") == []

    def test_trailing_comma_ignored(self) -> None:
        assert parse_spacing_rules("lc:+10,") == [("lc", 10)]

    def test_missing_colon_raises(self) -> None:
        with pytest.raises(ValueError, match="missing ':'"):
            parse_spacing_rules("badrule")

    def test_non_integer_delta_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_spacing_rules("lc:abc")


class TestResolveGlyphs:
    @pytest.fixture
    def glyph_order(self) -> list[str]:
        # A representative slice: caps, lowercase, digits, plus some
        # alts/composites with periods (legal in .fea identifiers).
        return [
            ".notdef",
            "A",
            "B",
            "C",
            "Z",
            "a",
            "b",
            "c",
            "z",
            "0",
            "1",
            "9",
            "A.alt",
            "B.alt",
            "Aacute",
            "comma",
        ]

    def test_preset_lc(self, glyph_order: list[str]) -> None:
        result = resolve_glyphs("lc", glyph_order)
        assert result == ["a", "b", "c", "z"]

    def test_preset_uc(self, glyph_order: list[str]) -> None:
        result = resolve_glyphs("uc", glyph_order)
        assert result == ["A", "B", "C", "Z"]

    def test_preset_digits(self, glyph_order: list[str]) -> None:
        assert resolve_glyphs("digits", glyph_order) == ["0", "1", "9"]

    def test_preset_all_returns_full_order(self, glyph_order: list[str]) -> None:
        # "all" preserves order and includes every glyph.
        assert resolve_glyphs("all", glyph_order) == glyph_order

    def test_character_range(self, glyph_order: list[str]) -> None:
        assert resolve_glyphs("A-C", glyph_order) == ["A", "B", "C"]

    def test_regex_pattern(self, glyph_order: list[str]) -> None:
        # Match anything ending in .alt
        assert resolve_glyphs("/\\.alt$/", glyph_order) == ["A.alt", "B.alt"]

    def test_literal_list(self, glyph_order: list[str]) -> None:
        # Mix of present and absent glyphs; absent ones get dropped.
        assert resolve_glyphs("A,B,XX", glyph_order) == ["A", "B"]

    def test_range_with_no_matches(self, glyph_order: list[str]) -> None:
        # Range Y-y spans codepoints not present in glyph_order.
        result = resolve_glyphs("y-y", glyph_order)
        assert result == []


class TestFeaGlyph:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("A", "A"),
            ("Aacute", "Aacute"),
            ("a.alt", "a.alt"),
            ("uni0041", "uni0041"),
            ("_private", "_private"),
            ("a.001", "a.001"),
        ],
    )
    def test_valid_identifier_unchanged(self, name: str, expected: str) -> None:
        assert _fea_glyph(name) == expected

    @pytest.mark.parametrize(
        "name",
        [
            "123abc",  # digit-leading
            "foo-bar",  # hyphen
            "foo bar",  # space
            ".notdef",  # leading period
            "a/b",  # slash
        ],
    )
    def test_invalid_identifier_escaped(self, name: str) -> None:
        # Anything that isn't a valid .fea identifier gets a backslash prefix
        # so feaLib treats it as a literal glyph name.
        assert _fea_glyph(name) == f"\\{name}"
