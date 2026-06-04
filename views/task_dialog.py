"""일감 편집 다이얼로그 — 새 일감 추가 및 기존 일감 수정"""
import logging
from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QComboBox, QTextEdit,
    QPushButton, QLabel, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QFileDialog,
    QColorDialog, QMessageBox,
)

logger = logging.getLogger(__name__)

_STATUS_LABELS = [("todo", "할 일"), ("doing", "진행 중"), ("done", "완료")]
_PRIORITY_LABELS = [("high", "높음"), ("mid", "보통"), ("low", "낮음")]


class _LinkDialog(QDialog):
    """지라/폴더 링크 이름+경로 입력 소다이얼로그."""

    def __init__(self, title: str, parent=None,
                 name: str = "", path: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)

        form = QFormLayout(self)
        self._name = QLineEdit(name)
        self._path = QLineEdit(path)
        self._path.setPlaceholderText("URL 또는 절대 경로")
        form.addRow("이름:", self._name)
        form.addRow("경로/URL:", self._path)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("확인")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        form.addRow(btn_row)

    def values(self) -> tuple[str, str]:
        return self._name.text().strip(), self._path.text().strip()


class TaskDialog(QDialog):
    """
    일감 생성/수정 다이얼로그.
      task=None         → 새 일감 (default_date가 시작/마감 기본값)
      task=dict(task)   → 기존 일감 수정
    """

    def __init__(self, store, task: dict | None = None,
                 default_date: date | None = None,
                 default_end_date: date | None = None,
                 parent=None):
        super().__init__(parent)
        self._store = store
        self._task = task
        self._color = task["color"] if task else "#4A90D9"
        self._default_end_date = default_end_date

        self.setWindowTitle("일감 수정" if task else "새 일감")
        self.setMinimumSize(500, 540)

        self._build_ui(default_date or date.today())
        if task:
            self._populate(task)

    # ------------------------------------------------------------------ #
    # UI 빌드
    # ------------------------------------------------------------------ #
    def _build_ui(self, default_date: date):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        tabs = QTabWidget()
        tabs.addTab(self._make_basic_tab(default_date), "기본 정보")
        tabs.addTab(self._make_links_tab(), "링크 & 첨부")
        root.addWidget(tabs, 1)

        # 하단 버튼 행
        btn_row = QHBoxLayout()
        if self._task:
            btn_del = QPushButton("삭제")
            btn_del.setStyleSheet(
                "QPushButton { background-color: transparent; color: #CC2222;"
                " border: 1px solid #CC2222; }"
                "QPushButton:hover { background-color: #CC2222; color: #FFFFFF; }"
            )
            btn_del.clicked.connect(self._on_delete)
            btn_row.addWidget(btn_del)
        btn_row.addStretch()
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("저장")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _make_basic_tab(self, default_date: date) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        # 제목
        self._title = QLineEdit()
        self._title.setPlaceholderText("일감 제목 (필수)")
        form.addRow("제목 *", self._title)

        # 기간
        qd_start = QDate(default_date.year, default_date.month, default_date.day)
        end_d = self._default_end_date or default_date
        qd_end = QDate(end_d.year, end_d.month, end_d.day)
        self._start = QDateEdit(qd_start)
        self._start.setCalendarPopup(True)
        self._start.setDisplayFormat("yyyy-MM-dd")
        self._end = QDateEdit(qd_end)
        self._end.setCalendarPopup(True)
        self._end.setDisplayFormat("yyyy-MM-dd")
        date_row = QHBoxLayout()
        date_row.addWidget(self._start)
        date_row.addWidget(QLabel("~"))
        date_row.addWidget(self._end)
        date_row.addStretch()
        form.addRow("기간", date_row)

        # 상태
        self._status = QComboBox()
        for key, label in _STATUS_LABELS:
            self._status.addItem(label, key)
        form.addRow("상태", self._status)

        # 우선순위
        self._priority = QComboBox()
        for key, label in _PRIORITY_LABELS:
            self._priority.addItem(label, key)
        self._priority.setCurrentIndex(1)   # 기본: 보통
        form.addRow("우선순위", self._priority)

        # 색상
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(24, 24)
        self._refresh_color_preview()
        btn_color = QPushButton("색 선택…")
        btn_color.clicked.connect(self._pick_color)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_preview)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        form.addRow("색상", color_row)

        # 메모
        self._memo = QTextEdit()
        self._memo.setPlaceholderText("메모 (선택)")
        self._memo.setMinimumHeight(90)
        form.addRow("메모", self._memo)

        return w

    def _make_links_tab(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setSpacing(6)

        self._jira_list = self._add_list_section(root, "지라 링크",
                                                  self._add_jira)
        self._folder_list = self._add_list_section(root, "폴더 링크",
                                                    self._add_folder)
        self._attach_list = self._add_list_section(root, "첨부 파일",
                                                    self._add_attachment)
        root.addStretch()
        return w

    def _add_list_section(self, parent_layout, label: str,
                          add_fn) -> QListWidget:
        """레이블 + 리스트 + 추가/삭제 버튼 묶음을 parent_layout에 추가하고 QListWidget을 반환."""
        parent_layout.addWidget(QLabel(label))
        row = QHBoxLayout()
        lst = QListWidget()
        lst.setMaximumHeight(90)
        lst.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        row.addWidget(lst, 1)
        btns = QVBoxLayout()
        btn_add = QPushButton("추가")
        btn_add.clicked.connect(add_fn)
        btn_del = QPushButton("삭제")
        btn_del.clicked.connect(lambda: self._remove_selected(lst))
        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        btns.addStretch()
        row.addLayout(btns)
        parent_layout.addLayout(row)
        return lst

    # ------------------------------------------------------------------ #
    # 필드 채우기 (수정 모드)
    # ------------------------------------------------------------------ #
    def _populate(self, task: dict):
        self._title.setText(task.get("title", ""))

        for edit, field in ((self._start, "start"), (self._end, "end")):
            qd = QDate.fromString(task.get(field, ""), "yyyy-MM-dd")
            if qd.isValid():
                edit.setDate(qd)

        status_keys = [k for k, _ in _STATUS_LABELS]
        idx = status_keys.index(task.get("status", "todo"))
        self._status.setCurrentIndex(max(0, idx))

        priority_keys = [k for k, _ in _PRIORITY_LABELS]
        idx = priority_keys.index(task.get("priority", "mid"))
        self._priority.setCurrentIndex(max(0, idx))

        self._color = task.get("color", "#4A90D9")
        self._refresh_color_preview()
        self._memo.setPlainText(task.get("memo", ""))

        for link in task.get("jiras", []):
            self._append_link(self._jira_list, link["name"], link["path"])
        for link in task.get("folders", []):
            self._append_link(self._folder_list, link["name"], link["path"])
        for path in task.get("attachments", []):
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._attach_list.addItem(item)

    # ------------------------------------------------------------------ #
    # 색상
    # ------------------------------------------------------------------ #
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "색상 선택")
        if color.isValid():
            self._color = color.name()
            self._refresh_color_preview()

    def _refresh_color_preview(self):
        self._color_preview.setStyleSheet(
            f"background-color:{self._color};"
            "border:1px solid #888; border-radius:3px;"
        )

    # ------------------------------------------------------------------ #
    # 링크 / 첨부
    # ------------------------------------------------------------------ #
    def _append_link(self, lst: QListWidget, name: str, path: str):
        item = QListWidgetItem(f"{name}  |  {path}" if name else path)
        item.setData(Qt.ItemDataRole.UserRole, {"name": name, "path": path})
        lst.addItem(item)

    def _add_jira(self):
        dlg = _LinkDialog("지라 링크 추가", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, path = dlg.values()
            if name or path:
                self._append_link(self._jira_list, name, path)

    def _add_folder(self):
        dlg = _LinkDialog("폴더 링크 추가", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, path = dlg.values()
            if name or path:
                self._append_link(self._folder_list, name, path)

    def _add_attachment(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "파일 선택", "", "모든 파일 (*)"
        )
        for p in paths:
            item = QListWidgetItem(Path(p).name)
            item.setData(Qt.ItemDataRole.UserRole, p)
            self._attach_list.addItem(item)

    def _remove_selected(self, lst: QListWidget):
        for item in lst.selectedItems():
            lst.takeItem(lst.row(item))

    # ------------------------------------------------------------------ #
    # 저장 / 삭제
    # ------------------------------------------------------------------ #
    def _collect(self) -> dict | None:
        """입력값 수집 및 기초 유효성 검사. 오류 시 None 반환."""
        title = self._title.text().strip()
        if not title:
            QMessageBox.warning(self, "입력 오류", "제목을 입력하세요.")
            self._title.setFocus()
            return None

        start = self._start.date().toString("yyyy-MM-dd")
        end = self._end.date().toString("yyyy-MM-dd")
        if end < start:
            QMessageBox.warning(self, "입력 오류",
                                "마감일이 시작일보다 앞설 수 없습니다.")
            return None

        jiras = [
            self._jira_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._jira_list.count())
        ]
        folders = [
            self._folder_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._folder_list.count())
        ]
        attachments = [
            self._attach_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._attach_list.count())
        ]

        return {
            "title": title,
            "start": start,
            "end": end,
            "status": self._status.currentData(),
            "priority": self._priority.currentData(),
            "color": self._color,
            "memo": self._memo.toPlainText(),
            "jiras": jiras,
            "folders": folders,
            "attachments": attachments,
        }

    def _on_save(self):
        data = self._collect()
        if data is None:
            return
        try:
            if self._task:
                self._store.update(self._task["id"], **data)
                logger.info("일감 수정: %s", self._task["id"])
            else:
                self._store.add(**data)
                logger.info("새 일감 추가: %s", data["title"])
        except Exception as exc:
            QMessageBox.critical(self, "저장 오류", str(exc))
            return
        self.accept()

    def _on_delete(self):
        if not self._task:
            return
        answer = QMessageBox.question(
            self, "삭제 확인",
            f"'{self._task['title']}' 일감을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self._store.delete(self._task["id"])
                logger.info("일감 삭제: %s", self._task["id"])
            except Exception as exc:
                QMessageBox.critical(self, "삭제 오류", str(exc))
                return
            self.accept()
