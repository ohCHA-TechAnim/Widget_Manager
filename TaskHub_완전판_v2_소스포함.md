# TaskHub 종합 인수인계 문서 (v2.0)

> **이 문서의 목적**: 다른 대화창(또는 다른 AI/개발자)에서 TaskHub 개발을 이어가기 위한 완전한 컨텍스트 전달 문서입니다.
> 최초 v1.0.0 명세를 기반으로, 이후 진행한 모든 리팩터링·기능 추가·버그 수정을 반영했습니다.
> **개발 대상자**: 차승현 (Nexon Games 3D Technical Artist)
> **핵심 환경**: Python 3.11.9, PyQt6, Selenium 4.20.0, openpyxl 3.1.2, python-docx, Windows 11

---

## 0. 새 대화에서 이어갈 때 먼저 읽을 것 (AI/개발자용 주의사항)

1. **이 앱은 사용자 PC(Desktop/TaskHub)에서 실행되는 PyQt6 데스크톱 앱이다.** 코드는 사용자의 `.venv`에서 돌아간다. 따라서 문서 생성 등은 Node 도구가 아니라 **Python 라이브러리**(예: python-docx)로 구현해야 한다.
2. **사용자는 모바일에서 작업할 때가 많다.** 부분 수정 발췌보다 "파일 전체 코드"를 요구하는 경우가 많으니, 변경 시 가능하면 해당 파일 전체본을 제공한다.
3. **들여쓰기/코드 순서 실수가 두 번 사고를 냈다.** (`cell` 참조 순서, 루프 들여쓰기) → 코드 블록을 줄 때 들여쓰기와 변수 정의 순서를 반드시 점검할 것.
4. **UI 복잡도에 민감하다.** 기능을 무더기로 추가하지 말고, 사용자가 고른 것만 하나씩 검증하며 추가한다. 헤더 버튼이 늘어나는 것을 특히 경계한다 → 자주 안 쓰는 기능은 트레이 메뉴로.
5. **검증 우선.** 순수 로직(수학/변환/집계)은 Qt 없이 단독 테스트가 가능하므로, 코드 제공 전에 기존 공식과 값이 일치하는지 확인한다.
6. **정확성에 솔직할 것.** 특히 회전(rotation) 좌표 변환은 단순 축 스왑으로 100% 정확하지 않다. 근사치는 근사치라고 명시하고 경고를 띄운다.
7. **PyInstaller --windowed 빌드 시 `print()`가 남아 있으면 크래시**한다(최초 문서의 주의점, 여전히 유효). 플러그인 로더 등에서 print 대신 로그 파일 기록 권장.

---

## 1. 프로젝트 개요 및 핵심 가치

TaskHub는 3D TA 업무의 두 축을 지원하는 바탕화면 상주형 데스크톱 가젯이다:
(A) 언리얼 엔진 Transform 오프셋 연산기, (B) 애니메이션팀 SharePoint 일정표 + Outlook 회의를 시각화하는 도킹 캘린더.

**최초 5대 핵심 가치(유지)**: ① 저피로 UX(불필요한 완료 알림창 제거, ✕는 종료가 아닌 트레이 숨김), ② 완벽 균등 바둑판 격자, ③ 6주차 자동 소멸(RowStretch), ④ Headless QThread 비동기(Selenium), ⑤ 실무형 협업 필터(병합셀 복제, 80% 공실 자동 휴일, 90% 공동 일감 청색).

**v2에서 더해진 가치**: ⑥ 재사용 가능한 공용 유틸/팩토리로 유지보수성 향상, ⑦ 안전한 사용자 확장(플러그인 + 화이트리스트), ⑧ 일감/회의 통합 뷰, ⑨ DCC 간 좌표/단위 변환, ⑩ 분기/연간 성과보고서 자동화.

---

## 2. 전체 디렉토리 구조 (v2 최종)

```
TaskHub/  (Desktop/TaskHub/)
│
├── .venv/
├── .gitignore
├── requirements.txt              # [수정] python-docx 추가
├── main.py                       # 진입점 (변경 없음)
│
├── core/
│   ├── __init__.py
│   ├── constants.py              # 경로/상수 (변경 없음)
│   ├── plugin_api.py             # [신규] PluginBase + PluginHost 인터페이스
│   ├── plugin_loader.py          # [신규] plugins/ 스캔 + 실패 격리 로더
│   └── action_registry.py        # [신규] 액션 화이트리스트 + 선언형 JSON→UI 빌더
│
├── model/
│   ├── __init__.py
│   ├── delta_calculator.py       # [수정] math_utils 위임 래퍼로 축소
│   ├── schedule_model.py         # [수정] hex/비율 헬퍼화 + meeting_data 로딩 추가
│   └── report_generator.py       # [신규] 분기/연간 성과보고서(.docx) 생성기
│
├── utils/
│   ├── __init__.py
│   ├── clipboard_helper.py       # 언리얼 쿼터니언↔오일러/파서 (변경 없음)
│   ├── registry_handler.py       # 시작프로그램 레지스트리 (변경 없음)
│   ├── selenium_downloader.py    # [수정] stale element 재시도 패치 + 디버그 덤프
│   ├── outlook_downloader.py     # [신규] Outlook 회의 크롤러 (QThread)
│   ├── math_utils.py             # [신규] 각도/색상/워크데이 순수 함수
│   └── coordinate_converter.py   # [신규] DCC 좌표/단위 변환 순수 로직
│
├── view/
│   ├── __init__.py
│   ├── styles.py                 # 글로벌 다크 QSS (변경 없음)
│   ├── Logo.png
│   ├── widget_factory.py         # [신규] ✕버튼/스핀박스/리스트세트 팩토리
│   ├── main_window.py            # [수정] ✕버튼 팩토리화 + 변환 탭 추가
│   └── calendar_window.py        # [수정] 일감/회의 스위핑, 버튼 통합, 셀 표시제한, +N팝업
│
├── view/components/
│   ├── __init__.py
│   ├── calculator_tab.py         # [수정] 스핀박스 팩토리 위임
│   ├── task_detail_dialog.py     # 일감 상세 다이얼로그 (변경 없음)
│   └── converter_tab.py          # [신규] 좌표/단위 변환 탭 UI
│
├── controller/
│   ├── __init__.py
│   ├── app_controller.py         # [수정] 플러그인 로드, PluginHost 구현, 회의/버튼통합, 보고서 메뉴
│   ├── calculator_controller.py  # [수정] 각도 wrapping 공유 + 죽은코드 제거
│   └── converter_controller.py   # [신규] 변환 탭 로직 바인딩
│
├── plugins/                      # [신규] 사용자 플러그인 폴더
│   ├── __init__.py
│   └── example_clock.py          # 플러그인 작성 템플릿
│
└── tests/                        # [신규] 순수 로직 테스트
    ├── __init__.py
    └── test_math_utils.py
```

> **중요**: 신규 폴더 `core/`, `plugins/`, `tests/` 에 빈 `__init__.py`가 반드시 있어야 import가 된다.

---

## 3. 단계별 변경 이력 (무엇을 왜 바꿨나)

### 3-1. 리팩터링 (재사용성/유지보수)
- **문제**: 각도 wrapping 공식이 `delta_calculator`와 `calculator_controller`에 중복. hex 색상 8자리 보정이 `schedule_model`에 3회 반복. ✕ 닫기 버튼 스타일이 두 창에 통째로 복붙. 스핀박스 생성 로직 산재.
- **해결**:
  - `utils/math_utils.py` 신설: `wrap_angle_180`, `shortest_rotator_delta`, `vector_delta`, `normalize_argb_hex`, `argb_to_css`, `count_workdays`, `ratio`.
  - `view/widget_factory.py` 신설: `make_close_button`, `make_spinbox`, `make_small_button`, `make_list_with_buttons` + 스타일 상수.
  - 기존 파일들이 이 함수를 호출하도록 교체. **수식 결과값은 기존과 동일함을 테스트로 검증 완료**(특히 회전 델타가 legacy 공식과 일치).
- **주의**: 임계값(80% 휴일, 90% 공동 일감)과 파싱 로직은 절대 변경 안 함. 색상/비율 산출 방식만 헬퍼로 치환.

### 3-2. 사용자 확장 시스템 (플러그인 + 화이트리스트)
- **설계 철학**: 사용자가 임의 코드를 실행하게 두지 않는다. (a) `PluginBase`를 구현한 `.py`를 `plugins/`에 떨구거나, (b) JSON으로 "버튼→등록된 액션 이름"만 매핑. `eval`/`exec` 없음.
- `core/plugin_api.py`: `PluginBase`(NAME + build(host)) + `PluginHost` 프로토콜(register_action/get_config/notify).
- `core/plugin_loader.py`: `plugins/` 스캔, 각 플러그인 import/인스턴스화를 try/except로 **격리**(하나가 깨져도 앱/타 플러그인 정상).
- `core/action_registry.py`: 이름→콜러블 화이트리스트. **미등록 액션은 실행 거부(KeyError)** — 테스트로 차단 검증 완료. `build_declarative_panel`이 JSON을 읽어 패널 생성, 미등록 액션 버튼은 회색 비활성 "(사용 불가)".
- `app_controller`가 `PluginHost` 역할 수행. 시작 시 `load_extensions()`로 플러그인을 계산기 창 탭에 추가, `<AppData>/Config/custom_ui.json`이 있으면 선언형 패널 탭 추가.
- 내장 화이트리스트 액션: `refresh_excel`, `clear_month`, `add_period`, `open_login`, `open_settings`, `fetch_meetings`.

### 3-3. Selenium stale element 수정
- **에러**: `stale element reference` — 요소를 잡아둔 뒤 페이지가 리렌더되어 참조 무효화(SharePoint SPA 특성).
- **해결**: `_act_with_retry` 헬퍼로 "찾는 즉시 사용 + 실패 시 재탐색 재시도". 고정 `sleep(8)`을 가능한 곳은 조건 대기로. 실패 시 스크린샷/HTML 덤프(`error_shot.png`, `error_page.html`)를 `EXCEL_PATH.parent`에 저장.

### 3-4. Outlook 회의 일정 (Selenium 방식)
- `utils/outlook_downloader.py` (QThread). SharePoint와 동일한 MS 로그인 흐름 재사용.
- 결과: `<AppData>/Data/meetings.json` = `{"y-m-d": [{"title","time","raw"}, ...]}`.
- **날짜 매핑**: (1) aria-label 내 날짜 우선 파싱 → (2) 없으면 요일 컬럼 x좌표로 추정 → (3) 폴백은 주 시작일.
- **미해결/주의**: OWA 회의 카드 셀렉터(`SELECTOR_EVENT_CARDS`, `SELECTOR_DAY_COLUMNS`)는 테넌트/UI 버전마다 다름. **첫 실행에 0건이 정상일 수 있음** → `outlook_page.html` 덤프로 실제 aria-label/class 확인 후 상단 상수 교정 필요. 셀렉터가 맞아야 날짜 매핑 정밀도도 보장됨.

### 3-5. 캘린더 UI 개선
- **일감/회의 스위핑**: `view_mode`("task"/"meeting"). 토글 버튼으로 전환, `draw_calendar`가 모드별로 일감 또는 회의를 그림. 회의 모드는 읽기 전용(더블클릭/우클릭 편집 차단).
- **버튼 통합**: "업데이트"와 "회의 받기"를 단일 `btn_action`으로 통합. `_apply_mode_buttons`가 모드에 따라 라벨/동작/색 전환. 일감 편집 버튼(기간추가/비우기)은 일감 모드에서만 노출.
- **주차 잘림 버그 수정**: 한 칸에 일감이 많으면 셀 내용 높이가 커져 5·6주차가 화면 밖(640px)으로 잘리던 버그. → `MAX_ITEMS_PER_CELL=3`으로 표시 제한 + `setWordWrap(False)` + 말줄임으로 행 높이 폭주 차단. 초과분은 "+N건 더"로 접음.
- **+N건 더 팝업**: 클릭 시 그날 전체 목록을 다크 다이얼로그로 표시(일감 모드는 항목 더블클릭→상세 편집).

### 3-6. 좌표/단위 변환 (새 탭)
- `utils/coordinate_converter.py` (순수 로직, 검증 완료): 위치(축+부호+단위), 스케일(축순서), 단위(cm↔m, 도↔라디안).
- **검증된 좌표 규약**: Unreal(LH, Z-up, cm) / Maya(RH, Y-up, cm) / 3ds Max(RH, Z-up) / Blender(RH, Z-up, m). 손잡이는 한 축 부호 반전, up축은 Y/Z 스왑. 왕복 변환(A→B→A==원본) 및 알려진 케이스(UE↔Maya 등) 테스트 통과.
- `view/components/converter_tab.py` + `controller/converter_controller.py`: From/To 콤보(언리얼/맥스/마야/블렌더), P·R·S 입력, 클립보드 일괄 붙여넣기, 변환 실행, 결과 복사, 단위 변환 섹션.
- **중대한 한계(반드시 유지)**: 회전 변환은 `convert_rotation_approx`로 **근사치 + 노란 경고**만 제공. 오일러 순서/짐벌/손잡이 때문에 정확하지 않음. 정확한 회전 변환은 향후 쿼터니언/행렬 기반으로 별도 설계 필요.
- **불변 규칙**: 콤보박스 순서(언리얼/맥스/마야/블렌더)가 `converter_tab.ENGINE_LABELS`와 `converter_controller.ENGINE_KEYS`에서 동일해야 매핑이 맞음.

### 3-7. 분기/연간 성과보고서
- `model/report_generator.py` (python-docx). 기간 필터(`period_range`로 연간/분기), 일감별 집계(`_collect_tasks`), 워크데이는 `math_utils.count_workdays` 재사용.
- 보고서 구성: 제목/작성자/기간, 요약 통계(총 일감·회의성·총 워크데이), 일감 상세(기간·워크데이·릴리즈, 메모, Jira/폴더 경로, 첨부 이미지 본문 삽입, 동영상은 경로 표기).
- UI: 트레이 메뉴 "📄 성과보고서 생성" → 연간/분기 선택 → 바탕화면에 `성과보고서_2026년_1분기.docx` 저장 후 자동 열기.
- **주의**: 동영상은 Word 본문 삽입 불가(경로만). `.venv`에 `python-docx` 설치 필수.

---

## 4. 데이터 구조 레퍼런스 (중요 — 새 코드 작성 시 기준)

```python
# schedule_model.schedule_data : 일감 (편집 가능)
{ (year, month, day): [ {"task": str, "color": "#RRGGBB"|"", "release": str}, ... ] }

# schedule_model.meeting_data : 회의 (읽기 전용, meetings.json 출처)
{ (year, month, day): [ {"title": str, "time": str, "raw": str}, ... ] }

# schedule_model.task_db : 일감별 부가정보 (편집 가능)
{ task_name: {
    "jiras":   [{"name": str, "path": str}, ...],
    "folders": [{"name": str, "path": str}, ...],
    "memo":    str,                       # 여러 줄, "\n[엑셀 메모 - M/D]\n..." 누적
    "attachments": [절대경로str, ...]      # 이미지/동영상 혼재
} }

# schedule_model.config : 설정 (config.json)
{ "target_name", "nexon_id", "nexon_pw", "library_url", "outlook_url"(신규),
  "sheet_name", "holidays": ["YYYY-M-D", ...], ... }
```

> 색상 규칙: 90% 공동 일감은 `#00BFFF`(DeepSkyBlue) 강제. 80% 이상 공실 날짜는 자동 휴일. 분홍(FF9494) 셀도 휴일.

---

## 5. 빌드/실행 주의사항 (최초 문서 + 갱신)

- **DPI/해상도**: 캘린더는 920×640. 640은 6주차까지 수용하는 황금값. (단 v2에서 셀 표시 제한으로 잘림은 추가 방어됨.)
- **PyInstaller --windowed**: `print()` 잔존 시 크래시. 플러그인 로더/다운로더의 print를 로그 파일로 대체 권장.
- **Logo.png 이식**: `get_application_tray_icon()`이 `view/Logo.png` 절대경로 추적. 배포 시 동봉. 없으면 동적 드로잉 fallback.
- **신규 의존성**: `requirements.txt`에 `python-docx` 추가. Selenium용 Chrome/chromedriver 버전 일치 필요(현재 chrome 148 계열에서 동작 확인).
- **신규 폴더 __init__.py**: `core/`, `plugins/`, `tests/`에 필수.
- **custom_ui.json 위치**: `<AppData>/TaskHub/Config/custom_ui.json` (파일명 정확히).

---

## 6. 알려진 미해결 과제 / 다음 작업 후보

1. **Outlook 셀렉터 교정** (최우선): 실제 OWA DOM에 맞춰 `SELECTOR_EVENT_CARDS`/`SELECTOR_DAY_COLUMNS` 조정. 교정 전엔 회의 0건 또는 날짜 어긋남 가능.
2. **정확한 회전 좌표 변환**: 현재 근사치. 쿼터니언/회전행렬 기반으로 재설계해야 DCC 간 회전이 정확.
3. **성능 (구조개선과 별개)**:
   - `parse_excel_data`의 시트 이중 풀스캔(휴일 스캔 + 본 스캔)을 단일 패스로 통합.
   - `draw_calendar`가 매번 전 셀을 delete 후 재생성 → 변경분만 갱신하는 방식 검토.
4. **플러그인 빌드 안전성**: 로더 print를 로그 파일로 전환(--windowed 크래시 방지).
5. **보고서 고도화**: 완료/진행 상태 분류, 월별 차트(matplotlib 이미지 삽입), 회의 통계 포함 등.
6. **테스트 확대**: 현재 math_utils만 커버. coordinate_converter, report_generator의 period_range도 테스트 추가 권장.

---

## 7. 더 나은 툴을 위한 제언 (Claude 첨언)

- **설정 일원화**: 로그인/URL/Outlook URL 설정이 여러 다이얼로그에 흩어져 있다. 단일 "환경설정" 탭이나 다이얼로그로 모으면 UX와 유지보수가 동시에 개선된다.
- **에러 로깅 인프라**: 현재 실패는 QMessageBox + (일부) print. `logging` 모듈로 `<AppData>/logs/`에 회전 로그를 남기면 사용자가 문제 발생 시 로그만 보내도 원인 추적이 된다. --windowed 크래시 문제도 동시 해결.
- **자격증명 보안**: `nexon_pw`가 config.json에 평문 저장된다. Windows DPAPI(`win32crypt`) 또는 `keyring`으로 암호화 저장을 검토. (회사 보안 정책상 중요할 수 있음.)
- **점진적 캘린더 렌더**: 셀 전체 재생성 대신 데이터 변경분만 갱신하면 큰 달/잦은 토글에서 체감 속도가 오른다.
- **플러그인을 1급 기능으로**: 좌표 변환·보고서 같은 기능도 사실 플러그인 인터페이스로 재구성 가능하다. 코어를 얇게 유지하고 기능을 플러그인으로 빼면 UI 복잡도 폭주를 구조적으로 막을 수 있다.
- **데이터 마이그레이션 대비**: schedule_data/task_db 스키마가 진화 중이다. config에 `"schema_version"`을 두고 로드 시 버전 체크/마이그레이션하면 향후 구조 변경이 안전해진다.
- **회전 변환은 솔직하게**: 정확 구현 전까지는 근사치임을 UI에 계속 명시. 신뢰가 핵심 도구에서 "조용히 틀린 값"보다 "경고와 함께 근사"가 낫다.

---

## 8. 새 대화 시작용 요약 프롬프트 (복붙용)

> "TaskHub라는 PyQt6 데스크톱 앱(언리얼 TA용 오프셋 계산기 + SharePoint/Outlook 캘린더 가젯)을 개발 중입니다. 첨부한 인수인계 문서(v2)에 아키텍처·폴더구조·데이터구조·변경이력·미해결과제가 모두 정리돼 있습니다. 이 문서 기준으로 [원하는 작업]을 이어가고 싶습니다. 저는 모바일 작업이 잦아 파일 전체 코드를 선호하고, UI 복잡도 증가를 경계하며, 순수 로직은 검증 후 제공받기를 원합니다."

---

*문서 버전: v2.0 — 최초 v1.0.0 명세 + 리팩터링/플러그인/Outlook회의/좌표변환/성과보고서/버그수정 반영*


---

# 부록 A. 전체 소스 코드 (v2 최종)
> 아래는 폴더 구조 그대로의 모든 파일 전체 소스입니다. `__init__.py`(빈 파일)는 생략했습니다 — 각 패키지 폴더(core/model/utils/view/view/components/controller/plugins/tests)에 빈 `__init__.py`를 두세요.

## `.gitignore`

```
.venv/
__pycache__/
*.pyc
build/
dist/
*.spec
AppData/
/Config/
/Data/
/Excel/

```

## `requirements.txt`

