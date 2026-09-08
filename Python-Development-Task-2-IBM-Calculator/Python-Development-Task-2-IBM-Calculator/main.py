"""
BMI Calculator & Health Tracker Application Entry Point

Starts the Tkinter application, initializes the SQLite database,
and manages top-level application lifecycle.
"""

import sys
import tkinter as tk
from tkinter import messagebox

from database import DatabaseManager, DatabaseError
from gui import BMICalculatorApp


def center_window(window: tk.Tk, width: int = 820, height: int = 720) -> None:
    """
    Center the application window on the user's desktop screen.
    
    Args:
        window: The root Tkinter window.
        width: Target window width in pixels.
        height: Target window height in pixels.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = max(0, int((screen_width - width) / 2))
    y = max(0, int((screen_height - height) / 2))
    
    window.geometry(f"{width}x{height}+{x}+{y}")


def main() -> None:
    """Main execution function."""
    try:
        # Initialize SQLite database
        db_manager = DatabaseManager("bmi_records.db")
    except DatabaseError as e:
        # If database fails to initialize, show graphical error and exit
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Fatal Database Error",
            f"Failed to initialize the local database 'bmi_records.db':\n{e}\n\nApplication cannot start."
        )
        sys.exit(1)

    # Initialize Tkinter GUI
    root = tk.Tk()
    center_window(root, 840, 740)

    # Instantiate Application Controller
    app = BMICalculatorApp(root=root, db_manager=db_manager)

    # Run Application Event Loop
    root.mainloop()


if __name__ == "__main__":
    main()
