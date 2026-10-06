# Decades Guild Hub — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans
> to implement each phase plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship the Decades guild hub (spec: `docs/specs/2026-09-28-guild-sync-design.md` v5): one addon,
one Windows companion, one Firebase backend (`decades-prod`), guild web app, min-max suite, directions.

**Architecture:** Addon writes rollups to SavedVariables → companion parses Lua→JSON, uploads via Firebase
Function `ingest`, Firestore stores rollups, Functions-only writes; web app + Discord bot reuse
`decades_app`. Two sim engines behind `SimProvider`. Map deep links for every location.

**Tech Stack:** Lua 5.1 (WoW API, no Ace), Python 3.11+ (companion, stdlib-only), TypeScript +
Firebase Functions 2nd-gen nodejs22 us-central1 + Firestore + Hosting, Vite/React/shadcn (web).

## Global Constraints
- WoW Forever client 1.60.x; interface number read in game (`/dump select(4, GetBuildInfo())`) before first release.
- Addon: no networking, no file I/O, no combat automation. Exits: SavedVariables (logout//reload), chat log (pos), combat log.
- Inbound to game: only `Data.lua` written by companion into the addon folder (TSM/Raider.IO pattern).
- Firebase project `decades-prod` only. Functions codebase `guild-hub`. Deploy via existing WIF workflow pattern. Secrets in Secret Manager.
- Addon-data writes: Functions only. Client writes: own signup entry; notes per claims.
- Companion: stdlib-only Python (no pip installs for v1); polling watcher; credentials in Windows Credential Manager.
- Every number shown carries provenance [F]/[C]/[?]; UI mobile+desktop separate, shadcn, e2e before deploy.
- Unity of naming: addon `DecadesSync`, companion `decades-companion`, functions codebase `guild-hub`, SV file `DecadesSyncDB`.

## Phase map (each phase = its own plan file; start Plan A now)
| Phase | Plan | Status | Blocked by |
|---|---|---|---|
| A | `2026-09-28-planA-addon-companion-pipe.md` — addon core + companion parse/upload/writer loop | ready | nothing |
| B | `2026-09-28-planB-firebase-backend.md` — ingest, Firestore, auth swap, addonData | scaffolded | decades_app access answers |
| C | Signups + Raid Builder + roster web module | task list below | B |
| D | WCL pull (or own combat-log parser) + Performance view | task list below | B + WCL/Forever answer |
| E | Loot module (addon loot capture + RCLootCouncil adapter + ledger) | task list below | A + B |
| F | Min-max suite: SimProvider, fight-adjusted re-sims, critique cards, mentor overlay | task list below | D + forever_sim maintainer pact |
| G | Go-there: map deep links, routes, addon `nav`, Discord `/where` | task list below | A + B |
| H | Public guild page + member cards + accolades/BiS down-sync | task list below | C/D/E live |

## Plan C task list (Signups + Raid Builder)
1. `firestore.rules` additions: `signups/{weekId}/entries/{discordId}` owner-write, guild-read.
2. Web: `/signup` page — week grid (Tue–Mon), day toggles, lockout checkboxes, note; writes own entry.
3. Web: `/raid-builder` (officer): pull week entries, drag roster into N raid frames, comp summary
   (class/role counts from `characters/`), save `raids/{raidId}`.
4. Function `weekRoll` (scheduled Sun 00:00): create next `signups/{weekId}` doc, Discord announce.
5. e2e: signup journey + builder journey.

## Plan D task list (WCL / Performance)
1. If WCL supports Forever: Function `wclPull` (scheduled, client-credentials from Secret Manager) → `parses/{characterId}`.
2. Else: companion combat-log tail adapter → events → Function `logIngest` → same schema (flag `source:"own"`).
3. Web: `/performance` — per boss: Actual vs Expected (from F) vs guild top performer same spec.
4. Metric extractors: cast counts/min, cooldown uses vs available, buff/DoT uptime %, idle GCD, deaths.

## Plan E task list (Loot)
1. Addon `loot` module: `CHAT_MSG_LOOT` capture (dedupe by item+player+5min), council award slash command `/dec loot <player>` on hover item; rows into SV.
2. RCLootCouncil adapter: parse `RCLootCouncil` SV (awards, reroutes) → map to ledger rows.
3. `loot/{autoId}` docs + web `/loot`: search by item/player; per-item "who has it"; priority view (Raider flag).
4. Discord: loot award feed route on existing router.

## Plan F task list (Min-max suite)
1. `SimProvider` TS interface + forever_sim adapter (headless run of its TS engine; setup-code in/out).
2. WoW4_SiMs adapter: `wowsimcli` via Cloud Run job (JSON in → metrics out); whitelist healer/raid-sim/timeline use until its DB is Forever-sourced.
3. Fight-adjusted re-sim: inputs from D's events (duration, active time, targets, buffs, consumes).
4. Four numbers (BiS/Ceiling/Expected/Actual) + gaps; critique card ranked by measured gain (re-sim per fix, batched).
5. Mentor overlay: timeline diff vs guild top parser same spec/boss.
6. Cross-check: both engines >5% apart → audit doc, not silent pick.

## Plan G task list (Go-there)
1. Item-source table (drop/vendor/rep/quest/craft) seeded from map POIs + item data; resolver order: own→bank→crafter→world.
2. Map deep links `#lat/lng/zoom` from wow-forever map; route builder via flight/zeppelins POIs.
3. Addon `nav` module: TomTom-style arrow (`UnitPosition`), `/dec go <target>`; step list to chat.
4. Discord `/where <item|npc>`: sources + holders + crafters + map link (route on existing router).

## Plan H task list (Public face)
1. `/guild` public page: progression, region rank, parse averages, accolades, rivalries; opt-out flag per member.
2. Member card page + share-as-image (og-image render); tooltips in addon show parse/BiS/accolade via Data.lua.
3. BiS lists from forever_sim optimizer (M5.7) → Data.lua down-sync.

## Self-review
- Spec coverage: Firebase(B), data catalog waves 1(A core,E, plus rep/inv/pos in A), sync-to-addon(H), sim(F), directions(G), public(H), signups(C), WCL(D), Discord routes (C,E,G). Map live-dots & zone-time & sightings & chat & pvp & deaths etc. from the data catalog → rolled into A's `pos`/`census` modules + E/F follow-ups; each named in A's module list.
- Placeholders: none; later-phase items are scoped task lists by design (each gets a full plan at phase start).
- Types: `DecadesSyncDB` schema, `Upload{schemaVersion,seq,char,deltas}` and `Data.lua` emitter names fixed in A and reused in B/H.
