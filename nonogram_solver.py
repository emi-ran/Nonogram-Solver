"""Dynamic Android Nonogram solver."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    first_x: int
    first_y: int
    step_x: int
    step_y: int

    def cell_center(self, row: int, column: int) -> tuple[int, int]:
        return self.first_x + column * self.step_x, self.first_y + row * self.step_y


Clue = tuple[int, ...]
Pattern = tuple[int, ...]
_ocr: RapidOCR | None = None
_adb_serial: str | None = None

PACKED_TEMPLATES = {
    0: bytes.fromhex("07e01ff81ff83c3c781c700e700ef00fe007e007e007e007e007e007e007e007f00f700e700e781e3c3c1ff81ff807e0"),
    1: bytes.fromhex("007f01ff0fff7fffff9ffe1ff01f801f001f001f001f001f001f001f001f001f001f001f001f001f001f001f001f001f"),
    2: bytes.fromhex("0fe01ff83ffc783ef01ee00ee00f000f000f001e001c003c007800f001f003e00f801f003e007c00f800ffffffffffff"),
    3: bytes.fromhex("0ff03ffc7ffc783ef00ee00e000f000e001e003c07f807f807fc001e000f00070007e007f00ff00f7c3e7ffc1ff807e0"),
    4: bytes.fromhex("0038007800f800f801f803f803b8073807380e381c381c38383838387038fffeffffffff7ffe00380038003800380038"),
    5: bytes.fromhex("7ffe7ffe7ffe7000f000f000e000e000e7f0fff8fffcfc3ef01fe00f000700070007e007f00ff81f7ffe3ffc1ff807e0"),
    6: bytes.fromhex("07f80ffc1ffe3c1e780f70077000f000e3f0e7f8effcfe3ef80ff80ff007f007f0077007780f380f3e3e1ffc0ff807e0"),
    7: bytes.fromhex("ffffffffffffffff001f001e003e003c00380078007000f000f001e003e003e007c007c0078007000f000f001e001c00"),
    8: bytes.fromhex("0ff01ffc3ffe7c1e780f700f7007700f780e3c3e1ffc1ff83ffc7c1e700ff007e007e007f007f00f7c1f7ffe1ffc0ff0"),
    9: bytes.fromhex("03001fe03ff07ff8f01cf01ee00ee00ee00ee00ee01e701f787e3ffe1fee0f8e000e000ef01ef01c7ff87ff01fe00380"),
}
TEMPLATES = {d: np.unpackbits(np.frombuffer(raw, dtype=np.uint8)).reshape(24, 16) for d, raw in PACKED_TEMPLATES.items()}


def _get_ocr() -> RapidOCR:
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def adb(*args: str, capture_output: bool = False, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    global _adb_serial
    if _adb_serial is None:
        output = subprocess.run(["adb", "devices"], check=True, capture_output=True).stdout.decode()
        serials = [line.split()[0] for line in output.splitlines()[1:] if line.endswith("\tdevice")]
        if len(serials) != 1:
            raise RuntimeError(f"ADB needs one device; found: {', '.join(serials) or 'none'}")
        _adb_serial = serials[0]
    return subprocess.run(["adb", "-s", _adb_serial, *args], check=True, capture_output=capture_output, input=input_bytes)


def screen_size() -> tuple[int, int]:
    output = adb("shell", "wm", "size", capture_output=True).stdout.decode()
    width, height = output.strip().splitlines()[-1].split()[-1].split("x")
    return int(width), int(height)


def capture(path: Path) -> None:
    path.write_bytes(adb("exec-out", "screencap", "-p", capture_output=True).stdout)


def tap(x: int, y: int) -> None:
    adb("shell", "input", "tap", str(x), str(y))


def _runs(values: np.ndarray, threshold: int) -> list[int]:
    positions = np.flatnonzero(values >= threshold)
    if not len(positions):
        return []
    groups = np.split(positions, np.where(np.diff(positions) > 1)[0] + 1)
    return [int(round(float(group.mean()))) for group in groups if len(group) >= 2]


def _line_centers(image: np.ndarray) -> tuple[list[int], list[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dark = gray < 235
    height, width = gray.shape
    # Board occupies stable screen area. Restrict projections so clue glyphs
    # and header controls cannot become fake grid lines.
    vertical = _runs(dark[780 : min(height, 1840)].sum(axis=0), 800)
    horizontal = _runs(dark[:, 220 : min(width, 1270)].sum(axis=1), 800)

    def merge_close(lines: list[int], maximum_gap: int) -> list[int]:
        merged: list[list[int]] = []
        for line in lines:
            if merged and line - merged[-1][-1] <= maximum_gap:
                merged[-1].append(line)
            else:
                merged.append([line])
        return [round(sum(group) / len(group)) for group in merged]

    vertical = merge_close([line for line in vertical if 220 <= line <= width - 15], 20)
    horizontal = merge_close([line for line in horizontal if 760 <= line <= min(height, 1850)], 20)
    columns, rows = len(vertical) - 1, len(horizontal) - 1
    if rows not in {5, 10, 15} or rows != columns:
        raise ValueError("Could not recognize a square Nonogram grid. No input sent.")
    return vertical, horizontal


def read_layout(image_path: Path) -> tuple[Layout, int, int]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Cannot read screenshot: {image_path}")
    vertical, horizontal = _line_centers(image)
    layout = Layout(
        image.shape[1],
        image.shape[0],
        (vertical[0] + vertical[1]) // 2,
        (horizontal[0] + horizontal[1]) // 2,
        round(float(np.diff(vertical).mean())),
        round(float(np.diff(horizontal).mean())),
    )
    return layout, len(horizontal) - 1, len(vertical) - 1


def _match_digit(image: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int | None, float]:
    x, y, width, height = box
    crop = image[y : y + height, x : x + width]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    mask = (gray < 150).astype("uint8")
    coords = cv2.findNonZero(mask)
    if coords is None:
        return None, 0.0
    bx, by, bw, bh = cv2.boundingRect(coords)
    digit = mask[by : by + bh, bx : bx + bw]
    resized = cv2.resize(digit.astype("float32"), (16, 24), interpolation=cv2.INTER_AREA)
    normalized = (resized > 0.3).astype("uint8")
    best_digit, best_score = None, -1.0
    for digit_value, template in TEMPLATES.items():
        intersection = np.sum((normalized == 1) & (template == 1))
        union = np.sum((normalized == 1) | (template == 1))
        score = float(intersection / max(1, union))
        if score > best_score:
            best_digit, best_score = digit_value, score
    return best_digit, best_score


def _card_clues(image: np.ndarray, layout: Layout, vertical_lines: list[int], horizontal_lines: list[int], count: int, horizontal: bool) -> list[Clue]:
    """Read each clue card independently, preserving glyph spacing."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result: list[Clue] = []
    for index in range(count):
        if horizontal:
            top = round(layout.first_y - layout.step_y / 2 + index * layout.step_y + 8)
            bottom = round(layout.first_y + layout.step_y / 2 + index * layout.step_y - 8)
            left, right = 10, vertical_lines[0] - 10
            order_axis = 0
        else:
            left = round(layout.first_x - layout.step_x / 2 + index * layout.step_x + 8)
            right = round(layout.first_x + layout.step_x / 2 + index * layout.step_x - 8)
            top, bottom = max(450, horizontal_lines[0] - 250), horizontal_lines[0] - 10
            order_axis = 1
        crop = gray[top:bottom, left:right]
        mask = (crop < 150).astype("uint8")
        _, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        glyphs: list[tuple[int, int, int, int]] = []
        for x, y, width, height, area in stats[1:]:
            if area >= 30 and height >= 15 and width >= 3:
                glyphs.append((int(x + left), int(y + top), int(width), int(height)))
        glyphs.sort(key=lambda box: box[order_axis])
        if horizontal:
            digits = [(box[0], box[0] + box[2], _match_digit(image, box)[0]) for box in glyphs]
            lines: list[list[tuple[int, int, int | None]]] = [digits]
        else:
            # Column clues stack vertically. Components sharing a y-line form
            # one token, so 12 stays 12 while separate 1 and 2 stay separate.
            raw_lines: list[list[tuple[int, int, int, int | None]]] = []
            for box in glyphs:
                center_y = box[1] + box[3] / 2
                line = next((line for line in raw_lines if abs(center_y - line[0][2]) <= box[3] * 0.45), None)
                entry = (box[0], box[0] + box[2], int(center_y), _match_digit(image, box)[0])
                if line is None:
                    raw_lines.append([entry])
                else:
                    line.append(entry)
            lines = [[(entry[0], entry[1], entry[3]) for entry in sorted(line)] for line in sorted(raw_lines, key=lambda line: line[0][2])]

        values: list[int] = []
        gap_limit = (layout.step_x if horizontal else layout.step_x) * 0.16
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
                    if next_start - end <= gap_limit and digit != 0 and next_digit is not None:
                        combined = digit * 10 + next_digit
                        if combined <= count:
                            values.append(combined)
                            position += 2
                            continue
                values.append(int(digit))
                position += 1
        result.append(tuple(values))
    return result


