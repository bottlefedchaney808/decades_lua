# Decades Guild Hub — Design (DRAFT)

Status: draft v5 (min-max suite, two sim engines, directions, public face). Refit to the GM's "Welcome to Forever" video (Decades, Reed, 2026-09-28,
https://youtu.be/ITOSnVrDOVI). Transcript ends where the AI-tools demo starts (music only
after that), so the app's exact screens were **not** captured. More GM info pending.
Target: WoW Forever client **1.60.x** (forever_sim scrapes build `1.60.1.70009`). WfPos's `## Interface: 11303` is
probably wrong for Forever: read the real value in game with `/dump select(4, GetBuildInfo())`.

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
                                                                    ├─ Map; Sim = link to sim.decades.gg
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

## Firebase integration (backend = Firebase, project `decades-prod`)
Found by reading `Decades-Guild/forever_sim` (public). What already exists in `decades-prod`:
- **Hosting**: site `forever-sim`, which is `https://sim.decades.gg`. It's a static Vite + React + TS + shadcn app.
- **Functions (2nd gen)**: codebase `forever-sim`, nodejs22, `us-central1`. It runs the Discord bot
  (`discordInteractions` HTTPS endpoint + `discordWorker` on Pub/Sub `discord-jobs`).
- **Discord application `decades_app`** (`1549936086892150885`, server `170966255409430528`). Its OAuth
  client is **already used for "decades_app's sign-in"**, so a Decades web app with Discord login
  already exists or is in progress (repo not public). Its router is designed to take decades_app's commands too.
- **Deploy**: GitHub Actions to Workload Identity Federation (no JSON keys) to `firebase-tools@15`. Secrets
  go in Secret Manager. No Firestore in use yet (the bot keeps its state in memory).

**Rule: the hub lives inside `decades-prod` and follows these conventions. No second project, no second login.**

### Layout
| Piece | Firebase service | Notes |
|---|---|---|
| Web app | Hosting, new target (e.g. `guild-hub`), or pages inside decades_app | same stack as the sim (Vite/React/TS/shadcn) |
| Login | Firebase Auth, **reusing decades_app's Discord sign-in** | Discord isn't a built-in Auth provider. Default: a Function swaps the Discord OAuth code for a Firebase **custom token**, with claims `{discordId, rank, roles}` |
| Data | **Firestore** | rollup documents, not raw event streams (keeps reads and cost down) |
| Ingest | Functions codebase `guild-hub`: `ingest` (HTTPS, needs an ID token) | the only writer for addon data (Admin SDK) |
| Raw uploads | Cloud Storage `uploads/{uid}/{ts}.json.gz` | kept 30 days so the parser can be replayed after a fix |
| WCL pull | scheduled Function, WCL API v2 client credentials in Secret Manager | writes the `parses` cache |
| Addon down-sync | `addonData` (HTTPS): one JSON bundle per member | the companion turns it into `Data.lua` |
| Discord | **the existing `discordInteractions` router** | hub commands register as decades_app routes. No second bot |
| Rank sync | Function: Discord roles and guild rank (from addon uploads) to Auth custom claims | rules key on claims |

### Data flow
```
addon SV ─> companion (parse Lua -> JSON, gzip) ─POST + Firebase ID token─> ingest()
   ingest: validate schema v# -> keep raw in Storage -> idempotent merge into Firestore rollups
web app  <── Firestore listeners (members) ──┐
companion <── addonData() JSON ──────────────┤──> writes GuildSync Data.lua
Discord  <── discordWorker jobs ─────────────┘
WCL API ──scheduled──> parses/{charId}
```

### Firestore model (first cut)
```
members/{discordId}                      rank, roles, mains/alts -> characterIds
characters/{realm-name}                  class, level, race, guildRank, hearth, lastSeen, owner
  /snapshots/{kind}                      kind = bags|bank|rep|professions|gear   (latest only; overwritten)
  /zoneTime/{zoneId}                     minutes by subzone        ("typically found in")
  /pvp/{victimKey}                       kills, lastAt, zones      (rivalries; mirrored counts on the victim)
loot/{autoId}                            item, winner, source(drop|council|trade|reroute), raid, boss, at, rclcId
bank/{bankCharId} + /log/{id}            contents + ledger (guild bank or bank alts)
sightings/{entityKey}                    count, firstAt, lastAt, byZone{}, bySpotter{}   (guild-wide rollup)
signups/{weekId}/entries/{discordId}     days[], lockouts, note
raids/{raidId}                           night, group, roster[], comp
parses/{characterId}                     WCL best/median per boss (Function-written)
notes/{characterId}/items/{id}           text, author, visibility(public|council|officer)
accolades/{id}                           type, characterId, at, detail
chat/{channel}/days/{yyyy-mm-dd}         officer/guild chat only (opt-in), capped
uploads/{uploadId}                       uploader, charId, seq, schemaVersion, status (dedupe key)
```
Sightings and PvP use `FieldValue.increment` in batched writes. The addon sends **deltas since the
last upload** (with a per-character sequence number), so a resent upload doesn't double-count.

