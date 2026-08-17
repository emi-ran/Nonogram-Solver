"""Pipeline runner for Nonogram detection and solving."""

from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np

from src.nonogram.config import DEFAULT_SCREENSHOT_PATH
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
    random_order: bool = False,
    save_screenshot: bool = False,
    auto_save_error: bool = True,
) -> SolveResult:
    """Execute the end-to-end solve workflow with zero disk I/O by default when online,

    or saving to disk when explicitly requested or when an error occurs.
    """
    raw_image: np.ndarray | None = None

    if offline:
        if screenshot_path is None:
            raise ValueError("In offline mode, a screenshot path must be provided.")
        path = Path(screenshot_path)
        if not path.suffix:
            path = path.with_suffix(".png")
        if not path.exists():
            raise FileNotFoundError(f"Offline screenshot not found: {path}")
        image_source: np.ndarray | Path = path
    else:
        if device is None:
            device = ADBController()

        raw_image = device.capture_image()
        image_source = raw_image

        if screenshot_path is not None or save_screenshot:
            target_path = Path(
                screenshot_path if screenshot_path is not None else DEFAULT_SCREENSHOT_PATH
            )
            if not target_path.suffix:
                target_path = target_path.with_suffix(".png")
            cv2.imwrite(str(target_path), raw_image)
            print(f"Screenshot saved to: {target_path}")

    try:
        result = solve_from_image(image_source)
    except Exception as e:
        if not offline and auto_save_error and raw_image is not None and not (screenshot_path is not None or save_screenshot):
            err_path = Path("error_screenshot.png")
            cv2.imwrite(str(err_path), raw_image)
            print(f"[Debug] Failed screen automatically saved to: {err_path.resolve()}")
        raise e

    if not result.is_solved:
        raise RuntimeError("Recognized Nonogram has no valid solution.")

    if apply_taps and not offline:
        if device is None:
            device = ADBController()
        if result.puzzle.layout and result.solution:
            device.apply_solution(result.solution, result.puzzle.layout, random_order=random_order)

    return result
