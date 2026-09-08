"""Modern Tkinter desktop GUI for the Random Password Generator.

Features:
- Responsive, clean layout using tkinter and ttk widgets.
- Synchronized Slider and Spinbox for password length selection (min 8).
- Checkboxes for Uppercase, Lowercase, Numbers, Symbols, and Ambiguous Character exclusion.
- Monospace password display with prominent Generate and Copy buttons.
- Real-time / generation-triggered visual password strength meter (Weak/Medium/Strong).
- Automatic clipboard copy on generation with friendly status feedback.
- In-memory session history showing the last 5 passwords with one-click copy buttons.
- Graceful error handling with in-GUI validation alerts.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

from password_generator.generator import (
    PasswordGenerator,
    PasswordOptions,
    ValidationError,
)
from password_generator.strength import calculate_strength, PasswordStrength
from password_generator.history import SessionHistory, HistoryEntry


class PasswordGeneratorApp:
    """Main Application GUI class."""

    # UI Color Palette
    COLOR_BG = "#F8F9FA"
    COLOR_CARD_BG = "#FFFFFF"
    COLOR_PRIMARY = "#2B5CE7"
    COLOR_PRIMARY_HOVER = "#1E44B5"
    COLOR_SECONDARY = "#4A5568"
    COLOR_TEXT = "#1A202C"
    COLOR_MUTED = "#718096"
    COLOR_BORDER = "#E2E8F0"
    COLOR_SUCCESS_BG = "#DEF7EC"
    COLOR_SUCCESS_TEXT = "#03543F"
    COLOR_ERROR_BG = "#FDE8E8"
    COLOR_ERROR_TEXT = "#9B1C1C"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Random Password Generator")
        self.root.geometry("620x760")
        self.root.minsize(560, 680)
        self.root.configure(bg=self.COLOR_BG)

        # High-DPI awareness on Windows
        if sys.platform.startswith("win"):
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        # State Variables
        self.history = SessionHistory(max_entries=5)
        self.length_var = tk.IntVar(value=16)
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.status_type = "info"  # 'info', 'success', 'error'

        self._configure_styles()
        self._build_ui()

        # Keyboard shortcuts
        self.root.bind("<Return>", lambda event: self.on_generate_clicked())
        self.root.bind("<Control-c>", lambda event: self.on_copy_clicked())
        self.root.bind("<Control-g>", lambda event: self.on_generate_clicked())

        # Generate an initial password on launch
        self.on_generate_clicked()

    def _configure_styles(self) -> None:
        """Configure ttk styles and fonts."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", background=self.COLOR_BG, foreground=self.COLOR_TEXT)
        self.style.configure(
            "Card.TFrame",
            background=self.COLOR_CARD_BG,
            relief="solid",
            borderwidth=1,
        )
        self.style.configure(
            "TCheckbutton",
            background=self.COLOR_CARD_BG,
            foreground=self.COLOR_TEXT,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "TLabel",
            background=self.COLOR_CARD_BG,
            foreground=self.COLOR_TEXT,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Muted.TLabel",
            background=self.COLOR_CARD_BG,
            foreground=self.COLOR_MUTED,
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Header.TLabel",
            background=self.COLOR_BG,
            foreground=self.COLOR_TEXT,
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "SubHeader.TLabel",
            background=self.COLOR_BG,
            foreground=self.COLOR_MUTED,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "SectionTitle.TLabel",
            background=self.COLOR_CARD_BG,
            foreground=self.COLOR_TEXT,
            font=("Segoe UI", 11, "bold"),
        )

    def _build_ui(self) -> None:
        """Build the main interface components."""
        main_container = tk.Frame(self.root, bg=self.COLOR_BG, padx=20, pady=16)
        main_container.pack(fill="both", expand=True)

        # 1. Header
        header_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        header_frame.pack(fill="x", pady=(0, 12))

        title_lbl = ttk.Label(
            header_frame,
            text="🔐 Random Password Generator",
            style="Header.TLabel",
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ttk.Label(
            header_frame,
            text="Generate cryptographically secure, randomized passwords with custom rules.",
            style="SubHeader.TLabel",
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Generated Password Display Card
        self._build_password_display_card(main_container)

        # 3. Status & Notification Banner
        self.status_banner = tk.Label(
            main_container,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            anchor="center",
        )
        # Initially hidden until a status message is set

        # 4. Configuration Controls Card
        self._build_controls_card(main_container)

        # 5. Session History Card
        self._build_history_card(main_container)

    def _build_password_display_card(self, parent: tk.Widget) -> None:
        """Build the generated password display box and action buttons."""
        card = tk.Frame(
            parent,
            bg=self.COLOR_CARD_BG,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        card.pack(fill="x", pady=(0, 10))

        # Password Entry Row
        entry_row = tk.Frame(card, bg=self.COLOR_CARD_BG)
        entry_row.pack(fill="x", pady=(0, 8))

        self.password_entry = tk.Entry(
            entry_row,
            textvariable=self.password_var,
            font=("Consolas", 15, "bold"),
            bg="#F1F5F9",
            fg="#0F172A",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor=self.COLOR_PRIMARY,
            justify="center",
        )
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        # Strength Meter Row
        strength_row = tk.Frame(card, bg=self.COLOR_CARD_BG)
        strength_row.pack(fill="x", pady=(4, 10))

        ttk.Label(strength_row, text="Strength:", font=("Segoe UI", 9, "bold")).pack(side="left")

        # Custom canvas progress bar for vivid colored fill
        self.strength_canvas = tk.Canvas(
            strength_row,
            height=8,
            width=180,
            bg="#E2E8F0",
            highlightthickness=0,
        )
        self.strength_canvas.pack(side="left", padx=10)

        self.strength_label = tk.Label(
            strength_row,
            text="Strong",
            font=("Segoe UI", 9, "bold"),
            fg="#27AE60",
            bg=self.COLOR_CARD_BG,
        )
        self.strength_label.pack(side="left", padx=4)

        self.entropy_label = tk.Label(
            strength_row,
            text="",
            font=("Segoe UI", 8),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD_BG,
        )
        self.entropy_label.pack(side="right")

        # Action Buttons Row
        btn_row = tk.Frame(card, bg=self.COLOR_CARD_BG)
        btn_row.pack(fill="x", pady=(2, 0))

        self.btn_generate = tk.Button(
            btn_row,
            text="⚡ Generate Password",
            command=self.on_generate_clicked,
            bg=self.COLOR_PRIMARY,
            fg="white",
            activebackground=self.COLOR_PRIMARY_HOVER,
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
        )
        self.btn_generate.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_copy = tk.Button(
            btn_row,
            text="📋 Copy to Clipboard",
            command=self.on_copy_clicked,
            bg="#EDF2F7",
            fg=self.COLOR_TEXT,
            activebackground="#E2E8F0",
            activeforeground=self.COLOR_TEXT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
        )
        self.btn_copy.pack(side="right", padx=(6, 0))

    def _build_controls_card(self, parent: tk.Widget) -> None:
        """Build the configuration options for length and character sets."""
        card = tk.Frame(
            parent,
            bg=self.COLOR_CARD_BG,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        card.pack(fill="x", pady=(0, 10))

        # Section Title
        ttk.Label(card, text="Password Settings", style="SectionTitle.TLabel").pack(
            anchor="w", pady=(0, 10)
        )

        # 1. Length Row (Slider + Spinbox + Value Label)
        length_frame = tk.Frame(card, bg=self.COLOR_CARD_BG)
        length_frame.pack(fill="x", pady=(0, 12))

        lbl_length_title = ttk.Label(
            length_frame, text="Password Length:", font=("Segoe UI", 10, "bold")
        )
        lbl_length_title.pack(side="left")

        self.lbl_length_val = ttk.Label(
            length_frame,
            text=f"{self.length_var.get()} characters",
            font=("Segoe UI", 10),
            foreground=self.COLOR_PRIMARY,
        )
        self.lbl_length_val.pack(side="left", padx=8)

        # Spinbox
        self.spin_length = tk.Spinbox(
            length_frame,
            from_=8,
            to=128,
            textvariable=self.length_var,
            width=5,
            font=("Segoe UI", 10),
            command=self._on_spinbox_changed,
            relief="solid",
            bd=1,
        )
        self.spin_length.pack(side="right")
        self.spin_length.bind("<KeyRelease>", lambda e: self._on_spinbox_changed())

        # Slider
        self.slider_length = ttk.Scale(
            card,
            from_=8,
            to=64,
            orient="horizontal",
            variable=self.length_var,
            command=self._on_slider_changed,
        )
        self.slider_length.pack(fill="x", pady=(0, 12))

        # 2. Character Categories Checkboxes (2x2 Grid)
        types_frame = tk.Frame(card, bg=self.COLOR_CARD_BG)
        types_frame.pack(fill="x", pady=(0, 8))

        cb_upper = ttk.Checkbutton(
            types_frame,
            text="Uppercase Letters (A-Z)",
            variable=self.upper_var,
        )
        cb_upper.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=3)

        cb_lower = ttk.Checkbutton(
            types_frame,
            text="Lowercase Letters (a-z)",
            variable=self.lower_var,
        )
        cb_lower.grid(row=0, column=1, sticky="w", pady=3)

        cb_digits = ttk.Checkbutton(
            types_frame,
            text="Numbers (0-9)",
            variable=self.digits_var,
        )
        cb_digits.grid(row=1, column=0, sticky="w", padx=(0, 20), pady=3)

        cb_symbols = ttk.Checkbutton(
            types_frame,
            text="Symbols (!@#$%^&*...)",
            variable=self.symbols_var,
        )
        cb_symbols.grid(row=1, column=1, sticky="w", pady=3)

        types_frame.columnconfigure(0, weight=1)
        types_frame.columnconfigure(1, weight=1)

        # 3. Ambiguous Characters Option
        ambig_frame = tk.Frame(card, bg=self.COLOR_CARD_BG)
        ambig_frame.pack(fill="x", pady=(6, 0))

        cb_ambig = ttk.Checkbutton(
            ambig_frame,
            text="Exclude ambiguous characters (0, O, o, 1, l, I, |)",
            variable=self.exclude_ambiguous_var,
        )
        cb_ambig.pack(anchor="w")

    def _build_history_card(self, parent: tk.Widget) -> None:
        """Build the in-memory session history list with copy shortcuts."""
        self.history_card = tk.Frame(
            parent,
            bg=self.COLOR_CARD_BG,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        self.history_card.pack(fill="both", expand=True)

        header_row = tk.Frame(self.history_card, bg=self.COLOR_CARD_BG)
        header_row.pack(fill="x", pady=(0, 8))

        ttk.Label(header_row, text="Generation History", style="SectionTitle.TLabel").pack(
            side="left"
        )
        ttk.Label(
            header_row,
            text="(Last 5 - In Memory Only)",
            style="Muted.TLabel",
        ).pack(side="left", padx=6)

        # Scrollable / Container frame for history entries
        self.history_items_frame = tk.Frame(self.history_card, bg=self.COLOR_CARD_BG)
        self.history_items_frame.pack(fill="both", expand=True)

        self._render_history_entries()

    def _render_history_entries(self) -> None:
        """Render the latest 5 generated passwords with copy buttons."""
        for widget in self.history_items_frame.winfo_children():
            widget.destroy()

        entries = self.history.get_entries()

        if not entries:
            empty_lbl = ttk.Label(
                self.history_items_frame,
                text="No passwords generated yet in this session.",
                style="Muted.TLabel",
            )
            empty_lbl.pack(anchor="center", pady=12)
            return

        for idx, entry in enumerate(entries):
            row = tk.Frame(
                self.history_items_frame,
                bg="#F8FAFC" if idx % 2 == 0 else self.COLOR_CARD_BG,
                padx=8,
                pady=4,
                highlightthickness=1,
                highlightbackground="#EDF2F7",
            )
            row.pack(fill="x", pady=2)

            # Time tag
            time_lbl = tk.Label(
                row,
                text=entry.timestamp,
                font=("Segoe UI", 8),
                fg=self.COLOR_MUTED,
                bg=row["bg"],
                width=8,
                anchor="w",
            )
            time_lbl.pack(side="left")

            # Strength Pill
            pill = tk.Label(
                row,
                text=entry.strength_label,
                font=("Segoe UI", 8, "bold"),
                fg=entry.strength_color,
                bg=row["bg"],
                width=7,
                anchor="center",
            )
            pill.pack(side="left", padx=4)

            # Masked/Truncated or full Password display
            pwd_lbl = tk.Label(
                row,
                text=entry.password,
                font=("Consolas", 10),
                fg=self.COLOR_TEXT,
                bg=row["bg"],
                anchor="w",
            )
            pwd_lbl.pack(side="left", fill="x", expand=True, padx=8)

            # Copy Button for this specific item
            copy_btn = tk.Button(
                row,
                text="Copy",
                command=lambda pwd=entry.password: self._copy_specific_password(pwd),
                font=("Segoe UI", 8),
                bg="#E2E8F0",
                fg=self.COLOR_TEXT,
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=1,
            )
            copy_btn.pack(side="right")

    def _on_slider_changed(self, val: str) -> None:
        """Handle slider value updates."""
        try:
            int_val = int(float(val))
            self.length_var.set(int_val)
            self.lbl_length_val.config(text=f"{int_val} characters")
        except ValueError:
            pass

    def _on_spinbox_changed(self) -> None:
        """Handle spinbox value changes."""
        try:
            val = self.length_var.get()
            self.lbl_length_val.config(text=f"{val} characters")
        except (ValueError, tk.TclError):
            pass

    def show_status(self, message: str, status_type: str = "info") -> None:
        """Display a status banner in the GUI."""
        self.status_var.set(message)
        self.status_type = status_type

        if status_type == "success":
            self.status_banner.config(
                bg=self.COLOR_SUCCESS_BG,
                fg=self.COLOR_SUCCESS_TEXT,
            )
        elif status_type == "error":
            self.status_banner.config(
                bg=self.COLOR_ERROR_BG,
                fg=self.COLOR_ERROR_TEXT,
            )
        else:
            self.status_banner.config(
                bg="#EBF8FF",
                fg="#2B6CB0",
            )

        self.status_banner.pack(fill="x", pady=(0, 10), before=self.history_card)

    def hide_status(self) -> None:
        """Hide status banner."""
        self.status_banner.pack_forget()

    def update_strength_display(self, strength: PasswordStrength) -> None:
        """Update the visual strength meter with current rating and color."""
        self.strength_label.config(
            text=strength.label,
            fg=strength.color,
        )

        # Redraw custom meter
        self.strength_canvas.delete("all")
        width = 180
        fill_width = int(width * strength.progress_value)

        # Draw filled portion
        self.strength_canvas.create_rectangle(
            0, 0, fill_width, 8, fill=strength.color, width=0
        )

        self.entropy_label.config(
            text=f"Entropy: ~{strength.entropy_bits} bits ({strength.feedback})"
        )

    def on_generate_clicked(self) -> None:
        """Handle password generation trigger."""
        try:
            length = int(self.length_var.get())
        except (ValueError, tk.TclError):
            self.show_status("Invalid password length. Please enter a valid number.", "error")
            return

        options = PasswordOptions(
            length=length,
            include_uppercase=self.upper_var.get(),
            include_lowercase=self.lower_var.get(),
            include_digits=self.digits_var.get(),
            include_symbols=self.symbols_var.get(),
            exclude_ambiguous=self.exclude_ambiguous_var.get(),
        )

        try:
            PasswordGenerator.validate_options(options)
        except ValidationError as ex:
            self.show_status(str(ex), "error")
            return

        # Generate cryptographically secure password
        password = PasswordGenerator.generate(options)
        self.password_var.set(password)

        # Update strength
        strength = calculate_strength(password)
        self.update_strength_display(strength)

        # Add to in-memory session history
        self.history.add(
            password=password,
            strength_label=strength.label,
            strength_color=strength.color,
        )
        self._render_history_entries()

        # Automatically copy to clipboard
        copied = self._copy_to_clipboard(password)
        if copied:
            self.show_status("✓ Password generated and copied to clipboard!", "success")
        else:
            self.show_status("✓ Password generated! (Clipboard unavailable)", "info")

    def _copy_to_clipboard(self, text: str) -> bool:
        """Safely copy text to clipboard using pyperclip or Tkinter fallback."""
        if not text:
            return False

        # Attempt 1: pyperclip
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(text)
                return True
            except Exception:
                pass

        # Attempt 2: Tkinter clipboard fallback
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            return True
        except Exception:
            return False

    def on_copy_clicked(self) -> None:
        """Handle manual 'Copy to Clipboard' button click."""
        password = self.password_var.get()
        if not password:
            self.show_status("No password to copy.", "error")
            return

        copied = self._copy_to_clipboard(password)
        if copied:
            self.show_status("✓ Password copied to clipboard.", "success")
        else:
            self.show_status("Failed to copy to clipboard.", "error")

    def _copy_specific_password(self, password: str) -> None:
        """Copy a password from the history list."""
        copied = self._copy_to_clipboard(password)
        if copied:
            self.show_status(f"✓ Copied: {password[:4]}•••• to clipboard.", "success")
        else:
            self.show_status("Failed to copy to clipboard.", "error")
