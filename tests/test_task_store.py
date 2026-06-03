"""task_store.py 단독 테스트 — Qt 없이 실행."""
import json
import sys
import tempfile
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.task_store import TaskStore


def make_store(tmp_path: Path) -> TaskStore:
    return TaskStore(data_path=tmp_path / "tasks.json")


def test_add_and_load():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        store = make_store(p)
        task = store.add(title="테스트 일감", start="2026-06-01", end="2026-06-05")
        assert task["title"] == "테스트 일감"
        assert task["status"] == "todo"
        assert task["source"] == "manual"
        assert len(store) == 1

        # 재로드 후 동일 데이터
        store2 = make_store(p)
        assert len(store2) == 1
        loaded = store2.all()[0]
        assert loaded["title"] == "테스트 일감"
    print("[PASS] test_add_and_load")


def test_update():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        task = store.add(title="수정 전", start="2026-06-01", end="2026-06-01")
        updated = store.update(task["id"], title="수정 후", status="doing")
        assert updated["title"] == "수정 후"
        assert updated["status"] == "doing"
    print("[PASS] test_update")


def test_delete():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        task = store.add(title="삭제될 일감", start="2026-06-01", end="2026-06-01")
        store.delete(task["id"])
        assert len(store) == 0
        store2 = make_store(Path(td))
        assert len(store2) == 0
    print("[PASS] test_delete")


def test_by_date_range():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        store.add(title="범위 안", start="2026-06-03", end="2026-06-07")
        store.add(title="범위 밖(이전)", start="2026-05-01", end="2026-05-31")
        store.add(title="범위 밖(이후)", start="2026-07-01", end="2026-07-10")
        store.add(title="범위 걸침(앞)", start="2026-05-28", end="2026-06-04")

        result = store.by_date_range("2026-06-01", "2026-06-30")
        titles = {t["title"] for t in result}
        assert "범위 안" in titles
        assert "범위 걸침(앞)" in titles
        assert "범위 밖(이전)" not in titles
        assert "범위 밖(이후)" not in titles
    print("[PASS] test_by_date_range")


def test_subscribe_notify():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        called = []
        store.subscribe(lambda: called.append(1))
        store.add(title="알림 테스트", start="2026-06-01", end="2026-06-01")
        assert len(called) == 1
        store.add(title="두 번째", start="2026-06-02", end="2026-06-02")
        assert len(called) == 2
    print("[PASS] test_subscribe_notify")


def test_validation_empty_title():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        try:
            store.add(title="  ", start="2026-06-01", end="2026-06-01")
            assert False, "ValueError가 발생해야 합니다."
        except ValueError:
            pass
    print("[PASS] test_validation_empty_title")


def test_validation_bad_status():
    with tempfile.TemporaryDirectory() as td:
        store = make_store(Path(td))
        task = store.add(title="상태 검사", start="2026-06-01", end="2026-06-01")
        try:
            store.update(task["id"], status="invalid_status")
            assert False, "ValueError가 발생해야 합니다."
        except ValueError:
            pass
    print("[PASS] test_validation_bad_status")


if __name__ == "__main__":
    test_add_and_load()
    test_update()
    test_delete()
    test_by_date_range()
    test_subscribe_notify()
    test_validation_empty_title()
    test_validation_bad_status()
    print("\n모든 테스트 통과!")
