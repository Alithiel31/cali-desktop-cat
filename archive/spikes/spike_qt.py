"""Mini-test Desktop Cat n°2 (Python + PySide6), Windows uniquement.

    pip install PySide6-Essentials
    python spike_qt.py            # le chat se perche sur tes fenêtres
    python spike_qt.py --floor    # le chat reste au bas de l'écran
    python spike_qt.py --debug    # cadre rouge autour de la fenêtre (pour voir sa taille)

Clic droit sur le chat = quitter (ou Ctrl+C dans la console).

Différence avec spike.py : le chat est dessiné directement par Qt (pas de page web),
dans une fenêtre sans bordure à fond translucide. Aucun rectangle ne doit apparaître.
"""
import ctypes
import sys
import time
from ctypes import wintypes

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

GRID = 32                 # le chat est dessiné sur une grille de 32 x 32
SCALE = 5                 # taille d'un "pixel" du pixel art à l'écran
SIZE = GRID * SCALE       # 160 px
FEET = 5 * SCALE          # marge transparente sous les pattes
SPEED = 3                 # pixels par image
FPS = 60
DEBUG = "--debug" in sys.argv
FLOOR_ONLY = "--floor" in sys.argv

OUTLINE, BASE, FACE, PATCH, TIP = "#2a1d18", "#8c7552", "#e0b072", "#d08c4a", "#1e1a18"
EYE, NOSE = "#241a1a", "#f08aa4"
LEGS_X = (7, 11, 16, 20)

# ───────────────────────── API Windows : lister les fenêtres ─────────────────────────
WIN = sys.platform == "win32"
if WIN:
    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)   # sleep/timers précis à 1 ms
    except Exception:
        pass

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    H = wintypes.HWND
    user32.IsWindowVisible.argtypes = [H]
    user32.IsIconic.argtypes = [H]
    user32.IsZoomed.argtypes = [H]
    user32.IsWindow.argtypes = [H]
    user32.GetWindowLongW.argtypes = [H, ctypes.c_int]
    user32.GetWindowRect.argtypes = [H, ctypes.POINTER(RECT)]
    user32.GetWindowTextLengthW.argtypes = [H]
    user32.GetWindowTextW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
    dwmapi.DwmGetWindowAttribute.argtypes = [H, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, H, wintypes.LPARAM)
    IGNORED_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
                       "Windows.UI.Core.CoreWindow"}

    def _text(fn, hwnd, size):
        buf = ctypes.create_unicode_buffer(size)
        fn(hwnd, buf, size)
        return buf.value

    def _frame_rect(hwnd):
        """Rectangle visible (sans l'ombre invisible des fenêtres Windows 10/11)."""
        r = RECT()
        if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) != 0:
            user32.GetWindowRect(hwnd, ctypes.byref(r))
        return r

    def _cloaked(hwnd):
        v = wintypes.DWORD(0)
        dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(v), ctypes.sizeof(v))
        return v.value != 0

    def perchable_windows(own_hwnd):
        """Fenêtres visibles, de la plus haute à la plus basse dans l'empilement.
        Retourne [(hwnd, titre, (gauche, haut, droite, bas) en pixels physiques)]."""
        found = []

        def cb(hwnd, _):
            if hwnd == own_hwnd or not user32.IsWindowVisible(hwnd):
                return True
            if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
                return True
            if user32.GetWindowLongW(hwnd, -20) & 0x80:             # WS_EX_TOOLWINDOW
                return True
            if _cloaked(hwnd) or _text(user32.GetClassNameW, hwnd, 256) in IGNORED_CLASSES:
                return True
            title = _text(user32.GetWindowTextW, hwnd, user32.GetWindowTextLengthW(hwnd) + 1)
            if not title:
                return True
            r = _frame_rect(hwnd)
            if r.right - r.left < 250 or r.bottom - r.top < 120:
                return True
            found.append((hwnd, title, (r.left, r.top, r.right, r.bottom)))
            return True

        user32.EnumWindows(EnumProc(cb), 0)
        return found
else:
    def perchable_windows(own_hwnd):
        return []


