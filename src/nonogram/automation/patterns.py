"""Tapping pattern strategies (Random, Ping-Pong, Center-Out, Reverse, Snake)."""

from __future__ import annotations
import math
import random
from enum import Enum
from typing import List, Tuple

from src.nonogram.solver.models import Layout, SolutionMatrix


class TapPattern(str, Enum):
    SEQUENTIAL = "sequential"   # Normal: row-by-row top-left to bottom-right
    RANDOM = "random"           # Completely randomized shuffle
    PING_PONG = "ping_pong"     # Converges: one from top-left, one from bottom-right, meeting in center
    CENTER_OUT = "center_out"   # Circular / radial: starts in the center and ripples outward
    REVERSE = "reverse"         # Inverted: bottom-right to top-left
    SNAKE = "snake"             # Zigzag: row 0 left-to-right, row 1 right-to-left...


def order_cells(
    solution: SolutionMatrix,
    layout: Layout,
    pattern: TapPattern | str = TapPattern.SEQUENTIAL,
) -> List[Tuple[int, int]]:
    """Convert a 2D solution matrix into an ordered list of screen (x, y) coordinates based on pattern."""
    if isinstance(pattern, str):
        try:
            pattern = TapPattern(pattern.lower().strip())
        except ValueError:
            pattern = TapPattern.RANDOM if "rand" in pattern.lower() else TapPattern.SEQUENTIAL

    rows = len(solution)
    cols = len(solution[0]) if rows > 0 else 0

    # Collect all (row, col) coordinates of filled cells
    filled_grid_coords: List[Tuple[int, int]] = [
        (r, c) for r in range(rows) for c in range(cols) if solution[r][c]
    ]

    if not filled_grid_coords:
        return []

    # 1. Apply pattern ordering to (r, c)
    if pattern == TapPattern.RANDOM:
        ordered_rc = list(filled_grid_coords)
        random.shuffle(ordered_rc)

    elif pattern == TapPattern.PING_PONG:
        ordered_rc = []
        left, right = 0, len(filled_grid_coords) - 1
        while left <= right:
            ordered_rc.append(filled_grid_coords[left])
            if left != right:
                ordered_rc.append(filled_grid_coords[right])
            left += 1
            right -= 1

    elif pattern == TapPattern.CENTER_OUT:
        center_r = (rows - 1) / 2.0
        center_c = (cols - 1) / 2.0
        # Sort by Euclidean distance from center, with angle tiebreaker
        ordered_rc = sorted(
            filled_grid_coords,
            key=lambda p: (
                math.dist((p[0], p[1]), (center_r, center_c)),
                math.atan2(p[0] - center_r, p[1] - center_c),
            ),
        )

    elif pattern == TapPattern.REVERSE:
        ordered_rc = list(reversed(filled_grid_coords))

    elif pattern == TapPattern.SNAKE:
        ordered_rc = sorted(
            filled_grid_coords,
            key=lambda p: (p[0], p[1] if p[0] % 2 == 0 else -p[1]),
        )

    else:  # SEQUENTIAL
        ordered_rc = filled_grid_coords

    # 2. Map (row, col) to screen pixel (x, y)
    return [layout.cell_center(r, c) for r, c in ordered_rc]
