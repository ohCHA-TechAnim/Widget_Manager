"""PyInstaller 대응 리소스 경로 헬퍼.

패키지 환경(--windowed exe)에서는 sys._MEIPASS가 번들 루트이므로
그 경로를 sys.path에 삽입해 'plugins.*' 임포트가 동작하도록 한다.
"""
import os
import sys
from pathlib import Path

if hasattr(sys, '_MEIPASS'):
    _ROOT = Path(sys._MEIPASS)
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
else:
    _ROOT = Path(__file__).resolve().parent.parent


def resource_path(relative: str) -> Path:
    """개발 환경과 PyInstaller 패키지 환경 모두에서 올바른 리소스 경로를 반환한다."""
    return _ROOT / relative


# ── 앱 전용 AppData 경로 헬퍼 ─────────────────────────────────────────────────
_appdata_env = os.environ.get("APPDATA")
_APP_ROOT = (
    Path(_appdata_env) / "Widget_Manager"
    if _appdata_env
    else Path.home() / "AppData" / "Roaming" / "Widget_Manager"
)


def _app_dir(subdir: str) -> Path:
    p = _APP_ROOT / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_data_dir() -> Path:
    return _app_dir("data")


def get_logs_dir() -> Path:
    return _app_dir("logs")


def get_downloads_dir() -> Path:
    return _app_dir("downloads")


def get_debug_dir() -> Path:
    return _app_dir("debug")
