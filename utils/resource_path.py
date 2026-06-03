"""PyInstaller 대응 리소스 경로 헬퍼.

패키지 환경(--windowed exe)에서는 sys._MEIPASS가 번들 루트이므로
그 경로를 sys.path에 삽입해 'plugins.*' 임포트가 동작하도록 한다.
"""
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
