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

    # Map display revision to size
    REVISION_TO_SIZE = {
        "A": "3.5",      # Turing 3.5"
        "B": "3.5",      # Turing 3.5" 
        "C": "5",        # Turing 5"
        "D": "3.5",      # Kipye Qiye 3.5"
        "WEACT_A": "3.5",  # WeAct 3.5"
        "WEACT_B": "0.96", # WeAct 0.96"
        "SIMU": None,    # Simulated - no filter
    }

    # Map resolution (WxH) to display size
    RESOLUTION_TO_SIZE = {
        (320, 480): "3.5",
        (480, 320): "3.5",
        (480, 800): "5",
        (800, 480): "5",
        (128, 128): "0.96",
        (160, 128): "0.96",
    }

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

    # ── Display detection ────────────────────────────────────

    def get_display_revision(self) -> Optional[str]:
        """Get the REVISION value from config.yaml."""
        content = self._read()
        match = re.search(
            r"^\s*REVISION\s*:\s*[\"']?([^\"'\n#]+)[\"']?",
            content,
            re.MULTILINE,
        )
        return match.group(1).strip() if match else None

    def get_display_size(self) -> Optional[str]:
        """
        Detect display size from REVISION in config.yaml.
        Returns '3.5', '5', '0.96', or None if unknown.
        """
        revision = self.get_display_revision()
        if revision:
            return self.REVISION_TO_SIZE.get(revision.upper())
        return None

    def _get_theme_size(self, theme_dir: Path) -> Optional[str]:
        """
        Detect theme size from theme.yaml.
        Checks DISPLAY_SIZE first, then falls back to resolution.
        """
        theme_yaml = theme_dir / "theme.yaml"
        if not theme_yaml.exists():
            return None
        
        try:
            with open(theme_yaml, "r", encoding="utf-8") as fh:
                content = fh.read()
            
            # Check for explicit DISPLAY_SIZE
            match = re.search(
                r"^\s*DISPLAY_SIZE\s*:\s*[\"']?([0-9.]+)",
                content,
                re.MULTILINE,
            )
            if match:
                return match.group(1)
            
            # Fall back to resolution detection from BACKGROUND
            width_match = re.search(
                r"BACKGROUND:.*?WIDTH\s*:\s*(\d+)",
                content,
                re.DOTALL,
            )
            height_match = re.search(
                r"BACKGROUND:.*?HEIGHT\s*:\s*(\d+)",
                content,
                re.DOTALL,
            )
            
            if width_match and height_match:
                w, h = int(width_match.group(1)), int(height_match.group(1))
                return self.RESOLUTION_TO_SIZE.get((w, h))
            
        except Exception:
            pass
        
        return None

    # ── Themes ───────────────────────────────────────────────

    def get_available_themes(self, filter_by_display: bool = True) -> List[str]:
        """
        List themes compatible with the current display.
        
        If filter_by_display is True (default), only returns themes
        that match the detected display size.
        """
        if not self.themes_dir.exists():
            return []
        
        display_size = self.get_display_size() if filter_by_display else None
        
        themes = []
        for d in self.themes_dir.iterdir():
            if not d.is_dir():
                continue
            if not (d / "theme.yaml").exists():
                continue
            
            # Skip special directories
            if d.name.startswith("--") or d.name.startswith("_"):
                continue
            
            # Filter by size if we know the display
            if display_size:
                theme_size = self._get_theme_size(d)
                # Include if: sizes match, or theme size is unknown (be permissive)
                if theme_size and theme_size != display_size:
                    continue
            
            themes.append(d.name)
        
        return sorted(themes)

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
