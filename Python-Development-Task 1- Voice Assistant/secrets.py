"""Security utilities for secret masking and credential protection."""

import re
from typing import Any

# Regex patterns for common credentials/tokens
SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|password|token|auth|pass)\s*[:=]\s*["\']?([^"\'\s,]+)["\']?'), r'\1="***REDACTED***"'),
    (re.compile(r'(?i)(https?://[^:]+:)([^@]+)(@)'), r'\1***REDACTED***\3'),
]


def redact_secrets(text: str) -> str:
    """Redact sensitive credentials, passwords, and API keys from text."""
    if not isinstance(text, str):
        return str(text)
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow-sanitized copy of a dictionary, masking sensitive keys."""
    sensitive_keys = {"password", "secret", "api_key", "token", "auth", "smtp_password"}
    clean: dict[str, Any] = {}
    for k, v in data.items():
        if any(s in k.lower() for s in sensitive_keys):
            clean[k] = "***REDACTED***"
        elif isinstance(v, dict):
            clean[k] = sanitize_dict(v)
        else:
            clean[k] = v
    return clean
