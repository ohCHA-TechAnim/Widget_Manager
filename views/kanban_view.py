"""칸반 뷰 — 할 일 / 진행 중 / 완료 3컬럼, 드래그&드롭으로 상태 변경"""
import logging

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QAbstractItemView,
)

logger = logging.getLogger(__name__)

_COLS = [
    ("todo",  "할 일"),
    ("doing", "진행 중"),
    ("done",  "완료"),
]


class _KanbanColumn(QListWidget):
    """드롭 완료 시 (task_id, new_status)를 내보내는 컬럼 위젯."""
    task_status_changed = pyqtSignal(str, str)

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.status = status
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSpacing(3)

    def dropEvent(self, event):
        src = event.source()
        if isinstance(src, _KanbanColumn) and src is not self:
            selected = src.selectedItems()
            if selected:
                task_id = selected[0].data(Qt.ItemDataRole.UserRole)
                super().dropEvent(event)
                # 드롭 이벤트 완전 종료 후 store 업데이트 (이벤트 중 뷰 재빌드 충돌 방지)
                QTimer.singleShot(
                    0, lambda: self.task_status_changed.emit(task_id, self.status)
                )
                return
        super().dropEvent(event)


class KanbanView(QWidget):
    """칸반 뷰 — 3컬럼, 드래그&드롭 상태 변경."""
    request_edit_task = pyqtSignal(str)

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self._store = store
        self._store.subscribe(self._refresh)
        self._cols: dict[str, _KanbanColumn] = {}
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        for status, label in _COLS:
            panel = QWidget()
            panel.setObjectName(f"kanban_col_{status}")   # QSS에서 컬럼 배경 지정
            vbox = QVBoxLayout(panel)
            vbox.setContentsMargins(4, 4, 4, 4)
            vbox.setSpacing(4)

            hdr = QLabel(label)
            hdr.setObjectName(f"kanban_hdr_{status}")     # QSS에서 헤더 색상 지정
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(hdr)

            col = _KanbanColumn(status)
            col.task_status_changed.connect(self._on_status_changed)
            col.itemDoubleClicked.connect(self._on_item_double_clicked)
            vbox.addWidget(col, 1)

            self._cols[status] = col
            root.addWidget(panel, 1)

    def _refresh(self):
        for col in self._cols.values():
            col.clear()

        for task in self._store.all():
            status = task.get("status", "todo")
            col = self._cols.get(status)
            if col is None:
                continue

            item = QListWidgetItem(
                f"{task['title']}\n{task['start']} ~ {task['end']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, task["id"])

            bg = QColor(task.get("color", "#4A90D9"))
            item.setBackground(bg)
            # 밝기에 따라 글씨색 자동 결정
            brightness = (
                bg.red() * 0.299 + bg.green() * 0.587 + bg.blue() * 0.114
            )
            item.setForeground(
                QColor("#FFFFFF" if brightness < 128 else "#1A1A1A")
            )
            col.addItem(item)

    def _on_status_changed(self, task_id: str, new_status: str):
        try:
            self._store.update(task_id, status=new_status)
            logger.info("칸반 상태 변경: %s → %s", task_id, new_status)
        except Exception:
            logger.exception("칸반 상태 변경 실패: %s → %s", task_id, new_status)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        self.request_edit_task.emit(item.data(Qt.ItemDataRole.UserRole))
