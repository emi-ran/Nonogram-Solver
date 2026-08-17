"""Daily Challenge game mode automation."""

from __future__ import annotations
import time
import numpy as np

from src.nonogram.automation.modes.base import BaseGameMode, ModeContext
from src.nonogram.automation.runner import solve_from_image
from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController


class DailyChallengeMode(BaseGameMode):
    """Handles daily challenge puzzles."""

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
            print(f"\n[DailyMode] 🧩 Daily challenge board detected ({detection.rows}x{detection.columns}). Solving...")
            result = solve_from_image(image)

            if not result.is_solved or result.solution is None or result.puzzle.layout is None:
                print("[DailyMode] ⚠️ Board could not be solved. Retrying...")
                return False

            print(f"[DailyMode] ✨ Solution found ({result.filled_count} filled cells). Tapping...")
            device.apply_solution(result.solution, result.puzzle.layout)
            context.last_solved_puzzle = result
            context.levels_completed += 1
            time.sleep(2.0)
            return True

        elif detection.state == GameState.LEVEL_COMPLETED:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[DailyMode] 🏆 Daily challenge completed! Tapping continue at ({x}, {y})...")
                device.tap(x, y)
                time.sleep(2.0)
                return True

        elif detection.state == GameState.POPUP_DIALOG:
            target = detection.action_coordinates
            if target:
                device.tap(target[0], target[1])
                time.sleep(1.5)
                return True

        return False
