#Requires -Version 5.1
<#
.SYNOPSIS
    GitHub의 TASK.md 변경을 감지하여 Claude Code를 자동 실행하는 대화형 워처.

.DESCRIPTION
    STATUS 신호등으로 흐름을 제어한다:
      IDLE         → 대기
      PENDING      → Claude Code 실행 (사용자가 지시한 상태)
      WAITING_USER → 대기 (Claude가 질문 중, 사용자 차례)
      DONE         → 대기 (작업 완료)

    60초마다 원격 저장소를 폴링. TASK.md가 변경됐고 STATUS가 PENDING이면
    Claude Code를 실행. 그 외 STATUS는 모두 건너뜀.

    기반: D:\UnrealProjects\TechAnim_Lab\scripts\watch_and_run.ps1
    (검증된 폴링/단일해시비교/git pull/try-catch 구조를 재사용)

.PARAMETER PollSeconds
    폴링 간격(초). 기본값 60.

.PARAMETER Branch
    감시할 브랜치. 기본값 main.

.EXAMPLE
    .\watch_and_run.ps1
    .\watch_and_run.ps1 -PollSeconds 15   # 빠른 테스트용
#>

param(
    [int]$PollSeconds = 60,
    [string]$Branch   = "main"
)

$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------------------
# 경로 설정 (TechAnim_Lab 패턴 동일 — PSScriptRoot = scripts/ 폴더)
# ---------------------------------------------------------------------------
$ProjectRoot = Split-Path -Parent $PSScriptRoot   # D:\Projects\Widget_Manager
$TaskFile    = Join-Path $ProjectRoot "TASK.md"
$StateFile   = Join-Path $PSScriptRoot "watcher_state.json"  # scripts/ 안에
$LogFile     = Join-Path $PSScriptRoot "task_runner.log"     # scripts/ 안에

# ---------------------------------------------------------------------------
# 유틸리티 함수 (TechAnim_Lab 동일 구조 재사용)
# ---------------------------------------------------------------------------
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')][$Level] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    switch ($Level) {
        "ERROR" { Write-Host $line -ForegroundColor Red    }
        "WARN"  { Write-Host $line -ForegroundColor Yellow }
        "OK"    { Write-Host $line -ForegroundColor Green  }
        default { Write-Host $line }
    }
}

function Get-LastProcessedHash {
    # scripts/watcher_state.json 에서 마지막으로 처리한 커밋 해시를 읽는다.
    if (Test-Path $StateFile) {
        try {
            return [string](Get-Content $StateFile -Raw -Encoding UTF8 |
                            ConvertFrom-Json).lastProcessedHash
        } catch { return "" }
    }
    return ""
}

function Save-LastProcessedHash([string]$Hash) {
    # 처리한 해시를 즉시 저장해 같은 커밋을 두 번 처리하지 않게 한다.
    # 중요: Claude 실행 전에 호출해야 이중 처리를 막는다.
    @{ lastProcessedHash = $Hash; updatedAt = (Get-Date -Format 'o') } |
        ConvertTo-Json | Set-Content $StateFile -Encoding UTF8
}

function Get-TaskStatus {
    # TASK.md 맨 위의 "STATUS: XXX" 줄에서 상태값을 파싱한다.
    # 없으면 빈 문자열 반환 → 워처가 skip.
    param([string]$Content)
    if ($Content -match 'STATUS:\s*(\S+)') {
        return $Matches[1].Trim().ToUpper()
    }
    return ""
}

# ---------------------------------------------------------------------------
# Claude Code 실행 프롬프트 (매 라운드 동일 — 질문/완료 지침 포함)
# ---------------------------------------------------------------------------
# 이 프롬프트가 Claude Code에게 "무엇을 할지"와 "언제 멈추고 질문할지"를 알려준다.
$ClaudePrompt = @"
너는 D:\Projects\Widget_Manager 프로젝트를 개발한다.
TASK.md 파일을 읽고 ## 작업 지시 섹션의 내용을 수행하라.
이전에 질문했다면 ## 💬 답변 섹션도 읽고 이어서 진행하라.

[중요한 결정 — 멈추고 질문할 것]:
아래 중 하나라도 해당하면 추측하지 말고 질문하라:
  - 데이터 구조 변경 또는 추가
  - 기능 추가·삭제·범위 변경
  - 파일/폴더 구조의 큰 결정
  - 외부 라이브러리(새 의존성) 추가
  - 기존 동작을 바꾸는 리팩터링
  - 사용자 의도가 모호한 지점

질문 방법:
  1. TASK.md에 "## ❓ 질문 N" 섹션을 추가하고 선택지(A/B/...)와 각 장단점을 적는다.
  2. STATUS를 정확히 "STATUS: WAITING_USER" 로 바꾼다.
  3. 변경된 TASK.md를 저장한다.
  4. 그 라운드를 종료한다 (commit & push는 워처가 처리).
  애매하면 질문하는 쪽을 택하라.

[알아서 진행해도 되는 것]:
  - 변수명, 함수명, 주석, 코드 포맷팅
  - 명백한 버그 수정
  - 지시에 이미 명시된 구현 세부사항
  - 테스트 코드 작성

[작업 완료 시]:
  - STATUS를 정확히 "STATUS: DONE" 으로 바꾼다.
  - "## ✅ 완료 노트" 섹션에 한국어로 수행 내용 요약을 작성한다 (날짜/시각 포함).
  - 변경된 TASK.md를 저장한다 (commit & push는 워처가 처리).

