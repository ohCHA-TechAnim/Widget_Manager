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


def _unhandled_exception_hook(exc_type, exc_value, exc_traceback):
    """처리되지 않은 예외를 로그에 기록하고 앱이 조용히 죽지 않도록 한다."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.exception(
        "처리되지 않은 예외 — 앱이 종료될 수 있습니다",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = _unhandled_exception_hook

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QPushButton, QWidget,
    QSystemTrayIcon, QMenu,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

from utils.resource_path import resource_path

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
from views.settings_dialog import SettingsDialog
from views.overlay_panel import OverlayPanel
from theme.theme_manager import ThemeManager, AccentPickerDialog
from core.updater import UpdateChecker


def _make_tray_icon() -> QIcon:
    """앱 아이콘(assets/app_icon.ico) 사용; 없으면 16×16 파란 원 생성."""
    ico_path = resource_path("assets/app_icon.ico")
    if ico_path.exists():
        return QIcon(str(ico_path))
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
        self._month_view.request_new_task_range.connect(self._on_new_task_range)
        self._month_view.request_edit_task.connect(self._on_edit_task)
        self._list_view.request_edit_task.connect(self._on_edit_task)
        self._kanban_view.request_edit_task.connect(self._on_edit_task)

        self._build_toolbar()
        self._setup_tray()

        # 오버레이 패널 (트레이 클릭 시 우측 하단에 표시)
        self._overlay = OverlayPanel(self._store)
        self._overlay.expand_requested.connect(self._show_window)

        # 플러그인 초기화 — UI 구성 완료 후 로드해야 플러그인이 main_window에 접근 가능
        ctx = AppContext(self._store, self._settings, self)
        self._plugin_loader.init(ctx)
        self._plugin_loader.load_enabled(self._settings.get("enabled_plugins", []))
        self._refresh_plugin_menu()

        # 시작 후 백그라운드에서 업데이트 체크
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

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

        settings_menu = menubar.addMenu("설정")
        self._action_theme = settings_menu.addAction(self._theme_label())
        self._action_theme.triggered.connect(self._toggle_theme)
        settings_menu.addAction("포인트색...", self._pick_accent)
        settings_menu.addSeparator()
        settings_menu.addAction("앱 설정...", self._on_open_settings)

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
        for idx, label in enumerate(["달력", "목록", "칸반", "좌표변환"]):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, i=idx: self._stack.setCurrentIndex(i))
            tb.addWidget(btn)

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
        """트레이 아이콘 클릭 동작:
        단일 클릭(Trigger) → 오버레이 패널 토글
        더블 클릭          → 메인 창 표시
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._overlay.isVisible():
                self._overlay.hide()
                logger.debug("트레이 클릭 → 오버레이 숨김")
            else:
                self._overlay.show()
                logger.debug("트레이 클릭 → 오버레이 표시")
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()
            logger.debug("트레이 더블클릭 → 메인 창 표시")

    def _on_open_settings(self):
        """트레이 '설정' → 설정 다이얼로그 열기"""
        dlg = SettingsDialog(self)
        dlg.exec()

    def _on_update_available(self, info: dict):
        """백그라운드 업데이트 체크 결과 — 트레이 풍선 알림"""
        self._tray.showMessage(
            "Widget Manager 업데이트",
            f"새 버전 {info['version']}이(가) 있습니다. 설정 → 업데이트 확인을 눌러 주세요.",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )
        logger.info("업데이트 알림: %s", info["version"])

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
        self._action_theme.setText(self._theme_label())

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

    def _on_new_task_range(self, start_date, end_date):
        dlg = TaskDialog(self._store, default_date=start_date, default_end_date=end_date, parent=self)
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
