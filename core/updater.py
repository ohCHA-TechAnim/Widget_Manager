"""GitHub Releases 기반 자동 업데이트 체커."""
import json
import logging
import urllib.request
from urllib.error import URLError

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

APP_VERSION = "0.2.1"
_GITHUB_REPO = "ohCHA-TechAnim/Widget_Manager"
_API_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
RELEASES_PAGE_URL = f"https://github.com/{_GITHUB_REPO}/releases/latest"


def _parse_version(v: str) -> tuple:
    """'v0.2.1' → (0, 2, 1)"""
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except ValueError:
        return (0,)


def check_for_update() -> dict | None:
    """
    GitHub 최신 릴리즈를 확인한다.
    현재 버전보다 새 버전이면 {'version', 'body', 'html_url'} dict 반환, 아니면 None.
    """
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "WidgetManager",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            return None
        if _parse_version(latest_tag) > _parse_version(APP_VERSION):
            return {
                "version": latest_tag,
                "body": data.get("body", ""),
                "html_url": data.get("html_url", RELEASES_PAGE_URL),
            }
        return None
    except URLError as exc:
        logger.debug("업데이트 확인 실패 (네트워크): %s", exc)
        return None
    except Exception as exc:
        logger.warning("업데이트 확인 실패: %s", exc)
        return None


class UpdateChecker(QThread):
    """백그라운드에서 업데이트를 체크하는 Qt 스레드."""

    update_available = pyqtSignal(dict)

    def run(self):
        info = check_for_update()
        if info:
            self.update_available.emit(info)
