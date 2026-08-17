"""Pipeline runner for Nonogram detection and solving."""

from __future__ import annotations
from pathlib import Path

import numpy as np

from src.nonogram.device.adb import ADBController
from src.nonogram.solver.engine import solve
from src.nonogram.solver.models import NonogramPuzzle, SolveResult
from src.nonogram.vision.grid import read_layout
from src.nonogram.vision.ocr import read_clues


def solve_from_image(image_or_path: np.ndarray | Path | str) -> SolveResult:
    """Analyze an image (in-memory or from file), extract clues, and calculate the solution."""
    layout, rows, columns = read_layout(image_or_path)
    row_clues, column_clues = read_clues(image_or_path, layout, rows, columns)

    puzzle = NonogramPuzzle(
        rows=rows,
        columns=columns,
        row_clues=row_clues,
        column_clues=column_clues,
        layout=layout,
    )

    solution = solve(row_clues, column_clues)
    filled_count = (
        sum(val for row in solution for val in row) if solution is not None else 0
    )

    return SolveResult(
        puzzle=puzzle,
        solution=solution,
        filled_count=filled_count,
    )


def run_pipeline(
    screenshot_path: Path | str | None = None,
    device: ADBController | None = None,
    apply_taps: bool = False,
    offline: bool = False,
    save_screenshot: bool = False,
) -> SolveResult:
    """Execute the end-to-end solve workflow with zero disk I/O by default when online."""
    if offline:
        if screenshot_path is None:
            raise ValueError("In offline mode, a screenshot path must be provided.")
        image_source: np.ndarray | Path | str = Path(screenshot_path)
    else:
        if device is None:
            device = ADBController()

        if save_screenshot and screenshot_path is not None:
            device.capture_screenshot(screenshot_path)
            image_source = Path(screenshot_path)
        else:
            # Capture directly into memory (RAM), skipping disk writes
            image_source = device.capture_image()

    result = solve_from_image(image_source)

    if not result.is_solved:
        raise RuntimeError("Recognized Nonogram has no valid solution.")

    if apply_taps and not offline:
        if device is None:
            device = ADBController()
        if result.puzzle.layout and result.solution:
            device.apply_solution(result.solution, result.puzzle.layout)

    return result
