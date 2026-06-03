# Widget_Manager — 구현 지시 (1차: 코어 v0.1)

## 이게 뭔가
범용 일감관리 데스크톱 위젯. PyQt6. 바탕화면 상주.
기존 `TaskHub`(같은 폴더의 `TaskHub_완전판_v2_소스포함.md`에 전체 소스 있음)를 **참고/부분 이식**하되, 캘린더·UI는 새 설계로 깨끗하게 새로 짠다.

**작업자 프로필**: 차승현(Nexon Games 3D TA). Python·PyQt 강함, C++ 약함. 한국어 주석 충분히. 한꺼번에 다 받기보다 단계별 검증 선호. 모바일에서 볼 때가 많으니 파일 수정 시 가능하면 전체본 제공.

**개발 환경**: Python 3.11, PyQt6. 작업 폴더 `D:\Projects\Widget_Manager` (GitHub: ohCHA-TechAnim/Widget_Manager, 현재 빈 저장소).

---

## 핵심 설계 원칙 (이게 전부다)

### 1. 데이터 하나, 보기 셋
일감 데이터는 한 곳(`core/task_store.py`)에 저장. 월/리스트/칸반 뷰는 **같은 데이터를 다르게 그리기만** 한다. 어느 뷰에서 수정해도 즉시 모든 뷰에 반영.

### 2. "파싱 없이도 완벽 작동"이 토대
손으로 일감을 추가/수정/삭제하는 것만으로 완전한 일정 관리가 되어야 한다. 외부 문서 파싱(SharePoint 등)은 **이 토대 위에 얹는 선택적 애드온**이지 필수가 아니다. v0.1에는 파싱을 넣지 않는다 (코어만).

### 3. 코어 + 애드온 분리
- **코어**(이 저장소): 캘린더·멀티뷰·테마·꾸미기·손입력 일감관리·순수유틸. 그 자체로 완결. 넥슨/회사 흔적 0.
- **애드온**(나중에 별도): 넥슨 SharePoint 가져오기 등. 코어가 `plugins/` 폴더를 스캔해 있으면 메뉴에 추가, 없으면 그냥 없는 채로 완벽 작동.
- 애드온 메커니즘은 TaskHub의 검증된 `plugin_loader.py`(실패 격리 로더) 구조를 재사용.
- 일감 데이터에 `source: "manual"|"<addon-id>"` 필드 — 출처 구분. 가져온 항목은 읽기전용 처리 가능하게.
- **회의(Outlook) 기능은 v0.1에서 제외** (사용자 결정).

---

## 일감 데이터 구조 (확정)
```python
{
  "id":        str,            # 고유 ID (uuid)
  "title":     str,            # 제목
  "start":     "YYYY-MM-DD",   # 시작일
  "end":       "YYYY-MM-DD",   # 마감일 (당일이면 start==end)
  "status":    "todo"|"doing"|"done",
  "priority":  "high"|"mid"|"low",
  "memo":      str,            # 메모/설명 (여러 줄)
  "color":     "#RRGGBB",      # 표시 색
  "jiras":     [{"name": str, "path": str}, ...],   # 지라 링크 (TaskHub 자산)
  "folders":   [{"name": str, "path": str}, ...],   # 폴더 링크 (TaskHub 자산)
  "attachments": [절대경로str, ...],                 # 이미지/영상
  "source":    "manual",       # 출처 (애드온이 넣으면 애드온 id)
  "deco_image": 절대경로str|null  # 칸별 꾸미기 이미지 (선택)
}
```
저장: `<AppData>/Widget_Manager/data/tasks.json` (JSON). 설정은 `settings.json`.

---

## 기능 명세 (v0.1)

### A. 멀티뷰 (월/리스트/칸반 토글)
- **월 캘린더**: 7열 격자. 기간 일감은 시작~마감 칸에 막대로 이어짐. 칸 넘치면 "+N". 캘린더 크기 기준 920×640 참고(TaskHub 황금값), 단 리사이즈 대응.
- **리스트**: 일감을 행으로. 정렬(마감일/우선순위/상태). 좌측 색 띠 + 상태/우선순위 표시.
- **칸반**: 할일/진행/완료 3컬럼. 카드 **드래그&드롭으로 상태 변경**(QListWidget 또는 커스텀 드롭). 드롭하면 task_store의 status 갱신 → 다른 뷰도 반영.

### B. 일감 편집
- 새 일감/수정 다이얼로그: 위 데이터 구조 필드 입력. 색은 QColorDialog. 첨부는 파일 선택. 지라/폴더는 이름+경로 쌍 추가/삭제.
- 월 뷰 칸 더블클릭 → 그 날짜로 새 일감. 기존 일감 클릭 → 상세/편집.

