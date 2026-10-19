"""Mini-test Desktop Cat (Python + pywebview), Windows uniquement.

    pip install pywebview
    python spike.py            # le chat se perche sur tes fenêtres
    python spike.py --floor    # le chat reste au bas de l'écran (test de fluidité seul)
    python spike.py --debug    # dessine un cadre rouge autour de la fenêtre invisible

Clic droit sur le chat = quitter (ou Ctrl+C dans la console).

Ce que le test vérifie :
  1. la fenêtre est-elle vraiment transparente (aucun rectangle derrière le chat) ?
  2. le déplacement par window.move() est-il fluide (voir "mises à jour/s" dans la console) ?
  3. Python voit-il tes fenêtres, et le chat marche-t-il sur leur bord supérieur ?
"""
import ctypes
import sys
import time
from ctypes import wintypes

if sys.platform != "win32":
    sys.exit("Ce test ne tourne que sous Windows.")

# DPI : sans ça, les coordonnées sont fausses avec une mise à l'échelle de 125 % ou 150 %.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import webview  # noqa: E402

TITLE = "DesktopCatSpike"
CAT_W = CAT_H = 160
FEET_FRAC = 5 / 32      # part transparente sous les pattes dans le dessin
SPEED = 3               # pixels par image
FPS = 60
DEBUG = "--debug" in sys.argv
FLOOR_ONLY = "--floor" in sys.argv

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
try:
    ctypes.windll.winmm.timeBeginPeriod(1)  # précision du sleep() à 1 ms
except Exception:
    pass


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


H = wintypes.HWND
user32.IsWindowVisible.argtypes = [H]
user32.IsIconic.argtypes = [H]
user32.IsZoomed.argtypes = [H]
user32.GetWindowLongW.argtypes = [H, ctypes.c_int]
user32.GetWindowRect.argtypes = [H, ctypes.POINTER(RECT)]
user32.GetWindowTextLengthW.argtypes = [H]
user32.GetWindowTextW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = H
user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
dwmapi.DwmGetWindowAttribute.argtypes = [H, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, H, wintypes.LPARAM)
IGNORED_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
                   "Windows.UI.Core.CoreWindow"}


def frame_rect(hwnd):
    """Rectangle visible de la fenêtre (sans l'ombre invisible de Windows 10/11)."""
    r = RECT()
    if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) != 0:
        user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r


def is_cloaked(hwnd):
    v = wintypes.DWORD(0)
    dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(v), ctypes.sizeof(v))
    return v.value != 0


def text_of(fn, hwnd, size):
    buf = ctypes.create_unicode_buffer(size)
    fn(hwnd, buf, size)
    return buf.value


def perchable_windows(own_hwnd):
    """Fenêtres visibles, de la plus haute à la plus basse dans l'ordre d'empilement."""
    found = []

    def cb(hwnd, _):
        if hwnd == own_hwnd or not user32.IsWindowVisible(hwnd):
            return True
        if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
            return True
        if user32.GetWindowLongW(hwnd, -20) & 0x80:          # WS_EX_TOOLWINDOW
            return True
        if is_cloaked(hwnd) or text_of(user32.GetClassNameW, hwnd, 256) in IGNORED_CLASSES:
            return True
        title = text_of(user32.GetWindowTextW, hwnd, user32.GetWindowTextLengthW(hwnd) + 1)
        if not title:
            return True
        r = frame_rect(hwnd)
        if r.right - r.left < 250 or r.bottom - r.top < 120:
            return True
        found.append((hwnd, title, r))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return found


def work_area():
    r = RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
    return r


HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent;overflow:hidden}
canvas{display:block;image-rendering:pixelated;%DEBUG%}
</style></head><body>
<canvas id="c" width="32" height="32" style="width:%SIZE%px;height:%SIZE%px"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');let dir=1,f=0;
function setDir(d){dir=d;draw()}
function r(px,py,w,h,col){x.fillStyle=col;x.fillRect(dir>0?px:32-px-w,py,w,h)}
function draw(){
  x.clearRect(0,0,32,32);
  const out='#2a1d18',base='#8c7552',face='#e0b072';
  r(2,9,4,10,out); r(5,13,18,10,out); r(19,8,10,11,out);          // contours
  [7,11,16,20].forEach((lx,i)=>{const up=(i+f)%2; r(lx-1,22,4,up?3:5,out)});
  r(3,10,2,8,base); r(6,14,16,8,base); r(20,9,8,9,face);          // queue, corps, tête
  r(20,6,2,3,face); r(26,6,2,3,face);                              // oreilles
  [7,11,16,20].forEach((lx,i)=>{const up=(i+f)%2; r(lx,22,2,up?2:4,base)});
  r(9,15,4,3,'#d08c4a'); r(15,17,4,3,'#d08c4a'); r(3,10,2,2,'#1e1a18');
  r(25,12,1,2,'#241a1a'); r(27,15,1,1,'#f08aa4');
}
setInterval(()=>{f^=1;draw()},180); draw();
document.oncontextmenu=e=>{e.preventDefault();pywebview.api.quit()};
</script></body></html>"""


class Api:
    def quit(self):
        win.destroy()


win = None


def run(window):
    time.sleep(1.0)
    hwnd = user32.FindWindowW(None, TITLE)
    if not hwnd:
        print("[erreur] fenêtre introuvable : impossible de lire sa position.")
        return

    # Calibrage : pywebview applique-t-il lui-même la mise à l'échelle de l'écran ?
    window.move(200, 200)
    time.sleep(0.3)
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    real_w, real_h = r.right - r.left, r.bottom - r.top
    scale = (r.left / 200.0) if r.left > 0 else 1.0
    print(f"[init] taille demandée {CAT_W}x{CAT_H} -> réelle {real_w}x{real_h} ; "
          f"échelle de move() ≈ {scale:.2f}")

    wa = work_area()
    feet = real_h * FEET_FRAC
    x = float(wa.left + 200)
    y = float(wa.bottom - real_h + feet)
    vy, d = 0.0, 1
    perch, perch_title = None, ""
    last_scan = last_report = 0.0
    frames = 0

    while True:
        t0 = time.perf_counter()
        now = time.time()

        if now - last_scan > 0.25:                       # on relit les fenêtres 4 fois/s
            last_scan = now
            perch = None
            if not FLOOR_ONLY:
                for _hwnd, title, rc in perchable_windows(hwnd):
                    if rc.top - (real_h - feet) >= wa.top:   # assez de place au-dessus
                        perch, perch_title = rc, title
                        break

        left, right, surface = (perch.left, perch.right, perch.top) if perch else (wa.left, wa.right, wa.bottom)
        ground = surface - real_h + feet

        x += d * SPEED
        if x <= left:
            x, d = float(left), 1
            window.evaluate_js("setDir(1)")
        elif x >= right - real_w:
            x, d = float(right - real_w), -1
            window.evaluate_js("setDir(-1)")

        if y < ground:                                   # chute libre (fenêtre fermée ou déplacée)
            vy += 0.8
            y = min(ground, y + vy)
        else:                                            # la surface a monté : on remonte vite
            vy = 0.0
            y = max(ground, y - 25)

        try:
            window.move(int(x / scale), int(y / scale))
        except Exception as e:  # fenêtre en cours de fermeture
            print("[stop]", e)
            return
        frames += 1

        if now - last_report >= 2:
            if last_report:
                where = f"sur « {perch_title[:40]} »" if perch else "au bas de l'écran"
                print(f"[move] {frames / (now - last_report):5.1f} mises à jour/s | chat {where}")
            frames, last_report = 0, now

        time.sleep(max(0.0, 1 / FPS - (time.perf_counter() - t0)))


if __name__ == "__main__":
    html = HTML.replace("%SIZE%", str(CAT_W)).replace(
        "%DEBUG%", "outline:1px dashed red;" if DEBUG else "")
    options = dict(html=html, width=CAT_W, height=CAT_H, x=100, y=100, frameless=True,
                   easy_drag=False, transparent=True, on_top=True, resizable=False,
                   shadow=False, js_api=Api())
    try:
        win = webview.create_window(TITLE, **options)
    except TypeError:            # anciennes versions de pywebview : pas de paramètre "shadow"
        options.pop("shadow")
        win = webview.create_window(TITLE, **options)
    webview.start(run, win)