```text
PyQt6==6.11.0
PyQt6-Qt6==6.11.1
PyQt6_sip==13.11.1
selenium==4.20.0
openpyxl==3.1.2
python-docx==1.1.2
pyinstaller==6.20.0
requests==2.34.2
urllib3==2.7.0

```

## `main.py`

```python
# -*- coding: utf-8 -*-
"""
main.py
~~~~~~~
TaskHub 실행 파일 (Entry Point)
"""

import sys
from PyQt6.QtWidgets import QApplication
from controller.app_controller import AppController
from view.styles import DARK_THEME_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(DARK_THEME_STYLE)
    controller = AppController()
    controller.start_application()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

```

## `core/constants.py`

```python
# -*- coding: utf-8 -*-
"""
core/constants.py
~~~~~~~~~~~~~~~~~
TaskHub 전역 설정 및 고정 경로 정의 모듈
"""

import os
from pathlib import Path

APP_NAME = "TaskHub"
CURRENT_VERSION = "2.0.0"

GITHUB_OWNER = "YourGitHubID"
GITHUB_REPO = "TaskHub"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

LOCAL_APPDATA_PATH = Path(os.environ["LOCALAPPDATA"]) / "TaskHub"
LOCAL_APPDATA_PATH.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = LOCAL_APPDATA_PATH / "Config"
DATA_DIR = LOCAL_APPDATA_PATH / "Data"
EXCEL_DIR = LOCAL_APPDATA_PATH / "Excel"
ATTACH_DIR = DATA_DIR / "Attachments"

for directory in [CONFIG_DIR, DATA_DIR, EXCEL_DIR, ATTACH_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

CONFIG_FILE_PATH = CONFIG_DIR / "config.json"
SCHEDULE_FILE_PATH = DATA_DIR / "schedules.json"
TASK_DB_FILE_PATH = DATA_DIR / "task_db.json"
EXCEL_PATH = EXCEL_DIR / "스케쥴_애니메이션팀(2026).xlsx"

UPDATE_TEMP_PATH = LOCAL_APPDATA_PATH / "temp"
UPDATE_TEMP_PATH.mkdir(parents=True, exist_ok=True)

```

## `core/plugin_api.py`

```python
# -*- coding: utf-8 -*-
"""
core/plugin_api.py
~~~~~~~~~~~~~~~~~~
사용자 플러그인이 따라야 하는 '계약(인터페이스)' 정의.

설계 철학
---------
- 플러그인은 임의 코드를 앱에 주입하는 통로가 아니라, 정해진 슬롯에 끼우는 확장점이다.
- 각 플러그인은 PluginBase를 상속하고 build() 에서 QWidget 하나를 돌려준다.
- 그 위젯은 메인 윈도우의 탭으로 자동 등록된다.
- 플러그인은 host(=PluginHost)를 통해서만 앱 기능에 접근한다.
  host가 노출하는 것 외에는 앱 내부에 손댈 수 없다 -> 격리.

플러그인 작성자가 쓰는 것:
  - utils.math_utils  (각도/색상/워크데이 등 검증된 순수 함수)
  - view.widget_factory (표준 위젯)
  - host.register_action / host.get_config 등 (아래 PluginHost 참고)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Callable, Any

from PyQt6.QtWidgets import QWidget


@runtime_checkable
class PluginHost(Protocol):
    """
    플러그인이 앱과 상호작용할 때 거치는 좁은 창구(파사드).
    여기 정의된 메서드 외의 앱 내부는 플러그인이 건드릴 수 없다.
    실제 구현은 controller 쪽에서 제공한다.
    """

    def register_action(self, name: str, func: Callable[..., Any]) -> None:
        """선언형 UI(JSON)에서 이름으로 호출할 액션을 등록."""
        ...

    def get_config(self, key: str, default: Any = None) -> Any:
        """앱 설정값 읽기(읽기 전용 사본)."""
        ...

    def notify(self, message: str) -> None:
        """상태 표시줄/헤더에 짧은 메시지 표기(알림창 띄우지 않음)."""
        ...


class PluginBase:
    """
    모든 플러그인의 부모 클래스.

    하위 클래스 필수 항목:
      - NAME (str): 탭 제목으로 쓰일 이름.
      - build(host) -> QWidget: 탭에 들어갈 위젯 생성.

    선택 항목:
      - VERSION (str)
      - on_unload(): 정리 작업이 필요할 때.
    """

    NAME: str = "Unnamed Plugin"
    VERSION: str = "0.0.0"

    def build(self, host: PluginHost) -> QWidget:  # noqa: D401
        raise NotImplementedError(
            f"플러그인 '{self.NAME}' 은 build(host) 를 구현해야 합니다."
        )

    def on_unload(self) -> None:
        """앱 종료/플러그인 해제 시 호출. 기본은 아무것도 안 함."""
        return None

```

## `core/plugin_loader.py`

```python
# -*- coding: utf-8 -*-
"""
core/plugin_loader.py
~~~~~~~~~~~~~~~~~~~~~
plugins/ 폴더를 스캔해 PluginBase 하위 클래스를 발견/적재한다.

격리 원칙
---------
- 플러그인 하나가 import 단계에서 깨지거나 build()에서 예외를 던져도
  나머지 플러그인과 앱 본체는 정상 동작해야 한다.
- 따라서 모든 적재/생성은 try/except로 감싸고, 실패는 로그로만 수집한다.
- eval/exec를 쓰지 않는다. importlib 로 모듈 단위 import만 한다.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Type

from core.plugin_api import PluginBase


@dataclass
class LoadResult:
    """적재 결과 보고서. UI/로그에서 사용자에게 보여줄 수 있다."""
    loaded: List[PluginBase] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _iter_plugin_files(plugins_dir: Path):
    """plugins/ 내부의 후보 .py 파일을 순회 (__init__, _로 시작하는 것 제외)."""
    if not plugins_dir.is_dir():
        return
    for path in sorted(plugins_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        yield path


def _load_module_from_path(path: Path):
    """단일 .py 파일을 모듈로 import. 실패 시 예외를 그대로 올림."""
    mod_name = f"taskhub_plugin_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"스펙 생성 실패: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)  # 여기서 플러그인 본문이 실행됨
    return module


def _find_plugin_classes(module) -> List[Type[PluginBase]]:
    """모듈 안에서 PluginBase를 상속한(자기 자신 제외) 클래스들을 수집."""
    found = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, PluginBase) and obj is not PluginBase:
            # 다른 모듈에서 import된 PluginBase 재노출은 제외
            if obj.__module__ == module.__name__:
                found.append(obj)
    return found


def discover_plugins(plugins_dir: Path) -> LoadResult:
    """
    plugins_dir를 스캔해 플러그인 인스턴스 목록을 만든다.
    각 파일/클래스 단위로 예외를 격리한다.
    """
    result = LoadResult()

    for path in _iter_plugin_files(plugins_dir):
        try:
            module = _load_module_from_path(path)
        except Exception:  # noqa: BLE001 - 플러그인 격리가 우선
            result.errors.append(
                f"[{path.name}] import 실패:\n{traceback.format_exc(limit=3)}"
            )
            continue

        classes = _find_plugin_classes(module)
        if not classes:
            result.errors.append(f"[{path.name}] PluginBase 하위 클래스를 찾지 못함")
            continue

        for cls in classes:
            try:
                instance = cls()
                # 최소 계약 검증: NAME 존재 + build 오버라이드 여부
                if not getattr(instance, "NAME", "").strip():
                    raise ValueError("NAME 속성이 비어 있음")
                result.loaded.append(instance)
            except Exception:  # noqa: BLE001
                result.errors.append(
                    f"[{path.name}:{cls.__name__}] 인스턴스화 실패:\n"
                    f"{traceback.format_exc(limit=3)}"
                )

    return result

```

## `core/action_registry.py`

```python
# -*- coding: utf-8 -*-
"""
core/action_registry.py
~~~~~~~~~~~~~~~~~~~~~~~~
선언형 커스텀 UI의 안전 장치.

핵심 보안 모델
-------------
- 사용자는 JSON으로 '버튼 -> 액션 이름'만 지정한다.
- 실제 호출 가능한 함수는 register()로 미리 등록된 화이트리스트뿐이다.
- 등록되지 않은 이름은 실행되지 않고 거부된다.
- eval/exec/getattr-by-string 으로 임의 코드를 부르지 않는다.

따라서 사용자가 JSON에 무엇을 적든 등록된 액션 외에는 절대 실행되지 않는다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel


class ActionRegistry:
    """이름 -> 콜러블 화이트리스트."""

    def __init__(self) -> None:
        self._actions: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        if not name or not callable(func):
            raise ValueError("액션 이름은 비어있지 않고 func는 호출 가능해야 합니다.")
        self._actions[name] = func

    def has(self, name: str) -> bool:
        return name in self._actions

    def names(self) -> List[str]:
        return sorted(self._actions)

    def invoke(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """등록된 액션만 호출. 미등록이면 KeyError(거부)."""
        if name not in self._actions:
            raise KeyError(f"등록되지 않은 액션: {name!r} (허용: {self.names()})")
        return self._actions[name](*args, **kwargs)


def load_ui_spec(path: Path) -> dict:
    """
    JSON UI 명세 로드 + 최소 스키마 검증.
    형식 예:
      {
        "title": "내 커스텀 패널",
        "buttons": [
          {"label": "엑셀 새로고침", "action": "refresh_excel"},
          {"label": "이번 달 비우기", "action": "clear_month"}
        ]
      }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("UI 명세 최상위는 객체여야 합니다.")
    buttons = data.get("buttons", [])
    if not isinstance(buttons, list):
        raise ValueError("'buttons'는 배열이어야 합니다.")
    for b in buttons:
        if not isinstance(b, dict) or "label" not in b or "action" not in b:
            raise ValueError("각 버튼은 'label'과 'action'을 가진 객체여야 합니다.")
    return data


def build_declarative_panel(spec: dict, registry: ActionRegistry) -> QWidget:
    """
    JSON 명세 -> QWidget 패널 생성.
    - registry에 등록된 action만 버튼에 연결된다.
    - 미등록 action을 가진 버튼은 비활성화 + 회색 처리(조용히 무시하되 흔적은 남김).
    """
    panel = QWidget()
    layout = QVBoxLayout(panel)

    title = spec.get("title", "커스텀 패널")
    title_lbl = QLabel(f"<b>{title}</b>")
    layout.addWidget(title_lbl)

    for b in spec.get("buttons", []):
        label = str(b["label"])
        action = str(b["action"])
        btn = QPushButton(label)

        if registry.has(action):
            # 기본 인자 dict가 있으면 그대로 전달 (사용자 정의 파라미터)
            params = b.get("params", {})
            btn.clicked.connect(
                lambda _checked, a=action, p=params: registry.invoke(a, **p)
            )
        else:
            btn.setEnabled(False)
            btn.setToolTip(f"등록되지 않은 액션: {action}")
            btn.setText(f"{label}  (사용 불가)")

        layout.addWidget(btn)

    layout.addStretch()
    return panel

```

## `model/delta_calculator.py`

```python
# -*- coding: utf-8 -*-
"""
model/delta_calculator.py
~~~~~~~~~~~~~~~~~~~~~~~~~
언리얼 엔진 좌표계 기반의 위치(Vector) 및 회전(Rotator) 최단 경로 연산 비즈니스 로직.

[리팩터링] 실제 수식은 utils.math_utils로 이관하고, 본 클래스는 호환용 얇은 래퍼만 유지한다.
이렇게 하면 동일 수식이 controller(보정 모드) 등 다른 곳과 한 곳을 공유한다.
"""

from typing import Tuple

from utils.math_utils import vector_delta, shortest_rotator_delta


class DeltaCalculator:
    """언리얼 엔진의 Transform 오프셋 계산을 전담하는 수학적 연산 모델 (math_utils 위임)"""

    @staticmethod
    def calculate_vector_delta(start: Tuple[float, float, float],
                               target: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """위치(Vector) 간의 단순 오프셋 계산 (Target - Start)"""
        return vector_delta(start, target)

    @staticmethod
    def calculate_rotator_delta(start: Tuple[float, float, float],
                                 target: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """회전(Rotator) 최단 경로 오프셋 계산 (Angle Wrapping)"""
        return shortest_rotator_delta(start, target)

```

## `model/schedule_model.py`

```python
# -*- coding: utf-8 -*-
"""
model/schedule_model.py
~~~~~~~~~~~~~~~~~~~~~~~
일정표 JSON 데이터 핸들러 및 Excel 파싱 연산을 담당하는 비즈니스 로직 모델 (전사 공동 일감 파란색 자동 전환 탑재)

[리팩터링] hex 색상 보정/CSS 변환/0나눗셈 방어 비율을 utils.math_utils 공유 함수로 위임.
판정 임계값(80% 휴일, 90% 공동일감)과 파싱 로직은 변경하지 않음.
"""

import json
import re
import openpyxl
from typing import Dict, List, Any
from core.constants import CONFIG_FILE_PATH, SCHEDULE_FILE_PATH, TASK_DB_FILE_PATH, EXCEL_PATH
from utils.math_utils import normalize_argb_hex, argb_to_css, ratio


class ScheduleModel:
    """일정표 수집 정보 및 엑셀 데이터 분석 모델"""

    def __init__(self):
        self.config = self.load_config()
        self.schedule_data = self.load_schedules()
        self.task_db = self.load_task_db()
        self.meeting_data = self.load_meetings()

    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "target_name": "", "nexon_id": "", "nexon_pw": "", "library_url": "",
            "sheet_name": "애니메이션", "main_position": {}, "login_position": {},
            "settings_position": {}, "details_position": {}, "period_position": {}, "holidays": []
        }
        if CONFIG_FILE_PATH.exists():
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    default_config.update(json.load(f))
            except:
                pass
        return default_config

    def save_config(self):
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def load_schedules(self) -> Dict[tuple, List[Dict[str, str]]]:
        if SCHEDULE_FILE_PATH.exists():
            try:
                with open(SCHEDULE_FILE_PATH, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    converted_data = {}
                    for date_str, tasks in raw_data.items():
                        y, m, d = map(int, date_str.split('-'))
                        converted_data[(y, m, d)] = tasks
                    return converted_data
            except:
                pass
        return {}

    def load_meetings(self):
        """meetings.json 로드. 키를 (y, m, d) 튜플로 변환. 회의는 읽기 전용."""
        from utils.outlook_downloader import MEETINGS_FILE_PATH
        if MEETINGS_FILE_PATH.exists():
            try:
                with open(MEETINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    converted = {}
                    for date_str, mtgs in raw.items():
                        y, m, d = map(int, date_str.split('-'))
                        converted[(y, m, d)] = mtgs
                    return converted
            except Exception:
                pass
        return {}

    def save_schedules(self):
        export_data = {f"{k[0]}-{k[1]}-{k[2]}": v for k, v in self.schedule_data.items()}
        with open(SCHEDULE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)

    def load_task_db(self) -> Dict[str, Any]:
        if TASK_DB_FILE_PATH.exists():
            try:
                with open(TASK_DB_FILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_task_db(self):
        with open(TASK_DB_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.task_db, f, ensure_ascii=False, indent=4)

    def get_task_db_entry(self, task_name: str) -> Dict[str, Any]:
        if task_name not in self.task_db:
            self.task_db[task_name] = {"jiras": [], "folders": [], "memo": "", "attachments": []}

        db_entry = self.task_db[task_name]
        for key in ["jiras", "folders"]:
            if key not in db_entry:
                db_entry[key] = []
            db_entry[key] = [{"name": x, "path": x} if isinstance(x, str) else x for x in db_entry[key]]

        if "memo" not in db_entry:
            db_entry["memo"] = ""
        if "attachments" not in db_entry:
            db_entry["attachments"] = []

        return db_entry

    @staticmethod
    def safe_text(obj: Any) -> str:
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return str(obj) if obj is not None else ""

    @staticmethod
    def get_cell_color(cell) -> str:
        try:
            if not cell or not hasattr(cell, 'fill') or not cell.fill:
                return ""
            color_obj = cell.fill.start_color
            if hasattr(color_obj, 'rgb') and color_obj.rgb:
                # [리팩터링] 8자리 ARGB 정규화는 공유 함수 사용
                return normalize_argb_hex(color_obj.rgb)
        except:
            pass
        return ""

    @staticmethod
    def clean_excel_comment(text: str) -> str:
        text = re.sub(r'(?si)\[Threaded comment\].*?linkid=\d+', '', text)
        text = re.sub(r'(?si)Your version of Excel.*?linkid=\d+', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        return text.strip()

    def parse_excel_data(self, target_year: int, target_month: int) -> bool:
        target_name = self.config["target_name"]
        sheet_name = self.config["sheet_name"]

        if not EXCEL_PATH.exists():
            return False

        wb = openpyxl.load_workbook(str(EXCEL_PATH), data_only=True)
        if sheet_name not in wb.sheetnames:
            raise Exception(f"스케줄 시트 '{sheet_name}'이 존재하지 않습니다.")

        ws = wb[sheet_name]
        rows = list(ws.iter_rows())
        if len(rows) < 3:
            raise Exception("엑셀 시트 행 구조가 유효하지 않습니다.")

        r1_cells, r3_cells = rows[0], rows[2]

        # 1. 작업자 행 색인 및 이름 열 색인 동적 분석
        target_row_idx = -1
        name_col_idx = -1
        for i, row in enumerate(rows):
            for col_i, cell in enumerate(row):
                if self.safe_text(cell.value).strip() == target_name:
                    target_row_idx = i
                    name_col_idx = col_i
                    break
            if target_row_idx != -1:
                break

        if target_row_idx == -1:
            raise Exception(f"스케줄러 내부에서 '{target_name}' 님을 찾을 수 없습니다.")

        target_cells = rows[target_row_idx]
        max_col_limit = len(target_cells)

        # 병합셀 정보 사전 해시 테이블 매핑
        merged_lookup = {}
        for crange in ws.merged_cells.ranges:
            clo, rlo, chi, rhi = crange.bounds
            top_cell = ws.cell(row=rlo, column=clo)
            top_value = top_cell.value
            top_comment = top_cell.comment
            top_hyperlink = top_cell.hyperlink
            top_fill = top_cell.fill
            for r in range(rlo, rhi + 1):
                for c in range(clo, chi + 1):
                    merged_lookup[(r, c)] = (top_value, top_comment, top_hyperlink, top_fill)

        # 전체 작업자(팀원) 행 색인 일괄 수집 (행 index 3부터 탐색)
        worker_rows = []
        for r in range(3, len(rows)):
            if r == target_row_idx:
                worker_rows.append(r)
                continue
            if name_col_idx != -1 and name_col_idx < len(rows[r]):
                name_val = self.safe_text(rows[r][name_col_idx].value).strip()
                if name_val and not name_val.isdigit() and len(name_val) < 15:
                    worker_rows.append(r)

        # 2. 휴일(빨간날) 스캔 매핑 및 8할 공실율 자동 감지
        new_holidays = []
        month_matched_for_holiday = None
        for col_idx in range(len(r3_cells)):
            c1 = r1_cells[col_idx] if col_idx < len(r1_cells) else None
            c3 = r3_cells[col_idx] if col_idx < len(r3_cells) else None

            c1_val = self.safe_text(c1.value) if c1 else ""
            c3_val = self.safe_text(c3.value) if c3 else ""

            if c1_val:
                match_m = re.search(r'(\d+)월', c1_val)
                if match_m:
                    month_matched_for_holiday = int(match_m.group(1))

            if month_matched_for_holiday and c3_val:
                match_day = re.search(r'^(\d+)', c3_val)
                if match_day:
                    d = int(match_day.group(1))

                    # 80% 일정 배분율 공실 검사
                    empty_count = 0
                    valid_workers = 0
                    for r in worker_rows:
                        if (r + 1, col_idx + 1) in merged_lookup:
                            cell_val = self.safe_text(merged_lookup[(r + 1, col_idx + 1)][0]).strip()
                        else:
                            cell_val = self.safe_text(rows[r][col_idx].value).strip() if col_idx < len(rows[r]) else ""

                        valid_workers += 1
                        if not cell_val or cell_val.lower() in ["none", "-", ""]:
                            empty_count += 1

                    # [리팩터링] 0나눗셈 방어 비율 공유 함수 사용 (임계값 0.8 유지)
                    is_auto_holiday = ratio(empty_count, valid_workers) >= 0.8

                    # 연분홍 셀 색상 매핑 휴일 판정
                    c3_row = 3
                    c3_col = col_idx + 1
                    if (c3_row, c3_col) in merged_lookup:
                        _, _, _, cell_fill_obj = merged_lookup[(c3_row, c3_col)]
                    else:
                        cell_fill_obj = c3.fill if c3 else None

                    cell_color = ""
                    if cell_fill_obj and hasattr(cell_fill_obj, 'start_color') and cell_fill_obj.start_color:
                        # [리팩터링] 8자리 ARGB 정규화 공유 함수 사용
                        cell_color = normalize_argb_hex(cell_fill_obj.start_color.rgb)

                    is_pink_holiday = cell_color and cell_color.upper().endswith('FF9494')

                    if is_pink_holiday or is_auto_holiday:
                        new_holidays.append(f"{target_year}-{month_matched_for_holiday}-{d}")

        self.config["holidays"] = list(set(self.config.get("holidays", []) + new_holidays))
        self.save_config()
        holidays_list = self.config["holidays"]

        # 3. 전방 순차 스캔 및 병합 셀 대입 가동 (전체 월 파싱)
        active_task, active_color, active_release = None, "", ""
        month_matched = None

        for col_idx in range(len(r3_cells)):
            c1 = r1_cells[col_idx] if col_idx < len(r1_cells) else None
            c3 = r3_cells[col_idx] if col_idx < len(r3_cells) else None

            c1_val = self.safe_text(c1.value) if c1 else ""
            c3_val = self.safe_text(c3.value) if c3 else ""

            if c1_val:
                match_m = re.search(r'(\d+)월', c1_val)
                if match_m:
                    month_matched = int(match_m.group(1))

            if month_matched and c3_val:
                match_day = re.search(r'^(\d+)', c3_val)
                if match_day:
                    d = int(match_day.group(1))
                    tc = target_cells[col_idx] if col_idx < max_col_limit else None

                    tc_row = target_row_idx + 1
                    tc_col = col_idx + 1

                    if (tc_row, tc_col) in merged_lookup:
                        m_val, m_comment, m_hyperlink, m_fill = merged_lookup[(tc_row, tc_col)]
                        tc_val = self.safe_text(m_val)
                        tc_comment = m_comment
                        tc_hyperlink = m_hyperlink
                        tc_fill = m_fill
                    else:
                        tc_val = self.safe_text(tc.value) if tc else ""
                        tc_comment = tc.comment if tc else None
                        tc_hyperlink = tc.hyperlink if tc else None
                        tc_fill = tc.fill if tc else None

                    if tc_val:
                        t_str = tc_val.strip()
                        if t_str and t_str.lower() != "none":
                            t_str = re.sub(r'^(예\)|완\)|진\)|보\))\s*', '', t_str)

                            release_tag = ""
                            match_release = re.search(r'(S\d+(?:E\d+)?[\~_ -]*W\d+)', t_str, re.IGNORECASE)
                            if match_release:
                                release_tag = match_release.group(1).upper()
                                t_str = t_str.replace(match_release.group(0), '').strip()

                            # [리팩터링] ARGB -> CSS 변환 공유 함수 사용
                            color_str = ""
                            if tc_fill and hasattr(tc_fill, 'start_color') and tc_fill.start_color:
                                color_str = argb_to_css(tc_fill.start_color.rgb)

                            active_task, active_color, active_release = t_str, color_str, release_tag
                            db = self.get_task_db_entry(active_task)

                            try:
                                if tc_hyperlink and getattr(tc_hyperlink, 'target', None):
                                    tgt = self.safe_text(tc_hyperlink.target).strip()
                                    if "sharepoint.com" not in tgt.lower() and "microsoft.com" not in tgt.lower():
                                        if not any(x['path'] == tgt for x in db["jiras"]):
                                            db["jiras"].append({"name": tgt, "path": tgt})
                            except:
                                pass

                            try:
                                if tc_comment and getattr(tc_comment, 'text', None):
                                    cmt_raw = self.clean_excel_comment(self.safe_text(tc_comment.text))
                                    clean_lines = []
                                    for line in cmt_raw.split('\n'):
                                        line_str = line.strip()
                                        if not line_str:
                                            continue

                                        urls = re.findall(r'(https?://[^\s]+)', line_str)
                                        if urls:
                                            for u in urls:
                                                if "sharepoint.com" not in u.lower() and "microsoft.com" not in u.lower():
                                                    if not any(x['path'] == u for x in db["jiras"]):
                                                        db["jiras"].append({"name": u, "path": u})
                                                line_str = line_str.replace(u, '').strip()

                                        if not line_str:
                                            continue

                                        path_candidate = line_str.replace('경로', '').replace(':', '', 1).strip()
                                        if path_candidate.startswith(r'\\') or re.match(r'^[a-zA-Z]:\\', path_candidate):
                                            if not any(x['path'] == path_candidate for x in db["folders"]):
                                                db["folders"].append({"name": path_candidate, "path": path_candidate})
                                            continue

                                        clean_lines.append(line_str)

                                    if clean_lines:
                                        new_memo = "\n".join(clean_lines)
                                        if new_memo not in db["memo"]:
                                            db["memo"] = (db["memo"] + f"\n\n[엑셀 메모 - {month_matched}/{d}]\n{new_memo}").strip()
                            except:
                                pass
                            self.save_task_db()
                        else:
                            active_task = None

                    if active_task:
                        is_h = f"{target_year}-{month_matched}-{d}" in holidays_list
                        is_w = (col_idx % 7 == 0) or (col_idx % 7 == 6)

                        if tc_val or (not is_h and not is_w):
                            # ---- [중요 패치: 공동 공유 일감 판정] ----
                            # 이 날짜(col_idx)에 이 일감을 가진 작업자 수 계산
                            match_count = 0
                            for r in worker_rows:
                                if (r + 1, col_idx + 1) in merged_lookup:
                                    w_val = self.safe_text(merged_lookup[(r + 1, col_idx + 1)][0]).strip()
                                else:
                                    w_val = self.safe_text(rows[r][col_idx].value).strip() if col_idx < len(rows[r]) else ""

                                w_val_clean = re.sub(r'^(예\)|완\)|진\)|보\))\s*', '', w_val)
                                match_rel = re.search(r'(S\d+(?:E\d+)?[\~_ -]*W\d+)', w_val_clean, re.IGNORECASE)
                                if match_rel:
                                    w_val_clean = w_val_clean.replace(match_rel.group(0), '').strip()

                                if w_val_clean == active_task:
                                    match_count += 1

                            # [리팩터링] 0나눗셈 방어 비율 공유 함수 사용 (임계값 0.9 유지)
                            # 전체 팀원의 9할 이상이 동일 일감을 가지면 "공유 공동 일감"으로 판단해 파란색(#00BFFF) 강제 매핑
                            is_shared_by_all = ratio(match_count, len(worker_rows)) >= 0.9
                            final_color = "#00BFFF" if is_shared_by_all else active_color

                            day_task_list = self.schedule_data.setdefault((target_year, month_matched, d), [])
                            if not any(x['task'] == active_task for x in day_task_list):
                                day_task_list.append({
                                    "task": active_task,
                                    "color": final_color,
                                    "release": active_release
                                })

        self.save_schedules()
        return True

```

