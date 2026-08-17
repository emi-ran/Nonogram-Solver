"""Event game modes automation (e.g. Rise & Dice, Adventure, Lilac Roses)."""

from __future__ import annotations
import time
import numpy as np

from src.nonogram.automation.modes.base import BaseGameMode, ModeContext
from src.nonogram.automation.runner import solve_from_image
from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController


class EventGameMode(BaseGameMode):
    """Handles event levels and specialized progression."""

    name: str = "event"
    description: str = "Event Mode (Rise & Dice / Adventure / Lilac Roses)"

    def handle_state(
        self,
        detection: StateDetectionResult,
        image: np.ndarray,
        device: ADBController,
        context: ModeContext,
    ) -> bool:
        if detection.state == GameState.PLAYING_BOARD:
            print(f"\n[EventMode] 🧩 Event board detected ({detection.rows}x{detection.columns}). Solving...")
            result = solve_from_image(image)

            if not result.is_solved or result.solution is None or result.puzzle.layout is None:
                print("[EventMode] ⚠️ Board could not be solved. Retrying...")
                return False

            print(f"[EventMode] ✨ Solution found ({result.filled_count} filled cells). Tapping...")
            device.apply_solution(result.solution, result.puzzle.layout)
            context.last_solved_puzzle = result
            context.levels_completed += 1
            time.sleep(2.0)
            return True

        elif detection.state == GameState.LEVEL_COMPLETED:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[EventMode] 🏆 Event level completed! Tapping next at ({x}, {y})...")
                device.tap(x, y)
                time.sleep(2.0)
                return True

        elif detection.state == GameState.POPUP_DIALOG:
            target = detection.action_coordinates
            if target:
                print(f"[EventMode] 🎁 Event reward/popup detected. Tapping at ({target[0]}, {target[1]})...")
                device.tap(target[0], target[1])
                time.sleep(1.5)
                return True

        return False
