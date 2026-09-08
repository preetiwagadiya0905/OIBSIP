"""Comprehensive unit and integration test suite for Random Password Generator."""

import string
import sys
import unittest
from collections import deque

from password_generator.generator import (
    PasswordGenerator,
    PasswordOptions,
    ValidationError,
    AMBIGUOUS_CHARS,
    generate_password,
)
from password_generator.strength import (
    calculate_strength,
    count_character_categories,
    calculate_entropy,
)
from password_generator.history import SessionHistory


class TestPasswordGenerator(unittest.TestCase):
    """Test suite for core password generation and cryptographic rules."""

    def test_minimum_length_enforcement(self):
        """Length below 8 must raise ValidationError."""
        for invalid_len in [0, 1, 5, 7]:
            options = PasswordOptions(
                length=invalid_len,
                include_uppercase=True,
                include_lowercase=True,
            )
            with self.assertRaises(ValidationError) as ctx:
                PasswordGenerator.generate(options)
            self.assertIn("at least 8", str(ctx.exception))

    def test_minimum_two_character_categories_enforcement(self):
        """Selecting fewer than 2 categories must raise ValidationError."""
        # 0 categories
        with self.assertRaises(ValidationError) as ctx:
            PasswordGenerator.generate(
                PasswordOptions(
                    length=12,
                    include_uppercase=False,
                    include_lowercase=False,
                    include_digits=False,
                    include_symbols=False,
                )
            )
        self.assertIn("at least 2 character types", str(ctx.exception))

        # 1 category only (uppercase only)
        with self.assertRaises(ValidationError) as ctx:
            PasswordGenerator.generate(
                PasswordOptions(
                    length=12,
                    include_uppercase=True,
                    include_lowercase=False,
                    include_digits=False,
                    include_symbols=False,
                )
            )
        self.assertIn("at least 2 character types", str(ctx.exception))

        # 1 category only (digits only)
        with self.assertRaises(ValidationError) as ctx:
            PasswordGenerator.generate(
                PasswordOptions(
                    length=12,
                    include_uppercase=False,
                    include_lowercase=False,
                    include_digits=True,
                    include_symbols=False,
                )
            )
        self.assertIn("at least 2 character types", str(ctx.exception))

    def test_category_guarantee(self):
        """Every selected category MUST have at least 1 character in the output."""
        # Test 100 generations with all 4 categories
        options_all = PasswordOptions(
            length=8,  # Minimum length to ensure tightly packed guarantees
            include_uppercase=True,
            include_lowercase=True,
            include_digits=True,
            include_symbols=True,
        )
        for _ in range(100):
            pwd = PasswordGenerator.generate(options_all)
            self.assertEqual(len(pwd), 8)
            has_upper = any(c in string.ascii_uppercase for c in pwd)
            has_lower = any(c in string.ascii_lowercase for c in pwd)
            has_digit = any(c in string.digits for c in pwd)
            has_symbol = any(c not in (string.ascii_letters + string.digits) for c in pwd)

            self.assertTrue(has_upper, f"Uppercase missing in {pwd}")
            self.assertTrue(has_lower, f"Lowercase missing in {pwd}")
            self.assertTrue(has_digit, f"Digit missing in {pwd}")
            self.assertTrue(has_symbol, f"Symbol missing in {pwd}")

        # Test with 2 categories: Lowercase + Digits
        options_2 = PasswordOptions(
            length=10,
            include_uppercase=False,
            include_lowercase=True,
            include_digits=True,
            include_symbols=False,
        )
        for _ in range(50):
            pwd = PasswordGenerator.generate(options_2)
            self.assertEqual(len(pwd), 10)
            self.assertTrue(any(c in string.ascii_lowercase for c in pwd))
            self.assertTrue(any(c in string.digits for c in pwd))
            self.assertFalse(any(c in string.ascii_uppercase for c in pwd))

    def test_ambiguous_character_exclusion(self):
        """When exclude_ambiguous is True, no ambiguous character should ever appear."""
        options = PasswordOptions(
            length=32,
            include_uppercase=True,
            include_lowercase=True,
            include_digits=True,
            include_symbols=True,
            exclude_ambiguous=True,
        )
        for _ in range(100):
            pwd = PasswordGenerator.generate(options)
            for ambig in AMBIGUOUS_CHARS:
                self.assertNotIn(
                    ambig,
                    pwd,
                    f"Ambiguous character '{ambig}' found in password: {pwd}",
                )

    def test_exact_length_generation(self):
        """Passwords must match the requested length exactly across various lengths."""
        for length in [8, 12, 16, 24, 32, 64, 128]:
            options = PasswordOptions(length=length)
            pwd = PasswordGenerator.generate(options)
            self.assertEqual(len(pwd), length)

    def test_no_random_module_used_in_generator(self):
        """Verify that 'random' module is not imported or used in generator.py."""
        import password_generator.generator as gen_module
        self.assertNotIn("random", sys.modules.get("password_generator.generator", {}).__dict__)
        self.assertTrue(hasattr(gen_module, "secrets"))


