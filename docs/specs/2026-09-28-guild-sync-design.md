# Decades Guild Hub — Design (DRAFT)

Status: draft v3 (GM data list added). Refit to the GM's "Welcome to Forever" video (Decades, Reed, 2026-09-28,
https://youtu.be/ITOSnVrDOVI). Transcript ends where the AI-tools demo starts (music only
after that), so the app's exact screens were **not** captured. More GM info pending.
Target: WoW Forever client (Classic-era API; existing WfPos addon uses `## Interface: 11303`, still to be confirmed).

## Who it's for (from the video)
- Guild **Decades**, GM Reed, founded 2005. Launch target **125–150+ players** (98 online at
  once at the premiere), roughly **8 raid groups of 20** (Reed says 10–12 raids). Mega-server:
  ranking is region-wide.
- Goals: top-50 region progression, a place on the **WarcraftLogs** leaderboard, global parses.
- Theme: members are adults with jobs and families. **Respect their time, sustainable schedule, no
  leadership burnout.** Tools exist so a small leadership team can run 150 people.
- "Going all in on AI." Officer **Leer** is a developer by trade and is already building tools
  with Reed. **We must line up with him.**

## What the GM has run before (and wants to take "to the next level")
| Past system | What it did | Hub equivalent |
|---|---|---|
| SoD raid sheet (Google Sheets) | weekly signup by day, lockout column, officers build raid groups per day | **Signups + Raid Builder** |
| WCL merged into the raid sheet | every player's parses for the tier next to their name | **Performance** (WCL API pull) |
| Classic loot system | every item ever awarded, search by item/player, "who's next" | **Loot** (loot council ledger) |
| PRS player rating | 1–10 on execution and attendance; drove improvement but drained the council | **Player Score**, mostly auto-computed from data |
| RBV raid boss videos | synced multi-perspective raid video | future module (Reed: "might recreate") |
| Guild capability model | weighted traits vs guild size, strengths and weaknesses | **Leadership dashboard** (Reed: "eventually public") |

## Leadership buckets (drive permissions and dashboards)
- **Operations**: signups, raid comp, discipline, economy, guild bank, materials logistics (Night).
- **Social**: recruitment pipeline (apply, 1:1 interview, notes, decision), morale, feedback, events.
- **Strategy**: raid strategy, class stacking, loot distribution, parsing.

Ranks: Recruit (about 1 month) → Member → Veteran (2+ content runs) → **Raider** (slight loot
priority, progression pool, around 30+) → Council → Officer → GM.

## Core principle: one pipe, many modules
Same as v1: one addon, one desktop companion, one backend. Features are modules on a shared
pipe. v2 change: **the web app is the main surface** (signups, raid builder, loot, recruiting
are officer and member workflows, not desktop ones). The desktop companion's job is getting data
**out of the game** (and back in).

```
 IN-GAME                         DESKTOP COMPANION                 BACKEND + WEB APP
 Decades addon (Lua) ─SV───┐                                        ├─ Signups / Raid Builder
 other addons' SV ─────────┼─> watcher -> adapters -> upload ─────> ├─ Loot ledger
 WoWChatLog.txt (pos) ─────┘                                        ├─ Performance (WCL API) <── WarcraftLogs
 WoWCombatLog.txt ──> official WCL uploader (unchanged)             ├─ Roster / Recruiting / Player Score
 Decades addon <── Data.lua <── writer <─────────────────────────── ├─ Economy / Bank
                                                                    ├─ Map, Sim (Jason's modules)
                                   Discord bot <──────────────────> └─ AI assistant over all of it
```

## Hard constraints (game rules)
- Addons can't use the network or write files. The only ways out: SavedVariables (written on
  logout or `/reload`), the combat log (live), and the chat log (live, the WfPos trick).
- The only way in: a Lua data file written into the addon folder, read on login or `/reload`
  (the TSM / Raider.IO pattern).
- In-game member-to-member sync uses addon messages: 255 characters each, throttled.
- No memory reading, no automation.

## Data collection principle (GM, 2026-09-28)
**Collect any data point that has value when viewed.** The addon collects cheaply and broadly;
the web app is where the value shows up. Rules that keep this from getting out of hand:
- The addon stores **rollups** (counts, last-seen, per-zone totals), not raw event streams, so
  SavedVariables stay small and login stays fast. Raw detail lives only in the combat log.
