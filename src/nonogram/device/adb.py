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

    @classmethod
    def list_devices(cls) -> list[str]:
        """List serials of all currently connected active ADB devices."""
        output = subprocess.run(
            ["adb", "devices"], check=True, capture_output=True
        ).stdout.decode()
        serials = [
            line.split()[0]
            for line in output.splitlines()[1:]
            if line.endswith("\tdevice")
        ]
        return serials

    @property
    def serial(self) -> str:
        if self._serial is None:
            serials = self.list_devices()
            if not serials:
                raise RuntimeError("No connected ADB devices found. Please enable USB/Wireless debugging.")
            if len(serials) == 1:
                self._serial = serials[0]
            else:
                # Multiple devices detected: prompt user to select interactively
                print("\n[ADB] Multiple Android devices detected:")
                for idx, dev in enumerate(serials, 1):
                    print(f"  [{idx}] {dev}")

                try:
                    choice_str = input(f"Select device (1-{len(serials)}) [default 1]: ").strip()
                    chosen_idx = int(choice_str) if choice_str else 1
                    if 1 <= chosen_idx <= len(serials):
                        self._serial = serials[chosen_idx - 1]
                    else:
                        self._serial = serials[0]
                except Exception:
                    self._serial = serials[0]

                print(f"[ADB] Active device selected: {self._serial}\n")

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

    def is_screen_awake(self) -> bool:
        """Check if device screen is on / awake."""
        output = self.run_cmd("shell", "dumpsys", "power", capture_output=True).stdout.decode()
        return "mWakefulness=Awake" in output or "mHoldingDisplaySuspendBlocker=true" in output

    def wake_up_and_unlock(self) -> None:
        """Ensure device screen is awake and unlocked."""
        if not self.is_screen_awake():
            self.run_cmd("shell", "input", "keyevent", "224")  # KEYCODE_WAKEUP
            self.run_cmd("shell", "input", "keyevent", "82")   # KEYCODE_MENU (unlocks basic lockscreen)
            # Swipe up in case of swipe-to-unlock
            w, h = self.screen_size()
            self.run_cmd("shell", "input", "swipe", str(w // 2), str(int(h * 0.8)), str(w // 2), str(int(h * 0.2)), "200")

    def is_app_in_foreground(self, package_name: str = "com.easybrain.nonogram") -> bool:
        """Check if the target app package is currently focused / in foreground."""
        output = self.run_cmd("shell", "dumpsys", "window", capture_output=True).stdout.decode()
        return package_name in output

    def launch_app(self, package_name: str = "com.easybrain.nonogram") -> None:
        """Launch the app using Android monkey launcher intent."""
        self.wake_up_and_unlock()
        self.run_cmd(
            "shell",
            "monkey",
            "-p",
            package_name,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        )

    def ensure_app_ready(self, package_name: str = "com.easybrain.nonogram") -> None:
        """Ensure device is awake and app is running in the foreground."""
        self.wake_up_and_unlock()
        if not self.is_app_in_foreground(package_name):
            print(f"[Device] App '{package_name}' not in foreground. Launching...")
            self.launch_app(package_name)

    def tap(self, x: int, y: int) -> None:
        """Send a single tap at (x, y)."""
        self.run_cmd("shell", "input", "tap", str(x), str(y))

    def apply_solution(
        self,
        solution: SolutionMatrix,
        layout: Layout,
        pattern: str = "sequential",
    ) -> str:
        """Tap all filled cells in a single interactive ADB shell session using the chosen pattern."""
        from src.nonogram.automation.patterns import order_cells, resolve_pattern

        concrete_pattern = resolve_pattern(pattern)
        cells = order_cells(solution, layout, pattern=concrete_pattern)

        commands = [f"input tap {x} {y}" for x, y in cells]
        if commands:
            payload = ("\n".join(commands) + "\n").encode()
            self.run_cmd("shell", input_bytes=payload)

        pat_val = concrete_pattern.value if hasattr(concrete_pattern, "value") else str(concrete_pattern)
        return str(pat_val)

