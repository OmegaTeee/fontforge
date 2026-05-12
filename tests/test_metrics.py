"""Unit tests for scripts/metrics.py pure functions."""

from metrics import classify_scripts


class TestClassifyScripts:
    def test_empty_set(self) -> None:
        assert classify_scripts(set()) == {}

    def test_basic_latin_only(self) -> None:
        # 'A', 'B', 'C' → Basic Latin = 3
        result = classify_scripts({0x41, 0x42, 0x43})
        assert result == {"Basic Latin": 3}

    def test_mixed_scripts(self) -> None:
        # Two Basic Latin + one Latin Extended-A
        result = classify_scripts({0x41, 0x42, 0x100})
        assert result == {"Basic Latin": 2, "Latin Extended-A": 1}

    def test_unmapped_codepoint_dropped(self) -> None:
        # Codepoint in no defined range (Tibetan, 0x0F00) is silently
        # excluded from the result — it doesn't show up as "Other".
        result = classify_scripts({0x0F00, 0x41})
        assert result == {"Basic Latin": 1}

    def test_cjk(self) -> None:
        # CJK ideographs
        result = classify_scripts({0x4E00, 0x4E01, 0x9FFF})
        assert result == {"CJK Unified": 3}

    def test_emoji_range(self) -> None:
        # 😀 U+1F600
        result = classify_scripts({0x1F600})
        assert result == {"Emoji": 1}

    def test_zero_counts_filtered_out(self) -> None:
        # Categories with 0 codepoints must not appear in the result dict.
        result = classify_scripts({0x41})
        assert "Cyrillic" not in result
        assert "Greek" not in result
        assert "Emoji" not in result
