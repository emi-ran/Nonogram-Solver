"""Game state detection and enumeration for autonomous play."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import cv2
import numpy as np

from src.nonogram.solver.models import Layout
from src.nonogram.vision.grid import find_line_centers, read_layout


class GameState(Enum):
    PLAYING_BOARD = auto()    # Active Nonogram puzzle board
    MAIN_MENU = auto()        # App home / main menu screen with "Level XX" and tabs
    LEVEL_COMPLETED = auto()  # "Level Completed!" screen with "Next Level" button
    POPUP_DIALOG = auto()     # Reward, claim, or event transition dialog
    UNKNOWN = auto()          # Animation, loading, or unknown screen


@dataclass
class StateDetectionResult:
    state: GameState
    layout: Layout | None = None
    rows: int = 0
    columns: int = 0
    action_coordinates: tuple[int, int] | None = None
    metadata: dict[str, Any] | None = None


class GameStateDetector:
    """Detects current screen state and interactive UI elements."""

    @staticmethod
    def detect(image: np.ndarray) -> StateDetectionResult:
        height, width = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 1. Check if an active playable Nonogram board is visible
        try:
            vertical, horizontal = find_line_centers(image)
            if vertical and horizontal:
                layout, rows, cols = read_layout(image)
                return StateDetectionResult(
                    state=GameState.PLAYING_BOARD,
                    layout=layout,
                    rows=rows,
                    columns=cols,
                )
        except Exception:
            pass

        # 2. Check for Main Menu screen:
        # - Has bottom tab bar ("Main", "Daily Challenges", "Me") with white/light background
        # - Has blue "Level XX" button in lower area (y ~ 75%-87%)
        bottom_bar = image[int(height * 0.92) : int(height * 0.98), :]
        bottom_bar_light = float(np.mean(cv2.cvtColor(bottom_bar, cv2.COLOR_BGR2GRAY) > 220)) if bottom_bar.size > 0 else 0.0

        if bottom_bar_light > 0.60:
            blue_btn_mask = cv2.inRange(hsv, np.array([100, 120, 150]), np.array([130, 255, 255]))
            crop_btn = blue_btn_mask[int(height * 0.75) : int(height * 0.87), int(width * 0.10) : int(width * 0.90)]
            coords_btn = cv2.findNonZero(crop_btn)

            if coords_btn is not None:
                bx, by, bw, bh = cv2.boundingRect(coords_btn)
                if bw > int(width * 0.45) and bh > int(height * 0.025):
                    btn_center_x = int(width * 0.10) + bx + bw // 2
                    btn_center_y = int(height * 0.75) + by + bh // 2

                    # Check if "Main" tab (bottom-left) is currently active (blue)
                    main_tab_crop = hsv[int(height * 0.91) : int(height * 0.98), int(width * 0.08) : int(width * 0.25)]
                    blue_tab_mask = cv2.inRange(main_tab_crop, np.array([100, 100, 100]), np.array([130, 255, 255]))
                    is_main_tab_active = float(np.mean(blue_tab_mask > 0)) > 0.04

                    tab_main_x = int(width * 0.165)
                    tab_main_y = int(height * 0.945)

                    return StateDetectionResult(
                        state=GameState.MAIN_MENU,
                        action_coordinates=(btn_center_x, btn_center_y) if is_main_tab_active else (tab_main_x, tab_main_y),
                        metadata={
                            "play_button": (btn_center_x, btn_center_y),
                            "main_tab_button": (tab_main_x, tab_main_y),
                            "is_main_tab_active": is_main_tab_active,
                        },
                    )

        # 3. Check for Level Completed screen (prominent white pill button near bottom center)
        # Position: y in [82%, 94%], x in [15%, 85%]
        btn_crop = image[int(height * 0.82) : int(height * 0.94), int(width * 0.15) : int(width * 0.85)]
        if btn_crop.size > 0:
            gray_btn = cv2.cvtColor(btn_crop, cv2.COLOR_BGR2GRAY)
            white_ratio = float(np.mean(gray_btn > 240))
            if white_ratio > 0.35 and bottom_bar_light < 0.40:
                # Target center of Next Level button
                target_x = int(width * 0.50)
                target_y = int(height * 0.888)
                return StateDetectionResult(
                    state=GameState.LEVEL_COMPLETED,
                    action_coordinates=(target_x, target_y),
                    metadata={"button": "Next Level"},
                )

        # 3. Check for intermediate dialogs / popups (Claim, Continue, Tap to continue, Collect)
        # Often has a bright button in the lower half (y: 65% - 85%)
        dialog_crop = image[int(height * 0.65) : int(height * 0.85), int(width * 0.20) : int(width * 0.80)]
        if dialog_crop.size > 0:
            gray_dialog = cv2.cvtColor(dialog_crop, cv2.COLOR_BGR2GRAY)
            bright_ratio = float(np.mean(gray_dialog > 230))
            if bright_ratio > 0.25:
                target_x = int(width * 0.50)
                target_y = int(height * 0.75)
                return StateDetectionResult(
                    state=GameState.POPUP_DIALOG,
                    action_coordinates=(target_x, target_y),
                    metadata={"dialog": "Continue/Claim"},
                )

        return StateDetectionResult(state=GameState.UNKNOWN)