class TestPasswordStrength(unittest.TestCase):
    """Test suite for strength and entropy calculation."""

    def test_weak_passwords(self):
        """Short passwords or low diversity must be classified as Weak."""
        weak_short = "Ab1!"  # len 4
        res1 = calculate_strength(weak_short)
        self.assertEqual(res1.label, "Weak")
        self.assertEqual(res1.color, "#E74C3C")

        weak_len8 = "abcdef12"  # len 8, 2 categories
        res2 = calculate_strength(weak_len8)
        self.assertEqual(res2.label, "Weak")

    def test_medium_passwords(self):
        """Medium length with reasonable diversity."""
        med_pwd = "Abcd1234ef"  # len 10, 3 categories
        res = calculate_strength(med_pwd)
        self.assertEqual(res.label, "Medium")
        self.assertEqual(res.color, "#E67E22")

    def test_strong_passwords(self):
        """Long passwords with 3+ categories or 12+ with 4 categories."""
        strong_pwd = "K#9xP$2mQ!7vL@4w"  # len 16, 4 categories
        res = calculate_strength(strong_pwd)
        self.assertEqual(res.label, "Strong")
        self.assertEqual(res.color, "#27AE60")
        self.assertEqual(res.progress_value, 1.0)
        self.assertGreater(res.entropy_bits, 80.0)

    def test_empty_password(self):
        """Empty string handled cleanly."""
        res = calculate_strength("")
        self.assertEqual(res.label, "Weak")
        self.assertEqual(res.score, 0)


class TestSessionHistory(unittest.TestCase):
    """Test suite for bounded in-memory session history."""

    def test_history_limit_and_fifo(self):
        """History must cap at 5 entries and drop the oldest when a 6th is added."""
        history = SessionHistory(max_entries=5)
        self.assertEqual(history.count, 0)

        # Add 5 passwords
        for i in range(1, 6):
            history.add(f"password_{i}", "Strong", "#27AE60")

        self.assertEqual(history.count, 5)
        entries = history.get_entries()
        # Newest first
        self.assertEqual(entries[0].password, "password_5")
        self.assertEqual(entries[-1].password, "password_1")

        # Add a 6th password
        history.add("password_6", "Strong", "#27AE60")
        self.assertEqual(history.count, 5)

        entries_after = history.get_entries()
        self.assertEqual(entries_after[0].password, "password_6")
        self.assertEqual(entries_after[1].password, "password_5")
        self.assertEqual(entries_after[-1].password, "password_2")
        # password_1 must have been dropped
        passwords = [e.password for e in entries_after]
        self.assertNotIn("password_1", passwords)

    def test_history_clear(self):
        """History can be cleared."""
        history = SessionHistory(max_entries=5)
        history.add("pwd1", "Weak", "#E74C3C")
        self.assertEqual(history.count, 1)
        history.clear()
        self.assertEqual(history.count, 0)


if __name__ == "__main__":
    unittest.main()
