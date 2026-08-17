"""Data models for Nonogram board, clues, and layout."""

from __future__ import annotations
from dataclasses import dataclass

Clue = tuple[int, ...]
Pattern = tuple[int, ...]
SolutionMatrix = list[list[int]]


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


@dataclass(frozen=True)
class NonogramPuzzle:
    rows: int
    columns: int
    row_clues: list[Clue]
    column_clues: list[Clue]
    layout: Layout | None = None


@dataclass(frozen=True)
class SolveResult:
    puzzle: NonogramPuzzle
    solution: SolutionMatrix | None
    filled_count: int

    @property
    def is_solved(self) -> bool:
        return self.solution is not None
