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
        prog="python main.py",
        description="Dynamic Android Nonogram Solver & Autonomous Player.",
        epilog="""
Examples:
  python main.py --auto                          # Play levels autonomously until Ctrl+C
  python main.py --auto --mode daily             # Play Daily Challenges autonomously
  python main.py --auto --max-levels 20          # Play 20 levels and exit
  python main.py --apply                         # Solve current on-screen puzzle and tap
  python main.py                                 # Dry-run solve on current screen (no taps)
  python main.py --screenshot                    # Capture screen to nonogram-screen.png and exit
  python main.py --screenshot screen.png         # Capture screen to screen.png and exit
  python main.py --offline assets/samples/Hard.png # Solve a local image file
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Core Execution Modes
    mode_group = parser.add_argument_group("Execution Modes")
    mode_group.add_argument(
        "--auto",
        action="store_true",
        help="Run fully autonomous gameplay (solves, taps next level, handles menus).",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Solve current on-screen level and tap solution cells on Android device.",
    )
    mode_group.add_argument(
        "--screenshot",
        type=Path,
        nargs="?",
        const=DEFAULT_SCREENSHOT_PATH,
        default=None,
        metavar="PATH",
        help="Capture screenshot to PATH (default: nonogram-screen.png). When used alone, exits immediately.",
    )
    mode_group.add_argument(
        "--offline",
        type=Path,
        default=None,
        metavar="IMAGE_PATH",
        help="Solve a local image file without connecting to ADB.",
    )

    # Auto-Player Options
    auto_group = parser.add_argument_group("Auto-Player Options")
    auto_group.add_argument(
        "--mode",
        type=str,
        default="normal",
        choices=["normal", "daily", "event", "adventure", "rise_dice", "lilac", "lilac_roses"],
        help="Game mode for auto-player (default: normal).",
    )
    auto_group.add_argument(
        "--max-levels",
        type=int,
        default=None,
        metavar="N",
        help="Maximum levels to play in auto mode (default: unlimited, runs until Ctrl+C).",
    )
    auto_group.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        metavar="SEC",
        help="Polling interval between state checks in seconds (default: 1.0s).",
    )

    # Gameplay & Interaction Options
    gameplay_group = parser.add_argument_group("Gameplay Options")
    gameplay_group.add_argument(
        "--random",
        action="store_true",
        help="Tap solved cells in randomized order instead of sequential row-by-row.",
    )

    # Device Options
    device_group = parser.add_argument_group("Device Options")
    device_group.add_argument(
        "--device",
        type=str,
        default=None,
        metavar="SERIAL",
        help="Specific ADB device serial if multiple devices are connected.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 1. Capture-only mode: Take screenshot and exit immediately when neither --auto nor --apply is used
    if args.screenshot is not None and not args.auto and not args.apply and args.offline is None:
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

    # 2. Autonomous gameplay mode
    if args.auto:
        device = ADBController(serial=args.device)
        save_screenshots = args.screenshot is not None
        screenshot_path = Path(args.screenshot) if args.screenshot is not None else DEFAULT_SCREENSHOT_PATH
        config = AutoPlayerConfig(
            mode=args.mode,
            max_levels=args.max_levels,
            poll_interval=args.poll_interval,
            random_order=args.random,
            save_screenshots=save_screenshots,
            screenshot_path=screenshot_path,
        )
        player = AutoPlayer(config=config, device=device)

        def on_progress(completed: int, msg: str):
            pass

        completed = player.run_loop(on_progress=on_progress)
        return

    # 3. Single solve mode (online or offline)
    is_offline = args.offline is not None
    if is_offline and args.apply:
        print("Error: --apply cannot be used together with --offline.", file=sys.stderr)
        sys.exit(1)

    device = ADBController(serial=args.device) if not is_offline else None

    save_screenshots = args.screenshot is not None
    screenshot_path = Path(args.screenshot) if args.screenshot is not None else DEFAULT_SCREENSHOT_PATH

    try:
        result = run_pipeline(
            screenshot_path=args.offline if is_offline else screenshot_path,
            device=device,
            apply_taps=args.apply,
            offline=is_offline,
            random_order=args.random,
            save_screenshot=save_screenshots,
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
