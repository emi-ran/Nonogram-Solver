"""Core constraint propagation and backtracking solver for Nonograms."""

from __future__ import annotations
from typing import List, Optional

from src.nonogram.solver.models import Clue, Pattern, SolutionMatrix


def generate_patterns(length: int, clues: Clue) -> list[Pattern]:
    """Generate all valid binary patterns for a single line given clue constraints."""
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
            build(
                index + 1,
                position + clues[index] + (1 if index + 1 < len(clues) else 0),
                next_cells,
            )

    build(0, 0, [])
    return result


def solve(row_clues: list[Clue], column_clues: list[Clue]) -> SolutionMatrix | None:
    """Solve a Nonogram puzzle using constraint propagation and MRV backtracking."""
    rows, columns = len(row_clues), len(column_clues)
    row_domains = [generate_patterns(columns, clue) for clue in row_clues]
    column_domains = [generate_patterns(rows, clue) for clue in column_clues]

    if any(not domain for domain in [*row_domains, *column_domains]):
        return None

    def search(
        current_rows: list[list[Pattern]], current_columns: list[list[Pattern]]
    ) -> SolutionMatrix | None:
        r_domains = [domain[:] for domain in current_rows]
        c_domains = [domain[:] for domain in current_columns]

        while True:
            if any(not domain for domain in [*r_domains, *c_domains]):
                return None

            forced = [[-1] * columns for _ in range(rows)]
            for r_idx, domain in enumerate(r_domains):
                for c_idx in range(columns):
                    values = {pattern[c_idx] for pattern in domain}
                    if len(values) == 1:
                        forced[r_idx][c_idx] = values.pop()

            for c_idx, domain in enumerate(c_domains):
                for r_idx in range(rows):
                    values = {pattern[r_idx] for pattern in domain}
                    if len(values) == 1:
                        val = values.pop()
                        if forced[r_idx][c_idx] not in (-1, val):
                            return None
                        forced[r_idx][c_idx] = val

            changed = False
            for r_idx in range(rows):
                filtered = [
                    pattern
                    for pattern in r_domains[r_idx]
                    if all(
                        forced[r_idx][c_idx] == -1
                        or pattern[c_idx] == forced[r_idx][c_idx]
                        for c_idx in range(columns)
                    )
                ]
                if len(filtered) != len(r_domains[r_idx]):
                    r_domains[r_idx], changed = filtered, True

            for c_idx in range(columns):
                filtered = [
                    pattern
                    for pattern in c_domains[c_idx]
                    if all(
                        forced[r_idx][c_idx] == -1
                        or pattern[r_idx] == forced[r_idx][c_idx]
                        for r_idx in range(rows)
                    )
                ]
                if len(filtered) != len(c_domains[c_idx]):
                    c_domains[c_idx], changed = filtered, True

            if not changed:
                break

        if all(len(domain) == 1 for domain in [*r_domains, *c_domains]):
            return [list(r_domains[r_idx][0]) for r_idx in range(rows)]

        choices = [
            (len(domain), "row", idx)
            for idx, domain in enumerate(r_domains)
            if len(domain) > 1
        ]
        choices.extend(
            (len(domain), "column", idx)
            for idx, domain in enumerate(c_domains)
            if len(domain) > 1
        )
        _, kind, target_idx = min(choices)

        domain_pool = r_domains if kind == "row" else c_domains
        for candidate in domain_pool[target_idx]:
            next_rows, next_cols = r_domains[:], c_domains[:]
            if kind == "row":
                next_rows[target_idx] = [candidate]
            else:
                next_cols[target_idx] = [candidate]

            solution = search(next_rows, next_cols)
            if solution is not None:
                return solution

        return None

    return search(row_domains, column_domains)