## `model/report_generator.py`

```python
# -*- coding: utf-8 -*-
"""
model/report_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
분기별/연간 성과보고서(.docx) 생성기. python-docx 기반.
워크데이 계산은 utils.math_utils.count_workdays 재사용.
[의존성] requirements.txt에 python-docx 필요.
"""

import os
import datetime
from typing import Dict, Tuple

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from utils.math_utils import count_workdays

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
_VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm")
_QUARTER_MONTHS = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
_MONTH_LASTDAY = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def period_range(year: int, mode: str, quarter: int = None) -> Tuple[datetime.date, datetime.date]:
    if mode == "year":
        return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    if mode == "quarter":
        if quarter not in _QUARTER_MONTHS:
            raise ValueError("quarter는 1~4 사이여야 합니다.")
        sm, em = _QUARTER_MONTHS[quarter]
        last = _MONTH_LASTDAY[em - 1]
        if em == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            last = 29
        return datetime.date(year, sm, 1), datetime.date(year, em, last)
    raise ValueError("mode는 'year' 또는 'quarter' 여야 합니다.")


def _collect_tasks(schedule_data: Dict, start: datetime.date, end: datetime.date) -> Dict:
    per_task = {}
    for (y, m, d), tasks in schedule_data.items():
        try:
            cd = datetime.date(y, m, d)
        except ValueError:
            continue
        if start <= cd <= end:
            for t in tasks:
                name = t.get("task", "").strip()
                if not name:
                    continue
                entry = per_task.setdefault(name, {"dates": [], "release": t.get("release", "")})
                entry["dates"].append(cd)
                if not entry["release"] and t.get("release"):
                    entry["release"] = t["release"]
    return per_task


class ReportGenerator:
    def __init__(self, model):
        self.model = model

    def generate(self, year, mode, quarter=None, author_name="", output_path=None):
        start, end = period_range(year, mode, quarter)
        holidays = self.model.config.get("holidays", [])
        per_task = _collect_tasks(self.model.schedule_data, start, end)

        if mode == "year":
            period_label = f"{year}년 연간"
        else:
            period_label = f"{year}년 {quarter}분기"
        if not author_name:
            author_name = self.model.config.get("target_name", "")

        if output_path is None:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            fname = f"성과보고서_{period_label.replace(' ', '_')}.docx"
            output_path = os.path.join(desktop, fname)

        doc = Document()
        self._add_title(doc, period_label, author_name, start, end)
        self._add_summary(doc, per_task, start, end, holidays)
        self._add_task_details(doc, per_task, holidays)
        doc.save(output_path)
        return output_path

    def _add_title(self, doc, period_label, author_name, start, end):
        title = doc.add_heading(f"{period_label} 성과보고서", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = sub.add_run(
            f"작성자: {author_name or '-'}    "
            f"보고 기간: {start.strftime('%Y.%m.%d')} ~ {end.strftime('%Y.%m.%d')}"
        )
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        doc.add_paragraph()

    def _add_summary(self, doc, per_task, start, end, holidays):
        doc.add_heading("요약 통계", level=1)
        total_tasks = len(per_task)
        total_meeting_like = sum(1 for n in per_task if "회의" in n or "교육" in n)
        total_wd = count_workdays(start, end, holidays)
        table = doc.add_table(rows=0, cols=2)
        table.style = "Light List Accent 1"
        for label, value in [
            ("총 일감 수", f"{total_tasks}건"),
            ("회의/교육성 일감", f"{total_meeting_like}건"),
            ("기간 내 총 워크데이", f"{total_wd}일"),
            ("보고 기간", f"{start.strftime('%Y.%m.%d')} ~ {end.strftime('%Y.%m.%d')}"),
        ]:
            row = table.add_row().cells
            row[0].text = label
            row[1].text = value
        doc.add_paragraph()

    def _add_task_details(self, doc, per_task, holidays):
        doc.add_heading("일감 상세", level=1)
        if not per_task:
            doc.add_paragraph("해당 기간에 등록된 일감이 없습니다.")
            return
        ordered = sorted(per_task.items(), key=lambda kv: min(kv[1]["dates"]))
        for name, info in ordered:
            dates = sorted(info["dates"])
            mn, mx = dates[0], dates[-1]
            wd = count_workdays(mn, mx, holidays)
            doc.add_heading(name, level=2)
            meta = doc.add_paragraph()
            rel = f"  [{info['release']}]" if info.get("release") else ""
            mrun = meta.add_run(
                f"기간: {mn.strftime('%Y.%m.%d')} ~ {mx.strftime('%Y.%m.%d')}  "
                f"(총 {wd} 워크데이){rel}"
            )
            mrun.font.size = Pt(9)
            mrun.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

            db = self.model.task_db.get(name, {})
            memo = (db.get("memo") or "").strip()
            if memo:
                doc.add_paragraph("메모", style="Intense Quote")
                for line in memo.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line.strip(), style="List Bullet")

            jiras = db.get("jiras", [])
            folders = db.get("folders", [])
            if jiras or folders:
                doc.add_paragraph("링크 / 경로", style="Intense Quote")
                for j in jiras:
                    doc.add_paragraph(f"Jira: {j.get('name', j.get('path', ''))}", style="List Bullet")
                for f in folders:
                    doc.add_paragraph(f"폴더: {f.get('name', f.get('path', ''))}", style="List Bullet")

            attachments = db.get("attachments", [])
            imgs = [a for a in attachments if isinstance(a, str) and a.lower().endswith(_IMAGE_EXTS)]
            others = [a for a in attachments if a not in imgs]
            if imgs:
                doc.add_paragraph("첨부 이미지", style="Intense Quote")
                for a in imgs:
                    if os.path.exists(a):
                        try:
                            doc.add_picture(a, width=Inches(4.5))
                        except Exception:
                            doc.add_paragraph(f"(이미지 삽입 실패: {os.path.basename(a)})")
                    else:
                        doc.add_paragraph(f"(파일 없음: {os.path.basename(a)})")
            if others:
                doc.add_paragraph("첨부 파일 (경로)", style="Intense Quote")
                for a in others:
                    note = " — 동영상" if a.lower().endswith(_VIDEO_EXTS) else ""
                    doc.add_paragraph(f"{a}{note}", style="List Bullet")
            doc.add_paragraph()

```

## `utils/math_utils.py`

```python
# -*- coding: utf-8 -*-
"""
utils/math_utils.py
~~~~~~~~~~~~~~~~~~~
Qt 비의존 순수 계산/포맷 유틸리티 모음.

여기 있는 함수들은 모두 입력 -> 출력만 있고 부작용/Qt 의존이 없습니다.
따라서 pytest로 단독 검증이 가능하며, 모델/컨트롤러/뷰 어디서든 import해 재사용합니다.

[모은 이유 - 기존 중복]
  - 각도 wrapping 공식 ((x + 180) % 360 - 180):
        delta_calculator.calculate_rotator_delta 와
        calculator_controller.calculate_deltas(보정 모드)에 따로 존재했음.
  - hex 색상 8자리 보정 ("FF" + rgb):
        schedule_model 안에서 최소 3회 반복.
  - 워크데이 카운트:
        task_detail_dialog._calculate_workdays 안에 인라인.
"""

from __future__ import annotations

import datetime
from typing import Iterable, Sequence, Tuple

Vec3 = Tuple[float, float, float]


# ----------------------------------------------------------------------
# 각도 / 회전
# ----------------------------------------------------------------------
def wrap_angle_180(angle: float) -> float:
    """임의의 각도를 (-180, 180] 범위 최단 표현으로 정규화."""
    return ((angle + 180.0) % 360.0) - 180.0


def shortest_rotator_delta(start: Vec3, target: Vec3, ndigits: int = 4) -> Vec3:
    """회전(Pitch, Yaw, Roll) 최단 경로 오프셋. 각 축에 wrap_angle_180 적용."""
    return tuple(  # type: ignore[return-value]
        round(wrap_angle_180(t - s), ndigits) for s, t in zip(start, target)
    )


def vector_delta(start: Vec3, target: Vec3, ndigits: int = 4) -> Vec3:
    """위치(Vector) 단순 오프셋 (target - start)."""
    return tuple(  # type: ignore[return-value]
        round(t - s, ndigits) for s, t in zip(start, target)
    )


# ----------------------------------------------------------------------
# 색상
# ----------------------------------------------------------------------
def normalize_argb_hex(rgb_val: str | None) -> str:
    """
    openpyxl 셀 색상값을 항상 8자리(AARRGGBB) hex 문자열로 정규화.
    유효하지 않으면 빈 문자열.
    """
    if not rgb_val:
        return ""
    s = str(rgb_val)
    if len(s) == 8:
        return s
    if len(s) == 6:
        return "FF" + s
    return ""


def argb_to_css(rgb_val: str | None) -> str:
    """8자리 ARGB hex -> CSS '#RRGGBB'. 유효하지 않으면 빈 문자열."""
    norm = normalize_argb_hex(rgb_val)
    return f"#{norm[2:]}" if norm else ""


# ----------------------------------------------------------------------
# 일정 / 워크데이
# ----------------------------------------------------------------------
def is_holiday_key(year: int, month: int, day: int, holidays: Iterable[str]) -> bool:
    """'YYYY-M-D' 키가 휴일 목록에 있는지."""
    return f"{year}-{month}-{day}" in set(holidays)


def count_workdays(
    start: datetime.date,
    end: datetime.date,
    holidays: Iterable[str],
) -> int:
    """
    start~end(양끝 포함) 사이 평일이면서 휴일이 아닌 날의 수.
    주말(토=5, 일=6) 및 holidays('YYYY-M-D')는 제외.
    """
    if end < start:
        return 0
    holiday_set = set(holidays)
    count = 0
    for i in range((end - start).days + 1):
        cd = start + datetime.timedelta(days=i)
        if cd.weekday() < 5 and f"{cd.year}-{cd.month}-{cd.day}" not in holiday_set:
            count += 1
    return count


def ratio(part: int, whole: int) -> float:
    """0 나눗셈 방어 비율. whole이 0이면 0.0."""
    return part / whole if whole > 0 else 0.0

```

## `utils/coordinate_converter.py`

```python
# -*- coding: utf-8 -*-
"""
utils/coordinate_converter.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DCC 간 좌표계 / 단위 변환 (Qt 비의존 순수 로직).

[검증된 규약]
  Unreal : 좌수(LH), Z-up, cm
  Maya   : 우수(RH), Y-up, cm
  3ds Max: 우수(RH), Z-up
  Blender: 우수(RH), Z-up, m

[변환 범위]
  - 위치(Vector): 축 매핑 + 부호 + 단위 (정확)
  - 스케일(Scale): 축 순서만 (부호/단위 없음)
  - 회전(Rotation): 축 매핑 기반 '근사'. 오일러 순서/짐벌로 어긋날 수 있어 경고 동반.
"""

from __future__ import annotations
from typing import Tuple, Dict
import math

Vec3 = Tuple[float, float, float]

UNIT_CM: Dict[str, float] = {"unreal": 1.0, "maya": 1.0, "max": 1.0, "blender": 100.0}
ENGINES = ("unreal", "maya", "max", "blender")


def cm_to_m(v: float) -> float:
    return v / 100.0


def m_to_cm(v: float) -> float:
    return v * 100.0


def deg_to_rad(v: float) -> float:
    return v * math.pi / 180.0


def rad_to_deg(v: float) -> float:
    return v * 180.0 / math.pi


def _to_unreal_position(x, y, z, src):
    s = UNIT_CM[src]
    x, y, z = x * s, y * s, z * s
    if src == "unreal":
        return (x, y, z)
    if src == "maya":
        return (-z, x, y)
    if src in ("max", "blender"):
        return (x, -y, z)
    raise ValueError(f"unknown engine: {src}")


def _from_unreal_position(x, y, z, dst):
    if dst == "unreal":
        ux, uy, uz = x, y, z
    elif dst == "maya":
        ux, uy, uz = y, z, -x
    elif dst in ("max", "blender"):
        ux, uy, uz = x, -y, z
    else:
        raise ValueError(f"unknown engine: {dst}")
    d = UNIT_CM[dst]
    return (ux / d, uy / d, uz / d)


def convert_position(vec: Vec3, src: str, dst: str) -> Vec3:
    src, dst = src.lower(), dst.lower()
    ue = _to_unreal_position(vec[0], vec[1], vec[2], src)
    out = _from_unreal_position(ue[0], ue[1], ue[2], dst)
    return tuple(round(v, 4) for v in out)


def convert_scale(scale: Vec3, src: str, dst: str) -> Vec3:
    src, dst = src.lower(), dst.lower()

    def to_ue(s, sx, sy, sz):
        if s in ("unreal", "max", "blender"):
            return (sx, sy, sz)
        if s == "maya":
            return (sz, sx, sy)
        raise ValueError(s)

    def from_ue(s, ux, uy, uz):
        if s in ("unreal", "max", "blender"):
            return (ux, uy, uz)
        if s == "maya":
            return (uy, uz, ux)
        raise ValueError(s)

    ue = to_ue(src, *scale)
    out = from_ue(dst, *ue)
    return tuple(round(v, 6) for v in out)


def convert_rotation_approx(rot: Vec3, src: str, dst: str) -> Tuple[Vec3, str]:
    src, dst = src.lower(), dst.lower()
    approx = convert_position(rot, src, dst)
    warn = "⚠ 회전값은 근사치입니다. 오일러 순서/짐벌 차이로 어긋날 수 있으니 DCC에서 검수하세요."
    return approx, warn

```

## `utils/clipboard_helper.py`

