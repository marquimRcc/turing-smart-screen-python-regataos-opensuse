"""Log viewer dialog — shows journalctl output for the service."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Callable, Optional


class LogViewerDialog(QDialog):
    def __init__(
        self,
        initial_text: str,
        i18n,
        refresh_callback: Optional[Callable[[], str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._refresh_cb = refresh_callback
        self.i18n = i18n
        t = i18n.t

        self.setWindowTitle(t("logs.title"))
        self.setMinimumSize(720, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # ── Text area ────────────────────────────────────────
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Monospace", 9))
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit)

        # Scroll to bottom
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        self.text_edit.setTextCursor(cursor)

        # ── Buttons ──────────────────────────────────────────
        btn_row = QHBoxLayout()

        btn_refresh = QPushButton(t("logs.refresh"))
        btn_refresh.clicked.connect(self._refresh)
        btn_row.addWidget(btn_refresh)

        btn_copy = QPushButton(t("logs.copy"))
        btn_copy.clicked.connect(self._copy)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()

        btn_close = QPushButton(t("logs.close"))
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def _refresh(self):
        if self._refresh_cb:
            text = self._refresh_cb()
            self.text_edit.setPlainText(text)
            cursor = self.text_edit.textCursor()
            cursor.movePosition(cursor.End)
            self.text_edit.setTextCursor(cursor)

    def _copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
