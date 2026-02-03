"""
Turing Smart Screen — System Tray Application.

Sits in the KDE Plasma / GNOME panel and provides quick access to
start/stop/restart the display, switch themes, change orientation,
view logs, hardware info, and preferences.
"""

import os
import subprocess
import webbrowser
from pathlib import Path

from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QActionGroup,
    QMessageBox, QApplication,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from service_manager import ServiceManager
from config_manager import TrayConfig, ScreenConfig
from i18n import I18n


class TuringTray(QSystemTrayIcon):
    """System-tray icon that controls the Turing Smart Screen service."""

    GITHUB_URL = (
        "https://github.com/marquimRcc/"
        "turing-smart-screen-python-regataos-opensuse"
    )
    UPSTREAM_URL = "https://github.com/mathoudebine/turing-smart-screen-python"
    VERSION = "1.0.0"

    # ── Initialization ───────────────────────────────────────

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app

        # Paths — the layout is: <repo>/tray/tray_app.py
        self.script_dir = Path(__file__).resolve().parent          # tray/
        self.turing_dir = self.script_dir.parent                   # repo root
        self.icons_dir = self.turing_dir / "assets" / "icons"

        # Managers
        self.service = ServiceManager()
        self.tray_config = TrayConfig()
        self.screen_config = ScreenConfig(str(self.turing_dir))
        self.i18n = I18n(self.tray_config.get("language", "pt_BR"))

        # Load icons
        self._init_icons()

        # Build context menu
        self._build_menu()

        # Periodic status check
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._update_status)
        self._poll_timer.start(self.tray_config.get("poll_interval", 5) * 1000)

        # Initial status
        self._update_status()

        # Click handler
        self.activated.connect(self._on_activated)

    # ── Icons ────────────────────────────────────────────────

    def _init_icons(self):
        def _load(name: str, fallback_theme: str) -> QIcon:
            path = self.icons_dir / name
            icon = QIcon(str(path)) if path.exists() else QIcon()
            return icon if not icon.isNull() else QIcon.fromTheme(fallback_theme)

        self.icon_running = _load("turing-tray-running.svg", "video-display")
        self.icon_stopped = _load("turing-tray-stopped.svg", "video-display")
        self.icon_error = _load("turing-tray-error.svg", "dialog-error")

    # ── Menu construction ────────────────────────────────────

    def _build_menu(self):
        t = self.i18n.t
        menu = QMenu()

        # Header
        hdr = menu.addAction("Turing Smart Screen")
        hdr.setEnabled(False)
        font = hdr.font()
        font.setBold(True)
        hdr.setFont(font)

        # Display info line (revision + size)
        revision = self.screen_config.get_display_revision()
        size = self.screen_config.get_display_size()
        if revision or size:
            info_parts = []
            if revision:
                info_parts.append(f"Rev. {revision}")
            if size:
                info_parts.append(f'{size}"')
            info_text = f"  📺 {' · '.join(info_parts)}"
            info_action = menu.addAction(info_text)
            info_action.setEnabled(False)

        menu.addSeparator()

        # ── Control ──────────────────────────────────────────
        self.act_start = menu.addAction(
            QIcon.fromTheme("media-playback-start"), t("menu.start"))
        self.act_start.triggered.connect(self.start_display)

        self.act_stop = menu.addAction(
            QIcon.fromTheme("media-playback-stop"), t("menu.stop"))
        self.act_stop.triggered.connect(self.stop_display)

        self.act_restart = menu.addAction(
            QIcon.fromTheme("view-refresh"), t("menu.restart"))
        self.act_restart.triggered.connect(self.restart_display)

        menu.addSeparator()

        # ── Themes ───────────────────────────────────────────
        self.themes_menu = menu.addMenu(
            QIcon.fromTheme("preferences-desktop-theme"), t("menu.themes"))
        self._populate_themes()
        # Refresh theme list every time submenu opens (catches configure.py changes)
        self.themes_menu.aboutToShow.connect(self._populate_themes)

        # ── Orientation ──────────────────────────────────────
        orient_menu = menu.addMenu(
            QIcon.fromTheme("object-rotate-right"), t("menu.orientation"))
        orient_group = QActionGroup(self)
        current_orient = self.screen_config.get_orientation()
        orient_labels = {0: "0° (Normal)", 1: "90°", 2: "180°", 3: "270°"}
        for val, label in orient_labels.items():
            act = orient_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(val == current_orient)
            act.triggered.connect(lambda _checked, v=val: self.set_orientation(v))
            orient_group.addAction(act)

        menu.addSeparator()

        # ── Configuration ────────────────────────────────────
        act_wizard = menu.addAction(
            QIcon.fromTheme("configure"), t("menu.configure"))
        act_wizard.triggered.connect(self.open_configurator)

        act_edit = menu.addAction(
            QIcon.fromTheme("document-edit"), t("menu.edit_config"))
        act_edit.triggered.connect(self.edit_config)

        act_prefs = menu.addAction(
            QIcon.fromTheme("preferences-system"), t("menu.preferences"))
        act_prefs.triggered.connect(self.show_preferences)

        menu.addSeparator()

        # ── Autostart ────────────────────────────────────────
        self.act_autostart = menu.addAction(
            QIcon.fromTheme("system-run"), t("menu.autostart"))
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(self.service.is_enabled())
        self.act_autostart.triggered.connect(self.toggle_autostart)

        menu.addSeparator()

        # ── Language ─────────────────────────────────────────
        lang_menu = menu.addMenu(
            QIcon.fromTheme("preferences-desktop-locale"), t("menu.language"))
        lang_group = QActionGroup(self)
        current_lang = self.tray_config.get("language", "pt_BR")
        for code, name in self.i18n.supported_languages.items():
            act = lang_menu.addAction(name)
            act.setCheckable(True)
            act.setChecked(code == current_lang)
            act.triggered.connect(lambda _checked, c=code: self.set_language(c))
            lang_group.addAction(act)

        menu.addSeparator()

        # ── Info ─────────────────────────────────────────────
        act_hw = menu.addAction(
            QIcon.fromTheme("hwinfo"), t("menu.hardware_info"))
        act_hw.triggered.connect(self.show_hardware_info)

        act_logs = menu.addAction(
            QIcon.fromTheme("text-x-log"), t("menu.view_logs"))
        act_logs.triggered.connect(self.view_logs)

        menu.addSeparator()

        act_support = menu.addAction(
            QIcon.fromTheme("help-contents"), t("menu.support"))
        act_support.triggered.connect(lambda: webbrowser.open(self.GITHUB_URL))

        act_about = menu.addAction(
            QIcon.fromTheme("help-about"), t("menu.about"))
        act_about.triggered.connect(self.show_about)

        menu.addSeparator()

        # ── Quit ─────────────────────────────────────────────
        act_quit = menu.addAction(
            QIcon.fromTheme("application-exit"), t("menu.quit"))
        act_quit.triggered.connect(self.quit_app)

        self.setContextMenu(menu)

    def _populate_themes(self):
        self.themes_menu.clear()
        themes = self.screen_config.get_available_themes()
        current = self.screen_config.get_current_theme()

        if not themes:
            empty = self.themes_menu.addAction(self.i18n.t("menu.no_themes"))
            empty.setEnabled(False)
            return

        group = QActionGroup(self)
        for theme in themes:
            act = self.themes_menu.addAction(theme)
            act.setCheckable(True)
            act.setChecked(theme == current)
            act.triggered.connect(
                lambda _checked, th=theme: self.set_theme(th))
            group.addAction(act)

    # ═══════════════════════════════════════════════════════════
    # Actions
    # ═══════════════════════════════════════════════════════════

    # ── Display control ──────────────────────────────────────

    def start_display(self):
        t = self.i18n.t
        if self.service.start():
            self._notify(t("notify.started"), t("notify.started_msg"))
        else:
            self._notify(t("notify.error"), t("notify.start_failed"),
                         QSystemTrayIcon.Critical)
        self._update_status()

    def stop_display(self):
        t = self.i18n.t
        if self.service.stop():
            self._notify(t("notify.stopped"), t("notify.stopped_msg"))
        else:
            self._notify(t("notify.error"), t("notify.stop_failed"),
                         QSystemTrayIcon.Critical)
        self._update_status()

    def restart_display(self):
        t = self.i18n.t
        if self.service.restart():
            self._notify(t("notify.restarted"), t("notify.restarted_msg"))
        else:
            self._notify(t("notify.error"), t("notify.restart_failed"),
                         QSystemTrayIcon.Critical)
        self._update_status()

    # ── Theme & orientation ──────────────────────────────────

    def set_theme(self, theme_name: str):
        t = self.i18n.t
        try:
            if self.screen_config.set_theme(theme_name):
                self._populate_themes()
                self._notify(t("notify.theme_applied"),
                             t("notify.theme_applied_msg", theme_name))
                if self.service.is_active():
                    reply = QMessageBox.question(
                        None, t("dialog.theme_changed"),
                        t("dialog.theme_restart_prompt"),
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.Yes:
                        self.restart_display()
        except Exception as exc:
            self._notify(t("notify.error"), str(exc),
                         QSystemTrayIcon.Critical)

    def set_orientation(self, value: int):
        t = self.i18n.t
        try:
            if self.screen_config.set_orientation(value):
                if self.service.is_active():
                    reply = QMessageBox.question(
                        None, t("dialog.orientation_changed"),
                        t("dialog.orientation_restart_prompt"),
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.Yes:
                        self.restart_display()
        except Exception as exc:
            self._notify(t("notify.error"), str(exc),
                         QSystemTrayIcon.Critical)

    # ── Configurator & editor ────────────────────────────────

    def open_configurator(self):
        venv_py = self.turing_dir / "venv" / "bin" / "python3.11"
        configure = self.turing_dir / "configure.py"
        if configure.exists() and venv_py.exists():
            subprocess.Popen(
                [str(venv_py), str(configure)],
                cwd=str(self.turing_dir),
            )
        else:
            QMessageBox.warning(
                None,
                self.i18n.t("dialog.error"),
                self.i18n.t("dialog.configurator_not_found"),
            )

    def edit_config(self):
        cfg = self.screen_config.config_file
        if cfg.exists():
            subprocess.Popen(["xdg-open", str(cfg)])
        else:
            QMessageBox.warning(
                None,
                self.i18n.t("dialog.error"),
                self.i18n.t("dialog.config_not_found"),
            )

    # ── Preferences ──────────────────────────────────────────

    def show_preferences(self):
        from dialogs.settings import SettingsDialog

        dlg = SettingsDialog(self.tray_config, self.i18n)
        if dlg.exec_():
            # Apply changes that take immediate effect
            new_lang = self.tray_config.get("language")
            if new_lang != self.i18n.language:
                self.set_language(new_lang)
            # Update poll timer
            interval = self.tray_config.get("poll_interval", 5) * 1000
            self._poll_timer.setInterval(interval)

    # ── Autostart ────────────────────────────────────────────

    def toggle_autostart(self):
        t = self.i18n.t
        if self.act_autostart.isChecked():
            if self.service.enable():
                self._notify(t("notify.autostart"), t("notify.autostart_enabled"))
            else:
                self.act_autostart.setChecked(False)
                self._notify(t("notify.error"), t("notify.autostart_failed"),
                             QSystemTrayIcon.Critical)
        else:
            if self.service.disable():
                self._notify(t("notify.autostart"), t("notify.autostart_disabled"))
            else:
                self.act_autostart.setChecked(True)

    # ── Language ─────────────────────────────────────────────

    def set_language(self, lang_code: str):
        self.tray_config.set("language", lang_code)
        self.i18n.set_language(lang_code)
        self._build_menu()
        self._update_status()

    # ── Dialogs ──────────────────────────────────────────────

    def show_hardware_info(self):
        from dialogs.hardware_info import HardwareInfoDialog
        HardwareInfoDialog(self.i18n).exec_()

    def view_logs(self):
        from dialogs.log_viewer import LogViewerDialog

        def _get_logs():
            text = self.service.journal(200)
            return text if text else self.i18n.t("dialog.no_logs")

        LogViewerDialog(
            initial_text=_get_logs(),
            i18n=self.i18n,
            refresh_callback=_get_logs,
        ).exec_()

    def show_about(self):
        from dialogs.about import AboutDialog
        AboutDialog(
            version=self.VERSION,
            github_url=self.GITHUB_URL,
            upstream_url=self.UPSTREAM_URL,
            i18n=self.i18n,
        ).exec_()

    # ═══════════════════════════════════════════════════════════
    # Status
    # ═══════════════════════════════════════════════════════════

    def _update_status(self):
        t = self.i18n.t
        active = self.service.is_active()

        if active:
            self.setIcon(self.icon_running)
            self.setToolTip(f"Turing Smart Screen — {t('status.running')}")
            self.act_start.setEnabled(False)
            self.act_stop.setEnabled(True)
            self.act_restart.setEnabled(True)
        else:
            self.setIcon(self.icon_stopped)
            self.setToolTip(f"Turing Smart Screen — {t('status.stopped')}")
            self.act_start.setEnabled(True)
            self.act_stop.setEnabled(False)
            self.act_restart.setEnabled(False)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.MiddleClick:
            # Middle-click toggles start/stop
            if self.service.is_active():
                self.stop_display()
            else:
                self.start_display()

    def _notify(self, title: str, message: str,
                icon=QSystemTrayIcon.Information):
        if self.tray_config.get("show_notifications", True):
            self.showMessage(title, message, icon, 3000)

    # ── Quit ─────────────────────────────────────────────────

    def quit_app(self):
        """Quit the tray — does NOT stop the display service."""
        self.hide()
        QApplication.quit()
