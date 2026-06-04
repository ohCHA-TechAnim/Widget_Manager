STATUS: PENDING

## 작업 지시 — Widget_Manager 재빌드 v0.2.1 (selenium 누락 수정 + onefile/폴더 둘 다 배포)

작업자: 차승현. 회사 PC에서 받은 exe로 SharePoint 가져오기를 눌렀더니 **“selenium 패키지 없음”** 에러가 났다.
원인: 직전 빌드(v0.2.0)에서 selenium이 exe에 포함되지 않았다. (빌드 환경에 selenium 미설치였거나, PyInstaller가 동적 import 많은 selenium을 누락.)
이번에 그걸 확실히 고치고, **onefile(단일 exe)과 폴더(_internal 포함) 두 가지를 모두** 릴리즈한다.

### 진행 규칙

- 아래 순서대로. 각 검증 단계에서 실패하면 그 지점에서 멈추고 ❓질문에 에러 적고 STATUS: WAITING_USER. 추측으로 넘어가지 마라.
- 코어/애드온 로직 코드는 수정 금지. 이번은 의존성·빌드·배포만. (버전 표기만 예외)

### 할 일

1. **selenium 설치 확인·설치 (가장 중요 — 여기서 빠지면 다 무의미)**
- 빌드 환경에 설치돼 있는지 먼저 확인:
  
  ```
  py -c "import selenium; print('selenium', selenium.__version__)"
  ```
- ImportError거나 버전이 안 뜨면 설치:
  
  ```
  py -m pip install selenium openpyxl python-docx
  ```
- 설치 후 위 import 확인 명령을 **다시 실행해서 버전이 출력되는지 반드시 검증.** 버전이 안 뜨면 멈추고 WAITING_USER로 보고.
- requirements.txt에도 selenium, openpyxl, python-docx 명시(애드온 전용 주석).
1. **APP_VERSION 갱신**
- `core/updater.py`의 `APP_VERSION`을 **“0.2.1”** 로 변경.
1. **spec에서 selenium을 강하게 포함**
- `widget_manager.spec`에서 PyInstaller가 selenium을 확실히 담도록:
  - 상단에 `from PyInstaller.utils.hooks import collect_all`
  - `sel_datas, sel_binaries, sel_hiddenimports = collect_all('selenium')` 사용해서 datas/binaries/hiddenimports에 합치기.
  - selenium뿐 아니라 그 의존(예: `trio`, `outcome`, `sniffio`, `wsproto`, `websocket` 등 Selenium 4 계열이 쓰는 것)도 collect_all/ hiddenimports로 누락 안 되게. (selenium collect_all이 대부분 잡지만, 빌드 후 검증에서 빠진 게 나오면 추가.)
  - openpyxl, python-docx도 hiddenimports에 포함.
  - plugins/ 폴더(특히 plugins/nexon_sharepoint/) 데이터 포함 확인.
- **단일 spec으로 onefile/폴더 둘 다 만들기 어렵다면, 빌드를 두 번 돌려라:**
  - 폴더(onedir)용 빌드 1회 → `dist\WidgetManager\`
  - onefile용 빌드 1회 → `dist\WidgetManager.exe` (단일 파일)
  - build.ps1에 `-OneFile` 스위치를 추가하거나, onefile용 spec(`widget_manager_onefile.spec`)을 별도로 만들어도 됨. 방식은 알아서.
1. **클린 빌드 (두 형태)**
- 폴더형: `dist\WidgetManager\WidgetManager.exe` + `_internal\`
- 단일형: `dist\WidgetManager_onefile.exe` (또는 적절한 이름. 폴더형 exe와 파일명이 겹치지 않게.)
1. **빌드 결과에 selenium이 진짜 들어갔는지 검증 (필수)**
- 폴더형: `dist\WidgetManager\_internal\` 안에 selenium 관련 파일/폴더가 있는지 확인 (예: `_internal\selenium\` 존재 여부를 dir로 확인).
- 가능하면 더 확실하게: 빌드된 exe를 잠깐 실행해 로그에 selenium import 성공이 찍히는지, 또는 별도 작은 점검. 최소한 _internal\selenium 폴더 존재는 dir로 확인해서 ❓질문에 결과 적기.
- selenium이 안 보이면 3번으로 돌아가 hiddenimports 보강 후 재빌드.
1. **배포용 패키징**
- 폴더형: `dist\WidgetManager` 전체를 `WidgetManager_v0.2.1_folder.zip`으로 압축 (_internal 반드시 포함).
- 단일형: `WidgetManager_v0.2.1_onefile.exe` (그대로, 또는 zip으로 감싸도 됨).
1. **GitHub Release 생성 + 둘 다 업로드**
   
   ```
   gh release create v0.2.1 "WidgetManager_v0.2.1_folder.zip" "WidgetManager_v0.2.1_onefile.exe" --title "Widget_Manager v0.2.1" --notes "selenium 포함 수정. 두 형태 제공 — onefile: exe 하나만 받으면 됨(첫 실행 느림). folder zip: 압축 풀어 _internal과 함께 실행(빠름). SharePoint 가져오기 동작하려면 PC에 Chrome 설치 필요."
   ```
- 태그 v0.2.1 = APP_VERSION 0.2.1 일치 확인.

### 참고 (사용자 환경)

- 회사 PC에서 SharePoint 가져오기를 실제로 쓰려면, 그 PC에 **Chrome 브라우저**가 설치돼 있어야 한다(selenium이 Chrome을 띄움). Selenium 4의 Selenium Manager가 chromedriver는 자동 처리 시도하나, 사내망 방화벽으로 드라이버 자동 다운로드가 막히면 수동 배치가 필요할 수 있음 — 그건 실제 테스트에서 확인.

### 완료 후

`## ❓ 질문`에 적기:

- selenium import 검증 결과(버전 출력), _internal\selenium 존재 확인 결과
- onefile/폴더 두 exe 크기
- **GitHub Release v0.2.1 URL**
- “회사 PC에서: onefile이면 exe 하나만 받아 실행, 폴더면 zip 풀어 실행. Chrome 설치 확인 후 SharePoint 가져오기 재시도. selenium 에러가 또 나면 알려달라.”
  그리고 STATUS: WAITING_USER.

## ❓ 질문

(Claude가 채움)

## 💬 답변

(사용자가 채움)

## ✅ 완료 노트

(Claude가 채움)