### Security rules (summary)
- Client writes are allowed only on: your own `signups` entry, and `notes` (council+).
  Everything the addon produces is written by Functions only.
- Read: members read guild data; `notes` and `chat` follow their `visibility`, based on custom claims;
  recruiting/officer data is officer-only.
- Emulator suite + rules unit tests before any deploy (matches forever_sim's gate).

### Desktop companion auth
Device-link flow: the companion opens `https://<hub>/link?code=XXXX`. The member signs in with Discord.
A Function binds the code and returns a Firebase custom token. The companion keeps the refresh token in
Windows Credential Manager and calls `ingest`/`addonData` with ID tokens. No passwords in the companion.

## Sim integration (forever_sim already exists)
`https://sim.decades.gg` is the guild's sim: every DPS spec plus 3 tanks. It sources from the Forever
client via wago.tools and is under active daily development. It pairs with Jason's WoW4_SiMs engine (see **Two sim engines, one interface**). **No third sim.**
Integration is link-based, which the sim's CSP (`connect-src 'self'`) needs anyway:
- The addon `gear` module exports gear, enchants, talents and consumables.
- The hub builds a forever_sim **setup code** (a `SimConfig` deflated to base64url, `src/app/setup-code.ts`,
  decision D21) and links `https://sim.decades.gg/#s=<code>`. "Sim my character" is one click, from
  the roster or in game (the link is printed to chat for copying).
- Needs forever_sim's `SimConfig` schema + `CONFIG_VERSION` as a shared contract. **Coordinate with its
  maintainer; don't fork the format.**
- Later: the sim's optimizer (M5.7) produces **BiS lists**, and the hub pushes them into the addon.

## Min-max suite: Sim × WCL × Performance
The question every raider asks after a kill: **"How much did I leave on the table, and what is the one
thing I should fix next?"** The suite answers it with three views of the same pull and a ranked list of fixes.

| View | Answers | Source |
|---|---|---|
| **Sim** (expected) | what this character *should* do with this gear, talents and consumables on this fight | forever_sim (DPS/TPS, Forever-sourced) + WoW4_SiMs (healers, raid sim, rotation timeline) |
| **WCL** (actual, ranked) | what you *did*, and where it ranks in the region | WCL API v2: rankings + report events |
| **Performance** (why) | the execution behind the number | computed from WCL report events (or our own combat-log parser if WCL doesn't support Forever): casts per ability, cooldown usage, buff/debuff/DoT uptime, idle GCD time, resource overcap, early refreshes and clipping, deaths and their timing, consumables and buffs present on pull |

### Fight-adjusted expectation (the core idea)
A raw sim is a stationary target dummy. Comparing it to a real kill isn't fair, and players ignore it.
So every kill is re-simmed under the fight's **real conditions**, taken from its log: duration, the
player's active time (downtime, movement, death), target count, the buffs and debuffs actually up,
and the consumables actually used. That gives four numbers per player per boss:

| Number | Meaning |
|---|---|
| **BiS** | sim, best-in-slot gear available now |
| **Ceiling** | sim, your gear, ideal setup (full consumables, buffs, enchants) |
| **Expected** | sim, your gear, *this fight's* real conditions |
| **Actual** | WCL |

- Ceiling − Expected = **setup loss**: consumables, buffs, enchants. Fixable before next raid.
- Expected − Actual = **execution loss**: rotation, uptime, cooldowns. Fixable with practice.
- BiS − Ceiling = **gear gap**: tied to upgrades and the loot ledger.

### Critique engine: every fix is measured
Each finding is re-simmed **with the fix applied**, so every line carries a measured gain, and the list
is ranked by gain. No generic advice. Card shape (illustrative numbers, not measured):
```
Grukk · Fury Warrior · Ragnaros kill · WCL 78
Actual 612 · Expected 701 · Ceiling 744 · BiS 866 DPS
1. Execution  Bloodthirst on cooldown 81% of the fight (sim 97%)       +38  [timeline]
2. Gear       next upgrade: <item> from <boss>, loot priority #3        +31  [loot] [go there]
3. Setup      no Elixir of the Mongoose                                 +24  [where to get it]
4. Execution  14 s of idle GCD in phase 2                               +19  [timeline]
```
- **Rotation critique**: casts per active minute vs the sim's, cooldown uses vs available uses,
  uptimes vs the sim's, idle GCD, clipping, overcap. Sources: WCL events, plus the sim's per-ability,
  aura, resource and timeline metrics (WoW4_SiMs `detailed_results`: cast, aura, resource, timeline).
- **Gear critique**: from the addon's gear export. Missing or wrong enchants (by sim stat weights), hit
  and weapon-skill caps, set bonuses, and an upgrade list per slot with its source
  (drop/crafted/rep/quest/vendor), cross-referenced to the loot ledger (who's ahead of you), guild
  crafters and the guild bank.
- **Mentor overlay**: your cast timeline laid over the guild's top parser of the same spec on the
  same boss. This is Reed's mentorship idea turned into a tool.
- Healers: WCL HPS + overheal vs WoW4_SiMs healing sims. Tanks: TPS in both sims.

### Officer views
- **Pre-pull setup check**: raid-wide missing consumables and buffs (addon + log). The cheapest DPS there is.
- **Raid Builder + raid sim**: sim the groups built from signups (WoW4_SiMs raid sim). Evidence for comp and bench calls.
- **Trends**: execution loss per player over weeks. Feeds Player Score (replaces the manual PRS grading).

### Two sim engines, one interface
| Engine | Strength | Use |
|---|---|---|
| **forever_sim** (guild, sim.decades.gg, TS) | Forever-client-sourced numbers, optimizer (M5.7) → BiS | headline DPS/TPS and BiS wherever it covers the spec |
| **WoW4_SiMs** (Jason, wowsims fork, Go→WASM + CLI) | all 19 specs incl. healers, raid sim, APL rotations, per-ability timeline/aura/resource metrics, WowSimsExporter import | healers, raid sim, rotation-timeline critique. Its combat values are still 1.12/SoD-scale until its database is regenerated from Forever client data (its `STATUS.md`) |

- `SimProvider` interface: `simulate(setup, conditions) → {metric, perAbility, auras, resources,
  timeline, assumptions[]}`. The hub calls either engine headless. forever_sim's TS engine runs in
  Functions or Cloud Run; WoW4_SiMs runs `wowsimcli` in a Cloud Run job, or WASM in the browser.
- **Cross-check**: where both engines cover a spec, run both. A disagreement over 5% opens an audit item
  for the sim maintainers instead of silently picking one.
- **Provenance on every number**: `[F]` Forever client, `[C]` Classic Era, `[?]` assumption, matching
  forever_sim's doctrine. Nothing is shown as fact that isn't sourced.

## Directions: "Go there" everywhere
Anything tied to a place gets a location, resolved from the map data (49 zones, 263 landmarks, 1,285
POIs incl. flight masters/zeppelins/boats, 17,637 herb and ore nodes) plus item-source data. That covers
upgrade drops, bosses, vendors, rep quartermasters, trainers, consumable reagents, gather nodes, a
crafter's "usually found in", and rare spawns.

**"Get it" resolution order (guild first, saves time):**
you already own it (bags/bank/alts) → guild bank → guild crafter (who, where they usually are) →
drop/vendor/farm location with a route.

| Surface | Form |
|---|---|
| Web | "Show on map" deep link (`#lat/lng/zoom`) plus a route from your hearth or live position via flight paths and zeppelins/boats |
| In game | addon `nav` module: TomTom-style arrow + distance from `UnitPosition`; `/dec go <target>`; step list printed to chat ("Hearth → fly Crossroads → run south to …") |
| Discord | `/where <item or npc>` returns sources, guild holders and crafters, and a map link |
| Critique | a consumables shopping list per player, turned into a reagent-farming route over the node data |

## Public face: represent Decades
- **Public guild page** on decades.gg: progression, region rank, parse averages, accolades, rivalry
  highlights. Reed called the SoD raid sheet "a massive recruiting tool"; this is its successor.
- **Member card**: one page per character: parse, sim gap, gear vs BiS, rep, professions, accolades,
  "usually found in". Shareable as an image in Discord.
- **Quality bar = forever_sim's**: mobile and desktop designed separately, shadcn/ui, provenance on
  every number, e2e-tested before deploy.
- Per-member opt-out for the public card and live position. Officer notes are never public.

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
Firebase (see **Firebase integration**). Discord login reused from decades_app; rank maps to custom claims.
| Module | Priority | Notes |
|---|---|---|
| Signups + Raid Builder | **launch-critical** | weekly availability by day, lockouts, drag-and-drop raid groups per night, "who's free Friday" |
| Performance | **launch-critical** | WCL API: tier parses, ranks, pulled automatically next to the roster |
| Loot | **launch-critical** | full ledger from the addon, search by item/player, loot priority, Raider flag, "who's next" |
| Roster / Recruiting | high | applications, interview notes, trial clock, rank promotion |
| Player Score | medium | auto-calculated from attendance, WCL, signup reliability; council adds notes |
| Economy / Bank | medium | bank contents, material needs vs raid consumable demand |
| Map | Jason's | existing wow-forever map, guild pins, optional live dots |
| Sim | link-out | existing sim.decades.gg, via setup-code links built from the gear export |
| AI assistant | later | ask questions over signups, loot, logs; drafts raid comps and feedback |
| Leadership dashboard | later | capability model, coverage per bucket |

### 4. Discord bot
Signup reminders and links, raid-night announcements, loot award feed. Added as routes on the
**existing** `discordInteractions` router (decades_app application), not a new bot.

## Module contract
Every module defines: data source (addon / adapter / WCL / web form), schema, permissions,
web UI, what it pushes into the game.

## Build order (proposed)
1. `guild-hub` Functions codebase + Firestore + rules/emulator tests in `decades-prod`; reuse decades_app login; roster.
2. Signups + Raid Builder (replaces the Google sheet; usable with no addon at all).
3. WCL Performance pull.
4. Addon core + loot + desktop companion upload, giving the Loot ledger.
5. Attendance, bank, gear, then Player Score and Economy.
6. Min-max suite: `SimProvider` for both engines, fight-adjusted re-sims, critique cards, mentor overlay.
7. Go-there: map deep links + routes, addon `nav` arrow, Discord `/where`.
8. Public guild page + member cards; AI assistant; Discord bot extras.

Steps 1–3 need **no addon**. They can ship before launch and cover the old sheet's job.

## Open questions
- [ ] **What have Reed and Leer already built?** (the AI tool shown at the end of the video) Extend it, or replace it?
- [ ] Launch date and the hard deadline for signups being live.
- [ ] Loot rules: pure loot council? Raider priority weighting? Is the ledger visible to everyone?
- [ ] Does WarcraftLogs support WoW Forever at launch (API/zone IDs)? If not, our own combat-log parser feeds the Performance view.
- [ ] WCL API v2: whose client credentials, and is the points quota enough for report events on every kill?
- [ ] **Access to decades_app** (the web app with Discord sign-in; its repo isn't public). Does the hub live inside it or on its own Hosting site?
- [ ] Firebase roles for us on `decades-prod` (a dev/staging project, or emulator only?) and the Blaze budget/alerts owner.
- [ ] forever_sim maintainer (commits are by "John Anderson"; is that Leer?): agree on the `SimConfig` setup-code contract.
- [ ] Third-party addons: RCLootCouncil confirmed. Others (Details!, etc.)?
- [ ] Does WoW Forever have a native guild bank, or is it bank alts?
- [ ] Does Elephant (or any chat logger) exist for Forever?
- [ ] Confirm the Forever interface number (`GetBuildInfo`) and the SavedVariables path.

## Decisions log
- 2026-09-28: One addon + one companion + one backend; features are modules on a shared pipe.
- 2026-09-28: Map (wow-forever) is a module. (Sim part superseded by v4.)
- 2026-09-28: WfPos folds into the addon as `pos`.
- 2026-09-28 (v2): Fit to the Decades GM video. The web app is the primary surface. WCL is integrated, not
  replaced (the guild ranks on WCL). Launch-critical = Signups/Raid Builder, WCL Performance, Loot.
- 2026-09-28 (v3): GM data list added. Principle: collect anything valuable to view, stored as rollups. RCLootCouncil read via adapter, not replaced. Elephant rebuilt as the `chat` module. Sync-to-addon: parses, BiS, accolades in the guild tab.
- 2026-09-28 (v4): Backend = Firebase `decades-prod`, following forever_sim's conventions (Functions 2nd gen nodejs22 us-central1, WIF deploy, Secret Manager). Firestore rollups; addon data written only by Functions; login and Discord bot reuse decades_app. Own-sim plan dropped; integrate with sim.decades.gg via setup-code links.
- 2026-09-28 (v5): Min-max suite (Sim × WCL × Performance, fight-adjusted re-sims, measured critique). Two engines behind `SimProvider`: forever_sim (headline/BiS) + WoW4_SiMs (healers, raid sim, timeline). Go-there directions on every surface. Public guild page + member cards. Supersedes v4's "own sim dropped".
