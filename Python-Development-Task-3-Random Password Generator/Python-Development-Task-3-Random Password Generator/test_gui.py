"""Headless / automated integration tests for Tkinter GUI interactions."""

import tkinter as tk
import unittest
from unittest.mock import patch

from password_generator.gui import PasswordGeneratorApp


class TestGUIIntegration(unittest.TestCase):
    """Test GUI logic, state updates, validation handling, and interactions."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during automated test
        self.app = PasswordGeneratorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_gui_initial_state(self):
        """Verify initial generated password and default options."""
        self.assertEqual(self.app.length_var.get(), 16)
        self.assertTrue(self.app.upper_var.get())
        self.assertTrue(self.app.lower_var.get())
        self.assertTrue(self.app.digits_var.get())
        self.assertTrue(self.app.symbols_var.get())
        self.assertFalse(self.app.exclude_ambiguous_var.get())
        self.assertEqual(len(self.app.password_var.get()), 16)
        self.assertEqual(self.app.history.count, 1)

    def test_gui_validation_length_below_8(self):
        """Setting length < 8 should display error status and not update history."""
        initial_history_count = self.app.history.count
        self.app.length_var.set(6)
        self.app.on_generate_clicked()

        self.assertIn("at least 8", self.app.status_var.get())
        self.assertEqual(self.app.status_type, "error")
        # History should not have increased
        self.assertEqual(self.app.history.count, initial_history_count)

    def test_gui_validation_less_than_two_categories(self):
        """Selecting only 1 category should display validation error."""
        self.app.upper_var.set(True)
        self.app.lower_var.set(False)
        self.app.digits_var.set(False)
        self.app.symbols_var.set(False)

        initial_history_count = self.app.history.count
        self.app.on_generate_clicked()

        self.assertIn("at least 2 character types", self.app.status_var.get())
        self.assertEqual(self.app.status_type, "error")
        self.assertEqual(self.app.history.count, initial_history_count)

    def test_gui_multiple_generations_and_history(self):
        """Generating multiple passwords should properly update display and keep last 5 in history."""
        self.app.length_var.set(20)
        self.app.upper_var.set(True)
        self.app.lower_var.set(True)
        self.app.digits_var.set(True)
        self.app.symbols_var.set(True)

        for _ in range(6):
            self.app.on_generate_clicked()

        self.assertEqual(len(self.app.password_var.get()), 20)
        self.assertEqual(self.app.history.count, 5)
        self.assertIn("copied to clipboard", self.app.status_var.get())

    def test_copy_button(self):
        """Test manual copy action."""
        self.app.on_copy_clicked()
        self.assertIn("copied to clipboard", self.app.status_var.get())


if __name__ == "__main__":
    unittest.main()
