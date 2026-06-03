"""Widget_Manager — 메인 진입점"""
import sys
import logging
from pathlib import Path

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

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from core.task_store import TaskStore
from views.month_view import MonthView
from views.task_dialog import TaskDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget Manager v0.1")
        self.resize(920, 640)

        self._store = TaskStore()
        self._month_view = MonthView(self._store)
        self._month_view.request_new_task.connect(self._on_new_task)
        self._month_view.request_edit_task.connect(self._on_edit_task)
        self.setCentralWidget(self._month_view)
        logger.info("메인 창 생성 완료")

    def _on_new_task(self, clicked_date):
        """날짜 더블클릭 → 새 일감 다이얼로그."""
        dlg = TaskDialog(self._store, default_date=clicked_date, parent=self)
        dlg.exec()

    def _on_edit_task(self, task_id):
        """일감 막대 클릭 → 수정 다이얼로그."""
        try:
            task = self._store.get(task_id)
        except KeyError:
            logger.warning("수정 요청한 일감 없음: %s", task_id)
            return
        dlg = TaskDialog(self._store, task=task, parent=self)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("애플리케이션 시작")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