# ───────────────────────── Le chat ─────────────────────────
class Cat(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                            | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(SIZE, SIZE)

        screen = QGuiApplication.primaryScreen()
        self.dpr = screen.devicePixelRatio()          # pixels physiques par pixel logique
        self.work = screen.availableGeometry()        # zone utile (hors barre des tâches), en pixels logiques

        self.x = float(self.work.left() + 200)
        self.y = float(self.work.bottom() - SIZE + FEET)
        self.vy = 0.0
        self.dir = 1
        self.frame = 0
        self.perch = None            # (hwnd, titre, rect logique)
        self.perch_hwnd = None
        self.last_scan = 0.0
        self.last_report = time.time()
        self.frames = 0

        self.move(int(self.x), int(self.y))
        self.show()
        self.hwnd = int(self.winId())
        print(f"[init] fenêtre {self.width()}x{self.height()} (logique), échelle écran ×{self.dpr:.2f}, "
              f"zone utile {self.work.width()}x{self.work.height()}")

        self.step_timer = QTimer(self)
        self.step_timer.setTimerType(Qt.PreciseTimer)
        self.step_timer.timeout.connect(self.step)
        self.step_timer.start(int(1000 / FPS))

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.toggle_frame)
        self.anim_timer.start(180)

    # --- dessin
    def toggle_frame(self):
        self.frame ^= 1
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        def r(px, py, w, h, color):
            x = px if self.dir > 0 else GRID - px - w
            p.fillRect(QRect(x * SCALE, py * SCALE, w * SCALE, h * SCALE), QColor(color))

        f = self.frame
        r(2, 9, 4, 10, OUTLINE); r(5, 13, 18, 10, OUTLINE); r(19, 8, 10, 11, OUTLINE)
        for i, lx in enumerate(LEGS_X):
            r(lx - 1, 22, 4, 3 if (i + f) % 2 else 5, OUTLINE)
        r(3, 10, 2, 8, BASE); r(6, 14, 16, 8, BASE); r(20, 9, 8, 9, FACE)
        r(20, 6, 2, 3, FACE); r(26, 6, 2, 3, FACE)
        for i, lx in enumerate(LEGS_X):
            r(lx, 22, 2, 2 if (i + f) % 2 else 4, BASE)
        r(9, 15, 4, 3, PATCH); r(15, 17, 4, 3, PATCH); r(3, 10, 2, 2, TIP)
        r(25, 12, 1, 2, EYE); r(27, 15, 1, 1, NOSE)

        if DEBUG:
            p.setPen(QPen(QColor("red"), 1, Qt.DashLine))
            p.drawRect(0, 0, self.width() - 1, self.height() - 1)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            QApplication.quit()

    # --- logique
    def scan_windows(self):
        self.perch = None
        if FLOOR_ONLY:
            return
        top_room = SIZE - FEET                                   # hauteur du chat au-dessus de ses pattes
        candidates = []
        for hwnd, title, (l, t, rr, b) in perchable_windows(self.hwnd):
            rect = (l / self.dpr, t / self.dpr, rr / self.dpr, b / self.dpr)
            if rect[1] - top_room >= self.work.top():            # assez de place au-dessus
                candidates.append((hwnd, title, rect))
        for c in candidates:                                     # on reste sur la même fenêtre si possible
            if c[0] == self.perch_hwnd:
                self.perch = c
                return
        if candidates:
            self.perch = candidates[0]
            self.perch_hwnd = self.perch[0]

    def step(self):
        now = time.time()
        if now - self.last_scan > 0.25:
            self.last_scan = now
            self.scan_windows()

        if self.perch:
            left, surface, right = self.perch[2][0], self.perch[2][1], self.perch[2][2]
        else:
            left, surface, right = self.work.left(), self.work.bottom() + 1, self.work.right() + 1
        ground = surface - SIZE + FEET

        self.x += self.dir * SPEED
        if self.x <= left:
            self.x, self.dir = float(left), 1
            self.update()
        elif self.x >= right - SIZE:
            self.x, self.dir = float(right - SIZE), -1
            self.update()

        if self.y < ground:                                      # chute libre
            self.vy += 0.8
            self.y = min(ground, self.y + self.vy)
        else:                                                    # surface plus haute : on remonte
            self.vy = 0.0
            self.y = max(ground, self.y - 25)

        self.move(int(self.x), int(self.y))
        self.frames += 1

        if now - self.last_report >= 2:
            where = f"sur « {self.perch[1][:40]} »" if self.perch else "au bas de l'écran"
            print(f"[move] {self.frames / (now - self.last_report):5.1f} mises à jour/s | chat {where}", flush=True)
            self.frames, self.last_report = 0, now


if __name__ == "__main__":
    if not WIN:
        sys.exit("Ce test ne tourne que sous Windows.")
    app = QApplication(sys.argv)
    cat = Cat()
    sys.exit(app.exec())
