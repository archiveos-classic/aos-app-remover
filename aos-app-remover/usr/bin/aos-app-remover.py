#!/usr/bin/env python3
import sys
import subprocess
import os
import locale
import apt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox,
    QProgressBar, QScrollArea
)

from PyQt6.QtCore import Qt, QProcess, QTimer, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon

# --- DOSYA YOLLARI ---
LOGO_FILE = "/usr/bin/aos-app-remover-logo.png"


def get_lang():
    try:
        lang = locale.getdefaultlocale()[0]

        if lang and lang.startswith("tr"):
            return "tr"

        return "en"

    except:
        return "en"


LANG = get_lang()

STRINGS = {
    "tr": {
        "title": "ArchiveOS Uygulama Silici",
        "search_hint": "Uygulama ara (Flatpak, Snap, APT)...",
        "uninstall_btn": "Uygulamayı Kaldır",
        "refresh_btn": "Yenile",
        "loading": "Uygulamalar taranıyor...",
        "removing": "Siliniyor: {}",
        "success": "Başarıyla kaldırıldı!",
        "error": "İşlem başarısız!",
        "confirm": "{} uygulamasını tamamen kaldırmak istediğine emin misin?",
        "logs": "İşlem Logları:",
        "listed": "Toplam {} uygulama listelendi."
    },

    "en": {
        "title": "ArchiveOS Uninstaller",
        "search_hint": "Search apps (Flatpak, Snap, APT)...",
        "uninstall_btn": "Uninstall App",
        "refresh_btn": "Refresh",
        "loading": "Scanning apps...",
        "removing": "Removing: {}",
        "success": "Removed successfully!",
        "error": "Operation failed!",
        "confirm": "Are you sure you want to completely remove {}?",
        "logs": "Process Logs:",
        "listed": "Total {} applications listed."
    }
}