- Every collector is its own module with an on/off toggle, so a new data point is a new module.
- Each data point is listed below as: source → what's stored → where it's shown.

## Data catalog
### Wave 1 (GM list)
| Data | In-game source (Classic API) | Stored | Viewed as |
|---|---|---|---|
| Loot collected | own capture: `CHAT_MSG_LOOT` (all loot, everyone in range) + **RCLootCouncil adapter** (reads its SV for council awards, reroutes/trades) | item, who, when, where, source (drop/council/trade) | loot ledger, per-item "who has it", per-player history |
| Reputation | `GetFactionInfo` on `UPDATE_FACTION` | faction, standing, value, per char | guild rep matrix ("who's Exalted with X") |
| Professions | `GetSkillLineInfo`, trade skill window scan when opened | skill levels + known recipes | crafter directory ("who can make X") |
| Inventory (bags) | bag scan on `BAG_UPDATE` (debounced) | item counts per char | "who has X", alt totals |
| Bank / alts | bank scan when `BANKFRAME_OPENED`; every char that logs in adds its own | per char | account-wide totals |
| Guild bank + logs | **see note below** | contents + deposit/withdraw log | bank page, audit log |
| Custom player notes | officer/member entry in web app, pushed back to the addon | note, author, visibility | roster, in-game tooltip |
| Position | `UnitPosition` (WfPos logic) | live via chat log | map live dots |
| Hearthstone location | `GetBindLocation()` | inn per char | roster column, map pin |
| "Typically found in" | time-in-zone accumulator (minutes per zone/subzone) | per-char zone histogram | profile ("usually in Orgrimmar bank"), guild heatmap on map |
| PvP kills + victims | combat log `PARTY_KILL` on players + honor-kill chat; deaths to players from last-damage source | killer → victim count, last time, zone | **rivalries**: "Tyler has killed X 50 times", nemesis list, leaderboards |
| Sightings | nameplates, target, mouseover, combat log GUIDs, deduped per GUID per 5 min | name/type → times seen, first/last seen, zones | "Spiderfang seen 312 times", rare/world-boss/enemy-player tracker, map heat |
| Chat history (**Elephant** remake) | chat events → per-channel log with a size cap | guild/officer/raid/whisper logs, local by default | in-game log window; guild/officer channels optionally synced |

**Guild bank note:** original vanilla (the Classic-era base) had **no guild bank**. It came in TBC.
If WoW Forever has one, read it natively (tabs + money log). If not, the "guild bank" is bank alts:
scan their bags, bank and mail, and build the log from their trades, mail and loot. **Confirm which.**

**Elephant:** it's a chat logger ("remembers the chat"). I could not confirm it has a WoW Forever
build. Plan: build it as the `chat` module either way. It's small, and it gives us guild-channel
history for free.

