"""Petites fenêtres flottantes autour du chat : bulle de dialogue, boîte cadeau, particules."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPalette, QPen, QTextDocument
from PySide6.QtGui import QAbstractTextDocumentLayout
from PySide6.QtWidgets import QWidget

from .sprite import GIFT_SIZE, draw_gift

_FLOATING = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
             | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)

BUBBLE_BG, BUBBLE_FG, BUBBLE_BORDER = "#fffaf0", "#2a1d18", "#2a1d18"


class Bubble(QWidget):
    """Bulle de dialogue, dessinée à la main (une QLabel à fond translucide n'affiche pas son fond : le texte sombre
    se retrouvait sans rien derrière lui). La police suit la taille du chat. Un clic dessus la ferme."""
    clicked = Signal()

    BORDER, PAD_X, PAD_Y, RADIUS, TAIL = 3, 14, 9, 14, 9

    def __init__(self, scale: int = 4):
        super().__init__(None, _FLOATING)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.S = scale
        self._html = ""
        self._border = QColor(BUBBLE_BORDER)
        self._tail_x: float | None = None          # abscisse de la pointe dans la bulle ; None = au milieu
        self._doc = QTextDocument(self)
        self._doc.setDocumentMargin(0)
        self._doc.setDefaultStyleSheet(f"body {{ color: {BUBBLE_FG}; }}")
        self._apply_font()

    @property
    def font_px(self) -> int:
        """Taille du texte en pixels : 16 px pour un chat à l'échelle 4, plus grand si le chat l'est."""
        return round(11 + 1.25 * self.S)

    def _apply_font(self) -> None:
        f = QFont("Segoe UI")
        f.setPixelSize(self.font_px)
        f.setWeight(QFont.Weight.DemiBold)
        self._doc.setDefaultFont(f)

    def set_scale(self, scale: int) -> None:
        if scale == self.S:
            return
        self.S = scale
        self._apply_font()
        if self._html:
            self._relayout()

    def set_border(self, color: str) -> None:
        self._border = QColor(color)
        self.update()

    def text(self) -> str:
        return self._html

    @property
    def tail_x(self) -> float:
        """Abscisse de la pointe (dans la bulle), gardée à l'écart des coins arrondis."""
        margin = self.BORDER + self.RADIUS + self.TAIL
        x = self.width() / 2 if self._tail_x is None else self._tail_x
        return max(margin, min(self.width() - margin, x))

    def set_tail_x(self, x: float) -> None:
        """Fait viser la pointe vers x (dans la bulle) : utile quand la bulle est décalée pour rester sur l'écran."""
        if self._tail_x is None or abs(self._tail_x - x) >= 0.5:
            self._tail_x = x
            self.update()

    def show_html(self, html: str, border: str = BUBBLE_BORDER) -> None:
        self._html = html
        self._border = QColor(border)
        self._relayout()
        self.show()

    def _relayout(self) -> None:
        doc = self._doc
        doc.setHtml(f'<span style="color:{BUBBLE_FG}">{self._html}</span>')   # couleur explicite, quel que soit le thème
        doc.setTextWidth(-1)
        text_w = min(doc.idealWidth(), 20.0 * self.font_px) + 1       # +1 : évite un retour à la ligne de trop
        doc.setTextWidth(text_w)
        size = doc.size()
        m = self.BORDER
        self.setFixedSize(math.ceil(size.width()) + 2 * (m + self.PAD_X),
                          math.ceil(size.height()) + 2 * (m + self.PAD_Y) + self.TAIL)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        b = self.BORDER
        w, h = self.width(), self.height() - self.TAIL
        body = QPainterPath()
        body.addRoundedRect(QRectF(b / 2, b / 2, w - b, h - b), self.RADIUS, self.RADIUS)
        tail = QPainterPath()                                          # petite pointe vers le chat
        cx = self.tail_x
        tail.moveTo(cx - self.TAIL, h - b / 2 - 1)
        tail.lineTo(cx, h + self.TAIL - b / 2)
        tail.lineTo(cx + self.TAIL, h - b / 2 - 1)
        tail.closeSubpath()
        shape = body.united(tail)
        p.setPen(QPen(self._border, b, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(QColor(BUBBLE_BG))
        p.drawPath(shape)
        p.translate(b + self.PAD_X, b + self.PAD_Y)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette.setColor(QPalette.ColorRole.Text, QColor(BUBBLE_FG))     # sinon : couleur du thème Windows (blanc en mode sombre)
        ctx.palette.setColor(QPalette.ColorRole.WindowText, QColor(BUBBLE_FG))
        self._doc.documentLayout().draw(p, ctx)
        p.end()

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
