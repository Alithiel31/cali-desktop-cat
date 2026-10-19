"""Gestion des interactions souris et du menu contextuel du chat."""
from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMenu

from .screens import clamp_point


class PetInput:
    """Adaptateur des événements Qt vers les actions de la fenêtre Pet."""

    def __init__(self, pet):
        self.pet = pet

    def press(self, event) -> None:
        pet = self.pet
        global_pos = event.globalPosition().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            pet._press = {"g": global_pos, "moved": False,
                          "off": (event.position().x(), event.position().y())}
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_menu(global_pos)

    def move(self, event) -> None:
        pet = self.pet
        press = pet._press
        if not press:
            return
        global_pos = event.globalPosition().toPoint()
        if not press["moved"] and math.hypot(global_pos.x() - press["g"].x(),
                                             global_pos.y() - press["g"].y()) > 5:
            press["moved"] = True
            pet.state = "drag"
            pet.stand, pet.jump, pet.vy = None, None, 0.0
            pet.setCursor(Qt.CursorShape.ClosedHandCursor)
        if press["moved"]:
            new_x = global_pos.x() - press["off"][0]
            new_y = global_pos.y() - press["off"][1]
            if abs(new_x - pet.fx) > 1:
                pet.dir = 1 if new_x > pet.fx else -1
            zones = [(work[0], work[1] + pet.FOOT, work[2], work[3]) for work in pet.works]
            cx, feet_y = clamp_point(zones, new_x + pet.CW / 2, new_y + pet.FOOT)
            pet.fx, pet.fy = cx - pet.CW / 2, feet_y

    def release(self, event) -> None:
        pet = self.pet
        press, pet._press = pet._press, None
        if not press or event.button() != Qt.MouseButton.LeftButton:
            return
        if press["moved"]:
            pet.unsetCursor()
            pet.state = "fall"
            pet.vy = 0.0
        else:
            pet._pet_timer.start(min(400, QApplication.doubleClickInterval()))

    def double_click(self) -> None:
        self.pet._pet_timer.stop()  # c'était un double-clic : pas de caresse
        self.pet.open_panel.emit()

    def show_menu(self, position) -> None:
        pet = self.pet
        menu = QMenu(pet)
        menu.addAction("Ouvrir le panneau", pet.open_panel.emit)
        if pet.game.focus:
            menu.addAction("Arrêter la concentration", pet.stop_focus.emit)
        else:
            menu.addAction("Concentration 25 min", lambda: pet.start_focus.emit(25))
        menu.addSeparator()
        menu.addAction("Quitter", pet.quit_app.emit)
        menu.exec(position)
