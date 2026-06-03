STATUS: WAITING_USER

## 작업 지시

9단계로 넘어가기 전에, 먼저 버그를 고쳐라:

[버그] 다크모드에서 월 캘린더의 "오늘" 칸(하루 한 칸)이 
테마 색 변환 없이 흰색으로 남는다. 6단계 보고에서 "월 캘린더 셀은 
custom-paint라 테마 미적용"이라고 했던 그 부분으로 추정된다. 
다크모드에서 모든 칸(오늘 칸 포함)이 다크 테마 색을 따르도록 고쳐라.

이 버그 수정 후, 9단계(트레이 상주 + 로깅)로 진행해도 좋다.
단 버그 수정을 먼저 완료하고, 고쳐진 걸 확인한 뒤 9단계로 가라.
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

---

## ❓ 질문

**코어 v0.1이 완성되었습니다. 다음 중 어떻게 진행할까요?**

1. **플러그인 시스템** (core/plugin_loader.py + plugin_api.py) — 애드온 인프라 준비
2. **배포/패키징** (PyInstaller spec 작성, 빌드 자동화)
3. **QA / 버그 수정** — 실제 사용 중 발견된 문제 수정
4. **기타 요청 기능** — 원하는 기능 말씀해 주세요

## 💬 답변

(여기에 답변을 작성하세요)

---

## ✅ 완료 노트

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
