"""넥슨 SharePoint Excel 다운로더 (QThread + Selenium).

TaskHub/utils/selenium_downloader.py 를 Widget_Manager 플러그인으로 이식.
검증된 부분: MS 로그인 흐름, stale element 재시도(_act_with_retry), 디버그 덤프.
변경 사항: print() → logging, 다운로드 경로 AppData/downloads로 일원화.
"""
import logging
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

from utils.resource_path import get_downloads_dir, get_debug_dir

logger = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT = 60  # seconds — Chrome 다운로드 완료 최대 대기


class SharePointDownloader(QThread):
    """SharePoint 라이브러리에서 엑셀을 비동기 다운로드하는 QThread."""

    progress_signal = pyqtSignal(int, str)   # (퍼센트, 메시지)
    finished_signal = pyqtSignal(str)        # 다운로드 완료된 파일 절대 경로
    failed_signal = pyqtSignal(str)

    def __init__(
        self,
        target_name: str,
        nexon_id: str,
        nexon_pw: str,
        library_url: str,
        file_keyword: str = "스케쥴_애니메이션팀",
    ):
        super().__init__()
        self.target_name = target_name
        self.nexon_id = nexon_id
        self.nexon_pw = nexon_pw
        self.library_url = library_url
        self.file_keyword = file_keyword
        self._is_running = True

    # ── TaskHub 검증 패턴 ─────────────────────────────────────────────────
    def _act_with_retry(self, driver, action, by, value, wait, retries=3, scroll=True):
        """stale element 방어 — '찾는 즉시 사용' + 실패 시 재탐색·재시도."""
        last_exc = None
        for _ in range(retries):
            try:
                el = wait.until(EC.presence_of_element_located((by, value)))
                if scroll:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", el
                    )
                    time.sleep(0.8)
                action(driver, el)
                return
            except StaleElementReferenceException as exc:
                last_exc = exc
                time.sleep(1.0)
        if last_exc:
            raise last_exc

    def _dump_debug(self, driver) -> None:
        """실패 시 스크린샷·HTML 덤프를 debug 폴더에 저장 (진단용)."""
        try:
            debug_dir = get_debug_dir()
            driver.save_screenshot(str(debug_dir / "sp_error_shot.png"))
            with open(debug_dir / "sp_error_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("디버그 덤프 저장: %s", debug_dir)
        except Exception:
            logger.exception("디버그 덤프 저장 실패")

    def _clean_downloads_dir(self, downloads_dir: Path) -> None:
        """재다운로드 idempotency — 기존 .xlsx/.crdownload 잔재를 제거한다."""
        removed = 0
        for pattern in ("*.xlsx", "*.crdownload"):
            for f in downloads_dir.glob(pattern):
                try:
                    f.unlink()
                    removed += 1
                except Exception:
                    logger.warning("기존 파일 삭제 실패: %s", f)
        if removed:
            logger.info("downloads 폴더 정리: %d개 파일 삭제", removed)

    def _wait_for_download(self, downloads_dir: Path) -> Path | None:
        """downloads_dir에 .xlsx가 나타나고 .crdownload가 없어질 때까지 폴링."""
        for elapsed in range(_DOWNLOAD_TIMEOUT):
            xlsx_files = sorted(
                downloads_dir.glob("*.xlsx"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            crdownload_files = list(downloads_dir.glob("*.crdownload"))
            if xlsx_files and not crdownload_files:
                logger.info("다운로드 감지: %s (경과 %d초)", xlsx_files[0].name, elapsed)
                return xlsx_files[0]
            time.sleep(1)
        return None

    # ── 메인 다운로드 로직 ─────────────────────────────────────────────────
    def run(self):
        driver = None
        try:
            self.progress_signal.emit(10, "Chrome 드라이버 초기화 중...")
            logger.info("SharePoint 다운로드 시작 (ID: %s)", self.nexon_id)

            downloads_dir = get_downloads_dir()
            self._clean_downloads_dir(downloads_dir)
            logger.info("다운로드 대상 폴더: %s", downloads_dir)

            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            prefs = {
                "download.default_directory": str(downloads_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            options.add_experimental_option("prefs", prefs)

            try:
                driver = webdriver.Chrome(options=options)
            except Exception as exc:
                raise RuntimeError(
                    f"Chrome/chromedriver 초기화 실패: {exc}\n"
                    "Chrome과 chromedriver 버전이 일치하는지 확인하세요.\n"
                    "https://chromedriver.chromium.org/downloads"
                ) from exc

            wait = WebDriverWait(driver, 30)

            # ── MS 로그인 흐름 (TaskHub 검증 코드 그대로) ───────────────────
            self.progress_signal.emit(30, "SharePoint 접속 및 로그인 중...")
            driver.get(self.library_url)

            email_input = wait.until(EC.element_to_be_clickable((By.NAME, "loginfmt")))
            email_input.clear()
            email_input.send_keys(self.nexon_id)
            wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
            time.sleep(1.5)

            self.progress_signal.emit(50, "비밀번호 검증 중...")
            pw_input = wait.until(EC.element_to_be_clickable((By.NAME, "passwd")))
            pw_input.clear()
            pw_input.send_keys(self.nexon_pw)
            wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()

            # "로그인 상태 유지?" → 건너뜀
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "idBtn_Back"))
                ).click()
            except Exception:
                pass

            # ── 파일 탐색 + 우클릭 다운로드 ─────────────────────────────────
            self.progress_signal.emit(70, f"'{self.file_keyword}' 파일 탐색 중...")
            kw = self.file_keyword
            file_xpath = (
                f"//*[contains(@title, '{kw}')] "
                f"| //*[contains(text(), '{kw}')]"
            )
            wait.until(EC.element_to_be_clickable((By.XPATH, file_xpath)))
            self._act_with_retry(
                driver,
                lambda drv, el: ActionChains(drv).context_click(el).perform(),
                By.XPATH, file_xpath, wait,
            )
            time.sleep(1.5)

            self.progress_signal.emit(85, "다운로드 명령 전송 중...")
            dl_btn_xpath = (
                "//button[@data-automationid='downloadCommand']"
                " | //button[.//span[contains(text(),'다운로드') or contains(text(),'Download')]]"
            )
            self._act_with_retry(
                driver,
                lambda drv, el: drv.execute_script("arguments[0].click();", el),
                By.XPATH, dl_btn_xpath, wait,
            )

            # ── 다운로드 완료 감지 (.crdownload 폴링) ─────────────────────────
            self.progress_signal.emit(95, f"다운로드 완료 대기 중... (최대 {_DOWNLOAD_TIMEOUT}초)")
            logger.info("downloads 폴더 폴링 시작: %s", downloads_dir)
            found = self._wait_for_download(downloads_dir)

            if found:
                self.progress_signal.emit(100, "완료")
                logger.info("SharePoint 엑셀 다운로드 완료: %s", found)
                self.finished_signal.emit(str(found))
            else:
                self._dump_debug(driver)
                debug_dir = get_debug_dir()
                self.failed_signal.emit(
                    f"다운로드 타임아웃 ({_DOWNLOAD_TIMEOUT}초 초과)\n"
                    f"디버그 스크린샷: {debug_dir / 'sp_error_shot.png'}"
                )

        except Exception as exc:
            logger.exception("SharePoint 다운로드 실패")
            if driver is not None:
                self._dump_debug(driver)
            self.failed_signal.emit(str(exc))
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
