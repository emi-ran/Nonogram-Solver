"""Main CLI entry point for Nonogram Solver."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from src.nonogram.automation.auto_player import AutoPlayer, AutoPlayerConfig
from src.nonogram.automation.runner import run_pipeline
from src.nonogram.config import DEFAULT_SCREENSHOT_PATH
from src.nonogram.device.adb import ADBController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dynamic Android Nonogram Solver & Auto-Player."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Tap solution cells on the connected Android device.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Analyze an existing local screenshot without ADB.",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=None,
        help="Path to screenshot file (e.g. error.png, board.png).",
    )
    parser.add_argument(
        "--save-screenshot",
        action="store_true",
        help="Save captured screenshot to disk (default file: nonogram-screen.png).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Specific ADB device serial if multiple devices are connected.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run in auto-player mode (solves levels consecutively).",
    )
    parser.add_argument(
        "--max-levels",
        type=int,
        default=10,
        help="Maximum levels to play in auto mode (default: 10).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.offline:
        if args.apply:
            print("Error: --apply cannot be used together with --offline.", file=sys.stderr)
            sys.exit(1)
        if args.screenshot is None:
            print("Error: --offline requires specifying a screenshot via --screenshot <path.png>", file=sys.stderr)
            sys.exit(1)

    if args.auto:
        device = ADBController(serial=args.device)
        config = AutoPlayerConfig(
            max_levels=args.max_levels,
            save_screenshots=args.save_screenshot or (args.screenshot is not None),
            screenshot_path=args.screenshot or DEFAULT_SCREENSHOT_PATH,
        )
        player = AutoPlayer(config=config, device=device)
        print(f"Starting Auto-Player mode (target: {args.max_levels} levels)...")

        def on_solved(level: int, res):
            print(f"-> Solved Level #{level}: {res.puzzle.rows}x{res.puzzle.columns} grid ({res.filled_count} filled cells)")

        completed = player.run_loop(on_level_solved=on_solved)
        print(f"Auto-Player completed {completed} levels.")
        return

    # Single solve mode
    device = ADBController(serial=args.device) if not args.offline else None

    try:
        result = run_pipeline(
            screenshot_path=args.screenshot,
            device=device,
            apply_taps=args.apply,
            offline=args.offline,
            save_screenshot=args.save_screenshot,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    p = result.puzzle
    print(f"Recognized {p.rows}x{p.columns} Nonogram; {result.filled_count} filled cells.")
    print(f"Rows: {p.row_clues}")
    print(f"Columns: {p.column_clues}")

    if args.apply:
        print("Solution taps applied successfully.")


if __name__ == "__main__":
    main()
