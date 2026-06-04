<#
.SYNOPSIS
  Widget Manager 배포 빌드 스크립트

.DESCRIPTION
  1. PyInstaller 설치 확인
  2. 아이콘 생성 (assets/app_icon.ico)
  3. 폴더형 빌드 → dist\WidgetManager\WidgetManager.exe
  4. -OneFile 지정 시 단일 exe 추가 빌드 → dist\WidgetManager_v0.2.1_onefile.exe

.PARAMETER Clean
  이전 빌드 캐시를 제거하고 처음부터 빌드한다.

.PARAMETER OneFile
  단일 exe (onefile)도 함께 빌드한다.

.EXAMPLE
  .\build.ps1                    # 폴더형 증분 빌드
  .\build.ps1 -Clean             # 폴더형 클린 빌드
  .\build.ps1 -Clean -OneFile    # 폴더형 + 단일형 클린 빌드
#>
param(
    [switch]$Clean,
    [switch]$OneFile
)

$ErrorActionPreference = 'Stop'
$StartTime = Get-Date
$totalSteps = if ($OneFile) { 4 } else { 3 }

function Write-Step([string]$msg) {
    Write-Host "`n[$([int]($script:step++))/$totalSteps] $msg" -ForegroundColor Cyan
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

# ── 3. 폴더형 빌드 ─────────────────────────────────────────────────────────
Write-Step "폴더형(onedir) 빌드 중..."
if ($Clean) {
    Write-Host "  --clean 옵션으로 클린 빌드 실행"
    py -3 -m PyInstaller --clean -y widget_manager.spec
} else {
    py -3 -m PyInstaller -y widget_manager.spec
}
if ($LASTEXITCODE -ne 0) { Write-Error "폴더형 빌드 실패"; exit 1 }

# ── 4. 단일형 빌드 (선택) ──────────────────────────────────────────────────
if ($OneFile) {
    Write-Step "단일 exe(onefile) 빌드 중..."
    if ($Clean) {
        py -3 -m PyInstaller --clean -y widget_manager_onefile.spec
    } else {
        py -3 -m PyInstaller -y widget_manager_onefile.spec
    }
    if ($LASTEXITCODE -ne 0) { Write-Error "단일형 빌드 실패"; exit 1 }
}

# ── 완료 보고 ──────────────────────────────────────────────────────────────
$elapsed = [int]((Get-Date) - $StartTime).TotalSeconds
$exePath  = Join-Path $PSScriptRoot "dist\WidgetManager\WidgetManager.exe"
$distSize = if (Test-Path "dist\WidgetManager") {
    "{0:N1} MB" -f ((Get-ChildItem "dist\WidgetManager" -Recurse | Measure-Object Length -Sum).Sum / 1MB)
} else { "?" }

Write-Host ""
Write-Host "=============================" -ForegroundColor Magenta
Write-Host " 빌드 성공!  (${elapsed}초)" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Magenta
Write-Host "폴더형 실행 파일 : $exePath"
Write-Host "폴더형 배포 크기 : $distSize  (dist\WidgetManager\ 전체)"
if ($OneFile) {
    $onefileSize = if (Test-Path "dist\WidgetManager_v0.2.1_onefile.exe") {
        "{0:N1} MB" -f ((Get-Item "dist\WidgetManager_v0.2.1_onefile.exe").Length / 1MB)
    } else { "?" }
    Write-Host "단일형 실행 파일 : dist\WidgetManager_v0.2.1_onefile.exe"
    Write-Host "단일형 크기      : $onefileSize"
}
Write-Host ""
