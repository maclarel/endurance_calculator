"""
Stable entrypoint for packaging.

PyInstaller target:
  pyinstaller --onefile --name endurance_calculator main.py
"""

from endurance import RaceStrategyApp
import tkinter as tk


def main() -> None:
    root = tk.Tk()
    app = RaceStrategyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
