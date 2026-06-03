# Widget_Manager

Python 기반 데스크톱 위젯 매니저. 원격(모바일)에서 지시하면 PC의 Claude Code가 자동으로 개발한다.

---

## 원격 작업 방법

### 1단계 — 지시 작성
[TASK.md 모바일 편집](https://github.com/ohCHA-TechAnim/Widget_Manager/edit/main/TASK.md)을 열어:
- `## 작업 지시` 아래에 원하는 내용을 쓴다.
- 맨 위 `STATUS: IDLE` → `STATUS: PENDING` 으로 바꾼다.
- 커밋 & push.

### 2단계 — 자동 실행
PC의 워처(`scripts/watch_and_run.ps1`)가 60초 안에 감지 → Claude Code가 작업 시작.

### 3단계 — 질문에 답하기 (필요 시)
Claude가 중요한 결정을 못 혼자 내릴 때:
- `STATUS: WAITING_USER` 로 바꾸고 `## ❓ 질문 N` 섹션에 선택지를 적어 push한다.
- 사용자가 `## 💬 답변 N` 에 답을 적고 `STATUS: PENDING` 으로 바꿔 push → Claude가 이어서 진행.

### 4단계 — 완료 확인
`STATUS: DONE` + `## ✅ 완료 노트` 에 요약이 적히면 완료.

---

## 로그 확인

```powershell
# 워처 실시간 로그
Get-Content D:\Projects\Widget_Manager\scripts\task_runner.log -Tail 20

# 스케줄러 상태
Get-ScheduledTask -TaskName "WidgetManagerWatcher" | Get-ScheduledTaskInfo
```

---

## 워처 수동 제어

```powershell
# 시작
Start-ScheduledTask  -TaskName "WidgetManagerWatcher"

# 중지
Stop-ScheduledTask   -TaskName "WidgetManagerWatcher"

# 직접 실행 (디버그용, 콘솔 출력 보임)
powershell -ExecutionPolicy Bypass -File "D:\Projects\Widget_Manager\scripts\watch_and_run.ps1"
```
