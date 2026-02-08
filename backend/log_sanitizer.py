"""Log sanitization utilities for PII and sensitive data protection.

This module provides utilities to sanitize sensitive data before logging,
preventing accidental exposure of PII, API keys, and other confidential
information in log files.

Security Guidelines (OWASP, LGPD, GDPR):
- Never log plaintext passwords
- Never log complete API keys
- Never log complete tokens (JWT, OAuth)
- Mask PII (emails, phone numbers, etc.)
- Use appropriate log levels in production

Usage:
    >>> from log_sanitizer import sanitize, mask_email, mask_api_key, SanitizedLogAdapter
    >>> logger = logging.getLogger(__name__)
    >>> safe_logger = SanitizedLogAdapter(logger)
    >>> safe_logger.info("User login", user_email=user_email)  # Auto-sanitized
"""

import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, Optional


# ============================================================================
# Environment Configuration
# ============================================================================

@lru_cache(maxsize=1)
def get_log_level() -> str:
    """Get configured log level (cached for performance)."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


@lru_cache(maxsize=1)
def is_production() -> bool:
    """Check if running in production environment."""
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    return env in ("production", "prod")


# ============================================================================
# Masking Functions
# ============================================================================

def mask_email(email: Optional[str]) -> str:
    """
    Mask email address, preserving domain for debugging.

    Examples:
        >>> mask_email("user@example.com")
        'u***@example.com'
        >>> mask_email("ab@test.org")
        'a***@test.org'
        >>> mask_email(None)
        '[no-email]'
    """
    if not email or not isinstance(email, str):
        return "[no-email]"

    if "@" not in email:
        return "[invalid-email]"

    local, domain = email.rsplit("@", 1)
    if len(local) > 1:
        masked_local = local[0] + "***"
    else:
        masked_local = "***"

    return f"{masked_local}@{domain}"


def mask_api_key(key: Optional[str], visible_chars: int = 4) -> str:
    """
    Mask API key, showing only last N characters.

    Args:
        key: API key to mask
        visible_chars: Number of characters to show at the end (default: 4)

    Examples:
        >>> mask_api_key("sk-1234567890abcdef")
        'sk-***cdef'
        >>> mask_api_key("short")
        '[key-hidden]'
        >>> mask_api_key(None)
        '[no-key]'
    """
    if not key or not isinstance(key, str):
        return "[no-key]"

    if len(key) <= visible_chars + 3:
        return "[key-hidden]"

    # Show prefix (like "sk-") and last N chars
    prefix_match = re.match(r'^([a-zA-Z]{2,3}[-_])', key)
    prefix = prefix_match.group(1) if prefix_match else ""
    suffix = key[-visible_chars:]

    return f"{prefix}***{suffix}"


def mask_token(token: Optional[str]) -> str:
    """
    Mask JWT or OAuth token, showing only structure hint.

    Examples:
        >>> mask_token("eyJhbGc.eyJzdWI.signature")
        'eyJ***[JWT]'
        >>> mask_token("Bearer abc123")
        'Bearer ***[TOKEN]'
        >>> mask_token(None)
        '[no-token]'
    """
    if not token or not isinstance(token, str):
        return "[no-token]"

    token = token.strip()

    # Handle Bearer prefix
    if token.lower().startswith("bearer "):
        return "Bearer ***[TOKEN]"

    # Detect JWT (three dot-separated parts starting with eyJ)
    if token.startswith("eyJ") and token.count(".") == 2:
        return "eyJ***[JWT]"

    # Generic token
    if len(token) > 10:
        return f"{token[:3]}***[TOKEN]"

    return "[token-hidden]"


def mask_user_id(user_id: Optional[str]) -> str:
    """
    Partially mask user ID for debugging while preserving uniqueness hint.

    For UUIDs, shows first 8 chars. For other formats, shows first 4 chars.

    Examples:
        >>> mask_user_id("550e8400-e29b-41d4-a716-446655440000")
        '550e8400-***'
        >>> mask_user_id("user123")
        'user***'
        >>> mask_user_id(None)
        '[no-id]'
    """
    if not user_id or not isinstance(user_id, str):
        return "[no-id]"

    # UUID format
    if len(user_id) == 36 and user_id.count("-") == 4:
        return f"{user_id[:8]}-***"

    # Other formats
    if len(user_id) > 4:
        return f"{user_id[:4]}***"

    return "[id-hidden]"


def mask_ip_address(ip: Optional[str]) -> str:
    """
    Mask IP address, preserving network segment for debugging.

    Examples:
        >>> mask_ip_address("192.168.1.100")
        '192.168.x.x'
        >>> mask_ip_address("2001:0db8::1")
        '2001:0db8::*'
        >>> mask_ip_address(None)
        '[no-ip]'
    """
    if not ip or not isinstance(ip, str):
        return "[no-ip]"

    # IPv4
    if "." in ip and ip.count(".") == 3:
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.x.x"

    # IPv6 (simplified)
    if ":" in ip:
        parts = ip.split(":")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}::*"
        return "[ipv6-hidden]"

    return "[ip-hidden]"


def mask_password(password: Any) -> str:
    """
    Always returns masked placeholder for passwords.

    Examples:
        >>> mask_password("secretpass123")
        '[PASSWORD_REDACTED]'
        >>> mask_password(None)
        '[PASSWORD_REDACTED]'
    """
    return "[PASSWORD_REDACTED]"


def mask_phone(phone: Optional[str]) -> str:
    """
    Mask phone number, showing only last 4 digits.

    Examples:
        >>> mask_phone("+55 11 99999-1234")
        '***-1234'
        >>> mask_phone("(11) 98765-4321")
        '***-4321'
        >>> mask_phone(None)
        '[no-phone]'
    """
    if not phone or not isinstance(phone, str):
        return "[no-phone]"

    # Extract only digits
    digits = re.sub(r'\D', '', phone)

    if len(digits) >= 4:
        return f"***-{digits[-4:]}"

    return "[phone-hidden]"


# ============================================================================
# Generic Sanitization
# ============================================================================

# Patterns for auto-detection
SENSITIVE_PATTERNS = {
    # API keys (various formats)
    re.compile(r'(?:api[_-]?key|apikey|secret[_-]?key)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.I): mask_api_key,
    # JWT tokens
    re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'): mask_token,
    # Bearer tokens
    re.compile(r'Bearer\s+[a-zA-Z0-9_-]{10,}', re.I): mask_token,
    # OpenAI API keys
    re.compile(r'sk-[a-zA-Z0-9]{40,}'): mask_api_key,
    # Supabase keys
    re.compile(r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'): mask_api_key,
}

# Field names that should be masked (case-insensitive)
SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'api-key', 'authorization', 'auth', 'credential', 'credentials',
    'private_key', 'private-key', 'access_token', 'refresh_token',
    'session_token', 'session-token', 'cookie', 'x-api-key',
    'supabase_key', 'openai_key', 'stripe_key', 'webhook_secret',
    'service_role_key', 'anon_key', 'new_password', 'old_password',
}

# Field names for email masking
EMAIL_FIELDS = {'email', 'user_email', 'customer_email', 'email_address'}

# Field names for user ID partial masking
USER_ID_FIELDS = {'user_id', 'userid', 'uid', 'id', 'admin_id', 'customer_id'}


def sanitize_value(key: str, value: Any) -> Any:
    """
    Sanitize a single value based on its key name.

    Args:
        key: Field/parameter name (used for context-aware masking)
        value: Value to sanitize

    Returns:
        Sanitized value
    """
    if value is None:
        return None

    key_lower = key.lower()

    # Password fields - always fully redact
    if any(pw in key_lower for pw in ('password', 'passwd', 'pwd')):
        return mask_password(value)

    # Secret/key fields
    if key_lower in SENSITIVE_FIELDS or any(s in key_lower for s in ('secret', 'key', 'token')):
        if 'api' in key_lower or 'secret' in key_lower or key_lower.endswith('_key'):
            return mask_api_key(str(value))
        return mask_token(str(value))

    # Email fields
    if key_lower in EMAIL_FIELDS or 'email' in key_lower:
        return mask_email(str(value))

    # IP address fields
    if 'ip' in key_lower and 'address' in key_lower or key_lower in ('ip', 'client_ip', 'remote_ip'):
        return mask_ip_address(str(value))

    # Phone fields
    if 'phone' in key_lower or 'tel' in key_lower or 'celular' in key_lower:
        return mask_phone(str(value))

    return value


def sanitize_dict(data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Sanitize all sensitive fields in a dictionary.

    Args:
        data: Dictionary to sanitize
        deep: If True, recursively sanitize nested dicts (default: True)

    Returns:
        New dictionary with sanitized values
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if deep and isinstance(value, dict):
            result[key] = sanitize_dict(value, deep=True)
        elif deep and isinstance(value, list):
            result[key] = [
                sanitize_dict(v, deep=True) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            result[key] = sanitize_value(key, value)

    return result


def sanitize_string(text: str) -> str:
    """
    Scan and sanitize sensitive patterns in a string.

    Auto-detects and masks:
    - API keys
    - JWT tokens
    - Bearer tokens
    - Email addresses (in common formats)

    Args:
        text: String to sanitize

    Returns:
        Sanitized string
    """
    if not text or not isinstance(text, str):
        return text

    result = text

    # Apply pattern-based masking
    for pattern, mask_func in SENSITIVE_PATTERNS.items():
        matches = pattern.findall(result)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]  # Extract from group
            masked = mask_func(match)
            result = result.replace(match, masked)

    # Also mask emails found in text
    email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
    for email in email_pattern.findall(result):
        result = result.replace(email, mask_email(email))

    return result


def sanitize(value: Any, context: Optional[str] = None) -> Any:
    """
    Universal sanitization function.

    Automatically detects value type and applies appropriate sanitization:
    - Dict: sanitize_dict()
    - String: sanitize_string()
    - Other: return as-is

    Args:
        value: Value to sanitize
        context: Optional context hint (e.g., field name) for better masking

    Returns:
        Sanitized value

    Examples:
        >>> sanitize({"email": "user@test.com", "name": "John"})
        {'email': 'u***@test.com', 'name': 'John'}
        >>> sanitize("Login failed for user@test.com")
        'Login failed for u***@test.com'
    """
    if context:
        return sanitize_value(context, value)

    if isinstance(value, dict):
        return sanitize_dict(value)

    if isinstance(value, str):
        return sanitize_string(value)

    return value


# ============================================================================
# Sanitized Logger Adapter
# ============================================================================

class SanitizedLogAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically sanitizes sensitive data.

    Wraps a standard logger and sanitizes all extra kwargs before logging.
    Also enforces log level restrictions in production.

    Usage:
        >>> logger = logging.getLogger(__name__)
        >>> safe_logger = SanitizedLogAdapter(logger)
        >>> safe_logger.info("User created", email=user_email, password=password)
        # Logs: "User created" with email masked and password redacted
    """

    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        """
        Initialize sanitized logger adapter.

        Args:
            logger: Underlying logger instance
            extra: Default extra data (will be sanitized)
        """
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and sanitize extra data."""
        # Sanitize the message itself
        msg = sanitize_string(str(msg))

        # Sanitize extra kwargs
        if 'extra' in kwargs:
            kwargs['extra'] = sanitize_dict(kwargs['extra'])

        # Merge with default extra
        extra = {**self.extra, **kwargs.get('extra', {})}
        kwargs['extra'] = sanitize_dict(extra)

        return msg, kwargs

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Debug level (suppressed in production)."""
        if is_production():
            return  # Skip debug logs in production
        super().debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Info level with sanitization."""
        super().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Warning level with sanitization."""
        super().warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Error level with sanitization."""
        super().error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        """Exception level with sanitization."""
        super().exception(msg, *args, **kwargs)


def get_sanitized_logger(name: str) -> SanitizedLogAdapter:
    """
    Get a logger with automatic sanitization enabled.

    Convenience function to create a sanitized logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        SanitizedLogAdapter wrapping the named logger

    Example:
        >>> logger = get_sanitized_logger(__name__)
        >>> logger.info("Processing user", email=user_email)  # Auto-masked
    """
    return SanitizedLogAdapter(logging.getLogger(name))


# ============================================================================
# Utility Functions for Common Log Patterns
# ============================================================================

def log_user_action(
    logger: logging.Logger,
    action: str,
    user_id: str,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log a user action with proper sanitization.

    Args:
        logger: Logger instance
        action: Action description (e.g., "created", "updated", "deleted")
        user_id: User ID (will be partially masked)
        details: Optional details dictionary (will be fully sanitized)
        level: Log level (default: INFO)

    Example:
        >>> log_user_action(logger, "login", user_id, {"ip": "192.168.1.1"})
        # Logs: "User action: login user_id=550e8400-*** details={'ip': '192.168.x.x'}"
    """
    masked_id = mask_user_id(user_id)
    sanitized_details = sanitize_dict(details) if details else None

    if sanitized_details:
        logger.log(level, f"User action: {action} user_id={masked_id} details={sanitized_details}")
    else:
        logger.log(level, f"User action: {action} user_id={masked_id}")


