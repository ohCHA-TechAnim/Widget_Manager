<#
.SYNOPSIS
  Widget Manager 배포 빌드 스크립트

.DESCRIPTION
  1. PyInstaller 설치 확인
  2. 아이콘 생성 (assets/app_icon.ico)
  3. PyInstaller 빌드 → dist\WidgetManager\WidgetManager.exe

.PARAMETER Clean
  이전 빌드 캐시를 제거하고 처음부터 빌드한다.

.EXAMPLE
  .\build.ps1          # 증분 빌드 (빠름)
  .\build.ps1 -Clean   # 클린 빌드
#>
param([switch]$Clean)

$ErrorActionPreference = 'Stop'
$StartTime = Get-Date

function Write-Step([string]$msg) {
    Write-Host "`n[$([int]($script:step++))/3] $msg" -ForegroundColor Cyan
}
$script:step = 1

Set-Location $PSScriptRoot
Write-Host "=== Widget Manager 빌드 ===" -ForegroundColor Magenta
Write-Host "작업 디렉터리: $PSScriptRoot"

# ── 1. PyInstaller 확인 / 설치 ─────────────────────────────────────────────
Write-Step "PyInstaller 확인 중..."
$piVersion = py -3 -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
if (-not $piVersion) {
    Write-Host "PyInstaller 미설치 — pip으로 설치합니다." -ForegroundColor Yellow
    py -3 -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller 설치 실패"; exit 1 }
    $piVersion = py -3 -c "import PyInstaller; print(PyInstaller.__version__)"
}
Write-Host "PyInstaller $piVersion 준비됨" -ForegroundColor Green

# ── 2. 아이콘 생성 ─────────────────────────────────────────────────────────
Write-Step "아이콘 생성 중 (assets/app_icon.ico)..."
py -3 make_icon.py
if ($LASTEXITCODE -ne 0) { Write-Error "아이콘 생성 실패"; exit 1 }

# ── 3. PyInstaller 빌드 ─────────────────────────────────────────────────────
Write-Step "PyInstaller 빌드 중..."
if ($Clean) {
    Write-Host "  --clean 옵션으로 클린 빌드 실행"
    py -3 -m PyInstaller --clean widget_manager.spec
} else {
    py -3 -m PyInstaller widget_manager.spec
}
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller 빌드 실패"; exit 1 }

# ── 완료 보고 ──────────────────────────────────────────────────────────────
$elapsed = [int]((Get-Date) - $StartTime).TotalSeconds
$exePath  = Join-Path $PSScriptRoot "dist\WidgetManager\WidgetManager.exe"
$distSize = if (Test-Path "dist\WidgetManager") {
    "{0:N0} MB" -f ((Get-ChildItem "dist\WidgetManager" -Recurse | Measure-Object Length -Sum).Sum / 1MB)
} else { "?" }

Write-Host ""
Write-Host "=============================" -ForegroundColor Magenta
Write-Host " 빌드 성공!  (${elapsed}초)" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Magenta
Write-Host "실행 파일 : $exePath"
Write-Host "배포 크기 : $distSize  (dist\WidgetManager\ 전체)"
Write-Host ""
Write-Host "배포 방법:"
Write-Host "  dist\WidgetManager\ 폴더 전체를 압축해 배포하세요."
Write-Host "  실행: dist\WidgetManager\WidgetManager.exe"
