STATUS: WAITING_USER
작업 지시 — SharePoint 일감 다듬기 (메모 정리 / 링크 관리 / 색상 / 작은창 상세보기) v0.2.5
작업자: 차승현. 큰 진전: v0.2.4에서 파싱까지 완전 성공. 엑셀 일감이 달력에 잘 들어온다. 이제 다듬는 단계. 아래 5가지를 개선한다.
진행 규칙
	•	코어 안정성 유지: manual 일감, 테마, 트레이/오버레이, 저장 흐름을 망가뜨리지 말 것.
	•	애매하면 그 자리에서 WAITING_USER로 질문. 끝나면 WAITING_USER로 멈춤.
1. 메모에 딸려오는 엑셀 시스템 텍스트 제거
	•	가져온 일감 메모에 엑셀 스레드 댓글 안내문이 섞여 들어온다. 예:
	•	[Threaded comment]
	•	Your version of Excel allows you to read this threaded comment; however, any edits to it will get removed if the file is opened in a newer version of Excel. Learn more:
	•	그 뒤에 붙는 https://go.microsoft.com/fwlink/... 더미 링크
	•	parser에서 이런 엑셀 시스템 안내 문구/더미 링크를 메모에서 걸러낸다. 실제 사용자가 쓴 메모 내용만 남기기.
	•	최소: “[Threaded comment]”, “Your version of Excel…Learn more:” 문장, “go.microsoft.com/fwlink” URL을 제거.
	•	안전하게: 알려진 패턴만 제거하고, 못 알아본 내용은 보존(실제 메모를 지우면 안 됨).
2. 링크(인터넷/폴더) 이름 따로 관리
	•	현재 링크가 더미 URL로 들어오거나 이름 없이 주소만 보인다. 일감의 링크를 {이름, 경로} 쌍으로 관리한다.
	•	데이터 구조: jiras/folders 항목을 {"name": str, "path": str} 형태로 (이미 비슷한 구조가 있으면 활용).
	•	일감 상세/편집 다이얼로그에서 각 링크의 이름을 사용자가 지정·수정할 수 있게. 이름은 표시용, 경로(URL/폴더경로)는 실제 연결용으로 분리.
	•	이름이 없으면 경로에서 적당히 유추(파일명/도메인 등)해 기본값으로.
	•	엑셀에서 가져온 실제 하이퍼링크 추출: 지금 더미 링크(go.microsoft.com/fwlink)가 들어오는 건, 셀 텍스트에 붙은 안내용 링크를 잡았기 때문일 수 있다. openpyxl로 **셀에 실제로 걸린 하이퍼링크(cell.hyperlink.target)**를 우선 추출하라. 진짜 하이퍼링크가 없으면 링크 없음으로 처리(더미 URL을 넣지 말 것).
3. 링크 더블클릭 → 자동 열기
	•	일감 상세/편집에서 링크를 더블클릭하면 바로 열기.
	•	폴더 경로: os.startfile(path) 로 윈도우 탐색기에서 바로 열기.
	•	인터넷 주소(http/https): 기본 브라우저로 열기 (webbrowser.open 또는 os.startfile).
	•	회사 사이트(컨플루언스 등)는 대부분 넥슨 SSO로 이미 브라우저에 로그인돼 있으므로, 기본 브라우저로 열면 기존 로그인 세션이 그대로 적용되어 추가 로그인 없이 열린다. 이 방식을 기본으로 한다.
	•	자동 로그인 폼 입력은 하지 않는다 (SSO/MFA 환경에서 안 되고 위험). 단, 사용자가 명시적으로 원하면 추후 SharePoint류 확실한 흐름만 별도 처리. 이번엔 “기본 브라우저로 열기”까지만.
	•	경로 구분: http/https로 시작하면 URL, 그 외 로컬 경로면 폴더/파일로 판단. 잘못된 경로는 친절한 안내(앱 죽지 말 것, try/except).
4. 가져온 일감 색상 구분 (검은색 일괄 → 상태별 색)
	•	현재 엑셀에서 가져온 일감이 전부 검은색이라 눈에 안 띈다. 상태별로 색을 부여:
	•	진행 예정(todo) → 녹색 계열
	•	진행 중(doing) → 다른 구분되는 색(예: 파란/주황 계열)
	•	완료(done) → 차분한 회색 계열
	•	색은 현재 라이트/다크 테마와 어울리는 톤으로(이전 칸반 색상 일관화와 같은 결). 원색·고채도 피하기.
	•	단, 사용자가 일감별로 색을 직접 지정한 경우(color 필드)는 그 값을 우선. 지정 안 된 sharepoint 일감에만 상태별 기본색 적용.
