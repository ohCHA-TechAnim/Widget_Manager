"""Widget_Manager — 메인 진입점"""
import sys
import logging
from pathlib import Path
from datetime import date as _date

# PyInstaller 패키지 환경 초기화 (sys._MEIPASS → sys.path, 리소스 경로 설정)
import utils.resource_path  # noqa: F401  side-effect import

# 로그 디렉터리: %APPDATA%\Widget_Manager\logs\
_log_dir = Path.home() / "AppData" / "Roaming" / "Widget_Manager" / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

# PyInstaller --windowed 환경에서는 sys.stdout이 None일 수 있음
_handlers: list = [logging.FileHandler(_log_dir / "widget_manager.log", encoding="utf-8")]
if sys.stdout is not None:
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QPushButton, QWidget,
    QSizePolicy, QSystemTrayIcon, QMenu,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

from core.task_store import TaskStore
from core.settings import Settings
from core.plugin_loader import PluginLoader, AppContext
from views.month_view import MonthView
from views.list_view import ListView
from views.kanban_view import KanbanView
from views.converter_view import ConverterView
from views.task_dialog import TaskDialog
from views.report_dialog import ReportDialog
from views.plugin_dialog import PluginDialog
from theme.theme_manager import ThemeManager, AccentPickerDialog


def _make_tray_icon() -> QIcon:
    """16×16 파란 원 아이콘 (별도 아이콘 파일 없어도 동작)"""
    pix = QPixmap(16, 16)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#4A90D9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, 14, 14)
    painter.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self._theme = theme_manager
        self.setWindowTitle("Widget Manager v0.1")
        self.resize(920, 640)

        self._store = TaskStore()
        self._settings = theme_manager._settings
        self._plugin_loader = PluginLoader()

        # 뷰 스택 (0=월, 1=목록, 2=칸반, 3=좌표변환)
        self._stack = QStackedWidget()
        self._month_view = MonthView(self._store, self._settings)
        self._list_view = ListView(self._store)
        self._kanban_view = KanbanView(self._store)
        self._converter_view = ConverterView()
        self._stack.addWidget(self._month_view)
        self._stack.addWidget(self._list_view)
        self._stack.addWidget(self._kanban_view)
        self._stack.addWidget(self._converter_view)
        self.setCentralWidget(self._stack)

        self._build_menubar()

        # 시그널 연결
        self._month_view.request_new_task.connect(self._on_new_task)
        self._month_view.request_edit_task.connect(self._on_edit_task)
        self._list_view.request_edit_task.connect(self._on_edit_task)
        self._kanban_view.request_edit_task.connect(self._on_edit_task)

        self._build_toolbar()
        self._setup_tray()

        # 플러그인 초기화 — UI 구성 완료 후 로드해야 플러그인이 main_window에 접근 가능
        ctx = AppContext(self._store, self._settings, self)
        self._plugin_loader.init(ctx)
        self._plugin_loader.load_enabled(self._settings.get("enabled_plugins", []))
        self._refresh_plugin_menu()

        logger.info("메인 창 생성 완료")

    # ── 메뉴바 ─────────────────────────────────────────────────────────────
    def _build_menubar(self):
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("도구")
        report_action = tools_menu.addAction("보고서 생성...")
        report_action.triggered.connect(self._on_generate_report)

        self._plugin_menu = menubar.addMenu("플러그인")
        self._plugin_menu.addAction("플러그인 관리...", self._on_manage_plugins)
        self._plugin_menu.addSeparator()

    def _refresh_plugin_menu(self):
        """플러그인 메뉴의 플러그인 액션을 최신 상태로 갱신한다."""
        actions = self._plugin_menu.actions()
        # 첫 두 항목(관리..., 구분선)은 유지하고 나머지만 제거
        for action in actions[2:]:
            self._plugin_menu.removeAction(action)
        for label, callback in self._plugin_loader.all_menu_actions():
            self._plugin_menu.addAction(label, callback)

    def _on_manage_plugins(self):
        dlg = PluginDialog(self._plugin_loader, self._settings, self)
        dlg.exec()
        self._refresh_plugin_menu()

    # ── 툴바 ───────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = self.addToolBar("메인")
        tb.setMovable(False)

        btn_new = QPushButton("새 일감")
        btn_new.clicked.connect(self._on_add_task)
        tb.addWidget(btn_new)
        tb.addSeparator()
        for idx, label in enumerate(["월 뷰", "목록", "칸반", "좌표변환"]):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, i=idx: self._stack.setCurrentIndex(i))
            tb.addWidget(btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tb.addWidget(spacer)

        self._btn_theme = QPushButton(self._theme_label())
        self._btn_theme.setFixedWidth(80)
        self._btn_theme.clicked.connect(self._toggle_theme)
        tb.addWidget(self._btn_theme)

        btn_accent = QPushButton("포인트색")
        btn_accent.clicked.connect(self._pick_accent)
        tb.addWidget(btn_accent)

    # ── 시스템 트레이 ──────────────────────────────────────────────────────
    def _setup_tray(self):
        """시스템 트레이 아이콘 + 컨텍스트 메뉴 설정"""
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_make_tray_icon())
        self._tray.setToolTip("Widget Manager")

        menu = QMenu()

        act_show = menu.addAction("열기")
        act_show.triggered.connect(self._show_window)

        act_report = menu.addAction("보고서 생성")
        act_report.triggered.connect(self._on_generate_report)

        act_settings = menu.addAction("설정")
        act_settings.triggered.connect(self._on_open_settings)

        menu.addSeparator()

        act_quit = menu.addAction("종료")
        act_quit.triggered.connect(self._quit_app)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
        logger.info("시스템 트레이 아이콘 등록")

    def _show_window(self):
        """창 표시 및 활성화"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        logger.debug("창 표시")

    def _on_tray_activated(self, reason):
        """트레이 아이콘 더블클릭 → 창 토글"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
                logger.debug("트레이 더블클릭 → 창 숨김")
            else:
                self._show_window()
                logger.debug("트레이 더블클릭 → 창 표시")

    def _on_open_settings(self):
        """트레이 '설정' → 창 표시 (설정 컨트롤은 툴바에 있음)"""
        self._show_window()

    def _quit_app(self):
        """트레이 '종료' → 애플리케이션 완전 종료"""
        logger.info("사용자 요청으로 애플리케이션 종료")
        QApplication.instance().quit()

    def closeEvent(self, event):
        """✕ 버튼 → 종료 대신 트레이로 숨김"""
        if QSystemTrayIcon.isSystemTrayAvailable() and self._tray.isVisible():
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "Widget Manager",
                "트레이에서 계속 실행됩니다. 완전 종료는 트레이 메뉴 → 종료를 누르세요.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
            logger.debug("✕ 클릭 → 트레이 숨김")
        else:
            logger.info("트레이 미지원 환경 — 애플리케이션 종료")
            event.accept()

    # ── 테마 ───────────────────────────────────────────────────────────────
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

    # ── 일감 ───────────────────────────────────────────────────────────────
    def _on_add_task(self):
        dlg = TaskDialog(self._store, default_date=_date.today(), parent=self)
        dlg.exec()

    def _on_new_task(self, clicked_date):
        dlg = TaskDialog(self._store, default_date=clicked_date, parent=self)
        dlg.exec()

    def _on_generate_report(self):
        dlg = ReportDialog(self._store, parent=self)
        dlg.exec()

    def _on_edit_task(self, task_id):
        try:
            task = self._store.get(task_id)
        except KeyError:
            logger.warning("수정 요청한 일감 없음: %s", task_id)
            return
        dlg = TaskDialog(self._store, task=task, parent=self)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    # 트레이 상주 — 모든 창이 닫혀도 이벤트 루프 유지
    app.setQuitOnLastWindowClosed(False)

    settings = Settings()
    theme_manager = ThemeManager(app, settings)
    theme_manager.apply()

    window = MainWindow(theme_manager)
    window.show()
    logger.info("애플리케이션 시작")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
