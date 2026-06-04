# -*- mode: python ; coding: utf-8 -*-
# Widget Manager — PyInstaller 빌드 스펙
# 빌드: python make_icon.py && pyinstaller widget_manager.spec --clean

import os

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # QSS 테마 파일
        ('theme/light.qss',  'theme'),
        ('theme/dark.qss',   'theme'),
        # 플러그인 디렉터리 (런타임 임포트용 .py 파일 포함)
        ('plugins',          'plugins'),
    ],
    hiddenimports=[
        # PyQt6 — 프린트 지원 (python-docx에서 간접 참조 가능)
        'PyQt6.QtPrintSupport',
        # python-docx 서브모듈 (auto-hook이 놓칠 수 있는 것)
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.oxml.parser',
        'docx.parts',
        'docx.parts.document',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        # selenium (PyInstaller auto-hook이 놓치는 서브모듈)
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        # trio / trio-websocket (selenium 비동기 의존성)
        'trio',
        'trio_websocket',
        # openpyxl
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 아이콘 파일이 없으면 None으로 폴백
_icon = 'assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WidgetManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # --windowed: 콘솔 창 없음
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WidgetManager',   # dist/WidgetManager/ 폴더에 생성
)
