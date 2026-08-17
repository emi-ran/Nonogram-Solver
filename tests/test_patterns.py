"""Unit tests for tap pattern strategies."""

import unittest
from src.nonogram.automation.patterns import TapPattern, order_cells
from src.nonogram.solver.models import Layout


class TestTapPatterns(unittest.TestCase):
    def setUp(self):
        # 3x3 layout
        self.layout = Layout(width=300, height=300, first_x=50, first_y=50, step_x=100, step_y=100)
        # 3x3 solution where corners and center are filled
        # [1, 0, 1]
        # [0, 1, 0]
        # [1, 0, 1]
        self.solution = [
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
        ]

    def test_sequential_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.SEQUENTIAL)
        self.assertEqual(len(cells), 5)
        # Expected order: (0,0), (0,2), (1,1), (2,0), (2,2)
        expected = [
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        ]
        self.assertEqual(cells, expected)

    def test_reverse_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.REVERSE)
        self.assertEqual(len(cells), 5)
        # Reverse of sequential
        expected = [
            self.layout.cell_center(2, 2),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(0, 0),
        ]
        self.assertEqual(cells, expected)

    def test_ping_pong_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.PING_PONG)
        self.assertEqual(len(cells), 5)
        # First element is first, second is last, third is second, etc.
        expected = [
            self.layout.cell_center(0, 0),  # left=0
            self.layout.cell_center(2, 2),  # right=4
            self.layout.cell_center(0, 2),  # left=1
            self.layout.cell_center(2, 0),  # right=3
            self.layout.cell_center(1, 1),  # center meeting point
        ]
        self.assertEqual(cells, expected)

    def test_center_out_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.CENTER_OUT)
        self.assertEqual(len(cells), 5)
        # Center (1, 1) must be the first element
        self.assertEqual(cells[0], self.layout.cell_center(1, 1))

    def test_snake_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.SNAKE)
        self.assertEqual(len(cells), 5)
        # Row 0: left to right -> (0, 0), (0, 2)
        # Row 1: right to left -> (1, 1)
        # Row 2: left to right -> (2, 0), (2, 2)
        expected = [
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        ]
        self.assertEqual(cells, expected)

    def test_random_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.RANDOM)
        self.assertEqual(len(cells), 5)
        # All original cells must be present in the shuffled list
        expected_set = {
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        }
        self.assertEqual(set(cells), expected_set)


if __name__ == "__main__":
    unittest.main()
