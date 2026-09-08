"""Cryptographically secure password generation logic using the Python secrets module.

This module provides functions and classes to generate strong, randomized passwords
based on configurable character types, length constraints, and ambiguity filters.
All randomness uses cryptographically secure primitives from Python's built-in `secrets`
module. Python's `random` module is intentionally avoided for security reasons.
"""

import secrets
import string
from dataclasses import dataclass
from typing import List, Set


# Standard character sets
UPPERCASE_CHARS = string.ascii_uppercase
LOWERCASE_CHARS = string.ascii_lowercase
DIGIT_CHARS = string.digits
SYMBOL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"

# Ambiguous characters visually confusing in many fonts (e.g., 0/O, 1/l/I/|)
AMBIGUOUS_CHARS: Set[str] = {"0", "O", "o", "1", "l", "I", "|"}


class ValidationError(ValueError):
    """Raised when password generation configuration or input is invalid."""
    pass


@dataclass(frozen=True)
class PasswordOptions:
    """Options configuring password generation."""
    length: int = 16
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_digits: bool = True
    include_symbols: bool = True
    exclude_ambiguous: bool = False


class PasswordGenerator:
    """Core generator class responsible for generating secure passwords."""

    MIN_LENGTH: int = 8

    @staticmethod
    def _filter_ambiguous(charset: str, exclude_ambiguous: bool) -> str:
        """Filter out visually ambiguous characters if requested."""
        if not exclude_ambiguous:
            return charset
        return "".join(c for c in charset if c not in AMBIGUOUS_CHARS)

    @classmethod
    def get_character_pools(
        cls,
        include_uppercase: bool,
        include_lowercase: bool,
        include_digits: bool,
        include_symbols: bool,
        exclude_ambiguous: bool,
    ) -> List[str]:
        """Return a list of active non-empty character category pools."""
        pools: List[str] = []

        if include_uppercase:
            charset = cls._filter_ambiguous(UPPERCASE_CHARS, exclude_ambiguous)
            if charset:
                pools.append(charset)
        if include_lowercase:
            charset = cls._filter_ambiguous(LOWERCASE_CHARS, exclude_ambiguous)
            if charset:
                pools.append(charset)
        if include_digits:
            charset = cls._filter_ambiguous(DIGIT_CHARS, exclude_ambiguous)
            if charset:
                pools.append(charset)
        if include_symbols:
            charset = cls._filter_ambiguous(SYMBOL_CHARS, exclude_ambiguous)
            if charset:
                pools.append(charset)

        return pools

    @classmethod
    def validate_options(cls, options: PasswordOptions) -> None:
        """Validate password generation options.

        Raises:
            ValidationError: If options do not meet security or configuration constraints.
        """
        if options.length < cls.MIN_LENGTH:
            raise ValidationError(
                f"Password length must be at least {cls.MIN_LENGTH} characters."
            )

        active_pools = cls.get_character_pools(
            include_uppercase=options.include_uppercase,
            include_lowercase=options.include_lowercase,
            include_digits=options.include_digits,
            include_symbols=options.include_symbols,
            exclude_ambiguous=options.exclude_ambiguous,
        )

        if len(active_pools) < 2:
            raise ValidationError("Please select at least 2 character types.")

    @staticmethod
    def _secure_shuffle(items: List[str]) -> List[str]:
        """In-place cryptographically secure Fisher-Yates shuffle using secrets.randbelow().

        This avoids standard `random.shuffle()` which relies on the insecure Mersenne Twister.
        """
        for i in range(len(items) - 1, 0, -1):
            # Pick a cryptographically secure random index 0 <= j <= i
            j = secrets.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]
        return items

    @classmethod
    def generate(cls, options: PasswordOptions) -> str:
        """Generate a cryptographically secure password meeting all specified options.

        Guarantees:
        1. Password length equals requested length (minimum 8).
        2. At least one character from EVERY selected character category is present.
        3. Remaining positions are filled securely using secrets.choice from the combined pool.
        4. Final characters are securely shuffled so required categories aren't predictably placed.
        5. Visual ambiguous characters are excluded if configured.
        """
        cls.validate_options(options)

        active_pools = cls.get_character_pools(
            include_uppercase=options.include_uppercase,
            include_lowercase=options.include_lowercase,
            include_digits=options.include_digits,
            include_symbols=options.include_symbols,
            exclude_ambiguous=options.exclude_ambiguous,
        )

        # 1. Guarantee at least one character from each selected category
        password_chars: List[str] = [
            secrets.choice(pool) for pool in active_pools
        ]

        # 2. Build full combined character pool
        combined_pool = "".join(active_pools)

        # 3. Fill remaining positions
        remaining_count = options.length - len(password_chars)
        for _ in range(remaining_count):
            password_chars.append(secrets.choice(combined_pool))

        # 4. Cryptographically secure shuffle of the character list
        cls._secure_shuffle(password_chars)

        return "".join(password_chars)


def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Convenience helper to generate a password directly."""
    options = PasswordOptions(
        length=length,
        include_uppercase=include_uppercase,
        include_lowercase=include_lowercase,
        include_digits=include_digits,
        include_symbols=include_symbols,
        exclude_ambiguous=exclude_ambiguous,
    )
    return PasswordGenerator.generate(options)
