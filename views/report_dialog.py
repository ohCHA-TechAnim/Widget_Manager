# -*- coding: utf-8 -*-
"""
views/report_dialog.py
~~~~~~~~~~~~~~~~~~~~~~
성과보고서 생성 다이얼로그. utils.report_generator 사용.
"""

import logging
from datetime import date as _date

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QComboBox, QLineEdit,
    QDialogButtonBox, QMessageBox, QLabel,
)

logger = logging.getLogger(__name__)


class ReportDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.setWindowTitle("성과보고서 생성")
        self.setMinimumWidth(340)
        self._store = store
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._year_spin = QSpinBox()
        self._year_spin.setRange(2020, 2099)
        self._year_spin.setValue(_date.today().year)
        layout.addRow("연도:", self._year_spin)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["연간", "분기별"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        layout.addRow("기간 유형:", self._mode_combo)

        self._quarter_label = QLabel("분기:")
        self._quarter_combo = QComboBox()
        self._quarter_combo.addItems(["1분기", "2분기", "3분기", "4분기"])
        layout.addRow(self._quarter_label, self._quarter_combo)
        # 기본은 연간이므로 숨김
        self._quarter_label.hide()
        self._quarter_combo.hide()

        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("작성자 이름 (선택)")
        layout.addRow("작성자:", self._author_edit)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("생성")
        btn_box.accepted.connect(self._generate)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _on_mode_changed(self, idx):
        is_quarter = (idx == 1)
        self._quarter_label.setVisible(is_quarter)
        self._quarter_combo.setVisible(is_quarter)

    def _generate(self):
        from utils.report_generator import ReportGenerator
        year = self._year_spin.value()
        mode = "quarter" if self._mode_combo.currentIndex() == 1 else "year"
        quarter = self._quarter_combo.currentIndex() + 1 if mode == "quarter" else None
        author = self._author_edit.text().strip()

        try:
            gen = ReportGenerator(self._store)
            path = gen.generate(year=year, mode=mode, quarter=quarter, author_name=author)
            QMessageBox.information(self, "완료", f"보고서 생성 완료:\n{path}")
            self.accept()
        except Exception as e:
            logger.exception("보고서 생성 실패")
            QMessageBox.critical(self, "오류", f"보고서 생성 실패:\n{e}")
