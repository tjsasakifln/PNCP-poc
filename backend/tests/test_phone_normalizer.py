"""Tests for STORY-258 AC19: Brazilian phone number normalization.

Rules:
1. Remove all non-digit characters
2. Strip country code +55 or 55 prefix
3. Strip leading 0 (legacy DDD prefix)
4. Result must be 10 digits (fixo) or 11 digits (celular)
"""

import pytest
from utils.phone_normalizer import normalize_phone, format_phone_display


class TestNormalizePhone:
    """Test normalize_phone function."""

    # -----------------------------------------------------------------
    # Standard Brazilian formats
    # -----------------------------------------------------------------

    def test_formatted_cell_with_parens_and_hyphen(self):
        """(11) 99999-1234 → 11999991234"""
        assert normalize_phone("(11) 99999-1234") == "11999991234"

    def test_with_country_code_plus_prefix(self):
        """+55 11 99999-1234 → 11999991234"""
        assert normalize_phone("+55 11 99999-1234") == "11999991234"

    def test_with_country_code_no_plus(self):
        """5511999991234 → 11999991234 (strips 55 prefix when ≥12 digits)"""
        assert normalize_phone("5511999991234") == "11999991234"

    def test_with_legacy_trunk_zero(self):
        """011 99999-1234 → 11999991234 (strips leading 0)"""
        assert normalize_phone("011 99999-1234") == "11999991234"

    def test_fixed_line_10_digits(self):
        """(11) 3333-4444 → 1133334444 (10-digit landline)"""
        assert normalize_phone("(11) 3333-4444") == "1133334444"

    def test_plain_11_digits(self):
        """11 digits without formatting returns unchanged."""
        assert normalize_phone("11999991234") == "11999991234"

    def test_plain_10_digits(self):
        """10 digits without formatting returns unchanged."""
        assert normalize_phone("1133334444") == "1133334444"

    def test_spaces_only_format(self):
        """Phone with spaces only: 11 99999 1234 → 11999991234"""
        assert normalize_phone("11 99999 1234") == "11999991234"

    def test_dots_as_separator(self):
        """Phone with dots: 11.99999.1234 → 11999991234"""
        assert normalize_phone("11.99999.1234") == "11999991234"

    # -----------------------------------------------------------------
    # Invalid inputs
    # -----------------------------------------------------------------

    def test_none_returns_none(self):
        """None input returns None."""
        assert normalize_phone(None) is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        assert normalize_phone("") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only returns None."""
        assert normalize_phone("   ") is None

    def test_too_short_returns_none(self):
        """Fewer than 10 digits after stripping → invalid → None."""
        assert normalize_phone("123") is None
        assert normalize_phone("9") is None
        assert normalize_phone("123456789") is None  # 9 digits

    def test_too_long_returns_none(self):
        """More than 11 digits after stripping (not 55+10/11) → None."""
        assert normalize_phone("999999999999999") is None  # 15 digits

    def test_letters_only_returns_none(self):
        """Non-numeric input with no digits returns None."""
        assert normalize_phone("abc-def-ghij") is None

    def test_mixed_valid_letters_stripped(self):
        """Letters are stripped; if remaining digits are valid, OK."""
        assert normalize_phone("(11) 9abc9999-1234") == "11999991234"

    # -----------------------------------------------------------------
    # Country code edge cases
    # -----------------------------------------------------------------

    def test_country_code_stripped_only_when_12_plus_digits(self):
        """55 prefix is stripped only when the total is ≥ 12 digits."""
        # "5511" (4 digits) — does NOT strip 55 (only 4 digits total)
        assert normalize_phone("5511") is None  # too short

    def test_full_international_format(self):
        """+55 (11) 9 9999-1234 → 11999991234"""
        assert normalize_phone("+55 (11) 9 9999-1234") == "11999991234"


class TestFormatPhoneDisplay:
    """Test format_phone_display function."""

    def test_format_11_digit_cell(self):
        """11-digit cell: 11999991234 → (11) 99999-1234"""
        assert format_phone_display("11999991234") == "(11) 99999-1234"

    def test_format_10_digit_landline(self):
        """10-digit landline: 1133334444 → (11) 3333-4444"""
        assert format_phone_display("1133334444") == "(11) 3333-4444"

    def test_format_none_returns_empty(self):
        """None returns empty string."""
        assert format_phone_display(None) == ""

    def test_format_empty_returns_empty(self):
        """Empty string returns empty string."""
        assert format_phone_display("") == ""

    def test_format_invalid_returns_original(self):
        """Invalid digit count returns original input unchanged."""
        assert format_phone_display("12345") == "12345"

    def test_format_with_non_digits_in_input(self):
        """Input with formatting is re-formatted after stripping non-digits."""
        # format_phone_display strips non-digits internally
        assert format_phone_display("(11) 99999-1234") == "(11) 99999-1234"

    def test_different_ddd_codes(self):
        """Various DDD codes are formatted correctly."""
        assert format_phone_display("21988887777") == "(21) 98888-7777"
        assert format_phone_display("4733334444") == "(47) 3333-4444"
        assert format_phone_display("85912345678") == "(85) 91234-5678"