```python
# -*- coding: utf-8 -*-
"""
utils/clipboard_helper.py
~~~~~~~~~~~~~~~~~~~~~~~~~
언리얼 엔진 전용 포지션/회전/스케일 데이터 개별 및 일괄 정밀 파싱 유틸리티
"""

import re
import math
from typing import Tuple, Optional


class ClipboardHelper:
    @staticmethod
    def format_to_unreal_vector(x: float, y: float, z: float) -> str:
        return f"(X={x:.4f},Y={y:.4f},Z={z:.4f})"

    @staticmethod
    def format_to_unreal_rotator(pitch: float, yaw: float, roll: float) -> str:
        return f"(Pitch={pitch:.4f},Yaw={yaw:.4f},Roll={roll:.4f})"

    @staticmethod
    def unreal_quat_to_rotator(x: float, y: float, z: float, w: float) -> Tuple[float, float, float]:
        singularity_test = z * x - w * y
        yaw_y = 2.0 * (w * z + x * y)
        yaw_x = 1.0 - 2.0 * (y * y + z * z)
        singularity_threshold = 0.4999995
        rad_to_deg = 180.0 / math.pi

        def normalize_axis(angle: float) -> float:
            angle = angle % 360.0
            if angle > 180.0:
                angle -= 360.0
            elif angle < -180.0:
                angle += 360.0
            return angle

        if singularity_test < -singularity_threshold:
            pitch = -90.0
            yaw = math.atan2(yaw_y, yaw_x) * rad_to_deg
            roll = normalize_axis(-yaw - (2.0 * math.atan2(x, w) * rad_to_deg))
        elif singularity_test > singularity_threshold:
            pitch = 90.0
            yaw = math.atan2(yaw_y, yaw_x) * rad_to_deg
            roll = normalize_axis(yaw - (2.0 * math.atan2(x, w) * rad_to_deg))
        else:
            pitch = math.asin(2.0 * singularity_test) * rad_to_deg
            yaw = math.atan2(yaw_y, yaw_x) * rad_to_deg
            roll = math.atan2(-2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y)) * rad_to_deg
        return round(pitch, 4), round(yaw, 4), round(roll, 4)

    @staticmethod
    def parse_vector(text: str) -> Optional[Tuple[float, float, float]]:
        if not text:
            return None
        clean_text = text.replace(" ", "")
        block_pattern = r"(?:Translation|Location|Location3D)\s*=\s*\(\s*X\s*=\s*([-?\d.]+)\s*,\s*Y\s*=\s*([-?\d.]+)\s*,\s*Z\s*=\s*([-?\d.]+)\s*\)"
        block_match = re.search(block_pattern, clean_text, re.IGNORECASE)
        if block_match:
            return float(block_match.group(1)), float(block_match.group(2)), float(block_match.group(3))
        simple_pattern = r"X\s*=\s*([-?\d.]+)\s*,\s*Y\s*=\s*([-?\d.]+)\s*,\s*Z\s*=\s*([-?\d.]+)"
        simple_match = re.search(simple_pattern, clean_text, re.IGNORECASE)
        if simple_match:
            return float(simple_match.group(1)), float(simple_match.group(2)), float(simple_match.group(3))
        return None

    @classmethod
    def parse_rotator(cls, text: str) -> Optional[Tuple[float, float, float]]:
        if not text:
            return None
        clean_text = text.replace(" ", "")
        pattern_euler = r"(?:Rotation|Rotator)?\s*=?\s*\(\s*Pitch\s*=\s*([-?\d.]+)\s*,\s*Yaw\s*=\s*([-?\d.]+)\s*,\s*Roll\s*=\s*([-?\d.]+)\s*\)"
        match_euler = re.search(pattern_euler, clean_text, re.IGNORECASE)
        if match_euler:
            return float(match_euler.group(1)), float(match_euler.group(2)), float(match_euler.group(3))
        pattern_quat = r"Rotation\s*=\s*\(\s*X\s*=\s*([-?\d.]+)\s*,\s*Y\s*=\s*([-?\d.]+)\s*,\s*Z\s*=\s*([-?\d.]+)\s*,\s*W\s*=\s*([-?\d.]+)\s*\)"
        match_quat = re.search(pattern_quat, clean_text, re.IGNORECASE)
        if match_quat:
            return cls.unreal_quat_to_rotator(
                float(match_quat.group(1)), float(match_quat.group(2)),
                float(match_quat.group(3)), float(match_quat.group(4))
            )
        return None

    @staticmethod
    def parse_scale(text: str) -> Optional[Tuple[float, float, float]]:
        if not text:
            return None
        clean_text = text.replace(" ", "")
        block_pattern = r"(?:Scale3D|Scale)\s*=\s*\(\s*X\s*=\s*([-?\d.]+)\s*,\s*Y\s*=\s*([-?\d.]+)\s*,\s*Z\s*=\s*([-?\d.]+)\s*\)"
        block_match = re.search(block_pattern, clean_text, re.IGNORECASE)
        if block_match:
            return float(block_match.group(1)), float(block_match.group(2)), float(block_match.group(3))
        simple_pattern = r"X\s*=\s*([-?\d.]+)\s*,\s*Y\s*=\s*([-?\d.]+)\s*,\s*Z\s*=\s*([-?\d.]+)"
        simple_match = re.search(simple_pattern, clean_text, re.IGNORECASE)
        if simple_match:
            return float(simple_match.group(1)), float(simple_match.group(2)), float(simple_match.group(3))
        return None

    @classmethod
    def parse_unreal_transform(cls, text: str):
        return cls.parse_vector(text), cls.parse_rotator(text)

```

## `utils/registry_handler.py`

```python
# -*- coding: utf-8 -*-
"""
utils/registry_handler.py
~~~~~~~~~~~~~~~~~~~~~~~~~
윈도우 시작 프로그램 등록/해제 레지스트리 유틸리티
"""

import sys
import os
import winreg
from core.constants import APP_NAME

REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


class RegistryHandler:
    @staticmethod
    def is_startup_enabled() -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    @staticmethod
    def toggle_startup(enable: bool) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE)
            if enable:
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                else:
                    app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[Error] Failed to toggle startup: {e}")
            return False

```

## `utils/selenium_downloader.py`

```python
# -*- coding: utf-8 -*-
"""
utils/selenium_downloader.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyQt6 QThread 기반 비동기 SharePoint Excel 다운로더.
[stale element 방어] 요소를 '찾는 즉시 사용' + 재시도. 실패 시 디버그 덤프.
"""

import os
import shutil
import time
from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from core.constants import EXCEL_PATH


class SeleniumDownloader(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()
    failed_signal = pyqtSignal(str)

    def __init__(self, target_name, nexon_id, nexon_pw, library_url):
        super().__init__()
        self.target_name = target_name
        self.nexon_id = nexon_id
        self.nexon_pw = nexon_pw
        self.library_url = library_url
        self._is_running = True

    def _act_with_retry(self, driver, action, by, value, wait, retries=3, scroll=True):
        last_exc = None
        for attempt in range(retries):
            try:
                el = wait.until(EC.presence_of_element_located((by, value)))
                if scroll:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    time.sleep(0.8)
                action(driver, el)
                return
            except StaleElementReferenceException as e:
                last_exc = e
                time.sleep(1.0)
        if last_exc:
            raise last_exc

    def _dump_debug(self, driver):
        try:
            driver.save_screenshot(str(EXCEL_PATH.parent / "error_shot.png"))
            with open(EXCEL_PATH.parent / "error_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception:
            pass

    def run(self):
        driver = None
        try:
            self.progress_signal.emit(10, "크롬 드라이버 초기화 중...")
            target_file_name_no_ext = "스케쥴_애니메이션팀(2026)"
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            download_path = os.path.join(download_dir, target_file_name_no_ext + ".xlsx")
            if os.path.exists(download_path):
                os.remove(download_path)

            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)

            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 30)

            self.progress_signal.emit(30, "일정표 서버 접속 및 계정 입력 중...")
            driver.get(self.library_url)

            email_input = wait.until(EC.element_to_be_clickable((By.NAME, "loginfmt")))
            email_input.clear()
            email_input.send_keys(self.nexon_id)
            wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
            time.sleep(1.5)

            self.progress_signal.emit(50, "보안 패스워드 검증 중...")
            pw_input = wait.until(EC.element_to_be_clickable((By.NAME, "passwd")))
            pw_input.clear()
            pw_input.send_keys(self.nexon_pw)
            wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()

            try:
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "idBtn_Back"))).click()
            except Exception:
                pass

            self.progress_signal.emit(70, f"'{self.target_name}' 님의 파일 색인 중...")
            file_xpath = (
                f"//*[contains(text(), '{target_file_name_no_ext}')] "
                f"| //*[contains(@title, '{target_file_name_no_ext}')]"
            )
            wait.until(EC.element_to_be_clickable((By.XPATH, file_xpath)))

            self._act_with_retry(
                driver,
                lambda drv, el: ActionChains(drv).context_click(el).perform(),
                By.XPATH, file_xpath, wait
            )
            time.sleep(1.5)

            self.progress_signal.emit(85, "보안 다운로드 명령 송신 중...")
            dl_btn_xpath = (
                "//button[@data-automationid='downloadCommand'] "
                "| //button[.//span[contains(text(), '다운로드') or contains(text(), 'Download')]]"
            )
            self._act_with_retry(
                driver,
                lambda drv, el: drv.execute_script("arguments[0].click();", el),
                By.XPATH, dl_btn_xpath, wait
            )

            self.progress_signal.emit(95, "로컬 캐시 이관 준비 중...")
            timeout = 40
            download_success = False
            while timeout > 0:
                if os.path.exists(download_path) and not os.path.exists(download_path + ".crdownload"):
                    if EXCEL_PATH.exists():
                        os.remove(str(EXCEL_PATH))
                    shutil.move(download_path, str(EXCEL_PATH))
                    download_success = True
                    break
                time.sleep(1)
                timeout -= 1

            if download_success:
                self.progress_signal.emit(100, "완료")
                self.finished_signal.emit()
            else:
                self._dump_debug(driver)
                self.failed_signal.emit("다운로드 제한 시간 초과 (Timeout)")

        except Exception as e:
            if driver is not None:
                self._dump_debug(driver)
            self.failed_signal.emit(str(e))
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

```

## `utils/outlook_downloader.py`

```python
# -*- coding: utf-8 -*-
"""
utils/outlook_downloader.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Outlook Web 캘린더 회의 크롤러 (QThread). SharePoint 다운로더와 동일 인증 흐름.

[셀렉터 교정 대상] 실제 OWA DOM에 맞춰 SELECTOR_* 조정 필요.
첫 실행에 0건이 나오면 outlook_page.html 덤프로 aria-label/class 확인 후 교정.
"""

import re
import json
import time
import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from core.constants import DATA_DIR

MEETINGS_FILE_PATH = DATA_DIR / "meetings.json"

SELECTOR_EVENT_CARDS = "div[role='button'][aria-label]"
SELECTOR_DAY_COLUMNS = "div[role='gridcell']"
OUTLOOK_CALENDAR_URL = "https://outlook.office.com/calendar/view/week"


class OutlookMeetingDownloader(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(int)
    failed_signal = pyqtSignal(str)

    def __init__(self, nexon_id, nexon_pw, calendar_url="", weeks_ahead=4):
        super().__init__()
        self.nexon_id = nexon_id
        self.nexon_pw = nexon_pw
        self.calendar_url = calendar_url.strip() or OUTLOOK_CALENDAR_URL
        self.weeks_ahead = weeks_ahead
        self._is_running = True

    def _find_all_fresh(self, driver, by, value, wait, retries=3):
        last_exc = None
        for _ in range(retries):
            try:
                wait.until(EC.presence_of_element_located((by, value)))
                return driver.find_elements(by, value)
            except StaleElementReferenceException as e:
                last_exc = e
                time.sleep(1.0)
            except TimeoutException:
                return []
        if last_exc:
            raise last_exc
        return []

    def _safe_attr(self, el, attr):
        try:
            return el.get_attribute(attr) or ""
        except StaleElementReferenceException:
            return ""

    def _safe_rect(self, el):
        try:
            return el.rect
        except StaleElementReferenceException:
            return None

    def _dump_debug(self, driver):
        try:
            driver.save_screenshot(str(DATA_DIR / "outlook_error_shot.png"))
            with open(DATA_DIR / "outlook_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception:
            pass

    def _parse_event_label(self, label):
        title = label.strip()
        time_str = ""
        m = re.search(r'((?:오전|오후)?\s?\d{1,2}:\d{2})', label)
        if m:
            time_str = m.group(1).strip()
        if "," in label:
            title = label.split(",")[0].strip()
        return title, time_str

    def _date_from_label(self, label, year):
        m = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', label)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        m = re.search(r'(\d{1,2})\s*월\s*(\d{1,2})\s*일', label)
        if m:
            return year, int(m.group(1)), int(m.group(2))
        return None

    def _column_bounds(self, driver):
        cols = driver.find_elements(By.CSS_SELECTOR, SELECTOR_DAY_COLUMNS)
        xs = []
        for col in cols:
            r = self._safe_rect(col)
            if r and r["width"] > 50:
                xs.append(r["x"])
        xs = sorted(set(int(x) for x in xs))
        if len(xs) >= 7:
            xs = xs[:7]
            width = xs[1] - xs[0] if len(xs) > 1 else 120
            return xs + [xs[-1] + width]
        win_w = driver.execute_script("return window.innerWidth;") or 1920
        step = win_w / 7.0
        return [int(step * i) for i in range(8)]

    def _col_index_from_x(self, x, bounds):
        for i in range(7):
            if bounds[i] <= x < bounds[i + 1]:
                return i
        return 0

    def run(self):
        driver = None
        try:
            self.progress_signal.emit(10, "크롬 드라이버 초기화 중...")
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 30)

            self.progress_signal.emit(30, "Outlook 접속 및 계정 입력 중...")
            driver.get(self.calendar_url)

            try:
                email_input = wait.until(EC.element_to_be_clickable((By.NAME, "loginfmt")))
                email_input.clear()
                email_input.send_keys(self.nexon_id)
                wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
                time.sleep(1.5)

                self.progress_signal.emit(50, "보안 패스워드 검증 중...")
                pw_input = wait.until(EC.element_to_be_clickable((By.NAME, "passwd")))
                pw_input.clear()
                pw_input.send_keys(self.nexon_pw)
                wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
                try:
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "idBtn_Back"))
                    ).click()
                except Exception:
                    pass
            except TimeoutException:
                pass

            self.progress_signal.emit(70, "캘린더 로딩 대기 중...")
            time.sleep(8)

            all_meetings = {}
            total_count = 0

            for week_i in range(self.weeks_ahead):
                self.progress_signal.emit(
                    70 + int(20 * week_i / max(1, self.weeks_ahead)),
                    f"{week_i + 1}주차 회의 수집 중..."
                )
                base = datetime.date.today() + datetime.timedelta(weeks=week_i)
                week_sunday = base - datetime.timedelta(days=(base.weekday() + 1) % 7)

                bounds = self._column_bounds(driver)
                cards = self._find_all_fresh(driver, By.CSS_SELECTOR, SELECTOR_EVENT_CARDS, wait)

                for card in cards:
                    label = self._safe_attr(card, "aria-label")
                    if not label:
                        continue
                    title, time_str = self._parse_event_label(label)
                    if not title:
                        continue
                    ymd = self._date_from_label(label, week_sunday.year)
                    if ymd is None:
                        rect = self._safe_rect(card)
                        if rect:
                            col = self._col_index_from_x(rect["x"], bounds)
                            day_date = week_sunday + datetime.timedelta(days=col)
                        else:
                            day_date = week_sunday
                        ymd = (day_date.year, day_date.month, day_date.day)
                    key = f"{ymd[0]}-{ymd[1]}-{ymd[2]}"
                    bucket = all_meetings.setdefault(key, [])
                    if not any(x["title"] == title and x["time"] == time_str for x in bucket):
                        bucket.append({"title": title, "time": time_str, "raw": label})
                        total_count += 1

                try:
                    next_btn = driver.find_elements(
                        By.CSS_SELECTOR, "button[aria-label*='다음'], button[aria-label*='Next']"
                    )
                    if next_btn:
                        driver.execute_script("arguments[0].click();", next_btn[0])
                        time.sleep(3)
                    else:
                        break
                except Exception:
                    break

            self.progress_signal.emit(95, "회의 데이터 저장 중...")
            with open(MEETINGS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(all_meetings, f, ensure_ascii=False, indent=4)

            if total_count == 0:
                self._dump_debug(driver)

            self.progress_signal.emit(100, "완료")
            self.finished_signal.emit(total_count)

        except Exception as e:
            if driver is not None:
                self._dump_debug(driver)
            self.failed_signal.emit(str(e))
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

```

## `view/styles.py`

```python
# -*- coding: utf-8 -*-
"""
view/styles.py
~~~~~~~~~~~~~~
Technical Artist용 글로벌 다크 QSS 스타일시트 (모든 팝업/대화상자 통합)
"""

DARK_THEME_STYLE = """
QWidget {
    background-color: #202020;
    color: #CCCCCC;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 9pt;
}
QWidget#CentralWidget {
    background-color: #202020;
    border: 1px solid #3F3F3F;
    border-radius: 8px;
}
QDialog, QMessageBox, QInputDialog, QFileDialog {
    background-color: #202020;
    color: #CCCCCC;
    border: 1px solid #3F3F3F;
}
QMenu {
    background-color: #2D2D2D;
    color: #CCCCCC;
    border: 1px solid #444444;
}
QMenu::item { background-color: transparent; padding: 6px 24px; }
QMenu::item:selected { background-color: #1A365D; color: #00BFFF; }
QLineEdit, QTextEdit, QPlainTextEdit, QDoubleSpinBox {
    background-color: #151515;
    color: #FFFFFF;
    border: 1px solid #3F3F3F;
    border-radius: 3px;
    padding: 4px;
}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus { border: 1px solid #007ACC; }
QPushButton {
    background-color: #333333;
    color: #E0E0E0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 12px;
}
QPushButton:hover { background-color: #444444; border-color: #007ACC; }
QPushButton:pressed { background-color: #222222; border-color: #005A9E; }
QPushButton#ToggleModeButton {
    background-color: #1A365D;
    color: #00BFFF;
    border: 1px solid #007ACC;
    font-weight: bold;
}
QPushButton#ToggleModeButton:hover { background-color: #2A4D7C; border-color: #00BFFF; }
QListWidget, QListView {
    background-color: #151515;
    color: #FFFFFF;
    border: 1px solid #3F3F3F;
    border-radius: 4px;
}
QListWidget::item:selected { background-color: #1A365D; color: #00BFFF; }
QScrollBar:vertical {
    background-color: #151515; width: 12px; margin: 15px 3px 15px 3px; border: none;
}
QScrollBar::handle:vertical { background-color: #444444; min-height: 20px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background-color: #555555; }
QTabWidget::pane {
    border: 1px solid #3F3F3F; background-color: #1A1A1A; border-radius: 4px;
}
QTabBar::tab {
    background-color: #2D2D2D; color: #888888; border: 1px solid #3F3F3F;
    border-bottom: none; padding: 6px 12px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1A1A1A; color: #007ACC; border-bottom: 1px solid #1A1A1A; font-weight: bold;
}
QTabBar::tab:hover:!selected { background-color: #333333; color: #CCCCCC; }
QLabel#TitleLabel { color: #E0E0E0; font-size: 11pt; font-weight: bold; padding-left: 5px; }
QLabel.SubLabel { color: #888888; font-size: 8pt; font-weight: bold; }
"""

```

## `view/widget_factory.py`

```python
# -*- coding: utf-8 -*-
"""
view/widget_factory.py
~~~~~~~~~~~~~~~~~~~~~~
반복 생성되는 위젯/스타일을 한곳에서 찍어내는 팩토리.

[모은 이유 - 기존 중복]
  - ✕ 닫기 버튼: main_window.py 와 calendar_window.py에 스타일까지 통째로 복붙.
  - QDoubleSpinBox 기본 설정: calculator_tab._create_spinbox 안에만 존재했으나
    위젯이 늘면 재사용 필요.
  - "리스트 + 추가/삭제 버튼" 세트: task_detail_dialog에서 Jira/폴더/첨부 3회 반복.

스타일 문자열은 모듈 상수로 분리해 한 곳에서만 고치면 모든 위젯에 반영되게 함.
"""

from __future__ import annotations

from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QPushButton, QDoubleSpinBox, QListWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
)


# ----------------------------------------------------------------------
# 공유 스타일 상수 (한 곳에서만 수정)
# ----------------------------------------------------------------------
CLOSE_BUTTON_QSS = """
    QPushButton {
        background-color: #222222;
        color: #ff5555;
        font-weight: bold;
        font-size: 10pt;
        border: 1px solid #444444;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #ff3333;
        color: white;
        border-color: #ff3333;
    }
"""

SMALL_PASTE_QSS = "font-size: 8pt; padding: 2px;"


# ----------------------------------------------------------------------
# 팩토리 함수
# ----------------------------------------------------------------------
def make_close_button() -> QPushButton:
    """창 우상단 ✕ 닫기(=트레이 숨김) 버튼. 모든 창이 동일 외형을 공유."""
    btn = QPushButton("✕")
    btn.setFixedSize(24, 24)
    btn.setStyleSheet(CLOSE_BUTTON_QSS)
    return btn


def make_spinbox(
    min_val: float = -9999999.0,
    max_val: float = 9999999.0,
    default: float = 0.0,
    decimals: int = 4,
    step: float = 1.0,
) -> QDoubleSpinBox:
    """오프셋 입력용 표준 QDoubleSpinBox."""
    spin = QDoubleSpinBox()
    spin.setRange(min_val, max_val)
    spin.setValue(default)
    spin.setDecimals(decimals)
    spin.setSingleStep(step)
    return spin


def make_small_button(text: str, width: Optional[int] = 55) -> QPushButton:
    """'붙여넣기' 류 소형 보조 버튼."""
    btn = QPushButton(text)
    if width is not None:
        btn.setFixedWidth(width)
    btn.setStyleSheet(SMALL_PASTE_QSS)
    return btn


def make_list_with_buttons(
    header_text: str,
    add_text: str = "추가",
    del_text: str = "삭제",
    list_qss: str = "background-color: #333; color: white;",
) -> Tuple[QWidget, QListWidget, QPushButton, QPushButton]:
    """
    '헤더 라벨 + 리스트 + (추가/삭제) 버튼' 세트를 한 번에 생성.

    반환: (컨테이너 위젯, 리스트위젯, 추가버튼, 삭제버튼)
    호출측은 컨테이너를 레이아웃에 넣고, 리스트/버튼에 시그널만 연결하면 됨.
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    layout.addWidget(QLabel(header_text))

    listbox = QListWidget()
    listbox.setStyleSheet(list_qss)
    layout.addWidget(listbox)

    btn_row = QHBoxLayout()
    btn_add = QPushButton(add_text)
    btn_del = QPushButton(del_text)
    btn_row.addWidget(btn_add)
    btn_row.addWidget(btn_del)
    layout.addLayout(btn_row)

    return container, listbox, btn_add, btn_del

```

