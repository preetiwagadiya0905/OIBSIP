"""Main entry point for the Random Password Generator desktop application."""

import tkinter as tk
from password_generator.gui import PasswordGeneratorApp


def main() -> None:
    """Launch the Random Password Generator application."""
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
