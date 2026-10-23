# Accessibility

[Français](../ACCESSIBILITE.md) · English

[Back to the README](../../README.en.md)

> **Draft.** This document is a skeleton: Desktop Cat is a Qt desktop application whose accessibility has not been
> audited yet. It will fill in over time. It exists so that a future maintainer does not have to investigate
> everything from scratch.

---

## What is already in place

| What | Where | Status |
|---|---|---|
| Meow bubble readable whatever the Windows theme | `widgets.py` (`Bubble`) | ✅ Drawn background, text forced dark, size tied to the cat's scale |
| Adjustable cat size (3 to 6 px per "pixel") | Panel, Settings | ✅ |
| Meows can be turned off | Panel, Settings ("Il miaule de temps en temps") | ✅ |
| Notifications can be turned off | Panel, Settings | ✅ |
| Tooltips on some controls | `panel.py` | ✅ Partial |
| Global keyboard shortcut **Ctrl+Alt+C** (show / hide the cat), can be turned off | `hotkey.py` | ✅ |
| Mouse hunting, carried mouse and Pomodoro break can be turned off | Panel, Settings | ✅ |
| Jazz's visits can be turned off | Panel, Settings ("Jazz rend visite à Cali") | ✅ |

## What remains to be checked

- [ ] **Keyboard navigation of the panel**: tab order, visible focus, every action reachable without a mouse.
- [ ] **The cat and its context menu**: the cat is mostly driven with the mouse (double-click, right-click,
      drag-and-drop); the same actions are in the notification-area icon's menu, and Ctrl+Alt+C shows or hides the cat
      — to be confirmed as a sufficient keyboard equivalent.
- [ ] **Screen readers (NVDA, Narrator)**: accessible names of the panel's Qt widgets (`setAccessibleName` is used
      nowhere today).
- [ ] **Contrast** of the panel in Windows light and dark themes (the bubble is already handled; the panel not
      necessarily).
- [ ] **Text size** independent of the cat's size (a [roadmap](./ROADMAP.md) item, level 4).
- [ ] **Motion**: an option to reduce animations (equivalent of `prefers-reduced-motion`) and to turn off particle
      effects ("z", hearts).
- [ ] **Quiet hours**: no meow or notification at certain hours (roadmap, level 4).
- [ ] **Windows high-contrast mode**: behavior of the panel and the bubble.
- [ ] **Fallback emoji font** if Segoe UI Emoji is missing (roadmap, level 4).
- [ ] **Windows scaling (125 %, 150 %...)**: readability of the panel.

## What is, by nature, out of reach of automated tools

To be recorded here once the audit has started: pixel-art rendering, the cat's physics and transparent windows slip past
most audit tools.

## Manual check script

To be written: a short run-through to replay at every Release (panel keyboard navigation, NVDA/Narrator, dark theme,
high contrast, 150 % scale).

- [ ] Write the script
- [ ] Run it a first time and note the gaps above