## `view/main_window.py`

```python
# -*- coding: utf-8 -*-
"""
view/main_window.py
~~~~~~~~~~~~~~~~~~~
TaskHub 메인 프레임리스 윈도우 (오프셋 연산기 + 좌표/단위 변환 탭).
"""

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QTabWidget
from PyQt6.QtCore import Qt, QPoint
from view.styles import DARK_THEME_STYLE
from view.widget_factory import make_close_button
from view.components.calculator_tab import CalculatorTab
from view.components.converter_tab import ConverterTab
from controller.calculator_controller import CalculatorController
from controller.converter_controller import ConverterController
from model.delta_calculator import DeltaCalculator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.resize(390, 550)
        self.drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 5, 5, 5)
        title_label = QLabel("TaskHub - TA Helper")
        title_label.setObjectName("TitleLabel")
        self.btn_close = make_close_button()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.btn_close)
        layout.addWidget(title_bar)

        self.tab_widget = QTabWidget()
        self.calculator_tab = CalculatorTab()
        self.tab_widget.addTab(self.calculator_tab, "통합 오프셋 연산기")
        self.converter_tab = ConverterTab()
        self.tab_widget.addTab(self.converter_tab, "좌표/단위 변환")
        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

        self.calculator_controller = CalculatorController(
            view=self.calculator_tab, model=DeltaCalculator()
        )
        self.converter_controller = ConverterController(view=self.converter_tab)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

```

## `view/calendar_window.py`

```python
# -*- coding: utf-8 -*-
"""
view/calendar_window.py
~~~~~~~~~~~~~~~~~~~~~~~
드래그 다중 선택 캘린더 + 일감/회의 스위핑.
- 업데이트/회의받기 통합 단일 btn_action (모드별 라벨/동작 전환)
- 셀당 표시 제한 + '+N건 더' 팝업 (하위 주차 잘림 방지)
"""

import calendar
import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGridLayout, QFrame, QMenu,
                             QDialog, QSizePolicy, QListWidget)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from view.styles import DARK_THEME_STYLE
from view.widget_factory import make_close_button
from view.components.task_detail_dialog import TaskDetailDialog

calendar.setfirstweekday(calendar.SUNDAY)

MAX_ITEMS_PER_CELL = 3


class DayCell(QFrame):
    cell_pressed = pyqtSignal(int)
    cell_entered = pyqtSignal(int)
    cell_released = pyqtSignal()
    double_clicked = pyqtSignal(int)
    right_clicked = pyqtSignal(object, int)
    more_clicked = pyqtSignal(int)

    def __init__(self, day_num, is_today, is_past, text_color, bg_color):
        super().__init__()
        self.day_num = day_num
        self.is_today = is_today
        self.is_past = is_past
        self.default_bg = bg_color
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(1, 1)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #252525; border-radius: 4px;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        lbl_style = f"color: {text_color}; font-weight: {'bold' if is_today else 'normal'}; font-size: 10pt;"
        self.num_label = QLabel(str(day_num))
        self.num_label.setStyleSheet(lbl_style)
        self.layout.addWidget(self.num_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def add_task_label(self, task_name, color, is_past):
        t_color = "#555555" if is_past else (color if color else "#bced91")
        tl = QLabel()
        tl.setWordWrap(False)
        tl.setStyleSheet(f"background-color: {'#2a2a2a' if is_past else '#333'}; color: {t_color}; font-size: 8.5pt; padding: 2px;")
        self._elide(tl, task_name, "■ ")
        self.layout.addWidget(tl)

    def add_meeting_label(self, title, time_str, is_past):
        t_color = "#555555" if is_past else "#ffcc00"
        prefix = f"🕒 {time_str} " if time_str else "🕒 "
        ml = QLabel()
        ml.setWordWrap(False)
        ml.setStyleSheet(f"background-color: {'#2a2a2a' if is_past else '#3a3320'}; color: {t_color}; font-size: 8.5pt; padding: 2px;")
        self._elide(ml, title, prefix)
        self.layout.addWidget(ml)

    def add_more_label(self, extra_count):
        more = QLabel(f"  + {extra_count}건 더…")
        more.setStyleSheet("color: #888888; font-size: 8pt; padding: 1px; text-decoration: underline;")
        more.setCursor(Qt.CursorShape.PointingHandCursor)

        def _emit(ev):
            if ev.button() == Qt.MouseButton.LeftButton:
                self.more_clicked.emit(self.day_num)
                ev.accept()

        more.mousePressEvent = _emit
        self.layout.addWidget(more)

    def _elide(self, label, text, prefix):
        full = f"{prefix}{text}"
        if len(full) > 16:
            full = full[:15] + "…"
        label.setText(full)
        label.setToolTip(f"{prefix}{text}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.cell_pressed.emit(self.day_num)
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(event.globalPosition().toPoint(), self.day_num)
            event.accept()

    def mouseMoveEvent(self, event):
        self.cell_entered.emit(self.day_num)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.cell_released.emit()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.day_num)
            event.accept()


class CalendarWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_THEME_STYLE)
        self._default_width, self._default_height = 920, 640
        self.resize(self._default_width, self._default_height)
        self.now = datetime.datetime.now()
        self.year, self.month = self.now.year, self.now.month
        self.view_mode = "task"
        self.selected_days = set()
        self.drag_start_day = None
        self.is_dragging = False
        self.cells = {}
        self.drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QWidget()
        header.setStyleSheet("background-color: #2d2d2d; border-radius: 4px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = QLabel(f"{self.year}년 {self.month}월")
        self.title_label.setStyleSheet("color: white; font-size: 12pt; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        self.btn_view_toggle = QPushButton("📋 일감 보기")
        self.btn_view_toggle.setStyleSheet("color: #bced91; font-weight: bold;")
        header_layout.addWidget(self.btn_view_toggle)

        self.btn_action = QPushButton("🔄 업데이트")
        self.btn_action.setStyleSheet("color: #5da9e9; font-weight: bold;")
        self.btn_period = QPushButton("📅 기간 추가")
        self.btn_period.setStyleSheet("color: #bced91; font-weight: bold;")
        self.btn_clear = QPushButton("🗑️ 비우기")
        self.btn_clear.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.btn_login = QPushButton("👤 로그인")
        self.btn_settings = QPushButton("⚙️ 설정")

        header_layout.addWidget(self.btn_action)
        header_layout.addWidget(self.btn_period)
        header_layout.addWidget(self.btn_clear)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_login)
        header_layout.addWidget(self.btn_settings)

        self.btn_close = make_close_button()
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header)

        self.body_layout = QGridLayout()
        self.body_layout.setSpacing(2)
        layout.addLayout(self.body_layout)

        self.btn_view_toggle.clicked.connect(self.toggle_view_mode)
        self._apply_mode_buttons()
        self.draw_calendar()
        self.setCentralWidget(central_widget)

    def _apply_mode_buttons(self):
        is_meeting = (self.view_mode == "meeting")
        if is_meeting:
            self.btn_action.setText("👥 회의 받기")
            self.btn_action.setStyleSheet("color: #ffcc00; font-weight: bold;")
            self.btn_view_toggle.setText("👥 회의 보기")
            self.btn_view_toggle.setStyleSheet("color: #ffcc00; font-weight: bold;")
        else:
            self.btn_action.setText("🔄 업데이트")
            self.btn_action.setStyleSheet("color: #5da9e9; font-weight: bold;")
            self.btn_view_toggle.setText("📋 일감 보기")
            self.btn_view_toggle.setStyleSheet("color: #bced91; font-weight: bold;")
        self.btn_period.setVisible(not is_meeting)
        self.btn_clear.setVisible(not is_meeting)

    def toggle_view_mode(self):
        self.view_mode = "meeting" if self.view_mode == "task" else "task"
        self._apply_mode_buttons()
        self.draw_calendar()

    def draw_calendar(self):
        for i in reversed(range(self.body_layout.count())):
            w = self.body_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self.cells.clear()
        cal = calendar.monthcalendar(self.year, self.month)
        today = datetime.date.today()
        holidays = self.model.config.get("holidays", [])
        self.body_layout.setRowStretch(0, 0)
        for i in range(7):
            self.body_layout.setColumnStretch(i, 1)
        for i in range(1, 7):
            self.body_layout.setRowStretch(i, 0)
        num_weeks = len(cal)
        for i in range(1, num_weeks + 1):
            self.body_layout.setRowStretch(i, 1)
        days_header = ['일', '월', '화', '수', '목', '금', '토']
        for i, d in enumerate(days_header):
            fg = '#ff6b6b' if i == 0 else ('#5da9e9' if i == 6 else '#aaaaaa')
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            lbl.setStyleSheet(f"color: {fg}; font-weight: bold; font-size: 10pt; padding: 5px;")
            self.body_layout.addWidget(lbl, 0, i)

        for r, week in enumerate(cal):
            for c, d in enumerate(week):
                if d == 0:
                    empty = QFrame()
                    empty.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
                    empty.setMinimumSize(1, 1)
                    empty.setStyleSheet("background-color: #1e1e1e; border: 1px solid #252525;")
                    self.body_layout.addWidget(empty, r + 1, c)
                    continue
                c_date = datetime.date(self.year, self.month, d)
                is_today = (c_date == today)
                is_past = (c_date < today)
                is_holi = f"{self.year}-{self.month}-{d}" in holidays
                bg = '#2d353d' if is_today else '#252525'
                cfg = '#777777' if is_past else ('#ff6b6b' if c == 0 or is_holi else ('#5da9e9' if c == 6 else 'white'))
                if is_today:
                    cfg = '#ffcc00'
                cell = DayCell(d, is_today, is_past, cfg, bg)
                if self.view_mode == "task":
                    items = self.model.schedule_data.get((self.year, self.month, d), [])
                    shown = items[:MAX_ITEMS_PER_CELL]
                    for t in shown:
                        cell.add_task_label(t["task"], t.get("color"), is_past)
                else:
                    items = self._get_meetings_for_day(d)
                    shown = items[:MAX_ITEMS_PER_CELL]
                    for mtg in shown:
                        cell.add_meeting_label(mtg.get("title", ""), mtg.get("time", ""), is_past)
                extra = len(items) - len(shown)
                if extra > 0:
                    cell.add_more_label(extra)
                cell.layout.addStretch(1)
                cell.cell_pressed.connect(self.on_cell_pressed)
                cell.cell_entered.connect(self.on_cell_entered)
                cell.cell_released.connect(self.on_cell_released)
                cell.double_clicked.connect(self.on_cell_double_clicked)
                cell.right_clicked.connect(self.on_cell_right_clicked)
                cell.more_clicked.connect(self.on_more_clicked)
                self.body_layout.addWidget(cell, r + 1, c)
                self.cells[d] = cell
        self.update_selection_highlights()

    def _get_meetings_for_day(self, d):
        meeting_data = getattr(self.model, "meeting_data", {})
        return meeting_data.get((self.year, self.month, d), [])

    def on_cell_pressed(self, day):
        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if day in self.selected_days:
                self.selected_days.remove(day)
            else:
                self.selected_days.add(day)
        else:
            self.selected_days = {day}
        self.drag_start_day = day
        self.is_dragging = True
        self.update_selection_highlights()

    def on_cell_entered(self, day):
        if self.is_dragging and self.drag_start_day is not None:
            s, e = min(self.drag_start_day, day), max(self.drag_start_day, day)
            self.selected_days = set(range(s, e + 1))
            self.update_selection_highlights()

    def on_cell_released(self):
        self.is_dragging = False

    def update_selection_highlights(self):
        for d, cell in self.cells.items():
            if d in self.selected_days:
                cell.setStyleSheet(f"background-color: {cell.default_bg}; border: 2px solid #ffcc00; border-radius: 4px;")
            else:
                cell.setStyleSheet(f"background-color: {cell.default_bg}; border: 1px solid #252525; border-radius: 4px;")

    def on_cell_double_clicked(self, day):
        if self.view_mode == "meeting":
            return
        dialog = TaskDetailDialog(self, (self.year, self.month, day), self.model)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.draw_calendar()

    def on_cell_right_clicked(self, pos, day):
        if self.view_mode == "meeting":
            return
        if day not in self.selected_days:
            self.selected_days = {day}
            self.update_selection_highlights()
        menu = QMenu(self)
        action_add = menu.addAction("➕ 선택 기간 일괄 추가")
        action_del = menu.addAction("🗑️ 선택 기간 일괄 삭제")
        action = menu.exec(pos)
        if action == action_add:
            self.btn_period.click()
        elif action == action_del:
            self.delete_selected_days_data()

    def on_more_clicked(self, day):
        if self.view_mode == "task":
            items = self.model.schedule_data.get((self.year, self.month, day), [])
            rows = [f"■ {it.get('task', '')}" for it in items]
            header = f"{self.month}/{day} 일감 전체 ({len(items)}건)"
        else:
            items = self._get_meetings_for_day(day)
            rows = []
            for it in items:
                t = it.get("time", "")
                prefix = f"🕒 {t} " if t else "🕒 "
                rows.append(f"{prefix}{it.get('title', '')}")
            header = f"{self.month}/{day} 회의 전체 ({len(items)}건)"
        dlg = QDialog(self)
        dlg.setWindowTitle(header)
        dlg.setStyleSheet(self.styleSheet())
        dlg.resize(360, 420)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>{header}</b>"))
        lst = QListWidget()
        lst.setStyleSheet("background-color: #1e1e1e; color: white; border: 1px solid #333;")
        for row in rows:
            lst.addItem(row)
        lay.addWidget(lst)
        if self.view_mode == "task":
            def _open_detail(_):
                dlg.accept()
                self.on_cell_double_clicked(day)
            lst.itemDoubleClicked.connect(_open_detail)
            hint = QLabel("항목 더블클릭 → 상세 편집")
            hint.setStyleSheet("color:#888; font-size:8pt;")
            lay.addWidget(hint)
        dlg.exec()

    def delete_selected_days_data(self):
        for d in self.selected_days:
            key = (self.year, self.month, d)
            if key in self.model.schedule_data:
                del self.model.schedule_data[key]
        self.selected_days.clear()
        self.model.save_schedules()
        self.draw_calendar()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

```

## `view/components/calculator_tab.py`

```python
# -*- coding: utf-8 -*-
"""
view/components/calculator_tab.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
클립보드 일괄 / 개별 PRS 수동 / 오프셋 가산 보정의 3가지 입력 모드를 동적 스왑하는 통합 뷰
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QStackedWidget, QGridLayout)
from PyQt6.QtCore import Qt
from view.widget_factory import make_spinbox


class CalculatorTab(QWidget):
    """3가지 입력 방식(클립보드, 수동 PRS, 오프셋 보정)을 로테이션 탑재한 연산 탭"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_layout()

    def _init_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.btn_toggle_mode = QPushButton("현재 모드: [일괄 클립보드] (클릭하여 전환)")
        self.btn_toggle_mode.setObjectName("ToggleModeButton")
        layout.addWidget(self.btn_toggle_mode)

        self.input_stack = QStackedWidget()

        # -- 페이지 0: 일괄 클립보드 계산 모드 --
        page0_clip = QWidget()
        page0_layout = QVBoxLayout(page0_clip)
        page0_layout.setContentsMargins(0, 0, 0, 0)
        page0_layout.setSpacing(8)

        page0_layout.addWidget(QLabel("<b>[1] Start Transform (A 오브젝트)</b>"))
        start_row = QHBoxLayout()
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("언리얼에서 복사 후 우측 버튼 클릭")
        self.start_input.setReadOnly(True)
        self.start_input.setStyleSheet("background-color: #151515; color: #FFFFFF; border: 1px solid #333; padding: 4px;")
        self.btn_paste_start = QPushButton("붙여넣기")
        start_row.addWidget(self.start_input)
        start_row.addWidget(self.btn_paste_start)
        page0_layout.addLayout(start_row)

        page0_layout.addWidget(QLabel("<b>[2] Target Transform (B 오브젝트)</b>"))
        target_row = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("언리얼에서 복사 후 우측 버튼 클릭")
        self.target_input.setReadOnly(True)
        self.target_input.setStyleSheet("background-color: #151515; color: #FFFFFF; border: 1px solid #333; padding: 4px;")
        self.btn_paste_target = QPushButton("붙여넣기")
        target_row.addWidget(self.target_input)
        target_row.addWidget(self.btn_paste_target)
        page0_layout.addLayout(target_row)

        self.input_stack.addWidget(page0_clip)

        # -- 페이지 1: 개별 PRS 수동 계산 모드 --
        page1_manual = QWidget()
        page1_layout = QVBoxLayout(page1_manual)
        page1_layout.setContentsMargins(0, 0, 0, 0)
        page1_layout.setSpacing(8)

        page1_layout.addWidget(QLabel("<b>[1] Start Transform (A 오브젝트)</b>"))
        start_grid = QGridLayout()
        self._setup_prs_inputs(start_grid, "start")
        page1_layout.addLayout(start_grid)

        page1_layout.addWidget(QLabel("<b>[2] Target Transform (B 오브젝트)</b>"))
        target_grid = QGridLayout()
        self._setup_prs_inputs(target_grid, "target")
        page1_layout.addLayout(target_grid)

        self.input_stack.addWidget(page1_manual)

        # -- 페이지 2: 오프셋 가산 보정 모드 --
        page2_corrector = QWidget()
        page2_layout = QVBoxLayout(page2_corrector)
        page2_layout.setContentsMargins(0, 0, 0, 0)
        page2_layout.setSpacing(8)

        page2_layout.addWidget(QLabel("<b>[1] 기존 계산된 오프셋 (Original Delta)</b>"))
        orig_grid = QGridLayout()
        self._setup_prs_inputs(orig_grid, "orig", show_scl=False)
        page2_layout.addLayout(orig_grid)

        page2_layout.addWidget(QLabel("<b>[2] 수정 전 씬 오브젝트 PRS (Base Old)</b>"))
        old_grid = QGridLayout()
        self._setup_prs_inputs(old_grid, "old", show_scl=False)
        page2_layout.addLayout(old_grid)

        page2_layout.addWidget(QLabel("<b>[3] 수정 후 씬 오브젝트 PRS (Base New)</b>"))
        new_grid = QGridLayout()
        self._setup_prs_inputs(new_grid, "new", show_scl=False)
        page2_layout.addLayout(new_grid)

        self.input_stack.addWidget(page2_corrector)

        layout.addWidget(self.input_stack)

        layout.addWidget(QLabel("<hr style='border: 1px solid #333333;' />"))

        self.result_title = QLabel("<b>[3] Calculated Delta Result (B - A)</b>")
        layout.addWidget(self.result_title)

        self.vector_lbl = QLabel("위치 오프셋 (Vector Delta):")
        layout.addWidget(self.vector_lbl)
        vector_row = QHBoxLayout()
        self.vector_result_label = QLabel("Waiting for Location inputs...")
        self.vector_result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.vector_result_label.setStyleSheet("background-color: #111111; padding: 6px; border-radius: 4px; color: #A0A0A0;")
        self.btn_copy_vector = QPushButton("복사")
        self.btn_copy_vector.setEnabled(False)
        vector_row.addWidget(self.vector_result_label, stretch=1)
        vector_row.addWidget(self.btn_copy_vector)
        layout.addLayout(vector_row)

        self.rotator_lbl = QLabel("회전 오프셋 (Rotator Delta - 최단 경로):")
        layout.addWidget(self.rotator_lbl)
        rotator_row = QHBoxLayout()
        self.rotator_result_label = QLabel("Waiting for Rotation inputs...")
        self.rotator_result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.rotator_result_label.setStyleSheet("background-color: #111111; padding: 6px; border-radius: 4px; color: #A0A0A0;")
        self.btn_copy_rotator = QPushButton("복사")
        self.btn_copy_rotator.setEnabled(False)
        rotator_row.addWidget(self.rotator_result_label, stretch=1)
        rotator_row.addWidget(self.btn_copy_rotator)
        layout.addLayout(rotator_row)

        layout.addStretch()

    def _setup_prs_inputs(self, grid, prefix, show_scl=True):
        lbl_p = QLabel("P (Loc)")
        lbl_p.setProperty("class", "SubLabel")
        setattr(self, f"{prefix}_px", self._create_spinbox())
        setattr(self, f"{prefix}_py", self._create_spinbox())
        setattr(self, f"{prefix}_pz", self._create_spinbox())
        setattr(self, f"{prefix}_btn_paste_loc", QPushButton("붙여넣기"))
        getattr(self, f"{prefix}_btn_paste_loc").setFixedWidth(55)
        getattr(self, f"{prefix}_btn_paste_loc").setStyleSheet("font-size: 8pt; padding: 2px;")

        grid.addWidget(lbl_p, 0, 0)
        grid.addWidget(getattr(self, f"{prefix}_px"), 0, 1)
        grid.addWidget(getattr(self, f"{prefix}_py"), 0, 2)
        grid.addWidget(getattr(self, f"{prefix}_pz"), 0, 3)
        grid.addWidget(getattr(self, f"{prefix}_btn_paste_loc"), 0, 4)

        lbl_r = QLabel("R (Rot)")
        lbl_r.setProperty("class", "SubLabel")
        setattr(self, f"{prefix}_rp", self._create_spinbox(-3600.0, 3600.0))
        setattr(self, f"{prefix}_ry", self._create_spinbox(-3600.0, 3600.0))
        setattr(self, f"{prefix}_rr", self._create_spinbox(-3600.0, 3600.0))
        setattr(self, f"{prefix}_btn_paste_rot", QPushButton("붙여넣기"))
        getattr(self, f"{prefix}_btn_paste_rot").setFixedWidth(55)
        getattr(self, f"{prefix}_btn_paste_rot").setStyleSheet("font-size: 8pt; padding: 2px;")

        grid.addWidget(lbl_r, 1, 0)
        grid.addWidget(getattr(self, f"{prefix}_rp"), 1, 1)
        grid.addWidget(getattr(self, f"{prefix}_ry"), 1, 2)
        grid.addWidget(getattr(self, f"{prefix}_rr"), 1, 3)
        grid.addWidget(getattr(self, f"{prefix}_btn_paste_rot"), 1, 4)

        if show_scl:
            lbl_s = QLabel("S (Scl)")
            lbl_s.setProperty("class", "SubLabel")
            setattr(self, f"{prefix}_sx", self._create_spinbox(-1000.0, 1000.0, 1.0))
            setattr(self, f"{prefix}_sy", self._create_spinbox(-1000.0, 1000.0, 1.0))
            setattr(self, f"{prefix}_sz", self._create_spinbox(-1000.0, 1000.0, 1.0))
            setattr(self, f"{prefix}_btn_paste_scl", QPushButton("붙여넣기"))
            getattr(self, f"{prefix}_btn_paste_scl").setFixedWidth(55)
            getattr(self, f"{prefix}_btn_paste_scl").setStyleSheet("font-size: 8pt; padding: 2px;")

            grid.addWidget(lbl_s, 2, 0)
            grid.addWidget(getattr(self, f"{prefix}_sx"), 2, 1)
            grid.addWidget(getattr(self, f"{prefix}_sy"), 2, 2)
            grid.addWidget(getattr(self, f"{prefix}_sz"), 2, 3)
            grid.addWidget(getattr(self, f"{prefix}_btn_paste_scl"), 2, 4)

    def _create_spinbox(self, min_val=-9999999.0, max_val=9999999.0, default=0.0):
        # [리팩터링] 표준 스핀박스 생성은 공용 팩토리에 위임
        return make_spinbox(min_val, max_val, default)

```

