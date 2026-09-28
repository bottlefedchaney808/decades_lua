# Guild Hub — Design (DRAFT, requirements incomplete)

Status: skeleton. GM requirements pending; update as info arrives.
Target: WoW Forever client (Classic-era API; existing WfPos addon uses `## Interface: 11303` — confirm).

## One-liner
One install for the guild: an in-game Lua addon + a Windows desktop **hub** that
pulls data out of the game (our addon, other addons, combat log), syncs it with
the guild backend, and powers every tool we build — logs ("WarcraftLogs, but
with other stuff"), the offline world map, the sim, and whatever comes next.

## Core principle: one pipe, many modules
Everything shares one data path. A new feature is a **module** that plugs into
that path; it does not get its own addon, its own installer, or its own backend.

```
 IN-GAME                          DESKTOP HUB                       GUILD BACKEND
 GuildSync addon (core+modules) ─┐
 other addons' SavedVariables ───┼─> watcher -> adapters -> event store ──sync──> API + web
 WoWCombatLog.txt ───────────────┤                 │                                 │
 WoWChatLog.txt (live pos) ──────┘                 ▼                                 │
                                         modules (UI in hub window)                  │
 GuildSync_Data addon <── Data.lua <── writer <───────────────────────── guild data ─┘
```

## Hard constraints (game rules)
- Addons cannot touch network or files. Only exits:
  - SavedVariables: written on logout / `/reload` only (bulk data).
  - Combat log: written live (`/combatlog` / `LoggingCombat`).
  - Chat log: written live (`/chatlog`), which is how WfPos already gets live position out.
- Only inbound path: a Lua data file the hub writes into an addon folder, read on
  next login / `/reload` (the TSM / Raider.IO pattern).
- Member-to-member in-game sync = addon messages, 255 chars/msg, throttled.
- No memory reading, no input automation. Same boundary WCL/TSM/Raider.IO use.

## Pieces

### 1. `GuildSync` addon (Lua): one addon, internal modules
| Module | Collects | Exit |
|---|---|---|
| core | character, realm, guild, rank, version, settings | SavedVariables |
| logs | auto-enable combat log in raids/dungeons, mark pulls/encounters | combat log |
| pos | position/zone (absorbs WfPos) | chat log (live) |
| sim-export | gear, enchants, talents, professions, buffs → sim input | SavedVariables |
| guild | TBD from GM (loot, attendance, roster, bank…) | SavedVariables + addon msgs |

### 2. `GuildSync_Data` addon (Lua)
Read-only data pushed down from the hub (guild notes, loot lists, sim targets,
map pins…). Displayed in-game.

### 3. Desktop hub (Windows)
- Finds the WoW Forever install; watches SavedVariables, combat log, chat log.
- **Adapters**: one per source (ours, combat log, each third-party addon) →
  common event schema. Adding a source = adding an adapter.
- **Local event store**: works offline; syncs when online.
- **Modules** (tabs in one window):
  - **Logs**: parse combat log, upload, WarcraftLogs-style reports.
  - **Map**: the existing `wow-forever` offline map, live player dot from `pos`,
    guildmates' dots via backend, shared guild pins.
  - **Sim**: WoW Forever sim (per `IDEA.md`, not built yet), fed by `sim-export`:
    one click "sim my character", guild-wide gear/upgrade views.
  - **Guild**: whatever the GM specifies.
  - Future modules plug in here.
- **Writer**: backend data → `GuildSync_Data/Data.lua`.
- Stack (proposed): local service + web UI in a desktop shell, because the map
  (Leaflet/HTML) and a wowsims-style sim are already web tech. Reuse, don't port.

### 4. Guild backend + web
Auth per member, store uploads, aggregate, serve reports/map/sim results to the
hub and a browser dashboard.

## Module contract (what every module must define)
1. Data it needs (addon module and/or adapter).
2. Events it adds to the common schema.
3. What it syncs to backend (if anything) and who can see it.
4. Its UI tab.
5. What, if anything, it pushes back into the game.

## Build order (proposed)
1. Core pipe: addon core + hub watcher + our adapter + local store. Proves the loop.
2. Map module (already built; just wire in `pos`). First visible win.
3. Logs module (combat log parser + reports).
4. Sim export + sim module (the sim itself is its own project).
5. Backend sync + guild module (blocked on GM requirements).

## Open questions (for GM)
- [ ] What is "the other stuff"? (loot/DKP, attendance, roster, bank, professions, consumables…)
- [ ] Which third-party addons must be read? (names)
- [ ] Does every member install the hub, or officers/loggers only?
- [ ] Windows only, or Mac too?
- [ ] Backend: where hosted, who pays, who sees reports (guild-only / public)?
- [ ] Confirm WoW Forever interface version + SavedVariables path.

## Decisions log
- 2026-09-28: One addon + one hub + one backend; features are modules on a shared pipe.
- 2026-09-28: Map (wow-forever) and sim (IDEA.md) are hub modules, not separate apps.
- 2026-09-28: WfPos gets folded into GuildSync as the `pos` module.
