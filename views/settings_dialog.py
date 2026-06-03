"""앱 설정 다이얼로그 — 시작프로그램·업데이트 설정."""
import webbrowser
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QPushButton, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt

from core import updater
from utils import startup

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumWidth(380)
        self._checker = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── 시작프로그램 ──────────────────────────────────────────────
        startup_group = QGroupBox("시작프로그램")
        sl = QVBoxLayout(startup_group)
        self._chk_startup = QCheckBox("Windows 시작 시 자동 실행")
        sl.addWidget(self._chk_startup)
        layout.addWidget(startup_group)

        # ── 업데이트 ──────────────────────────────────────────────────
        update_group = QGroupBox("업데이트")
        ul = QHBoxLayout(update_group)
        self._lbl_version = QLabel(f"현재 버전: <b>{updater.APP_VERSION}</b>")
        self._btn_check = QPushButton("업데이트 확인")
        self._btn_check.setFixedWidth(110)
        ul.addWidget(self._lbl_version)
        ul.addStretch()
        ul.addWidget(self._btn_check)
        layout.addWidget(update_group)

        # ── 닫기 ─────────────────────────────────────────────────────
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        self._chk_startup.toggled.connect(self._on_startup_toggled)
        self._btn_check.clicked.connect(self._on_check_update)

    def _refresh(self):
        self._chk_startup.blockSignals(True)
        self._chk_startup.setChecked(startup.is_registered())
        self._chk_startup.blockSignals(False)

    def _on_startup_toggled(self, checked: bool):
        ok = startup.register() if checked else startup.unregister()
        if not ok:
            QMessageBox.warning(self, "오류", "시작프로그램 설정을 변경하지 못했습니다.")
            self._chk_startup.blockSignals(True)
            self._chk_startup.setChecked(not checked)
            self._chk_startup.blockSignals(False)

    def _on_check_update(self):
        self._btn_check.setEnabled(False)
        self._btn_check.setText("확인 중...")
        self.repaint()

        info = updater.check_for_update()

        self._btn_check.setEnabled(True)
        self._btn_check.setText("업데이트 확인")

        if info:
            reply = QMessageBox.question(
                self,
                "업데이트 있음",
                f"새 버전 <b>{info['version']}</b>이(가) 있습니다.<br>"
                "릴리즈 페이지를 열겠습니까?",
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open(info["html_url"])
                logger.info("릴리즈 페이지 열기: %s", info["html_url"])
        else:
            QMessageBox.information(self, "업데이트 확인", "현재 최신 버전입니다.")
