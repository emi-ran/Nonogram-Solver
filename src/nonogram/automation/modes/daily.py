"""Daily Challenge game mode automation."""

from __future__ import annotations
import time
import numpy as np

from src.nonogram.automation.modes.base import BaseGameMode, ModeContext
from src.nonogram.automation.runner import solve_from_image
from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController


class DailyChallengeMode(BaseGameMode):
    """Handles continuous Daily Challenge puzzles."""

    name: str = "daily"
    description: str = "Daily Challenge Mode"

    def handle_state(
        self,
        detection: StateDetectionResult,
        image: np.ndarray,
        device: ADBController,
        context: ModeContext,
    ) -> bool:
        if detection.state == GameState.PLAYING_BOARD:
            print(f"\n[DailyMode] Daily challenge board detected ({detection.rows}x{detection.columns}). Solving...")
            result = solve_from_image(image)

            if not result.is_solved or result.solution is None or result.puzzle.layout is None:
                print("[DailyMode] Board could not be solved. Retrying...")
                return False

            print(f"[DailyMode] Solution found ({result.filled_count} filled cells). Tapping ({context.pattern})...")
            device.apply_solution(result.solution, result.puzzle.layout, pattern=context.pattern)
            context.last_solved_puzzle = result
            context.levels_completed += 1
            context.consecutive_unknowns = 0
            time.sleep(2.0)
            return True

        elif detection.state == GameState.LEVEL_COMPLETED:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[DailyMode] Challenge completed! Tapping 'Continue' at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True

        elif detection.state == GameState.DAILY_RESTART_DIALOG:
            cancel_coords = detection.action_coordinates
            if cancel_coords:
                x, y = cancel_coords
                print(f"[DailyMode] Restart Level dialog detected. Tapping 'Cancel' at ({x}, {y})...")
                device.tap(x, y)
            print("\n[DailyMode] Daily bitti! (All available Daily Challenges completed).")
            context.is_finished = True
            context.consecutive_unknowns = 0
            time.sleep(1.0)
            return True

        elif detection.state == GameState.MAIN_MENU:
            meta = detection.metadata or {}
            play_coords = meta.get("play_button")
            if play_coords:
                x, y = play_coords
                print(f"[DailyMode] Daily Challenges calendar detected. Tapping 'Play' at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True

        elif detection.state == GameState.POPUP_DIALOG:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[DailyMode] Reward / Dialog popup detected. Tapping at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)
                return True

        elif detection.state == GameState.UNKNOWN:
            context.consecutive_unknowns += 1
            if context.consecutive_unknowns > 3:
                h, w = image.shape[:2]
                fallback_x, fallback_y = int(w * 0.50), int(h * 0.888)
                print(f"[DailyMode] Waiting... (attempting fallback tap at {fallback_x}, {fallback_y})")
                device.tap(fallback_x, fallback_y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)

        return False
