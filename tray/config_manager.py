"""
Configuration management for Turing Smart Screen.

Two independent config layers:
- ``TrayConfig``   – tray application preferences (JSON in ~/.config)
- ``ScreenConfig`` – turing-smart-screen project config.yaml
"""

import json
import os
import re
from pathlib import Path
from typing import Any, List, Optional


# ═══════════════════════════════════════════════════════════════
# Tray application settings
# ═══════════════════════════════════════════════════════════════

class TrayConfig:
    """
    Persists tray-specific preferences to
    ``~/.config/turing-screen/tray.json``.
    """

    CONFIG_DIR = Path.home() / ".config" / "turing-screen"
    CONFIG_FILE = CONFIG_DIR / "tray.json"

    DEFAULTS: dict[str, Any] = {
        "language": "pt_BR",
        "show_notifications": True,
        "check_updates": True,
        "poll_interval": 5,
    }

    def __init__(self):
        self._data: dict[str, Any] = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass  # Keep defaults on corrupt file

    def save(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    def reset(self):
        self._data = dict(self.DEFAULTS)
        self.save()


# ═══════════════════════════════════════════════════════════════
# Turing Smart Screen project config.yaml
# ═══════════════════════════════════════════════════════════════

class ScreenConfig:
    """
    Reads and writes selected fields from the turing-smart-screen
    ``config.yaml`` using regex (avoids reformatting the YAML).
    """

    def __init__(self, turing_dir: str):
        self.turing_dir = Path(turing_dir)
        self.config_file = self.turing_dir / "config.yaml"
        self.themes_dir = self.turing_dir / "res" / "themes"

    # ── Raw I/O ──────────────────────────────────────────────

    def _read(self) -> str:
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as fh:
                return fh.read()
        return ""

    def _write(self, content: str):
        with open(self.config_file, "w", encoding="utf-8") as fh:
            fh.write(content)

    def exists(self) -> bool:
        return self.config_file.exists()

    # ── Themes ───────────────────────────────────────────────

    def get_available_themes(self) -> List[str]:
        """List directories under ``res/themes/`` that contain a theme.yaml."""
        if not self.themes_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.themes_dir.iterdir()
            if d.is_dir() and (d / "theme.yaml").exists()
        )

    def get_current_theme(self) -> Optional[str]:
        content = self._read()
        match = re.search(
            r"^\s*THEME\s*:\s*[\"']?([^\"'\n]+)[\"']?\s*$",
            content,
            re.MULTILINE,
        )
        return match.group(1).strip() if match else None

    def set_theme(self, theme_name: str) -> bool:
        content = self._read()
        new, count = re.subn(
            r"^(\s*THEME\s*:\s*)[\"']?[^\"'\n]+[\"']?\s*$",
            rf"\g<1>{theme_name}",
            content,
            flags=re.MULTILINE,
        )
        if count:
            self._write(new)
            return True
        return False

    # ── Orientation ──────────────────────────────────────────

    # Turing Smart Screen uses 0=0°, 1=90°, 2=180°, 3=270°
    _ORIENT_PATTERN = r"^(\s*DISPLAY_ORIENTATION\s*:\s*)\d+"

    def get_orientation(self) -> int:
        content = self._read()
        match = re.search(self._ORIENT_PATTERN, content, re.MULTILINE)
        if match:
            # Extract just the digit from the full match
            digit_match = re.search(r"\d+$", match.group(0))
            return int(digit_match.group(0)) if digit_match else 0
        return 0

    def set_orientation(self, value: int) -> bool:
        """Set orientation: 0=0°, 1=90°, 2=180°, 3=270°."""
        if value not in (0, 1, 2, 3):
            return False
        content = self._read()
        new, count = re.subn(
            self._ORIENT_PATTERN,
            rf"\g<1>{value}",
            content,
            flags=re.MULTILINE,
        )
        if count:
            self._write(new)
            return True
        return False

    # ── Display model ────────────────────────────────────────

    def get_display_model(self) -> Optional[str]:
        content = self._read()
        match = re.search(
            r"^\s*DISPLAY\s*:\s*[\"']?([^\"'\n]+)[\"']?\s*$",
            content,
            re.MULTILINE,
        )
        return match.group(1).strip() if match else None
