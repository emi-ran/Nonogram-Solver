"""Centralized configuration and constants for Nonogram Solver."""

from pathlib import Path

# Paths
DEFAULT_SCREENSHOT_PATH = Path("nonogram-screen.png")
SAMPLES_DIR = Path("assets/samples")

# Grid Recognition Constraints
ALLOWED_GRID_SIZES = {5, 10, 15, 20}
MIN_GRID_COORDINATE_Y = 760
MAX_GRID_COORDINATE_Y = 1850
MIN_GRID_COORDINATE_X = 220
LINE_GAP_THRESHOLD = 20
LINE_PROJECTION_THRESHOLD = 800

# Digit / Template Matching
DIGIT_WIDTH = 16
DIGIT_HEIGHT = 24
DIGIT_THRESHOLD = 0.3
OCR_BINARIZATION_THRESHOLD = 150
GLYPH_MIN_AREA = 30
GLYPH_MIN_HEIGHT = 15
GLYPH_MIN_WIDTH = 3
