"""About dialog showing project information and links."""

import webbrowser

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap


class AboutDialog(QDialog):
    def __init__(self, version, github_url, upstream_url, i18n, parent=None):
        super().__init__(parent)
        t = i18n.t

        self.setWindowTitle(t("about.title"))
        self.setFixedSize(440, 430)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # ── Title ────────────────────────────────────────────
        title = QLabel("Turing Smart Screen")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Subtitle ────────────────────────────────────────
        subtitle = QLabel(t("about.subtitle"))
        sub_font = QFont()
        sub_font.setPointSize(10)
        subtitle.setFont(sub_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        # ── Version ─────────────────────────────────────────
        ver_label = QLabel(f"{t('about.version')}: {version}")
        ver_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver_label)

        # ── Separator ───────────────────────────────────────
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #444;")
        layout.addWidget(sep)

        # ── Description ─────────────────────────────────────
        desc = QLabel(t("about.description"))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("padding: 8px;")
        layout.addWidget(desc)

        # ── Credits ────────────────────────────────────────
        credits_label = QLabel(t("about.credits"))
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet("color: #4a9eff; font-size: 11px; font-weight: bold; padding: 8px;")
        layout.addWidget(credits_label)

        # ── License ─────────────────────────────────────────
        license_label = QLabel(t("about.license"))
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(license_label)

        layout.addStretch()

        # ── Link buttons ────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_fork = QPushButton(t("about.github"))
        btn_fork.setCursor(Qt.PointingHandCursor)
        btn_fork.clicked.connect(lambda: webbrowser.open(github_url))
        btn_row.addWidget(btn_fork)

        btn_orig = QPushButton(t("about.upstream"))
        btn_orig.setCursor(Qt.PointingHandCursor)
        btn_orig.clicked.connect(lambda: webbrowser.open(upstream_url))
        btn_row.addWidget(btn_orig)

        layout.addLayout(btn_row)

        # ── Close ───────────────────────────────────────────
        btn_close = QPushButton(t("about.close"))
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)