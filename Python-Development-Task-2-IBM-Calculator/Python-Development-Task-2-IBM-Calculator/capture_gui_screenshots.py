"""
Script to capture actual screenshots of the running BMI Calculator Tkinter application.
Uses Win32 GDI PrintWindow to capture pixel-perfect window renders.
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image

from database import DatabaseManager
from gui import BMICalculatorApp
from seed_sample_data import seed_database

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Set DPI awareness for sharp renders
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def capture_window_to_image(window: tk.Tk) -> Image.Image:
    """Capture a Tkinter window to a PIL Image using Win32 API."""
    window.update()
    window.update_idletasks()
    time.sleep(0.1)

    hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    hwndDC = user32.GetWindowDC(hwnd)
    mfcDC = gdi32.CreateCompatibleDC(hwndDC)
    saveBitMap = gdi32.CreateCompatibleBitmap(hwndDC, w, h)
    gdi32.SelectObject(mfcDC, saveBitMap)

    # 2 = PW_RENDERFULLCONTENT
    user32.PrintWindow(hwnd, mfcDC, 2)

    # Convert HBITMAP to PIL Image via GetDIBits
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down DIB
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0  # BI_RGB

    buffer_size = w * h * 4
    buffer = ctypes.create_string_buffer(buffer_size)

    gdi32.GetDIBits(
        mfcDC,
        saveBitMap,
        0,
        h,
        buffer,
        ctypes.byref(bmi),
        0  # DIB_RGB_COLORS
    )

    # Cleanup GDI objects
    gdi32.DeleteObject(saveBitMap)
    gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(hwnd, hwndDC)

    # Create PIL image from BGRA buffer
    raw_img = Image.frombuffer("RGBA", (w, h), buffer, "raw", "BGRA", 0, 1)
    # Convert to RGB (or keep RGBA)
    img = raw_img.convert("RGB")
    return img


def main():
    artifact_dir = r"C:\Users\TempAdmin\.gemini\antigravity\brain\5dacd9e4-cd08-4a47-9dbf-5251da058884"
    os.makedirs(artifact_dir, exist_ok=True)

    # Seed sample database
    seed_database("bmi_records.db")
    db = DatabaseManager("bmi_records.db")

    # -------------------------------------------------------------
    # 1. Main Calculator View with John's calculation (Normal - Green)
    # -------------------------------------------------------------
    root = tk.Tk()
    root.geometry("840x740+50+50")
    app = BMICalculatorApp(root=root, db_manager=db)
    
    app.user_name_var.set("John")
    app.weight_var.set("70")
    app.height_var.set("1.75")
    app.on_calculate()
    root.update()

    img_calc = capture_window_to_image(root)
    calc_path_art = os.path.join(artifact_dir, "bmi_calculator_main.png")
    img_calc.save(calc_path_art)
    print("Saved:", calc_path_art)

    # -------------------------------------------------------------
    # 2. Historical Records View (Tab 2)
    # -------------------------------------------------------------
    app.switch_to_tab(1)
    app.history_user_var.set("All Users")
    app.refresh_history_table()
    root.update()

    img_hist = capture_window_to_image(root)
    hist_path_art = os.path.join(artifact_dir, "bmi_history_view.png")
    img_hist.save(hist_path_art)
    print("Saved:", hist_path_art)

    # -------------------------------------------------------------
    # 3. BMI Trend Chart View (Tab 3) for John Doe
    # -------------------------------------------------------------
    app.switch_to_tab(2)
    app.trend_user_var.set("John Doe")
    app.plot_user_trend()
    root.update()

    img_trend = capture_window_to_image(root)
    trend_path_art = os.path.join(artifact_dir, "bmi_trend_chart.png")
    img_trend.save(trend_path_art)
    print("Saved:", trend_path_art)

    # -------------------------------------------------------------
    # 4. Color Feedback Comparison (Overweight / Obese / Underweight)
    # -------------------------------------------------------------
    app.switch_to_tab(0)
    app.user_name_var.set("David Miller")
    app.weight_var.set("105")
    app.height_var.set("1.78")
    app.on_calculate()
    root.update()

    img_obese = capture_window_to_image(root)
    obese_path_art = os.path.join(artifact_dir, "bmi_result_obese.png")
    img_obese.save(obese_path_art)
    print("Saved:", obese_path_art)

    root.destroy()
    print("All screenshots captured successfully!")


if __name__ == "__main__":
    main()
