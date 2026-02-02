#!/usr/bin/env python3
"""
Turing Smart Screen — System Tray Application
Regata OS / openSUSE Edition

Entry point. Starts the PyQt5 event loop with the TuringTray icon.
"""

import sys
import os
import signal

# Ensure this module's directory is on the import path so that
# ``import tray_app``, ``import service_manager``, etc. work
# regardless of the current working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from tray_app import TuringTray


def main() -> int:
    # Allow Ctrl+C to kill the process cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Turing Smart Screen")
    app.setApplicationVersion(TuringTray.VERSION)
    app.setOrganizationName("RegataOS")
    app.setDesktopFileName("turing-smart-screen")

    # Prevent duplicate instances
    from PyQt5.QtNetwork import QLocalServer, QLocalSocket

    socket = QLocalSocket()
    socket.connectToServer("turing-smart-screen-tray")
    if socket.waitForConnected(200):
        # Another instance is already running
        print("Turing Smart Screen tray is already running.")
        socket.close()
        return 0
    socket.close()

    server = QLocalServer()
    server.removeServer("turing-smart-screen-tray")
    server.listen("turing-smart-screen-tray")

    tray = TuringTray(app)
    tray.show()

    ret = app.exec_()
    server.close()
    return ret


if __name__ == "__main__":
    sys.exit(main())
