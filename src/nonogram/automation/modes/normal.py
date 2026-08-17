"""Normal / Classic game mode automation."""

from __future__ import annotations
import time
import numpy as np

from src.nonogram.automation.modes.base import BaseGameMode, ModeContext
from src.nonogram.automation.runner import solve_from_image
from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController


class NormalGameMode(BaseGameMode):
    """Handles standard consecutive Nonogram levels (Board -> Level Completed -> Next Level)."""

    name: str = "normal"
    description: str = "Normal Classic Game Mode"

    def handle_state(
        self,
        detection: StateDetectionResult,
        image: np.ndarray,
        device: ADBController,
        context: ModeContext,
    ) -> bool:
        if detection.state == GameState.PLAYING_BOARD:
            print(f"\n[NormalMode] Playable board detected ({detection.rows}x{detection.columns}). Solving...")
            result = solve_from_image(image)

            if not result.is_solved or result.solution is None or result.puzzle.layout is None:
                print("[NormalMode] Board could not be solved. Retrying...")
                return False

            print(f"[NormalMode] Solution found ({result.filled_count} filled cells). Tapping...")
            device.apply_solution(result.solution, result.puzzle.layout)
            context.last_solved_puzzle = result
            context.levels_completed += 1
            context.consecutive_unknowns = 0

            # Allow board completion animation to finish
            time.sleep(2.0)
            return True

        elif detection.state == GameState.MAIN_MENU:
            meta = detection.metadata or {}
            is_main_tab = meta.get("is_main_tab_active", False)
            if not is_main_tab:
                tab_x, tab_y = meta.get("main_tab_button", (int(image.shape[1] * 0.165), int(image.shape[0] * 0.945)))
                print(f"[NormalMode] Switching to 'Main' tab at ({tab_x}, {tab_y})...")
                device.tap(tab_x, tab_y)
                time.sleep(1.0)
                return True
            else:
                play_x, play_y = meta.get("play_button", (int(image.shape[1] * 0.50), int(image.shape[0] * 0.809)))
                print(f"[NormalMode] Main menu detected. Starting level at ({play_x}, {play_y})...")
                device.tap(play_x, play_y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True

        elif detection.state == GameState.LEVEL_COMPLETED:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[NormalMode] Level Completed screen detected! Tapping 'Next Level' at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(2.0)
                return True

        elif detection.state == GameState.POPUP_DIALOG:
            target = detection.action_coordinates
            if target:
                x, y = target
                print(f"[NormalMode] Reward / Dialog popup detected. Tapping continue at ({x}, {y})...")
                device.tap(x, y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)
                return True

        elif detection.state == GameState.UNKNOWN:
            context.consecutive_unknowns += 1
            if context.consecutive_unknowns > 3:
                # If stuck in unknown transition, tap middle-bottom to dismiss any overlay
                h, w = image.shape[:2]
                fallback_x, fallback_y = int(w * 0.50), int(h * 0.888)
                print(f"[NormalMode] Waiting... (attempting fallback tap at {fallback_x}, {fallback_y})")
                device.tap(fallback_x, fallback_y)
                context.consecutive_unknowns = 0
                time.sleep(1.5)

        return False
