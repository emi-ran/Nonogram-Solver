# 🧩 Nonogram Solver & Autonomous Player

<p align="center">
  <a href="README.md"><b>English</b></a> •
  <a href="README.tr.md">Türkçe</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/ADB-Android%20Automation-orange.svg" alt="ADB">
  <img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Tests-23%20Passing-brightgreen.svg" alt="Tests">
</p>

A fast, dynamic, end-to-end **Android Nonogram Solver and Autonomous Player** powered by Computer Vision (OpenCV), Constraint Propagation, and ADB automation. Supports continuous infinite play, Daily Challenges, Special Events (Lilac Roses), and customizable interactive tapping patterns.

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
│       │   ├── grid.py      # Regular equidistant grid extraction (5x5 to 20x20)
│       │   ├── ocr.py       # Number recognition & card clue parsing
│       │   └── templates.py # Pre-computed binary digit templates
│       ├── device/          # Android ADB bridge
│       │   └── adb.py       # Screencap & in-memory decoding, high-speed batch taps
│       └── automation/      # Autonomous state machine & game modes
│           ├── runner.py    # Pipeline runner (Capture -> OCR -> Solve -> Tap)
│           ├── states.py    # Screen state detector (Playing, Completed, Dialog)
│           ├── patterns.py  # Interactive tapping patterns (Ping-Pong, Center-Out, etc.)
│           ├── auto_player.py # Autonomous game loop coordinator
│           └── modes/       # Strategy-pattern extensible game modes
│               ├── base.py    # Base game mode interface
│               ├── normal.py  # Normal / Classic mode (Next Level auto-advancement)
│               ├── daily.py   # Daily Challenge mode
│               └── events.py  # Event modes (Rise & Dice, Adventure, Lilac Roses)
├── tests/                   # Automated unit & integration tests (23 tests)
│   ├── test_solver.py       # Core solver unit tests
│   ├── test_vision.py       # Vision & OCR tests against sample boards (5x5 to 20x20)
│   ├── test_patterns.py     # Tapping pattern permutation tests
│   └── test_automation.py   # State detector & game mode tests
├── DEVELOPMENT.md           # Deep-dive architecture & developer guide
├── main.py                  # Primary CLI entry point
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
# or
python main.py --auto --mode lilac_roses

# 4. Other Events (Rise & Dice, Adventure)
python main.py --auto --mode event
python main.py --auto --mode adventure

# 🎲 Tapping Patterns & Visual Modes (--random [MODE]):
# 1. Random Selector (Picks a random fun pattern per level):
python main.py --auto --mode lilac --random

# 2. bfs (Breadth-First Flood Fill / Ripple spread):
python main.py --auto --mode lilac --random bfs

# 3. dfs (Depth-First Ant Crawler / Labyrinth trace):
python main.py --auto --mode lilac --random dfs

# 4. spiral (Clockwise inward swirl):
python main.py --auto --mode lilac --random spiral

# 5. diagonal (45-degree slash wave):
python main.py --auto --mode lilac --random diagonal

# 6. checkerboard (Light tiles first, then dark tiles):
python main.py --auto --mode lilac --random checkerboard

# 7. corners_in (4-way corner convergence toward center):
python main.py --auto --mode lilac --random corners_in

# 8. gravity (Tetris / sand stacking from bottom to top):
python main.py --auto --mode lilac --random gravity

# 9. shuffle (Pure uniform random shuffle):
python main.py --auto --mode lilac --random shuffle

# 10. ping_pong, center_out, reverse, snake:
python main.py --auto --mode lilac --random ping_pong
python main.py --auto --mode lilac --random center_out
python main.py --auto --mode lilac --random reverse
python main.py --auto --mode lilac --random snake
```

#### 🎯 Single Level (Solve Current Board Once)
```powershell
# Solve and automatically tap solution on screen:
python main.py --apply
python main.py --apply --random center_out

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
python main.py --offline assets/samples/extreme.png
python main.py --offline assets/samples/Hard.png
python main.py --offline assets/samples/Medium.png
```

### 3. Running Tests
```powershell
python -m unittest discover -s tests
```
