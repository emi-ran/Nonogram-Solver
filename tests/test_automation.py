"""Unit and integration tests for state machine and autonomous play modes."""

import unittest
import cv2
from pathlib import Path

from src.nonogram.automation.modes import get_game_mode, NormalGameMode, DailyChallengeMode, EventGameMode
from src.nonogram.automation.states import GameState, GameStateDetector
from src.nonogram.config import SAMPLES_DIR


class TestAutomationStateMachine(unittest.TestCase):
    def test_state_detection_playing_board(self):
        sample_path = SAMPLES_DIR / "Medium.png"
        image = cv2.imread(str(sample_path))
        self.assertIsNotNone(image)

        detection = GameStateDetector.detect(image)
        self.assertEqual(detection.state, GameState.PLAYING_BOARD)
        self.assertEqual(detection.rows, 10)
        self.assertEqual(detection.columns, 10)

    def test_state_detection_level_completed(self):
        sample_path = SAMPLES_DIR / "completed.png"
        if not sample_path.exists():
            sample_path = Path("completed.png")
        self.assertTrue(sample_path.exists())

        image = cv2.imread(str(sample_path))
        detection = GameStateDetector.detect(image)
        self.assertEqual(detection.state, GameState.LEVEL_COMPLETED)
        self.assertIsNotNone(detection.action_coordinates)
        x, y = detection.action_coordinates
        # Center of screen for 1280x2772 screen is x=640, y~2461
        self.assertEqual(x, 640)
        self.assertGreater(y, 2000)

    def test_state_detection_main_menu(self):
        sample_path = SAMPLES_DIR / "main_menu.png"
        if not sample_path.exists():
            sample_path = Path("main_menu.png")
        self.assertTrue(sample_path.exists())

        image = cv2.imread(str(sample_path))
        detection = GameStateDetector.detect(image)
        self.assertEqual(detection.state, GameState.MAIN_MENU)
        self.assertIsNotNone(detection.metadata)
        self.assertTrue(detection.metadata["is_main_tab_active"])
        self.assertEqual(detection.action_coordinates, (640, 2243))

    def test_get_game_mode_registry(self):
        normal_mode = get_game_mode("normal")
        self.assertIsInstance(normal_mode, NormalGameMode)

        daily_mode = get_game_mode("daily")
        self.assertIsInstance(daily_mode, DailyChallengeMode)

        event_mode = get_game_mode("event")
        self.assertIsInstance(event_mode, EventGameMode)

        adv_mode = get_game_mode("adventure")
        self.assertIsInstance(adv_mode, EventGameMode)


if __name__ == "__main__":
    unittest.main()
