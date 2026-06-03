# Widget_Manager — 대화형 원격 작업 시스템 구축 지시 (워처)

## 목적
집/회사 어디서든 **GitHub만으로** Widget_Manager 개발을 지시하고, Claude Code가 **중요한 결정이 필요할 때 멈춰서 질문**하면 사용자가 모바일로 답하는 "왕복 대화형" 원격 작업 시스템을 만든다.

기존에 검증된 워처가 있다: `D:\UnrealProjects\TechAnim_Lab\scripts\watch_and_run.ps1` (+ setup_scheduler.ps1).
**그 코드를 먼저 읽고**, 폴링·git pull·Claude 자동실행·push·STATUS 갱신·단일 해시 비교(과거 버그 수정 포함) 로직을 재사용한다. 단, 아래의 "대화형 왕복"을 추가하는 게 핵심 차이다.

작업 폴더: `D:\Projects\Widget_Manager` (GitHub: ohCHA-TechAnim/Widget_Manager).
작업자: 차승현. 한국어. PyInstaller 무관하지만 ps1 안정성 중요.

---

## 핵심: STATUS 신호등 (기존 워처와 다른 점)

GitHub 저장소에 `TASK.md` 한 파일을 둔다. 맨 위 `STATUS:` 줄이 "지금 누구 차례인지" 신호등이다.

| STATUS | 뜻 | 다음 동작 |
|--------|-----|----------|
| `IDLE` | 할 일 없음 | 워처 대기 |
| `PENDING` | 사용자가 지시함 (Claude 차례) | 워처가 Claude Code 실행 |
| `WAITING_USER` | Claude가 질문함 (사용자 차례) | 워처 대기, 사용자가 답할 때까지 |
| `DONE` | 작업 완료 | 워처 대기 |

### 흐름
1. 사용자가 `TASK.md`에 지시 작성 + `STATUS: PENDING` → 커밋(모바일 가능).
2. 워처가 폴링으로 PENDING 감지 → `git pull` → Claude Code 실행.
3. Claude Code가 작업. **중요한 결정이 필요하면**:
   - `TASK.md`에 `## ❓ 질문 [번호]` 섹션으로 "무엇을 정해야 하는지 + 선택지(A/B/...)+ 각 장단점"을 적고,
   - `STATUS: WAITING_USER`로 바꾸고,
   - commit & push 후 **작업 중단**(그 라운드 종료).
4. 사용자가 push된 질문을 읽고, 그 아래 `## 💬 답변 [번호]`에 답을 적고 `STATUS: PENDING` → 커밋.
5. 워처가 다시 PENDING 감지 → Claude Code 실행 → 답을 읽고 이어서 진행.
6. 작업이 완전히 끝나면 Claude가 `STATUS: DONE` + 요약 적고 push.

> 워처는 PENDING일 때만 Claude를 실행한다. WAITING_USER/IDLE/DONE이면 아무것도 안 하고 다음 폴링까지 대기 (사용자 차례를 침범하지 않게).

---

## "중요한 결정"의 기준 (균형 모드)

Claude Code 실행 시 system/지시에 아래를 명시해, **중요한 것만 묻고 사소한 건 알아서** 진행하게 한다.

**멈춰서 질문해야 하는 것 (중요):**
- 데이터 구조 변경/추가 (일감 필드 등)
- 기능 추가·삭제·범위 변경
- 파일/폴더 구조의 큰 결정
- 외부 의존성(새 라이브러리) 추가
- 기존 동작을 바꾸는 리팩터링
- 사용자 설계 의도와 충돌하거나 모호한 지점

**알아서 진행해도 되는 것 (사소):**
- 변수/함수 이름, 주석, 코드 포맷팅
- 명백한 버그 수정
- 지시에 이미 명시된 내용의 구현 세부
- 테스트 코드 작성

애매하면 **질문하는 쪽**으로 (방향 틀어진 채 멀리 가는 것보다 안전).

---

## 만들 것

