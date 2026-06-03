"""플러그인 로더 — 발견 · 로드 · 훅 발신."""
from __future__ import annotations
import importlib
import inspect
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from core.plugin_api import PluginBase

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow
    from core.settings import Settings
    from core.task_store import TaskStore

logger = logging.getLogger(__name__)

_PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"


class AppContext:
    """플러그인에 앱 API를 노출하는 컨텍스트 객체."""

    def __init__(
        self,
        store: "TaskStore",
        settings: "Settings",
        main_window: "QMainWindow | None" = None,
    ):
        self.store = store
        self.settings = settings
        self.main_window = main_window

    def get_plugin_setting(self, plugin_name: str, key: str, default=None):
        """플러그인 전용 네임스페이스에서 설정 값을 읽는다."""
        return self.settings.get(f"plugin_{plugin_name}", {}).get(key, default)

    def set_plugin_setting(self, plugin_name: str, key: str, value) -> None:
        """플러그인 전용 네임스페이스에 설정 값을 저장한다."""
        ns = f"plugin_{plugin_name}"
        data = dict(self.settings.get(ns, {}))
        data[key] = value
        self.settings.set(ns, data)


class PluginLoader:
    """
    ``plugins/`` 디렉터리에서 플러그인을 발견·로드·관리한다.

    플러그인 패키지 구조::

        plugins/
          my_plugin/
            __init__.py   ← PluginBase 서브클래스를 정의

    플러그인 이름은 디렉터리 이름과 같다.
    """

    def __init__(self, plugins_dir: Path = _PLUGINS_DIR):
        self._dir = plugins_dir
        self._loaded: dict[str, PluginBase] = {}
        self._ctx: AppContext | None = None

    # ── 초기화 ────────────────────────────────────────────────────────────
    def init(self, ctx: AppContext) -> None:
        """AppContext를 주입하고 TaskStore 변경 구독을 시작한다."""
        self._ctx = ctx
        ctx.store.subscribe(self._on_store_changed)

    # ── 발견 ─────────────────────────────────────────────────────────────
    def discover(self) -> list[str]:
        """``plugins/`` 디렉터리에서 유효한 플러그인 이름 목록을 반환한다."""
        if not self._dir.is_dir():
            return []
        return sorted(
            item.name
            for item in self._dir.iterdir()
            if item.is_dir()
            and (item / "__init__.py").exists()
            and item.name != "__pycache__"
        )

    # ── 로드 / 언로드 ──────────────────────────────────────────────────
    def load(self, plugin_name: str) -> bool:
        """플러그인 하나를 임포트하고 on_load()를 호출한다. 성공하면 True."""
        if plugin_name in self._loaded:
            return True
        try:
            module_path = f"plugins.{plugin_name}"
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)

            cls = self._find_plugin_class(module)
            if cls is None:
                logger.warning("PluginBase 서브클래스 없음: %s", plugin_name)
                return False

            instance: PluginBase = cls()
            if self._ctx is not None:
                instance.on_load(self._ctx)
            self._loaded[plugin_name] = instance
            logger.info("플러그인 로드: %s v%s", instance.name or plugin_name, instance.version)
            return True
        except Exception:
            logger.exception("플러그인 로드 실패: %s", plugin_name)
            return False

    def unload(self, plugin_name: str) -> bool:
        """플러그인의 on_unload()를 호출하고 제거한다. 성공하면 True."""
        if plugin_name not in self._loaded:
            return False
        try:
            self._loaded[plugin_name].on_unload()
        except Exception:
            logger.exception("on_unload 오류: %s", plugin_name)
        del self._loaded[plugin_name]
        logger.info("플러그인 언로드: %s", plugin_name)
        return True

    def load_enabled(self, names: list[str]) -> None:
        """names 목록의 플러그인을 순서대로 로드한다."""
        for name in names:
            self.load(name)

    # ── 훅 발신 ────────────────────────────────────────────────────────
    def emit(self, hook: str, *args, **kwargs) -> None:
        """로드된 모든 플러그인에 hook 메서드를 호출한다. 예외는 격리된다."""
        for name, plugin in list(self._loaded.items()):
            method = getattr(plugin, hook, None)
            if callable(method):
                try:
                    method(*args, **kwargs)
                except Exception:
                    logger.exception("플러그인 훅 오류 [%s.%s]", name, hook)

    def _on_store_changed(self) -> None:
        self.emit("on_store_changed")

    # ── 정보 접근 ──────────────────────────────────────────────────────
    def get_loaded(self) -> dict[str, PluginBase]:
        """현재 로드된 플러그인 {이름: 인스턴스}를 반환한다."""
        return dict(self._loaded)

    def all_menu_actions(self) -> list[tuple[str, "callable"]]:
        """모든 플러그인의 get_menu_actions() 결과를 합쳐 반환한다."""
        actions: list = []
        for name, plugin in self._loaded.items():
            try:
                actions.extend(plugin.get_menu_actions())
            except Exception:
                logger.exception("메뉴 액션 수집 실패: %s", name)
        return actions

    @staticmethod
    def _find_plugin_class(module: ModuleType):
        """모듈에서 PluginBase의 구체 서브클래스를 찾아 반환한다."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, PluginBase)
                and obj is not PluginBase
                and obj.__module__ == module.__name__
            ):
                return obj
        return None
