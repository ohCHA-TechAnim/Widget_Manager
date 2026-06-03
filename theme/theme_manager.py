"""테마 관리자 — QSS 런타임 교체 + 포인트색 주입."""
import logging
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QColorDialog, QSizePolicy,
)

logger = logging.getLogger(__name__)

_THEME_DIR = Path(__file__).parent

_ACCENT_PRESETS = [
    ("#4A90D9", "파랑"),
    ("#5C6BC0", "인디고"),
    ("#26A69A", "청록"),
    ("#66BB6A", "초록"),
    ("#FFA726", "주황"),
    ("#EF5350", "빨강"),
    ("#AB47BC", "보라"),
    ("#78909C", "청회"),
]


def _lighter(hex_str: str) -> str:
    """RGB를 15% 밝게 (255 클램프)."""
    c = QColor(hex_str)
    r = min(255, int(c.red() * 1.15))
    g = min(255, int(c.green() * 1.15))
    b = min(255, int(c.blue() * 1.15))
    return f"#{r:02X}{g:02X}{b:02X}"


def _darker(hex_str: str) -> str:
    """RGB를 20% 어둡게."""
    c = QColor(hex_str)
    return f"#{int(c.red()*0.80):02X}{int(c.green()*0.80):02X}{int(c.blue()*0.80):02X}"


def _contrast_text(hex_str: str) -> str:
    """배경 밝기에 따라 흰/검 텍스트 결정 (ITU-R BT.601)."""
    c = QColor(hex_str)
    lum = c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114
    return "#FFFFFF" if lum < 140 else "#111111"


class AccentPickerDialog(QDialog):
    """포인트색 선택 — 프리셋 8개 + QColorDialog 직접 지정."""

    def __init__(self, current_accent: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("포인트색 선택")
        self.setFixedWidth(340)
        self._selected = current_accent

        root = QVBoxLayout(self)
        root.setSpacing(8)

        root.addWidget(QLabel("프리셋"))
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (color, name) in enumerate(_ACCENT_PRESETS):
            btn = QPushButton(name)
            btn.setFixedHeight(30)
            fg = _contrast_text(color)
            border = "2px solid #333" if color.upper() == current_accent.upper() else "none"
            btn.setStyleSheet(
                f"QPushButton {{ background-color:{color}; color:{fg};"
                f" border:{border}; border-radius:3px; font-size:8pt; }}"
            )
            btn.clicked.connect(lambda _, h=color: self._pick(h))
            grid.addWidget(btn, i // 4, i % 4)
        root.addLayout(grid)

        btn_custom = QPushButton("색상 선택기…")
        btn_custom.clicked.connect(self._pick_custom)
        root.addWidget(btn_custom)

        self._preview = QLabel()
        self._preview.setFixedHeight(28)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_preview()
        root.addWidget(self._preview)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("적용")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    def _pick(self, hex_color: str):
        self._selected = hex_color
        self._refresh_preview()

    def _pick_custom(self):
        color = QColorDialog.getColor(QColor(self._selected), self, "색상 선택")
        if color.isValid():
            self._selected = color.name()
            self._refresh_preview()

    def _refresh_preview(self):
        fg = _contrast_text(self._selected)
        self._preview.setStyleSheet(
            f"background-color:{self._selected}; color:{fg};"
            " border-radius:3px; padding:2px;"
        )
        self._preview.setText(f"미리보기: {self._selected}")

    def selected_color(self) -> str:
        return self._selected


class ThemeManager:
    """
    QApplication 스타일시트를 런타임 교체.
    settings: core.settings.Settings 인스턴스.
    """

    def __init__(self, app: QApplication, settings):
        self._app = app
        self._settings = settings

    def apply(self):
        """저장된 테마·포인트색을 QApplication에 즉시 적용."""
        theme = self._settings.get("theme", "light")
        accent = self._settings.get("accent_color", "#4A90D9")
        self._apply(theme, accent)

    def set_theme(self, name: str):
        """테마 이름("light"|"dark") 저장 후 즉시 적용."""
        self._settings.set("theme", name)
        self._apply(name, self._settings.get("accent_color", "#4A90D9"))
        logger.info("테마 변경: %s", name)

    def set_accent(self, hex_color: str):
        """포인트색 저장 후 즉시 적용."""
        self._settings.set("accent_color", hex_color)
        self._apply(self._settings.get("theme", "light"), hex_color)
        logger.info("포인트색 변경: %s", hex_color)

    def current_theme(self) -> str:
        return self._settings.get("theme", "light")

    def current_accent(self) -> str:
        return self._settings.get("accent_color", "#4A90D9")

    def _apply(self, theme: str, accent: str):
        qss_path = _THEME_DIR / f"{theme}.qss"
        if not qss_path.exists():
            logger.warning("QSS 파일 없음: %s", qss_path)
            self._app.setStyleSheet("")
            return

        qss = qss_path.read_text(encoding="utf-8")
        # 긴 토큰부터 교체해야 {ACCENT} 가 {ACCENT_HOVER} 내부를 건드리지 않음
        qss = qss.replace("{ACCENT_HOVER}", _lighter(accent))
        qss = qss.replace("{ACCENT_DARK}", _darker(accent))
        qss = qss.replace("{ACCENT_TEXT}", _contrast_text(accent))
        qss = qss.replace("{ACCENT}", accent)
        self._app.setStyleSheet(qss)
