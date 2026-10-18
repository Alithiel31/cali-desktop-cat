"""Petites fenêtres flottantes autour du chat : bulle de dialogue, boîte cadeau, particules."""
from __future__ import annotations

import time

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QLabel, QWidget

from .sprite import GIFT_SIZE, draw_gift

_FLOATING = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
             | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)

BUBBLE_STYLE = ("QLabel{{background:#fffaf0;color:#2a1d18;border:2px solid {border};border-radius:10px;"
                "padding:6px 10px;font:600 13px 'Segoe UI';}}")


class Bubble(QLabel):
    """Bulle de dialogue. Un clic dessus la ferme."""
    clicked = Signal()

    def __init__(self):
        super().__init__(None, _FLOATING)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setMaximumWidth(280)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_border("#2a1d18")

    def set_border(self, color: str) -> None:
        self.setStyleSheet(BUBBLE_STYLE.format(border=color))

    def show_html(self, html: str, border: str = "#2a1d18") -> None:
        self.set_border(border)
        self.setText(html)
        self.adjustSize()
        self.show()

    def mousePressEvent(self, event):
        self.hide()
        self.clicked.emit()


class GiftBox(QWidget):
    """Boîte cadeau posée à côté du chat. Un clic l'ouvre."""
    clicked = Signal()

    def __init__(self, scale: int):
        super().__init__(None, _FLOATING)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.S = scale
        self.setFixedSize(GIFT_SIZE * scale, GIFT_SIZE * scale)
        self._t0 = time.monotonic()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)

    def set_scale(self, scale: int) -> None:
        self.S = scale
        self.setFixedSize(GIFT_SIZE * scale, GIFT_SIZE * scale)

    def showEvent(self, event):
        self._timer.start(120)

    def hideEvent(self, event):
        self._timer.stop()

    def paintEvent(self, event):
        p = QPainter(self)
        draw_gift(p, self.S, (time.monotonic() - self._t0) * 1000)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class FxLayer(QWidget):
    """Particules (cœurs, étoiles, « z »). Fenêtre plein écran transparente aux clics,
    visible seulement tant qu'il reste des particules."""
    COLORS = {"heart": "#ff5c8a", "star": "#ffd23f", "zzz": "#8fb8ff"}
    GLYPHS = {"heart": "♥", "star": "✦", "zzz": "z"}

    def __init__(self, area: QRect):
        super().__init__(None, _FLOATING | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setGeometry(area)
        self.particles: list[dict] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.enabled = True

    def set_area(self, area: QRect) -> None:
        self.setGeometry(area)

    def spawn(self, kind: str, gx: float, gy: float) -> None:
        """gx, gy : position globale (pixels logiques de l'écran)."""
        if not self.enabled:
            return
        life = 2.2 if kind == "zzz" else 1.4
        self.particles.append({"kind": kind, "x": gx - self.x(), "y": gy - self.y(), "born": time.monotonic(), "life": life})
        if not self.isVisible():
            self.show()
            self._timer.start(33)

    def clear(self) -> None:
        self.particles.clear()
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        now = time.monotonic()
        self.particles = [q for q in self.particles if now - q["born"] < q["life"]]
        if not self.particles:
            self._timer.stop()
            self.hide()
            return
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        font = QFont("Segoe UI Symbol", 16)
        font.setBold(True)
        p.setFont(font)
        now = time.monotonic()
        for q in self.particles:
            k = (now - q["born"]) / q["life"]
            col = QColor(self.COLORS[q["kind"]])
            col.setAlphaF(max(0.0, 1.0 - k * k))
            p.setPen(col)
            p.drawText(int(q["x"]), int(q["y"] - 46 * k), self.GLYPHS[q["kind"]])
        p.end()
