"""플러그인 공개 API — 플러그인은 PluginBase를 상속해 구현한다."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.plugin_loader import AppContext


class PluginBase:
    """모든 플러그인이 상속해야 하는 기본 클래스.

    서브클래스는 클래스 속성(name, version, description, author)을 재정의하고
    필요한 훅 메서드를 오버라이드한다.
    """

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    author: str = ""

    def __init__(self):
        self._ctx: "AppContext | None" = None

    # ── 수명 주기 훅 ──────────────────────────────────────────────────────
    def on_load(self, ctx: "AppContext") -> None:
        """플러그인 로드 시 호출. ctx를 저장해 두면 앱에 접근할 수 있다."""
        self._ctx = ctx

    def on_unload(self) -> None:
        """플러그인 언로드(비활성화) 시 호출."""

    # ── 일감 스토어 훅 ────────────────────────────────────────────────────
    def on_store_changed(self) -> None:
        """일감 데이터가 변경(추가·수정·삭제)된 직후 호출."""

    # ── UI 확장 ───────────────────────────────────────────────────────────
    def get_menu_actions(self) -> list[tuple[str, "callable"]]:
        """플러그인 메뉴에 노출할 (레이블, 콜백) 목록을 반환한다."""
        return []
