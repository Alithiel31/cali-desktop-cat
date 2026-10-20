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

# Styles étendus (GetWindowLongW(hwnd, GWL_EXSTYLE))
WS_EX_TRANSPARENT = 0x00000020      # les clics passent au travers : overlay (Steam, NVIDIA, Discord...)
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000       # ne peut pas devenir la fenêtre active : overlay, notification, clavier visuel
LWA_ALPHA = 0x2


def is_ghost_window(exstyle: int, layered_alpha: int | None = None) -> bool:
    """Vrai pour une fenêtre sur laquelle le chat ne doit pas se percher : invisible à l'œil ou sans « vrai » bord
    (overlay transparent aux clics, fenêtre outil, fenêtre impossible à activer, fenêtre superposée d'opacité nulle).
    `layered_alpha` : opacité réglée par SetLayeredWindowAttributes, ou None si elle est inconnue."""
    if exstyle & (WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE):
        return True
    return bool(exstyle & WS_EX_LAYERED) and layered_alpha == 0


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
    user32.GetWindowTextW.argtypes = [_H, wintypes.LPWSTR, ctypes.c_int]
    user32.InternalGetWindowText.argtypes = [_H, wintypes.LPWSTR, ctypes.c_int]
    user32.GetLayeredWindowAttributes.argtypes = [_H, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.c_ubyte),
                                                  ctypes.POINTER(wintypes.DWORD)]
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
        # InternalGetWindowText lit le titre sans envoyer de message à la fenêtre : GetWindowTextLength, lui, en
        # envoie un, et une fenêtre qui « ne répond pas » pourrait geler la boucle du chat.
        return _text(user32.InternalGetWindowText, hwnd, 512)

    def _layered_alpha(hwnd):
        """Opacité d'une fenêtre superposée (0 à 255), ou None si elle n'est pas réglée de cette façon."""
        key, alpha, flags = wintypes.DWORD(0), ctypes.c_ubyte(255), wintypes.DWORD(0)
        if not user32.GetLayeredWindowAttributes(hwnd, ctypes.byref(key), ctypes.byref(alpha), ctypes.byref(flags)):
            return None
        return alpha.value if flags.value & LWA_ALPHA else None

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
            exstyle = user32.GetWindowLongW(hwnd, -20) & 0xFFFFFFFF      # GWL_EXSTYLE
            alpha = _layered_alpha(hwnd) if exstyle & WS_EX_LAYERED else None
            if is_ghost_window(exstyle, alpha):
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
    left, top, right, bottom = fg.rect
    ml, mt, mr, mb = monitor_rect
    return left <= ml and top <= mt and right >= mr and bottom >= mb
