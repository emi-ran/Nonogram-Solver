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
        "--screenshot",
        "--capture",
        dest="screenshot",
        type=Path,
        nargs="?",
        const=DEFAULT_SCREENSHOT_PATH,
        default=None,
        help="Capture and save screenshot only (e.g. --screenshot error.png), without solving.",
    )
    parser.add_argument(
        "--file",
        "--image",
        dest="offline_image",
        type=Path,
        default=None,
        help="Path to existing local screenshot for offline solving.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Analyze an existing local screenshot without ADB (requires --file or --screenshot).",
    )
    parser.add_argument(
        "--save-screenshot",
        action="store_true",
        help="Save captured screenshot to disk during solve mode.",
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
        help="Run in fully autonomous auto-player mode.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="normal",
        choices=["normal", "daily", "event", "adventure", "rise_dice"],
        help="Game mode for auto-player (default: normal).",
    )
    parser.add_argument(
        "--max-levels",
        type=int,
        default=50,
        help="Maximum levels to play in auto mode (default: 50).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Polling interval between state checks in seconds (default: 1.0s).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 1. Capture-only mode: Take screenshot and exit immediately
    if args.screenshot is not None and not args.offline and not args.auto and not args.apply:
        device = ADBController(serial=args.device)
        target_path = Path(args.screenshot)
        if not target_path.suffix:
            target_path = target_path.with_suffix(".png")
        try:
            device.capture_screenshot(target_path)
            print(f"[Capture] Screenshot successfully captured and saved to: {target_path}")
        except Exception as e:
            print(f"Error capturing screenshot: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 2. Offline solving mode
    offline_path = args.offline_image or (args.screenshot if args.offline else None)
    if args.offline:
        if args.apply:
            print("Error: --apply cannot be used together with --offline.", file=sys.stderr)
            sys.exit(1)
        if offline_path is None:
            print("Error: --offline requires specifying an image via --file <path.png> or --screenshot <path.png>", file=sys.stderr)
            sys.exit(1)

    # 3. Autonomous gameplay mode
    if args.auto:
        device = ADBController(serial=args.device)
        config = AutoPlayerConfig(
            mode=args.mode,
            max_levels=args.max_levels,
            poll_interval=args.poll_interval,
            save_screenshots=args.save_screenshot,
            screenshot_path=args.screenshot or DEFAULT_SCREENSHOT_PATH,
        )
        player = AutoPlayer(config=config, device=device)

        def on_progress(completed: int, msg: str):
            pass

        completed = player.run_loop(on_progress=on_progress)
        return

    # 4. Single solve mode (online or offline)
    device = ADBController(serial=args.device) if not args.offline else None

    try:
        result = run_pipeline(
            screenshot_path=offline_path if args.offline else args.screenshot,
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
