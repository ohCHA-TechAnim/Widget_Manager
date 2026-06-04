"""트레이 클릭 시 화면 우측 하단에 나타나는 미니 오버레이 패널."""
import logging
from datetime import date as _date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QGuiApplication

logger = logging.getLogger(__name__)

_PANEL_W = 280
_PANEL_H = 370
_MARGIN = 12

_STATUS_KO = {"todo": "예정", "doing": "진행", "done": "완료"}


class OverlayPanel(QWidget):
    """트레이 오버레이 미니 패널 — 우측 하단 고정."""

    expand_requested = pyqtSignal()  # "전체보기" 버튼 클릭 시

    def __init__(self, store):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._store = store
        self.setObjectName("overlay_panel")
        self.setFixedSize(_PANEL_W, _PANEL_H)
        self._build_ui()
        self._store.subscribe(self._on_store_changed)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 헤더 바 ──────────────────────────────────────────────────
        hdr_widget = QWidget()
        hdr_widget.setObjectName("overlay_header")
        hdr_layout = QHBoxLayout(hdr_widget)
        hdr_layout.setContentsMargins(10, 8, 10, 8)
        hdr_layout.setSpacing(6)

        lbl_title = QLabel("Widget Manager")
        lbl_title.setObjectName("overlay_title")
        hdr_layout.addWidget(lbl_title)
        hdr_layout.addStretch()

        btn_expand = QPushButton("전체보기")
        btn_expand.setObjectName("overlay_expand_btn")
        btn_expand.setFixedHeight(22)
        btn_expand.clicked.connect(self.expand_requested)
        hdr_layout.addWidget(btn_expand)

        outer.addWidget(hdr_widget)

        # ── 구분선 ──────────────────────────────────────────────────
        sep_top = QFrame()
        sep_top.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(sep_top)

        # ── 내용 영역 ────────────────────────────────────────────────
        content = QWidget()
        content.setObjectName("overlay_content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(6)

        # 오늘 섹션
        lbl_today_hdr = QLabel()
        lbl_today_hdr.setObjectName("overlay_section_header")
        self._lbl_today_hdr = lbl_today_hdr
        content_layout.addWidget(lbl_today_hdr)

        self._today_layout = QVBoxLayout()
        self._today_layout.setSpacing(2)
        content_layout.addLayout(self._today_layout)

        sep_mid = QFrame()
        sep_mid.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(sep_mid)

        # 다가오는 일감 섹션
        lbl_upcoming_hdr = QLabel("다가오는 일감 (7일)")
        lbl_upcoming_hdr.setObjectName("overlay_section_header")
        content_layout.addWidget(lbl_upcoming_hdr)

        self._upcoming_layout = QVBoxLayout()
        self._upcoming_layout.setSpacing(2)
        content_layout.addLayout(self._upcoming_layout)

        content_layout.addStretch()
        outer.addWidget(content, 1)

        # ── 하단 바 ──────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("overlay_footer")
        foot_layout = QHBoxLayout(footer)
        foot_layout.setContentsMargins(10, 6, 10, 8)
        foot_layout.addStretch()

        btn_close = QPushButton("닫기")
        btn_close.setObjectName("overlay_close_btn")
        btn_close.setFixedHeight(22)
        btn_close.clicked.connect(self.hide)
        foot_layout.addWidget(btn_close)

        outer.addWidget(footer)

    # ── 데이터 갱신 ────────────────────────────────────────────────
    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        """일감 데이터를 최신 상태로 갱신한다."""
        today = _date.today()
        today_str = today.isoformat()
        in_7d_str = (today + timedelta(days=7)).isoformat()

        self._lbl_today_hdr.setText(f"오늘 ({today.strftime('%m/%d')})")

        all_tasks = self._store.all()

        # 오늘 일감: start <= today <= end, 완료 제외
        today_tasks = sorted(
            [t for t in all_tasks
             if t["start"] <= today_str <= t["end"] and t["status"] != "done"],
            key=lambda x: x["start"],
        )

        self._clear_layout(self._today_layout)
        if today_tasks:
            for t in today_tasks[:5]:
                status = _STATUS_KO.get(t["status"], t["status"])
                title = t["title"]
                if len(title) > 22:
                    title = title[:21] + "…"
                lbl = QLabel(f"• [{status}] {title}")
                lbl.setObjectName("overlay_task_item")
                self._today_layout.addWidget(lbl)
        else:
            lbl = QLabel("  오늘 일감 없음")
            lbl.setObjectName("overlay_empty_label")
            self._today_layout.addWidget(lbl)

        # 다가오는 일감: start > today and start <= today+7d
        upcoming = sorted(
            [t for t in all_tasks if today_str < t["start"] <= in_7d_str],
            key=lambda x: x["start"],
        )

        self._clear_layout(self._upcoming_layout)
        if upcoming:
            for t in upcoming[:5]:
                mm_dd = t["start"][5:]  # "MM-DD"
                title = t["title"]
                if len(title) > 20:
                    title = title[:19] + "…"
                lbl = QLabel(f"• [{mm_dd}] {title}")
                lbl.setObjectName("overlay_task_item")
                self._upcoming_layout.addWidget(lbl)
        else:
            lbl = QLabel("  다가오는 일감 없음")
            lbl.setObjectName("overlay_empty_label")
            self._upcoming_layout.addWidget(lbl)

    def _on_store_changed(self):
        if self.isVisible():
            self.refresh()

    # ── 위치 ───────────────────────────────────────────────────────
    def _move_to_bottom_right(self):
        """화면 availableGeometry 기준 우측 하단에 배치한다."""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - _MARGIN
        y = screen.bottom() - self.height() - _MARGIN
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self._move_to_bottom_right()

    def changeEvent(self, event):
        """다른 창이 활성화되면 자동으로 패널을 숨긴다."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.hide()
