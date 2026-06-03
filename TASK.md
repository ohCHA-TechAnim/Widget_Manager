STATUS: PENDING

## ✅ 2단계 완료 보고 — 배포/패키징 (PyInstaller exe 빌드)

완료된 내용:
- `utils/resource_path.py` — `resource_path(rel)` 헬퍼. PyInstaller 환경(`sys._MEIPASS`)과 개발 환경 모두 올바른 경로 반환. 패키지 환경에서 `sys._MEIPASS`를 `sys.path`에 삽입해 `plugins.*` 임포트 동작.
- `theme/theme_manager.py` — `_THEME_DIR` → `resource_path("theme")` 변경
- `core/plugin_loader.py` — `_PLUGINS_DIR` → `resource_path("plugins")` 변경
- `main.py` — 최상단에 `import utils.resource_path` (조기 초기화 side-effect)
- `make_icon.py` — PyQt6로 16/32/48/256px 원형 아이콘 렌더링 → ICO 포맷 생성 (`assets/app_icon.ico`)
- `widget_manager.spec` — PyInstaller 6.x 스펙. `theme/*.qss`, `plugins/` 데이터 포함. `--windowed` (콘솔 없음), ICO 아이콘 적용.
- `build.ps1` — 1) PyInstaller 확인/설치, 2) 아이콘 생성, 3) 빌드 자동화. `-Clean` 스위치 지원.
- `requirements-dev.txt` — 빌드 전용 의존성 (`pyinstaller>=6.0`)
- `.gitignore` — `build/`, `dist/`, `assets/app_icon.ico` 추가

빌드 결과 (실측):
- `dist\WidgetManager\WidgetManager.exe` — 3.8 MB
- `dist\WidgetManager\_internal\` — 총 99.6 MB (235 파일)
- exe 실행 확인: 프로세스 정상 기동, 로그 오류 없음, 트레이 아이콘·설정·일감 모두 정상

빌드 방법:
```powershell
.\build.ps1          # 증분 빌드
.\build.ps1 -Clean   # 클린 빌드
```

---

**다음 단계: 3단계 — 자동 업데이트 + 시작프로그램 등록**
진행해도 될까요?

## ✅ 3단계 완료 보고 — 자동 업데이트 + 시작프로그램 등록

완료된 내용:
- `utils/startup.py` — `is_registered()` / `register()` / `unregister()`. HKCU `Software\Microsoft\Windows\CurrentVersion\Run` 레지스트리 키 사용. 패키지 환경이면 exe 경로, 개발 환경이면 `pythonw.exe main.py` 등록. `winreg` (stdlib, Windows 전용).
- `core/updater.py` — `APP_VERSION = "0.1.0"`, `check_for_update()` (urllib, GitHub Releases API), `UpdateChecker(QThread)` — `update_available(dict)` 시그널 방출.
- `views/settings_dialog.py` — `SettingsDialog`: 시작프로그램 체크박스(토글 즉시 반영), 업데이트 확인 버튼(동기 체크 → 새 버전 있으면 릴리즈 페이지 브라우저 오픈).
- `main.py` 수정:
  - `SettingsDialog`, `UpdateChecker` 임포트 추가
  - 트레이 "설정" → `SettingsDialog` 열기 (기존: 창 표시만 했음)
  - `MainWindow.__init__` 완료 후 `UpdateChecker` 스레드 시작 → 업데이트 있으면 트레이 풍선 알림
  - `_on_update_available()` 핸들러 추가
- 새 의존성 없음 (`urllib`, `winreg` 모두 stdlib)
- 구문 검사 통과 (py 3.11)

사용법:
- **시작프로그램**: 트레이 → 설정 → "Windows 시작 시 자동 실행" 체크박스
- **업데이트**: 시작 시 백그라운드 체크 (있으면 트레이 알림) + 설정 → "업데이트 확인" 버튼

---

**다음 단계: 코어 v0.1 완성 이후 계획은?**

1. **QA / 버그 수정** — 실제 사용 중 발견된 문제
2. **빌드 재패키징** — spec에 새 파일 반영 후 exe 재빌드
3. **기타 기능 추가**

진행해도 될까요?

---

## 작업 지시

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

진행해

---

## ✅ 완료 노트

- **플러그인 시스템 (2026-06-04)**:
  - `core/plugin_api.py` — `PluginBase` 추상 기반 클래스 (메타데이터 속성, 수명주기 훅 `on_load`/`on_unload`, 일감 훅 `on_store_changed`, UI 확장 `get_menu_actions`)
  - `core/plugin_loader.py` — `AppContext`(store·settings·main_window 노출), `PluginLoader`(발견·로드·언로드·훅 발신·에러 격리)
  - `views/plugin_dialog.py` — 활성화/비활성화 UI, 설정 `enabled_plugins` 자동 저장
  - `plugins/hello_plugin/__init__.py` — 데모 플러그인 (정보 메시지 액션 포함)
  - `main.py` — 플러그인 메뉴 추가, 앱 시작 시 활성화 목록 자동 로드



- **3단계 (2026-06-04)**: `utils/startup.py` (레지스트리 시작프로그램 등록/해제) + `core/updater.py` (GitHub Releases API + UpdateChecker QThread) + `views/settings_dialog.py` (시작프로그램 토글 + 업데이트 확인 UI) + `main.py` (백그라운드 업데이트 체크, 트레이 알림, 설정 다이얼로그 연결).
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
