"""Unit tests for scripts/rename.py pure functions.

Covers filename/name-table normalization without needing real font files.
"""

from pathlib import Path

import pytest
from rename import (
    compute_new_name_from_filename,
    normalize_family,
    normalize_subfamily,
    parse_family_from_filename,
    parse_weight_from_filename,
)


class TestNormalizeFamily:
    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Google Sans", "GoogleSans"),
            ("adobe garamond", "AdobeGaramond"),
            ("Adobe-Garamond", "AdobeGaramond"),
            ("Adobe_Garamond", "AdobeGaramond"),
            ("GoogleSans", "GoogleSans"),
            ("PPLX Sans Beta (v2)", "PPLXSansBeta"),
            ("  Burbank  ", "Burbank"),
            ("Family   With   Spaces", "FamilyWithSpaces"),
        ],
    )
    def test_normalize_family(self, input_name: str, expected: str) -> None:
        assert normalize_family(input_name) == expected

    def test_short_lowercase_tokens_preserved(self) -> None:
        # Tokens <=2 chars stay as-is (no capitalize) — see rename.py:112.
        assert normalize_family("pt sans") == "ptSans"

    def test_mixed_case_token_preserved(self) -> None:
        assert normalize_family("PPLX Mono") == "PPLXMono"


class TestNormalizeSubfamily:
    @pytest.mark.parametrize(
        ("subfamily", "weight_class", "expected"),
        [
            ("Bold", None, "Bold"),
            ("Regular", None, "Regular"),
            ("Bold Italic", None, "BoldItalic"),
            ("Italic", None, "Italic"),
            ("Extra Bold", None, "ExtraBold"),
            ("SemiBold Italic", None, "SemiBoldItalic"),
            ("", 700, "Bold"),
            ("", 400, "Regular"),
            ("", None, "Regular"),
            ("italic", 400, "Italic"),
        ],
    )
    def test_normalize_subfamily(
        self, subfamily: str, weight_class: int | None, expected: str
    ) -> None:
        assert normalize_subfamily(subfamily, weight_class) == expected

    def test_unknown_subfamily_falls_back_to_weight_class(self) -> None:
        # When the string doesn't match any alias, weight_class wins.
        assert normalize_subfamily("WeirdName", 900) == "Black"

    def test_longest_alias_wins(self) -> None:
        # "extrabold" must beat "bold" (rename.py sorts by descending length).
        assert normalize_subfamily("ExtraBold", None) == "ExtraBold"


class TestParseWeightFromFilename:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("(Bold) Family.ttf", "Bold"),
            ("(Light) Some Family.otf", "Light"),
            ("Family - Bold.ttf", "Bold"),
            ("Family - SemiBold.ttf", "SemiBold"),
            ("Family.ttf", "Regular"),
            ("Family-Regular.ttf", "Regular"),
            ("(Unknown) Family.ttf", "Regular"),
        ],
    )
    def test_parse_weight(self, filename: str, expected: str) -> None:
        assert parse_weight_from_filename(filename) == expected


class TestParseFamilyFromFilename:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("(Bold) Adobe Garamond.ttf", "AdobeGaramond"),
            ("Adobe Garamond - Bold.ttf", "AdobeGaramond"),
            ("GoogleSans-Regular.ttf", "GoogleSans"),
            ("Family.ttf", "Family"),
        ],
    )
    def test_parse_family(self, filename: str, expected: str) -> None:
        assert parse_family_from_filename(filename) == expected


class TestComputeNewNameFromFilename:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (Path("(Bold) Adobe Garamond.ttf"), "AdobeGaramond-Bold.ttf"),
            (Path("Family.ttf"), "Family-Regular.ttf"),
            (Path("Family-Black.woff2"), "Family-Black.woff2"),
            (Path("Family - SemiBold.otf"), "Family-SemiBold.otf"),
        ],
    )
    def test_compute_new_name(self, path: Path, expected: str) -> None:
        assert compute_new_name_from_filename(path) == expected

    def test_italic_only_filename_does_not_roundtrip(self) -> None:
        # `parse_weight_from_filename` only recognizes WEIGHT_ALIASES (Bold,
        # Light, …) — "Italic" is a style, not a weight, so it isn't stripped
        # from the family and isn't carried forward as a subfamily. Documented
        # here so a future "fix" doesn't silently change name-table behavior.
        result = compute_new_name_from_filename(Path("Family - Italic.otf"))
        assert result == "FamilyItalic-Regular.otf"
