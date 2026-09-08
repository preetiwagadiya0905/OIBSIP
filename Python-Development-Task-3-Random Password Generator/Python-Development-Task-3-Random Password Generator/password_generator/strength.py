"""Password strength calculation and evaluation logic.

Evaluates password strength deterministically based on length, character set diversity,
number of character categories present, and estimated entropy.
Returns human-readable strength ratings ('Weak', 'Medium', 'Strong'), visual color codes,
and progress percentages for UI meters.
"""

import math
import string
from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class PasswordStrength:
    """Represents the strength evaluation of a password."""
    score: int               # 0 to 100 scale
    label: str               # 'Weak', 'Medium', 'Strong'
    color: str               # Hex color code for UI (Red, Orange, Green)
    progress_value: float    # 0.0 to 1.0 for progress bar
    entropy_bits: float      # Shannon entropy estimate in bits
    feedback: str            # Short explanation of the score


def count_character_categories(password: str) -> int:
    """Count how many character categories (upper, lower, digit, symbol) are in the password."""
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_symbol = any(c not in (string.ascii_letters + string.digits) for c in password)

    return sum([has_upper, has_lower, has_digit, has_symbol])


def calculate_entropy(password: str) -> float:
    """Calculate approximate entropy in bits based on character set pool size and length."""
    if not password:
        return 0.0

    pool_size = 0
    if any(c in string.ascii_lowercase for c in password):
        pool_size += 26
    if any(c in string.ascii_uppercase for c in password):
        pool_size += 26
    if any(c in string.digits for c in password):
        pool_size += 10
    if any(c not in (string.ascii_letters + string.digits) for c in password):
        pool_size += 32

    if pool_size == 0:
        return 0.0

    return len(password) * math.log2(pool_size)


def calculate_strength(password: str) -> PasswordStrength:
    """Deterministically calculate the strength of a given password.

    Classification logic:
    - Weak: Length < 10 or low category diversity (< 3 categories with length < 12).
    - Medium: Length 10-13 with at least 2-3 categories, or longer with 2 categories.
    - Strong: Length >= 14 with 3+ categories, or length >= 12 with all 4 categories.

    Returns:
        PasswordStrength object with label, score, color, progress value, entropy, and feedback.
    """
    if not password:
        return PasswordStrength(
            score=0,
            label="Weak",
            color="#E74C3C",  # Red
            progress_value=0.0,
            entropy_bits=0.0,
            feedback="Empty password",
        )

    length = len(password)
    categories = count_character_categories(password)
    entropy = calculate_entropy(password)

    # Base points from length
    if length < 8:
        length_score = 15
    elif length < 10:
        length_score = 30
    elif length < 12:
        length_score = 45
    elif length < 16:
        length_score = 65
    elif length < 20:
        length_score = 75
    else:
        length_score = 85

    # Diversity points from categories (0 - 20)
    category_bonus = {
        1: 0,
        2: 8,
        3: 14,
        4: 20,
    }.get(categories, 0)

    # Unique character ratio bonus (0 - 10)
    unique_ratio = len(set(password)) / length
    variety_bonus = int(unique_ratio * 10)

    total_score = min(100, length_score + category_bonus + variety_bonus)

    # Deterministic categorization:
    # Strong criteria: length >= 14 with >= 3 categories, OR length >= 12 with all 4 categories (entropy >= 70)
    # Weak criteria: length < 10 OR (length < 12 and categories <= 2) OR total_score < 50
    # Medium criteria: everything in between
    if length >= 14 and categories >= 3:
        label = "Strong"
        color = "#27AE60"  # Vibrant Green
        progress = 1.0
        feedback = "Excellent length and high character variety"
    elif length >= 12 and categories == 4:
        label = "Strong"
        color = "#27AE60"  # Vibrant Green
        progress = 1.0
        feedback = "Great length with all character types included"
    elif length < 10 or (length < 12 and categories <= 2) or total_score < 48:
        label = "Weak"
        color = "#E74C3C"  # Red
        progress = 0.33
        if length < 10:
            feedback = "Short length; increase length for better security"
        else:
            feedback = "Low character diversity; add more character types"
    else:
        label = "Medium"
        color = "#E67E22"  # Warm Orange / Amber
        progress = 0.66
        feedback = "Good password; increase length or add symbols for maximum strength"

    return PasswordStrength(
        score=total_score,
        label=label,
        color=color,
        progress_value=progress,
        entropy_bits=round(entropy, 1),
        feedback=feedback,
    )