def read_clues(image_path: Path, layout: Layout, rows: int, columns: int) -> tuple[list[Clue], list[Clue]]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Cannot read screenshot: {image_path}")
    vertical, horizontal = _line_centers(image)
    rows_result = _card_clues(image, layout, vertical, horizontal, rows, horizontal=True)
    columns_result = _card_clues(image, layout, vertical, horizontal, columns, horizontal=False)
    if any(value <= 0 or value > rows for line in rows_result for value in line) or any(value <= 0 or value > columns for line in columns_result for value in line):
        raise ValueError("Nonogram clue value is outside board size. No input sent.")
    if not any(rows_result) or not any(columns_result):
        raise ValueError("No Nonogram clues recognized. No input sent.")
    return rows_result, columns_result


def patterns(length: int, clues: Clue) -> list[Pattern]:
    if not clues:
        return [tuple(0 for _ in range(length))]
    if sum(clues) + len(clues) - 1 > length:
        return []
    result: list[Pattern] = []

    def build(index: int, start: int, cells: list[int]) -> None:
        if index == len(clues):
            result.append(tuple(cells + [0] * (length - len(cells))))
            return
        remaining = sum(clues[index + 1 :]) + max(0, len(clues) - index - 2)
        for position in range(start, length - remaining - clues[index] + 1):
            next_cells = cells + [0] * (position - len(cells)) + [1] * clues[index]
            if index + 1 < len(clues):
                next_cells.append(0)
            build(index + 1, position + clues[index] + (1 if index + 1 < len(clues) else 0), next_cells)

    build(0, 0, [])
    return result


