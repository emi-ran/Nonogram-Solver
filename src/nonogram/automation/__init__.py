"""Automation package for Nonogram solving and autonomous play."""

from src.nonogram.automation.auto_player import AutoPlayer, AutoPlayerConfig
from src.nonogram.automation.modes import (
    AVAILABLE_MODES,
    BaseGameMode,
    DailyChallengeMode,
    EventGameMode,
    NormalGameMode,
    get_game_mode,
)
from src.nonogram.automation.runner import run_pipeline, solve_from_image
from src.nonogram.automation.states import (
    GameState,
    GameStateDetector,
    StateDetectionResult,
)

__all__ = [
    "AutoPlayer",
    "AutoPlayerConfig",
    "GameState",
    "GameStateDetector",
    "StateDetectionResult",
    "BaseGameMode",
    "NormalGameMode",
    "DailyChallengeMode",
    "EventGameMode",
    "AVAILABLE_MODES",
    "get_game_mode",
    "run_pipeline",
    "solve_from_image",
]
