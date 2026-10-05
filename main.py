"""
Launcher for the School Management System.

Both GUIs share the same data model (part1_oop.py) and the same
school_data.json file, so data saved in one interface can be loaded
in the other. Each GUI runs in its own process because Tkinter and
PyQt5 cannot share one event loop.

Usage:
    python main.py            # opens a small chooser window
    python main.py tkinter    # Tkinter GUI (Part 2)
    python main.py pyqt       # PyQt5 GUI (Part 3)
    python main.py database   # SQLite-backed Tkinter GUI (Part 4)
    python main.py demo       # console OOP demo (Part 1)
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

APPS = {
    "tkinter": ("Tkinter GUI", "part2_tkinter.py"),
    "pyqt": ("PyQt5 GUI", "part3_pyqt.py"),
    "database": ("Database GUI (SQLite)", "part4_database.py"),
    "demo": ("Console OOP demo", "part1_oop.py"),
}


def launch(key, wait=False):
    """Start one of the apps in a separate Python process."""
    script = os.path.join(HERE, APPS[key][1])
    proc = subprocess.Popen([sys.executable, script], cwd=HERE)
    if wait:
        proc.wait()
    return proc


def chooser():
    """Small Tkinter window with one button per interface."""
    import tkinter as tk

    root = tk.Tk()
    root.title("School Management System")
    tk.Label(root, text="Choose an interface", font=("Helvetica", 14, "bold")).pack(padx=20, pady=(15, 10))
    for key in ("tkinter", "pyqt", "database"):
        label = APPS[key][0]
        tk.Button(root, text=label, width=25, command=lambda k=key: launch(k)).pack(padx=20, pady=4)
    tk.Button(root, text="Quit", width=25, command=root.destroy).pack(padx=20, pady=(10, 15))
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
        if choice not in APPS:
            sys.exit(f"Unknown option '{choice}'. Choose from: {', '.join(APPS)}")
        launch(choice, wait=True)
    else:
        chooser()
