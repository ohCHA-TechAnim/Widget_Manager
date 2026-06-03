#Requires -RunAsAdministrator
<#
.SYNOPSIS
    WidgetManagerWatcher 작업 스케줄러를 등록한다.
    로그인 시 자동으로 watch_and_run.ps1 이 시작된다.

.NOTES
    실행 (관리자 PowerShell 필요):
      powershell -ExecutionPolicy Bypass -File "D:\Projects\Widget_Manager\scripts\setup_scheduler.ps1"

    ── 유용한 명령 ──────────────────────────────────────────────────────
    시작     : Start-ScheduledTask  -TaskName "WidgetManagerWatcher"
    중지     : Stop-ScheduledTask   -TaskName "WidgetManagerWatcher"
    상태확인 : Get-ScheduledTask    -TaskName "WidgetManagerWatcher" | Get-ScheduledTaskInfo
    제거     : Unregister-ScheduledTask -TaskName "WidgetManagerWatcher" -Confirm:$false
    직접실행 : powershell -ExecutionPolicy Bypass -File "D:\Projects\Widget_Manager\scripts\watch_and_run.ps1"

    ── 검증 방법 ────────────────────────────────────────────────────────
    1) Start-ScheduledTask 로 수동 시작 후 로그 확인:
       Get-Content D:\Projects\Widget_Manager\scripts\task_runner.log -Tail 10
    2) TASK.md 에 지시 작성 + STATUS: PENDING 커밋 → 자동 실행 확인.
    3) 재부팅 후 워처가 자동 시작됐는지 Get-ScheduledTask 로 확인.

    ── 기존 태스크와 이름 충돌 없음 ────────────────────────────────────
    ClaudeTaskRunner_TechAnimLab  : TechAnim_Lab 프로젝트 워처
    DailyTechAnimReport           : 새벽 TA 뉴스 리포트
    WidgetManagerWatcher          : 이 태스크 (Widget_Manager 전용)
#>

$TaskName   = "WidgetManagerWatcher"
$ScriptPath = "D:\Projects\Widget_Manager\scripts\watch_and_run.ps1"

if (-not (Test-Path $ScriptPath)) {
    Write-Error "watch_and_run.ps1 을 찾을 수 없습니다: $ScriptPath"
    exit 1
}

# 기존 태스크 제거 (재등록 시 깨끗하게)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 동작: 백그라운드에서 워처 실행 (-WindowStyle Minimized 로 창 최소화)
$Action = New-ScheduledTaskAction `
    -Execute  "powershell.exe" `
    -Argument "-NonInteractive -WindowStyle Minimized -ExecutionPolicy Bypass -File `"$ScriptPath`""

# 트리거: 로그인할 때마다 자동 시작
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# 실행 설정
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `  # 시간 제한 없음 (무한 루프 워처)
    -RestartCount       3 `                   # 실패 시 최대 3회 재시도
    -RestartInterval    (New-TimeSpan -Minutes 2) `  # 재시도 간격 2분
    -StartWhenAvailable `                     # 놓친 실행은 다음 가능 시점에 즉시 시작
    -MultipleInstances  IgnoreNew             # 이미 실행 중이면 새 인스턴스 무시

# 실행 주체: 현재 사용자, 최고 권한
$Principal = New-ScheduledTaskPrincipal `
    -UserId   $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName   $TaskName `
    -Action     $Action `
    -Trigger    $Trigger `
    -Settings   $Settings `
    -Principal  $Principal `
    -Description "Widget_Manager TASK.md 변경 감지 → Claude Code 자동 실행 (대화형 워처)" `
    -Force | Out-Null

Write-Host ""
Write-Host "등록 완료: '$TaskName'" -ForegroundColor Green
Write-Host ""
Write-Host "지금 시작:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "로그 확인:" -ForegroundColor Cyan
Write-Host "  Get-Content D:\Projects\Widget_Manager\scripts\task_runner.log -Tail 20"
