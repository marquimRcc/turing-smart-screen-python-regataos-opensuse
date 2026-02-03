"""
Internationalization (i18n) module for Turing Smart Screen Tray.
Supports pt_BR and en_US with fallback to English.
"""

import json
from pathlib import Path
from typing import Any


class I18n:
    """Simple JSON-based translation manager."""

    SUPPORTED = {
        "pt_BR": "Português (Brasil)",
        "pt_PT": "Português (Portugal)",
        "en_US": "English (US)",
        "es_ES": "Español",
    }

    def __init__(self, language: str = "pt_BR"):
        self._lang_dir = Path(__file__).parent
        self._fallback: dict[str, str] = {}
        self._translations: dict[str, str] = {}
        self._load_fallback()
        self.set_language(language)

    # ── Loading ──────────────────────────────────────────────

    def _load_file(self, lang_code: str) -> dict[str, str]:
        path = self._lang_dir / f"{lang_code}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return {}

    def _load_fallback(self):
        self._fallback = self._load_file("en_US")

    def set_language(self, language: str):
        if language not in self.SUPPORTED:
            language = "en_US"
        self._lang = language
        self._translations = self._load_file(language)

    # ── Translation ──────────────────────────────────────────

    def t(self, key: str, *args: Any) -> str:
        """
        Get translated string for *key*.

        Supports ``str.format`` positional arguments::

            i18n.t("notify.theme_applied_msg", "MyTheme")
            # → "Theme 'MyTheme' applied successfully."
        """
        text = self._translations.get(key, self._fallback.get(key, key))
        if args:
            try:
                text = text.format(*args)
            except (IndexError, KeyError):
                pass
        return text

    # ── Helpers ──────────────────────────────────────────────

    @property
    def language(self) -> str:
        return self._lang

    @property
    def supported_languages(self) -> dict[str, str]:
        return dict(self.SUPPORTED)
