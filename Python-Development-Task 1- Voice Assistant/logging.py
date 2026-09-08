"""Structured, secure logging system with automatic secret redaction."""

import logging
import sys

from voice_assistant.security.secrets import redact_secrets


class SecretMaskingFilter(logging.Filter):
    """Logging filter that automatically redacts secrets and credentials from records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_secrets(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_secrets(str(arg)) for arg in record.args)
        return True


class StructuredFormatter(logging.Formatter):
    """Structured, readable log formatter with timestamp, level, and component."""

    def __init__(self, fmt: str | None = None):
        default_fmt = "%(asctime)s | %(levelname)-7s | %(name)-24s | %(message)s"
        super().__init__(fmt=fmt or default_fmt, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Initialize application root logging with secret masking and structured format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger("voice_assistant")
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-initialization
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        handler.setFormatter(StructuredFormatter())
        handler.addFilter(SecretMaskingFilter())
        root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Obtain a logger scoped to a specific component."""
    if not name.startswith("voice_assistant"):
        name = f"voice_assistant.{name}"
    logger = logging.getLogger(name)
    # Ensure filter is attached to logger as well
    if not any(isinstance(f, SecretMaskingFilter) for f in logger.filters):
        logger.addFilter(SecretMaskingFilter())
    return logger
