"""ADB communication and device touch automation."""

from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.nonogram.solver.models import Layout, SolutionMatrix


class ADBController:
    """Manages ADB connection, screen captures, and touch events on an Android device."""

    def __init__(self, serial: str | None = None) -> None:
        self._serial = serial

    @property
    def serial(self) -> str:
        if self._serial is None:
            output = subprocess.run(
                ["adb", "devices"], check=True, capture_output=True
            ).stdout.decode()
            serials = [
                line.split()[0]
                for line in output.splitlines()[1:]
                if line.endswith("\tdevice")
            ]
            if len(serials) != 1:
                raise RuntimeError(
                    f"ADB needs one device; found: {', '.join(serials) or 'none'}"
                )
            self._serial = serials[0]
        return self._serial

    def run_cmd(
        self,
        *args: str,
        capture_output: bool = False,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        """Run an ADB command targeting the active device."""
        cmd = ["adb", "-s", self.serial, *args]
        return subprocess.run(
            cmd, check=True, capture_output=capture_output, input=input_bytes
        )

    def screen_size(self) -> tuple[int, int]:
        """Get the device screen resolution (width, height)."""
        output = self.run_cmd("shell", "wm", "size", capture_output=True).stdout.decode()
        width, height = output.strip().splitlines()[-1].split()[-1].split("x")
        return int(width), int(height)

    def capture_image(self) -> np.ndarray:
        """Capture device screen directly into memory as a NumPy BGR image (no disk write)."""
        raw_png = self.run_cmd("exec-out", "screencap", "-p", capture_output=True).stdout
        image = cv2.imdecode(np.frombuffer(raw_png, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Failed to decode screenshot from ADB stream into memory.")
        return image

    def capture_screenshot(self, destination_path: Path | str) -> None:
        """Capture device screenshot and save to the specified file."""
        dest = Path(destination_path)
        raw_png = self.run_cmd("exec-out", "screencap", "-p", capture_output=True).stdout
        dest.write_bytes(raw_png)

    def tap(self, x: int, y: int) -> None:
        """Send a single tap at (x, y)."""
        self.run_cmd("shell", "input", "tap", str(x), str(y))

    def apply_solution(self, solution: SolutionMatrix, layout: Layout) -> None:
        """Tap all filled cells in a single interactive ADB shell session for maximum speed."""
        commands: list[str] = []
        for row_idx, line in enumerate(solution):
            for col_idx, value in enumerate(line):
                if value:
                    x, y = layout.cell_center(row_idx, col_idx)
                    commands.append(f"input tap {x} {y}")
        if commands:
            payload = ("\n".join(commands) + "\n").encode()
            self.run_cmd("shell", input_bytes=payload)
