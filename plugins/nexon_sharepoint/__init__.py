"""넥슨 SharePoint 일정 플러그인 — Widget_Manager 1라운드 애드온.

on_load / on_unload / get_menu_actions 구현.
Selenium·openpyxl은 실행 시점에만 import(코어 격리 — 없어도 플러그인 로드 성공).
"""
import logging
from datetime import date

from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

from core.plugin_api import PluginBase

logger = logging.getLogger(__name__)

_PLUGIN_NAME = "nexon_sharepoint"


class NexonSharePointPlugin(PluginBase):
    name = "Nexon SharePoint"
    version = "0.1.0"
    description = "넥슨 SharePoint 애니메이션팀 일정을 가져와 달력에 표시합니다."
    author = "차승현"

    def __init__(self):
        super().__init__()
        self._downloader = None
        self._pending_sheet: str = "애니메이션"
        self._pending_target: str = ""
        self._pending_file_keyword: str = "스케쥴_애니메이션팀(2026)"
        self._pending_nexon_id: str = ""
        self._pending_library_url: str = ""
        self._login_attempts: int = 0
        self._max_login_attempts: int = 3  # 비밀번호 시도 최대 횟수

    # ── 수명 주기 ─────────────────────────────────────────────────────────
    def on_load(self, ctx):
        super().on_load(ctx)
        logger.info("Nexon SharePoint 플러그인 로드됨")

    def on_unload(self):
        if self._downloader and self._downloader.isRunning():
            self._downloader.quit()
            self._downloader.wait(3000)
        logger.info("Nexon SharePoint 플러그인 언로드됨")

    # ── UI 확장 ───────────────────────────────────────────────────────────
    def get_menu_actions(self) -> list[tuple]:
        actions = [("SharePoint 설정...", self._open_settings)]
        if self._is_enabled():
            actions.insert(0, ("SharePoint 일정 가져오기", self._fetch_schedule))
        return actions

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────
    def _is_enabled(self) -> bool:
        if self._ctx is None:
            return False
        return bool(self._ctx.get_plugin_setting(_PLUGIN_NAME, "enabled", False))

    def _get(self, key: str, default=""):
        return self._ctx.get_plugin_setting(_PLUGIN_NAME, key, default)

    def _open_settings(self):
        from plugins.nexon_sharepoint.settings_dialog import SharePointSettingsDialog
        parent = self._ctx.main_window if self._ctx else None
        dlg = SharePointSettingsDialog(self._ctx, parent)
        dlg.exec()
        mw = self._ctx.main_window if self._ctx else None
        if mw and hasattr(mw, "_refresh_plugin_menu"):
            mw._refresh_plugin_menu()

    def _fetch_schedule(self):
        if self._ctx is None:
            return

        nexon_id = self._get("nexon_id")
        library_url = self._get("library_url")
        sheet_name = self._get("sheet_name", "애니메이션")
        target_name = self._get("target_name")
        file_keyword = self._get("file_keyword", "스케쥴_애니메이션팀(2026)")
        parent = self._ctx.main_window

        if not nexon_id or not library_url or not target_name:
            QMessageBox.warning(
                parent,
                "설정 필요",
                "SharePoint 설정을 먼저 완료해 주세요.\n"
                "플러그인 메뉴 → SharePoint 설정...\n\n"
                "필수: 넥슨 ID, 라이브러리 URL, 대상자 이름",
            )
            return

        # 비밀번호 입력 — 평문 저장 금지, 실행 시마다 입력
        pw, ok = QInputDialog.getText(
            parent,
            "넥슨 계정 인증",
            f"{nexon_id} 의 비밀번호를 입력하세요.\n(보안상 저장되지 않습니다.)",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not pw.strip():
            return

        if self._downloader and self._downloader.isRunning():
            QMessageBox.information(parent, "알림", "이미 다운로드가 진행 중입니다.")
            return

        # downloader 지연 임포트 (Selenium 없어도 플러그인 로드 가능)
        try:
            from plugins.nexon_sharepoint.downloader import SharePointDownloader  # noqa: F401
        except ImportError as exc:
            QMessageBox.critical(
                parent,
                "selenium 없음",
                f"selenium 패키지가 설치되지 않았습니다.\n"
                f"pip install selenium 을 실행해 주세요.\n\n{exc}",
            )
            return

        # 다운로드 후 파서에 전달할 정보 보관
        self._pending_sheet = sheet_name
        self._pending_target = target_name
        self._pending_file_keyword = file_keyword
        self._pending_nexon_id = nexon_id
        self._pending_library_url = library_url
        self._login_attempts = 0  # 비밀번호 시도 횟수 초기화

        self._start_downloader(pw.strip())

    def _start_downloader(self, nexon_pw: str) -> None:
        """새 다운로더 스레드를 생성하고 시작한다."""
        if self._ctx is None:
            return

        try:
            from plugins.nexon_sharepoint.downloader import SharePointDownloader
        except ImportError:
            return

        self._downloader = SharePointDownloader(
            target_name=self._pending_target,
            nexon_id=self._pending_nexon_id,
            nexon_pw=nexon_pw,
            library_url=self._pending_library_url,
            file_keyword=self._pending_file_keyword,
        )
        self._downloader.progress_signal.connect(self._on_progress)
        self._downloader.finished_signal.connect(self._on_download_finished)
        self._downloader.failed_signal.connect(self._on_download_failed)
        self._downloader.start()
        logger.info(
            "SharePoint 다운로드 스레드 시작 (시도 %d/%d)",
            self._login_attempts + 1,
            self._max_login_attempts,
        )

        mw = self._ctx.main_window if self._ctx else None
        if mw and hasattr(mw, "statusBar"):
            mw.statusBar().showMessage("SharePoint 일정 다운로드 중...", 0)

    def _on_progress(self, percent: int, message: str):
        logger.debug("SharePoint %d%% — %s", percent, message)
        mw = self._ctx.main_window if self._ctx else None
        if mw and hasattr(mw, "statusBar"):
            mw.statusBar().showMessage(f"SharePoint: {message} ({percent}%)", 0)

    def _on_download_finished(self, excel_path: str):
        logger.info("SharePoint 다운로드 완료 — 파싱 시작: %s", excel_path)
        mw = self._ctx.main_window if self._ctx else None
        if mw and hasattr(mw, "statusBar"):
            mw.statusBar().showMessage("SharePoint 엑셀 파싱 중...", 0)

        try:
            from plugins.nexon_sharepoint.parser import parse_excel
        except ImportError as exc:
            logger.exception("파서 임포트 실패")
            if mw:
                QMessageBox.critical(mw, "파서 오류", f"파서를 로드할 수 없습니다: {exc}")
            return

        tasks = parse_excel(
            excel_path=excel_path,
            target_name=self._pending_target,
            sheet_name=self._pending_sheet,
            target_year=date.today().year,
        )
        logger.info("SharePoint 파싱 완료: %d건", len(tasks))

        self._sync_tasks(tasks)

        if mw and hasattr(mw, "statusBar"):
            mw.statusBar().showMessage(
                f"SharePoint 완료: {len(tasks)}개 일감 반영", 5000
            )

        if tasks:
            QMessageBox.information(
                mw,
                "SharePoint 일정 가져오기 완료",
                f"{len(tasks)}개 일감이 달력에 반영되었습니다.",
            )
        else:
            QMessageBox.warning(
                mw,
                "SharePoint 일정 가져오기",
                "파일은 받았으나 파싱 결과가 0건입니다.\n\n"
                "확인 사항:\n"
                "• 시트 이름이 설정과 일치하는지\n"
                "• 대상자 이름이 엑셀 내 표기와 일치하는지\n"
                "• 셀렉터(열 구조) 변경 여부",
            )

    def _on_download_failed(self, error_msg: str):
        from plugins.nexon_sharepoint.downloader import LOGIN_FAILED_PREFIX

        mw = self._ctx.main_window if self._ctx else None

        if error_msg.startswith(LOGIN_FAILED_PREFIX):
            self._login_attempts += 1

            if self._login_attempts < self._max_login_attempts:
                # 비밀번호 재입력 다이얼로그
                new_pw, ok = QInputDialog.getText(
                    mw,
                    "비밀번호 오류",
                    f"비밀번호가 올바르지 않습니다. 다시 입력해주세요.\n"
                    f"({self._login_attempts}/{self._max_login_attempts - 1}번 시도)",
                    QLineEdit.EchoMode.Password,
                )
                if ok and new_pw.strip():
                    self._start_downloader(new_pw.strip())
                    return
                # 사용자가 취소한 경우 조용히 종료
                if mw and hasattr(mw, "statusBar"):
                    mw.statusBar().showMessage("SharePoint 로그인 취소됨", 3000)
                return

            # 최대 시도 횟수 초과
            logger.error(
                "SharePoint 로그인 %d회 실패 — 중단", self._max_login_attempts
            )
            if mw and hasattr(mw, "statusBar"):
                mw.statusBar().showMessage("SharePoint 로그인 실패", 5000)
            QMessageBox.critical(
                mw,
                "로그인 실패",
                f"비밀번호를 {self._max_login_attempts}회 모두 잘못 입력했습니다.\n"
                "넥슨 계정 ID와 비밀번호를 다시 확인하세요.",
            )
            return

        # 로그인 외 일반 실패
        logger.error("SharePoint 다운로드 실패: %s", error_msg)
        if mw and hasattr(mw, "statusBar"):
            mw.statusBar().showMessage("SharePoint 다운로드 실패", 5000)
        QMessageBox.critical(
            mw,
            "SharePoint 다운로드 실패",
            f"오류: {error_msg}\n\n"
            "확인 사항:\n"
            "• Chrome/chromedriver 버전 일치 여부\n"
            "• 넥슨 ID·비밀번호·라이브러리 URL 정확성\n"
            "• 디버그 스크린샷: AppData\\Roaming\\Widget_Manager\\debug\\\n"
            "• 로그: AppData\\Roaming\\Widget_Manager\\logs\\widget_manager.log",
        )

    def _sync_tasks(self, new_tasks: list[dict]):
        """기존 sharepoint 일감 전체 삭제 후 새 일감 추가. manual 일감 불변."""
        store = self._ctx.store

        old_ids = [t["id"] for t in store.all() if t.get("source") == "sharepoint"]
        for tid in old_ids:
            try:
                store.delete(tid)
            except Exception:
                logger.exception("기존 sharepoint 일감 삭제 실패: %s", tid)

        added = 0
        for task_data in new_tasks:
            try:
                store.add(**task_data)
                added += 1
            except Exception:
                logger.exception("sharepoint 일감 추가 실패: %s", task_data.get("title"))

        logger.info(
            "SharePoint 동기화: 삭제 %d건 → 추가 %d건", len(old_ids), added
        )
