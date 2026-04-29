# -*- mode: python ; coding: utf-8 -*-

# EXCLUDE unused heavy modules to shrink size
EXCLUDED = [
    'PySide6.QtWidgets', 'PySide6.QtNetwork', 'PySide6.QtSql', 'PySide6.QtXml',
    'PySide6.QtWebEngine', 'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtQml',
    'PySide6.QtDesigner', 'PySide6.QtTest', 'tkinter', 'matplotlib', 'scipy'
]

a = Analysis(
    ['show.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'imageio',
        'imageio.plugins.pillow',
        'numpy',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDED,
    noarchive=False,
    optimize=1,
)

# Manually remove heavy DLLs we don't need
def dll_filter(name):
    kill_list = ['Qt6WebEngine', 'Qt6Network', 'Qt6Sql', 'Qt6Multimedia', 'Qt6Quick', 'Qt6Qml', 'Qt6Xml']
    return any(k.lower() in name.lower() for k in kill_list)

a.binaries = [x for x in a.binaries if not dll_filter(x[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='showcase',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Keep False for Windows
    upx=True,     # Use UPX if you have it installed to shrink even more
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['show.ico'],
)
