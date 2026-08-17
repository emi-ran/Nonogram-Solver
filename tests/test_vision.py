"""Tests for vision and OCR against sample screenshots."""

import unittest
from pathlib import Path

from src.nonogram.automation.runner import solve_from_image
from src.nonogram.config import SAMPLES_DIR


class TestNonogramVision(unittest.TestCase):
    def test_basic_sample(self):
        sample_path = SAMPLES_DIR / "Basic.png"
        self.assertTrue(sample_path.exists(), f"Missing sample file: {sample_path}")
        result = solve_from_image(sample_path)

        self.assertTrue(result.is_solved)
        self.assertEqual(result.puzzle.rows, 5)
        self.assertEqual(result.puzzle.columns, 5)
        self.assertEqual(result.filled_count, 18)

    def test_medium_sample(self):
        sample_path = SAMPLES_DIR / "Medium.png"
        self.assertTrue(sample_path.exists(), f"Missing sample file: {sample_path}")
        result = solve_from_image(sample_path)

        self.assertTrue(result.is_solved)
        self.assertEqual(result.puzzle.rows, 10)
        self.assertEqual(result.puzzle.columns, 10)
        self.assertEqual(result.filled_count, 52)

    def test_hard_sample(self):
        sample_path = SAMPLES_DIR / "Hard.png"
        self.assertTrue(sample_path.exists(), f"Missing sample file: {sample_path}")
        result = solve_from_image(sample_path)

        self.assertTrue(result.is_solved)
        self.assertEqual(result.puzzle.rows, 15)
        self.assertEqual(result.puzzle.columns, 15)
        self.assertEqual(result.filled_count, 126)

    def test_error_sample(self):
        sample_path = SAMPLES_DIR / "error.png"
        if not sample_path.exists():
            sample_path = Path("error.png")
        if sample_path.exists():
            result = solve_from_image(sample_path)
            self.assertTrue(result.is_solved)
            self.assertEqual(result.puzzle.rows, 5)
            self.assertEqual(result.puzzle.columns, 5)
            self.assertEqual(result.filled_count, 14)

    def test_extreme_sample(self):
        sample_path = SAMPLES_DIR / "extreme.png"
        if not sample_path.exists():
            sample_path = Path("extreme.png")
        self.assertTrue(sample_path.exists(), f"Missing sample file: {sample_path}")
        result = solve_from_image(sample_path)

        self.assertTrue(result.is_solved)
        self.assertEqual(result.puzzle.rows, 20)
        self.assertEqual(result.puzzle.columns, 20)
        self.assertEqual(result.filled_count, 201)


if __name__ == "__main__":
    unittest.main()
