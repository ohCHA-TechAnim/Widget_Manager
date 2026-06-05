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
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
)

from utils.resource_path import get_downloads_dir, get_debug_dir

logger = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT = 60  # seconds — Chrome 다운로드 완료 최대 대기

# failed_signal 에 이 접두사가 붙으면 비밀번호 오류 → 재입력 UX 트리거
LOGIN_FAILED_PREFIX = "LOGIN_FAILED:"


class LoginFailedError(Exception):
    """MS 로그인 실패 (잘못된 비밀번호)."""


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

    # ── 로그인 실패 감지 ──────────────────────────────────────────────────
    def _check_login_failure(self, driver) -> bool:
        """비밀번호 오입력으로 인한 MS 로그인 실패 여부 확인.

        SharePoint로 이미 이동했다면 False.
        MS 로그인 페이지에 오류 요소가 보이면 True.
        """
        try:
            if "sharepoint.com" in driver.current_url:
                return False
        except Exception:
            pass

        # MS 로그인 에러 요소 확인
        for error_id in ("idTD_Error", "passwordError"):
            try:
                el = driver.find_element(By.ID, error_id)
                if el.is_displayed() and el.text.strip():
                    logger.warning("로그인 에러 요소 감지: #%s = '%s'", error_id, el.text.strip()[:80])
                    return True
            except Exception:
                pass

        # passwd 필드가 여전히 존재하고 MS 도메인에 있으면 로그인 실패로 간주
        try:
            driver.find_element(By.NAME, "passwd")
            if "login.microsoftonline.com" in driver.current_url:
                logger.warning("passwd 필드 여전히 존재 — 로그인 미완료")
                return True
        except NoSuchElementException:
            pass
        except Exception:
            pass

        return False

    # ── SharePoint 페이지 로드 대기 ───────────────────────────────────────
    def _wait_for_sharepoint_load(self, driver) -> None:
        """로그인 후 SharePoint 파일 목록이 렌더될 때까지 대기."""
        # document.readyState == "complete" 대기 (최대 20초)
        for _ in range(20):
            try:
                if driver.execute_script("return document.readyState") == "complete":
                    break
            except Exception:
                pass
            time.sleep(1)

        # SharePoint SPFx 파일 목록 컨테이너 대기 (최대 15초)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "[data-automationid='list'], [role='grid'], [role='list'], "
                     "[data-automationid='fileListCommandBar']")
                )
            )
        except Exception:
            pass  # 못 찾아도 이어서 시도

        time.sleep(2)  # React 렌더 마무리 버퍼
        logger.info("SharePoint 페이지 로드 대기 완료 (URL: %s)", driver.current_url)

    # ── 파일 탐색 실패 진단 ───────────────────────────────────────────────
    def _dump_file_search_diagnostics(self, driver, keyword: str) -> None:
        """파일 탐색 실패 시 스크린샷·HTML·후보 목록을 debug 폴더에 저장."""
        try:
            debug_dir = get_debug_dir()
            driver.save_screenshot(str(debug_dir / "sp_search_fail.png"))
            with open(debug_dir / "sp_search_fail.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            candidates: set[str] = set()
            for attr in ("title", "aria-label"):
                try:
                    for el in driver.find_elements(
                        By.XPATH, f"//*[@{attr} and string-length(@{attr}) > 3]"
                    ):
                        try:
                            val = el.get_attribute(attr)
                            if val:
                                candidates.add(val[:120])
                        except Exception:
                            pass
                except Exception:
                    pass

            logger.warning("==== 파일 탐색 실패 진단 ====")
            logger.warning("찾으려는 검색어: '%s'", keyword)
            logger.warning("페이지 title/aria-label 후보 목록 (%d개):", len(candidates))
            for c in sorted(candidates):
                logger.warning("  후보: %s", c)
            logger.warning("디버그 덤프 저장 위치: %s", debug_dir)
        except Exception:
            logger.exception("파일 탐색 진단 덤프 저장 실패")

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

            # ── MS 로그인 흐름 ─────────────────────────────────────────────
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

            # 비밀번호 제출 후 오류 or 다음 화면 대기 (최대 8초)
            time.sleep(4)
            if self._check_login_failure(driver):
                raise LoginFailedError("비밀번호가 올바르지 않습니다")

            # "로그인 상태 유지?" → 건너뜀
            try:
                WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.ID, "idBtn_Back"))
                ).click()
            except Exception:
                pass

            # ── SharePoint 페이지 완전 로드 대기 ──────────────────────────
            self.progress_signal.emit(65, "SharePoint 페이지 로드 중...")
            self._wait_for_sharepoint_load(driver)

            # ── 파일 탐색 + 우클릭 다운로드 ──────────────────────────────
            self.progress_signal.emit(70, f"'{self.file_keyword}' 파일 탐색 중...")
            kw = self.file_keyword
            file_xpath = (
                f"//*[contains(@title, '{kw}')] "
                f"| //*[contains(text(), '{kw}')] "
                f"| //*[contains(@aria-label, '{kw}')]"
            )
            logger.info("파일 탐색 XPath: %s", file_xpath)

            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, file_xpath)))
            except TimeoutException:
                self._dump_file_search_diagnostics(driver, kw)
                debug_dir = get_debug_dir()
                raise RuntimeError(
                    f"검색어 '{kw}'에 해당하는 파일을 페이지에서 찾을 수 없습니다.\n"
                    f"설정의 '파일 검색어'가 SharePoint 실제 파일명과 일치하는지 확인하세요.\n"
                    f"(debug 폴더에 페이지 덤프 저장됨: {debug_dir})"
                )

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

            # ── 다운로드 완료 감지 (.crdownload 폴링) ─────────────────────
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

        except LoginFailedError as exc:
            logger.warning("MS 로그인 실패 (비밀번호 오류): %s", exc)
            self.failed_signal.emit(f"{LOGIN_FAILED_PREFIX}{exc}")

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