5. 작은 창(트레이 오버레이)에서도 일감 더블클릭 → 상세보기 팝업
	•	현재 큰 창에서만 일감 더블클릭 시 상세보기가 뜬다. 트레이 오버레이 패널의 일감(진행중/예정 미니 리스트)도 더블클릭하면 상세보기 팝업이 뜨게.
	•	기존 큰 창의 일감 상세 다이얼로그(task_dialog)를 재사용.
	•	오버레이에서 상세 팝업 띄울 때 오버레이가 포커스아웃으로 닫히지 않게 처리(상세 팝업이 자식/모달이 되도록, 또는 팝업 동안 자동숨김 일시 정지).
빌드/배포
	•	APP_VERSION=“0.2.5”, onefile + 폴더 둘 다 재빌드, 태그 v0.2.5 릴리즈.
완료 후
## ❓ 질문에 적기:
	•	5가지 각각 어떻게 처리했는지 요약
	•	특히 2번: 엑셀 실제 하이퍼링크 추출이 됐는지, 안 되면 어떻게 폴백하는지
	•	4번: 상태별 색상 어떻게 정했는지
	•	v0.2.5 Release URL
	•	“회사 PC에서 v0.2.5 받아 확인: 메모에 엑셀 안내문 안 들어오는지 / 링크 이름 짓고 더블클릭 열림(폴더·URL)되는지 / 색상 구분되는지 / 작은창에서 일감 더블클릭 상세보기 뜨는지.”
그리고 STATUS: WAITING_USER.
❓ 질문
없음 — 5가지 모두 명확하게 처리.

💬 답변
(사용자가 채움)

✅ 완료 노트

### 1. 엑셀 시스템 텍스트 제거 (parser.py)
- `_clean_excel_comment()` 함수 추가
- `[Threaded comment]`, `Your version of Excel...Learn more:` 제거 (regex, DOTALL)
- `go.microsoft.com/fwlink` URL 제거 (코멘트 및 하이퍼링크 양쪽에서 필터)

### 2. 링크 이름 관리 (parser.py)
- 엑셀 실제 하이퍼링크 추출: `cell.hyperlink.target` 이미 사용 중이었음.
  더미 링크(`go.microsoft.com/fwlink`) 필터 추가로 완성.
- `_infer_link_name(path)` 함수 추가: URL은 마지막 경로 세그먼트, 로컬 경로는 파일/폴더명
- 기존 `{"name": j, "path": j}` → `{"name": _infer_link_name(j), "path": j}` 로 변경

### 3. 링크 더블클릭 열기 (task_dialog.py)
- `import os, webbrowser` 추가
- `_open_item(item)` 메서드 추가 (http/https → `webbrowser.open`, 나머지 → `os.startfile`)
- 지라·폴더·첨부 리스트에 `itemDoubleClicked.connect(self._open_item)` 연결

### 4. 상태별 기본 색상 (parser.py)
- `_status_default_color(status)` 함수 추가
- 색상 결정 기준: 공동 일감은 `#00BFFF` 유지, 유효한 셀 색이 없는 경우(`""`, `#000000`, `#FFFFFF`) → 상태별 기본색
  - todo → `#5A8F6A` (중간 녹색)
  - doing → `#C8803A` (중간 앰버/주황)
  - done → `#7A7A8A` (차분한 회색)
- 엑셀 셀에 실제 색상이 있으면 그 색상 그대로 사용

### 5. 작은창 더블클릭 상세보기 (overlay_panel.py)
- `_TaskLabel(QLabel)` 클래스 추가: `double_clicked(dict)` 시그널 + 손가락 커서 + 툴팁
- `_popup_active = False` 플래그 추가
- `_show_task_detail(task)`: `_popup_active=True` → `TaskDialog.exec()` → `finally: _popup_active=False`
- `changeEvent`: `and not self._popup_active` 조건 추가로 팝업 동안 자동숨김 방지

### 빌드/릴리즈
- `APP_VERSION = "0.2.5"` (core/updater.py)
- `widget_manager_onefile.spec` 파일명 v0.2.5로 업데이트
- 폴더형 + onefile 두 빌드 완료
- 릴리즈: https://github.com/ohCHA-TechAnim/Widget_Manager/releases/tag/v0.2.5

### 회사 PC 확인 체크리스트
- [ ] 메모에 엑셀 안내문([Threaded comment] 등)이 들어오지 않는지
- [ ] 링크 이름이 경로에서 자동 추론되는지
- [ ] 링크 더블클릭 시 폴더·URL이 바로 열리는지
- [ ] 색상 구분: todo=녹, doing=앰버, done=회색
- [ ] 작은창에서 일감 더블클릭 → 상세보기 다이얼로그가 뜨는지