### Proposed additions (same principle, cheap to collect)
- Deaths: what killed you, where, level. Guild "most deaths", dangerous zones on the map.
- Leveling timeline: level-up timestamps and `/played`. "Race to 60" board for launch week.
- Gold over time per char, repair spend.
- Gathering: herbs and ore picked, by node location (ties into the map's 17,637 nodes).
- Dungeon and raid runs: clears, time, group.
- Raid consumables and world buffs present on pull (the combat log already has them).
- Quests completed, for the map/Questie side.
- Achievements-style firsts: first kill of a boss, first to exalted, first epic mount.

## Sync TO the addon (future state)
Via the hub-written `Data.lua`, shown in the **guild tab / guild roster** and tooltips:
- Parses (WCL best/median per player)
- BiS lists (per class/spec, with an "you have it / you need it" marker)
- Accolades (badges: firsts, rivalries, top parser, attendance streaks)
- Custom player notes, rank tags ("Decades · Raider")

## Pieces

### 1. `Decades` addon (Lua): one addon, internal modules
| Module | Does | Exit |
|---|---|---|
| core | char, class, level, guild rank, alts, version | SV |
| loot | all loot seen (`CHAT_MSG_LOOT`) + council awards; RCLootCouncil adapter for reroutes | SV |
| attendance | raid roster snapshots on boss pulls and kills | SV |
| bank | guild bank / bank-alt inventory scan | SV |
| gear (sim-export) | gear, enchants, talents, professions, consumables | SV |
| pos | position, hearthstone, time-in-zone (absorbs WfPos) | chat log + SV |
| inventory | bags, bank, alts, guild bank or bank alts | SV |
| rep / prof | reputations, professions and recipes | SV |
| pvp | kills and deaths vs players (rivalries) | SV |
| sightings | NPC/player/rare sighting counts | SV |
| chat | Elephant-style chat logger | SV |
| display | shows hub data in game: your signups, loot history on item tooltips, "Decades · Raider" player tooltip | reads Data.lua |

### 2. Desktop companion (Windows, lightweight)
Finds the WoW Forever install, watches SV and chat log, parses Lua tables through per-source
adapters, uploads, and writes Data.lua back. Tray app. Members install it once. It does **not**
replace the WCL uploader: WCL stays the source of truth for rankings.

### 3. Backend + web app
Auth: Discord login (the guild lives in Discord). Rank maps to permissions.
| Module | Priority | Notes |
|---|---|---|
| Signups + Raid Builder | **launch-critical** | weekly availability by day, lockouts, drag-and-drop raid groups per night, "who's free Friday" |
| Performance | **launch-critical** | WCL API: tier parses, ranks, pulled automatically next to the roster |
| Loot | **launch-critical** | full ledger from the addon, search by item/player, loot priority, Raider flag, "who's next" |
| Roster / Recruiting | high | applications, interview notes, trial clock, rank promotion |
| Player Score | medium | auto-calculated from attendance, WCL, signup reliability; council adds notes |
| Economy / Bank | medium | bank contents, material needs vs raid consumable demand |
| Map | Jason's | existing wow-forever map, guild pins, optional live dots |
| Sim | Jason's | IDEA.md sim, fed by the gear export |
| AI assistant | later | ask questions over signups, loot, logs; drafts raid comps and feedback |
| Leadership dashboard | later | capability model, coverage per bucket |

### 4. Discord bot
Signup reminders and links, raid-night announcements, loot award feed. Ties the Discord
(Reed's priority) to the hub.

## Module contract
Every module defines: data source (addon / adapter / WCL / web form), schema, permissions,
web UI, what it pushes into the game.

## Build order (proposed)
1. Web skeleton + Discord login + roster (ranks and permissions).
2. Signups + Raid Builder (replaces the Google sheet; usable with no addon at all).
3. WCL Performance pull.
4. Addon core + loot + desktop companion upload, giving the Loot ledger.
5. Attendance, bank, gear, then Player Score and Economy.
6. Map and Sim modules, AI assistant, Discord bot extras.

Steps 1–3 need **no addon**. They can ship before launch and cover the old sheet's job.

## Open questions
- [ ] **What have Reed and Leer already built?** (the AI tool shown at the end of the video) Extend it, or replace it?
- [ ] Launch date and the hard deadline for signups being live.
- [ ] Loot rules: pure loot council? Raider priority weighting? Is the ledger visible to everyone?
- [ ] Does WarcraftLogs support WoW Forever at launch (API/zone IDs)?
- [ ] Hosting, domain, budget.
- [ ] Third-party addons: RCLootCouncil confirmed. Others (Details!, etc.)?
- [ ] Does WoW Forever have a native guild bank, or is it bank alts?
- [ ] Does Elephant (or any chat logger) exist for Forever?
- [ ] Confirm WoW Forever interface version and SavedVariables path.

## Decisions log
- 2026-09-28: One addon + one companion + one backend; features are modules on a shared pipe.
- 2026-09-28: Map (wow-forever) and sim (IDEA.md) are modules, not separate apps.
- 2026-09-28: WfPos folds into the addon as `pos`.
- 2026-09-28 (v2): Fit to the Decades GM video. The web app is the primary surface. WCL is integrated, not
  replaced (the guild ranks on WCL). Launch-critical = Signups/Raid Builder, WCL Performance, Loot.
- 2026-09-28 (v3): GM data list added. Principle: collect anything valuable to view, stored as rollups. RCLootCouncil read via adapter, not replaced. Elephant rebuilt as the `chat` module. Sync-to-addon: parses, BiS, accolades in the guild tab.
