"""Widget_Manager — 메인 진입점"""
import sys
import logging
from pathlib import Path
from datetime import date as _date

# 로그 디렉터리: %APPDATA%\Widget_Manager\logs\
_log_dir = Path.home() / "AppData" / "Roaming" / "Widget_Manager" / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "widget_manager.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QPushButton, QWidget,
    QSizePolicy,
)

from core.task_store import TaskStore
from core.settings import Settings
from views.month_view import MonthView
from views.list_view import ListView
from views.kanban_view import KanbanView
from views.task_dialog import TaskDialog
from theme.theme_manager import ThemeManager, AccentPickerDialog


class MainWindow(QMainWindow):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self._theme = theme_manager
        self.setWindowTitle("Widget Manager v0.1")
        self.resize(920, 640)

        self._store = TaskStore()
        self._settings = theme_manager._settings

        # 뷰 스택 (0=월, 1=목록, 2=칸반)
        self._stack = QStackedWidget()
        self._month_view = MonthView(self._store, self._settings)
        self._list_view = ListView(self._store)
        self._kanban_view = KanbanView(self._store)
        self._stack.addWidget(self._month_view)
        self._stack.addWidget(self._list_view)
        self._stack.addWidget(self._kanban_view)
        self.setCentralWidget(self._stack)

        # 시그널 연결
        self._month_view.request_new_task.connect(self._on_new_task)
        self._month_view.request_edit_task.connect(self._on_edit_task)
        self._list_view.request_edit_task.connect(self._on_edit_task)
        self._kanban_view.request_edit_task.connect(self._on_edit_task)

        self._build_toolbar()
        logger.info("메인 창 생성 완료")

    def _build_toolbar(self):
        tb = self.addToolBar("메인")
        tb.setMovable(False)

        # 왼쪽: 일감 관리 + 뷰 전환
        btn_new = QPushButton("새 일감")
        btn_new.clicked.connect(self._on_add_task)
        tb.addWidget(btn_new)
        tb.addSeparator()
        for idx, label in enumerate(["월 뷰", "목록", "칸반"]):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, i=idx: self._stack.setCurrentIndex(i))
            tb.addWidget(btn)

        # 스페이서 — 이후 버튼들을 우측으로 밀기
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tb.addWidget(spacer)

        # 우측: 테마 토글 + 포인트색
        self._btn_theme = QPushButton(self._theme_label())
        self._btn_theme.setFixedWidth(80)
        self._btn_theme.clicked.connect(self._toggle_theme)
        tb.addWidget(self._btn_theme)

        btn_accent = QPushButton("포인트색")
        btn_accent.clicked.connect(self._pick_accent)
        tb.addWidget(btn_accent)

    def _theme_label(self) -> str:
        return "다크 모드" if self._theme.current_theme() == "light" else "라이트 모드"

    def _toggle_theme(self):
        new = "dark" if self._theme.current_theme() == "light" else "light"
        self._theme.set_theme(new)
        self._btn_theme.setText(self._theme_label())

    def _pick_accent(self):
        dlg = AccentPickerDialog(self._theme.current_accent(), self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._theme.set_accent(dlg.selected_color())

    def _on_add_task(self):
        """툴바 '새 일감' — 오늘 날짜로 다이얼로그 열기."""
        dlg = TaskDialog(self._store, default_date=_date.today(), parent=self)
        dlg.exec()

    def _on_new_task(self, clicked_date):
        """월 뷰 날짜 더블클릭 → 새 일감 다이얼로그."""
        dlg = TaskDialog(self._store, default_date=clicked_date, parent=self)
        dlg.exec()

    def _on_edit_task(self, task_id):
        """일감 클릭 → 수정 다이얼로그."""
        try:
            task = self._store.get(task_id)
        except KeyError:
            logger.warning("수정 요청한 일감 없음: %s", task_id)
            return
        dlg = TaskDialog(self._store, task=task, parent=self)
        dlg.exec()


def main():
    app = QApplication(sys.argv)

    settings = Settings()
    theme_manager = ThemeManager(app, settings)
    theme_manager.apply()   # 창 뜨기 전에 QSS 적용

    window = MainWindow(theme_manager)
    window.show()
    logger.info("애플리케이션 시작")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
