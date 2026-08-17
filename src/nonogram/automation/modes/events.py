"""Event game modes automation (e.g. Lilac Roses, Rise & Dice, Adventure)."""

from __future__ import annotations
import time
import numpy as np

from src.nonogram.automation.modes.base import BaseGameMode, ModeContext
from src.nonogram.automation.runner import solve_from_image
from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController


class EventGameMode(BaseGameMode):
    """Handles event levels and specialized progression (Lilac Roses, Rise & Dice, Adventure)."""

    name: str = "event"
    description: str = "Event Mode (Lilac Roses / Rise & Dice / Adventure)"

    def handle_state(
        self,
        detection: StateDetectionResult,
        image: np.ndarray,
        device: ADBController,
        context: ModeContext,
    ) -> bool:
        if detection.state == GameState.PLAYING_BOARD:
            print(f"\n[EventMode] Event board detected ({detection.rows}x{detection.columns}). Solving...")
            result = solve_from_image(image)

            if not result.is_solved or result.solution is None or result.puzzle.layout is None:
                print("[EventMode] Board could not be solved. Retrying...")
                return False

            print(f"[EventMode] Solution found ({result.filled_count} filled cells). Tapping ({context.pattern})...")
            device.apply_solution(result.solution, result.puzzle.layout, pattern=context.pattern)
            context.last_solved_puzzle = result
            context.levels_completed += 1
            context.consecutive_unknowns = 0
            time.sleep(2.0)
            return True

        elif detection.state == GameState.EVENT_MENU:
            meta = detection.metadata or {}
            is_ready = meta.get("ready", False)
            play_coords = meta.get("play_button", (int(image.shape[1] * 0.50), int(image.shape[0] * 0.845)))

            if is_ready:
                x, y = play_coords
                print(f"[EventMode] Event map detected. Starting level by tapping 'Play' at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True
            else:
                print("[EventMode] Waiting for level completion animation to finish in event menu...")
                context.consecutive_unknowns = 0
                time.sleep(1.5)
                return True

        elif detection.state == GameState.LEVEL_COMPLETED:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[EventMode] Event level completed! Tapping next/continue at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True

        elif detection.state == GameState.POPUP_DIALOG:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[EventMode] Event reward/dialog detected. Tapping at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)
                return True

        elif detection.state == GameState.UNKNOWN:
            context.consecutive_unknowns += 1
            if context.consecutive_unknowns > 3:
                h, w = image.shape[:2]
                fallback_x, fallback_y = int(w * 0.50), int(h * 0.845)
                print(f"[EventMode] Waiting... (attempting fallback tap at {fallback_x}, {fallback_y})")
                device.tap(fallback_x, fallback_y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)

        return False
