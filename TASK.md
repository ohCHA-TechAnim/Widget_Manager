STATUS: PENDING
작업 지시 — Widget_Manager 재빌드 + GitHub Releases 배포 (회사에서 exe 받기 위함)
작업자: 차승현. 현재 v0.2 + nexon_sharepoint 애드온까지 코드 완료된 상태.
사용자가 지금 회사에 있고, 집 PC(이 워처가 도는 PC)에서 만들어진 최신 exe를 회사 PC에서 받아 테스트하려 한다.
목표: 최신 코드로 exe를 재빌드하고 GitHub Releases에 올려서, 회사에서 다운로드할 수 있게 한다.
진행 규칙
	•	아래 순서대로 하고, 끝나면 ## ❓ 질문에 결과(릴리즈 URL 포함) 적고 STATUS: WAITING_USER로 멈춰라.
	•	빌드/배포 중 실패하면 그 지점에서 멈추고 에러를 ❓질문에 적고 WAITING_USER. (추측으로 우회하지 마라.)
	•	코어/애드온 코드는 수정하지 마라. 이번은 빌드·배포만.
할 일
	1.	의존성 확인·설치
	•	selenium, openpyxl 등 SharePoint 애드온이 쓰는 패키지가 빌드 환경에 설치돼 있는지 확인. 없으면 설치.
	•	py -m pip install selenium openpyxl python-docx (이미 있으면 넘어감)
	2.	spec에 애드온 의존성 포함
	•	widget_manager.spec을 점검해서, exe에 selenium, openpyxl, python-docx, plugins/nexon_sharepoint/ 가 포함되도록 한다.
	•	PyInstaller가 selenium을 누락하기 쉬우니 hiddenimports 또는 collect_all로 selenium을 명시적으로 포함. plugins 폴더 데이터도 포함 확인.
	•	목표: 빌드된 exe에서 “SharePoint 일정 가져오기”를 눌렀을 때 “selenium 없음” 에러가 나지 않아야 한다.
	•	(단, chromedriver 자체는 사용자 PC의 Chrome에 맞춰야 하므로 exe에 안 넣어도 됨. selenium은 Selenium Manager로 드라이버 자동 처리 시도하니, 그 동작 확인.)
	3.	버전 올리기
	•	core/updater.py의 APP_VERSION을 “0.1.0” → “0.2.0” 으로 변경. (v0.2 + 애드온 반영 버전)
	•	이건 코드 수정이지만 버전 표기라 예외로 허용.
	4.	클린 재빌드
	•	.\build.ps1 -Clean 으로 처음부터 새로 빌드.
	•	결과: dist\WidgetManager\WidgetManager.exe + dist\WidgetManager\_internal\
	•	빌드 후 exe가 실제로 기동되는지 간단 확인(프로세스 뜨고 로그 에러 없는지).
	5.	배포용 zip 생성
	•	dist\WidgetManager 폴더 전체(exe + _internal 통째로)를 zip으로 압축.
	•	반드시 _internal 폴더를 포함해야 함 (exe 혼자선 안 돌아감).
	•	zip 이름 예: WidgetManager_v0.2.0.zip
	6.	GitHub Release 생성 + 업로드
	•	gh CLI로 릴리즈 생성하고 zip 첨부: