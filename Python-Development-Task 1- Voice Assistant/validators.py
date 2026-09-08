"""Input, URL, and action validators enforcing security constraints."""

import re
from urllib.parse import urlparse

from voice_assistant.config.constants import CustomActionType
from voice_assistant.errors.exceptions import SecurityValidationError

# Strict email regex matching valid standard email addresses
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

ALLOWED_URL_SCHEMES = {"http", "https"}


def validate_email_address(email: str) -> str:
    """Validate email address format. Returns cleaned email if valid.

    Raises:
        SecurityValidationError: If the email address is invalid.
    """
    if not email or not isinstance(email, str):
        raise SecurityValidationError("Email address cannot be empty.")

    cleaned = email.strip()
    if not EMAIL_REGEX.match(cleaned):
        raise SecurityValidationError(f"Invalid email address format: '{cleaned}'.")
    return cleaned


def validate_url(url: str) -> str:
    """Validate URL format and ensure only safe protocols (http, https) are permitted.

    Disallows javascript:, file:, data:, or raw local paths.

    Raises:
        SecurityValidationError: If URL protocol or structure is unsafe.
    """
    if not url or not isinstance(url, str):
        raise SecurityValidationError("URL cannot be empty.")

    cleaned = url.strip()
    parsed = urlparse(cleaned)

    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        raise SecurityValidationError(
            f"Unsafe URL scheme '{parsed.scheme}'. Only HTTP and HTTPS protocols are permitted."
        )

    if not parsed.netloc:
        raise SecurityValidationError(f"Invalid URL missing domain host: '{cleaned}'.")

    return cleaned


def validate_custom_action(action: str, target: str) -> None:
    """Validate user-defined custom command action type and target.

    Disallows dangerous actions like shell execution or arbitrary code.

    Raises:
        SecurityValidationError: If action is not allowlisted or target is unsafe.
    """
    valid_actions = {a.value for a in CustomActionType}
    if action not in valid_actions:
        raise SecurityValidationError(
            f"Action '{action}' is not permitted. Allowed actions: {sorted(valid_actions)}."
        )

    if action == CustomActionType.OPEN_URL.value:
        validate_url(target)
    elif action == CustomActionType.SPEAK.value:
        if not target or not target.strip():
            raise SecurityValidationError("Speak action target response text cannot be empty.")
        if len(target) > 1000:
            raise SecurityValidationError("Speak action target exceeds maximum length of 1000 characters.")


def sanitize_speech_input(text: str) -> str:
    """Strip dangerous control characters from speech transcriptions while preserving Unicode."""
    if not text:
        return ""
    # Remove non-printable control characters except standard whitespace
    return "".join(ch for ch in text if ch == " " or ch == "\n" or ch.isprintable()).strip()
