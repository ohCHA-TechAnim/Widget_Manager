STATUS: WAITING_USER

---

**다크모드 버그 수정 + 9단계 완료 보고 — 코어 v0.1 완성. 다음 단계는?**

완료된 내용:
- **다크모드 버그 수정**: `views/month_view.py` `CalendarCell.paintEvent()` — QPalette.Window 밝기(`lightness() < 128`)로 다크/라이트 판별, 셀 배경·날짜색·테두리·+N 오버플로 색상 다크 모드 대응
  - 셀 배경: 다크 시 #2D2D2D(일반) / #252525(다른달) / #1A3A5A(오늘)
  - 날짜색: 다크 시 #CCCCCC(일반) / #666666(다른달) / #7FBFFF(오늘)
  - 테두리: 다크 시 #555555(일반) / #4A90D9(오늘, 동일)
- **9단계**: 트레이 상주 + 로깅 (`main.py` 수정)
  - `QSystemTrayIcon` — 16×16 파란 원 프로그래매틱 아이콘 (별도 파일 불필요)
  - `closeEvent` 오버라이드: ✕ 버튼 → 트레이 숨김 (종료 아님) + 풍선 알림
  - 트레이 컨텍스트 메뉴: **열기** / **보고서 생성** / **설정** / **종료**
    - 설정: 창 표시 (설정 컨트롤은 툴바 우측에 있음)
    - 종료: `QApplication.quit()` 완전 종료
  - 트레이 아이콘 더블클릭 → 창 토글 (표시/숨김)
  - `app.setQuitOnLastWindowClosed(False)` — 창 숨겨도 이벤트 루프 유지
  - PyInstaller `--windowed` 대비: `sys.stdout is None` 체크 후 StreamHandler 조건부 등록
  - 구문 검사 통과 (py 3.11)

**질문**: 코어 v0.1이 완성되었습니다. 다음 중 어떻게 진행할까요?
1. **플러그인 시스템** (core/plugin_loader.py + plugin_api.py) — 애드온 인프라 준비
2. **배포/패키징** (PyInstaller spec 작성, 빌드 자동화)
3. **QA / 버그 수정** — 실제 사용 중 발견된 문제 수정
4. **기타 요청 기능** — 원하는 기능 말씀해 주세요

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

**6단계 완료 보고 — 7단계(꾸미기: 배경/칸별 이미지)로 진행할까요?**

