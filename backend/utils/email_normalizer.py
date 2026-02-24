"""STORY-258 AC4: Email normalization for duplicate detection.

Rules:
1. Lowercase + trim
2. Gmail/Googlemail: remove dots from local part
3. Gmail/Googlemail/Outlook/Hotmail: remove +alias
4. googlemail.com → gmail.com
"""

# Domains where dots in local part are ignored
_DOT_IGNORE_DOMAINS = frozenset({"gmail.com", "googlemail.com"})

# Domains where +alias is stripped
_PLUS_ALIAS_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
    "live.com", "protonmail.com", "proton.me", "pm.me",
})

# Domain canonicalization
_DOMAIN_CANONICAL = {
    "googlemail.com": "gmail.com",
}


def normalize_email(email: str) -> str:
    """Normalize email for duplicate detection.

    Args:
        email: Raw email address.

    Returns:
        Normalized email string.

    Examples:
        >>> normalize_email("  J.O.H.N@Gmail.Com  ")
        'john@gmail.com'
        >>> normalize_email("john+test@gmail.com")
        'john@gmail.com'
        >>> normalize_email("john@googlemail.com")
        'john@gmail.com'
        >>> normalize_email("  User@Company.Com.Br  ")
        'user@company.com.br'
    """
    if not email or "@" not in email:
        return email.strip().lower() if email else ""

    email = email.strip().lower()
    local, domain = email.rsplit("@", 1)

    # Canonicalize domain
    domain = _DOMAIN_CANONICAL.get(domain, domain)

    # Strip +alias
    if domain in _PLUS_ALIAS_DOMAINS and "+" in local:
        local = local.split("+", 1)[0]

    # Remove dots from local part (Gmail treats them as identical)
    if domain in _DOT_IGNORE_DOMAINS:
        local = local.replace(".", "")

    return f"{local}@{domain}"
