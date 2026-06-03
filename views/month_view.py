"""월 캘린더 뷰 — 7열 격자, 기간 일감 막대, 더블클릭 추가"""
import calendar
import logging
from datetime import date, timedelta

from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
)

logger = logging.getLogger(__name__)

# 각 칸의 최소 높이
_CELL_MIN_H = 80
# 한 칸에 표시할 최대 일감 막대 수 (초과 시 "+N" 표시)
_MAX_BARS = 3


class CalendarCell(QWidget):
    """단일 날짜 칸."""
    double_clicked = pyqtSignal(date)
    task_clicked = pyqtSignal(str)   # task id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cell_date: date | None = None
        self.tasks: list[dict] = []          # 이 칸에 표시할 일감
        self.is_today = False
        self.is_other_month = False
        self.setMinimumHeight(_CELL_MIN_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._hit_rects: list[tuple[int, int, int, int, str]] = []  # (x,y,w,h, task_id)

    def set_data(self, cell_date: date, tasks: list[dict],
                 is_today: bool, is_other_month: bool):
        self.cell_date = cell_date
        self.tasks = tasks
        self.is_today = is_today
        self.is_other_month = is_other_month
        self._hit_rects = []
        self.update()

    # --- 페인팅 ---
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 배경
        if self.is_today:
            bg = QColor("#EAF4FF")
        elif self.is_other_month:
            bg = QColor("#F5F5F5")
        else:
            bg = QColor("#FFFFFF")
        p.fillRect(0, 0, w, h, bg)

        # 테두리
        border_col = QColor("#C0C0C0") if not self.is_today else QColor("#4A90D9")
        p.setPen(QPen(border_col, 1))
        p.drawRect(0, 0, w - 1, h - 1)

        if self.cell_date is None:
            return

        # 날짜 숫자
        font = QFont()
        font.setPointSize(9)
        if self.is_today:
            font.setBold(True)
        p.setFont(font)
        day_color = QColor("#1A1A1A") if not self.is_other_month else QColor("#AAAAAA")
        if self.is_today:
            day_color = QColor("#0055CC")
        p.setPen(day_color)
        p.drawText(4, 2, w - 8, 18, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                   str(self.cell_date.day))

        # 일감 막대
        self._hit_rects = []
        bar_y = 22
        bar_h = 16
        gap = 2
        shown = 0
        for task in self.tasks[:_MAX_BARS]:
            color = QColor(task.get("color", "#4A90D9"))
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(2, bar_y, w - 4, bar_h, 3, 3)

            # 일감 제목
            p.setPen(QColor("#FFFFFF"))
            font2 = QFont()
            font2.setPointSize(8)
            p.setFont(font2)
            fm = QFontMetrics(font2)
            title = fm.elidedText(task.get("title", ""), Qt.TextElideMode.ElideRight, w - 10)
            p.drawText(5, bar_y, w - 10, bar_h,
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title)

            self._hit_rects.append((2, bar_y, w - 4, bar_h, task["id"]))
            bar_y += bar_h + gap
            shown += 1

        overflow = len(self.tasks) - shown
        if overflow > 0:
            p.setPen(QColor("#888888"))
            font3 = QFont()
            font3.setPointSize(8)
            p.setFont(font3)
            p.drawText(4, bar_y, w - 8, bar_h,
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       f"+{overflow}")

    def mouseDoubleClickEvent(self, event):
        if self.cell_date:
            self.double_clicked.emit(self.cell_date)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = int(event.position().x()), int(event.position().y())
            for rx, ry, rw, rh, tid in self._hit_rects:
                if rx <= x <= rx + rw and ry <= y <= ry + rh:
                    self.task_clicked.emit(tid)
                    return
        super().mousePressEvent(event)


class MonthView(QWidget):
    """월 캘린더 전체 위젯."""
    request_new_task = pyqtSignal(date)   # 날짜 더블클릭 → 새 일감
    request_edit_task = pyqtSignal(str)   # 일감 클릭 → 편집

    def __init__(self, task_store, parent=None):
        super().__init__(parent)
        self._store = task_store
        self._store.subscribe(self._on_store_changed)

        today = date.today()
        self._year = today.year
        self._month = today.month

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(2)

        # 상단: 이전/다음 + 연월 레이블
        nav = QHBoxLayout()
        self._btn_prev = QPushButton("◀")
        self._btn_prev.setFixedWidth(32)
        self._btn_prev.clicked.connect(self._prev_month)
        self._lbl_month = QLabel()
        self._lbl_month.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self._lbl_month.setFont(font)
        self._btn_next = QPushButton("▶")
        self._btn_next.setFixedWidth(32)
        self._btn_next.clicked.connect(self._next_month)
        self._btn_today = QPushButton("오늘")
        self._btn_today.clicked.connect(self._go_today)

        nav.addWidget(self._btn_prev)
        nav.addWidget(self._lbl_month, 1)
        nav.addWidget(self._btn_today)
        nav.addWidget(self._btn_next)
        root.addLayout(nav)

        # 요일 헤더
        header = QHBoxLayout()
        header.setSpacing(1)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        for d in days:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(20)
            if d == "토":
                lbl.setStyleSheet("color: #2266CC;")
            elif d == "일":
                lbl.setStyleSheet("color: #CC2222;")
            header.addWidget(lbl)
        root.addLayout(header)

        # 6×7 격자 (최대 6주)
        from PyQt6.QtWidgets import QGridLayout
        self._grid = QGridLayout()
        self._grid.setSpacing(1)
        self._cells: list[CalendarCell] = []
        for row in range(6):
            for col in range(7):
                cell = CalendarCell()
                cell.double_clicked.connect(self.request_new_task)
                cell.task_clicked.connect(self.request_edit_task)
                self._grid.addWidget(cell, row, col)
                self._cells.append(cell)
        root.addLayout(self._grid, 1)

    # --- 네비게이션 ---
    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._refresh()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._refresh()

    def _go_today(self):
        today = date.today()
        self._year, self._month = today.year, today.month
        self._refresh()

    # --- 갱신 ---
    def _on_store_changed(self):
        self._refresh()

    def _refresh(self):
        self._lbl_month.setText(f"{self._year}년 {self._month}월")

        # 이번 달 1일의 요일(0=월 … 6=일) 및 마지막 날
        first_weekday, days_in_month = calendar.monthrange(self._year, self._month)
        # calendar.monthrange은 0=월요일

        # 격자 시작일 (이전 달 포함)
        start_date = date(self._year, self._month, 1) - timedelta(days=first_weekday)

        # 이번 달 일감을 날짜별로 분류
        month_start = date(self._year, self._month, 1).isoformat()
        last_day = days_in_month
        month_end = date(self._year, self._month, last_day).isoformat()

        # 표시 범위는 격자 전체(최대 42일)이므로 좀 더 넓게 쿼리
        grid_end = start_date + timedelta(days=41)
        tasks = self._store.by_date_range(start_date.isoformat(), grid_end.isoformat())

        today = date.today()

        for idx, cell in enumerate(self._cells):
            cell_date = start_date + timedelta(days=idx)
            is_other = cell_date.month != self._month

            # 이 칸에 걸치는 일감 필터
            cell_tasks = [
                t for t in tasks
                if t["start"] <= cell_date.isoformat() <= t["end"]
            ]
            # 시작일 기준 정렬
            cell_tasks.sort(key=lambda t: t["start"])

            cell.set_data(
                cell_date=cell_date,
                tasks=cell_tasks,
                is_today=(cell_date == today),
                is_other_month=is_other,
            )
