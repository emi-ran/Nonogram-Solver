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
        expected_set = {
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        }
        self.assertEqual(set(cells), expected_set)

    def test_shuffle_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.SHUFFLE)
        self.assertEqual(len(cells), 5)
        expected_set = {
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        }
        self.assertEqual(set(cells), expected_set)

    def test_bfs_pattern(self):
        # 3x3 with connected cross shape
        # [0, 1, 0]
        # [1, 1, 1]
        # [0, 1, 0]
        solution_cross = [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ]
        cells = order_cells(solution_cross, self.layout, pattern=TapPattern.BFS)
        self.assertEqual(len(cells), 5)
        # Center (1, 1) should be the first seed since it is closest to center
        self.assertEqual(cells[0], self.layout.cell_center(1, 1))

    def test_dfs_pattern(self):
        solution_cross = [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ]
        cells = order_cells(solution_cross, self.layout, pattern=TapPattern.DFS)
        self.assertEqual(len(cells), 5)
        self.assertEqual(cells[0], self.layout.cell_center(1, 1))

    def test_spiral_pattern(self):
        # Full 3x3 grid
        full_solution = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        cells = order_cells(full_solution, self.layout, pattern=TapPattern.SPIRAL)
        self.assertEqual(len(cells), 9)
        # Top row: (0,0), (0,1), (0,2)
        # Right col: (1,2), (2,2)
        # Bottom row: (2,1), (2,0)
        # Left col: (1,0)
        # Center: (1,1)
        expected = [
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 1),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(1, 2),
            self.layout.cell_center(2, 2),
            self.layout.cell_center(2, 1),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(1, 0),
            self.layout.cell_center(1, 1),
        ]
        self.assertEqual(cells, expected)

    def test_diagonal_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.DIAGONAL)
        self.assertEqual(len(cells), 5)
        # Diagonals (r+c):
        # (0,0) -> sum 0
        # (0,2) & (2,0) & (1,1) -> sum 2
        # (2,2) -> sum 4
        self.assertEqual(cells[0], self.layout.cell_center(0, 0))
        self.assertEqual(cells[-1], self.layout.cell_center(2, 2))

    def test_checkerboard_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.CHECKERBOARD)
        self.assertEqual(len(cells), 5)
        # In our solution, all 5 filled cells ((0,0),(0,2),(1,1),(2,0),(2,2)) have (r+c)%2 == 0
        # Let's test with a solution having both
        mixed_solution = [
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        mixed_cells = order_cells(mixed_solution, self.layout, pattern=TapPattern.CHECKERBOARD)
        # (0, 0) has sum 0 (light), (0, 1) has sum 1 (dark)
        self.assertEqual(mixed_cells[0], self.layout.cell_center(0, 0))
        self.assertEqual(mixed_cells[1], self.layout.cell_center(0, 1))

    def test_corners_in_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.CORNERS_IN)
        self.assertEqual(len(cells), 5)
        # The 4 corners should come first, center last
        corners_set = {
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
        }
        self.assertEqual(set(cells[:4]), corners_set)
        self.assertEqual(cells[4], self.layout.cell_center(1, 1))

    def test_gravity_pattern(self):
        cells = order_cells(self.solution, self.layout, pattern=TapPattern.GRAVITY)
        self.assertEqual(len(cells), 5)
        # Row 2 comes first ((2,0), (2,2)), then Row 1 ((1,1)), then Row 0 ((0,0), (0,2))
        expected = [
            self.layout.cell_center(2, 0),
            self.layout.cell_center(2, 2),
            self.layout.cell_center(1, 1),
            self.layout.cell_center(0, 0),
            self.layout.cell_center(0, 2),
        ]
        self.assertEqual(cells, expected)


if __name__ == "__main__":
    unittest.main()

