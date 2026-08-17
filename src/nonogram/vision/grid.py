"""Grid and board layout detection from screenshots."""

from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np

from src.nonogram import config
from src.nonogram.solver.models import Layout


def _runs(values: np.ndarray, threshold: int) -> list[int]:
    """Find continuous segments exceeding a threshold and return their center indices."""
    positions = np.flatnonzero(values >= threshold)
    if not len(positions):
        return []
    groups = np.split(positions, np.where(np.diff(positions) > 1)[0] + 1)
    return [int(round(float(group.mean()))) for group in groups if len(group) >= 2]


def extract_regular_grid(
    lines: list[int],
    allowed_sizes: tuple[int, ...] = (5, 10, 15, 20),
    line_cluster_gap: int = 30,
) -> list[int] | None:
    """Find a subset of candidate lines that forms a highly regular, equidistant Nonogram grid."""
    if not lines:
        return None

    # Merge very close duplicate/fragment lines (< line_cluster_gap)
    merged: list[list[int]] = []
    for line in sorted(lines):
        if merged and line - merged[-1][-1] <= line_cluster_gap:
            merged[-1].append(line)
        else:
            merged.append([line])
    distinct = [round(sum(group) / len(group)) for group in merged]

    # Check largest grid sizes first (e.g. 20 -> 15 -> 10 -> 5) so sub-slices of larger grids are not misidentified
    for n in sorted(allowed_sizes, reverse=True):
        target_len = n + 1
        if len(distinct) < target_len:
            continue
        best_for_n: list[int] | None = None
        best_score = float("inf")
        for start in range(len(distinct) - target_len + 1):
            sub = distinct[start : start + target_len]
            diffs = np.diff(sub)
            std = float(np.std(diffs))
            mean_step = float(np.mean(diffs))
            expected_step = 1000.0 / n
            if 0.65 * expected_step <= mean_step <= 1.45 * expected_step:
                if std < best_score and std < 12.0:
                    best_score = std
                    best_for_n = sub
        if best_for_n is not None:
            return best_for_n

    return None


def find_line_centers(image: np.ndarray) -> tuple[list[int], list[int]]:
    """Detect vertical and horizontal grid lines on the Nonogram board."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dark = gray < 235
    height, width = gray.shape

    # Restrict projections so clue glyphs & header controls cannot become fake grid lines
    vertical_raw = _runs(
        dark[780 : min(height, 1840)].sum(axis=0), config.LINE_PROJECTION_THRESHOLD
    )
    horizontal_raw = _runs(
        dark[:, config.MIN_GRID_COORDINATE_X : min(width, 1270)].sum(axis=1),
        config.LINE_PROJECTION_THRESHOLD,
    )

    vertical = extract_regular_grid(
        [line for line in vertical_raw if config.MIN_GRID_COORDINATE_X <= line <= width - 15]
    )
    horizontal = extract_regular_grid(
        [line for line in horizontal_raw if config.MIN_GRID_COORDINATE_Y <= line <= min(height, config.MAX_GRID_COORDINATE_Y)]
    )

    if vertical is None or horizontal is None:
        raise ValueError("Could not recognize a valid Nonogram grid on screen.")

    columns, rows = len(vertical) - 1, len(horizontal) - 1
    if rows not in config.ALLOWED_GRID_SIZES or rows != columns:
        raise ValueError(
            f"Could not recognize a valid square Nonogram grid (found {rows}x{columns})."
        )
    return vertical, horizontal


def read_layout(image_or_path: np.ndarray | Path | str) -> tuple[Layout, int, int]:
    """Read board layout from an image or image path."""
    if isinstance(image_or_path, (str, Path)):
        image = cv2.imread(str(image_or_path))
        if image is None:
            raise ValueError(f"Cannot read screenshot: {image_or_path}")
    else:
        image = image_or_path

    vertical, horizontal = find_line_centers(image)
    layout = Layout(
        width=image.shape[1],
        height=image.shape[0],
        first_x=(vertical[0] + vertical[1]) // 2,
        first_y=(horizontal[0] + horizontal[1]) // 2,
        step_x=round(float(np.diff(vertical).mean())),
        step_y=round(float(np.diff(horizontal).mean())),
    )
    return layout, len(horizontal) - 1, len(vertical) - 1
