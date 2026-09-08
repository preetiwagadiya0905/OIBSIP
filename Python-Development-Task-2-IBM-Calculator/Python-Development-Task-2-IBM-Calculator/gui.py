"""
GUI Layer for BMI Calculator Application

Implements a modern, responsive tkinter interface with:
- Input validation and instant color-coded feedback
- Multi-user selection and management
- SQLite-backed historical records table with ttk.Treeview
- Embedded Matplotlib trend chart using FigureCanvasTkAgg
- Resilient error handling and dialogs
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Dict, Any, List

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from bmi_logic import (
    calculate_bmi,
    classify_bmi,
    validate_inputs,
    get_healthy_weight_range,
    CATEGORY_COLORS,
    CATEGORY_BG_COLORS
)
from database import DatabaseManager, DatabaseError


class BMICalculatorApp:
    """Main Application Controller and GUI for the BMI Calculator."""

    def __init__(self, root: tk.Tk, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the BMI Calculator GUI.
        
        Args:
            root: The root tkinter window.
            db_manager: An instance of DatabaseManager.
        """
        self.root = root
        self.root.title("BMI Calculator & Health Tracker")
        self.root.geometry("820x720")
        self.root.minsize(760, 640)

        # Database layer
        self.db = db_manager or DatabaseManager("bmi_records.db")

        # Application state
        self.current_bmi: Optional[float] = None
        self.current_category: Optional[str] = None
        self.current_weight: Optional[float] = None
        self.current_height: Optional[float] = None
        self.current_user: str = ""

        # Setup styling and UI components
        self._configure_styles()
        self._build_ui()
        self._load_users_into_comboboxes()

        # Keyboard shortcuts
        self.root.bind("<Return>", lambda event: self.on_calculate())

    def _configure_styles(self) -> None:
        """Configure ttk styles for a clean, modern desktop appearance."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass  # Fallback to default theme if clam is unavailable

        # Base style definitions
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TNotebook", background="#F5F7FA")
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[16, 8])
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#FFFFFF"), ("!selected", "#E0E5EC")],
                       foreground=[("selected", "#1565C0"), ("!selected", "#555555")])

        self.style.configure("Card.TFrame", background="#FFFFFF", relief="flat")
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#1A237E", background="#F5F7FA")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#5C6BC0", background="#F5F7FA")

        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), foreground="#FFFFFF", background="#1976D2")
        self.style.map("Primary.TButton",
                       background=[("active", "#1565C0"), ("pressed", "#0D47A1")])

        self.style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), foreground="#FFFFFF", background="#2E7D32")
        self.style.map("Success.TButton",
                       background=[("active", "#1B5E20"), ("pressed", "#0D3813")])

        self.style.configure("Secondary.TButton", font=("Segoe UI", 10), foreground="#333333", background="#E0E0E0")
        self.style.map("Secondary.TButton",
                       background=[("active", "#D5D5D5"), ("pressed", "#BDBDBD")])

        self.style.configure("Danger.TButton", font=("Segoe UI", 10), foreground="#FFFFFF", background="#C62828")
        self.style.map("Danger.TButton",
                       background=[("active", "#B71C1C"), ("pressed", "#7F0000")])

        # Treeview styling
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#ECEFF1", foreground="#263238")
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        self.style.map("Treeview", background=[("selected", "#BBDEFB")], foreground=[("selected", "#0D47A1")])

    def _build_ui(self) -> None:
        """Construct the overall application structure with a header and tabs."""
        self.root.configure(bg="#F5F7FA")

        # Top Header Banner
        header_frame = tk.Frame(self.root, bg="#F5F7FA", pady=12, padx=20)
        header_frame.pack(fill="x")

        title_label = ttk.Label(header_frame, text="BMI CALCULATOR & HEALTH TRACKER", style="Header.TLabel")
        title_label.pack(anchor="w")
        subtitle_label = ttk.Label(
            header_frame,
            text="Calculate Body Mass Index, monitor multi-user history, and visualize health trends over time.",
            style="SubHeader.TLabel"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Main Tabbed Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Tab 1: Calculator
        self.calc_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.calc_tab, text="  🧮 Calculator  ")
        self._build_calculator_tab()

        # Tab 2: History Table
        self.history_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.history_tab, text="  📜 Historical Records  ")
        self._build_history_tab()

        # Tab 3: Trend Chart
        self.trend_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.trend_tab, text="  📈 BMI Trend Chart  ")
        self._build_trend_tab()

        # Listen for tab switch to refresh data
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready. Enter user details and measurements to calculate.")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief="sunken",
            anchor="w",
            font=("Segoe UI", 9),
            bg="#ECEFF1",
            fg="#37474F",
            padx=10,
            pady=4
        )
        status_bar.pack(side="bottom", fill="x")

    # ==========================================
    # Tab 1: Calculator Implementation
    # ==========================================
    def _build_calculator_tab(self) -> None:
        """Construct the Calculator tab layout."""
        # Top Container (Inputs + Actions)
        content_frame = tk.Frame(self.calc_tab, bg="#F5F7FA")
        content_frame.pack(fill="both", expand=True)

        # Left Column: Inputs Card
        input_card = tk.LabelFrame(
            content_frame,
            text=" Measurement Inputs ",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#1A237E",
            padx=18,
            pady=16,
            relief="solid",
            bd=1
        )
        input_card.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=6)

        # 1. User Name Field
        lbl_user = tk.Label(input_card, text="User Name:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#333333")
        lbl_user.grid(row=0, column=0, sticky="w", pady=(4, 2))
        
        self.user_name_var = tk.StringVar()
        self.user_name_cb = ttk.Combobox(
            input_card,
            textvariable=self.user_name_var,
            font=("Segoe UI", 11),
            width=26
        )
        self.user_name_cb.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.user_name_cb.bind("<<ComboboxSelected>>", self._on_user_selected_in_calc)

        # 2. Weight Field
        lbl_weight = tk.Label(input_card, text="Weight (kg):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#333333")
        lbl_weight.grid(row=2, column=0, sticky="w", pady=(4, 2))
        
        self.weight_var = tk.StringVar()
        self.weight_entry = ttk.Entry(input_card, textvariable=self.weight_var, font=("Segoe UI", 11), width=26)
        self.weight_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # 3. Height Field
        lbl_height = tk.Label(input_card, text="Height (m):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#333333")
        lbl_height.grid(row=4, column=0, sticky="w", pady=(4, 2))
        
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(input_card, textvariable=self.height_var, font=("Segoe UI", 11), width=26)
        self.height_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        # Calculation Buttons
        btn_frame = tk.Frame(input_card, bg="#FFFFFF")
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 8))

        btn_calc = ttk.Button(btn_frame, text="⚡ Calculate BMI", style="Primary.TButton", command=self.on_calculate)
        btn_calc.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_clear = ttk.Button(btn_frame, text="Clear", style="Secondary.TButton", command=self.on_clear_inputs)
        btn_clear.pack(side="right", padx=(6, 0))

        # Save & Navigation Buttons
        action_btn_frame = tk.Frame(input_card, bg="#FFFFFF")
        action_btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        self.btn_save = ttk.Button(
            action_btn_frame,
            text="💾 Save Record",
            style="Success.TButton",
            command=self.on_save_record,
            state="disabled"
        )
        self.btn_save.pack(fill="x", pady=(0, 8))

        quick_nav_frame = tk.Frame(action_btn_frame, bg="#FFFFFF")
        quick_nav_frame.pack(fill="x")

        btn_to_history = ttk.Button(
            quick_nav_frame,
            text="📜 View History",
            style="Secondary.TButton",
            command=lambda: self.switch_to_tab(1)
        )
        btn_to_history.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_to_trend = ttk.Button(
            quick_nav_frame,
            text="📈 BMI Trend",
            style="Secondary.TButton",
            command=lambda: self.switch_to_tab(2)
        )
        btn_to_trend.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Right Column: Result Card & Category Reference
        right_column = tk.Frame(content_frame, bg="#F5F7FA")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=6)

        # Result Display Box
        self.result_card = tk.LabelFrame(
            right_column,
            text=" BMI Result ",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#1A237E",
            padx=18,
            pady=16,
            relief="solid",
            bd=1
        )
        self.result_card.pack(fill="x", pady=(0, 12))

        # Default Placeholder in Result Box
        self.result_status_label = tk.Label(
            self.result_card,
            text="No calculation yet.\nEnter your details and click 'Calculate BMI'.",
            font=("Segoe UI", 10, "italic"),
            bg="#FFFFFF",
            fg="#757575",
            pady=20
        )
        self.result_status_label.pack(fill="both", expand=True)

        # Dynamic Result Elements (Initially hidden)
        self.result_bmi_label = tk.Label(
            self.result_card,
            text="",
            font=("Segoe UI", 28, "bold"),
            bg="#FFFFFF",
            fg="#1A237E"
        )

        self.result_cat_badge = tk.Label(
            self.result_card,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg="#E8F5E9",
            fg="#2E7D32",
            padx=16,
            pady=6,
            relief="solid",
            bd=1
        )

        self.result_info_label = tk.Label(
            self.result_card,
            text="",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#424242",
            justify="center",
            wraplength=280
        )

        # Category Reference Scale Card
        ref_card = tk.LabelFrame(
            right_column,
            text=" WHO BMI Categories Reference ",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#37474F",
            padx=14,
            pady=10,
            relief="solid",
            bd=1
        )
        ref_card.pack(fill="both", expand=True)

        categories_info = [
            ("Underweight", "< 18.5", CATEGORY_COLORS["Underweight"], CATEGORY_BG_COLORS["Underweight"]),
            ("Normal", "18.5 – 24.9", CATEGORY_COLORS["Normal"], CATEGORY_BG_COLORS["Normal"]),
            ("Overweight", "25.0 – 29.9", CATEGORY_COLORS["Overweight"], CATEGORY_BG_COLORS["Overweight"]),
            ("Obese", "≥ 30.0", CATEGORY_COLORS["Obese"], CATEGORY_BG_COLORS["Obese"]),
        ]

        for idx, (name, rng, fg_color, bg_color) in enumerate(categories_info):
            row_frame = tk.Frame(ref_card, bg=bg_color, relief="groove", bd=1, padx=8, pady=4)
            row_frame.pack(fill="x", pady=3)

            dot = tk.Label(row_frame, text="●", font=("Segoe UI", 12, "bold"), fg=fg_color, bg=bg_color)
            dot.pack(side="left", padx=(0, 6))

            cat_lbl = tk.Label(row_frame, text=f"{name}", font=("Segoe UI", 9, "bold"), fg=fg_color, bg=bg_color)
            cat_lbl.pack(side="left")

            rng_lbl = tk.Label(row_frame, text=rng, font=("Segoe UI", 9, "bold"), fg="#37474F", bg=bg_color)
            rng_lbl.pack(side="right")

    # ==========================================
    # Tab 2: Historical Records Implementation
    # ==========================================
    def _build_history_tab(self) -> None:
        """Construct the Historical Records table tab."""
        # Filter & Controls Bar
        control_frame = tk.Frame(self.history_tab, bg="#F5F7FA", pady=6)
        control_frame.pack(fill="x")

        lbl_filter = tk.Label(control_frame, text="Filter by User:", font=("Segoe UI", 10, "bold"), bg="#F5F7FA")
        lbl_filter.pack(side="left", padx=(0, 8))

        self.history_user_var = tk.StringVar(value="All Users")
        self.history_user_cb = ttk.Combobox(
            control_frame,
            textvariable=self.history_user_var,
            font=("Segoe UI", 10),
            state="readonly",
            width=22
        )
        self.history_user_cb.pack(side="left", padx=(0, 10))
        self.history_user_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_history_table())

        btn_refresh = ttk.Button(control_frame, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_history_table)
        btn_refresh.pack(side="left", padx=4)

        btn_delete_rec = ttk.Button(
            control_frame,
            text="🗑️ Delete Selected",
            style="Danger.TButton",
            command=self.on_delete_selected_record
        )
        btn_delete_rec.pack(side="right", padx=(4, 0))

        btn_clear_user = ttk.Button(
            control_frame,
            text="Clear User Records",
            style="Secondary.TButton",
            command=self.on_clear_user_history
        )
        btn_clear_user.pack(side="right", padx=4)

        # Empty State Banner
        self.history_empty_lbl = tk.Label(
            self.history_tab,
            text="No BMI records found. Calculate and save measurements to view history.",
            font=("Segoe UI", 11, "italic"),
            bg="#FFFFFF",
            fg="#757575",
            pady=30,
            relief="solid",
            bd=1
        )

        # Table Frame with Treeview and Scrollbars
        self.table_frame = tk.Frame(self.history_tab, bg="#FFFFFF", relief="solid", bd=1)
        self.table_frame.pack(fill="both", expand=True, pady=(8, 0))

        columns = ("id", "user_name", "date_time", "weight", "height", "bmi", "category")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("user_name", text="User Name")
        self.tree.heading("date_time", text="Date / Time")
        self.tree.heading("weight", text="Weight (kg)")
        self.tree.heading("height", text="Height (m)")
        self.tree.heading("bmi", text="BMI")
        self.tree.heading("category", text="Category")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("user_name", width=110, anchor="w")
        self.tree.column("date_time", width=150, anchor="center")
        self.tree.column("weight", width=95, anchor="e")
        self.tree.column("height", width=95, anchor="e")
        self.tree.column("bmi", width=85, anchor="e")
        self.tree.column("category", width=120, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Add tag color styling to tree rows
        for cat_name, col in CATEGORY_COLORS.items():
            self.tree.tag_configure(cat_name, foreground=col)

    # ==========================================
    # Tab 3: BMI Trend Visualization Implementation
    # ==========================================
    def _build_trend_tab(self) -> None:
        """Construct the Matplotlib Trend Chart tab."""
        # Filter & Control Bar
        control_frame = tk.Frame(self.trend_tab, bg="#F5F7FA", pady=6)
        control_frame.pack(fill="x")

        lbl_trend_user = tk.Label(control_frame, text="Select User:", font=("Segoe UI", 10, "bold"), bg="#F5F7FA")
        lbl_trend_user.pack(side="left", padx=(0, 8))

        self.trend_user_var = tk.StringVar()
        self.trend_user_cb = ttk.Combobox(
            control_frame,
            textvariable=self.trend_user_var,
            font=("Segoe UI", 10),
            state="readonly",
            width=22
        )
        self.trend_user_cb.pack(side="left", padx=(0, 10))
        self.trend_user_cb.bind("<<ComboboxSelected>>", lambda e: self.plot_user_trend())

        btn_refresh_chart = ttk.Button(
            control_frame,
            text="🔄 Refresh Chart",
            style="Secondary.TButton",
            command=self.plot_user_trend
        )
        btn_refresh_chart.pack(side="left", padx=4)

        # Matplotlib Canvas Container Frame
        self.chart_container = tk.Frame(self.trend_tab, bg="#FFFFFF", relief="solid", bd=1)
        self.chart_container.pack(fill="both", expand=True, pady=(8, 0))

        # Create Matplotlib Figure
        self.figure = Figure(figsize=(7, 4.5), dpi=100, facecolor="#FFFFFF")
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.22)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        self._render_empty_chart_message("Select a user to display the BMI progression over time.")

    # ==========================================
    # Logic & Event Handlers
    # ==========================================
    def on_calculate(self) -> None:
        """Handle the Calculate BMI button click and validate form fields."""
        raw_user = self.user_name_var.get()
        raw_weight = self.weight_var.get()
        raw_height = self.height_var.get()

        try:
            cleaned_user, weight, height = validate_inputs(raw_user, raw_weight, raw_height)
        except ValueError as err:
            messagebox.showerror("Input Error", str(err), parent=self.root)
            self.status_var.set(f"Input validation error: {err}")
            return

        # Perform Calculation and Classification
        try:
            bmi = calculate_bmi(weight, height)
            category, color = classify_bmi(bmi)
            min_w, max_w = get_healthy_weight_range(height)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Unexpected error during calculation: {e}", parent=self.root)
            return

        # Store Current State
        self.current_user = cleaned_user
        self.current_weight = weight
        self.current_height = height
        self.current_bmi = bmi
        self.current_category = category

        # Update Result View
        self._display_calculation_result(cleaned_user, bmi, category, color, min_w, max_w)
        self.btn_save.config(state="normal")
        self.status_var.set(
            f"Calculated BMI for '{cleaned_user}': {bmi:.2f} ({category}). Click 'Save Record' to persist."
        )

    def _display_calculation_result(
        self,
        user_name: str,
        bmi: float,
        category: str,
        color: str,
        min_w: float,
        max_w: float
    ) -> None:
        """Render the calculated BMI and color-coded badge into the UI."""
        self.result_status_label.pack_forget()

        # Update BMI Label
        self.result_bmi_label.config(text=f"BMI: {bmi:.2f}", fg=color)
        self.result_bmi_label.pack(pady=(6, 2))

        # Update Category Badge
        bg_col = CATEGORY_BG_COLORS.get(category, "#F5F5F5")
        self.result_cat_badge.config(
            text=f"Category: {category}",
            fg=color,
            bg=bg_col
        )
        self.result_cat_badge.pack(pady=(0, 8))

        # Additional Context Info
        info_text = f"Healthy weight range for {self.current_height:.2f}m is {min_w:.1f} kg – {max_w:.1f} kg."
        self.result_info_label.config(text=info_text)
        self.result_info_label.pack(pady=(0, 6))

    def on_clear_inputs(self) -> None:
        """Reset input fields and results to default state."""
        self.weight_var.set("")
        self.height_var.set("")
        self.current_bmi = None
        self.current_category = None
        self.btn_save.config(state="disabled")

        self.result_bmi_label.pack_forget()
        self.result_cat_badge.pack_forget()
        self.result_info_label.pack_forget()
        self.result_status_label.pack(fill="both", expand=True)
        self.status_var.set("Inputs cleared.")

    def on_save_record(self) -> None:
        """Save the currently calculated BMI record to the SQLite database."""
        if (
            self.current_bmi is None or
            self.current_weight is None or
            self.current_height is None or
            not self.current_user
        ):
            messagebox.showwarning("No Calculation", "Please calculate a BMI before saving.", parent=self.root)
            return

        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            rec_id = self.db.add_record(
                user_name=self.current_user,
                weight=self.current_weight,
                height=self.current_height,
                bmi=self.current_bmi,
                category=self.current_category,
                recorded_at=recorded_at
            )
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Failed to save record:\n{err}", parent=self.root)
            self.status_var.set(f"Database error: {err}")
            return

        messagebox.showinfo(
            "Record Saved",
            f"Successfully saved record #{rec_id} for user '{self.current_user}'.\n"
            f"Date/Time: {recorded_at}\nBMI: {self.current_bmi:.2f} ({self.current_category})",
            parent=self.root
        )
        self.status_var.set(f"Saved BMI record #{rec_id} for '{self.current_user}'.")

        # Refresh combobox user lists across tabs
        self._load_users_into_comboboxes(selected_user=self.current_user)

    def _load_users_into_comboboxes(self, selected_user: Optional[str] = None) -> None:
        """Reload the user lists into dropdown comboboxes."""
        try:
            users = self.db.get_all_users()
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Could not load users from database:\n{err}", parent=self.root)
            users = []

        # Calculator User Combobox
        self.user_name_cb["values"] = users
        if selected_user and selected_user in users:
            self.user_name_var.set(selected_user)

        # History User Combobox
        history_options = ["All Users"] + users
        self.history_user_cb["values"] = history_options
        if selected_user and selected_user in users:
            self.history_user_var.set(selected_user)
        elif not self.history_user_var.get():
            self.history_user_var.set("All Users")

        # Trend User Combobox
        self.trend_user_cb["values"] = users
        if selected_user and selected_user in users:
            self.trend_user_var.set(selected_user)
        elif users and (not self.trend_user_var.get() or self.trend_user_var.get() not in users):
            self.trend_user_var.set(users[0])

    def _on_user_selected_in_calc(self, event=None) -> None:
        """Handle selection of an existing user from the calculator dropdown."""
        user = self.user_name_var.get().strip()
        if user:
            self.status_var.set(f"Selected user '{user}'.")

    def _on_tab_changed(self, event=None) -> None:
        """Handle tab switching and refresh tab content accordingly."""
        selected_tab_idx = self.notebook.index(self.notebook.select())
        if selected_tab_idx == 1:
            self.refresh_history_table()
        elif selected_tab_idx == 2:
            self.plot_user_trend()

    def switch_to_tab(self, tab_idx: int) -> None:
        """Programmatically switch tabs and sync user selection."""
        # Synchronize user selection if present
        current_name = self.user_name_var.get().strip()
        if current_name:
            if tab_idx == 1:
                users = list(self.history_user_cb["values"])
                if current_name in users:
                    self.history_user_var.set(current_name)
            elif tab_idx == 2:
                users = list(self.trend_user_cb["values"])
                if current_name in users:
                    self.trend_user_var.set(current_name)

        self.notebook.select(tab_idx)

    # ==========================================
    # History Operations
    # ==========================================
    def refresh_history_table(self) -> None:
        """Fetch records from SQLite and populate the Treeview table."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_user = self.history_user_var.get().strip()

        try:
            if selected_user and selected_user != "All Users":
                records = self.db.get_records_by_user(selected_user, order_asc=False)
            else:
                # Fetch all records across all users
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, user_name, weight, height, bmi, category, recorded_at
                        FROM bmi_records
                        ORDER BY datetime(recorded_at) DESC, id DESC;
                    """)
                    records = [dict(r) for r in cursor.fetchall()]
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Error fetching history records:\n{err}", parent=self.root)
            return

        if not records:
            self.table_frame.pack_forget()
            empty_msg = f"No BMI records found for '{selected_user}'." if selected_user != "All Users" else "No BMI records found in database."
            self.history_empty_lbl.config(text=empty_msg)
            self.history_empty_lbl.pack(fill="both", expand=True, pady=20)
            self.status_var.set(empty_msg)
            return

        self.history_empty_lbl.pack_forget()
        self.table_frame.pack(fill="both", expand=True, pady=(8, 0))

        for rec in records:
            self.tree.insert(
                "",
                "end",
                iid=str(rec["id"]),
                values=(
                    rec["id"],
                    rec["user_name"],
                    rec["recorded_at"],
                    f"{rec['weight']:.2f}",
                    f"{rec['height']:.2f}",
                    f"{rec['bmi']:.2f}",
                    rec["category"]
                ),
                tags=(rec["category"],)
            )

        self.status_var.set(f"Displaying {len(records)} record(s) for '{selected_user}'.")

    def on_delete_selected_record(self) -> None:
        """Delete the currently selected record from the table and database."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("Selection Required", "Please select a record in the table to delete.", parent=self.root)
            return

        record_id = int(selected_item[0])
        item_values = self.tree.item(selected_item[0])["values"]
        user_name = item_values[1]
        recorded_at = item_values[2]

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete record #{record_id} for '{user_name}' ({recorded_at})?",
            parent=self.root
        )
        if not confirmed:
            return

        try:
            deleted = self.db.delete_record(record_id)
            if deleted:
                self.tree.delete(selected_item[0])
                self._load_users_into_comboboxes()
                self.refresh_history_table()
                self.status_var.set(f"Deleted record #{record_id}.")
            else:
                messagebox.showwarning("Not Found", f"Record #{record_id} was not found.", parent=self.root)
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Failed to delete record:\n{err}", parent=self.root)

    def on_clear_user_history(self) -> None:
        """Delete all records for the selected user."""
        selected_user = self.history_user_var.get().strip()
        if not selected_user or selected_user == "All Users":
            messagebox.showinfo("Select User", "Please select a specific user to clear their history.", parent=self.root)
            return

        confirmed = messagebox.askyesno(
            "Confirm Clear History",
            f"Are you sure you want to delete ALL records for user '{selected_user}'?\nThis action cannot be undone.",
            parent=self.root
        )
        if not confirmed:
            return

        try:
            count = self.db.clear_user_records(selected_user)
            messagebox.showinfo("History Cleared", f"Deleted {count} record(s) for '{selected_user}'.", parent=self.root)
            self._load_users_into_comboboxes()
            self.refresh_history_table()
            self.status_var.set(f"Cleared {count} record(s) for '{selected_user}'.")
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Failed to clear history for '{selected_user}':\n{err}", parent=self.root)

    # ==========================================
    # Trend Chart Operations
    # ==========================================
    def _render_empty_chart_message(self, message: str) -> None:
        """Render a placeholder message on the Matplotlib canvas."""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, message,
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax.transAxes,
            fontsize=11,
            color="#757575",
            style="italic"
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_frame_on(False)
        self.canvas.draw()

    def plot_user_trend(self) -> None:
        """Generate and render the Matplotlib line chart for the selected user."""
        user_name = self.trend_user_var.get().strip()
        if not user_name:
            self._render_empty_chart_message("No user selected.\nSelect a user to display the BMI progression.")
            self.status_var.set("No user selected for trend chart.")
            return

        try:
            records = self.db.get_records_by_user(user_name, order_asc=True)
        except DatabaseError as err:
            messagebox.showerror("Database Error", f"Failed to fetch trend records:\n{err}", parent=self.root)
            self._render_empty_chart_message(f"Error loading records: {err}")
            return

        if not records:
            self._render_empty_chart_message(
                f"No BMI records found for '{user_name}'.\nCalculate and save measurements to view trends."
            )
            self.status_var.set(f"No records found for '{user_name}'.")
            return

        self.ax.clear()
        self.ax.set_frame_on(True)

        # Parse data points
        timestamps = []
        dates_display = []
        bmis = []

        for rec in records:
            raw_date = rec["recorded_at"]
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                timestamps.append(dt)
                dates_display.append(dt.strftime("%b %d, %H:%M"))
            except ValueError:
                # Fallback if timestamp format differs
                timestamps.append(raw_date)
                dates_display.append(raw_date)
            bmis.append(float(rec["bmi"]))

        # Add background WHO BMI Category Reference Bands
        y_min = max(10.0, min(bmis) - 3.0)
        y_max = max(35.0, max(bmis) + 4.0)

        self.ax.axhspan(0, 18.5, facecolor="#E3F2FD", alpha=0.6, label="Underweight (<18.5)")
        self.ax.axhspan(18.5, 25.0, facecolor="#E8F5E9", alpha=0.6, label="Normal (18.5-24.9)")
        self.ax.axhspan(25.0, 30.0, facecolor="#FFF3E0", alpha=0.6, label="Overweight (25.0-29.9)")
        self.ax.axhspan(30.0, 100.0, facecolor="#FFEBEE", alpha=0.6, label="Obese (≥30.0)")

        # Threshold boundary reference lines
        self.ax.axhline(18.5, color="#1976D2", linestyle="--", linewidth=0.8, alpha=0.5)
        self.ax.axhline(25.0, color="#2E7D32", linestyle="--", linewidth=0.8, alpha=0.5)
        self.ax.axhline(30.0, color="#E65100", linestyle="--", linewidth=0.8, alpha=0.5)

        # Plot Trend Line and Markers
        x_indices = list(range(len(bmis)))
        
        # Main progression line
        self.ax.plot(
            x_indices,
            bmis,
            color="#0D47A1",
            linestyle="-",
            linewidth=2.5,
            marker="o",
            markersize=7,
            markerfacecolor="#FFFFFF",
            markeredgecolor="#0D47A1",
            markeredgewidth=2,
            label="BMI Measurement"
        )

        # Value Annotations on Data Points
        for i, val in enumerate(bmis):
            self.ax.annotate(
                f"{val:.2f}",
                (x_indices[i], val),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=9,
                fontweight="bold",
                color="#1A237E",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#B0BEC5", alpha=0.85)
            )

        # Chart Labels and Layout
        self.ax.set_title(f"BMI Trend for {user_name}", fontsize=13, fontweight="bold", pad=12, color="#1A237E")
        self.ax.set_xlabel("Measurement Date & Time", fontsize=10, fontweight="bold", labelpad=8, color="#37474F")
        self.ax.set_ylabel("Body Mass Index (BMI)", fontsize=10, fontweight="bold", labelpad=8, color="#37474F")

        # X-Axis Tick Formatting
        self.ax.set_xticks(x_indices)
        self.ax.set_xticklabels(dates_display, rotation=25, ha="right", fontsize=8)
        
        if len(bmis) == 1:
            self.ax.set_xlim(-0.6, 0.6)
        else:
            self.ax.set_xlim(-0.3, len(bmis) - 0.7)
            
        self.ax.set_ylim(y_min, y_max)
        self.ax.grid(True, linestyle=":", alpha=0.6, color="#90A4AE")

        # Clean Legend
        handles, labels = self.ax.get_legend_handles_labels()
        self.ax.legend(
            handles=handles,
            loc="upper right",
            fontsize=8,
            framealpha=0.9,
            edgecolor="#CFD8DC"
        )

        self.figure.tight_layout()
        self.canvas.draw()
        self.status_var.set(f"Rendered BMI trend for '{user_name}' ({len(records)} measurement(s)).")
