"""Auto-player for continuous level progression."""

from __future__ import annotations
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.nonogram.automation.runner import run_pipeline
from src.nonogram.device.adb import ADBController
from src.nonogram.solver.models import SolveResult


@dataclass
class AutoPlayerConfig:
    max_levels: int = 100
    delay_between_levels: float = 2.5
    save_screenshots: bool = False
    screenshot_path: Path = Path("nonogram-screen.png")
    next_level_button_pos: tuple[int, int] | None = None


class AutoPlayer:
    """Automates playing multiple consecutive Nonogram levels."""

    def __init__(
        self,
        config: AutoPlayerConfig | None = None,
        device: ADBController | None = None,
    ) -> None:
        self.config = config or AutoPlayerConfig()
        self.device = device or ADBController()

    def play_single_level(self) -> SolveResult:
        """Solve and tap the current on-screen level (in-memory, no disk I/O by default)."""
        return run_pipeline(
            screenshot_path=self.config.screenshot_path if self.config.save_screenshots else None,
            device=self.device,
            apply_taps=True,
            offline=False,
            save_screenshot=self.config.save_screenshots,
        )

    def advance_to_next_level(self) -> None:
        """Click next level button or trigger progression if coordinate is defined."""
        if self.config.next_level_button_pos:
            x, y = self.config.next_level_button_pos
            self.device.tap(x, y)

    def run_loop(
        self,
        on_level_solved: Callable[[int, SolveResult], None] | None = None,
    ) -> int:
        """Run the auto-play loop across levels."""
        completed_count = 0

        for level_idx in range(1, self.config.max_levels + 1):
            try:
                result = self.play_single_level()
                completed_count += 1
                if on_level_solved:
                    on_level_solved(level_idx, result)

                time.sleep(self.config.delay_between_levels)
                self.advance_to_next_level()
                time.sleep(1.0)
            except Exception as e:
                print(f"[AutoPlayer] Stopped at level {level_idx}: {e}")
                break

        return completed_count
