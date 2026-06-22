"""Unit tests for scripts/build.py pure functions.

Covers Unicode subset parsing without invoking fontTools' subsetter.
"""

from pathlib import Path

from build import UNICODE_RANGES, load_subset_codepoints, parse_unicode_ranges


class TestParseUnicodeRanges:
    def test_single_codepoint(self) -> None:
        assert parse_unicode_ranges("U+0041") == [0x41]

    def test_lowercase_u_prefix(self) -> None:
        assert parse_unicode_ranges("u+0041") == [0x41]

    def test_no_prefix(self) -> None:
        # The function strips both "U+" and "u+" — bare hex should still work.
        assert parse_unicode_ranges("0041") == [0x41]

    def test_range(self) -> None:
        # A..C inclusive
        assert parse_unicode_ranges("U+0041-0043") == [0x41, 0x42, 0x43]

    def test_multiple_entries(self) -> None:
        # Mix single + range, ensure sorted dedup output
        result = parse_unicode_ranges("U+0041,U+0061-0062,U+0041")
        assert result == [0x41, 0x61, 0x62]

    def test_whitespace_tolerated(self) -> None:
        assert parse_unicode_ranges(" U+0041 , U+0042 ") == [0x41, 0x42]


class TestLoadSubsetCodepoints:
    def test_none_returns_none(self) -> None:
        assert load_subset_codepoints(None, None) is None

    def test_named_range_latin(self) -> None:
        result = load_subset_codepoints("latin", None)
        assert result is not None
        # 'A' is in basic Latin; verify it landed in the codepoint list.
        assert 0x41 in result
        # Result is sorted with no duplicates.
        assert result == sorted(set(result))

    def test_named_range_case_insensitive(self) -> None:
        # Both calls should yield the same set.
        a = load_subset_codepoints("Latin", None)
        b = load_subset_codepoints("latin", None)
        assert a == b

    def test_combined_named_ranges(self) -> None:
        latin = set(load_subset_codepoints("latin", None) or [])
        combined = set(load_subset_codepoints("latin+latin-ext", None) or [])
        # latin+latin-ext is a strict superset of latin alone.
        assert latin.issubset(combined)
        assert len(combined) > len(latin)

    def test_unknown_named_range_returns_none(self) -> None:
        # Single unknown name doesn't match the "+" branch and falls through
        # all branches, returning None.
        assert load_subset_codepoints("klingon", None) is None

    def test_raw_unicode_range_is_reachable(self) -> None:
        assert load_subset_codepoints("U+0041-0043", None) == [0x41, 0x42, 0x43]

    def test_subset_file(self, tmp_path: Path) -> None:
        # Subset file branch: read characters from a file, skip whitespace.
        f = tmp_path / "chars.txt"
        f.write_text("ABC\n   X", encoding="utf-8")
        result = load_subset_codepoints(None, f)
        assert result == [0x41, 0x42, 0x43, 0x58]

    def test_known_ranges_registered(self) -> None:
        # Sanity: the named ranges expected by the pipeline are present.
        for name in ("latin", "latin-ext", "cyrillic", "greek", "vietnamese"):
            assert name in UNICODE_RANGES
