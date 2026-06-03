"""월 캘린더 뷰 — 7열 격자, 배경 이미지/GIF, 칸별 deco"""
import calendar
import logging
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QFontMetrics, QPixmap, QMovie,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QSizePolicy, QMenu, QFileDialog, QDialog, QSlider, QDialogButtonBox,
    QFormLayout,
)

logger = logging.getLogger(__name__)

_CELL_MIN_H = 80
_MAX_BARS = 3


class BgSettingsDialog(QDialog):
    """배경 이미지/GIF 설정 다이얼로그."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("배경 설정")
        self.setFixedWidth(420)
        self._settings = settings
        self._path = settings.get("bg_image", "")
        self._opacity = int(settings.get("bg_opacity", 0.4) * 100)

        layout = QFormLayout(self)
        layout.setSpacing(10)

        # 파일 경로 + 버튼 행
        row_w = QWidget()
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0, 0, 0, 0)
        self._lbl_path = QLabel(Path(self._path).name if self._path else "없음")
        self._lbl_path.setMaximumWidth(220)
        self._lbl_path.setWordWrap(True)
        btn_pick = QPushButton("파일 선택")
        btn_pick.clicked.connect(self._pick_file)
        btn_remove = QPushButton("제거")
        btn_remove.clicked.connect(self._remove_bg)
        row_l.addWidget(self._lbl_path, 1)
        row_l.addWidget(btn_pick)
        row_l.addWidget(btn_remove)
        layout.addRow("배경 파일:", row_w)

        # 불투명도 슬라이더
        slider_w = QWidget()
        sl_l = QHBoxLayout(slider_w)
        sl_l.setContentsMargins(0, 0, 0, 0)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(10, 100)
        self._slider.setValue(self._opacity)
        self._lbl_opacity = QLabel(f"{self._opacity}%")
        self._lbl_opacity.setFixedWidth(38)
        self._slider.valueChanged.connect(self._on_slider)
        sl_l.addWidget(self._slider, 1)
        sl_l.addWidget(self._lbl_opacity)
        layout.addRow("이미지 밝기:", slider_w)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_slider(self, v: int):
        self._opacity = v
        self._lbl_opacity.setText(f"{v}%")

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "배경 이미지 선택", "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if path:
            self._path = path
            self._lbl_path.setText(Path(path).name)

    def _remove_bg(self):
        self._path = ""
        self._lbl_path.setText("없음")

    def _apply(self):
        self._settings.set("bg_image", self._path)
        self._settings.set("bg_opacity", self._opacity / 100.0)
        self.accept()


class CalendarCell(QWidget):
    """단일 날짜 칸."""
    double_clicked = pyqtSignal(date)
    task_clicked = pyqtSignal(str)           # task id
    deco_changed = pyqtSignal(date, str)     # (날짜, 경로 or "")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cell_date: date | None = None
        self.tasks: list[dict] = []
        self.is_today = False
        self.is_other_month = False
        self._deco_image: str = ""
        self._deco_pixmap: QPixmap | None = None
        self._bg_active = False
        self.setMinimumHeight(_CELL_MIN_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAutoFillBackground(False)
        self._hit_rects: list[tuple[int, int, int, int, str]] = []

    def set_data(
        self,
        cell_date: date,
        tasks: list[dict],
        is_today: bool,
        is_other_month: bool,
        deco_image: str = "",
        bg_active: bool = False,
    ):
        self.cell_date = cell_date
        self.tasks = tasks
        self.is_today = is_today
        self.is_other_month = is_other_month
        self._bg_active = bg_active
        self._hit_rects = []

        # deco 픽스맵 — 경로가 바뀔 때만 재로드
        if deco_image != self._deco_image:
            self._deco_image = deco_image
            if deco_image and Path(deco_image).exists():
                self._deco_pixmap = QPixmap(deco_image)
                if self._deco_pixmap.isNull():
                    self._deco_pixmap = None
            else:
                self._deco_pixmap = None

        # 배경 이미지가 있으면 셀을 반투명하게 (부모 배경이 비침)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, bg_active)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 셀 배경 — bg_active 시 반투명 RGBA
        if self._bg_active:
            if self.is_today:
                bg = QColor(234, 244, 255, 210)
            elif self.is_other_month:
                bg = QColor(245, 245, 245, 150)
            else:
                bg = QColor(255, 255, 255, 185)
        else:
            if self.is_today:
                bg = QColor("#EAF4FF")
            elif self.is_other_month:
                bg = QColor("#F5F5F5")
            else:
                bg = QColor("#FFFFFF")
        p.fillRect(0, 0, w, h, bg)

        # deco 이미지 썸네일 (하단 절반, 반투명)
        if self._deco_pixmap and not self._deco_pixmap.isNull():
            img_h = max(h // 2, 40)
            scaled = self._deco_pixmap.scaled(
                w, img_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.setOpacity(0.38)
            src_x = max(0, (scaled.width() - w) // 2)
            p.drawPixmap(0, h - img_h, w, img_h, scaled, src_x, 0, w, img_h)
            p.setOpacity(1.0)

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
        p.drawText(4, 2, w - 8, 18,
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
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

            p.setPen(QColor("#FFFFFF"))
            font2 = QFont()
            font2.setPointSize(8)
            p.setFont(font2)
            fm = QFontMetrics(font2)
            title = fm.elidedText(
                task.get("title", ""), Qt.TextElideMode.ElideRight, w - 10
            )
            p.drawText(5, bar_y, w - 10, bar_h,
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                       title)

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

    def contextMenuEvent(self, event):
        if not self.cell_date:
            return
        menu = QMenu(self)
        if self._deco_image:
            menu.addAction("꾸미기 이미지 제거").triggered.connect(self._clear_deco)
        menu.addAction("꾸미기 이미지 설정…").triggered.connect(self._set_deco)
        menu.exec(event.globalPos())

    def _set_deco(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "꾸미기 이미지 선택", "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if path and self.cell_date:
            self.deco_changed.emit(self.cell_date, path)

    def _clear_deco(self):
        if self.cell_date:
            self.deco_changed.emit(self.cell_date, "")


class MonthView(QWidget):
    """월 캘린더 전체 위젯."""
    request_new_task = pyqtSignal(date)
    request_edit_task = pyqtSignal(str)

    def __init__(self, task_store, settings, parent=None):
        super().__init__(parent)
        self._store = task_store
        self._settings = settings
        self._store.subscribe(self._on_store_changed)

        today = date.today()
        self._year = today.year
        self._month = today.month

        self._bg_pixmap: QPixmap | None = None
        self._bg_movie: QMovie | None = None

        self._build_ui()
        self._apply_bg()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(2)

        # 네비게이션 바
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
        self._btn_bg = QPushButton("배경")
        self._btn_bg.setFixedWidth(50)
        self._btn_bg.clicked.connect(self._open_bg_dialog)

        nav.addWidget(self._btn_prev)
        nav.addWidget(self._lbl_month, 1)
        nav.addWidget(self._btn_today)
        nav.addWidget(self._btn_next)
        nav.addWidget(self._btn_bg)
        root.addLayout(nav)

        # 요일 헤더
        header = QHBoxLayout()
        header.setSpacing(1)
        for d in ["월", "화", "수", "목", "금", "토", "일"]:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(20)
            if d == "토":
                lbl.setStyleSheet("color: #2266CC;")
            elif d == "일":
                lbl.setStyleSheet("color: #CC2222;")
            header.addWidget(lbl)
        root.addLayout(header)

        # 6×7 격자
        self._grid = QGridLayout()
        self._grid.setSpacing(1)
        self._cells: list[CalendarCell] = []
        for row in range(6):
            for col in range(7):
                cell = CalendarCell()
                cell.double_clicked.connect(self.request_new_task)
                cell.task_clicked.connect(self.request_edit_task)
                cell.deco_changed.connect(self._on_deco_changed)
                self._grid.addWidget(cell, row, col)
                self._cells.append(cell)
        root.addLayout(self._grid, 1)

    # --- 배경 ---
    def _open_bg_dialog(self):
        dlg = BgSettingsDialog(self._settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._apply_bg()
            self._refresh()

    def _apply_bg(self):
        """설정에서 배경 이미지 로드 (GIF면 QMovie 사용)."""
        if self._bg_movie:
            self._bg_movie.stop()
            self._bg_movie = None
        self._bg_pixmap = None

        path = self._settings.get("bg_image", "")
        if not path or not Path(path).exists():
            self.update()
            return

        if path.lower().endswith(".gif"):
            self._bg_movie = QMovie(path)
            self._bg_movie.frameChanged.connect(lambda _: self.update())
            self._bg_movie.start()
        else:
            pix = QPixmap(path)
            self._bg_pixmap = pix if not pix.isNull() else None

        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        pixmap: QPixmap | None = None
        if self._bg_movie:
            pixmap = self._bg_movie.currentPixmap()
        elif self._bg_pixmap:
            pixmap = self._bg_pixmap

        if pixmap is None or pixmap.isNull():
            return

        opacity = self._settings.get("bg_opacity", 0.4)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        p = QPainter(self)
        p.setOpacity(opacity)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        p.drawPixmap(x, y, scaled)

    # --- deco ---
    def _on_deco_changed(self, cell_date: date, path: str):
        date_str = cell_date.isoformat()
        if path:
            self._settings.set_deco_image(date_str, path)
            logger.info("deco 설정: %s → %s", date_str, path)
        else:
            self._settings.clear_deco_image(date_str)
            logger.info("deco 제거: %s", date_str)
        self._refresh()

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

    def _on_store_changed(self):
        self._refresh()

    def _refresh(self):
        self._lbl_month.setText(f"{self._year}년 {self._month}월")

        first_weekday, days_in_month = calendar.monthrange(self._year, self._month)
        start_date = date(self._year, self._month, 1) - timedelta(days=first_weekday)
        grid_end = start_date + timedelta(days=41)

        tasks = self._store.by_date_range(start_date.isoformat(), grid_end.isoformat())
        today = date.today()

        bg_path = self._settings.get("bg_image", "")
        bg_active = bool(bg_path and Path(bg_path).exists())

        for idx, cell in enumerate(self._cells):
            cell_date = start_date + timedelta(days=idx)
            is_other = cell_date.month != self._month

            cell_tasks = [
                t for t in tasks
                if t["start"] <= cell_date.isoformat() <= t["end"]
            ]
            cell_tasks.sort(key=lambda t: t["start"])

            deco = self._settings.get_deco_image(cell_date.isoformat())

            cell.set_data(
                cell_date=cell_date,
                tasks=cell_tasks,
                is_today=(cell_date == today),
                is_other_month=is_other,
                deco_image=deco,
                bg_active=bg_active,
            )
