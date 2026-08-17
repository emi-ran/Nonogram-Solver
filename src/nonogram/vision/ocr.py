"""OCR and clue extraction using template matching and connected components."""

from __future__ import annotations
from pathlib import Path

import cv2
import numpy as np

from src.nonogram import config
from src.nonogram.solver.models import Clue, Layout
from src.nonogram.vision.grid import find_line_centers
from src.nonogram.vision.templates import TEMPLATES


def match_digit(image: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int | None, float]:
    """Match a cropped bounding box against digit templates."""
    x, y, width, height = box
    crop = image[y : y + height, x : x + width]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    mask = (gray < config.OCR_BINARIZATION_THRESHOLD).astype("uint8")
    coords = cv2.findNonZero(mask)
    if coords is None:
        return None, 0.0
    bx, by, bw, bh = cv2.boundingRect(coords)
    digit = mask[by : by + bh, bx : bx + bw]
    resized = cv2.resize(
        digit.astype("float32"),
        (config.DIGIT_WIDTH, config.DIGIT_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )
    normalized = (resized > config.DIGIT_THRESHOLD).astype("uint8")
    best_digit, best_score = None, -1.0
    for digit_value, template in TEMPLATES.items():
        intersection = np.sum((normalized == 1) & (template == 1))
        union = np.sum((normalized == 1) | (template == 1))
        score = float(intersection / max(1, union))
        if score > best_score:
            best_digit, best_score = digit_value, score
    return best_digit, best_score


def read_card_clues(
    image: np.ndarray,
    layout: Layout,
    vertical_lines: list[int],
    horizontal_lines: list[int],
    count: int,
    horizontal: bool,
) -> list[Clue]:
    """Read clue values for each row or column card independently."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    result: list[Clue] = []

    for index in range(count):
        if horizontal:
            top = horizontal_lines[index] + 2
            bottom = horizontal_lines[index + 1] - 2
            left, right = 5, vertical_lines[0] - 5
            order_axis = 0
        else:
            left = vertical_lines[index] + 2
            right = vertical_lines[index + 1] - 2
            top = max(450, horizontal_lines[0] - 240)
            bottom = horizontal_lines[0] - 8
            order_axis = 1

        crop = gray[top:bottom, left:right]
        mask = (crop < config.OCR_BINARIZATION_THRESHOLD).astype("uint8")
        _, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        glyphs: list[tuple[int, int, int, int]] = []
        for x, y, width, height, area in stats[1:]:
            if (
                area >= 20
                and height >= 10
                and width >= config.GLYPH_MIN_WIDTH
            ):
                glyphs.append((int(x + left), int(y + top), int(width), int(height)))
        glyphs.sort(key=lambda box: box[order_axis])

        if horizontal:
            digits = [
                (box[0], box[0] + box[2], match_digit(image, box)[0]) for box in glyphs
            ]
            lines: list[list[tuple[int, int, int | None]]] = [digits]
            gap_limit = layout.step_x * 0.12
        else:
            # Column clues stack vertically. Components sharing a y-line form one token.
            raw_lines: list[list[tuple[int, int, int, int | None]]] = []
            for box in glyphs:
                center_y = box[1] + box[3] / 2
                line = next(
                    (
                        line
                        for line in raw_lines
                        if abs(center_y - line[0][2]) <= max(8.0, box[3] * 0.50)
                    ),
                    None,
                )
                entry = (
                    box[0],
                    box[0] + box[2],
                    int(center_y),
                    match_digit(image, box)[0],
                )
                if line is None:
                    raw_lines.append([entry])
                else:
                    line.append(entry)
            lines = [
                [(entry[0], entry[1], entry[3]) for entry in sorted(line)]
                for line in sorted(raw_lines, key=lambda line: line[0][2])
            ]
            gap_limit = max(15.0, layout.step_x * 0.35)

        values: list[int] = []
        allow_two_digit = count >= 10
        for line in lines:
            position = 0
            while position < len(line):
                start, end, digit = line[position]
                if digit is None:
                    position += 1
                    continue
                if allow_two_digit and position + 1 < len(line):
                    next_start, next_end, next_digit = line[position + 1]
                    if (
                        next_start - end <= gap_limit
                        and digit != 0
                        and next_digit is not None
                    ):
                        combined = digit * 10 + next_digit
                        if combined <= count:
                            values.append(combined)
                            position += 2
                            continue
                values.append(int(digit))
                position += 1
        result.append(tuple(values))
    return result


def read_clues(
    image_or_path: np.ndarray | Path | str, layout: Layout, rows: int, columns: int
) -> tuple[list[Clue], list[Clue]]:
    """Read both row and column clues from an image."""
    if isinstance(image_or_path, (str, Path)):
        image = cv2.imread(str(image_or_path))
        if image is None:
            raise ValueError(f"Cannot read screenshot: {image_or_path}")
    else:
        image = image_or_path

    vertical, horizontal = find_line_centers(image)
    rows_result = read_card_clues(
        image, layout, vertical, horizontal, rows, horizontal=True
    )
    columns_result = read_card_clues(
        image, layout, vertical, horizontal, columns, horizontal=False
    )

    if any(
        value <= 0 or value > rows for line in rows_result for value in line
    ) or any(
        value <= 0 or value > columns for line in columns_result for value in line
    ):
        raise ValueError("Nonogram clue value is outside board size. No input sent.")
    if not any(rows_result) or not any(columns_result):
        raise ValueError("No Nonogram clues recognized. No input sent.")

    return rows_result, columns_result