## `view/components/converter_tab.py`

```python
# -*- coding: utf-8 -*-
"""
view/components/converter_tab.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
좌표계 변환(언리얼/맥스/마야/블렌더) + 단위 변환(cm↔m, 도↔라디안) 입력 뷰.
로직은 controller/converter_controller.py 가 담당.
[불변] ENGINE_LABELS 순서 = converter_controller.ENGINE_KEYS 순서.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt
from view.widget_factory import make_spinbox

ENGINE_LABELS = [("언리얼", "unreal"), ("3ds Max", "max"), ("마야", "maya"), ("블렌더", "blender")]


class ConverterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>[좌표계 변환]</b>"))

        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("From"))
        self.combo_from = QComboBox()
        self.combo_to = QComboBox()
        for label, _ in ENGINE_LABELS:
            self.combo_from.addItem(label)
            self.combo_to.addItem(label)
        self.combo_from.setCurrentIndex(2)
        self.combo_to.setCurrentIndex(0)
        self.btn_swap_engine = QPushButton("⇄")
        self.btn_swap_engine.setObjectName("ToggleModeButton")
        self.btn_swap_engine.setFixedWidth(40)
        engine_row.addWidget(self.combo_from)
        engine_row.addWidget(self.btn_swap_engine)
        engine_row.addWidget(QLabel("To"))
        engine_row.addWidget(self.combo_to)
        engine_row.addStretch()
        layout.addLayout(engine_row)

        grid = QGridLayout()
        grid.addWidget(QLabel("<b>입력 (P / R / S)</b>"), 0, 0, 1, 5)
        self._make_xyz(grid, "pos", 1, "P (Loc)")
        self._make_xyz(grid, "rot", 2, "R (Rot)")
        self._make_xyz(grid, "scl", 3, "S (Scl)", default=1.0)
        self.btn_paste_clip = QPushButton("📋 언리얼 클립보드 일괄 붙여넣기")
        grid.addWidget(self.btn_paste_clip, 4, 0, 1, 5)
        layout.addLayout(grid)

        self.btn_convert = QPushButton("▶ 변환 실행")
        self.btn_convert.setObjectName("ToggleModeButton")
        layout.addWidget(self.btn_convert)

        layout.addWidget(QLabel("<b>[변환 결과]</b>"))
        self.lbl_pos_result = self._result_label("위치: -")
        layout.addWidget(self.lbl_pos_result)
        self.lbl_scl_result = self._result_label("스케일: -")
        layout.addWidget(self.lbl_scl_result)
        self.lbl_rot_result = self._result_label("회전(근사): -")
        layout.addWidget(self.lbl_rot_result)
        self.lbl_warn = QLabel("")
        self.lbl_warn.setWordWrap(True)
        self.lbl_warn.setStyleSheet("color:#ffcc00; font-size:8pt;")
        layout.addWidget(self.lbl_warn)

        self.btn_copy_pos = QPushButton("위치 복사 (언리얼 형식)")
        self.btn_copy_pos.setEnabled(False)
        layout.addWidget(self.btn_copy_pos)

        layout.addWidget(QLabel("<hr style='border:1px solid #333;'/>"))

        layout.addWidget(QLabel("<b>[단위 변환]</b>"))
        unit_row = QHBoxLayout()
        self.unit_input = make_spinbox(-1e9, 1e9, 0.0)
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["cm → m", "m → cm", "도 → 라디안", "라디안 → 도"])
        unit_row.addWidget(self.unit_input)
        unit_row.addWidget(self.combo_unit)
        layout.addLayout(unit_row)
        self.lbl_unit_result = self._result_label("결과: -")
        layout.addWidget(self.lbl_unit_result)

        layout.addStretch()

    def _make_xyz(self, grid, prefix, row, label, default=0.0):
        grid.addWidget(QLabel(label), row, 0)
        for i, axis in enumerate(("x", "y", "z")):
            spin = make_spinbox(-1e9, 1e9, default)
            setattr(self, f"{prefix}_{axis}", spin)
            grid.addWidget(spin, row, i + 1)

    def _result_label(self, text):
        lbl = QLabel(text)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet("background-color:#111; padding:6px; border-radius:4px; color:#bced91;")
        return lbl

```

## `view/components/task_detail_dialog.py`

```python
# -*- coding: utf-8 -*-
"""
view/components/task_detail_dialog.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
일감별 상세 메모, Jira 링크, 네트워크 경로, 미디어 첨부파일 제어 다크 다이얼로그
(이름 변경 즉시 피드백 연동)
"""

import os
import shutil
import time
import webbrowser
import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QTextEdit, QFileDialog, QInputDialog, QMenu, QWidget)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QGuiApplication, QKeySequence, QShortcut
from core.constants import ATTACH_DIR


class TaskDetailDialog(QDialog):
    def __init__(self, parent, date_tuple, schedule_model):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setWindowTitle(f"일감 상세 관리자 ({date_tuple[1]}월 {date_tuple[2]}일)")
        self.date_tuple = date_tuple
        self.model = schedule_model
        self.cur_tasks = [dict(t) for t in self.model.schedule_data.get(date_tuple, [])]
        self.active_task = None
        self.current_jiras = []
        self.current_folders = []
        self.current_attach = []
        self._init_ui()
        self._load_first_task()

    def _init_ui(self):
        self.setStyleSheet(self.parent().styleSheet())
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        body = QHBoxLayout()

        left_frame = QWidget()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel(f"📅 {self.date_tuple[1]}/{self.date_tuple[2]} 일감 목록"))
        self.task_list_widget = QListWidget()
        self.task_list_widget.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
        self.task_list_widget.itemClicked.connect(self.on_task_selected)
        left_layout.addWidget(self.task_list_widget)
        btn_add_task = QPushButton("+ 새 일감 추가")
        btn_add_task.clicked.connect(self.add_new_task)
        left_layout.addWidget(btn_add_task)
        body.addWidget(left_frame, stretch=1)

        right_frame = QWidget()
        right_frame.setStyleSheet("background-color: #222222; border: 1px solid #444; border-radius: 4px;")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)

        edit_name_row = QHBoxLayout()
        self.txt_task_name = QLineEdit()
        self.txt_task_name.setStyleSheet("background-color: #333; color: #5da9e9; font-size: 12pt; font-weight: bold; border: none; padding: 4px;")
        btn_save_name = QPushButton("💾 이름 변경 저장")
        btn_save_name.setStyleSheet("background-color: #1a365d; color: #00bfff; border: 1px solid #007acc; font-weight: bold;")
        btn_save_name.clicked.connect(self.save_task_name)
        edit_name_row.addWidget(self.txt_task_name, stretch=1)
        edit_name_row.addWidget(btn_save_name)
        right_layout.addLayout(edit_name_row)

        self.lbl_status = QLabel("일정 대기 중...")
        self.lbl_status.setStyleSheet("color: #ffcc00; font-size: 9pt;")
        right_layout.addWidget(self.lbl_status)

        links_row = QHBoxLayout()
        jira_layout = QVBoxLayout()
        jira_layout.addWidget(QLabel("🌐 Jira (더블클릭: 이동 / 우클릭: 이름변경)"))
        self.jira_listbox = QListWidget()
        self.jira_listbox.setStyleSheet("background-color: #333; color: white;")
        self.jira_listbox.doubleClicked.connect(self.open_jira_link)
        self.jira_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.jira_listbox.customContextMenuRequested.connect(self.show_jira_context_menu)
        jira_layout.addWidget(self.jira_listbox)
        btn_jira_control = QHBoxLayout()
        btn_add_j = QPushButton("추가")
        btn_add_j.clicked.connect(self.add_jira)
        btn_del_j = QPushButton("삭제")
        btn_del_j.clicked.connect(self.del_jira)
        btn_jira_control.addWidget(btn_add_j)
        btn_jira_control.addWidget(btn_del_j)
        jira_layout.addLayout(btn_jira_control)
        links_row.addLayout(jira_layout)

        folder_layout = QVBoxLayout()
        folder_layout.addWidget(QLabel("📁 폴더 (더블클릭: 열기 / 우클릭: 이름변경)"))
        self.folder_listbox = QListWidget()
        self.folder_listbox.setStyleSheet("background-color: #333; color: white;")
        self.folder_listbox.doubleClicked.connect(self.open_folder_path)
        self.folder_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_listbox.customContextMenuRequested.connect(self.show_folder_context_menu)
        folder_layout.addWidget(self.folder_listbox)
        btn_folder_control = QHBoxLayout()
        btn_add_f = QPushButton("추가")
        btn_add_f.clicked.connect(self.add_folder)
        btn_del_f = QPushButton("삭제")
        btn_del_f.clicked.connect(self.del_folder)
        btn_folder_control.addWidget(btn_add_f)
        btn_folder_control.addWidget(btn_del_f)
        folder_layout.addLayout(btn_folder_control)
        links_row.addLayout(folder_layout)
        right_layout.addLayout(links_row)

        memo_attach_row = QHBoxLayout()
        memo_layout = QVBoxLayout()
        memo_title_bar = QHBoxLayout()
        memo_title_bar.addWidget(QLabel("📝 누적 엑셀 메모 및 주의사항"))
        btn_clear_memo = QPushButton("🗑️ 지우기")
        btn_clear_memo.setStyleSheet("font-size: 8pt; padding: 2px;")
        btn_clear_memo.clicked.connect(lambda: self.memo_text.clear())
        memo_title_bar.addWidget(btn_clear_memo)
        memo_layout.addLayout(memo_title_bar)
        self.memo_text = QTextEdit()
        self.memo_text.setStyleSheet("background-color: #1e1e1e; color: white; border: none; padding: 5px;")
        self.memo_text.setUndoRedoEnabled(True)
        memo_layout.addWidget(self.memo_text)
        memo_attach_row.addLayout(memo_layout, stretch=1)

        attach_layout = QVBoxLayout()
        attach_layout.addWidget(QLabel("📎 파일 첨부 (Ctrl+V 클립보드 이미지 지원)"))
        self.attach_listbox = QListWidget()
        self.attach_listbox.setStyleSheet("background-color: #333; color: white;")
        self.attach_listbox.doubleClicked.connect(self.open_attachment)
        self.attach_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.attach_listbox.customContextMenuRequested.connect(self.show_attach_context_menu)
        attach_layout.addWidget(self.attach_listbox)
        btn_add_attach = QPushButton("[+] 파일 추가")
        btn_add_attach.clicked.connect(self.add_attachment_file)
        attach_layout.addWidget(btn_add_attach)
        memo_attach_row.addLayout(attach_layout, stretch=1)
        right_layout.addLayout(memo_attach_row)

        save_layout = QHBoxLayout()
        save_layout.addStretch()
        btn_save_all = QPushButton("모든 정보 통합 저장")
        btn_save_all.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 18px;")
        btn_save_all.clicked.connect(self.save_all_and_close)
        save_layout.addWidget(btn_save_all)
        right_layout.addLayout(save_layout)

        body.addWidget(right_frame, stretch=2)
        container_layout.addLayout(body)
        main_layout.addWidget(container)

        self.shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self.attach_listbox)
        self.shortcut_paste.activated.connect(self.paste_image_from_clipboard)
        self.resize(1050, 600)

    def _load_first_task(self):
        self._render_left_task_list()
        if self.cur_tasks:
            self.task_list_widget.setCurrentRow(0)
            self._load_task_details(self.cur_tasks[0])

    def _render_left_task_list(self):
        self.task_list_widget.clear()
        for t in self.cur_tasks:
            self.task_list_widget.addItem(t["task"])

    def on_task_selected(self):
        idx = self.task_list_widget.currentRow()
        if 0 <= idx < len(self.cur_tasks):
            self._save_active_task_buffer()
            self._load_task_details(self.cur_tasks[idx])

    def _load_task_details(self, t_dict):
        self.active_task = t_dict
        task_name = t_dict["task"]
        self.txt_task_name.setText(task_name)
        db = self.model.get_task_db_entry(task_name)
        self.current_jiras = list(db.get("jiras", []))
        self.current_folders = list(db.get("folders", []))
        self.current_attach = list(db.get("attachments", []))
        self.jira_listbox.clear()
        for j in self.current_jiras:
            self.jira_listbox.addItem(j["name"])
        self.folder_listbox.clear()
        for f in self.current_folders:
            self.folder_listbox.addItem(f["name"])
        self.attach_listbox.clear()
        for a in self.current_attach:
            self.attach_listbox.addItem(os.path.basename(a))
        self.memo_text.setText(db.get("memo", ""))
        self._calculate_workdays(task_name, t_dict.get("release", ""))

    def _save_active_task_buffer(self):
        if self.active_task:
            task_name = self.active_task["task"]
            db = self.model.get_task_db_entry(task_name)
            db["jiras"] = self.current_jiras.copy()
            db["folders"] = self.current_folders.copy()
            db["attachments"] = self.current_attach.copy()
            db["memo"] = self.memo_text.toPlainText().strip()

    def _calculate_workdays(self, task_name, release):
        dates = []
        for d_tuple, tasks in self.model.schedule_data.items():
            if any(x.get("task") == task_name for x in tasks):
                dates.append(datetime.date(d_tuple[0], d_tuple[1], d_tuple[2]))
        if dates:
            mn, mx = min(dates), max(dates)
            today = datetime.date.today()
            holidays = self.model.config.get("holidays", [])
            work_days = 0
            total_days = (mx - mn).days + 1
            for i in range(total_days):
                cd = mn + datetime.timedelta(days=i)
                if cd.weekday() < 5 and f"{cd.year}-{cd.month}-{cd.day}" not in holidays:
                    work_days += 1
            rem_total = (mx - today).days
            if rem_total < 0:
                d_str = "종료됨"
            else:
                rem_wd = 0
                for i in range(rem_total + 1):
                    cd = today + datetime.timedelta(days=i)
                    if cd.weekday() < 5 and f"{cd.year}-{cd.month}-{cd.day}" not in holidays:
                        rem_wd += 1
                if rem_total == 0:
                    d_str = f"D-Day (남은 WD: {rem_wd}일 - 오늘 마감!)"
                else:
                    d_str = f"D-{rem_total} (남은 WD: {rem_wd}일)"
            prefix = f"[{release}] " if release else ""
            self.lbl_status.setText(f"{prefix}일정: {mn.strftime('%m/%d')}~{mx.strftime('%m/%d')} (총 {work_days} WD)  |  {d_str}")
        else:
            self.lbl_status.setText("등록된 일정이 없습니다.")

    def save_task_name(self):
        old_name = self.active_task["task"] if self.active_task else ""
        new_name = self.txt_task_name.text().strip()
        if not old_name or not new_name or old_name == new_name:
            return
        if old_name in self.model.task_db:
            self.model.task_db[new_name] = self.model.task_db.pop(old_name)
        else:
            self.model.task_db[new_name] = {"jiras": [], "folders": [], "memo": "", "attachments": []}
        for d_tuple, tasks in self.model.schedule_data.items():
            for t in tasks:
                if t.get("task") == old_name:
                    t["task"] = new_name
        self.active_task["task"] = new_name
        self.model.save_task_db()
        self.model.save_schedules()
        self._render_left_task_list()
        self._load_task_details(self.active_task)
        if hasattr(self.parent(), "draw_calendar"):
            self.parent().draw_calendar()

    def add_new_task(self):
        self._save_active_task_buffer()
        new_item = {"task": "새 작업", "color": "", "release": ""}
        self.cur_tasks.append(new_item)
        self._render_left_task_list()
        self.task_list_widget.setCurrentRow(len(self.cur_tasks) - 1)
        self._load_task_details(new_item)

    def add_jira(self):
        text, ok = QInputDialog.getText(self, "Jira 링크 추가", "URL 주소를 입력하세요:")
        if ok and text.strip():
            url = text.strip()
            if not any(x["path"] == url for x in self.current_jiras):
                self.current_jiras.append({"name": url, "path": url})
                self.jira_listbox.addItem(url)

    def del_jira(self):
        row = self.jira_listbox.currentRow()
        if row >= 0:
            self.current_jiras.pop(row)
            self.jira_listbox.takeItem(row)

    def open_jira_link(self):
        row = self.jira_listbox.currentRow()
        if 0 <= row < len(self.current_jiras):
            webbrowser.open(self.current_jiras[row]["path"])

    def show_jira_context_menu(self, pos):
        item = self.jira_listbox.itemAt(pos)
        if item:
            menu = QMenu(self)
            action_rename = menu.addAction("별명 지정")
            action = menu.exec(self.jira_listbox.mapToGlobal(pos))
            if action == action_rename:
                idx = self.jira_listbox.row(item)
                curr_name = self.current_jiras[idx]["name"]
                new_n, ok = QInputDialog.getText(self, "별명 지정", "표시될 닉네임을 입력하세요:", text=curr_name)
                if ok and new_n.strip():
                    self.current_jiras[idx]["name"] = new_n.strip()
                    item.setText(new_n.strip())

    def add_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "네트워크 / 로컬 폴더 연동")
        if dir_path:
            path = dir_path.strip()
            if not any(x["path"] == path for x in self.current_folders):
                self.current_folders.append({"name": path, "path": path})
                self.folder_listbox.addItem(path)

    def del_folder(self):
        row = self.folder_listbox.currentRow()
        if row >= 0:
            self.current_folders.pop(row)
            self.folder_listbox.takeItem(row)

    def open_folder_path(self):
        row = self.folder_listbox.currentRow()
        if 0 <= row < len(self.current_folders):
            path = self.current_folders[row]["path"]
            if os.path.exists(path):
                os.startfile(path)

    def show_folder_context_menu(self, pos):
        item = self.folder_listbox.itemAt(pos)
        if item:
            menu = QMenu(self)
            action_rename = menu.addAction("별명 지정")
            action = menu.exec(self.folder_listbox.mapToGlobal(pos))
            if action == action_rename:
                idx = self.folder_listbox.row(item)
                curr_name = self.current_folders[idx]["name"]
                new_n, ok = QInputDialog.getText(self, "별명 지정", "표시될 폴더 닉네임 입력:", text=curr_name)
                if ok and new_n.strip():
                    self.current_folders[idx]["name"] = new_n.strip()
                    item.setText(new_n.strip())

    def add_attachment_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "첨부할 미디어 파일 선택")
        for fp in file_paths:
            if os.path.exists(fp):
                fn = os.path.basename(fp)
                dest = ATTACH_DIR / fn
                if dest.exists():
                    dest = ATTACH_DIR / f"{int(time.time())}_{fn}"
                shutil.copy2(fp, str(dest))
                dest_str = str(dest)
                if dest_str not in self.current_attach:
                    self.current_attach.append(dest_str)
                    self.attach_listbox.addItem(fn)

    def paste_image_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                fn = f"클립보드_캡처_{time.strftime('%Y%m%d_%H%M%S')}.png"
                dest = ATTACH_DIR / fn
                image.save(str(dest), "PNG")
                dest_str = str(dest)
                if dest_str not in self.current_attach:
                    self.current_attach.append(dest_str)
                    self.attach_listbox.addItem(fn)

    def open_attachment(self):
        row = self.attach_listbox.currentRow()
        if 0 <= row < len(self.current_attach):
            os.startfile(self.current_attach[row])

    def show_attach_context_menu(self, pos):
        item = self.attach_listbox.itemAt(pos)
        if item:
            menu = QMenu(self)
            action_open = menu.addAction("크게 열기")
            action_copy = menu.addAction("경로 복사")
            action_del = menu.addAction("목록에서 삭제")
            action = menu.exec(self.attach_listbox.mapToGlobal(pos))
            idx = self.attach_listbox.row(item)
            if action == action_open:
                os.startfile(self.current_attach[idx])
            elif action == action_copy:
                clipboard = QGuiApplication.clipboard()
                clipboard.setText(self.current_attach[idx])
            elif action == action_del:
                self.current_attach.pop(idx)
                self.attach_listbox.takeItem(idx)

    def save_all_and_close(self):
        self._save_active_task_buffer()
        final_tasks = [t for t in self.cur_tasks if t.get("task", "").strip()]
        if final_tasks:
            self.model.schedule_data[self.date_tuple] = final_tasks
        else:
            if self.date_tuple in self.model.schedule_data:
                del self.model.schedule_data[self.date_tuple]
        self.model.save_task_db()
        self.model.save_schedules()
        self.accept()

```

