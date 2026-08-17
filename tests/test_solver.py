"""Unit tests for the core Nonogram solver engine."""

import unittest
from src.nonogram.solver.engine import generate_patterns, solve


class TestNonogramSolverEngine(unittest.TestCase):
    def test_generate_patterns_simple(self):
        # Line of length 5 with clue (3,)
        patterns = generate_patterns(5, (3,))
        self.assertEqual(len(patterns), 3)
        self.assertIn((1, 1, 1, 0, 0), patterns)
        self.assertIn((0, 1, 1, 1, 0), patterns)
        self.assertIn((0, 0, 1, 1, 1), patterns)

    def test_generate_patterns_multiple_blocks(self):
        # Line of length 5 with clue (1, 1)
        patterns = generate_patterns(5, (1, 1))
        # Valid: (1,0,1,0,0), (1,0,0,1,0), (1,0,0,0,1), (0,1,0,1,0), (0,1,0,0,1), (0,0,1,0,1)
        self.assertEqual(len(patterns), 6)

    def test_generate_patterns_full_match(self):
        # Line of length 5 with clue (5,)
        patterns = generate_patterns(5, (5,))
        self.assertEqual(patterns, [(1, 1, 1, 1, 1)])

    def test_solve_5x5_basic(self):
        # Basic 5x5 puzzle (from Basic.png sample)
        # Rows: [(5,), (2, 2), (3,), (1,), (5,)]
        # Columns: [(2, 1), (3, 1), (1, 3), (3, 1), (2, 1)]
        row_clues = [(5,), (2, 2), (3,), (1,), (5,)]
        col_clues = [(2, 1), (3, 1), (1, 3), (3, 1), (2, 1)]

        solution = solve(row_clues, col_clues)
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), 5)
        self.assertEqual(sum(val for row in solution for val in row), 18)

    def test_solve_unsolvable(self):
        row_clues = [(5,), (5,)]
        col_clues = [(1,), (1,)]
        solution = solve(row_clues, col_clues)
        self.assertIsNone(solution)


if __name__ == "__main__":
    unittest.main()
