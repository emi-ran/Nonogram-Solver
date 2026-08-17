"""Automation package for Nonogram solving and auto-play."""

from src.nonogram.automation.auto_player import AutoPlayer, AutoPlayerConfig
from src.nonogram.automation.runner import run_pipeline, solve_from_image

__all__ = [
    "AutoPlayer",
    "AutoPlayerConfig",
    "run_pipeline",
    "solve_from_image",
]
