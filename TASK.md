STATUS: PENDING

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
(Claude Code가 채웁니다)

💬 답변
(사용자가 채웁니다)

✅ 완료 노트
(Claude Code가 채웁니다)
