"""
Main Application Entry Point: ATM Cash Management DSS
Runs Executive Dashboard by default and provides seamless navigation across all 7 pages.
"""

import runpy
from pathlib import Path

# Always dynamically execute the latest Executive Dashboard on root run
exec_page_path = Path(__file__).parent / "pages" / "01_Executive_Dashboard.py"
runpy.run_path(str(exec_page_path), run_name="__main__")
