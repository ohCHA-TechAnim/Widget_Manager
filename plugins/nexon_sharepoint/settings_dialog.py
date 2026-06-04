"""SharePoint 플러그인 설정 다이얼로그.

nexon_id, library_url, sheet_name, target_name, file_keyword, enabled 를 관리한다.
비밀번호는 보안상 여기에 저장하지 않는다 (가져오기 실행 시마다 입력).
"""
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QCheckBox, QHBoxLayout, QPushButton, QLabel, QGroupBox,
)

logger = logging.getLogger(__name__)

_PLUGIN_NAME = "nexon_sharepoint"


class SharePointSettingsDialog(QDialog):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self.setWindowTitle("SharePoint 설정")
        self.setMinimumWidth(440)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── 활성화 ────────────────────────────────────────────────────────
        en_group = QGroupBox("플러그인 활성화")
        el = QVBoxLayout(en_group)
        self._chk_enabled = QCheckBox("SharePoint 일정 가져오기 활성화")
        el.addWidget(self._chk_enabled)
        hint = QLabel(
            "OFF 시 플러그인 메뉴에서 '가져오기' 항목이 숨겨집니다.\n"
            "코어 기능(손입력 일정·테마·오버레이)은 영향받지 않습니다."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 8pt;")
        el.addWidget(hint)
        layout.addWidget(en_group)

        # ── 계정 / 연결 정보 ──────────────────────────────────────────────
        cn_group = QGroupBox("계정 / 연결 정보")
        cl = QFormLayout(cn_group)

        self._nexon_id = QLineEdit()
        self._nexon_id.setPlaceholderText("예: user@nexon.com")
        cl.addRow("넥슨 ID (이메일):", self._nexon_id)

        pw_note = QLabel(
            "비밀번호는 저장하지 않습니다 — 보안 정책 준수.\n"
            "'가져오기' 실행 시마다 팝업으로 입력합니다."
        )
        pw_note.setWordWrap(True)
        pw_note.setStyleSheet("color: #aaa; font-size: 8pt;")
        cl.addRow(pw_note)

        self._library_url = QLineEdit()
        self._library_url.setPlaceholderText(
            "예: https://nexon.sharepoint.com/sites/anim/Shared%20Documents"
        )
        cl.addRow("라이브러리 URL:", self._library_url)

        self._file_keyword = QLineEdit()
        self._file_keyword.setPlaceholderText("예: 스케쥴_애니메이션팀(2026)")
        cl.addRow("파일 검색어:", self._file_keyword)

        self._sheet_name = QLineEdit()
        self._sheet_name.setPlaceholderText("예: 애니메이션")
        cl.addRow("시트명:", self._sheet_name)

        self._target_name = QLineEdit()
        self._target_name.setPlaceholderText("예: 차승현")
        cl.addRow("대상자 이름:", self._target_name)

        layout.addWidget(cn_group)

        # ── 버튼 ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("저장")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load(self):
        g = lambda k, d: self._ctx.get_plugin_setting(_PLUGIN_NAME, k, d)
        self._chk_enabled.setChecked(g("enabled", False))
        self._nexon_id.setText(g("nexon_id", ""))
        self._library_url.setText(g("library_url", ""))
        self._file_keyword.setText(g("file_keyword", "스케쥴_애니메이션팀(2026)"))
        self._sheet_name.setText(g("sheet_name", "애니메이션"))
        self._target_name.setText(g("target_name", ""))

    def _on_save(self):
        s = lambda k, v: self._ctx.set_plugin_setting(_PLUGIN_NAME, k, v)
        s("enabled", self._chk_enabled.isChecked())
        s("nexon_id", self._nexon_id.text().strip())
        s("library_url", self._library_url.text().strip())
        s("file_keyword", self._file_keyword.text().strip() or "스케쥴_애니메이션팀(2026)")
        s("sheet_name", self._sheet_name.text().strip() or "애니메이션")
        s("target_name", self._target_name.text().strip())
        logger.info("SharePoint 설정 저장 완료")
        self.accept()
