STATUS: PENDING
작업 지시 — Widget_Manager 넥슨 SharePoint 일정 애드온 (1라운드: 이식 + 구조 연결)
작업자: 차승현(Nexon 3D TA). 한국어 주석. PyQt6.
현재 v0.2까지 완성(코어 + 트레이 오버레이). 이제 v0.1 때 깔아둔 플러그인 토대(core/plugin_loader.py, core/plugin_api.py) 위에 실제 넥슨 SharePoint 애드온을 얹는다.
핵심: 새로 만드는 게 아니라, TaskHub에 이미 검증된 코드를 플러그인으로 이식하는 것이다.
원본 소스: 같은 PC의 TaskHub 인수인계 문서에 SharePoint 다운로더 전체 코드가 있다. (사용자가 별도로 알려주는 경로의 TaskHub_완전판_v2_소스포함.md, 또는 기존 TaskHub 프로젝트 폴더의 utils/selenium_downloader.py.) 그 파일을 먼저 읽어서 검증된 로직을 그대로 가져와라. 추측으로 새로 짜지 마라.
원격 진행 규칙 (반드시 지킬 것)
	•	한 번에 다 만들지 마라. 이번 라운드는 SharePoint만(Outlook 회의는 다음 라운드). 끝나면 ## ❓ 질문에 완료 보고 + “실제 로그인 테스트는 회사 PC에서 해야 한다. 2라운드(Outlook) 갈까, 아니면 먼저 회사에서 SharePoint 테스트할까?“를 적고 STATUS: WAITING_USER로 멈춰라.
	•	중요한 결정(데이터 흐름 변경, 기존 동작 변경, 플러그인 인터페이스 설계 모호점)이 생기면 추측 말고 그 자리에서 WAITING_USER로 질문.
	•	사소한 것(변수명/주석/내부 함수 분리)은 알아서.
	•	각 의미 단위마다 git commit.
	•	기존에 동작하던 코어 기능(손입력 일정, 테마, 트레이 오버레이, tasks.json 저장)을 절대 망가뜨리지 마라. 애드온은 그 위에 얹기만 한다. 애드온이 꺼져 있어도 코어는 100% 작동해야 한다.
이번 라운드 목표 (SharePoint 일정 → 달력에 표시)
회사 SharePoint 라이브러리의 애니메이션팀 일정 엑셀을 Selenium으로 (넥슨 계정 웹 로그인 우회로) 받아와 파싱하고, 그 일정을 Widget_Manager 달력에 source: "sharepoint"로 표시한다.
할 일
	1.	TaskHub 원본 읽기
	•	TaskHub 문서/프로젝트에서 utils/selenium_downloader.py(SeleniumDownloader QThread, stale element 재시도 패치 포함)와 엑셀 파싱 로직(parse_excel_data 류), 설정 구조를 읽어라.
	•	검증된 부분: MS 로그인 흐름, SharePoint 라이브러리 접근, 엑셀 다운로드, stale element 재시도. 이건 그대로 이식.
	2.	플러그인으로 이식 — plugins/nexon_sharepoint/ 폴더 신설
	•	plugins/nexon_sharepoint/__init__.py — PluginBase 상속한 애드온 클래스. core/plugin_api.py의 인터페이스를 따른다. on_load/on_unload, 메뉴 액션(예: “SharePoint 일정 가져오기”) 제공.
	•	plugins/nexon_sharepoint/downloader.py — TaskHub의 selenium_downloader.py 이식 (QThread 비동기 유지). Chrome/chromedriver 사용.
	•	plugins/nexon_sharepoint/parser.py — 엑셀 → 일정 데이터 변환. Widget_Manager의 일정 데이터 구조(id/title/start/end/status/priority/memo/color/source/…)에 맞게 필드 매핑. source는 “sharepoint” 고정.
	•	TaskHub의 색상/휴일 규칙(90% 공동 일감 #00BFFF, 80%+ 공실 자동 휴일, 분홍 셀 휴일)도 가져오되, parser 안에 가둬라(코어는 모름).
	3.	데이터 흐름 연결 (코어 오염 금지)
	•	애드온은 가져온 일정을 core/task_store.py에 source: "sharepoint"로 넣는다.
	•	달력/리스트/칸반은 기존대로 task_store만 읽으니 자동 표시됨. 뷰 코드는 건드리지 마라.
	•	가져온(sharepoint) 일정은 읽기 전용 취급: 손으로 만든(manual) 일정과 구분되게, 편집/삭제 시 경고하거나 막는 정도. (세부는 합리적으로. 핵심은 “원본은 SharePoint에 있으니 여기서 수정해도 의미 없음”을 사용자가 알게.)
	•	재가져오기 시 기존 sharepoint 일정은 갱신(중복 누적 금지). manual 일정은 절대 건드리지 않게.
	4.	설정 연결 — v0.2에서 만든 설정 다이얼로그(메뉴바 → 설정 → 앱 설정)에 SharePoint 항목 추가
	•	입력: 넥슨 ID, 라이브러리 URL, 시트명, target_name(대상자), holidays. (TaskHub config 구조 참고: nexon_id, library_url, sheet_name, holidays.)
	•	비밀번호(nexon_pw): 평문 저장 금지. TaskHub는 평문이었지만 이식하면서 개선한다. 1차로는 비밀번호를 settings.json에 저장하지 말고 가져오기 실행 시마다 입력받거나, 가능하면 Windows DPAPI/keyring 사용. (keyring 의존성 추가가 부담이면 “매번 입력” 방식으로. 어느 쪽이든 평문 저장만은 피하라.)
	•	“SharePoint 일정 가져오기” ON/OFF 토글. OFF면 애드온 메뉴/동작 안 보임, 코어는 그대로.
	5.	빌드/안정성 주의 (TaskHub 교훈 반영)
	•	print() 금지 — 모두 logging으로 %APPDATA%\Widget_Manager\logs\에 기록 (PyInstaller –windowed 크래시 방지).
	•	새 의존성(selenium 등)은 requirements.txt에 추가하되, 애드온 전용임을 명시. 코어는 selenium 없이도 import/실행돼야 한다(애드온 로드 실패가 코어를 죽이면 안 됨 — plugin_loader의 에러 격리 확인).
	•	Selenium은 Chrome/chromedriver 버전 일치 필요. 코드에 버전 불일치 시 친절한 에러 메시지/로그.
이번 라운드에서 하지 말 것
	•	Outlook 회의 크롤러(다음 라운드).
	•	실제 넥슨 계정으로 로그인 테스트 (회사 PC에서 사용자가 직접). 너는 코드 이식과 구조 연결, 그리고 가짜/샘플 엑셀로 parser 단위 동작 확인까지만.
	•	셀렉터 교정(테넌트마다 다름 — 실제 화면 보고 회사에서).
완료 후
## ❓ 질문에 적기:
	•	무엇을 이식했는지(파일 목록), 데이터 흐름이 어떻게 연결됐는지
	•	코어가 애드온 없이도 여전히 작동하는지 확인 결과
	•	parser를 샘플 데이터로 테스트한 결과(가능하면)
	•	“실제 SharePoint 로그인·다운로드 테스트는 회사 PC에서 해야 한다. Chrome/chromedriver 버전 확인 필요. 2라운드(Outlook 회의)로 갈까, 아니면 먼저 회사에서 SharePoint 실제 테스트할까?”
그리고 STATUS: WAITING_USER로.
❓ 질문
(Claude가 채움)
💬 답변
(사용자가 채움)
✅ 완료 노트
(Claude가 단계별로 채움)