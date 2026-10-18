"""Tout ce qui parle à Windows : fenêtres, inactivité, application active.

Sur un autre système, les fonctions renvoient des valeurs neutres (le module reste importable,
ce qui permet de tester la logique ailleurs que sous Windows).
Les coordonnées renvoyées sont en pixels PHYSIQUES : c'est à l'appelant de les convertir.
"""
from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from dataclasses import dataclass

IS_WIN = sys.platform == "win32"

SHELL_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}
IGNORED_CLASSES = SHELL_CLASSES | {"Windows.UI.Core.CoreWindow"}


@dataclass(frozen=True)
class WinInfo:
    hwnd: int
    title: str
    rect: tuple          # (gauche, haut, droite, bas) en pixels physiques
    zoomed: bool = False


@dataclass(frozen=True)
class Foreground:
    hwnd: int
    pid: int
    exe: str             # « firefox.exe », en minuscules
    title: str
    rect: tuple
    cls: str


if IS_WIN:
    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi
    kernel32 = ctypes.windll.kernel32
    # Pas de timeBeginPeriod(1) : il force toute la machine en minuterie 1 ms (batterie), et le PreciseTimer de Qt
    # suffit à la boucle du chat.

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    _H = wintypes.HWND
    user32.IsWindowVisible.argtypes = [_H]
    user32.IsIconic.argtypes = [_H]
    user32.IsZoomed.argtypes = [_H]
    user32.IsWindow.argtypes = [_H]
    user32.GetWindowLongW.argtypes = [_H, ctypes.c_int]
    user32.GetWindowRect.argtypes = [_H, ctypes.POINTER(RECT)]
    user32.GetWindowTextLengthW.argtypes = [_H]
    user32.GetWindowTextW.argtypes = [_H, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.argtypes = [_H, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [_H, ctypes.POINTER(wintypes.DWORD)]
    user32.GetForegroundWindow.restype = _H
    user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
    dwmapi.DwmGetWindowAttribute.argtypes = [_H, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    kernel32.GetTickCount.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                    ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    _EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, _H, wintypes.LPARAM)

    def _text(fn, hwnd, size):
        buf = ctypes.create_unicode_buffer(size)
        fn(hwnd, buf, size)
        return buf.value

    def _class(hwnd) -> str:
        return _text(user32.GetClassNameW, hwnd, 256)

    def _title(hwnd) -> str:
        return _text(user32.GetWindowTextW, hwnd, user32.GetWindowTextLengthW(hwnd) + 1)

    def _frame(hwnd):
        """Rectangle visible de la fenêtre (sans l'ombre invisible de Windows 10/11)."""
        r = RECT()
        if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) != 0:   # EXTENDED_FRAME_BOUNDS
            user32.GetWindowRect(hwnd, ctypes.byref(r))
        return (r.left, r.top, r.right, r.bottom)

    def _cloaked(hwnd) -> bool:
        v = wintypes.DWORD(0)
        dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(v), ctypes.sizeof(v))           # CLOAKED
        return v.value != 0

    def _exe_of_pid(pid: int) -> str:
        if not pid:
            return ""
        h = kernel32.OpenProcess(0x1000, False, pid)         # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(h)
        return ""

    def idle_seconds() -> float:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        return ((kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0

    def list_windows(exclude=()) -> list:
        """Fenêtres normales visibles, de la plus haute à la plus basse dans l'empilement.
        Les fenêtres maximisées sont incluses (marquées `zoomed`) car elles masquent celles du dessous."""
        exclude = set(exclude)
        found = []

        def cb(hwnd, _):
            if hwnd in exclude or not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                return True
            if user32.GetWindowLongW(hwnd, -20) & 0x80:                 # WS_EX_TOOLWINDOW
                return True
            if _cloaked(hwnd) or _class(hwnd) in IGNORED_CLASSES:
                return True
            title = _title(hwnd)
            if not title:
                return True
            rect = _frame(hwnd)
            if rect[2] - rect[0] < 250 or rect[3] - rect[1] < 120:
                return True
            found.append(WinInfo(int(hwnd), title, rect, bool(user32.IsZoomed(hwnd))))
            return True

        user32.EnumWindows(_EnumProc(cb), 0)
        return found

    def window_rect(hwnd: int):
        """Rectangle de la fenêtre, ou None si elle a disparu, est réduite, maximisée ou masquée."""
        if not hwnd or not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return None
        if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd) or _cloaked(hwnd):
            return None
        return _frame(hwnd)

    def foreground():
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return Foreground(int(hwnd), int(pid.value), _exe_of_pid(pid.value), _title(hwnd), _frame(hwnd), _class(hwnd))

else:
    def idle_seconds() -> float:
        return 0.0

    def list_windows(exclude=()) -> list:
        return []

    def window_rect(hwnd: int):
        return None

    def foreground():
        return None


def fullscreen_monitor(fg, monitor_rects):
    """Indice de l'écran entièrement couvert par la fenêtre active, ou None."""
    for i, rect in enumerate(monitor_rects):
        if is_fullscreen(fg, rect):
            return i
    return None


def is_fullscreen(fg, monitor_rect) -> bool:
    """Vrai si la fenêtre active couvre tout l'écran (jeu, vidéo plein écran) et n'est pas le bureau."""
    if fg is None or fg.cls in SHELL_CLASSES or fg.pid == os.getpid():
        return False
    l, t, r, b = fg.rect
    ml, mt, mr, mb = monitor_rect
    return l <= ml and t <= mt and r >= mr and b >= mb
