"""Panneau de contrôle : garde-robe, concentration, statistiques, réglages."""
from __future__ import annotations

import time
from datetime import date, timedelta

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget, QGroupBox)

from .hats import HATS, RARITIES, RARITY_ORDER
from .sprite import FURS, render_pixmap

ACCENT, GREEN, MUTED, LINE, CARD, BG = "#ffb454", "#6fd3a0", "#9aa4b8", "#3a4258", "#2a3040", "#1f2430"

STYLE = f"""
QWidget {{ background: {BG}; color: #eef1f7; font: 13px 'Segoe UI'; }}
QTabWidget::pane {{ border: 0; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 14px; border-radius: 8px; }}
QTabBar::tab:selected {{ background: {CARD}; color: #eef1f7; font-weight: 700; }}
QPushButton {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 8px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #666d7e; }}
QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: #2a1d18; font-weight: 700; }}
QLineEdit, QSpinBox, QComboBox {{ background: #171b25; border: 1px solid {LINE}; border-radius: 8px; padding: 5px 8px; }}
QFrame#card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 12px; }}
QFrame#card QLabel {{ background: transparent; }}
QScrollArea {{ border: 0; }}
QLabel#muted {{ color: {MUTED}; }}
"""


def fmt_minutes(sec: float) -> str:
    m = round(sec / 60)
    return f"{m // 60} h {m % 60:02d}" if m >= 60 else f"{m} min"


def fmt_app(exe: str) -> str:
    name = exe[:-4] if exe.endswith(".exe") else exe
    return (name or "inconnu").capitalize()


