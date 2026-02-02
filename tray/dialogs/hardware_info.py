"""Hardware information dialog — GPU, sensors, USB devices."""

import subprocess

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class HardwareInfoDialog(QDialog):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        t = i18n.t

        self.setWindowTitle(t("hardware.title"))
        self.setMinimumSize(560, 440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # ── Title ────────────────────────────────────────────
        title = QLabel(t("hardware.title"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # ── Info area ────────────────────────────────────────
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Monospace", 9))
        layout.addWidget(self.text_area)

        # ── Buttons ──────────────────────────────────────────
        btn_row = QHBoxLayout()

        btn_refresh = QPushButton(t("hardware.refresh"))
        btn_refresh.clicked.connect(self._refresh)
        btn_row.addWidget(btn_refresh)

        btn_copy = QPushButton(t("hardware.copy"))
        btn_copy.clicked.connect(self._copy)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()

        btn_close = QPushButton(t("hardware.close"))
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

        # Initial load
        self._refresh()

    # ── Data gathering ───────────────────────────────────────

    @staticmethod
    def _cmd(args: list[str], timeout: int = 5) -> str:
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip() if r.stdout else ""
        except FileNotFoundError:
            return ""
        except subprocess.TimeoutExpired:
            return "(timeout)"
        except Exception as exc:
            return f"(error: {exc})"

    def _gather(self) -> str:
        t = self.i18n.t
        sections: list[str] = []

        # GPU
        sections.append(f"{'═' * 20} {t('hardware.gpu')} {'═' * 20}")
        lspci = self._cmd(["lspci"])
        if lspci:
            gpu_lines = [
                ln for ln in lspci.splitlines()
                if any(k in ln.lower() for k in ("vga", "3d", "display"))
            ]
            sections.append("\n".join(gpu_lines) if gpu_lines else t("hardware.not_detected"))
        else:
            sections.append(t("hardware.detection_error"))

        sections.append("")

        # Sensors
        sections.append(f"{'═' * 20} {t('hardware.sensors')} {'═' * 20}")
        sensors_out = self._cmd(["sensors"])
        sections.append(sensors_out if sensors_out else t("hardware.sensors_not_available"))

        sections.append("")

        # USB
        sections.append(f"{'═' * 20} {t('hardware.usb')} {'═' * 20}")
        usb_out = self._cmd(["lsusb"])
        sections.append(usb_out if usb_out else t("hardware.usb_not_available"))

        return "\n".join(sections)

    # ── Actions ──────────────────────────────────────────────

    def _refresh(self):
        self.text_area.setPlainText(self._gather())

    def _copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_area.toPlainText())
