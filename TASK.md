STATUS: WAITING_USER

작업 지시
Widget_Manager 코어 v0.1 개발을 시작한다. 같은 폴더의 Widget_Manager_구현지시_1차.md가 전체 설계 문서다. 그 문서를 읽고 따르되, 원격 작업이므로 아래 진행 규칙을 지켜라.
이번 라운드 범위 (1라운드)
지시문의 작업 순서 중 1~2단계만 한다:

폴더 골격 + requirements.txt + main.py 빈 창 띄우기 (PyQt6 설치 확인)
core/task_store.py + 일감 데이터 구조 + JSON 저장/로드 (Qt 없이 단독 테스트)

그 이상(월 뷰, 테마 등)은 이번 라운드에 하지 마라.
1라운드 끝나면

1~2단계가 실제로 도는지 확인(빈 창 뜨고, task_store 테스트 통과)한 뒤
## ❓ 질문 섹션에 "1~2단계 완료, 이러이러하게 됐다. 3단계(월 뷰)로 진행할까? 아니면 조정할 것 있나?"를 적고
STATUS: WAITING_USER 로 바꾸고 commit & push 후 멈춰라.

진행 규칙 (원격)

중요한 결정(데이터구조 변경/기능 추가삭제/파일구조/새 라이브러리/기존동작 변경/설계 모호점)이 생기면: 추측하지 말고 ## ❓ 질문 N에 선택지+장단점 적고 STATUS: WAITING_USER로 바꿔 push 후 멈춰라.
사소한 것(변수명/주석/포맷/명백한 버그/지시문에 이미 있는 세부)은 묻지 말고 진행하라.
한 라운드에 너무 많이 하지 마라. 단계별로 끊어서, 매 단계 후 WAITING_USER로 보고하고 다음 지시를 기다려라.
한국어 주석. PyInstaller 대비 print 대신 logging 사용.
각 단계 끝에 git commit (단계명 포함).

참고 자산 (같은 폴더)

Widget_Manager_구현지시_1차.md — 전체 설계 (데이터 구조, 기능 명세, 폴더 구조, 작업 순서)
TaskHub_완전판_v2_소스포함.md — 기존 TaskHub 소스 (나중 단계에서 math_utils/coordinate_converter/report_generator 이식용. 이번 1라운드엔 불필요)


❓ 질문

**5단계 완료 보고 — 6단계(테마: 라이트/다크 + 커스텀 색)로 진행할까요?**

완료된 내용:
- **5단계**: 리스트 뷰 + 칸반 뷰 + 뷰 토글
  - `views/list_view.py` — QTableWidget 기반 목록 뷰
    - 색 띠(8px) + 제목/시작일/마감일/상태/우선순위 컬럼
    - 마감일 기준 자동 정렬, 완료 일감 흐리게 표시
    - 더블클릭 → TaskDialog
  - `views/kanban_view.py` — 3컬럼 칸반 뷰
    - 드래그&드롭으로 할 일/진행 중/완료 이동 → task_store status 자동 갱신
    - 카드 배경색 밝기 기반 글씨색 자동 결정 (흰/검)
    - 더블클릭 → TaskDialog
  - `main.py` — 툴바(새 일감 | 월 뷰 | 목록 | 칸반) + QStackedWidget 전환

PyQt6 UI라 헤드리스에서 스크린샷 불가하지만, 구문 검사 통과 (py 3.11).

**질문**: 6단계(테마 시스템 — 라이트/다크 QSS 교체 + 커스텀 포인트색)로 진행할까요?

💬 답변
(사용자가 채웁니다)

✅ 완료 노트

- **1단계 (2026-06-03)**: 폴더 골격 생성, PyQt6 6.11.0 설치, `main.py` 빈 창(920×640), `requirements.txt`, `.gitignore`, 로깅(`%APPDATA%\Widget_Manager\logs\`)
- **2단계 (2026-06-03)**: `core/task_store.py` — 일감 데이터 구조, JSON 영속화(`%APPDATA%\Widget_Manager\data\tasks.json`), CRUD, 날짜 범위 쿼리, 옵저버 패턴, 유효성 검사. 단독 테스트 7개 통과.
- **3단계 (2026-06-03)**: `views/month_view.py` — 6×7 격자 월 캘린더, 일감 막대, +N 오버플로, 오늘 강조, 이전/다음 네비게이션, 더블클릭/클릭 시그널. `main.py` 연결.
- **4단계 (2026-06-04)**: `views/task_dialog.py` — 기본 정보 탭(제목/기간/상태/우선순위/색상/메모) + 링크&첨부 탭(지라/폴더/파일). 수정 모드 삭제 버튼. `main.py` QInputDialog 제거.
- **5단계 (2026-06-04)**: `views/list_view.py` + `views/kanban_view.py` + 뷰 토글 툴바. 드래그&드롭 상태 변경. QStackedWidget 전환.
