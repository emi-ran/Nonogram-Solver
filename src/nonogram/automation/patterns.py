"""Tapping pattern strategies (Random Picker, Shuffle, BFS, DFS, Spiral, Diagonal, Checkerboard, Corners-In, Gravity, Ping-Pong, Center-Out, Reverse, Snake)."""

from __future__ import annotations
from collections import deque
import math
import random
from enum import Enum
from typing import List, Set, Tuple

from src.nonogram.solver.models import Layout, SolutionMatrix


class TapPattern(str, Enum):
    SEQUENTIAL = "sequential"       # Normal: row-by-row top-left to bottom-right
    RANDOM = "random"               # Randomly chooses any available pattern per solve
    SHUFFLE = "shuffle"             # Completely randomized shuffle of cells
    BFS = "bfs"                     # Breadth-first flood fill / ripple spread from islands
    DFS = "dfs"                     # Depth-first labyrinth crawl / ant walker
    SPIRAL = "spiral"               # Clockwise inward spiral from outer boundary to center
    DIAGONAL = "diagonal"           # 45-degree diagonal wave / slash sweep
    CHECKERBOARD = "checkerboard"   # Alternating checkerboard (light squares then dark)
    CORNERS_IN = "corners_in"       # 4 corners converging simultaneously toward center
    GRAVITY = "gravity"             # Tetris / gravity sand stacking from bottom to top
    PING_PONG = "ping_pong"         # Converges: one from top-left, one from bottom-right
    CENTER_OUT = "center_out"       # Circular / radial: starts in the center and ripples outward
    REVERSE = "reverse"             # Inverted: bottom-right to top-left
    SNAKE = "snake"                 # Zigzag: row 0 left-to-right, row 1 right-to-left...


# All concrete patterns available for random selection (excluding SEQUENTIAL and meta-RANDOM)
CONCRETE_PATTERNS: List[TapPattern] = [
    TapPattern.SHUFFLE,
    TapPattern.BFS,
    TapPattern.DFS,
    TapPattern.SPIRAL,
    TapPattern.DIAGONAL,
    TapPattern.CHECKERBOARD,
    TapPattern.CORNERS_IN,
    TapPattern.GRAVITY,
    TapPattern.PING_PONG,
    TapPattern.CENTER_OUT,
    TapPattern.REVERSE,
    TapPattern.SNAKE,
]


def _order_bfs(filled_set: Set[Tuple[int, int]], rows: int, cols: int) -> List[Tuple[int, int]]:
    """BFS flood-fill starting from the closest cell to the center of each disconnected island."""
    visited: Set[Tuple[int, int]] = set()
    result: List[Tuple[int, int]] = []
    center_r, center_c = (rows - 1) / 2.0, (cols - 1) / 2.0

    remaining = set(filled_set)
    while remaining:
        # Pick the unvisited cell closest to center as the seed for this island
        seed = min(remaining, key=lambda p: (p[0] - center_r) ** 2 + (p[1] - center_c) ** 2)
        queue = deque([seed])
        visited.add(seed)
        remaining.remove(seed)

        while queue:
            curr = queue.popleft()
            result.append(curr)
            r, c = curr
            # 4-directional neighbors
            for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
                neighbor = (nr, nc)
                if neighbor in remaining:
                    visited.add(neighbor)
                    remaining.remove(neighbor)
                    queue.append(neighbor)

    return result


def _order_dfs(filled_set: Set[Tuple[int, int]], rows: int, cols: int) -> List[Tuple[int, int]]:
    """DFS ant-walker crawling along connected filled cells."""
    visited: Set[Tuple[int, int]] = set()
    result: List[Tuple[int, int]] = []
    center_r, center_c = (rows - 1) / 2.0, (cols - 1) / 2.0

    remaining = set(filled_set)
    while remaining:
        seed = min(remaining, key=lambda p: (p[0] - center_r) ** 2 + (p[1] - center_c) ** 2)
        stack = [seed]
        visited.add(seed)
        remaining.remove(seed)

        while stack:
            curr = stack.pop()
            result.append(curr)
            r, c = curr
            # Explore neighbors in structured order
            for nr, nc in [(r - 1, c), (r, c + 1), (r + 1, c), (r, c - 1)]:
                neighbor = (nr, nc)
                if neighbor in remaining:
                    visited.add(neighbor)
                    remaining.remove(neighbor)
                    stack.append(neighbor)

    return result


def _order_spiral(filled_set: Set[Tuple[int, int]], rows: int, cols: int) -> List[Tuple[int, int]]:
    """Clockwise inward spiral from borders to center."""
    top, bottom = 0, rows - 1
    left, right = 0, cols - 1
    spiral_order: List[Tuple[int, int]] = []

    while top <= bottom and left <= right:
        # Move right along top boundary
        for c in range(left, right + 1):
            if (top, c) in filled_set:
                spiral_order.append((top, c))
        top += 1

        # Move down along right boundary
        for r in range(top, bottom + 1):
            if (r, right) in filled_set:
                spiral_order.append((r, right))
        right -= 1

        # Move left along bottom boundary
        if top <= bottom:
            for c in range(right, left - 1, -1):
                if (bottom, c) in filled_set:
                    spiral_order.append((bottom, c))
            bottom -= 1

        # Move up along left boundary
        if left <= right:
            for r in range(bottom, top - 1, -1):
                if (r, left) in filled_set:
                    spiral_order.append((r, left))
            left += 1

    return spiral_order