def solve(row_clues: list[Clue], column_clues: list[Clue]) -> list[list[int]] | None:
    rows, columns = len(row_clues), len(column_clues)
    row_domains = [patterns(columns, clue) for clue in row_clues]
    column_domains = [patterns(rows, clue) for clue in column_clues]
    if any(not domain for domain in [*row_domains, *column_domains]):
        return None

    def search(current_rows: list[list[Pattern]], current_columns: list[list[Pattern]]) -> list[list[int]] | None:
        row_domains = [domain[:] for domain in current_rows]
        column_domains = [domain[:] for domain in current_columns]
        while True:
            if any(not domain for domain in [*row_domains, *column_domains]):
                return None
            forced = [[-1] * columns for _ in range(rows)]
            for row, domain in enumerate(row_domains):
                for column in range(columns):
                    values = {pattern[column] for pattern in domain}
                    if len(values) == 1:
                        forced[row][column] = values.pop()
            for column, domain in enumerate(column_domains):
                for row in range(rows):
                    values = {pattern[row] for pattern in domain}
                    if len(values) == 1:
                        value = values.pop()
                        if forced[row][column] not in (-1, value):
                            return None
                        forced[row][column] = value
            changed = False
            for row in range(rows):
                filtered = [pattern for pattern in row_domains[row] if all(forced[row][column] == -1 or pattern[column] == forced[row][column] for column in range(columns))]
                if len(filtered) != len(row_domains[row]):
                    row_domains[row], changed = filtered, True
            for column in range(columns):
                filtered = [pattern for pattern in column_domains[column] if all(forced[row][column] == -1 or pattern[row] == forced[row][column] for row in range(rows))]
                if len(filtered) != len(column_domains[column]):
                    column_domains[column], changed = filtered, True
            if not changed:
                break
        if all(len(domain) == 1 for domain in [*row_domains, *column_domains]):
            return [list(row_domains[row][0]) for row in range(rows)]
        choices = [(len(domain), "row", index) for index, domain in enumerate(row_domains) if len(domain) > 1]
        choices.extend((len(domain), "column", index) for index, domain in enumerate(column_domains) if len(domain) > 1)
        _, kind, index = min(choices)
        for candidate in (row_domains if kind == "row" else column_domains)[index]:
            next_rows, next_columns = row_domains[:], column_domains[:]
            if kind == "row":
                next_rows[index] = [candidate]
            else:
                next_columns[index] = [candidate]
            solution = search(next_rows, next_columns)
            if solution is not None:
                return solution
        return None

    return search(row_domains, column_domains)


def apply(solution: list[list[int]], layout: Layout) -> None:
    """Tap filled cells in one ADB shell session."""
    commands: list[str] = []
    for row, line in enumerate(solution):
        for column, value in enumerate(line):
            if value:
                x, y = layout.cell_center(row, column)
                commands.append(f"input tap {x} {y}")
    if commands:
        adb("shell", input_bytes=("\n".join(commands) + "\n").encode())


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve current Nonogram through ADB.")
    parser.add_argument("--apply", action="store_true", help="Tap solution cells. Default is dry-run.")
    parser.add_argument("--offline", action="store_true", help="Use existing screenshot; do not call ADB.")
    parser.add_argument("--screenshot", type=Path, default=Path("nonogram-screen.png"))
    args = parser.parse_args()
    if args.offline:
        if args.apply:
            raise SystemExit("--apply cannot be used with --offline.")
        image = cv2.imread(str(args.screenshot))
        if image is None:
            raise SystemExit(f"Cannot read screenshot: {args.screenshot}")
        height, width = image.shape[:2]
    else:
        width, height = screen_size()
        capture(args.screenshot)
    layout, rows, columns = read_layout(args.screenshot)
    row_clues, column_clues = read_clues(args.screenshot, layout, rows, columns)
    solution = solve(row_clues, column_clues)
    if solution is None:
        raise SystemExit("Recognized Nonogram has no valid solution. No input sent.")
    filled = sum(value for line in solution for value in line)
    print(f"Recognized {rows}x{columns} Nonogram; {filled} filled cells.")
    print(f"Rows: {row_clues}")
    print(f"Columns: {column_clues}")
    if args.apply:
        apply(solution, layout)


if __name__ == "__main__":
    main()
