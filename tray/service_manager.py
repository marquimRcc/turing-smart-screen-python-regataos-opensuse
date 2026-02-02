"""
Manages the Turing Smart Screen systemd user service.

Controls start/stop/restart/enable/disable of the ``turing-screen``
user-level systemd service that runs the display process.
"""

import subprocess
import shutil
from typing import Tuple


class ServiceManager:
    """Interface to ``systemctl --user`` for the turing-screen service."""

    SERVICE_NAME = "turing-screen"

    def __init__(self):
        self._systemctl = shutil.which("systemctl")

    # ── Low-level ────────────────────────────────────────────

    def _run(self, *args: str, timeout: int = 10) -> Tuple[bool, str]:
        """Run a ``systemctl --user`` command and return (success, stdout)."""
        if not self._systemctl:
            return False, "systemctl not found"
        try:
            result = subprocess.run(
                [self._systemctl, "--user", *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as exc:
            return False, str(exc)

    # ── Service lifecycle ────────────────────────────────────

    def start(self) -> bool:
        ok, _ = self._run("start", self.SERVICE_NAME)
        return ok

    def stop(self) -> bool:
        ok, _ = self._run("stop", self.SERVICE_NAME)
        return ok

    def restart(self) -> bool:
        ok, _ = self._run("restart", self.SERVICE_NAME)
        return ok

    def is_active(self) -> bool:
        ok, _ = self._run("is-active", self.SERVICE_NAME)
        return ok

    # ── Autostart (enable/disable) ───────────────────────────

    def enable(self) -> bool:
        ok, _ = self._run("enable", self.SERVICE_NAME)
        return ok

    def disable(self) -> bool:
        ok, _ = self._run("disable", self.SERVICE_NAME)
        return ok

    def is_enabled(self) -> bool:
        ok, _ = self._run("is-enabled", self.SERVICE_NAME)
        return ok

    # ── Diagnostics ──────────────────────────────────────────

    def status(self) -> str:
        """Return the full ``systemctl status`` output."""
        _, output = self._run("status", self.SERVICE_NAME, timeout=5)
        return output

    def journal(self, lines: int = 100) -> str:
        """Return recent journal entries for the service."""
        try:
            result = subprocess.run(
                [
                    "journalctl", "--user",
                    "-u", self.SERVICE_NAME,
                    "-n", str(lines),
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.stdout else ""
        except Exception as exc:
            return f"Error reading journal: {exc}"

    def daemon_reload(self) -> bool:
        ok, _ = self._run("daemon-reload")
        return ok
