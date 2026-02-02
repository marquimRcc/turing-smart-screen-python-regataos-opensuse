"""Preferences dialog for tray application settings."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton,
    QComboBox, QGroupBox, QFormLayout,
    QSpinBox, QMessageBox,
)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """Preferences dialog — modifies TrayConfig values."""

    def __init__(self, tray_config, i18n, parent=None):
        super().__init__(parent)
        self.tray_config = tray_config
        self.i18n = i18n
        t = i18n.t

        self.setWindowTitle(t("settings.title"))
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 16, 20, 16)

        # ── General ─────────────────────────────────────────
        grp_general = QGroupBox(t("settings.general"))
        form_general = QFormLayout()
        form_general.setSpacing(10)

        # Language selector
        self.combo_lang = QComboBox()
        for code, name in i18n.supported_languages.items():
            self.combo_lang.addItem(name, code)
        idx = self.combo_lang.findData(tray_config.get("language", "pt_BR"))
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        form_general.addRow(t("settings.language"), self.combo_lang)

        # Notifications toggle
        self.chk_notifications = QCheckBox()
        self.chk_notifications.setChecked(tray_config.get("show_notifications", True))
        form_general.addRow(t("settings.notifications"), self.chk_notifications)

        # Check updates toggle
        self.chk_updates = QCheckBox()
        self.chk_updates.setChecked(tray_config.get("check_updates", True))
        form_general.addRow(t("settings.check_updates"), self.chk_updates)

        grp_general.setLayout(form_general)
        layout.addWidget(grp_general)

        # ── Display ─────────────────────────────────────────
        grp_display = QGroupBox(t("settings.display"))
        form_display = QFormLayout()
        form_display.setSpacing(10)

        # Poll interval
        self.spin_poll = QSpinBox()
        self.spin_poll.setRange(2, 60)
        self.spin_poll.setSuffix(" s")
        self.spin_poll.setValue(tray_config.get("poll_interval", 5))
        form_display.addRow(t("settings.poll_interval"), self.spin_poll)

        grp_display.setLayout(form_display)
        layout.addWidget(grp_display)

        layout.addStretch()

        # ── Buttons ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_save = QPushButton(t("settings.save"))
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton(t("settings.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)

    def _save(self):
        self.tray_config.set("language", self.combo_lang.currentData())
        self.tray_config.set("show_notifications", self.chk_notifications.isChecked())
        self.tray_config.set("check_updates", self.chk_updates.isChecked())
        self.tray_config.set("poll_interval", self.spin_poll.value())

        QMessageBox.information(
            self,
            self.i18n.t("settings.title"),
            self.i18n.t("settings.saved"),
        )
        self.accept()
