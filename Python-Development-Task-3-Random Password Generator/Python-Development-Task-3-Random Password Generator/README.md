# 🔐 Random Password Generator (Desktop Application)

A cryptographically secure, modern desktop GUI application built in Python for generating customizable, high-entropy random passwords.

Designed according to industry security best practices, the application utilizes Python's native `secrets` module (a Cryptographically Secure Pseudo-Random Number Generator, or CSPRNG) to protect against entropy exhaustion and predictability vulnerabilities.

---

## 🌟 Features

### 🎛️ Configurable Password Generation
- **Customizable Length**: Choose password length using synchronized slider and spinbox controls (Minimum: **8**, Default: **16**, Maximum: **128**).
- **Character Categories**: Select any combination of:
  - Uppercase Letters (`A-Z`)
  - Lowercase Letters (`a-z`)
  - Numbers (`0-9`)
  - Special Symbols (`!@#$%^&*()_+-=[]{}|;:,.<>?/~`)
- **Category Guarantee**: Enforces that **at least 2 character types** are selected and guarantees that **every selected type** appears at least once in the generated password.
- **Ambiguous Character Filter**: Exclude visually confusing characters (e.g., `0`, `O`, `o`, `1`, `l`, `I`, `|`) to ensure generated passwords can be easily transcribed.

### 🛡️ Security & Cryptography
- **Built-in `secrets` CSPRNG**: Utilizes operating system entropy sources (`secrets.choice` and `secrets.randbelow`).
- **Cryptographic Fisher-Yates Shuffle**: Rearranges required category characters using `secrets.randbelow()` to eliminate positional predictability without compromising cryptographic entropy.
- **No `random` Module Usage**: Intentionally avoids Python's standard `random` module (which uses the non-cryptographic Mersenne Twister PRNG).

### 📊 Deterministic Password Strength Meter
- Real-time visual progress bar and color-coded status badge:
  - 🔴 **Weak**: Short length (< 10) or low category diversity.
  - 🟠 **Medium**: Balanced length (10–13) with multiple categories.
  - 🟢 **Strong**: High length (14+) and high diversity / Shannon entropy (70+ bits).
- Displays calculated Shannon entropy bits and actionable security recommendations.

### 📋 Clipboard Integration
- **Automatic Clipboard Copy**: Newly generated passwords are automatically copied to your clipboard on generation.
- **Dedicated Copy Button**: Manually copy the current password at any time.
- **Graceful Error Handling**: Employs fallback mechanisms if system clipboard services are restricted.

### 🕒 Session-Only Generation History
- Displays the **last 5 generated passwords** with timestamps and strength indicators.
- **Strictly In-Memory (FIFO)**: Automatically discards older entries when new ones are generated.
- **Zero Disk I/O / Zero Logging**: Passwords are never written to disk, saved to persistent configuration files, or exposed to terminal/log outputs.

---

## 🛠️ Technology Stack

- **Python 3.8+**
- **Tkinter / ttk**: Desktop GUI toolkit
- **`secrets`** (Python Built-in): Cryptographic random generation
- **`string`** (Python Built-in): Character set definitions
- **`pyperclip`**: Cross-platform clipboard operations

---

## 🚀 Installation & Getting Started

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your system.

### 2. Install Dependencies
Install external requirements using `pip`:

```bash
pip install -r requirements.txt
```

> **Note**: Tkinter is bundled by default with standard Python installations on Windows and macOS. On Linux, if Tkinter is not already present, install it via `sudo apt-get install python3-tk`.

### 3. Run the Application
Launch the desktop GUI:

```bash
python main.py
```

### 4. Run Automated Tests
Execute the comprehensive test suite (17 automated unit and integration tests):

```bash
python -m unittest discover -v
```

---

## 🔍 How Password Generation Works

1. **Validation**: The generator verifies that `length >= 8` and at least 2 character categories are selected.
2. **Category Guarantee**: One character is securely drawn from each active character pool using `secrets.choice()`.
3. **Pool Construction & Fill**: The remaining positions (`length - selected_categories`) are drawn from the unified pool using `secrets.choice()`.
4. **Cryptographic Shuffle**: The resulting character list is shuffled using an in-place Fisher-Yates algorithm powered by `secrets.randbelow()`, ensuring uniform distribution without predictable category positions.
5. **Display & Auto-Copy**: The password is rendered in a clear monospace font, evaluated for entropy strength, auto-copied to the system clipboard, and added to the bounded session history.

---

## 🔐 Why `secrets` Instead of `random`?

| Feature | `random` Module | `secrets` Module |
| :--- | :--- | :--- |
| **Algorithm** | Mersenne Twister (MT19937) | Operating System CSPRNG (`CryptGenRandom` / `getrandom`) |
| **Security Status** | ❌ **Insecure** for cryptography | ✅ **Cryptographically Secure** |
| **Predictability** | State can be reconstructed after observing 624 32-bit outputs | State is unpredictable and computationally infeasible to invert |
| **Intended Use** | Simulations, games, statistical modeling | Passwords, security tokens, cryptographic keys |

---

## 📁 Project Structure

```
focused-salk/
├── password_generator/
│   ├── __init__.py           # Package exports
│   ├── generator.py          # Cryptographic generation, pools, and validation
│   ├── strength.py           # Strength scoring, Shannon entropy, and color metrics
│   ├── history.py            # Bounded in-memory session history (FIFO max 5)
│   └── gui.py                # Modern Tkinter/ttk desktop GUI layout and handlers
├── main.py                   # Desktop application entry point
├── requirements.txt          # External dependencies (pyperclip)
├── test_generator.py         # Unit tests for generation logic, security, and strength
├── test_gui.py               # Automated GUI interaction and validation tests
└── README.md                 # Complete documentation and user manual
```

---

## 📜 License
Open source and free for personal and educational use.
