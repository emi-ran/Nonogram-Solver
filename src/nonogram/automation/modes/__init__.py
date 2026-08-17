"""Game modes registry and factories."""

from typing import Type

from src.nonogram.automation.modes.base import BaseGameMode
from src.nonogram.automation.modes.daily import DailyChallengeMode
from src.nonogram.automation.modes.events import EventGameMode
from src.nonogram.automation.modes.normal import NormalGameMode

AVAILABLE_MODES: dict[str, Type[BaseGameMode]] = {
    "normal": NormalGameMode,
    "daily": DailyChallengeMode,
    "event": EventGameMode,
    "adventure": EventGameMode,
    "rise_dice": EventGameMode,
}


def get_game_mode(mode_name: str) -> BaseGameMode:
    """Retrieve game mode instance by name."""
    mode_cls = AVAILABLE_MODES.get(mode_name.lower().strip())
    if not mode_cls:
        valid_modes = ", ".join(AVAILABLE_MODES.keys())
        raise ValueError(f"Unknown game mode '{mode_name}'. Available modes: {valid_modes}")
    return mode_cls()


__all__ = [
    "BaseGameMode",
    "NormalGameMode",
    "DailyChallengeMode",
    "EventGameMode",
    "AVAILABLE_MODES",
    "get_game_mode",
]