class WeekChart(QWidget):
    """7 derniers jours : temps devant l'écran (orange) et temps de concentration (vert)."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(170)
        self.days: list[tuple[str, float, float]] = []

    def set_days(self, days) -> None:
        self.days = days
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.days:
            return
        top, bottom = 8, self.height() - 34
        peak = max(3600.0, *(d[1] for d in self.days))
        col_w = self.width() / len(self.days)
        small = QFont("Segoe UI", 8)
        p.setFont(small)
        for i, (label, active, focus) in enumerate(self.days):
            x = i * col_w + col_w * 0.18
            w = col_w * 0.64 / 2
            for j, (val, color) in enumerate(((active, ACCENT), (focus, GREEN))):
                h = max(2.0, (bottom - top - 14) * val / peak)
                p.setBrush(QColor(color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(QRectF(x + j * (w + 2), bottom - h, w, h), 3, 3)
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(i * col_w, bottom + 2, col_w, 14), Qt.AlignmentFlag.AlignCenter, fmt_minutes(active))
            p.drawText(QRectF(i * col_w, bottom + 16, col_w, 14), Qt.AlignmentFlag.AlignCenter, label)
        p.end()


class AppsChart(QWidget):
    """Applications les plus utilisées aujourd'hui."""
    ROW = 26

    def __init__(self):
        super().__init__()
        self.rows: list[tuple[str, float]] = []
        self.empty_text = "Pas encore de données aujourd'hui."
        self.setMinimumHeight(self.ROW)

    def set_rows(self, rows) -> None:
        self.rows = rows
        self.setMinimumHeight(max(self.ROW, self.ROW * len(rows)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.rows:
            p.setPen(QColor(MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.empty_text)
            return
        peak = max(r[1] for r in self.rows)
        name_w, time_w = 120, 64
        bar_x, bar_w = name_w + 8, self.width() - name_w - time_w - 16
        for i, (name, sec) in enumerate(self.rows):
            y = i * self.ROW
            p.setPen(QColor("#eef1f7"))
            p.drawText(QRectF(0, y, name_w, self.ROW), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       p.fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, name_w))
            p.setBrush(QColor(ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(bar_x, y + 7, max(3.0, bar_w * sec / peak), 12), 4, 4)
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(self.width() - time_w, y, time_w, self.ROW),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, fmt_minutes(sec))
        p.end()


class Panel(QWidget):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self._quitting = False
        app = QGuiApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(lambda: setattr(self, "_quitting", True))
        self.setWindowTitle("Desktop Cat")
        self.resize(540, 720)
        self.setStyleSheet(STYLE)
        self._animated: list[tuple[QLabel, str]] = []

        root = QVBoxLayout(self)
        head = QHBoxLayout()
        self.title = QLabel()
        self.title.setStyleSheet("font: 700 20px 'Segoe UI';")
        self.fish = QLabel()
        self.fish.setToolTip("Croquettes gagnées en vendant des doublons et en finissant des sessions")
        self.fish.setStyleSheet(f"background:{CARD};border:1px solid {LINE};border-radius:12px;padding:3px 12px;font-weight:700;")
        head.addWidget(self.title)
        head.addStretch(1)
        head.addWidget(self.fish)
        root.addLayout(head)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_wardrobe(), "Garde-robe")
        self.tabs.addTab(self._build_focus(), "Concentration")
        self.tabs.addTab(self._build_stats(), "Statistiques")
        self.tabs.addTab(self._build_settings(), "Réglages")
        root.addWidget(self.tabs)

        game.changed.connect(self.refresh)
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start(1000)
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._animate_hats)
        self._anim.start(150)
        self.refresh()

    def show_tab(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)

    # ───────────────────────── garde-robe
    def _build_wardrobe(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        self.wardrobe_sum = QLabel()
        self.wardrobe_sum.setObjectName("muted")
        lay.addWidget(self.wardrobe_sum)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(10)
        scroll.setWidget(self.grid_host)
        lay.addWidget(scroll)
        return page

    def _refresh_wardrobe(self) -> None:
        d = self.game.data
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._animated.clear()
        owned = sum(1 for h in HATS if d["hats"].get(h.id))
        self.wardrobe_sum.setText(f"{owned} / {len(HATS)} chapeaux découverts. "
                                  f"Un cadeau arrive toutes les {self.game.settings['gift_every_min']} min d'activité.")
        ordered = sorted(HATS, key=lambda h: RARITY_ORDER.index(h.rarity))
        for i, hat in enumerate(ordered):
            self.grid.addWidget(self._card(hat), i // 3, i % 3)
        for c in range(3):
            self.grid.setColumnStretch(c, 1)

    def _card(self, hat) -> QFrame:
        d = self.game.data
        count = d["hats"].get(hat.id, 0)
        rar = RARITIES[hat.rarity]
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"QFrame#card{{border:2px solid {rar['color'] if count else LINE};"
                           f"{'outline: 2px solid ' + ACCENT + ';' if d['equipped'] == hat.id else ''}}}")
        lay = QVBoxLayout(card)
        lay.setSpacing(2)
        pic = QLabel()
        pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pic.setPixmap(render_pixmap(3, locked=not count, hat=hat.id, fur=d["fur"], happy=True, t=0))
        lay.addWidget(pic)
        if count and hat.animated:
            self._animated.append((pic, hat.id))
        name = QLabel(f"<b>{hat.name}</b>" + (f" ×{count}" if count > 1 else "") if count else "<b>???</b>")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        kind = QLabel(f"<b style='color:{rar['color']}'>{rar['label']}</b>")
        kind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name)
        lay.addWidget(kind)
        if count:
            row = QHBoxLayout()
            worn = d["equipped"] == hat.id
            wear = QPushButton("Retirer" if worn else "Porter")
            wear.clicked.connect(lambda _=False, h=hat.id, w=worn: self.game.equip(None if w else h))
            row.addWidget(wear)
            if count > 1:
                sell = QPushButton(f"+{rar['sell']} 🐟")
                sell.setToolTip("Vendre un doublon")
                sell.clicked.connect(lambda _=False, h=hat.id: self.game.sell(h))
                row.addWidget(sell)
            lay.addLayout(row)
        return card

    def _animate_hats(self) -> None:
        if not self.isVisible() or not self._animated:
            return
        fur = self.game.data["fur"]
        t = time.monotonic() * 1000
        for label, hat_id in self._animated:
            label.setPixmap(render_pixmap(3, hat=hat_id, fur=fur, happy=True, t=t))

    # ───────────────────────── concentration
    def _build_focus(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        self.clock = QLabel("--:--")
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setStyleSheet("font: 800 56px 'Segoe UI'; background: transparent;")
        self.focus_msg = QLabel()
        self.focus_msg.setObjectName("muted")
        self.focus_msg.setWordWrap(True)
        self.focus_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.clock)
        cl.addWidget(self.focus_msg)
        presets = QHBoxLayout()
        self.preset_buttons = []
        for m in (15, 25, 45, 60):
            b = QPushButton(f"{m} min")
            b.clicked.connect(lambda _=False, mm=m: self.game.start_focus(mm))
            presets.addWidget(b)
            self.preset_buttons.append(b)
        cl.addLayout(presets)
        custom = QHBoxLayout()
        custom.addStretch(1)
        self.custom_min = QSpinBox()
        self.custom_min.setRange(1, 180)
        self.custom_min.setValue(30)
        self.custom_min.setSuffix(" min")
        self.start_btn = QPushButton("Démarrer")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(lambda: self.game.start_focus(self.custom_min.value()))
        self.stop_btn = QPushButton("Arrêter")
        self.stop_btn.clicked.connect(lambda: self.game.stop_focus(False))
        custom.addWidget(self.custom_min)
        custom.addWidget(self.start_btn)
        custom.addWidget(self.stop_btn)
        custom.addStretch(1)
        cl.addLayout(custom)
        lay.addWidget(card)
        lay.addStretch(1)
        return page

    def _refresh_focus(self) -> None:
        f = self.game.focus
        for w in (*self.preset_buttons, self.custom_min, self.start_btn):
            w.setVisible(not f)
        self.stop_btn.setVisible(bool(f))
        if f:
            left = max(0, int(f["ends_at"] - self.game.clock() + 0.999))
            self.clock.setText(f"{left // 60:02d}:{left % 60:02d}")
            self.focus_msg.setText(f"{self.game.data['name']} reste à côté de toi. Session de {f['total_min']} min en cours.")
        else:
            self.clock.setText("--:--")
            self.focus_msg.setText("Lance une session : ton chat s'installe avec son ordinateur, "
                                   "et te rapporte un cadeau à la fin.")

    # ───────────────────────── statistiques
    def _build_stats(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        row = QHBoxLayout()
        self.st = {}
        for key, caption in (("active", "devant l'écran aujourd'hui"), ("focus", "de concentration"), ("gifts", "cadeaux reçus")):
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            big = QLabel("0")
            big.setAlignment(Qt.AlignmentFlag.AlignCenter)
            big.setStyleSheet("font: 800 22px 'Segoe UI';")
            cap = QLabel(caption)
            cap.setObjectName("muted")
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap.setWordWrap(True)
            cl.addWidget(big)
            cl.addWidget(cap)
            row.addWidget(card)
            self.st[key] = big
        lay.addLayout(row)
        lay.addWidget(self._title("7 derniers jours"))
        self.week = WeekChart()
        lay.addWidget(self.week)
        lay.addWidget(self._title("Applications aujourd'hui"))
        self.apps = AppsChart()
        lay.addWidget(self.apps)
        note = QLabel("Le temps d'écran compte les secondes où le clavier ou la souris ont servi durant la dernière minute. "
                      "Le suivi des applications se coupe dans les Réglages. Tout reste sur ton PC.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        lay.addWidget(note)
        clear = QPushButton("Effacer mes statistiques")
        clear.setToolTip("Efface le temps d'écran, la concentration, les cadeaux comptés et les applications, "
                         "y compris dans les copies de sécurité. Chapeaux et croquettes sont conservés.")
        clear.clicked.connect(self._clear_stats)
        self.clear_btn = clear
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(clear)
        lay.addLayout(row2)
        lay.addStretch(1)
        return page

    def _confirm_clear(self) -> bool:
        answer = QMessageBox.question(
            self, "Effacer mes statistiques",
            "Effacer toutes les statistiques (temps d'écran, concentration, applications) ?\n"
            "Chapeaux et croquettes sont conservés. Cette action est définitive.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        return answer == QMessageBox.StandardButton.Yes

    def _clear_stats(self) -> None:
        if self._confirm_clear():
            self.game.clear_stats()

    @staticmethod
    def _title(text: str) -> QLabel:
        lab = QLabel(text)
        lab.setStyleSheet("font-weight: 700; margin-top: 10px;")
        return lab

    def _refresh_stats(self) -> None:
        store = self.game.store
        d = store.data["days"].get(date.today().isoformat(), {"active": 0, "focus": 0, "gifts": 0, "apps": {}})
        self.st["active"].setText(fmt_minutes(d["active"]))
        self.st["focus"].setText(fmt_minutes(d["focus"]))
        self.st["gifts"].setText(str(d["gifts"]))
        days = []
        for i in range(6, -1, -1):
            day = date.today() - timedelta(days=i)
            v = store.data["days"].get(day.isoformat(), {})
            days.append((("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")[day.weekday()], v.get("active", 0), v.get("focus", 0)))
        self.week.set_days(days)
        top = sorted(d.get("apps", {}).items(), key=lambda kv: kv[1], reverse=True)[:6]
        self.apps.empty_text = "Pas encore de données aujourd'hui." if self.game.settings["track_apps"] \
            else "Suivi des applications désactivé (Réglages)."
        self.apps.set_rows([(fmt_app(name), sec) for name, sec in top])

    # ───────────────────────── réglages
    def _build_settings(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)
        g = self.game

        identity = QGroupBox("Ton chat")
        identity_form = QFormLayout(identity)
        identity_form.setVerticalSpacing(10)
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(20)
        self.name_edit.setPlaceholderText("Miso")
        self.name_edit.editingFinished.connect(lambda: g.set_name(self.name_edit.text()))
        identity_form.addRow("Nom", self.name_edit)

        self.fur_box = QComboBox()
        for key, f in FURS.items():
            self.fur_box.addItem(f["label"], key)
        self.fur_box.activated.connect(lambda i: g.set_fur(self.fur_box.itemData(i)))
        identity_form.addRow("Pelage", self.fur_box)
        root.addWidget(identity)

        rhythm = QGroupBox("Rythme et apparence")
        rhythm_form = QFormLayout(rhythm)
        rhythm_form.setVerticalSpacing(10)
        self.spins = {}
        for key, label, lo, hi, suffix in (
                ("scale", "Taille du chat", 3, 6, ""),
                ("gift_every_min", "Cadeau toutes les", 5, 120, " min d'activité"),
                ("sleep_after_min", "Sommeil après", 1, 60, " min d'inactivité")):
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setSuffix(suffix)
            sp.editingFinished.connect(lambda k=key, s=sp: g.set_setting(k, s.value()))
            rhythm_form.addRow(label, sp)
            self.spins[key] = sp
        root.addWidget(rhythm)

        self.checks = {}
        descriptions = {
            "meows": "Affiche parfois une bulle au-dessus du chat.",
            "notifications": "Prévient quand une session de concentration se termine.",
            "track_apps": "Garde localement le nom des applications utilisées pour les statistiques.",
            "launch_at_startup": "Ouvre le chat automatiquement à l'ouverture de ta session Windows.",
        }
        groups = (
            ("Comportement du chat", (
                ("perch_windows", "Marcher sur le bord des fenêtres"),
                ("jump_between_windows", "Sauter d'une fenêtre à l'autre"),
                ("follow_active", "Rejoindre la fenêtre active"),
                ("meows", "Miauler de temps en temps"),
            )),
            ("Notifications et confidentialité", (
                ("notifications", "Notifications de concentration"),
                ("track_apps", "Suivi des applications"),
            )),
            ("Démarrage", (("launch_at_startup", "Lancer avec Windows"),)),
        )
        for title, items in groups:
            section = QGroupBox(title)
            section_layout = QVBoxLayout(section)
            section_layout.setSpacing(7)
            for key, label in items:
                row = QWidget()
                row_layout = QVBoxLayout(row)
                row_layout.setContentsMargins(0, 2, 0, 2)
                row_layout.setSpacing(2)
                cb = QCheckBox(label)
                cb.toggled.connect(lambda v, k=key, box=cb: self._set_checkbox_setting(k, v, box))
                row_layout.addWidget(cb)
                if key in descriptions:
                    hint = QLabel(descriptions[key])
                    hint.setObjectName("muted")
                    hint.setWordWrap(True)
                    row_layout.addWidget(hint)
                section_layout.addWidget(row)
                self.checks[key] = cb
            root.addWidget(section)

        test = QPushButton("Recevoir un cadeau maintenant (test)")
        test.clicked.connect(g.force_gift)
        test.setToolTip("Outil de test : ajoute un cadeau à la progression actuelle.")
        root.addWidget(test)
        root.addStretch(1)
        return page

    def _set_checkbox_setting(self, key: str, value: bool, checkbox: QCheckBox) -> None:
        if self.game.set_setting(key, value):
            return
        checkbox.blockSignals(True)
        checkbox.setChecked(self.game.settings[key])
        checkbox.blockSignals(False)
        if key == "launch_at_startup":
            QMessageBox.warning(
                self, "Démarrage avec Windows",
                "Windows n'a pas pu modifier le démarrage automatique. Vérifie les permissions de ton compte, puis réessaie.")

    def _refresh_settings(self) -> None:
        d, s = self.game.data, self.game.settings
        if not self.name_edit.hasFocus():
            self.name_edit.setText(d["name"])
        self.fur_box.setCurrentIndex(max(0, self.fur_box.findData(d["fur"])))
        for key, sp in self.spins.items():
            if not sp.hasFocus() and sp.value() != s[key]:
                sp.setValue(s[key])
        for key, cb in self.checks.items():
            if cb.isChecked() != s[key]:
                cb.blockSignals(True)
                cb.setChecked(s[key])
                cb.blockSignals(False)

    # ───────────────────────── rafraîchissement
    def refresh(self) -> None:
        d = self.game.data
        self.title.setText(f"Desktop Cat — {d['name']}")
        self.fish.setText(f"🐟 {d['fish']}")
        self._refresh_wardrobe()
        self._refresh_focus()
        self._refresh_stats()
        self._refresh_settings()

    def _on_tick(self) -> None:
        if not self.isVisible():
            return
        self._refresh_focus()
        if self.tabs.currentIndex() == 2:
            self._refresh_stats()

    def closeEvent(self, event) -> None:
        if self._quitting or self._session_ending():
            event.accept()      # sinon Windows croit que l'appli refuse de s'arrêter
            return
        event.ignore()          # le chat reste actif : on cache seulement le panneau
        self.hide()

    @staticmethod
    def _session_ending() -> bool:
        check = getattr(QGuiApplication.instance(), "isSavingSession", None)   # méthode d'instance
        return bool(check and check())
