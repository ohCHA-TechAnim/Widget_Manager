"""일감 저장소 — 데이터 CRUD + JSON 영속화 + 변경 통지"""
import json
import logging
import uuid
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# 기본 저장 경로: %APPDATA%\Widget_Manager\data\tasks.json
_DEFAULT_DATA_DIR = Path.home() / "AppData" / "Roaming" / "Widget_Manager" / "data"


def _default_task(
    title: str = "",
    start: str = "",
    end: str = "",
    status: str = "todo",
    priority: str = "mid",
    memo: str = "",
    color: str = "#4A90D9",
    source: str = "manual",
    jiras: list | None = None,
    folders: list | None = None,
    attachments: list | None = None,
) -> dict:
    """새 일감 딕셔너리를 기본값으로 생성한다."""
    today = date.today().isoformat()
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "start": start or today,
        "end": end or start or today,
        "status": status,          # "todo" | "doing" | "done"
        "priority": priority,      # "high" | "mid" | "low"
        "memo": memo,
        "color": color,
        "jiras": jiras if jiras is not None else [],
        "folders": folders if folders is not None else [],
        "attachments": attachments if attachments is not None else [],
        "source": source,          # "manual" 또는 애드온 id
        "deco_image": None,        # 칸별 꾸미기 이미지 경로
    }


# 허용 status / priority 값
_VALID_STATUS = {"todo", "doing", "done"}
_VALID_PRIORITY = {"high", "mid", "low"}


def _validate(task: dict) -> None:
    """기본 유효성 검사 — 잘못된 값이면 ValueError 발생."""
    if not task.get("title", "").strip():
        raise ValueError("title은 빈 문자열일 수 없습니다.")
    if task.get("status") not in _VALID_STATUS:
        raise ValueError(f"status는 {_VALID_STATUS} 중 하나여야 합니다.")
    if task.get("priority") not in _VALID_PRIORITY:
        raise ValueError(f"priority는 {_VALID_PRIORITY} 중 하나여야 합니다.")


class TaskStore:
    """
    일감 데이터의 단일 진실 소스.
    뷰가 변경 통지를 받으려면 subscribe()로 콜백을 등록한다.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self._path: Path = (data_path or _DEFAULT_DATA_DIR / "tasks.json")
        self._tasks: dict[str, dict] = {}        # id → task
        self._listeners: list[Callable] = []
        self.load()

    # ------------------------------------------------------------------
    # 영속화
    # ------------------------------------------------------------------
    def load(self) -> None:
        """디스크에서 tasks.json을 읽는다. 파일이 없으면 빈 상태로 시작."""
        if not self._path.exists():
            logger.info("tasks.json 없음 — 빈 상태로 시작: %s", self._path)
            self._tasks = {}
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                raw = json.load(f)
            self._tasks = {t["id"]: t for t in raw}
            logger.info("tasks.json 로드 완료 — %d건", len(self._tasks))
        except Exception:
            logger.exception("tasks.json 로드 실패")
            self._tasks = {}

    def save(self) -> None:
        """현재 상태를 tasks.json에 저장한다."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(list(self._tasks.values()), f, ensure_ascii=False, indent=2)
            logger.debug("tasks.json 저장 완료 — %d건", len(self._tasks))
        except Exception:
            logger.exception("tasks.json 저장 실패")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def add(self, **kwargs) -> dict:
        """새 일감을 추가하고 저장 후 반환한다."""
        task = _default_task(**kwargs)
        _validate(task)
        self._tasks[task["id"]] = task
        self.save()
        self._notify()
        logger.info("일감 추가: %s (%s)", task["title"], task["id"])
        return deepcopy(task)

    def update(self, task_id: str, **fields) -> dict:
        """지정 id 일감의 필드를 수정하고 저장 후 반환한다."""
        if task_id not in self._tasks:
            raise KeyError(f"일감을 찾을 수 없음: {task_id}")
        task = self._tasks[task_id]
        task.update(fields)
        _validate(task)
        self.save()
        self._notify()
        logger.info("일감 수정: %s (%s)", task["title"], task_id)
        return deepcopy(task)

    def delete(self, task_id: str) -> None:
        """지정 id 일감을 삭제하고 저장한다."""
        if task_id not in self._tasks:
            raise KeyError(f"일감을 찾을 수 없음: {task_id}")
        title = self._tasks[task_id]["title"]
        del self._tasks[task_id]
        self.save()
        self._notify()
        logger.info("일감 삭제: %s (%s)", title, task_id)

    def get(self, task_id: str) -> dict:
        """id로 단일 일감을 반환한다 (복사본)."""
        if task_id not in self._tasks:
            raise KeyError(f"일감을 찾을 수 없음: {task_id}")
        return deepcopy(self._tasks[task_id])

    def all(self) -> list[dict]:
        """전체 일감 목록을 복사본으로 반환한다."""
        return [deepcopy(t) for t in self._tasks.values()]

    def by_date_range(self, start: str, end: str) -> list[dict]:
        """start~end(YYYY-MM-DD) 범위에 걸치는 일감 목록을 반환한다."""
        result = []
        for t in self._tasks.values():
            # 일감 기간과 쿼리 기간이 겹치면 포함
            if t["start"] <= end and t["end"] >= start:
                result.append(deepcopy(t))
        return result

    # ------------------------------------------------------------------
    # 변경 통지 (옵저버)
    # ------------------------------------------------------------------
    def subscribe(self, callback: Callable) -> None:
        """변경 시 호출될 콜백을 등록한다."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        """콜백 등록을 해제한다."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                logger.exception("변경 통지 콜백 오류")

    def __len__(self) -> int:
        return len(self._tasks)
