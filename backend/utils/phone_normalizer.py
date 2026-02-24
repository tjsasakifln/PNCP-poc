"""STORY-258 AC8: Brazilian phone number normalization.

Rules:
1. Remove all non-digit characters
2. Strip country code +55 or 55 prefix
3. Strip leading 0 (legacy DDD prefix)
4. Result: 10 or 11 digits (DDD + number)
"""

import re


def normalize_phone(phone: str | None) -> str | None:
    """Normalize a Brazilian phone number to digits-only format.

    Args:
        phone: Raw phone string (may include +55, spaces, parens, hyphens).

    Returns:
        Normalized phone string (10-11 digits) or None if invalid/empty.

    Examples:
        >>> normalize_phone("(11) 99999-1234")
        '11999991234'
        >>> normalize_phone("+55 11 99999-1234")
        '11999991234'
        >>> normalize_phone("011 99999-1234")
        '11999991234'
        >>> normalize_phone(None)
        >>> normalize_phone("")
        >>> normalize_phone("123")
    """
    if not phone:
        return None

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None

    # Strip country code +55 (Brazil)
    if digits.startswith("55") and len(digits) >= 12:
        digits = digits[2:]

    # Strip leading 0 (legacy trunk prefix)
    if digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]

    # Valid Brazilian phone: 10 digits (fixo) or 11 digits (celular)
    if len(digits) not in (10, 11):
        return None

    return digits


def format_phone_display(phone: str | None) -> str:
    """Format a normalized phone for display.

    Args:
        phone: Normalized phone string (10-11 digits).

    Returns:
        Formatted string like "(11) 99999-1234" or empty string.
    """
    if not phone:
        return ""

    digits = re.sub(r"\D", "", phone)

    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return phone
