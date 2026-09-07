"""
Sudoku Game & AI Solver — Main Launcher
=========================================
Launches the CustomTkinter GUI for the Sudoku AI Solver.
"""

import sys
import os

# Add the AI-CCP inner package directory to sys.path so modules can import seamlessly
package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "AI-CCP", "AI-CCP"))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

if __name__ == "__main__":
    from main_gui import SudokuApp
    app = SudokuApp()
    app.mainloop()
