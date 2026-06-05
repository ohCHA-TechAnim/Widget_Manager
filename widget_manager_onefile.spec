# -*- mode: python ; coding: utf-8 -*-
# Widget Manager — PyInstaller 빌드 스펙 (단일 exe)
# 빌드: pyinstaller widget_manager_onefile.spec --clean

import os
from PyInstaller.utils.hooks import collect_all

# selenium 전체 수집
sel_datas, sel_binaries, sel_hiddenimports = collect_all('selenium')

# selenium 주요 의존 패키지도 수집
trio_datas, trio_binaries, trio_hiddenimports = collect_all('trio')
outcome_datas, outcome_binaries, outcome_hiddenimports = collect_all('outcome')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[] + sel_binaries + trio_binaries + outcome_binaries,
    datas=[
        ('theme/light.qss',  'theme'),
        ('theme/dark.qss',   'theme'),
        ('plugins',          'plugins'),
    ] + sel_datas + trio_datas + outcome_datas,
    hiddenimports=[
        'PyQt6.QtPrintSupport',
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.oxml.parser',
        'docx.parts',
        'docx.parts.document',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        'sniffio',
        'wsproto',
        'websocket',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
    ] + sel_hiddenimports + trio_hiddenimports + outcome_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

_icon = 'assets/app_icon.ico' if os.path.exists('assets/app_icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WidgetManager_v0.2.4_onefile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=_icon,
    onefile=True,
)
