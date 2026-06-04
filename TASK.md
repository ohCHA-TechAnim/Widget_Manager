STATUS: PENDING

## 작업 지시 — SharePoint 애드온 버그 수정 (다운로드 경로 일원화 + 타임아웃 + 재다운로드 + 일감 생성)

작업자: 차승현. 회사 PC에서 실제 테스트 중. selenium 에러는 해결됐고 **로그인·엑셀 다운로드까지 성공**(파일이 실제로 받아짐). 그러나 아래 버그들이 있다.

### 증상 (실측)

1. **다운로드 타임아웃(40초 초과) 에러** 발생. 그런데 엑셀 파일은 실제로 **Chrome 기본 다운로드 폴더**에 받아져 있다. → 즉 다운로드는 됐는데 앱이 “받아진 파일”을 엉뚱한 경로에서 기다리다 타임아웃. **파일이 떨어지는 위치와 앱이 감시하는 위치가 다르다.**
1. **일감 생성이 완료되지 않음.** (1번 때문에 파싱 단계로 못 넘어가는 것으로 추정.)
1. **재다운로드 시 기존 파일/일감을 삭제하고 새로 받는 처리가 안 됨.** (두 번째 가져오기에서 기존 것 정리 실패.)

### 해결 방향 (핵심)

모든 앱 산출물을 **`%APPDATA%\Widget_Manager\` (= AppData/Roaming/Widget_Manager) 아래로 일원화**하고, 종류별 하위 폴더로 구분한다. 다운로드도 Chrome 기본 폴더가 아니라 이 앱 전용 폴더로 직접 받게 해서 “받는 위치 = 읽는 위치”를 일치시킨다.

### 폴더 구조 (없으면 생성 — os.makedirs(exist_ok=True))

```
%APPDATA%\Widget_Manager\
├── data\        # tasks.json 등 핵심 데이터 (기존 유지)
├── logs\        # widget_manager.log (기존 유지)
├── downloads\   # [신규] SharePoint 등에서 받은 엑셀 원본
└── debug\       # [신규] sp_error_shot.png 등 디버그 스크린샷/덤프
```

- 경로 헬퍼를 한 곳에 두고(예: core/paths.py 또는 기존 경로 유틸), 모든 모듈이 이걸 쓰게. 하드코딩된 다운로드 경로/스크린샷 경로 전부 이걸로 교체.
- 폴더가 없으면 자동 생성.

### 할 일

1. **앱 전용 경로 헬퍼 정리**
- `%APPDATA%\Widget_Manager` 루트와 위 4개 하위 폴더(data/logs/downloads/debug) 경로를 반환하는 헬퍼 마련(없으면 생성). 기존에 data/logs 경로 잡는 코드가 있으면 거기에 downloads/debug 추가.
1. **다운로드를 downloads 폴더로 직접 받기 (타임아웃 근본 해결)**
- downloader.py(Selenium)에서 Chrome 옵션으로 **다운로드 기본 경로를 `%APPDATA%\Widget_Manager\downloads`로 지정**:
  - `options.add_experimental_option("prefs", {"download.default_directory": <downloads경로>, "download.prompt_for_download": False, "download.directory_upgrade": True, "safebrowsing.enabled": True})`
- 다운로드 완료 감지: 그 downloads 폴더에서 대상 확장자(.xlsx) 파일이 나타나고 **.crdownload(임시파일)가 사라질 때까지** 폴링. (Chrome은 받는 중엔 `*.crdownload`를 만든다.) 이 방식으로 “받아진 걸 확실히” 감지 → 40초 타임아웃 방지.
- 타임아웃 값도 적절히(예: 60~90초) 두되, 핵심은 올바른 폴더를 감시하는 것.
1. **재다운로드 시 정리 (idempotent)**
- 가져오기 시작 시 downloads 폴더의 기존 대상 엑셀(또는 이전 다운로드 잔재 *.xlsx, *.crdownload)을 먼저 삭제하고 새로 받기. (또는 타임스탬프/고정 파일명으로 관리.)
- 파싱 후 task_store에 넣을 때: **기존 `source=="sharepoint"` 일감을 전부 제거한 뒤 새로 추가**(중복 누적 금지). manual 일감은 절대 건드리지 말 것. (이미 1라운드에 이 로직을 의도했으니, 실제로 동작하는지 점검·수정.)
1. **일감 생성 완료까지 흐름 잇기**
- 다운로드 성공 → parser.parse_excel(받은 파일 경로) → task dict 목록 → task_store 갱신 → 뷰 자동 반영. 이 체인이 1번 타임아웃 때문에 끊겼을 것이므로, 2번 수정 후 끝까지 도달하는지 확인.
- 완료 시 사용자에게 “N개 일감 가져옴” 안내. 0개면 “파일은 받았으나 파싱 0건 — 시트명/대상자/셀렉터 확인” 안내(셀렉터 교정은 별도).
1. **디버그 산출물 경로도 통일**
- sp_error_shot.png 등 스크린샷/page_source 덤프는 `%APPDATA%\Widget_Manager\debug\`로. 에러 메시지의 안내 경로도 실제 저장 위치와 일치하게 수정.
1. **로깅**
- 다운로드 시작/완료/감지된 파일 경로/파싱 건수/정리된 기존 일감 수를 logs에 남겨, 다음에 문제 생기면 로그만 봐도 추적되게. print 금지(logging만).

### 빌드/배포

- 수정 후 v0.2.1과 동일 방식으로 **onefile + 폴더 둘 다** 재빌드해서 **v0.2.2**로 릴리즈. (`core/updater.py` APP_VERSION=“0.2.2”, 태그 v0.2.2 일치.)
- selenium 포함은 v0.2.1에서 됐으니 그 spec 유지.

### 완료 후

`## ❓ 질문`에 적기:

- 바뀐 폴더 구조와 경로 헬퍼 위치
- 다운로드 감지 방식(.crdownload 폴링) 적용 결과
- 재다운로드 정리·sharepoint 일감 교체 로직 점검 결과
- v0.2.2 Release URL
- “회사 PC에서 v0.2.2 받아 재테스트: 가져오기 → downloads 폴더에 받기는지, 타임아웃 없이 일감 생성되는지, 두 번째 가져오기에서 기존 게 갈리는지 확인. 안 되면 그때 sp_error_shot.png와 widget_manager.log 내용 알려달라.”
  그리고 STATUS: WAITING_USER.

## ❓ 질문

(Claude가 채움)

## 💬 답변

(사용자가 채움)

## ✅ 완료 노트

(Claude가 채움)