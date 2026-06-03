# -*- coding: utf-8 -*-
"""
views/converter_view.py
~~~~~~~~~~~~~~~~~~~~~~~
DCC 좌표/단위 변환 탭 뷰 (Qt UI + utils.coordinate_converter 로직).
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDoubleSpinBox, QPushButton,
    QGroupBox, QTextEdit,
)
from PyQt6.QtCore import Qt

from utils.coordinate_converter import convert_position, convert_scale, convert_rotation_approx

logger = logging.getLogger(__name__)

_ENGINES = ["Unreal", "Maya", "3ds Max", "Blender"]
_ENGINE_KEYS = ["unreal", "maya", "max", "blender"]


class ConverterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 소스 → 목적지 엔진 선택
        engine_box = QGroupBox("DCC 선택")
        engine_layout = QHBoxLayout(engine_box)
        engine_layout.addWidget(QLabel("원본:"))
        self._src_combo = QComboBox()
        self._src_combo.addItems(_ENGINES)
        engine_layout.addWidget(self._src_combo)
        engine_layout.addSpacing(16)
        engine_layout.addWidget(QLabel("→"))
        engine_layout.addSpacing(16)
        engine_layout.addWidget(QLabel("대상:"))
        self._dst_combo = QComboBox()
        self._dst_combo.addItems(_ENGINES)
        self._dst_combo.setCurrentIndex(1)  # 기본: Maya
        engine_layout.addWidget(self._dst_combo)
        engine_layout.addStretch()
        main_layout.addWidget(engine_box)

        # 입력 영역
        input_group = QGroupBox("변환 입력")
        grid = QGridLayout(input_group)
        grid.setColumnStretch(0, 2)
        for col, lbl in enumerate(["X", "Y", "Z"], start=1):
            grid.addWidget(QLabel(lbl, alignment=Qt.AlignmentFlag.AlignCenter), 0, col)

        self._pos_spins: list[QDoubleSpinBox] = []
        self._scale_spins: list[QDoubleSpinBox] = []
        self._rot_spins: list[QDoubleSpinBox] = []

        row_defs = [
            ("위치 (Position)", self._pos_spins, 1.0),
            ("스케일 (Scale)", self._scale_spins, 1.0),
            ("회전 (Rotation) ※근사", self._rot_spins, 1.0),
        ]
        for row, (label, spin_list, step) in enumerate(row_defs, start=1):
            grid.addWidget(QLabel(label), row, 0)
            for col in range(3):
                spin = QDoubleSpinBox()
                spin.setRange(-999999.0, 999999.0)
                spin.setDecimals(4)
                spin.setSingleStep(step)
                spin_list.append(spin)
                grid.addWidget(spin, row, col + 1)

        # 스케일 기본값 1
        for sp in self._scale_spins:
            sp.setValue(1.0)

        main_layout.addWidget(input_group)

        # 변환 버튼
        btn_convert = QPushButton("변환")
        btn_convert.clicked.connect(self._on_convert)
        main_layout.addWidget(btn_convert)

        # 결과 출력
        result_group = QGroupBox("변환 결과")
        result_layout = QVBoxLayout(result_group)
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(130)
        result_layout.addWidget(self._result_text)
        main_layout.addWidget(result_group)

        note = QLabel(
            "※ 회전값은 근사치입니다. 오일러 순서/짐벌 차이로 어긋날 수 있으니 DCC에서 검수하세요.\n"
            "   위치/스케일 변환은 정확합니다."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 10px;")
        main_layout.addWidget(note)

    def _get_vec3(self, spins) -> tuple:
        return tuple(s.value() for s in spins)

    def _on_convert(self):
        src = _ENGINE_KEYS[self._src_combo.currentIndex()]
        dst = _ENGINE_KEYS[self._dst_combo.currentIndex()]

        pos_in = self._get_vec3(self._pos_spins)
        scale_in = self._get_vec3(self._scale_spins)
        rot_in = self._get_vec3(self._rot_spins)

        try:
            pos_out = convert_position(pos_in, src, dst)
            scale_out = convert_scale(scale_in, src, dst)
            rot_out, warn = convert_rotation_approx(rot_in, src, dst)
        except ValueError as e:
            self._result_text.setText(f"오류: {e}")
            return

        lines = [
            f"[위치]  {pos_out[0]:.4f},  {pos_out[1]:.4f},  {pos_out[2]:.4f}",
            f"[스케일]  {scale_out[0]:.6f},  {scale_out[1]:.6f},  {scale_out[2]:.6f}",
            f"[회전]  {rot_out[0]:.4f},  {rot_out[1]:.4f},  {rot_out[2]:.4f}",
            "",
            warn,
        ]
        self._result_text.setText("\n".join(lines))
        logger.debug("좌표변환: %s → %s", src, dst)