1. `scripts/watch_and_run.ps1` — 기존 TechAnim_Lab 워처 기반 + STATUS 신호등 로직.
   - 60초 폴링, `git fetch`+로컬/원격 해시 비교로 변경 감지(기존 단일 해시 비교 버그수정 반영).
   - 변경 감지 시 `git pull`. `TASK.md`의 STATUS 파싱.
   - `PENDING`이면 Claude Code를 작업 지시(아래 프롬프트)와 함께 실행. 그 외 STATUS면 skip.
   - Claude 실행은 비대화 모드로 TASK.md 내용을 입력. (TechAnim_Lab이 쓰던 `--dangerously-skip-permissions` 방식 참고하되, "중요 결정 시 WAITING_USER로 멈추라"는 지시를 매 실행 프롬프트에 포함.)
   - 실행 후 결과 commit & push. 로그는 `scripts/task_runner.log` (print 아닌 파일 기록).
2. `scripts/setup_scheduler.ps1` — 로그인 시 워처 자동 시작 등록. 태스크명 `WidgetManagerWatcher` (기존 ClaudeTaskRunner_TechAnimLab, DailyTechAnimReport와 **충돌 금지, 다른 이름**).
3. `TASK.md` — 템플릿. 맨 위 `STATUS: IDLE`. 사용법 주석(모바일에서 STATUS 바꾸고 지시 쓰는 법). 질문/답변 섹션 양식 포함.
4. `README.md`에 원격 작업법 간단 안내 + 모바일 편집 링크(`https://github.com/ohCHA-TechAnim/Widget_Manager/edit/main/TASK.md`).

## 매 Claude 실행에 주입할 지시(워처가 Claude에 넘기는 프롬프트에 포함)
- "너는 Widget_Manager를 개발한다. `TASK.md`의 지시를 수행하라."
- "**중요한 결정**(데이터구조/기능범위/파일구조/의존성/기존동작변경)이 필요하면, 추측하지 말고 `TASK.md`에 `## ❓ 질문 N` 으로 선택지와 장단점을 적고 `STATUS: WAITING_USER`로 바꾼 뒤 commit&push하고 그 라운드를 종료하라."
- "사소한 것(이름/주석/포맷/명백한 버그/지시에 이미 있는 세부)은 묻지 말고 진행하라."
- "작업이 완전히 끝나면 `STATUS: DONE`과 한국어 요약을 TASK.md에 적어라."
- "한국어 주석. 단계가 길면 중간 진행상황도 TASK.md에 남겨라."

---

## 검증 (만든 뒤)
1. `TASK.md`에 간단한 테스트 지시(예: "TEST.txt에 'hello' 쓰기") + `STATUS: PENDING` 커밋 → 워처가 감지·실행·push까지 자동으로 되는지 (TechAnim_Lab 때 33초 걸렸던 그 흐름).
2. **대화형 검증**: "파일 이름을 a로 할지 b로 할지 물어봐" 같은 지시 → Claude가 `WAITING_USER`로 질문 남기고 멈추는지 → 답 달고 PENDING → 이어서 진행되는지.
3. 재부팅 후 워처 자동 시작되는지(setup_scheduler 등록 확인).
4. 기존 두 자동화(TechAnim_Lab 워처, DailyTechAnimReport 새벽 리포트)와 **간섭 없는지** 확인.

## 주의
- 태스크명·로그파일·폴더가 기존 자동화들과 절대 겹치지 않게.
- 워처가 무한 루프로 자기 커밋을 또 감지하지 않도록(자기 push 후 로컬 해시 갱신).
- ps1은 print 대신 로그파일. 관리자 권한 필요 시 안내.
- 완성되면 사용법을 한국어 5~10줄로 요약.

## 끝나고 — 이 시스템으로 할 다음 일
이 원격 시스템이 검증되면, 그 위에서 `Widget_Manager_구현지시_1차.md`(위젯 코어 v0.1)를 TASK.md에 올려 원격으로 개발 시작한다.