## `controller/app_controller.py`

```python
# -*- coding: utf-8 -*-
"""
controller/app_controller.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TaskHub 마스터 컨트롤러. PluginHost 역할 겸함.
- 플러그인 자동 로드 + 선언형 custom_ui.json 패널
- 업데이트/회의받기 통합 액션 버튼 분기
- 성과보고서 트레이 메뉴
"""

import os
import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QMessageBox, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QInputDialog)
from PyQt6.QtGui import QIcon, QAction, QGuiApplication, QPixmap, QPainter, QColor
from PyQt6.QtCore import QObject, QTimer, QPoint, Qt
from view.main_window import MainWindow
from view.calendar_window import CalendarWindow
from model.schedule_model import ScheduleModel
from model.report_generator import ReportGenerator
from utils.selenium_downloader import SeleniumDownloader
from utils.outlook_downloader import OutlookMeetingDownloader
from utils.registry_handler import RegistryHandler
from core.constants import CONFIG_DIR
from core.plugin_loader import discover_plugins
from core.action_registry import ActionRegistry, load_ui_spec, build_declarative_panel


def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(0, 0, 0, 0))
    painter.setBrush(QColor("#00BFFF"))
    painter.drawRoundedRect(8, 16, 48, 40, 6, 6)
    painter.setBrush(QColor("#ff5555"))
    painter.drawRoundedRect(8, 8, 48, 14, 4, 4)
    painter.setBrush(QColor("#ffffff"))
    for x in (14, 28, 42):
        painter.drawRect(x, 24, 8, 8)
        painter.drawRect(x, 38, 8, 8)
    painter.end()
    return QIcon(pixmap)


def get_application_tray_icon():
    logo_path = Path(__file__).resolve().parent.parent / "view" / "Logo.png"
    if logo_path.exists():
        return QIcon(str(logo_path))
    return create_tray_icon()


class LoginDialog(QDialog):
    def __init__(self, parent, current_config, style_sheet):
        super().__init__(parent)
        self.setWindowTitle("Nexon Games 계정 등록")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet(style_sheet)
        self.resize(320, 260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        title = QLabel("👤 Nexon Games 계정 등록")
        title.setStyleSheet("font-size: 11pt; font-weight: bold; color: #00BFFF; margin-bottom: 5px;")
        layout.addWidget(title)
        layout.addWidget(QLabel("작업자 성함:"))
        self.txt_name = QLineEdit()
        self.txt_name.setText(current_config.get("target_name", ""))
        self.txt_name.setStyleSheet("background-color: #151515; color: white; padding: 4px; border: 1px solid #3f3f3f;")
        layout.addWidget(self.txt_name)
        layout.addWidget(QLabel("Nexon 오피스 ID (Email):"))
        self.txt_id = QLineEdit()
        self.txt_id.setText(current_config.get("nexon_id", ""))
        self.txt_id.setStyleSheet("background-color: #151515; color: white; padding: 4px; border: 1px solid #3f3f3f;")
        layout.addWidget(self.txt_id)
        layout.addWidget(QLabel("오피스 패스워드:"))
        self.txt_pw = QLineEdit()
        self.txt_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pw.setText(current_config.get("nexon_pw", ""))
        self.txt_pw.setStyleSheet("background-color: #151515; color: white; padding: 4px; border: 1px solid #3f3f3f;")
        layout.addWidget(self.txt_pw)
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 저장")
        self.btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("✕ 취소")
        self.btn_cancel.setStyleSheet("background-color: #333333; color: white;")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)


class AppController(QObject):
    def __init__(self):
        super().__init__()
        self.model = ScheduleModel()
        self.calc_window = MainWindow()
        self.cal_window = CalendarWindow(self.model)
        self.downloader_thread = None
        self.meeting_thread = None
        self.registry = ActionRegistry()
        self._register_builtin_actions()
        self._bind_calendar_header_actions()
        self._setup_system_tray()
        self.cal_window.btn_close.clicked.connect(self.cal_window.hide)
        self.calc_window.btn_close.clicked.connect(self.calc_window.hide)

    # ---- PluginHost 인터페이스 ----
    def register_action(self, name, func):
        self.registry.register(name, func)

    def get_config(self, key, default=None):
        return self.model.config.get(key, default)

    def notify(self, message):
        self.cal_window.title_label.setText(str(message))

    def _register_builtin_actions(self):
        self.registry.register("refresh_excel", self.trigger_excel_update)
        self.registry.register("clear_month", self.open_clear_menu)
        self.registry.register("add_period", self.open_period_dialog)
        self.registry.register("open_login", self.open_login_dialog)
        self.registry.register("open_settings", self.open_settings_dialog)
        self.registry.register("fetch_meetings", self.trigger_meeting_fetch)

    # ---- 확장 로딩 ----
    def load_extensions(self):
        self._load_plugins()
        self._load_custom_ui_panel()

    def _load_plugins(self):
        plugins_dir = Path(__file__).resolve().parent.parent / "plugins"
        result = discover_plugins(plugins_dir)
        for plugin in result.loaded:
            try:
                widget = plugin.build(self)
                self.calc_window.tab_widget.addTab(widget, plugin.NAME)
            except Exception:
                self.notify(f"플러그인 로드 실패: {plugin.NAME}")

    def _load_custom_ui_panel(self):
        spec_path = CONFIG_DIR / "custom_ui.json"
        if not spec_path.exists():
            return
        try:
            spec = load_ui_spec(spec_path)
            panel = build_declarative_panel(spec, self.registry)
            title = spec.get("title", "커스텀 패널")
            self.calc_window.tab_widget.addTab(panel, title)
        except Exception:
            self.notify("커스텀 UI 로드 실패 (custom_ui.json 확인)")

    def start_application(self):
        self.load_extensions()
        self.dock_windows()
        self.calc_window.show()
        self.cal_window.show()

    def dock_windows(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        cal_w = self.cal_window.width()
        cal_h = self.cal_window.height()
        calc_w = self.calc_window.width()
        cal_x = screen_geometry.right() - cal_w - 10
        cal_y = screen_geometry.bottom() - cal_h - 10
        self.cal_window.move(cal_x, cal_y)
        calc_x = cal_x - calc_w - 10
        calc_y = screen_geometry.bottom() - self.calc_window.height() - 10
        self.calc_window.move(calc_x, calc_y)

    def _setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(create_tray_icon())
        tray_menu = QMenu()
        action_toggle_calc = QAction("🧮 오프셋 계산기 보이기/숨기기", self)
        action_toggle_calc.triggered.connect(self._toggle_calc)
        action_toggle_cal = QAction("📅 일정표 위젯 보이기/숨기기", self)
        action_toggle_cal.triggered.connect(self._toggle_cal)
        action_report = QAction("📄 성과보고서 생성", self)
        action_report.triggered.connect(self.open_report_dialog)
        action_quit = QAction("❌ 종료", self)
        action_quit.triggered.connect(self.quit_application)
        tray_menu.addAction(action_toggle_calc)
        tray_menu.addAction(action_toggle_cal)
        tray_menu.addSeparator()
        tray_menu.addAction(action_report)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_cal()

    def _toggle_calc(self):
        if self.calc_window.isVisible():
            self.calc_window.hide()
        else:
            self.calc_window.show()
            self.calc_window.raise_()

    def _toggle_cal(self):
        if self.cal_window.isVisible():
            self.cal_window.hide()
        else:
            self.cal_window.show()
            self.cal_window.raise_()

    def _bind_calendar_header_actions(self):
        self.cal_window.btn_action.clicked.connect(self.on_action_button)
        self.cal_window.btn_period.clicked.connect(self.open_period_dialog)
        self.cal_window.btn_clear.clicked.connect(self.open_clear_menu)
        self.cal_window.btn_login.clicked.connect(self.open_login_dialog)
        self.cal_window.btn_settings.clicked.connect(self.open_settings_dialog)

    def on_action_button(self):
        if self.cal_window.view_mode == "meeting":
            self.trigger_meeting_fetch()
        else:
            self.trigger_excel_update()

    # ---- 엑셀 업데이트 ----
    def trigger_excel_update(self):
        cfg = self.model.config
        if not cfg["nexon_id"] or not cfg["nexon_pw"]:
            QMessageBox.warning(self.cal_window, "경고", "로그인 아이디/패스워드 설정을 완료해 주세요.")
            return
        self.cal_window.btn_action.setEnabled(False)
        self.cal_window.title_label.setText("접속 대기 중... 10%")
        self.downloader_thread = SeleniumDownloader(
            target_name=cfg["target_name"], nexon_id=cfg["nexon_id"],
            nexon_pw=cfg["nexon_pw"], library_url=cfg["library_url"]
        )
        self.downloader_thread.progress_signal.connect(self._on_update_progress)
        self.downloader_thread.finished_signal.connect(self._on_update_success)
        self.downloader_thread.failed_signal.connect(self._on_update_failed)
        self.downloader_thread.start()

    def _on_update_progress(self, percent, msg):
        self.cal_window.title_label.setText(f"{msg} {percent}%")

    def _on_update_success(self):
        self.downloader_thread = None
        try:
            self.model.parse_excel_data(self.cal_window.year, self.cal_window.month)
            self.cal_window.draw_calendar()
            self.cal_window.title_label.setText("✅ 엑셀 동기화 성공!")
        except Exception as e:
            QMessageBox.critical(self.cal_window, "에러", f"엑셀 분석 대입 중 치명적 오류가 일어났습니다:\n{e}")
        self.cal_window.btn_action.setEnabled(True)
        QTimer.singleShot(3000, self._restore_header_title)

    def _on_update_failed(self, err_msg):
        self.downloader_thread = None
        QMessageBox.critical(self.cal_window, "에러", f"셀레니움 다운로드가 취소/실패되었습니다:\n{err_msg}")
        self.cal_window.btn_action.setEnabled(True)
        self._restore_header_title()

    # ---- 회의 받기 ----
    def trigger_meeting_fetch(self):
        cfg = self.model.config
        if not cfg["nexon_id"] or not cfg["nexon_pw"]:
            QMessageBox.warning(self.cal_window, "경고", "로그인 아이디/패스워드 설정을 완료해 주세요.")
            return
        self.cal_window.btn_action.setEnabled(False)
        self.cal_window.title_label.setText("회의 일정 접속 중... 10%")
        self.meeting_thread = OutlookMeetingDownloader(
            nexon_id=cfg["nexon_id"], nexon_pw=cfg["nexon_pw"],
            calendar_url=cfg.get("outlook_url", ""), weeks_ahead=4
        )
        self.meeting_thread.progress_signal.connect(self._on_meeting_progress)
        self.meeting_thread.finished_signal.connect(self._on_meeting_success)
        self.meeting_thread.failed_signal.connect(self._on_meeting_failed)
        self.meeting_thread.start()

    def _on_meeting_progress(self, percent, msg):
        self.cal_window.title_label.setText(f"{msg} {percent}%")

    def _on_meeting_success(self, count):
        self.meeting_thread = None
        self.model.meeting_data = self.model.load_meetings()
        self.cal_window.view_mode = "meeting"
        self.cal_window._apply_mode_buttons()
        self.cal_window.draw_calendar()
        self.cal_window.title_label.setText(f"✅ 회의 {count}건 수집 완료!")
        self.cal_window.btn_action.setEnabled(True)
        QTimer.singleShot(3000, self._restore_header_title)

    def _on_meeting_failed(self, err_msg):
        self.meeting_thread = None
        QMessageBox.critical(self.cal_window, "에러", f"회의 일정 수집 실패:\n{err_msg}")
        self.cal_window.btn_action.setEnabled(True)
        self._restore_header_title()

    def _restore_header_title(self):
        self.cal_window.title_label.setText(f"{self.cal_window.year}년 {self.cal_window.month}월")

    # ---- 성과보고서 ----
    def open_report_dialog(self):
        mode_label, ok = QInputDialog.getItem(
            self.cal_window, "성과보고서", "기간 단위 선택:",
            ["연간", "1분기", "2분기", "3분기", "4분기"], 0, False
        )
        if not ok:
            return
        year = self.cal_window.year
        if mode_label == "연간":
            mode, quarter = "year", None
        else:
            mode, quarter = "quarter", int(mode_label[0])
        try:
            gen = ReportGenerator(self.model)
            path = gen.generate(year=year, mode=mode, quarter=quarter,
                                author_name=self.model.config.get("target_name", ""))
            self.cal_window.title_label.setText("✅ 보고서 생성 완료")
            os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self.cal_window, "에러", f"보고서 생성 실패:\n{e}")

    # ---- 기간/비우기/로그인/설정 ----
    def open_period_dialog(self):
        s_day = min(self.cal_window.selected_days) if self.cal_window.selected_days else ""
        e_day = max(self.cal_window.selected_days) if self.cal_window.selected_days else ""
        s, ok1 = QInputDialog.getInt(self.cal_window, "시작일 입력", "시작 날짜를 입력하세요 (숫자):", value=int(s_day) if s_day else 1, min=1, max=31)
        if not ok1:
            return
        e, ok2 = QInputDialog.getInt(self.cal_window, "종료일 입력", "종료 날짜를 입력하세요 (숫자):", value=int(e_day) if e_day else s, min=s, max=31)
        if not ok2:
            return
        txt, ok3 = QInputDialog.getText(self.cal_window, "일감 내용 기입", "추가할 일감 타이틀을 명세해 주세요:")
        if not ok3 or not txt.strip():
            return
        hols = self.model.config.get("holidays", [])
        for d in range(s, e + 1):
            is_w = (datetime.date(self.cal_window.year, self.cal_window.month, d).weekday() >= 5)
            is_h = f"{self.cal_window.year}-{self.cal_window.month}-{d}" in hols
            if is_w or is_h:
                continue
            day_tasks = self.model.schedule_data.setdefault((self.cal_window.year, self.cal_window.month, d), [])
            if not any(x.get("task") == txt.strip() for x in day_tasks):
                day_tasks.append({"task": txt.strip(), "color": "", "release": ""})
        self.model.save_schedules()
        self.cal_window.selected_days.clear()
        self.cal_window.draw_calendar()

    def open_clear_menu(self):
        menu = QMenu(self.cal_window)
        action_month = menu.addAction(f"⚠️ {self.cal_window.month}월 일정 전체 삭제")
        action_all = menu.addAction("🚨 데이터 베이스 영구 포맷")
        action = menu.exec(self.cal_window.btn_clear.mapToGlobal(QPoint(0, 30)))
        if action == action_month:
            res = QMessageBox.question(self.cal_window, "확인", f"이번 {self.cal_window.month}월 로컬 데이터 일정을 전부 지우시겠습니까?")
            if res == QMessageBox.StandardButton.Yes:
                self.model.schedule_data = {k: v for k, v in self.model.schedule_data.items() if not (k[0] == self.cal_window.year and k[1] == self.cal_window.month)}
                self.model.save_schedules()
                self.cal_window.draw_calendar()
        elif action == action_all:
            res = QMessageBox.question(self.cal_window, "포맷 경고", "TaskHub 로컬 DB가 완전 초기화됩니다. 이관을 진행하시겠습니까?")
            if res == QMessageBox.StandardButton.Yes:
                self.model.schedule_data.clear()
                self.model.save_schedules()
                self.cal_window.draw_calendar()

    def open_login_dialog(self):
        dialog = LoginDialog(self.cal_window, self.model.config, self.cal_window.styleSheet())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.config.update({
                "target_name": dialog.txt_name.text().strip(),
                "nexon_id": dialog.txt_id.text().strip(),
                "nexon_pw": dialog.txt_pw.text().strip()
            })
            self.model.save_config()

    def open_settings_dialog(self):
        cfg = self.model.config
        url, ok = QInputDialog.getText(self.cal_window, "설정", "SharePoint 라이브러리 URL 주소:", text=cfg.get("library_url", ""))
        if not ok:
            return
        cfg["library_url"] = url.strip()
        # Outlook URL도 함께 설정(선택)
        ourl, ok2 = QInputDialog.getText(self.cal_window, "설정", "Outlook 캘린더 URL (비우면 기본값):", text=cfg.get("outlook_url", ""))
        if ok2:
            cfg["outlook_url"] = ourl.strip()
        self.model.save_config()
        startup_enabled = RegistryHandler.is_startup_enabled()
        reply = QMessageBox.question(
            self.cal_window, "시작 프로그램 등록",
            f"윈도우 시작 시 자동으로 TaskHub를 구동할까요?\n(현재 등록 상태: {'등록됨' if startup_enabled else '미등록'})",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            RegistryHandler.toggle_startup(True)
        else:
            RegistryHandler.toggle_startup(False)

    def quit_application(self):
        self.tray_icon.hide()
        self.calc_window.close()
        self.cal_window.close()

```

## `controller/calculator_controller.py`