### C. 테마 시스템
- 라이트/다크 **기본 제공**. 토글 버튼 + 설정에서 선택. QSS를 런타임 교체(스타일 두 벌).
- **커스텀 포인트색**: 설정창에서 프리셋 몇 개 + QColorDialog로 직접 지정. 선택 색이 강조 요소(버튼/선택표시/오늘)에 즉시 반영. settings.json에 저장.

### D. 꾸미기
- **배경**: 캘린더 전체 배경에 이미지/GIF. QLabel + QMovie(GIF 애니), 가독성 위해 반투명 오버레이. 없음/이미지/GIF 선택. 끄기 가능.
- **칸별 이미지**: 특정 날짜 칸 우클릭 → 이미지 첨부(`deco_image`). 칸 배경 썸네일.

### E. 순수 유틸 이식 (TaskHub 문서에서)
`TaskHub_완전판_v2_소스포함.md`에서 아래를 가져와 `utils/`에 배치. **Qt 비의존 순수 로직이라 거의 그대로 이식 가능.** 이식 후 기존 테스트(`test_math_utils.py`)도 같이 가져와 통과 확인:
- `math_utils.py` — wrap_angle_180, shortest_rotator_delta, vector_delta, normalize_argb_hex, argb_to_css, count_workdays, ratio
- `coordinate_converter.py` — DCC 좌표/단위 변환 (Unreal/Maya/Max/Blender). **회전은 근사치+경고 그대로 유지**(문서 3-6 참조).
- `report_generator.py` — 분기/연간 성과보고서(python-docx). 새 데이터 구조에 맞게 필드 매핑 조정.
- (이 세 기능은 코어 탭/메뉴로 노출. 좌표변환 탭, 보고서 생성 메뉴.)

### F. 트레이 / 상주
- ✕ = 종료 아닌 트레이 숨김(TaskHub 철학 유지). 트레이 메뉴: 열기/보고서생성/설정/종료.
- print() 금지 — `logging`으로 `<AppData>/Widget_Manager/logs/`에 기록(PyInstaller --windowed 크래시 방지, 문서 0-7 참조).

---

## 권장 폴더 구조
```
Widget_Manager/
├── main.py
├── requirements.txt          # PyQt6, python-docx (selenium은 애드온에서)
├── core/
│   ├── task_store.py         # 일감 저장/로드/CRUD + 변경 통지(뷰 갱신)
│   ├── plugin_loader.py      # 애드온 스캔/격리 로드 (TaskHub 재사용)
│   ├── plugin_api.py         # PluginBase + Host 인터페이스
│   └── settings.py           # 테마/색/꾸미기 설정 저장
├── views/
│   ├── month_view.py
│   ├── list_view.py
│   ├── kanban_view.py
│   └── task_dialog.py        # 일감 편집 다이얼로그
├── utils/
│   ├── math_utils.py         # 이식
│   ├── coordinate_converter.py  # 이식
│   └── report_generator.py   # 이식
├── theme/
│   ├── light.qss
│   ├── dark.qss
│   └── theme_manager.py      # 런타임 교체 + 커스텀색 주입
├── plugins/                  # 애드온 폴더 (비어있어도 됨)
│   └── __init__.py
└── tests/
    └── test_math_utils.py    # 이식 (이식 검증)
```

---

## 작업 순서 (단계별, 각 단계 검증)
1. 폴더 골격 + `requirements.txt` + main.py 빈 창 띄우기 (PyQt6 설치 확인)
2. `task_store.py` + 일감 데이터 구조 + JSON 저장/로드. Qt 없이 단독 테스트.
3. **월 뷰** 먼저 — 손으로 일감 추가/표시되는 것까지. (가장 핵심)
4. 일감 편집 다이얼로그
5. 리스트 뷰 → 칸반 뷰(드래그&드롭) → 뷰 토글
6. 테마(라이트/다크) + 커스텀 색
7. 꾸미기(배경/칸별)
8. 순수 유틸 이식(math_utils → 테스트 통과 → coordinate_converter → report_generator) + 탭/메뉴 연결
9. 트레이 상주 + 로깅
10. git commit & push (단계별로 커밋 권장)

**플랜 모드로 시작.** 1~2단계까지 만들고 한 번 멈춰서 사용자에게 "여기까지 돌아간다" 확인받은 뒤 진행. 한꺼번에 다 만들지 말 것 (사용자 선호 + UI 복잡도 민감).

## 주의 (TaskHub 문서 0번 교훈)
- 들여쓰기/변수 정의 순서 실수가 과거 사고 → 코드 줄 때 점검.
- UI 복잡도 민감 — 헤더 버튼 무더기 금지. 자주 안 쓰는 건 트레이/설정으로.
- 순수 로직은 Qt 없이 단독 테스트 먼저.
- print 금지(로깅).

## 끝나고
- 단계별 무엇을 만들었는지 한국어로 요약.
- v0.1이 "파싱 없이 손으로 일감 관리"가 완전히 되는지 확인.
- 다음 단계(애드온, 배포 자동화)는 별도 지시 예정 — 지금은 코어만.
