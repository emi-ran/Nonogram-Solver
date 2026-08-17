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
    PLAYING_BOARD = auto()         # Active Nonogram puzzle board
    MAIN_MENU = auto()             # App home / main menu screen with "Level XX" and tabs
    EVENT_MENU = auto()            # Event book/map menu (e.g. Lilac Roses, Adventure)
    LEVEL_COMPLETED = auto()       # "Level Completed!" screen with "Next Level" button
    DAILY_RESTART_DIALOG = auto()  # "Restart Level / Cancel" modal when all daily challenges are finished
    POPUP_DIALOG = auto()          # Reward, claim, or event transition dialog
    UNKNOWN = auto()               # Animation, loading, or unknown screen


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
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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

        # 2. Check for "Restart Level / Cancel" modal card (Daily challenges all completed)
        # White bottom card covering play button with dimmed background overlay
        top_brightness = float(np.mean(gray[int(height * 0.20) : int(height * 0.50), :]))
        card_crop = gray[int(height * 0.83) : int(height * 0.97), int(width * 0.05) : int(width * 0.95)]
        blue_pill = cv2.inRange(
            hsv[int(height * 0.80) : int(height * 0.88), int(width * 0.15) : int(width * 0.85)],
            np.array([100, 120, 150]),
            np.array([130, 255, 255]),
        )
        blue_pill_ratio = float(np.mean(blue_pill > 0)) if blue_pill.size > 0 else 0.0

        if card_crop.size > 0:
            white_ratio = float(np.mean(card_crop > 245))
            if top_brightness < 110 and white_ratio > 0.80 and blue_pill_ratio < 0.10:
                cancel_x = int(width * 0.50)
                cancel_y = int(height * 0.93)
                restart_x = int(width * 0.50)
                restart_y = int(height * 0.87)
                return StateDetectionResult(
                    state=GameState.DAILY_RESTART_DIALOG,
                    action_coordinates=(cancel_x, cancel_y),
                    metadata={
                        "cancel": (cancel_x, cancel_y),
                        "restart": (restart_x, restart_y),
                    },
                )

        # 3. Check for Level Completed screen (prominent white pill button near bottom center)
        # Position: y in [82%, 94%], x in [15%, 85%]
        bottom_bar = image[int(height * 0.92) : int(height * 0.98), :]
        bottom_bar_light = float(np.mean(cv2.cvtColor(bottom_bar, cv2.COLOR_BGR2GRAY) > 220)) if bottom_bar.size > 0 else 0.0

        center_crop = hsv[int(height * 0.30) : int(height * 0.70), int(width * 0.15) : int(width * 0.85)]
        beige_mask = cv2.inRange(center_crop, np.array([12, 15, 160]), np.array([35, 110, 255]))
        beige_ratio = float(np.mean(beige_mask > 0)) if center_crop.size > 0 else 0.0

        btn_crop = image[int(height * 0.82) : int(height * 0.94), int(width * 0.15) : int(width * 0.85)]
        if btn_crop.size > 0:
            gray_btn = cv2.cvtColor(btn_crop, cv2.COLOR_BGR2GRAY)
            white_ratio = float(np.mean(gray_btn > 240))
            if white_ratio > 0.35 and bottom_bar_light < 0.40 and beige_ratio < 0.30:
                # Target center of Next Level / Continue button
                target_x = int(width * 0.50)
                target_y = int(height * 0.888)
                return StateDetectionResult(
                    state=GameState.LEVEL_COMPLETED,
                    action_coordinates=(target_x, target_y),
                    metadata={"button": "Next Level/Continue"},
                )

        # 4. Check for Event Menu (e.g. Lilac Roses warm orange storybook map with beige book pages)
        orange_mask = cv2.inRange(hsv, np.array([5, 120, 120]), np.array([28, 255, 255]))
        orange_ratio = float(np.mean(orange_mask > 0))
        if orange_ratio > 0.20 and beige_ratio > 0.30:
            event_btn_crop = gray[int(height * 0.80) : int(height * 0.90), int(width * 0.10) : int(width * 0.90)]
            event_white_ratio = float(np.mean(event_btn_crop > 240)) if event_btn_crop.size > 0 else 0.0
            event_gray_ratio = (
                float(np.mean((event_btn_crop > 200) & (event_btn_crop <= 240))) if event_btn_crop.size > 0 else 0.0
            )

            if event_white_ratio > 0.25 or event_gray_ratio > 0.25:
                ready = event_white_ratio > 0.25
                cx = int(width * 0.50)
                cy = int(height * 0.845)
                return StateDetectionResult(
                    state=GameState.EVENT_MENU,
                    action_coordinates=(cx, cy) if ready else None,
                    metadata={
                        "ready": ready,
                        "play_button": (cx, cy),
                        "event": "lilac_roses",
                    },
                )

        # 5. Check for Main Menu screen:
        # - Has bottom tab bar ("Main", "Daily Challenges", "Me") with white/light background
        # - Has blue "Level XX" button in lower area (y ~ 75%-87%)
        if bottom_bar_light > 0.60:
            blue_btn_mask = cv2.inRange(hsv, np.array([100, 120, 150]), np.array([130, 255, 255]))
            crop_btn = blue_btn_mask[int(height * 0.75) : int(height * 0.87), int(width * 0.10) : int(width * 0.90)]
            coords_btn = cv2.findNonZero(crop_btn)

            if coords_btn is not None:
                bx, by, bw, bh = cv2.boundingRect(coords_btn)
                if bw > int(width * 0.45) and bh > int(height * 0.025):
                    btn_center_x = int(width * 0.10) + bx + bw // 2
                    btn_center_y = int(height * 0.75) + by + bh // 2

                    # Check which tab in bottom navigation is currently active (blue)
                    main_tab_crop = hsv[int(height * 0.91) : int(height * 0.98), int(width * 0.08) : int(width * 0.25)]
                    blue_main_mask = cv2.inRange(main_tab_crop, np.array([100, 100, 100]), np.array([130, 255, 255]))
                    is_main_tab_active = float(np.mean(blue_main_mask > 0)) > 0.04

                    daily_tab_crop = hsv[int(height * 0.91) : int(height * 0.98), int(width * 0.40) : int(width * 0.60)]
                    blue_daily_mask = cv2.inRange(daily_tab_crop, np.array([100, 100, 100]), np.array([130, 255, 255]))
                    is_daily_tab_active = float(np.mean(blue_daily_mask > 0)) > 0.04

                    tab_main_x = int(width * 0.165)
                    tab_main_y = int(height * 0.945)

                    return StateDetectionResult(
                        state=GameState.MAIN_MENU,
                        action_coordinates=(btn_center_x, btn_center_y) if is_main_tab_active else (tab_main_x, tab_main_y),
                        metadata={
                            "play_button": (btn_center_x, btn_center_y),
                            "main_tab_button": (tab_main_x, tab_main_y),
                            "is_main_tab_active": is_main_tab_active,
                            "is_daily_tab_active": is_daily_tab_active,
                        },
                    )

        # 6. Check for intermediate dialogs / popups (Claim, Continue, Tap to continue, Collect)
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
