"""Hello Plugin — 플러그인 시스템 동작을 확인하는 데모 플러그인."""
import logging
from core.plugin_api import PluginBase

logger = logging.getLogger(__name__)


class HelloPlugin(PluginBase):
    name = "Hello Plugin"
    version = "0.1.0"
    description = "플러그인 시스템 동작을 확인하는 데모 플러그인"
    author = "Widget Manager"

    def on_load(self, ctx):
        super().on_load(ctx)
        logger.info("Hello Plugin 로드됨 — 현재 일감 수: %d", len(ctx.store))

    def on_unload(self):
        logger.info("Hello Plugin 언로드됨")

    def on_store_changed(self):
        logger.debug("Hello Plugin: 일감 데이터 변경 감지")

    def get_menu_actions(self):
        return [("Hello Plugin 정보...", self._show_info)]

    def _show_info(self):
        from PyQt6.QtWidgets import QMessageBox
        parent = self._ctx.main_window if self._ctx else None
        QMessageBox.information(
            parent,
            "Hello Plugin",
            f"<b>{self.name}</b> v{self.version}<br><br>{self.description}",
        )
