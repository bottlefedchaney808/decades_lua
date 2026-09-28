# Guild Sync — Design (DRAFT, requirements incomplete)

Status: skeleton. GM requirements pending; update as info arrives.
Target: WoW Forever client (Classic-era API; existing WfPos addon uses `## Interface: 11303` — confirm).

## One-liner
"WarcraftLogs, but with other stuff": an in-game Lua addon + a Windows desktop
companion that collects guild data from our addon (and other addons), uploads
it to a guild backend, and pushes guild data back into the game.

## Known requirements
1. Lua addon (in-game).
2. Desktop sync app that reads data from our addon **and other addons**.
3. Combat-log reports in the style of WarcraftLogs.

## Architecture (proposed)

```
 WoW client
 ├─ GuildSync addon (Lua) ──writes──> WTF/Account/<ACC>/SavedVariables/GuildSync.lua
 ├─ other addons (Details!, loot addons…) ─> SavedVariables/<Addon>.lua
 ├─ combat logging (LoggingCombat) ──────> Logs/WoWCombatLog.txt
 └─ GuildSync_Data addon (Lua) <──reads── Interface/AddOns/GuildSync_Data/Data.lua
                                             ▲ written by desktop app
 Desktop companion (Windows)
 ├─ watches SavedVariables/*.lua + WoWCombatLog.txt
 ├─ parses Lua tables / combat log via per-source adapters
 ├─ uploads to backend
 └─ downloads guild data -> writes GuildSync_Data/Data.lua (loads on /reload or login)

 Backend + web dashboard
 └─ guild reports: combat logs + whatever else the GM specifies
```

### Hard constraints (game rules)
- Addons cannot touch network or files. Only exits: SavedVariables (written on
  logout / `/reload` only) and combat log (written live).
- Only inbound path: a Lua data file the desktop app writes into an addon
  folder, read on next load (the TSM / Raider.IO pattern).
- In-game member-to-member sync = addon messages, 255 chars/msg, throttled.
- No memory reading, no input automation. Same boundary WCL/TSM/Raider.IO use.

### Components
| Unit | Job | Depends on |
|---|---|---|
| `GuildSync` addon | collect in-game data, auto-enable combat log in raids, SavedVariables | WoW API |
| `GuildSync_Data` addon | read-only data pushed from desktop, displayed in-game | desktop writer |
| Desktop: file watcher | detect SavedVariables / combat log changes | WoW install path |
| Desktop: adapters | one per source (ours, combat log, each third-party addon) → common schema | parser |
| Desktop: uploader/downloader | talk to backend, auth per member | backend |
| Backend + web | store, aggregate, render reports | — |

## Open questions (for GM)
- [ ] What is "the other stuff"? (loot/DKP, attendance, roster, bank, professions, consumables…)
- [ ] Which third-party addons must be read? (names)
- [ ] Who installs the desktop app — every member, or officers/loggers only?
- [ ] Windows only, or Mac too?
- [ ] Where is the backend hosted, who pays, and who can see reports (guild-only / public)?
- [ ] Confirm WoW Forever interface version + SavedVariables path.

## Decisions log
- (none yet)
