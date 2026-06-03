"""Windows 시작프로그램 등록/해제 헬퍼 (HKCU Run 레지스트리 키)"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_APP_NAME = "WidgetManager"
_REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows() -> bool:
    return sys.platform == "win32"


def get_exe_path() -> str:
    """등록할 실행 명령어 반환. 패키지 환경이면 exe 경로, 개발 환경이면 pythonw + main.py."""
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    main_py = (Path(__file__).parent.parent / "main.py").resolve()
    runner = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{runner}" "{main_py}"'


def is_registered() -> bool:
    """시작프로그램에 등록되어 있는지 확인."""
    if not _is_windows():
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception as exc:
        logger.error("시작프로그램 상태 확인 실패: %s", exc)
        return False


def register() -> bool:
    """HKCU Run 키에 앱을 등록한다."""
    if not _is_windows():
        return False
    try:
        import winreg
        cmd = get_exe_path()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, cmd)
        logger.info("시작프로그램 등록: %s", cmd)
        return True
    except Exception as exc:
        logger.error("시작프로그램 등록 실패: %s", exc)
        return False


def unregister() -> bool:
    """HKCU Run 키에서 앱을 제거한다."""
    if not _is_windows():
        return False
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, _APP_NAME)
                logger.info("시작프로그램 등록 해제 완료")
            except FileNotFoundError:
                pass
        return True
    except Exception as exc:
        logger.error("시작프로그램 등록 해제 실패: %s", exc)
        return False
