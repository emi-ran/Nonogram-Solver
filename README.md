# Nonogram Solver & Autonomous Auto-Player

Dynamic Android Nonogram solver and full autonomous auto-player. Captures screenshots via ADB directly in RAM (zero disk I/O), reads board clues & UI state via OpenCV, solves constraint matrices with an MRV backtracking solver, and automates continuous level progression.

## Project Structure

```text
Nonogram-Solver/
├── assets/
│   └── samples/             # Sample screenshots for offline testing & state verification
├── src/
│   └── nonogram/
│       ├── config.py        # Central configuration & tolerances
│       ├── solver/          # Pure Python Nonogram solver engine
│       │   ├── engine.py    # Pattern generator & constraint solver
│       │   └── models.py    # Board, Clue, and Layout data models
│       ├── vision/          # Vision and OCR processing
│       │   ├── grid.py      # Regular equidistant grid extraction
│       │   ├── ocr.py       # Number recognition & card clue parsing
│       │   └── templates.py # Pre-computed binary digit templates
│       ├── device/          # Android ADB bridge
│       │   └── adb.py       # Screencap & in-memory decoding, high-speed batch taps
│       └── automation/      # Autonomous state machine & game modes
│           ├── runner.py    # Pipeline runner (Capture -> OCR -> Solve -> Tap)
│           ├── states.py    # Screen state detector (Playing, Completed, Dialog)
│           ├── auto_player.py # Autonomous game loop coordinator
│           └── modes/       # Strategy-pattern extensible game modes
│               ├── base.py    # Base game mode interface
│               ├── normal.py  # Normal / Classic mode (Next Level auto-advancement)
│               ├── daily.py   # Daily Challenge mode
│               └── events.py  # Event modes (Rise & Dice, Adventure, Lilac Roses)
├── tests/                   # Automated unit & integration tests
│   ├── test_solver.py       # Core solver unit tests
│   ├── test_vision.py       # Vision & OCR tests against sample boards
│   └── test_automation.py   # State detector & game mode tests
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

#### 🤖 Fully Autonomous Mode (Continuous Play)
Runs in a continuous loop: detects active board -> solves & taps -> detects "Level Completed" -> taps "Next Level" -> dismisses event/reward dialogs -> repeats.

```powershell
# 1. Normal (Classic) Mode - Continuous Autonomous Play
python main.py --auto --mode normal

# 2. Daily Challenges Mode
python main.py --auto --mode daily
python main.py --auto --mode daily --max-levels 5

# 3. Lilac Roses Event Mode
python main.py --auto --mode lilac
# veya
python main.py --auto --mode lilac_roses

# 4. Other Events (Rise & Dice, Adventure)
python main.py --auto --mode event
python main.py --auto --mode adventure
```

#### 🎯 Single Level (Solve Current Board Once)
```powershell
# Solve and automatically tap solution on screen:
python main.py --apply

# Solve only (dry-run, prints detected clues and solution, no taps):
python main.py
```

#### 📸 Capture Screenshot Only (No Solving)
Takes a screenshot from the connected device and exits immediately:
```powershell
# Saves to default nonogram-screen.png:
python main.py --screenshot

# Saves to custom file name:
python main.py --screenshot board.png
```

#### 🧪 Offline Testing (Local Image Analysis)
```powershell
python main.py --offline assets/samples/Hard.png
python main.py --offline assets/samples/Medium.png
```

### 3. Running Tests
```powershell
python -m unittest discover tests
```
