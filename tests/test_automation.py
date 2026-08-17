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

    def test_state_detection_daily_flow(self):
        # 1. after_first.png -> LEVEL_COMPLETED with Continue button
        first_path = SAMPLES_DIR / "after_first.png"
        if not first_path.exists():
            first_path = Path("after_first.png")
        self.assertTrue(first_path.exists())
        img1 = cv2.imread(str(first_path))
        det1 = GameStateDetector.detect(img1)
        self.assertEqual(det1.state, GameState.LEVEL_COMPLETED)
        self.assertEqual(det1.action_coordinates, (640, 2461))

        # 2. after_second.png -> MAIN_MENU / Calendar with daily tab active and Play button
        sec_path = SAMPLES_DIR / "after_second.png"
        if not sec_path.exists():
            sec_path = Path("after_second.png")
        self.assertTrue(sec_path.exists())
        img2 = cv2.imread(str(sec_path))
        det2 = GameStateDetector.detect(img2)
        self.assertEqual(det2.state, GameState.MAIN_MENU)
        self.assertIsNotNone(det2.metadata)
        self.assertTrue(det2.metadata["is_daily_tab_active"])
        self.assertEqual(det2.metadata["play_button"][0], 640)
        self.assertGreater(det2.metadata["play_button"][1], 2200)

        # 3. yes_finished.png -> DAILY_RESTART_DIALOG with Cancel button
        fin_path = SAMPLES_DIR / "yes_finished.png"
        if not fin_path.exists():
            fin_path = Path("yes_finished.png")
        self.assertTrue(fin_path.exists())
        img3 = cv2.imread(str(fin_path))
        det3 = GameStateDetector.detect(img3)
        self.assertEqual(det3.state, GameState.DAILY_RESTART_DIALOG)
        self.assertIsNotNone(det3.action_coordinates)
        self.assertEqual(det3.action_coordinates[0], 640)
        self.assertGreater(det3.action_coordinates[1], 2500)

    def test_state_detection_lilac_event(self):
        # 1. lilac_menu.png -> EVENT_MENU ready
        p1 = SAMPLES_DIR / "lilac_menu.png"
        if not p1.exists():
            p1 = Path("lilac_menu.png")
        self.assertTrue(p1.exists())
        det1 = GameStateDetector.detect(cv2.imread(str(p1)))
        self.assertEqual(det1.state, GameState.EVENT_MENU)
        self.assertIsNotNone(det1.metadata)
        self.assertTrue(det1.metadata["ready"])
        self.assertIsNotNone(det1.action_coordinates)
        self.assertEqual(det1.action_coordinates[0], 640)
        self.assertGreater(det1.action_coordinates[1], 2300)

        # 2. lilac_menu_leve_completed.png -> EVENT_MENU not ready (animation running)
        p2 = SAMPLES_DIR / "lilac_menu_leve_completed.png"
        if not p2.exists():
            p2 = Path("lilac_menu_leve_completed.png")
        self.assertTrue(p2.exists())
        det2 = GameStateDetector.detect(cv2.imread(str(p2)))
        self.assertEqual(det2.state, GameState.EVENT_MENU)
        self.assertIsNotNone(det2.metadata)
        self.assertFalse(det2.metadata["ready"])
        self.assertIsNone(det2.action_coordinates)

        # 3. after_lilac_menu_leve_completed.png -> EVENT_MENU ready again
        p3 = SAMPLES_DIR / "after_lilac_menu_leve_completed.png"
        if not p3.exists():
            p3 = Path("after_lilac_menu_leve_completed.png")
        self.assertTrue(p3.exists())
        det3 = GameStateDetector.detect(cv2.imread(str(p3)))
        self.assertEqual(det3.state, GameState.EVENT_MENU)
        self.assertIsNotNone(det3.metadata)
        self.assertTrue(det3.metadata["ready"])
        self.assertIsNotNone(det3.action_coordinates)
        self.assertEqual(det3.action_coordinates[0], 640)
        self.assertGreater(det3.action_coordinates[1], 2300)

        # 4. event_level_completed.png -> LEVEL_COMPLETED with Continue button
        p4 = SAMPLES_DIR / "event_level_completed.png"
        if not p4.exists():
            p4 = Path("event_level_completed.png")
        self.assertTrue(p4.exists())
        det4 = GameStateDetector.detect(cv2.imread(str(p4)))
        self.assertEqual(det4.state, GameState.LEVEL_COMPLETED)
        self.assertIsNotNone(det4.action_coordinates)
        self.assertEqual(det4.action_coordinates[0], 640)
        self.assertGreater(det4.action_coordinates[1], 2400)

    def test_get_game_mode_registry(self):
        normal_mode = get_game_mode("normal")
        self.assertIsInstance(normal_mode, NormalGameMode)

        daily_mode = get_game_mode("daily")
        self.assertIsInstance(daily_mode, DailyChallengeMode)

        event_mode = get_game_mode("event")
        self.assertIsInstance(event_mode, EventGameMode)

        lilac_mode = get_game_mode("lilac")
        self.assertIsInstance(lilac_mode, EventGameMode)

        lilac_roses_mode = get_game_mode("lilac_roses")
        self.assertIsInstance(lilac_roses_mode, EventGameMode)

        adv_mode = get_game_mode("adventure")
        self.assertIsInstance(adv_mode, EventGameMode)


if __name__ == "__main__":
    unittest.main()
