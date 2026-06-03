"""일감 목록 뷰 — 표 형식, 마감일 기준 정렬, 더블클릭 편집"""
import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)

logger = logging.getLogger(__name__)

_STATUS_LABEL = {"todo": "할 일", "doing": "진행 중", "done": "완료"}
_PRIORITY_LABEL = {"high": "높음", "mid": "보통", "low": "낮음"}


class ListView(QWidget):
    """일감 목록 뷰 — 행마다 일감 하나, 더블클릭으로 편집 다이얼로그 열기."""
    request_edit_task = pyqtSignal(str)   # task_id

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self._store = store
        self._store.subscribe(self._refresh)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(0)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["", "제목", "시작일", "마감일", "상태", "우선순위"]
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setColumnWidth(0, 8)   # 색 띠
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.doubleClicked.connect(self._on_double_click)
        root.addWidget(self._table)

    def _refresh(self):
        tasks = sorted(
            self._store.all(),
            key=lambda t: (t["end"], t["start"])
        )

        # 정렬 중 행 재배치 방지
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            tid = task["id"]

            # 색 띠 칸 — task_id를 UserRole에 보관
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(task.get("color", "#4A90D9")))
            color_item.setData(Qt.ItemDataRole.UserRole, tid)
            self._table.setItem(row, 0, color_item)

            for col, text in enumerate([
                task["title"],
                task["start"],
                task["end"],
                _STATUS_LABEL.get(task["status"], task["status"]),
                _PRIORITY_LABEL.get(task["priority"], task["priority"]),
            ], start=1):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, tid)
                self._table.setItem(row, col, item)

            # 완료 일감 흐리게
            if task["status"] == "done":
                for col in range(1, 6):
                    cell = self._table.item(row, col)
                    if cell:
                        cell.setForeground(QColor("#AAAAAA"))

        self._table.setSortingEnabled(True)

    def _on_double_click(self, index):
        cell = self._table.item(index.row(), 0)
        if cell:
            self.request_edit_task.emit(cell.data(Qt.ItemDataRole.UserRole))
