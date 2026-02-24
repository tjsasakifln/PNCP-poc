"""Tests for STORY-258 AC18: Email normalization for duplicate detection.

Rules validated:
1. Lowercase + trim whitespace
2. Gmail/Googlemail: remove dots from local part
3. Gmail/Googlemail/Outlook/Hotmail/etc.: remove +alias
4. googlemail.com → gmail.com (canonical domain)
5. Non-Gmail dots are preserved
"""

import pytest
from utils.email_normalizer import normalize_email


class TestGmailNormalization:
    """Gmail-specific normalization: dots removed, +alias stripped, canonical domain."""

    def test_gmail_dots_removed(self):
        """Dots in Gmail local part must be removed."""
        assert normalize_email("j.o.h.n@gmail.com") == "john@gmail.com"

    def test_gmail_plus_alias_stripped(self):
        """Plus-alias on Gmail must be stripped."""
        assert normalize_email("john+test@gmail.com") == "john@gmail.com"

    def test_gmail_dots_and_plus_combined(self):
        """Both dots and +alias are handled together."""
        assert normalize_email("j.o.h.n+work@gmail.com") == "john@gmail.com"

    def test_gmail_uppercase_normalized(self):
        """Uppercase Gmail address is lowercased and normalized."""
        assert normalize_email("USER@Gmail.COM") == "user@gmail.com"

    def test_gmail_leading_trailing_whitespace(self):
        """Leading/trailing whitespace is trimmed."""
        assert normalize_email("  user@gmail.com  ") == "user@gmail.com"

    def test_googlemail_becomes_gmail(self):
        """googlemail.com is canonicalized to gmail.com."""
        assert normalize_email("user@googlemail.com") == "user@gmail.com"

    def test_googlemail_dots_removed_and_canonical(self):
        """googlemail.com: dots removed AND domain canonicalized."""
        assert normalize_email("j.o.h.n@googlemail.com") == "john@gmail.com"

    def test_googlemail_plus_alias_stripped(self):
        """googlemail.com +alias is stripped."""
        assert normalize_email("john+lists@googlemail.com") == "john@gmail.com"

    def test_gmail_multiple_dots(self):
        """Multiple consecutive dots in Gmail local are all removed."""
        assert normalize_email("a..b..c@gmail.com") == "abc@gmail.com"


class TestOutlookHotmailNormalization:
    """Outlook/Hotmail: +alias stripped, dots preserved."""

    def test_outlook_plus_alias_stripped(self):
        """Plus-alias on Outlook is stripped."""
        assert normalize_email("john+news@outlook.com") == "john@outlook.com"

    def test_hotmail_plus_alias_stripped(self):
        """Plus-alias on Hotmail is stripped."""
        assert normalize_email("john+test@hotmail.com") == "john@hotmail.com"

    def test_outlook_dots_preserved(self):
        """Dots in Outlook local part are NOT removed (different from Gmail)."""
        assert normalize_email("j.o.h.n@outlook.com") == "j.o.h.n@outlook.com"

    def test_hotmail_dots_preserved(self):
        """Dots in Hotmail local part are preserved."""
        assert normalize_email("john.doe@hotmail.com") == "john.doe@hotmail.com"

    def test_outlook_uppercase_lowercased(self):
        """Uppercase Outlook address is lowercased."""
        assert normalize_email("USER@OUTLOOK.COM") == "user@outlook.com"


class TestCorporateEmailNormalization:
    """Corporate emails: only lowercase/trim, no dot/alias manipulation."""

    def test_corporate_lowercase(self):
        """Corporate email is lowercased."""
        assert normalize_email("User@Company.Com.Br") == "user@company.com.br"

    def test_corporate_whitespace_trimmed(self):
        """Whitespace around corporate email is trimmed."""
        assert normalize_email("  user@empresa.com.br  ") == "user@empresa.com.br"

    def test_corporate_dots_preserved(self):
        """Dots in corporate local part are preserved."""
        assert normalize_email("joao.silva@empresa.com.br") == "joao.silva@empresa.com.br"

    def test_corporate_plus_alias_preserved(self):
        """Plus-alias in corporate email is preserved (no alias stripping for unknown domains)."""
        assert normalize_email("user+tag@empresa.com.br") == "user+tag@empresa.com.br"

    def test_gov_br_domain(self):
        """Government .gov.br domains are only lowercased."""
        assert normalize_email("Servidor@Prefeitura.SP.GOV.BR") == "servidor@prefeitura.sp.gov.br"


class TestEdgeCases:
    """Edge cases for email normalization."""

    def test_empty_string_returns_empty(self):
        """Empty string returns empty string."""
        assert normalize_email("") == ""

    def test_no_at_sign(self):
        """String without @ is lowercased and returned as-is."""
        assert normalize_email("NOTANEMAIL") == "notanemail"

    def test_whitespace_only(self):
        """Whitespace-only string returns empty string."""
        assert normalize_email("   ") == ""

    def test_already_normalized(self):
        """Already normalized email is idempotent."""
        assert normalize_email("user@gmail.com") == "user@gmail.com"
        assert normalize_email("john@outlook.com") == "john@outlook.com"

    def test_mixed_case_domain(self):
        """Mixed-case domain is lowercased."""
        assert normalize_email("user@GMAIL.COM") == "user@gmail.com"

    def test_protonmail_plus_alias_stripped(self):
        """ProtonMail +alias is stripped per _PLUS_ALIAS_DOMAINS."""
        assert normalize_email("user+work@protonmail.com") == "user@protonmail.com"

    def test_live_com_plus_alias_stripped(self):
        """live.com +alias is stripped."""
        assert normalize_email("user+filter@live.com") == "user@live.com"
