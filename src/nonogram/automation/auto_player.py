"""Autonomous Auto-Player engine with state machine and extensible game modes."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from src.nonogram.automation.modes import BaseGameMode, get_game_mode
from src.nonogram.automation.modes.base import ModeContext
from src.nonogram.automation.states import GameStateDetector
from src.nonogram.device.adb import ADBController


@dataclass
class AutoPlayerConfig:
    mode: str = "normal"
    max_levels: int = 100
    poll_interval: float = 1.0
    save_screenshots: bool = False
    screenshot_path: Path = Path("nonogram-screen.png")
    stop_on_error: bool = False
    game_mode_handler: BaseGameMode | None = None


class AutoPlayer:
    """Orchestrates fully autonomous Nonogram gameplay across levels."""

    def __init__(
        self,
        config: AutoPlayerConfig | None = None,
        device: ADBController | None = None,
    ) -> None:
        self.config = config or AutoPlayerConfig()
        self.device = device or ADBController()
        self.mode_handler = (
            self.config.game_mode_handler or get_game_mode(self.config.mode)
        )
        self.context = ModeContext()

    def run_loop(
        self,
        on_progress: Callable[[int, str], None] | None = None,
    ) -> int:
        """Run the main autonomous state machine loop."""
        print(f"[AutoPlayer] Started | Mode: '{self.mode_handler.name}' | Target: {self.config.max_levels} levels")
        consecutive_errors = 0

        # Ensure device is awake and Nonogram app is launched in foreground
        try:
            self.device.ensure_app_ready()
            time.sleep(2.0)
        except Exception as e:
            print(f"[AutoPlayer] Warning on initial app launch: {e}")

        while self.context.levels_completed < self.config.max_levels:
            try:
                # 1. Capture screen directly in memory
                image = self.device.capture_image()
                if self.config.save_screenshots:
                    self.device.capture_screenshot(self.config.screenshot_path)

                # 2. Detect screen state
                detection = GameStateDetector.detect(image)

                # 3. Dispatch to game mode handler
                progress_made = self.mode_handler.handle_state(
                    detection=detection,
                    image=image,
                    device=self.device,
                    context=self.context,
                )

                if progress_made:
                    consecutive_errors = 0
                    if on_progress:
                        on_progress(self.context.levels_completed, f"State: {detection.state.name}")

                time.sleep(self.config.poll_interval)

            except KeyboardInterrupt:
                print("\n[AutoPlayer] Stopped by user.")
                break
            except Exception as e:
                consecutive_errors += 1
                print(f"[AutoPlayer] Warning: {e}")
                if self.config.stop_on_error or consecutive_errors >= 5:
                    print("[AutoPlayer] Stopping due to repeated errors.")
                    break
                time.sleep(1.5)

        print(f"\n[AutoPlayer] Session ended. Completed {self.context.levels_completed}/{self.config.max_levels} levels.")
        return self.context.levels_completed
