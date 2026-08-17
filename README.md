# Nonogram Solver & Auto-Player

Dynamic Android Nonogram solver and auto-player. Captures screenshots via ADB, reads the board grid & clues with template-based OCR, solves constraint matrices with an MRV backtracking solver, and automates level completion.

## Project Structure

```text
Nonogram-Solver/
├── assets/
│   └── samples/             # Sample screenshots for offline testing
├── src/
│   └── nonogram/
│       ├── config.py        # Central configuration & tolerances
│       ├── solver/          # Pure Python Nonogram solver engine
│       │   ├── engine.py    # Pattern generator & constraint solver
│       │   └── models.py    # Board, Clue, and Layout data models
│       ├── vision/          # Vision and OCR processing
│       │   ├── grid.py      # Grid detection and line alignment
│       │   ├── ocr.py       # Number recognition & card clue parsing
│       │   └── templates.py # Pre-computed binary digit templates
│       ├── device/          # Android ADB bridge
│       │   └── adb.py       # Screencap and high-speed batch tapping
│       └── automation/      # Game loop & auto-progression
│           ├── runner.py    # Pipeline runner (Capture -> OCR -> Solve -> Tap)
│           └── auto_player.py # Automated level progression loop
├── tests/                   # Automated unit & integration tests
│   ├── test_solver.py       # Core solver unit tests
│   └── test_vision.py       # Vision & OCR tests against sample boards
├── main.py                  # Primary CLI entry point
├── nonogram_solver.py       # Backward-compatible wrapper
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Requirements
- Python 3.9+
- Connected Android device with USB debugging enabled (`adb devices`)
- Python dependencies:
  ```powershell
  pip install -r requirements.txt
  ```

### 2. Usage

#### Run on Live Device (Single Board)
```powershell
# Solve and output clues/solution (dry-run, no taps):
python main.py

# Solve and automatically tap solution on screen:
python main.py --apply
```

#### Run in Auto-Player Mode (Multiple Levels)
```powershell
# Automatically solve and advance consecutive levels:
python main.py --auto --max-levels 20
```

#### Offline Testing (No Device Needed)
```powershell
python main.py --offline --screenshot assets/samples/Hard.png
python main.py --offline --screenshot assets/samples/Medium.png
python main.py --offline --screenshot assets/samples/Basic.png
```

### 3. Running Tests
```powershell
python -m unittest discover tests
```
