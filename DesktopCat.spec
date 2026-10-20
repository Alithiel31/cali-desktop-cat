# -*- mode: python ; coding: utf-8 -*-
# Définition du build de DesktopCat.exe (un seul fichier, sans console).
# Utilisation : python tools/make_version_file.py && pyinstaller DesktopCat.spec
# (le .spec lit build/version_info.txt, écrit par make_version_file.py).
# Partagé entre le build local et release.yml : ne pas dupliquer ces options ailleurs.


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DesktopCat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX augmente les faux positifs antivirus ; explicite pour ne pas dépendre de la machine
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='build/version_info.txt',
    icon=['assets/desktopcat.ico'],
)