class ArchiveOSUninstaller(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            STRINGS[LANG]["title"]
        )

        self.setFixedSize(700, 800)

        self.process = QProcess()

        # PENCERE + GÖREV ÇUBUĞU İKONU
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))

        self.init_ui()
        self.apply_styles()

        self.process.readyReadStandardOutput.connect(
            self.handle_stdout
        )

        self.process.readyReadStandardError.connect(
            self.handle_stderr
        )

        self.process.finished.connect(
            self.process_finished
        )

        QTimer.singleShot(500, self.load_apps)

    def init_ui(self):

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(
            self.central_widget
        )

        self.layout.setContentsMargins(
            25, 25, 25, 25
        )

        # HEADER
        header = QHBoxLayout()

        self.lbl_logo = QLabel()

        if os.path.exists(LOGO_FILE):

            pixmap = QPixmap(LOGO_FILE)

            # SOL ÜST LOGO
            self.lbl_logo.setPixmap(
                pixmap.scaled(
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            # PENCERE + GÖREV ÇUBUĞU İKONU
            self.setWindowIcon(QIcon(pixmap))

        header.addWidget(self.lbl_logo)

        self.lbl_title = QLabel(
            STRINGS[LANG]["title"]
        )

        self.lbl_title.setFont(
            QFont(
                "Sans",
                22,
                QFont.Weight.Bold
            )
        )

        header.addWidget(self.lbl_title)

        header.addStretch()

        self.layout.addLayout(header)

        # SEARCH
        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            STRINGS[LANG]["search_hint"]
        )

        self.search_box.textChanged.connect(
            self.filter_apps
        )

        self.layout.addWidget(self.search_box)

        # APP LIST
        self.pkg_list = QListWidget()

        self.pkg_list.setIconSize(
            QSize(40, 40)
        )

        self.layout.addWidget(self.pkg_list)

        # LOGS
        self.txt_logs = QLabel("")

        self.txt_logs.setWordWrap(True)

        self.log_scroll = QScrollArea()

        self.log_scroll.setFixedHeight(100)

        self.log_scroll.setWidget(
            self.txt_logs
        )

        self.log_scroll.setWidgetResizable(True)

        self.layout.addWidget(self.log_scroll)

        # PROGRESS
        self.progress_bar = QProgressBar()

        self.progress_bar.setVisible(False)

        self.layout.addWidget(self.progress_bar)

        # BUTTONS
        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton(
            STRINGS[LANG]["refresh_btn"]
        )

        self.btn_refresh.setFixedSize(120, 50)

        self.btn_refresh.clicked.connect(
            self.load_apps
        )

        self.btn_uninstall = QPushButton(
            STRINGS[LANG]["uninstall_btn"]
        )

        self.btn_uninstall.setFixedSize(250, 50)

        self.btn_uninstall.setObjectName(
            "BlueButton"
        )

        self.btn_uninstall.clicked.connect(
            self.confirm_uninstall
        )

        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()

        btn_layout.addWidget(self.btn_uninstall)

        self.layout.addLayout(btn_layout)

    def apply_styles(self):

        self.setStyleSheet("""

            QMainWindow {
                background-color: #080808;
            }

            QLabel {
                color: #f0f0f0;
            }

            QLineEdit {
                background: #121212;
                color: white;
                border: 1px solid #333;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
            }

            QListWidget {
                background: #121212;
                color: #eee;
                border: 1px solid #1a1a1a;
                border-radius: 10px;
                padding: 5px;
            }

            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #1a1a1a;
            }

            QListWidget::item:selected {
                background: #0078d4;
                color: white;
                border-radius: 6px;
            }

            QScrollArea {
                background: #050505;
                border: 1px solid #222;
                border-radius: 8px;
            }

            #BlueButton {
                background: #0078d4;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 15px;
            }

            #BlueButton:hover {
                background: #0086ed;
            }

            QPushButton {
                background: #1a1a1a;
                color: white;
                border: 1px solid #3daee9;
                border-radius: 10px;
            }

            QProgressBar {
                border: 1px solid #333;
                height: 8px;
                background: #111;
                border-radius: 4px;
            }

            QProgressBar::chunk {
                background-color: #00aaff;
            }

        """)

    def get_icon(self, name, source):

        if source == "flatpak":

            return QIcon.fromTheme(
                name.split('.')[-1].lower()
            ) or QIcon.fromTheme(
                "package-x-generic"
            )

        return QIcon.fromTheme(
            name.lower()
        ) or QIcon.fromTheme(
            "package-x-generic"
        )

    def load_apps(self):

        self.pkg_list.clear()

        self.txt_logs.setText(
            STRINGS[LANG]["loading"]
        )

        # FLATPAK
        try:

            fps = subprocess.check_output(
                "flatpak list --app --columns=application,name",
                shell=True,
                text=True
            )

            for line in fps.strip().split('\n'):

                if line:

                    app_id, name = line.split('\t')

                    item = QListWidgetItem(
                        f"{name} (Flatpak)"
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        {
                            "id": app_id,
                            "type": "flatpak"
                        }
                    )

                    item.setIcon(
                        self.get_icon(
                            app_id,
                            "flatpak"
                        )
                    )

                    self.pkg_list.addItem(item)

        except Exception as e:
            print("Flatpak error:", e)

        # SNAP
        try:

            snaps = subprocess.check_output(
                "snap list",
                shell=True,
                text=True
            )

            for line in snaps.strip().split('\n')[1:]:

                parts = line.split()

                if len(parts) >= 1:

                    name = parts[0]

                    item = QListWidgetItem(
                        f"{name} (Snap)"
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        {
                            "id": name,
                            "type": "snap"
                        }
                    )

                    item.setIcon(
                        self.get_icon(
                            name,
                            "snap"
                        )
                    )

                    self.pkg_list.addItem(item)

        except Exception as e:
            print("Snap error:", e)

        # APT
        try:

            cache = apt.Cache()

            added = set()

            for pkg in cache:

                try:

                    if pkg.is_installed:

                        if pkg.name.startswith((
                            "lib",
                            "fonts-",
                            "linux-",
                            "gir1.2",
                            "mesa-",
                            "xserver-"
                        )):
                            continue

                        installed = pkg.installed

                        if not installed:
                            continue

                        summary = installed.summary.lower()

                        keywords = [
                            "application",
                            "app",
                            "tool",
                            "browser",
                            "editor",
                            "viewer",
                            "game",
                            "player",
                            "client",
                            "desktop"
                        ]

                        if any(
                            k in summary
                            for k in keywords
                        ):

                            if pkg.name not in added:

                                added.add(pkg.name)

                                item = QListWidgetItem(
                                    f"{pkg.name} (APT)"
                                )

                                item.setData(
                                    Qt.ItemDataRole.UserRole,
                                    {
                                        "id": pkg.name,
                                        "type": "apt"
                                    }
                                )

                                item.setIcon(
                                    self.get_icon(
                                        pkg.name,
                                        "apt"
                                    )
                                )

                                self.pkg_list.addItem(item)

                except:
                    pass

        except Exception as e:
            print("APT error:", e)

        self.txt_logs.setText(
            STRINGS[LANG]["listed"].format(
                self.pkg_list.count()
            )
        )

    def filter_apps(self, text):

        for i in range(
            self.pkg_list.count()
        ):

            item = self.pkg_list.item(i)

            item.setHidden(
                text.lower()
                not in item.text().lower()
            )

    def confirm_uninstall(self):

        selected = self.pkg_list.currentItem()

        if not selected:
            return

        data = selected.data(
            Qt.ItemDataRole.UserRole
        )

        ans = QMessageBox.question(
            self,
            "ArchiveOS",
            STRINGS[LANG]["confirm"].format(
                selected.text()
            )
        )

        if ans == QMessageBox.StandardButton.Yes:
            self.start_removal(data)

    def start_removal(self, data):

        self.btn_uninstall.setEnabled(False)

        self.progress_bar.setVisible(True)

        self.progress_bar.setRange(0, 0)

        if data["type"] == "flatpak":

            self.process.start(
                "flatpak",
                [
                    "uninstall",
                    "-y",
                    data["id"]
                ]
            )

        elif data["type"] == "snap":

            self.process.start(
                "pkexec",
                [
                    "snap",
                    "remove",
                    data["id"]
                ]
            )

        else:

            self.process.start(
                "pkexec",
                [
                    "apt",
                    "purge",
                    "-y",
                    data["id"]
                ]
            )

    def handle_stdout(self):

        data = self.process.readAllStandardOutput().data().decode()

        self.append_log(data)

    def handle_stderr(self):

        data = self.process.readAllStandardError().data().decode()

        self.append_log(
            f"<span style='color:red;'>{data}</span>"
        )

    def append_log(self, text):

        self.txt_logs.setText(
            self.txt_logs.text()
            + "<br>"
            + text.replace("\n", "<br>")
        )

    def process_finished(self, exit_code):

        self.progress_bar.setRange(0, 100)

        self.progress_bar.setValue(100)

        if exit_code == 0:

            QMessageBox.information(
                self,
                "ArchiveOS",
                STRINGS[LANG]["success"]
            )

            self.load_apps()

        else:

            QMessageBox.warning(
                self,
                "ArchiveOS",
                STRINGS[LANG]["error"]
            )

        self.btn_uninstall.setEnabled(True)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = ArchiveOSUninstaller()

    win.show()

    sys.exit(app.exec())