완료된 내용:
- **6단계**: 테마 시스템 — 라이트/다크 + 커스텀 포인트색
  - `core/settings.py` — Settings 클래스 (`%APPDATA%\Widget_Manager\settings.json` 저장/로드)
    - `theme` ("light"|"dark"), `accent_color` (#RRGGBB) 지속 저장
  - `theme/light.qss` / `theme/dark.qss` — QSS 두 벌
    - `{ACCENT}`, `{ACCENT_HOVER}`, `{ACCENT_DARK}`, `{ACCENT_TEXT}` 자리표시자
    - 버튼·입력필드·탭·리스트·테이블·스크롤바·툴바 스타일 완성
  - `theme/theme_manager.py`
    - `ThemeManager` — 런타임 QSS 교체 + 포인트색 주입 (밝기 보정 자동)
    - `AccentPickerDialog` — 프리셋 8색 + QColorDialog 직접 지정
  - `main.py` — 툴바 우측에 **다크/라이트 토글** 버튼 + **포인트색** 버튼 추가
  - `views/task_dialog.py` — 삭제 버튼을 danger-outline 스타일로 변경
- 구문 검사 통과 (py 3.11). 월 캘린더 셀·칸반 컬럼 배경은 custom-paint/inline-style이므로 테마 미적용(다음 단계에서 조정 가능).

**질문**: 7단계(꾸미기 — 캘린더 전체 배경 이미지/GIF + 칸별 deco_image)로 진행할까요?

💬 답변
진행하는데, 다크모드에서 하루(한칸)은 색변환 없이 흰색으로 나와. 다크모드 제대로 적용해야해

---

**7단계 완료 보고 — 8단계(순수 유틸 이식)로 진행할까요?**

완료된 내용:
- **7단계**: 꾸미기 — 배경 이미지/GIF + 칸별 deco_image
  - `core/settings.py` — `bg_image`, `bg_opacity`, `deco_images` 필드 추가; `get/set/clear_deco_image()` 헬퍼
  - `views/month_view.py`
    - `BgSettingsDialog` — 파일 선택(이미지/GIF) + 밝기 슬라이더(10~100%) + 제거 버튼
    - `CalendarCell` — deco_image 썸네일(하단 40% 반투명 표시), 우클릭 컨텍스트 메뉴(설정/제거), 배경 활성 시 `WA_TranslucentBackground`로 반투명 셀 전환
    - `MonthView.paintEvent()` — `QPixmap`(정적) / `QMovie`(GIF 애니) 배경 렌더링, 밝기 opacity 적용
    - nav bar에 **배경** 버튼 추가 → `BgSettingsDialog` 오픈
  - `main.py` — `MonthView`에 `settings` 인스턴스 전달
- 구문 검사 통과 (py 3.11), 앱 정상 실행 확인

**질문**: 8단계(순수 유틸 이식 — `math_utils.py`, `coordinate_converter.py`, `report_generator.py` + 탭/메뉴 연결)로 진행할까요?

✅ 완료 노트

- **1단계 (2026-06-03)**: 폴더 골격 생성, PyQt6 6.11.0 설치, `main.py` 빈 창(920×640), `requirements.txt`, `.gitignore`, 로깅(`%APPDATA%\Widget_Manager\logs\`)
- **2단계 (2026-06-03)**: `core/task_store.py` — 일감 데이터 구조, JSON 영속화(`%APPDATA%\Widget_Manager\data\tasks.json`), CRUD, 날짜 범위 쿼리, 옵저버 패턴, 유효성 검사. 단독 테스트 7개 통과.
- **3단계 (2026-06-03)**: `views/month_view.py` — 6×7 격자 월 캘린더, 일감 막대, +N 오버플로, 오늘 강조, 이전/다음 네비게이션, 더블클릭/클릭 시그널. `main.py` 연결.
- **4단계 (2026-06-04)**: `views/task_dialog.py` — 기본 정보 탭(제목/기간/상태/우선순위/색상/메모) + 링크&첨부 탭(지라/폴더/파일). 수정 모드 삭제 버튼. `main.py` QInputDialog 제거.
- **5단계 (2026-06-04)**: `views/list_view.py` + `views/kanban_view.py` + 뷰 토글 툴바. 드래그&드롭 상태 변경. QStackedWidget 전환.
- **6단계 (2026-06-04)**: `core/settings.py` + `theme/light.qss` + `theme/dark.qss` + `theme/theme_manager.py`. 라이트/다크 토글, 포인트색 프리셋+직접 선택. 설정 settings.json 지속 저장.
- **7단계 (2026-06-04)**: `core/settings.py` bg/deco 확장 + `views/month_view.py` 배경 이미지/GIF + 칸별 deco_image 썸네일 + 우클릭 메뉴. BgSettingsDialog 추가.
- **8단계 (2026-06-04)**: `utils/math_utils.py` + `utils/coordinate_converter.py` + `utils/report_generator.py` 이식. `tests/test_math_utils.py` 20개 통과. `views/converter_view.py` + `views/report_dialog.py` 추가. `main.py` 좌표변환 탭 + 보고서 생성 메뉴 연결. python-docx 설치.
- **다크모드 버그 수정 (2026-06-04)**: `views/month_view.py` — CalendarCell 셀 배경·날짜색·테두리 QPalette 기반 다크/라이트 대응. QPalette 임포트 추가.
- **9단계 (2026-06-04)**: `main.py` — QSystemTrayIcon, closeEvent 오버라이드(✕=숨김), 트레이 메뉴(열기/보고서생성/설정/종료), 트레이 더블클릭 토글, setQuitOnLastWindowClosed(False), PyInstaller --windowed 대비 로깅 처리.
