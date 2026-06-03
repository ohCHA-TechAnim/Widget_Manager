"""앱 설정 저장/로드 — 테마·포인트색 등."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SETTINGS_PATH = (
    Path.home() / "AppData" / "Roaming" / "Widget_Manager" / "settings.json"
)

_DEFAULTS: dict = {
    "theme": "light",
    "accent_color": "#4A90D9",
}


class Settings:
    def __init__(self, path: Path = _SETTINGS_PATH):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.debug("설정 로드: %s", self._path)
            except Exception as exc:
                logger.error("설정 로드 실패: %s", exc)
                self._data = {}

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error("설정 저장 실패: %s", exc)

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()
