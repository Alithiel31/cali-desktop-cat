# Manual test before a Release

[Français](../TEST-MANUEL.md) · English

What CI cannot check: the real Windows (windows, overlays, shortcut, multiple screens) and the executable.
Allow 20 to 30 min. Mark each point ✅ / ❌; for a ❌, attach `desktopcat.log` (tray icon menu > Ouvrir le journal /
Open the log). The app's interface is in French; labels are quoted as they appear on screen.

## 0. Before starting
- [ ] CI on `main` is green (the repository's *Actions* tab), in particular the **Windows** jobs.
- [ ] Launch the test instance: double-click `tools\run_test_instance.bat`
  (isolated save in `%TEMP%\desktopcat_test`, 50 kibble, hungry cat, meows off).
  To find the log: `%TEMP%\desktopcat_test\DesktopCat\desktopcat.log`.

## 1. Startup
- [ ] The cat appears at the bottom of the screen, with no rectangle around it; the icon is in the notification area.
- [ ] Relaunch the `.bat`: no 2nd cat.
- [ ] The log contains "Démarrage" and "Raccourci Ctrl+Alt+C actif", with no `ERROR` line.

## 2. Windows and perching
- [ ] Open Notepad, wait: the cat eventually jumps onto its top edge and walks on it.
- [ ] Move the window: it follows, without teleporting.
- [ ] Minimize / close the window: it falls and lands on the floor (or on a window below).
- [ ] Pick it up with the mouse and drop it above a window: it lands on it.
- [ ] **Overlays**: open Steam and/or Discord (in-game overlay enabled if possible). The cat never walks "in the void".
- [ ] A window that is "not responding" (optional): the cat keeps moving normally.

## 3. Interactions
- [ ] Click: hearts. Double-click: the panel opens.
- [ ] **Meal**: right-click > "Donner des croquettes" ("Give kibble"): "Miam !", hearts; panel header: 🐟 45, mood 45.
  Repeat up to 95+: the option is greyed out.
- [ ] **Hunt**: move the mouse near the cat (same height, on the floor beside it), then let go. Within a few seconds,
  it stalks it (wide-open eyes) then pounces. Repeat, moving during the stalk: it gives up.
- [ ] **Jazz**: Settings > "Faire venir Jazz maintenant (test)" ("Bring Jazz now (test)"): a red dog comes in from one edge
  of the screen and trots along the floor. Repeat several times: sometimes he just crosses (occasionally sitting for a
  moment), sometimes he sits next to Cali, who turns to him (hearts), then leaves, often followed by her. A click on him
  goes straight through.
- [ ] **Nap together**: let Cali fall asleep (a nap on the floor, without moving), then bring Jazz: he lies down against
  her without waking her, and leaves when she wakes up. Hide the cat (Ctrl+Alt+C) during a visit: Jazz disappears too.
  Untick "Jazz rend visite à Cali": the test button no longer does anything.
- [ ] **Shortcut**: in another app (browser), Ctrl+Alt+C hides the cat, once more shows it again.
  The tray menu shows "Cacher le chat   Ctrl+Alt+C". Untick the setting: the shortcut does nothing any more.

## 4. Gifts and focus
- [ ] Settings > "Recevoir un cadeau maintenant" ("Receive a gift now") twice: the cat puts down a gift; when opening it,
  the hat bubble stays readable, then the 2nd gift arrives.
- [ ] **10 min** session (Concentration tab, free field) while staying in front of the screen: the cat settles at its
  computer, ⏱ in the bubble. At the end: notification, gift, "Pause de 5 min", ☕ in the bubble,
  "Passer la pause" button in the panel and in the tray menu.
- [ ] Let the break run to the end (or set 1 min in the Settings before the session): "Pause finie !".

## 5. Full screen and sleep
- [ ] A full-screen YouTube video: the cat disappears from that screen, comes back on exit.
- [ ] Touch nothing for 5 min: it falls asleep ("z"). Move the mouse: "Te revoilà !".

## 6. Multiple screens (if available)
- [ ] It goes from one screen to the other (on foot if the bottoms line up, otherwise jumping or falling).
- [ ] Different scales (100 % / 125 %): bubble and particles stay above its head.
- [ ] Unplug the screen it is on: it reappears on the other.

## 7. The executable (on a PC without Python if possible)
- [ ] Download the latest build's `DesktopCat-windows` artifact (Actions > Release > Artifacts), check the SHA256.
- [ ] It starts (SmartScreen: "More info" > "Run anyway").
- [ ] Log and save file created in `%APPDATA%\DesktopCat`.
- [ ] Settings > "Lancer avec Windows" ticked, sign out of Windows and back in: the cat comes back.
- [ ] Task Manager > Startup: "Disable" Desktop Cat, then reopen the panel: the box is unticked.
  Re-tick it: Task Manager (F5) shows it "Enabled".

## 8. Seasonal hat (optional)
- [ ] Set the Windows date to 31 October, relaunch, open about ten test gifts: a Citrouille (Pumpkin) comes out
  (≈ 1 in 5). Put the date back.

## Result
Everything ✅: update the version (`desktopcat/__init__.py`), the CHANGELOG section, then tag
(see [DISTRIBUTION.md](DISTRIBUTION.md)).
