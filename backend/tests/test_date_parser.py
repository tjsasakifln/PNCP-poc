"""Tests for date_parser utility (GTM-FIX-011 AC28).

Covers:
- br_to_iso: DD/MM/AAAA -> YYYY-MM-DD
- iso_to_br: YYYY-MM-DD -> DD/MM/AAAA
- parse_date_flexible: accepts both formats
- Edge cases: invalid dates, leap years, roundtrips
"""

from datetime import datetime

from utils.date_parser import br_to_iso, iso_to_br, parse_date_flexible


# br_to_iso

def test_br_to_iso_valid():
    assert br_to_iso("15/01/2026") == "2026-01-15"
    assert br_to_iso("01/12/2024") == "2024-12-01"
    assert br_to_iso("31/03/2025") == "2025-03-31"


def test_br_to_iso_leap_year_valid():
    assert br_to_iso("29/02/2024") == "2024-02-29"


def test_br_to_iso_non_leap_year_invalid():
    assert br_to_iso("29/02/2025") is None


def test_br_to_iso_feb_31_invalid():
    assert br_to_iso("31/02/2026") is None


def test_br_to_iso_wrong_format():
    assert br_to_iso("2026/01/15") is None
    assert br_to_iso("15-01-2026") is None
    assert br_to_iso("2026-01-15") is None


def test_br_to_iso_empty():
    assert br_to_iso("") is None


def test_br_to_iso_none():
    assert br_to_iso(None) is None


def test_br_to_iso_partial():
    assert br_to_iso("15/01") is None
    assert br_to_iso("15") is None


# iso_to_br

def test_iso_to_br_valid():
    assert iso_to_br("2026-01-15") == "15/01/2026"
    assert iso_to_br("2024-12-01") == "01/12/2024"


def test_iso_to_br_leap_year_valid():
    assert iso_to_br("2024-02-29") == "29/02/2024"


def test_iso_to_br_non_leap_year_invalid():
    assert iso_to_br("2025-02-29") is None


def test_iso_to_br_feb_31_invalid():
    assert iso_to_br("2024-02-31") is None


def test_iso_to_br_wrong_format():
    assert iso_to_br("15/01/2026") is None
    assert iso_to_br("2026/01/15") is None


def test_iso_to_br_empty():
    assert iso_to_br("") is None


def test_iso_to_br_none():
    assert iso_to_br(None) is None


# parse_date_flexible

def test_flexible_br_format():
    result = parse_date_flexible("15/01/2026")
    assert isinstance(result, datetime)
    assert result == datetime(2026, 1, 15)


def test_flexible_iso_format():
    result = parse_date_flexible("2026-01-15")
    assert isinstance(result, datetime)
    assert result == datetime(2026, 1, 15)


def test_flexible_invalid():
    assert parse_date_flexible("31/02/2026") is None
    assert parse_date_flexible("2026-02-31") is None


def test_flexible_empty():
    assert parse_date_flexible("") is None


def test_flexible_none():
    assert parse_date_flexible(None) is None


def test_flexible_unrecognized():
    assert parse_date_flexible("Jan 15, 2026") is None
    assert parse_date_flexible("2026/01/15") is None


# Roundtrip

def test_roundtrip_br_iso_br():
    original = "15/01/2026"
    assert iso_to_br(br_to_iso(original)) == original


def test_roundtrip_iso_br_iso():
    original = "2026-01-15"
    assert br_to_iso(iso_to_br(original)) == original


def test_roundtrip_leap_year():
    assert iso_to_br(br_to_iso("29/02/2024")) == "29/02/2024"


def test_consistency_both_formats_same_datetime():
    br_result = parse_date_flexible("15/01/2026")
    iso_result = parse_date_flexible("2026-01-15")
    assert br_result == iso_result