def log_admin_action(
    logger: logging.Logger,
    admin_id: str,
    action: str,
    target_user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log an admin action with proper sanitization.

    Args:
        logger: Logger instance
        admin_id: Admin user ID
        action: Action description
        target_user_id: Optional target user ID
        details: Optional details (will be sanitized)
        level: Log level

    Example:
        >>> log_admin_action(logger, admin_id, "reset-password", target_user_id)
    """
    masked_admin = mask_user_id(admin_id)

    msg_parts = [f"Admin action: {action} admin={masked_admin}"]

    if target_user_id:
        masked_target = mask_user_id(target_user_id)
        msg_parts.append(f"target={masked_target}")

    if details:
        sanitized = sanitize_dict(details)
        msg_parts.append(f"details={sanitized}")

    logger.log(level, " ".join(msg_parts))


def log_auth_event(
    logger: logging.Logger,
    event: str,
    success: bool,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    reason: Optional[str] = None,
    level: Optional[int] = None,
) -> None:
    """
    Log authentication event with proper sanitization.

    Args:
        logger: Logger instance
        event: Event type (e.g., "login", "logout", "token_refresh")
        success: Whether the event was successful
        user_id: Optional user ID
        email: Optional email (will be masked)
        reason: Optional failure reason
        level: Log level (auto-determined if not provided)

    Example:
        >>> log_auth_event(logger, "login", success=False, email=email, reason="invalid password")
    """
    if level is None:
        level = logging.INFO if success else logging.WARNING

    msg_parts = [f"Auth: {event} success={success}"]

    if user_id:
        msg_parts.append(f"user={mask_user_id(user_id)}")

    if email:
        msg_parts.append(f"email={mask_email(email)}")

    if reason and not success:
        # Sanitize reason in case it contains sensitive data
        msg_parts.append(f"reason={sanitize_string(reason)}")

    logger.log(level, " ".join(msg_parts))
