"""Base interface for game automation modes."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.nonogram.automation.states import GameState, StateDetectionResult
from src.nonogram.device.adb import ADBController
from src.nonogram.solver.models import SolveResult


@dataclass
class ModeContext:
    levels_completed: int = 0
    consecutive_unknowns: int = 0
    is_finished: bool = False
    random_order: bool = False
    last_solved_puzzle: SolveResult | None = None
    custom_data: dict[str, Any] | None = None


class BaseGameMode(ABC):
    """Abstract base class for all game automation modes."""

    name: str = "base"
    description: str = "Base Game Mode"

    @abstractmethod
    def handle_state(
        self,
        detection: StateDetectionResult,
        image: np.ndarray,
        device: ADBController,
        context: ModeContext,
    ) -> bool:
        """Handle the current detected state. Returns True if progress was made, False to wait/retry."""
        pass