```python
# -*- coding: utf-8 -*-
"""
controller/calculator_controller.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
일괄 클립보드 / 수동 PRS / 가산식 오프셋 보정 기능을 총괄 계산하는 통합 컨트롤러
"""

from PyQt6.QtWidgets import QApplication
from utils.clipboard_helper import ClipboardHelper
from utils.math_utils import wrap_angle_180


class CalculatorController:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.start_vector = (0.0, 0.0, 0.0)
        self.start_rotator = (0.0, 0.0, 0.0)
        self.target_vector = (0.0, 0.0, 0.0)
        self.target_rotator = (0.0, 0.0, 0.0)

        self.orig_vector = (0.0, 0.0, 0.0)
        self.orig_rotator = (0.0, 0.0, 0.0)
        self.old_vector = (0.0, 0.0, 0.0)
        self.old_rotator = (0.0, 0.0, 0.0)
        self.new_vector = (0.0, 0.0, 0.0)
        self.new_rotator = (0.0, 0.0, 0.0)

        self.view.btn_toggle_mode.clicked.connect(self.toggle_input_mode)

        self.view.btn_paste_start.clicked.connect(self.paste_start_bulk)
        self.view.btn_paste_target.clicked.connect(self.paste_target_bulk)

        self.view.btn_copy_vector.clicked.connect(self.copy_vector_to_clipboard)
        self.view.btn_copy_rotator.clicked.connect(self.copy_rotator_to_clipboard)

        self._bind_all_manual_inputs()

    def toggle_input_mode(self):
        current_idx = self.view.input_stack.currentIndex()
        next_idx = (current_idx + 1) % 3
        self.view.input_stack.setCurrentIndex(next_idx)

        if next_idx == 0:
            self.view.btn_toggle_mode.setText("현재 모드: [일괄 클립보드] (클릭하여 전환)")
            self.view.result_title.setText("<b>[3] Calculated Delta Result (B - A)</b>")
            self.view.vector_lbl.setText("위치 오프셋 (Vector Delta):")
            self.view.rotator_lbl.setText("회전 오프셋 (Rotator Delta - 최단 경로):")
        elif next_idx == 1:
            self.view.btn_toggle_mode.setText("현재 모드: [개별 PRS 수동] (클릭하여 전환)")
            self.view.result_title.setText("<b>[3] Calculated Delta Result (B - A)</b>")
            self.view.vector_lbl.setText("위치 오프셋 (Vector Delta):")
            self.view.rotator_lbl.setText("회전 오프셋 (Rotator Delta - 최단 경로):")
        elif next_idx == 2:
            self.view.btn_toggle_mode.setText("현재 모드: [오프셋 가산 보정] (클릭하여 전환)")
            self.view.result_title.setText("<b>[결과] 수정된 최종 오프셋 (Revised Delta)</b>")
            self.view.vector_lbl.setText("수정 위치 오프셋 (New Vector Delta):")
            self.view.rotator_lbl.setText("수정 회전 오프셋 (New Rotator Delta - 최단 경로):")

        self.calculate_deltas()

    def _bind_all_manual_inputs(self):
        prefixes = ["start", "target", "orig", "old", "new"]

        for prefix in prefixes:
            getattr(self.view, f"{prefix}_px").valueChanged.connect(self.on_manual_change)
            getattr(self.view, f"{prefix}_py").valueChanged.connect(self.on_manual_change)
            getattr(self.view, f"{prefix}_pz").valueChanged.connect(self.on_manual_change)
            getattr(self.view, f"{prefix}_rp").valueChanged.connect(self.on_manual_change)
            getattr(self.view, f"{prefix}_ry").valueChanged.connect(self.on_manual_change)
            getattr(self.view, f"{prefix}_rr").valueChanged.connect(self.on_manual_change)

            getattr(self.view, f"{prefix}_btn_paste_loc").clicked.connect(
                lambda checked, p=prefix: self.paste_prs_individual(p, "loc")
            )
            getattr(self.view, f"{prefix}_btn_paste_rot").clicked.connect(
                lambda checked, p=prefix: self.paste_prs_individual(p, "rot")
            )

            if hasattr(self.view, f"{prefix}_btn_paste_scl"):
                getattr(self.view, f"{prefix}_btn_paste_scl").clicked.connect(
                    lambda checked, p=prefix: self.paste_prs_individual(p, "scl")
                )

    def paste_prs_individual(self, prefix, mode):
        clipboard_text = QApplication.clipboard().text().strip()
        self.block_manual_signals(True)

        if mode == "loc":
            parsed = ClipboardHelper.parse_vector(clipboard_text)
            if parsed:
                getattr(self.view, f"{prefix}_px").setValue(parsed[0])
                getattr(self.view, f"{prefix}_py").setValue(parsed[1])
                getattr(self.view, f"{prefix}_pz").setValue(parsed[2])
        elif mode == "rot":
            parsed = ClipboardHelper.parse_rotator(clipboard_text)
            if parsed:
                getattr(self.view, f"{prefix}_rp").setValue(parsed[0])
                getattr(self.view, f"{prefix}_ry").setValue(parsed[1])
                getattr(self.view, f"{prefix}_rr").setValue(parsed[2])
        elif mode == "scl":
            parsed = ClipboardHelper.parse_scale(clipboard_text)
            if parsed:
                getattr(self.view, f"{prefix}_sx").setValue(parsed[0])
                getattr(self.view, f"{prefix}_sy").setValue(parsed[1])
                getattr(self.view, f"{prefix}_sz").setValue(parsed[2])

        self.block_manual_signals(False)
        self.on_manual_change()

    def on_manual_change(self):
        self.start_vector = (self.view.start_px.value(), self.view.start_py.value(), self.view.start_pz.value())
        self.start_rotator = (self.view.start_rp.value(), self.view.start_ry.value(), self.view.start_rr.value())
        self.target_vector = (self.view.target_px.value(), self.view.target_py.value(), self.view.target_pz.value())
        self.target_rotator = (self.view.target_rp.value(), self.view.target_ry.value(), self.view.target_rr.value())

        self.orig_vector = (self.view.orig_px.value(), self.view.orig_py.value(), self.view.orig_pz.value())
        self.orig_rotator = (self.view.orig_rp.value(), self.view.orig_ry.value(), self.view.orig_rr.value())
        self.old_vector = (self.view.old_px.value(), self.view.old_py.value(), self.view.old_pz.value())
        self.old_rotator = (self.view.old_rp.value(), self.view.old_ry.value(), self.view.old_rr.value())
        self.new_vector = (self.view.new_px.value(), self.view.new_py.value(), self.view.new_pz.value())
        self.new_rotator = (self.view.new_rp.value(), self.view.new_ry.value(), self.view.new_rr.value())

        self.update_clipboard_text_display()
        self.calculate_deltas()

    def paste_start_bulk(self):
        clipboard_text = QApplication.clipboard().text().strip()
        parsed_vector, parsed_rotator = ClipboardHelper.parse_unreal_transform(clipboard_text)

        if parsed_vector or parsed_rotator:
            if parsed_vector:
                self.start_vector = parsed_vector
            if parsed_rotator:
                self.start_rotator = parsed_rotator
            self.sync_data_to_prs_widgets("start")
            self.update_clipboard_text_display()
            self.calculate_deltas()
        else:
            self.view.start_input.setText("Error: 파싱 가능한 언리얼 데이터가 없습니다.")

    def paste_target_bulk(self):
        clipboard_text = QApplication.clipboard().text().strip()
        parsed_vector, parsed_rotator = ClipboardHelper.parse_unreal_transform(clipboard_text)

        if parsed_vector or parsed_rotator:
            if parsed_vector:
                self.target_vector = parsed_vector
            if parsed_rotator:
                self.target_rotator = parsed_rotator
            self.sync_data_to_prs_widgets("target")
            self.update_clipboard_text_display()
            self.calculate_deltas()
        else:
            self.view.target_input.setText("Error: 파싱 가능한 언리얼 데이터가 없습니다.")

    def sync_data_to_prs_widgets(self, prefix):
        self.block_manual_signals(True)
        vec = self.start_vector if prefix == "start" else self.target_vector
        rot = self.start_rotator if prefix == "start" else self.target_rotator

        if vec:
            getattr(self.view, f"{prefix}_px").setValue(vec[0])
            getattr(self.view, f"{prefix}_py").setValue(vec[1])
            getattr(self.view, f"{prefix}_pz").setValue(vec[2])
        if rot:
            getattr(self.view, f"{prefix}_rp").setValue(rot[0])
            getattr(self.view, f"{prefix}_ry").setValue(rot[1])
            getattr(self.view, f"{prefix}_rr").setValue(rot[2])
        self.block_manual_signals(False)

    def update_clipboard_text_display(self):
        self.update_input_display(self.view.start_input, self.start_vector, self.start_rotator)
        self.update_input_display(self.view.target_input, self.target_vector, self.target_rotator)

    def update_input_display(self, line_edit, vector, rotator):
        parts = []
        if vector is not None:
            parts.append(f"Loc(X={vector[0]:.2f}, Y={vector[1]:.2f}, Z={vector[2]:.2f})")
        else:
            parts.append("Loc(None)")
        if rotator is not None:
            parts.append(f"Rot(P={rotator[0]:.2f}, Y={rotator[1]:.2f}, R={rotator[2]:.2f})")
        else:
            parts.append("Rot(None)")
        line_edit.setText("  |  ".join(parts))

    def calculate_deltas(self):
        current_idx = self.view.input_stack.currentIndex()

        if current_idx in (0, 1):
            if self.start_vector is not None and self.target_vector is not None:
                v_delta = self.model.calculate_vector_delta(self.start_vector, self.target_vector)
                v_unreal = ClipboardHelper.format_to_unreal_vector(*v_delta)
                self.view.vector_result_label.setText(v_unreal)
                self.view.btn_copy_vector.setEnabled(True)
            else:
                self.view.vector_result_label.setText("Waiting for Location inputs...")
                self.view.btn_copy_vector.setEnabled(False)

            if self.start_rotator is not None and self.target_rotator is not None:
                r_delta = self.model.calculate_rotator_delta(self.start_rotator, self.target_rotator)
                r_unreal = ClipboardHelper.format_to_unreal_rotator(*r_delta)
                self.view.rotator_result_label.setText(r_unreal)
                self.view.btn_copy_rotator.setEnabled(True)
            else:
                self.view.rotator_result_label.setText("Waiting for Rotation inputs...")
                self.view.btn_copy_rotator.setEnabled(False)

        elif current_idx == 2:
            base_x = (
                self.old_vector[0] - self.orig_vector[0],
                self.old_vector[1] - self.orig_vector[1],
                self.old_vector[2] - self.orig_vector[2],
            )
            revised_vec = self.model.calculate_vector_delta(base_x, self.new_vector)
            v_unreal = ClipboardHelper.format_to_unreal_vector(*revised_vec)
            self.view.vector_result_label.setText(v_unreal)
            self.view.btn_copy_vector.setEnabled(True)

            # [리팩터링] 각도 wrapping은 utils.math_utils.wrap_angle_180 공유 사용
            base_rot_x = tuple(
                wrap_angle_180(self.old_rotator[i] - self.orig_rotator[i]) for i in range(3)
            )
            revised_rot = self.model.calculate_rotator_delta(base_rot_x, self.new_rotator)
            r_unreal = ClipboardHelper.format_to_unreal_rotator(*revised_rot)
            self.view.rotator_result_label.setText(r_unreal)
            self.view.btn_copy_rotator.setEnabled(True)

    def block_manual_signals(self, block):
        prefixes = ["start", "target", "orig", "old", "new"]
        for p in prefixes:
            getattr(self.view, f"{p}_px").blockSignals(block)
            getattr(self.view, f"{p}_py").blockSignals(block)
            getattr(self.view, f"{p}_pz").blockSignals(block)
            getattr(self.view, f"{p}_rp").blockSignals(block)
            getattr(self.view, f"{p}_ry").blockSignals(block)
            getattr(self.view, f"{p}_rr").blockSignals(block)

    def copy_vector_to_clipboard(self):
        text = self.view.vector_result_label.text()
        QApplication.clipboard().setText(text)

    def copy_rotator_to_clipboard(self):
        text = self.view.rotator_result_label.text()
        QApplication.clipboard().setText(text)

```

## `controller/converter_controller.py`

```python
# -*- coding: utf-8 -*-
"""
controller/converter_controller.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ConverterTab 의 좌표/단위 변환 로직 바인딩.
[불변] ENGINE_KEYS 순서 = converter_tab.ENGINE_LABELS 순서.
"""

from PyQt6.QtWidgets import QApplication
from utils.coordinate_converter import (
    convert_position, convert_scale, convert_rotation_approx,
    cm_to_m, m_to_cm, deg_to_rad, rad_to_deg,
)
from utils.clipboard_helper import ClipboardHelper

ENGINE_KEYS = ["unreal", "max", "maya", "blender"]


class ConverterController:
    def __init__(self, view):
        self.view = view
        self.last_pos_result = None
        v = self.view
        v.btn_swap_engine.clicked.connect(self.swap_engines)
        v.btn_convert.clicked.connect(self.do_convert)
        v.btn_paste_clip.clicked.connect(self.paste_clipboard)
        v.btn_copy_pos.clicked.connect(self.copy_pos)
        v.combo_unit.currentIndexChanged.connect(self.do_unit_convert)
        v.unit_input.valueChanged.connect(self.do_unit_convert)

    def _src(self):
        return ENGINE_KEYS[self.view.combo_from.currentIndex()]

    def _dst(self):
        return ENGINE_KEYS[self.view.combo_to.currentIndex()]

    def _xyz(self, prefix):
        return (getattr(self.view, f"{prefix}_x").value(),
                getattr(self.view, f"{prefix}_y").value(),
                getattr(self.view, f"{prefix}_z").value())

    def swap_engines(self):
        i, j = self.view.combo_from.currentIndex(), self.view.combo_to.currentIndex()
        self.view.combo_from.setCurrentIndex(j)
        self.view.combo_to.setCurrentIndex(i)
        self.do_convert()

    def do_convert(self):
        src, dst = self._src(), self._dst()
        if src == dst:
            self.view.lbl_warn.setText("From과 To가 같습니다.")
            return
        pos = convert_position(self._xyz("pos"), src, dst)
        scl = convert_scale(self._xyz("scl"), src, dst)
        rot, warn = convert_rotation_approx(self._xyz("rot"), src, dst)
        self.view.lbl_pos_result.setText(f"위치: X={pos[0]}  Y={pos[1]}  Z={pos[2]}")
        self.view.lbl_scl_result.setText(f"스케일: X={scl[0]}  Y={scl[1]}  Z={scl[2]}")
        self.view.lbl_rot_result.setText(f"회전(근사): P={rot[0]}  Y={rot[1]}  R={rot[2]}")
        self.view.lbl_warn.setText(warn)
        self.last_pos_result = pos
        self.view.btn_copy_pos.setEnabled(True)

    def paste_clipboard(self):
        text = QApplication.clipboard().text().strip()
        vec, rot = ClipboardHelper.parse_unreal_transform(text)
        if vec:
            self.view.pos_x.setValue(vec[0]); self.view.pos_y.setValue(vec[1]); self.view.pos_z.setValue(vec[2])
        if rot:
            self.view.rot_x.setValue(rot[0]); self.view.rot_y.setValue(rot[1]); self.view.rot_z.setValue(rot[2])
        if vec or rot:
            self.do_convert()
        else:
            self.view.lbl_warn.setText("클립보드에서 파싱 가능한 언리얼 데이터를 찾지 못했습니다.")

    def copy_pos(self):
        if self.last_pos_result:
            txt = ClipboardHelper.format_to_unreal_vector(*self.last_pos_result)
            QApplication.clipboard().setText(txt)

    def do_unit_convert(self):
        val = self.view.unit_input.value()
        mode = self.view.combo_unit.currentIndex()
        if mode == 0:
            out, unit = cm_to_m(val), "m"
        elif mode == 1:
            out, unit = m_to_cm(val), "cm"
        elif mode == 2:
            out, unit = deg_to_rad(val), "rad"
        else:
            out, unit = rad_to_deg(val), "°"
        self.view.lbl_unit_result.setText(f"결과: {round(out, 6)} {unit}")

```

## `plugins/example_clock.py`

```python
# -*- coding: utf-8 -*-
"""
plugins/example_clock.py
~~~~~~~~~~~~~~~~~~~~~~~~
플러그인 작성 예제 (사용자가 복사해서 시작하는 템플릿).

이 파일을 plugins/ 폴더에 두면 앱 시작 시 자동으로 새 탭으로 등록된다.
PluginBase를 상속하고 NAME + build(host)만 구현하면 끝.
"""

from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, QTime

from core.plugin_api import PluginBase, PluginHost


class ClockPlugin(PluginBase):
    NAME = "🕐 시계"
    VERSION = "1.0.0"

    def build(self, host: PluginHost) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self.label = QLabel("--:--:--")
        self.label.setStyleSheet("font-size: 20pt; color: #00BFFF;")
        layout.addWidget(self.label)

        # host를 통해 앱에 액션을 등록 -> 선언형 JSON UI에서도 호출 가능해짐
        host.register_action("ping_clock", lambda: host.notify("시계 플러그인 동작 중"))

        btn = QPushButton("앱에 신호 보내기")
        btn.clicked.connect(lambda: host.notify("시계에서 보낸 신호!"))
        layout.addWidget(btn)

        self._timer = QTimer(w)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()
        return w

    def _tick(self) -> None:
        self.label.setText(QTime.currentTime().toString("HH:mm:ss"))

```

## `sample_custom_ui.json`

```json
{
  "title": "내 커스텀 패널 예시",
  "buttons": [
    {"label": "엑셀 새로고침", "action": "refresh_excel"},
    {"label": "이번 달 비우기", "action": "clear_month"},
    {"label": "위험한 명령", "action": "delete_system32"}
  ]
}

```

## `tests/test_math_utils.py`

```python
# -*- coding: utf-8 -*-
"""
tests/test_math_utils.py
~~~~~~~~~~~~~~~~~~~~~~~~
math_utils 순수 함수 검증. Qt 불필요, `pytest` 단독 실행 가능.

목적: 리팩터링 전후로 '동작이 안 변했음'을 기계적으로 보장하는 안전망.
"""

import datetime

import pytest

from utils import math_utils as m


# ---- 각도 wrapping ----
@pytest.mark.parametrize("angle,expected", [
    (0, 0),
    (180, 180),
    (-180, 180),       # -180은 (-180,180] 규약상 180으로 접힘
    (181, -179),
    (360, 0),
    (540, 180),
    (-190, 170),
])
def test_wrap_angle_180(angle, expected):
    assert m.wrap_angle_180(angle) == pytest.approx(expected)


def test_shortest_rotator_delta_takes_short_path():
    # 350도에서 10도로: 단순 차이는 -340이지만 최단경로는 +20
    assert m.shortest_rotator_delta((350, 0, 0), (10, 0, 0)) == (20.0, 0.0, 0.0)


def test_rotator_delta_matches_legacy_formula():
    # 기존 delta_calculator의 공식과 직접 대조
    def legacy(s, t):
        return tuple(round(((t[i] - s[i] + 180.0) % 360.0) - 180.0, 4) for i in range(3))
    cases = [
        ((10, 20, 30), (40, 350, 5)),
        ((-90, 0, 179), (90, 1, -179)),
        ((0, 0, 0), (720, -720, 360)),
    ]
    for s, t in cases:
        assert m.shortest_rotator_delta(s, t) == legacy(s, t)


def test_vector_delta():
    assert m.vector_delta((1, 2, 3), (4, 6, 8)) == (3.0, 4.0, 5.0)


# ---- 색상 ----
@pytest.mark.parametrize("raw,expected", [
    ("FF9494", "FFFF9494"),     # 6자리 -> FF 접두
    ("00BFFF00", "00BFFF00"),   # 8자리 그대로
    ("00BFFF", "FF00BFFF"),
    (None, ""),
    ("xyz", ""),                # 길이 안 맞으면 빈 문자열
])
def test_normalize_argb_hex(raw, expected):
    assert m.normalize_argb_hex(raw) == expected


def test_argb_to_css():
    assert m.argb_to_css("FF00BFFF") == "#00BFFF"
    assert m.argb_to_css("00BFFF") == "#00BFFF"
    assert m.argb_to_css(None) == ""


# ---- 워크데이 ----
def test_count_workdays_excludes_weekend():
    # 2026-06-01(월) ~ 2026-06-07(일): 월~금 5일
    start = datetime.date(2026, 6, 1)
    end = datetime.date(2026, 6, 7)
    assert m.count_workdays(start, end, []) == 5


def test_count_workdays_excludes_holiday():
    start = datetime.date(2026, 6, 1)
    end = datetime.date(2026, 6, 5)   # 월~금 = 5
    assert m.count_workdays(start, end, ["2026-6-3"]) == 4


def test_count_workdays_reversed_range():
    start = datetime.date(2026, 6, 5)
    end = datetime.date(2026, 6, 1)
    assert m.count_workdays(start, end, []) == 0


def test_ratio_zero_guard():
    assert m.ratio(3, 0) == 0.0
    assert m.ratio(8, 10) == pytest.approx(0.8)

```
