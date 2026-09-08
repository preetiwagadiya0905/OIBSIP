"""
Integration Tests for GUI and Application Controller
"""

import os
import tempfile
import tkinter as tk
from unittest.mock import patch
import pytest

from database import DatabaseManager
from gui import BMICalculatorApp


@pytest.fixture
def app_instance():
    """Create a headless Tk instance and BMICalculatorApp for testing."""
    root = tk.Tk()
    root.withdraw()  # Keep hidden during automated test runs

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path)

    app = BMICalculatorApp(root=root, db_manager=db)
    yield app, root, db, db_path

    try:
        root.destroy()
    except Exception:
        pass
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


class TestBMICalculatorApp:
    """Test GUI interactions and event handlers programmatically."""

    def test_gui_initial_state(self, app_instance):
        app, root, db, db_path = app_instance
        assert app.user_name_var.get() == ""
        assert app.weight_var.get() == ""
        assert app.height_var.get() == ""
        assert str(app.btn_save["state"]) == "disabled"

    def test_calculation_flow(self, app_instance):
        app, root, db, db_path = app_instance
        app.user_name_var.set("John Doe")
        app.weight_var.set("70")
        app.height_var.set("1.75")

        app.on_calculate()

        assert app.current_bmi == 22.86
        assert app.current_category == "Normal"
        assert str(app.btn_save["state"]) == "normal"
        assert "BMI: 22.86" in app.result_bmi_label.cget("text")
        assert "Category: Normal" in app.result_cat_badge.cget("text")

    def test_calculation_validation_error(self, app_instance):
        app, root, db, db_path = app_instance
        app.user_name_var.set("John Doe")
        app.weight_var.set("invalid")
        app.height_var.set("1.75")

        with patch("tkinter.messagebox.showerror") as mock_err:
            app.on_calculate()
            assert mock_err.called
            assert app.current_bmi is None

    def test_save_and_history_flow(self, app_instance):
        app, root, db, db_path = app_instance
        app.user_name_var.set("Sarah")
        app.weight_var.set("60")
        app.height_var.set("1.65")

        app.on_calculate()

        with patch("tkinter.messagebox.showinfo") as mock_info:
            app.on_save_record()
            assert mock_info.called

        records = db.get_records_by_user("Sarah")
        assert len(records) == 1
        assert records[0]["bmi"] == 22.04
        assert records[0]["category"] == "Normal"

        # Check history view table population
        app.history_user_var.set("Sarah")
        app.refresh_history_table()
        items = app.tree.get_children()
        assert len(items) == 1

    def test_delete_record_from_gui(self, app_instance):
        app, root, db, db_path = app_instance
        rec_id = db.add_record("Sarah", 60, 1.65, 22.04, "Normal")
        app.history_user_var.set("Sarah")
        app.refresh_history_table()

        # Select the item
        app.tree.selection_set(str(rec_id))

        with patch("tkinter.messagebox.askyesno", return_value=True):
            app.on_delete_selected_record()

        assert len(db.get_records_by_user("Sarah")) == 0

    def test_trend_chart_rendering_single_and_multiple(self, app_instance):
        app, root, db, db_path = app_instance
        
        # Test empty trend
        app.trend_user_var.set("NonExistent")
        app.plot_user_trend()
        assert "No records found" in app.status_var.get()

        # Add 1 record
        db.add_record("Alice", 55.0, 1.60, 21.48, "Normal", "2026-08-21 10:00:00")
        app.trend_user_var.set("Alice")
        app.plot_user_trend()
        assert "Rendered BMI trend for 'Alice' (1 measurement(s))" in app.status_var.get()

        # Add second record
        db.add_record("Alice", 57.0, 1.60, 22.27, "Normal", "2026-08-22 10:00:00")
        app.plot_user_trend()
        assert "Rendered BMI trend for 'Alice' (2 measurement(s))" in app.status_var.get()

    def test_clear_inputs_flow(self, app_instance):
        app, root, db, db_path = app_instance
        app.user_name_var.set("John")
        app.weight_var.set("80")
        app.height_var.set("1.80")
        app.on_calculate()

        assert app.current_bmi is not None
        app.on_clear_inputs()

        assert app.weight_var.get() == ""
        assert app.height_var.get() == ""
        assert app.current_bmi is None
        assert str(app.btn_save["state"]) == "disabled"
