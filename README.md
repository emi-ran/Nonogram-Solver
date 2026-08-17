# Nonogram Solver

Dynamic Android Nonogram solver. Reads current grid and clues from screenshot, solves line constraints, and optionally taps filled cells through ADB.

## Run

```powershell
python nonogram_solver.py
python nonogram_solver.py --apply
python nonogram_solver.py --offline --screenshot Hard.png
```

- Default: capture and solve only. No taps.
- `--apply`: tap filled cells. App must start level in square/fill mode.
- `--screenshot path.png`: save and read specified screenshot path.
- `--offline`: read existing screenshot without ADB. Never sends taps.

## Requirements

- One connected Android device with USB debugging enabled.
- `adb` on `PATH`.
- Python packages in `requirements.txt`.

Supports square Nonogram boards from 5x5 through 20x20. Grid size comes from visible board lines; clues come from local OCR; no level data is hardcoded.
