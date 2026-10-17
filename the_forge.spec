# THE FORGE  |  Copyright (c) 2026 Yannie D. Forest. All rights reserved.
# NO LICENCE IS GRANTED. No copying, adaptation, redistribution, reverse
# engineering or commercial use without the author's written permission.
# See LICENCE.txt. Every distributed copy carries a build marker.
# -*- mode: python ; coding: utf-8 -*-
#
# The Forge — the Windows program, built as a PROGRAM FOLDER that the
# installer (the_forge.iss) puts in place, not as one self-unpacking .exe.
#
#   Built on GitHub by .github/workflows/build-windows-app.yml. You do not run
#   this file yourself.
#
# 9s58: MADE THE WAY INKWELL 7.36 IS MADE. Inkwell's recipe is one PyInstaller
# command line (Inkwell's .github/workflows/windows.yml):
#
#     --noconfirm --clean --windowed --onedir --name Inkwell
#     --icon inkwell.ico --runtime-hook build/quiet_console.py
#     --add-data (the page and the two icons)
#     --collect-all webview --collect-all clr_loader --collect-all pythonnet
#
# This file gives the same result, line for line:
#   --windowed            console=False
#   --onedir              EXE(exclude_binaries=True) and COLLECT: a folder
#   --name, --icon        name=APP_NAME, icon='the_forge.ico'
#   --runtime-hook        runtime_hooks: quiet_console.py, Inkwell's own hook
#   --add-data            datas: the_forge.html and the two icons
#   --collect-all         collect_all for webview, clr_loader and pythonnet
#   --noconfirm --clean   given on the workflow's command line
#   (no packing)          upx=False: never packed with UPX (Inkwell's line
#                         asks for no UPX, and as far as I know GitHub's
#                         computer has none to use)
# and with PyInstaller's STANDARD starter (runw.exe from the pip wheel, the
# one inside Inkwell), not a starter compiled for each build.
#
# Kept from the Forge, and why:
#   - version details (publisher, product name, version, copyright), shown
#     under Properties, Details. Inkwell's program has none. Ordinary in
#     installed programs; the 9s58 study found no sign that they help or harm
#     an unsigned program, so they stay until a build shows otherwise.
#   - four hidden imports named outright (pywebview's Windows back ends and
#     clr). Inkwell names none of them and its window opens, so its three
#     --collect-all already bring them in; here they are only a safety net in
#     case that collection is ever skipped. They add nothing else.
#
# The folder must stay together: moved out of it on its own, the program
# stops with "Failed to load Python DLL ...\_internal\python3xx.dll". That is
# why it is installed by an installer that keeps the folder together and
# makes the Start menu entry, and is published only as that installer.

import os
import re

from PyInstaller.utils.hooks import collect_all

APP_NAME = 'The Forge'


# ---------------------------------------------------------------------------
# Version details, read from BUILD_INFO.txt ("Pass: 624", "Stamp: 9s56").
# A stamp like 9s56 and pass 624 give the version 9.56.624.0; any other stamp
# gives 1.0.<pass>.0. Windows allows at most 65535 in each part.
def _build_info():
    info = {}
    try:
        with open(os.path.join(SPECPATH, 'BUILD_INFO.txt'), encoding='utf-8') as fh:
            for line in fh:
                key, sep, val = line.partition(':')
                if sep:
                    info[key.strip().lower()] = val.strip()
    except OSError:
        pass
    return info


_info = _build_info()
_pass = int(re.sub(r'[^0-9]', '', _info.get('pass', '')) or 0)
_stamp = _info.get('stamp', '')
_m = re.match(r'^(\d+)s(\d+)$', _stamp)
_major, _minor = (int(_m.group(1)), int(_m.group(2))) if _m else (1, 0)
VERSION_NUMBERS = tuple(min(n, 65535) for n in (_major, _minor, _pass, 0))
VERSION_DOTTED = '.'.join(str(n) for n in VERSION_NUMBERS)
VERSION_LABEL = (_stamp or VERSION_DOTTED) + ((' (build %d)' % _pass) if _pass else '')


def _version_resource():
    """The Windows version details, or None where they cannot be made.

    The classes live in PyInstaller's Windows-only helpers, which import only
    on Windows; elsewhere PyInstaller ignores version details anyway.
    """
    try:
        from PyInstaller.utils.win32.versioninfo import (
            VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable,
            StringStruct, VarFileInfo, VarStruct)
    except Exception as _e:
        print('the_forge: no version details on this system (%s)' % _e)
        return None
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=VERSION_NUMBERS, prodvers=VERSION_NUMBERS),
        kids=[
            StringFileInfo([StringTable('040904B0', [
                StringStruct('CompanyName', 'Yannie D. Forest'),
                StringStruct('FileDescription', APP_NAME),
                StringStruct('FileVersion', VERSION_DOTTED),
                StringStruct('InternalName', 'the_forge'),
                StringStruct('LegalCopyright', 'Copyright (c) 2026 Yannie D. Forest. All rights reserved.'),
                StringStruct('OriginalFilename', APP_NAME + '.exe'),
                StringStruct('ProductName', APP_NAME),
                StringStruct('ProductVersion', VERSION_LABEL),
            ])]),
            VarFileInfo([VarStruct('Translation', [1033, 1200])]),
        ])


# ---------------------------------------------------------------------------
# Inkwell's three --collect-all: pywebview ships JavaScript files it loads
# FROM DISK while a window opens, and on Windows it reaches .NET through
# pythonnet, whose clr_loader carries native DLLs and runtime configuration of
# its own. collect_all gathers modules, data files AND binaries together.
# (9s58: proxy_tools is no longer collected whole. Inkwell does not collect
# it; pywebview imports it by name, so PyInstaller finds it anyway.)
extra_datas = []
extra_binaries = []
extra_hidden = []

for _pkg in ('webview', 'clr_loader', 'pythonnet'):
    try:
        _d, _b, _h = collect_all(_pkg)
        extra_datas += _d
        extra_binaries += _b
        extra_hidden += _h
    except Exception as _e:
        print('the_forge: nothing collected for %s (%s)' % (_pkg, _e))

a = Analysis(
    ['the_forge_app.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=[('the_forge.html', '.'), ('the_forge.ico', '.'), ('the_forge.png', '.')] + extra_datas,
    hiddenimports=[
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'webview.platforms.mshtml',
        'clr',
    ] + extra_hidden,
    hookspath=[],
    hooksconfig={},
    # Inkwell's quiet console hook. A windowed program has no standard
    # output; a stray print then goes to os.devnull instead of stopping the
    # program. Named by its full path, so the build works from any folder.
    runtime_hooks=[os.path.join(SPECPATH, 'quiet_console.py')],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# The program folder: dist\The Forge\The Forge.exe, with Python, the
# libraries and the_forge.html in dist\The Forge\_internal (PyInstaller 6's
# default). The program finds the page through sys._MEIPASS, which PyInstaller
# points at that folder.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='the_forge.ico',
    version=_version_resource(),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
