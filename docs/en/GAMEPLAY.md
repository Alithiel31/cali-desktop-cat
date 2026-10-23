# Game rules

[Français](../GAMEPLAY.md) · English

Default values; most are adjustable in the panel (Réglages / Settings tab).

## Activity and sleep
- You are "active" if your last keyboard/mouse action was less than 60 s ago.
- After 5 min of inactivity (adjustable, 1 to 60), the cat falls asleep. It wakes up as soon as you touch the mouse.

## Gifts
- A gift arrives after 20 min of accumulated activity (adjustable, 5 to 120). Progress does not count while a gift is
  waiting to be opened.
- Opening the gift draws a random hat: first the rarity, then a hat of that rarity.
- A hat you never had is worn right away. A duplicate increases the counter.

| Rarity | Weight | Resale price (🐟) |
|---|---|---|
| Common | 60 % | 5 |
| Uncommon | 22 % | 12 |
| Rare | 11 % | 30 |
| Epic | 5 % | 80 |
| Legendary | 1.5 % | 250 |
| Exotic | 0.5 % | 800 |

Only duplicates can be sold (one copy always remains).

Waiting gifts add up (99 at most): a focus gift does not replace an ordinary gift.

### Seasonal hats
- **Citrouille** (Pumpkin, epic): only from 25 October to 2 November (Halloween).
- In season, one gift in five directly gives a hat of the season; the others follow the normal draw.
- Out of season, the wardrobe shows it as "???" with the name of its season.
- Adding a season: an entry in `hats.SEASONS`, and `season="…"` on the hat.

## Mood and kibble
- Mood goes from 0 to 100 (50 for a new cat). It loses 1 point every 3 min of activity (not during absence).
- **Feeding** (panel, or right-click the cat): 5 kibble for +25. Not possible above 95 (it is no longer hungry).
- A pet gives +1, without going above 60: nothing replaces a meal.
- **Full** (70 and above): ordinary gifts arrive 25 % faster. **Starving** (below 25): it begs in its meows. In
  between: content.
- Kibble comes from focus sessions and from selling duplicates.

## Mouse hunting
- When the mouse has just stopped (between 1.2 and 15 s ago) at the cat's height, on its surface and within its reach,
  it stalks it for 1 to 2 s then pounces.
- If the mouse moves during the stalk, it escapes (the cat sulks for 8 s).
- Between two hunts: 25 to 60 s. Never during a focus session or while asleep.
- Can be turned off ("Chasser la souris", "Hunt the mouse").
- **She carries the mouse**: after a successful pounce she holds the cursor in front of her paws and takes it wherever
  she goes (walking, jumping, falling). She does not fall asleep on it. She lets go as soon as you move the mouse by more
  than 3 px, pick her up, or a focus session starts; she does not hunt again for 25 s.
- Can be turned off separately ("Emporter la souris après le bond", "Carry the mouse after the pounce").

## Jazz, Cali's big brother
- Jazz (a Nova Scotia Duck Tolling Retriever) drops by from time to time: first visit 2 to 5 min after launch, then every
  6 to 15 min. He comes in from one edge of the screen, trots along the floor of Cali's screen (crossing adjacent screens)
  and leaves by the other side. He cannot be clicked and never gets in the way of a window.
- **Visit to Cali** (6 times out of 10, when she is on the floor and free): he sits next to her for 3.5 to 6 s; she turns
  to him, with hearts and a small bubble (if meows are on). He leaves the way he came, and Cali follows him 7 times
  out of 10, for 4 to 8 s, before letting go.
- **Nap together**: if Cali is napping, he almost always (8 times out of 10) lies down against her without waking her;
  her nap then lasts at least 12 s. He leaves when she wakes up (90 s at most).
- Otherwise he just passes through, sometimes stopping for 2 to 4 s.
- Never while the cat is hidden or asleep (user away), nor during a focus session. He gives up if Cali becomes
  unavailable (working, perched on a window, mid-jump, carried with the mouse) or when she reaches the end of the floor
  while following him.
- Can be turned off ("Jazz rend visite à Cali", "Jazz visits Cali"). The "Faire venir Jazz maintenant (test)" ("Bring
  Jazz now (test)") button in the Settings brings him right away, if he can come at that moment.

## Focus
- Session of 1 to 180 min (25 min from the icon or the menu).
- During the session, the cat goes to the end of the screen (or onto the edge of the window it is perched on), sits in
  front of its laptop, fully visible, and shows the remaining time.
- End of a session of **10 min or more**: `10 + duration in minutes` kibble and an immediate gift.
- Below 10 min: no reward.
- You must have been **present for at least half of the session** (keyboard/mouse activity in the last 60 seconds). A
  session spent away from the computer, or during a PC sleep, ends with no reward.
- Presence is kept if the app restarts mid-session.
- The session survives an app restart. If it ended in the meantime, it is dropped without reward.

### Break (Pomodoro method)
- After every **rewarded** session, a 5 min break (adjustable, 1 to 30): ☕ timer in the bubble, and the cat reminds you
  to get up. At the end, it suggests starting again.
- Starting a new session or "Passer la pause" ("Skip the break") stops it. Can be turned off ("Pause après chaque
  session", "Break after every session").
- The break is not saved: an app restart forgets it.

## Keyboard shortcut
- **Ctrl+Alt+C** shows or hides the cat, from any application. Can be turned off.
- If another application already uses this shortcut, it stays inactive (message in the log).
- On a keyboard where AltGr+C types a character, that character is captured: turn the shortcut off in the Settings.

## Statistics
- Active time, focus time and gifts opened per day, over 60 kept days.
- Most-used apps of the day (40 at most), based on the executable name of the active window. Can be turned off in the
  Settings ("Noter les applications utilisées", "Record the apps used"): screen time keeps counting.
- **Effacer mes statistiques** ("Erase my statistics", Statistics tab, with confirmation): empties the history,
  including in daily copies and migration copies. Hats, kibble and settings are kept. An unreadable copy
  (`save.json.<date>.bak`) cannot be cleaned: delete it by hand if needed.
- Everything stays in `%APPDATA%/DesktopCat/save.json` (and its backup copies, see
  [TROUBLESHOOTING.md](TROUBLESHOOTING.md)); nothing is sent anywhere.

## Full screen
A full-screen app (game, video) hides the cat on **its** screen only.