모든 코드에 한국어 주석을 달아라.
"@

# ---------------------------------------------------------------------------
# 시작
# ---------------------------------------------------------------------------
Set-Location $ProjectRoot
Write-Log "=== Widget_Manager 워처 시작 ==="
Write-Log "프로젝트: $ProjectRoot"
Write-Log "브랜치: $Branch | 폴링 간격: ${PollSeconds}초"

# claude CLI 존재 확인
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Log "claude CLI를 찾을 수 없습니다. Claude Code 설치를 확인하세요." "ERROR"
    exit 1
}

# ---------------------------------------------------------------------------
# 메인 루프
# ---------------------------------------------------------------------------
while ($true) {
    try {
        # 1) 원격 변경사항 fetch (로컬 파일 변경 없음)
        $null = git fetch origin $Branch 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "git fetch 실패 — 네트워크 확인 필요." "WARN"
            Start-Sleep -Seconds $PollSeconds
            continue
        }

        # 2) TASK.md의 원격 최신 커밋 해시 (단일 문자열 보장 — 기존 배열 버그 수정 적용)
        $remoteHash = ((git log -1 --format="%H" "origin/$Branch" -- TASK.md 2>&1) -join "").Trim()
        if (-not $remoteHash -or $remoteHash -like "fatal:*") {
            # TASK.md 가 아직 없거나 저장소가 비어있음 — 다음 폴링 때 재시도
            Start-Sleep -Seconds $PollSeconds
            continue
        }

        # 3) 이미 처리한 커밋이면 건너뜀
        $lastHash = Get-LastProcessedHash
        if ($remoteHash -eq $lastHash) {
            Start-Sleep -Seconds $PollSeconds
            continue
        }

        Write-Log "TASK.md 변경 감지 (commit: $($remoteHash.Substring(0,8)))"

        # 4) 최신 코드 pull
        $pullOut = git pull origin $Branch 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "git pull 실패: $pullOut" "ERROR"
            Start-Sleep -Seconds $PollSeconds
            continue
        }

        if (-not (Test-Path $TaskFile)) {
            Write-Log "TASK.md 파일이 없습니다." "WARN"
            Save-LastProcessedHash $remoteHash
            Start-Sleep -Seconds $PollSeconds
            continue
        }

        # 5) 해시를 즉시 저장 — Claude 실행 전에 저장해야 이중 처리를 막는다
        #    (워처가 재시작되더라도 같은 커밋을 다시 처리하지 않음)
        Save-LastProcessedHash $remoteHash

        # 6) STATUS 파싱
        $taskContent = Get-Content $TaskFile -Raw -Encoding UTF8
        $status      = Get-TaskStatus $taskContent

        switch ($status) {
            "PENDING" {
                # 사용자가 지시를 남긴 상태 — Claude Code 실행
                Write-Log "STATUS=PENDING 확인. Claude Code 실행 시작..." "OK"
            }
            "WAITING_USER" {
                Write-Log "STATUS=WAITING_USER — 사용자 답변 대기 중. 건너뜁니다."
                Start-Sleep -Seconds $PollSeconds
                continue
            }
            "DONE" {
                Write-Log "STATUS=DONE — 이미 완료된 작업. 건너뜁니다."
                Start-Sleep -Seconds $PollSeconds
                continue
            }
            "IDLE" {
                Write-Log "STATUS=IDLE — 대기 중. 건너뜁니다."
                Start-Sleep -Seconds $PollSeconds
                continue
            }
            default {
                Write-Log "STATUS='$status' — 알 수 없는 값. 건너뜁니다." "WARN"
                Start-Sleep -Seconds $PollSeconds
                continue
            }
        }

        # 7) Claude Code 실행 (비대화 모드 + 권한 자동 승인)
        Write-Log "claude 실행 중..."
        $claudeOutput  = & claude --dangerously-skip-permissions -p $ClaudePrompt 2>&1
        $claudeExitCode = $LASTEXITCODE

        if ($claudeExitCode -eq 0) {
            Write-Log "Claude Code 종료 (정상)." "OK"
        } else {
            Write-Log "Claude Code 오류 반환 (exit: $claudeExitCode)." "WARN"
        }

        # 8) Claude가 변경한 파일들을 모두 commit & push
        git add -A
        $staged = (git diff --staged --name-only 2>&1) -join ""
        if ($staged) {
            git commit -m "auto: Claude 작업 완료 (ref $($remoteHash.Substring(0,8)))"

            $pushOut = git push origin $Branch 2>&1
            if ($LASTEXITCODE -ne 0) {
                # push 충돌 시 rebase 후 재시도
                Write-Log "Push 실패. rebase 재시도..." "WARN"
                git pull --rebase origin $Branch 2>&1 | Out-Null
                git push origin $Branch 2>&1 | Out-Null
            }

            if ($LASTEXITCODE -eq 0) {
                Write-Log "GitHub push 완료." "OK"
            } else {
                Write-Log "Push 최종 실패. 수동 push 필요." "ERROR"
            }
        } else {
            Write-Log "파일 변경 없음 — commit 생략."
        }

    } catch {
        Write-Log "예외 발생: $_" "ERROR"
    }

    Start-Sleep -Seconds $PollSeconds
}
