"""Integration tests that load the fixture font.

These tests exercise the scripts against a real TTF
(tests/fixtures/AtkinsonHyperlegibleNext-Regular.ttf) and are slower than
the unit tests (~50–100ms vs <1ms). Run unit tests only with:

    pytest -m "not integration"
"""

from pathlib import Path

import pytest
from baseline import fit_win_metrics, shift_glyphs, shift_metrics
from fontTools.ttLib import TTFont
from kern import extract_kerning, has_nonstandard_kern
from metrics import extract_metrics
from rename import get_font_names

pytestmark = pytest.mark.integration


class TestMetrics:
    def test_extract_metrics_basic_fields(self, fixture_font_path: Path) -> None:
        info = extract_metrics(fixture_font_path)
        assert info["family"].startswith("Atkinson Hyperlegible")
        assert info["subfamily"] == "Regular"
        assert info["weight_class"] == 400
        assert info["format"] == "TTF"
        assert info["glyph_count"] > 100
        # GPOS/GSUB are present — this is the modern OpenType layout pair.
        assert "GPOS" in info["tables"]
        assert "GSUB" in info["tables"]


class TestRenameNames:
    def test_get_font_names(self, fixture_font_path: Path) -> None:
        names = get_font_names(fixture_font_path)
        assert names["family"] is not None
        assert "Atkinson" in names["family"]
        # OS/2 weight class Regular
        assert names["weight_class"] == 400


class TestKern:
    def test_no_nonstandard_kern(self, fixture_font_path: Path) -> None:
        # Atkinson ships GPOS-only kerning — no legacy Apple `kern` table.
        # This is the negative case for has_nonstandard_kern; the positive
        # case (Burbank et al.) is documented in CLAUDE.md but not under
        # OFL so isn't in the test fixtures.
        font = TTFont(fixture_font_path)
        try:
            assert has_nonstandard_kern(font) is False
        finally:
            font.close()

    def test_extract_kerning_returns_pairs(self, fixture_font_path: Path) -> None:
        font = TTFont(fixture_font_path)
        try:
            pairs = extract_kerning(font)
        finally:
            font.close()
        # Atkinson has GPOS kerning — expect non-empty result with the
        # documented (lhs, rhs, value) tuple shape.
        assert len(pairs) > 0
        lhs, rhs, value = pairs[0]
        assert isinstance(lhs, str)
        assert isinstance(rhs, str)
        assert isinstance(value, int)


class TestBaseline:
    """The composite-shift behavior is the load-bearing invariant here.

    CLAUDE.md calls out a regression in AnthropicSans caused by adding
    `component.y += shift` to composites — they ended up at twice the
    intended shift. These tests pin the correct behavior: simple glyphs
    move by exactly `shift`, composite components' offsets stay put.
    """

    def test_shift_moves_simple_glyph_contours(self, fixture_font_path: Path) -> None:
        font = TTFont(fixture_font_path)
        try:
            glyf = font["glyf"]
            # Pick a glyph guaranteed to be a simple (non-composite) outline.
            # 'A' (numberOfContours > 0) is reliably present and simple in
            # virtually every Latin font.
            assert glyf["A"].numberOfContours > 0, "expected 'A' to be a simple glyph"
            before = list(glyf["A"].coordinates)

            shift = -40
            shift_glyphs(font, shift)

            after = list(glyf["A"].coordinates)
            assert len(before) == len(after)
            for (bx, by), (ax, ay) in zip(before, after, strict=True):
                assert ax == bx
                assert ay == by + shift
        finally:
            font.close()

    def test_shift_does_not_double_shift_composites(self, fixture_font_path: Path) -> None:
        # The regression test. Find a composite glyph (Aacute is reliable:
        # composite of A + acute in any Latin font with diacritics), grab
        # its component y-offsets, shift, and verify the offsets are
        # *unchanged*. If someone reintroduces `component.y += shift`,
        # this assertion fails immediately.
        font = TTFont(fixture_font_path)
        try:
            glyf = font["glyf"]
            assert glyf["Aacute"].numberOfContours == -1, (
                "expected 'Aacute' to be a composite glyph"
            )
            before_offsets = [(c.glyphName, c.x, c.y) for c in glyf["Aacute"].components]

            shift_glyphs(font, -40)

            after_offsets = [(c.glyphName, c.x, c.y) for c in glyf["Aacute"].components]
            assert before_offsets == after_offsets, (
                "composite component offsets must not be modified by shift_glyphs "
                "— they inherit the shift through their base glyphs already"
            )
        finally:
            font.close()

    def test_shift_metrics_updates_vertical_metrics(self, fixture_font_path: Path) -> None:
        font = TTFont(fixture_font_path)
        try:
            hhea_before = (font["hhea"].ascender, font["hhea"].descender)
            os2_before = (font["OS/2"].sTypoAscender, font["OS/2"].sTypoDescender)

            shift_metrics(font, -40)

            assert font["hhea"].ascender == hhea_before[0] - 40
            assert font["hhea"].descender == hhea_before[1] - 40
            assert font["OS/2"].sTypoAscender == os2_before[0] - 40
            assert font["OS/2"].sTypoDescender == os2_before[1] - 40
        finally:
            font.close()

    def test_fit_win_metrics_returns_non_negative_pair(self, fixture_font_path: Path) -> None:
        font = TTFont(fixture_font_path)
        try:
            ascent, descent = fit_win_metrics(font)
            # Both are unsigned magnitudes; usWinDescent stores descent
            # below baseline as a positive number.
            assert ascent > 0
            assert descent > 0
            # The function only grows values (via max(...)), so the result
            # is never smaller than what was already there.
            assert font["OS/2"].usWinAscent == ascent
            assert font["OS/2"].usWinDescent == descent
        finally:
            font.close()
