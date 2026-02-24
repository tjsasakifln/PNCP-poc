"""Tests for STORY-258 AC17: Disposable email domain detection.

Validates:
- Known disposable domains return True
- Legitimate/personal/corporate domains return False
- Edge cases: empty string, no @ sign, None
"""

import pytest
from utils.disposable_emails import is_disposable_email, is_corporate_email


class TestIsDisposableEmail:
    """Test disposable email detection."""

    @pytest.mark.parametrize("email", [
        "user@tempmail.com",
        "someone@guerrillamail.com",
        "test@mailinator.com",
        "test@yopmail.com",
        "test@throwaway.email",
        "test@trashmail.com",
        "test@dispostable.com",
        "test@10minutemail.com",
        "test@maildrop.cc",
        "test@fakeinbox.com",
        "test@emailtemporario.com.br",
        "test@tempmail.com.br",
        "test@lixomail.com.br",
        "test@spambox.com.br",
        "test@mailnesia.com",
        "test@sharklasers.com",
        "test@discard.email",
        "test@mohmal.com",
    ])
    def test_known_disposable_domains_return_true(self, email: str):
        """Known disposable email domains must be detected."""
        assert is_disposable_email(email) is True, f"Expected {email} to be disposable"

    @pytest.mark.parametrize("email", [
        "user@gmail.com",
        "john.doe@outlook.com",
        "pessoa@hotmail.com",
        "someone@yahoo.com",
        "empresa@empresa.com.br",
    ])
    def test_legitimate_domains_return_false(self, email: str):
        """Legitimate email providers must NOT be flagged as disposable."""
        assert is_disposable_email(email) is False, f"Expected {email} NOT to be disposable"

    def test_empty_string_returns_false(self):
        """Empty string is not disposable."""
        assert is_disposable_email("") is False

    def test_no_at_sign_returns_false(self):
        """String without @ cannot have a domain — not disposable."""
        assert is_disposable_email("notanemail") is False

    def test_none_returns_false(self):
        """None is treated as non-disposable (no crash)."""
        assert is_disposable_email(None) is False  # type: ignore[arg-type]

    def test_case_insensitive_domain(self):
        """Detection works regardless of domain case — function lowercases the domain internally."""
        # The function lowercases the domain via rsplit, so mixed-case is detected
        assert is_disposable_email("user@TempMail.COM") is True
        assert is_disposable_email("user@TEMPMAIL.COM") is True
        assert is_disposable_email("user@Gmail.COM") is False

    def test_subdomain_not_flagged(self):
        """Subdomains of disposable domains are NOT in the blocklist."""
        # sub.tempmail.com is not in the set (only exact match)
        assert is_disposable_email("user@sub.tempmail.com") is False

    def test_email_with_plus_alias(self):
        """Plus-alias emails use the same domain check."""
        assert is_disposable_email("user+spam@mailinator.com") is True
        assert is_disposable_email("user+work@gmail.com") is False

    def test_email_with_dots_in_local(self):
        """Dots in local part don't affect domain detection."""
        assert is_disposable_email("j.o.h.n@tempmail.com") is True
        assert is_disposable_email("j.o.h.n@gmail.com") is False

    def test_at_only_email(self):
        """'@' alone without local or domain returns False gracefully."""
        # '@' splits into ['', ''] — domain is '' which is not in set
        assert is_disposable_email("@") is False

    def test_multiple_at_signs(self):
        """Multiple @ — uses rsplit to get last segment as domain."""
        # rsplit("@", 1) gives ["local@part", "domain"]
        # For "a@b@tempmail.com" → domain is "tempmail.com"
        assert is_disposable_email("a@b@tempmail.com") is True


class TestIsCorporateEmail:
    """Test corporate email detection."""

    @pytest.mark.parametrize("email", [
        "contato@empresa.com.br",
        "joao@confenge.com.br",
        "compras@prefeitura.sp.gov.br",
        "usuario@minhaempresa.tech",
        "rh@corporativo.com",
    ])
    def test_corporate_domains_return_true(self, email: str):
        """Non-personal, non-disposable domains are considered corporate."""
        assert is_corporate_email(email) is True, f"Expected {email} to be corporate"

    @pytest.mark.parametrize("email", [
        "user@gmail.com",
        "user@outlook.com",
        "user@hotmail.com",
        "user@yahoo.com",
        "user@yahoo.com.br",
        "user@icloud.com",
        "user@protonmail.com",
        "user@uol.com.br",
        "user@bol.com.br",
    ])
    def test_personal_providers_are_not_corporate(self, email: str):
        """Known personal email providers are NOT corporate."""
        assert is_corporate_email(email) is False, f"Expected {email} NOT to be corporate"

    @pytest.mark.parametrize("email", [
        "user@tempmail.com",
        "user@mailinator.com",
        "user@guerrillamail.com",
    ])
    def test_disposable_domains_not_corporate(self, email: str):
        """Disposable emails are never corporate."""
        assert is_corporate_email(email) is False, f"Expected {email} NOT to be corporate"

    def test_empty_string_returns_false(self):
        """Empty string returns False."""
        assert is_corporate_email("") is False

    def test_no_at_sign_returns_false(self):
        """No @ sign cannot be corporate."""
        assert is_corporate_email("notanemail") is False

    def test_none_returns_false(self):
        """None is handled gracefully."""
        assert is_corporate_email(None) is False  # type: ignore[arg-type]