def _order_corners_in(filled_grid_coords: List[Tuple[int, int]], rows: int, cols: int) -> List[Tuple[int, int]]:
    """4-corner simultaneous convergence toward center."""
    c_tl = sorted(filled_grid_coords, key=lambda p: p[0]**2 + p[1]**2)
    c_tr = sorted(filled_grid_coords, key=lambda p: p[0]**2 + (cols - 1 - p[1])**2)
    c_bl = sorted(filled_grid_coords, key=lambda p: (rows - 1 - p[0])**2 + p[1]**2)
    c_br = sorted(filled_grid_coords, key=lambda p: (rows - 1 - p[0])**2 + (cols - 1 - p[1])**2)

    queues = [deque(c_tl), deque(c_tr), deque(c_bl), deque(c_br)]
    visited: Set[Tuple[int, int]] = set()
    result: List[Tuple[int, int]] = []

    total = len(filled_grid_coords)
    idx = 0
    while len(result) < total:
        q = queues[idx % 4]
        idx += 1
        while q:
            cell = q.popleft()
            if cell not in visited:
                visited.add(cell)
                result.append(cell)
                break

    return result


def resolve_pattern(pattern: TapPattern | str = TapPattern.SEQUENTIAL) -> TapPattern:
    """Resolve pattern input into a concrete TapPattern (resolving RANDOM to a concrete choice)."""
    if isinstance(pattern, str):
        pat_str = pattern.lower().strip()
        try:
            pattern = TapPattern(pat_str)
        except ValueError:
            if pat_str in ("rand", "random"):
                pattern = TapPattern.RANDOM
            elif pat_str == "shuffle":
                pattern = TapPattern.SHUFFLE
            else:
                pattern = TapPattern.SEQUENTIAL

    if pattern == TapPattern.RANDOM:
        return random.choice(CONCRETE_PATTERNS)
    return pattern


def order_cells(
    solution: SolutionMatrix,
    layout: Layout,
    pattern: TapPattern | str = TapPattern.SEQUENTIAL,
) -> List[Tuple[int, int]]:
    """Convert a 2D solution matrix into an ordered list of screen (x, y) coordinates based on pattern."""
    concrete_pattern = resolve_pattern(pattern)

    rows = len(solution)
    cols = len(solution[0]) if rows > 0 else 0

    # Collect all (row, col) coordinates of filled cells
    filled_grid_coords: List[Tuple[int, int]] = [
        (r, c) for r in range(rows) for c in range(cols) if solution[r][c]
    ]

    if not filled_grid_coords:
        return []

    filled_set = set(filled_grid_coords)

    # Apply selected pattern ordering
    if concrete_pattern == TapPattern.SHUFFLE:
        ordered_rc = list(filled_grid_coords)
        random.shuffle(ordered_rc)

    elif concrete_pattern == TapPattern.BFS:
        ordered_rc = _order_bfs(filled_set, rows, cols)

    elif concrete_pattern == TapPattern.DFS:
        ordered_rc = _order_dfs(filled_set, rows, cols)

    elif concrete_pattern == TapPattern.SPIRAL:
        ordered_rc = _order_spiral(filled_set, rows, cols)

    elif concrete_pattern == TapPattern.DIAGONAL:
        # Sort by diagonal index (r + c), then by column
        ordered_rc = sorted(filled_grid_coords, key=lambda p: (p[0] + p[1], p[1]))

    elif concrete_pattern == TapPattern.CHECKERBOARD:
        # First light cells ((r+c)%2 == 0), then dark cells ((r+c)%2 == 1)
        light = [p for p in filled_grid_coords if (p[0] + p[1]) % 2 == 0]
        dark = [p for p in filled_grid_coords if (p[0] + p[1]) % 2 != 0]
        ordered_rc = light + dark

    elif concrete_pattern == TapPattern.CORNERS_IN:
        ordered_rc = _order_corners_in(filled_grid_coords, rows, cols)

    elif concrete_pattern == TapPattern.GRAVITY:
        # Bottom-up stacking (highest row index first, left-to-right)
        ordered_rc = sorted(filled_grid_coords, key=lambda p: (-p[0], p[1]))

    elif concrete_pattern == TapPattern.PING_PONG:
        ordered_rc = []
        left, right = 0, len(filled_grid_coords) - 1
        while left <= right:
            ordered_rc.append(filled_grid_coords[left])
            if left != right:
                ordered_rc.append(filled_grid_coords[right])
            left += 1
            right -= 1

    elif concrete_pattern == TapPattern.CENTER_OUT:
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

    elif concrete_pattern == TapPattern.REVERSE:
        ordered_rc = list(reversed(filled_grid_coords))

    elif concrete_pattern == TapPattern.SNAKE:
        ordered_rc = sorted(
            filled_grid_coords,
            key=lambda p: (p[0], p[1] if p[0] % 2 == 0 else -p[1]),
        )

    else:  # SEQUENTIAL
        ordered_rc = filled_grid_coords

    # Map (row, col) to screen pixel (x, y)
    return [layout.cell_center(r, c) for r, c in ordered_rc]


