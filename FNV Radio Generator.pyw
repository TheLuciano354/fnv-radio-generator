"""Double-click to open the radio generator (runs without a console window)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fnv_radio.gui import main  # noqa: E402

main()
