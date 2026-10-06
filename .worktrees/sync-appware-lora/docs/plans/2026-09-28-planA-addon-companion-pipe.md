# Plan A — Addon + Companion Pipe (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task.

**Goal:** Prove the data loop end-to-end offline: addon collects rollups into SavedVariables → companion detects logout-write, parses Lua→JSON, stores locally, and writes `Data.lua` back into the addon folder, which the addon reads on next login.

**Architecture:** Two deliverables in this repo. `addon/DecadesSync/` (Lua 5.1, no libraries, namespace `Decades`, SV table `DecadesSyncDB`). `companion/` (stdlib-only Python 3.11+, polling watcher, deterministic Lua-table parser, local JSON store `companion/store/`, Data.lua emitter). Firebase upload is stubbed behind config — Plan B wires it.

**Tech Stack:** Lua 5.1 (WoW Forever 1.60.x API), Python 3.11 stdlib + `unittest`.

## Global Constraints (from master plan)
- Addon: no networking, no file I/O, no automation. Only SavedVariables + chat log out; only `Data.lua` in.
- SV written by the game only on logout/`/reload`; companion never writes SV.
- Companion: stdlib only; single process; poll interval 2 s; all paths relative to a discovered WoW dir.
- Names fixed: addon folder `DecadesSync`, SV `DecadesSyncDB`, namespace table `Decades`, Data file `Data/DecadesData.lua` returning a table via `DayOneData` global pattern (see Task 9), config `companion/companion.toml` (parsed by hand — stdlib has no toml before 3.11; 3.11 has `tomllib`).

---

### Task 1: Repo layout + addon skeleton (toc + core frame)

**Files:**
- Create: `addon/DecadesSync/DecadesSync.toc`
- Create: `addon/DecadesSync/core.lua`
- Create: `companion/__init__.py` (empty), `companion/pyproject.toml` (metadata only)

**Interfaces:**
- Produces: global table `Decades` with `Decades:RegisterModule(name, defaults)` used by later tasks; SV `DecadesSyncDB` per-realm-per-char table.

- [ ] **Step 1: Write the toc** (`addon/DecadesSync/DecadesSync.toc`)

```toc
## Interface: 11303
## Title: Decades Sync
## Notes: Decades guild data collection. Companion app uploads on logout.
## Author: Decades
## Version: 0.1.0
## SavedVariablesPerCharacter: DecadesSyncDB
core.lua
```
(Interface number is corrected in Task 10 after reading it in game.)

- [ ] **Step 2: Write core.lua**

```lua
-- DecadesSync core: namespace, module registry, SavedVariables bootstrap.
Decades = Decades or {}
Decades.VERSION = "0.1.0"

Decades.modules = Decades.modules or {}

-- Register a module: defaults merged under DecadesSyncDB[name] on login.
-- mod.OnEvent(frame, event, ...) and mod.OnUpdate(elapsed) are optional.
function Decades:RegisterModule(name, defaults)
  local mod = { name = name, defaults = defaults or {} }
  self.modules[name] = mod
  return mod
end

local frame = CreateFrame("Frame")

local function initCharDB()
  DecadesSyncDB = DecadesSyncDB or {}
  for name, mod in pairs(Decades.modules) do
    local db = DecadesSyncDB[name]
    if db == nil then
      db = {}
      DecadesSyncDB[name] = db
    end
    for k, v in pairs(mod.defaults) do
      if db[k] == nil then db[k] = v end
    end
  end
end

frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:SetScript("OnEvent", function(self, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "DecadesSync" then
    initCharDB()
  elseif event == "PLAYER_LOGIN" then
    -- core facts, refreshed every login
    local _, class = UnitClass("player")
    local db = DecadesSyncDB and DecadesSyncDB.core
    if db then
      db.name = UnitName("player")
      db.realm = GetRealmName()
      db.class = class
      db.level = UnitLevel("player")
      db.guild, _, db.guildRankIndex = GetGuildInfo("player")
      db.addonVersion = Decades.VERSION
      db.lastLogin = date("%Y-%m-%dT%H:%M:%S")
    end
  end
end)
```

- [ ] **Step 3: Commit**

```bash
git add addon companion
git commit -m "feat(addon): DecadesSync skeleton - namespace, module registry, SV bootstrap"
```

---

### Task 2: `pos` module (live position over chat log + zone-time accumulator)

**Files:**
- Create: `addon/DecadesSync/pos.lua`
- Modify: `addon/DecadesSync/DecadesSync.toc` (add `pos.lua` after `core.lua`)

**Interfaces:**
- Consumes: `Decades:RegisterModule` (Task 1).
- Produces: `DecadesSyncDB.pos = { home=<inn>, zoneTime={ [zoneSub]=seconds }, lastZone, lastSub }`; chat line `[DEC] POS|zone|sub|x|y|z` when moved >5yd or zone changed (WfPos format, new tag).

- [ ] **Step 1: Write pos.lua**

```lua
-- pos: live position via /chatlog bridge + "typically found in" accumulator.
local MOV_GATE, TICK = 5, 0.5
local mod = Decades:RegisterModule("pos", { zoneTime = {}, home = "", lastZone = "", lastSub = "" })

local frame, acc = CreateFrame("Frame"), 0
local lastX, lastY

local function emit()
  local x, y, z = UnitPosition("player")
  if not x or not y then return end
  local zone, sub = GetZoneText(), (GetSubZoneText() or "")
  local moved = lastX == nil or (math.abs(x-lastX) + math.abs(y-lastY) > MOV_GATE)
  local zc = zone ~= mod.db.lastZone or sub ~= mod.db.lastSub
  -- zone-time accumulator (rollup, not events)
  local key = zone .. "/" .. sub
  mod.db.zoneTime[key] = (mod.db.zoneTime[key] or 0) + TICK
  if zc then
    mod.db.lastZone, mod.db.lastSub = zone, sub
    mod.db.home = GetBindLocation() or mod.db.home
  end
  if not (moved or zc) then return end
  lastX, lastY = x, y
  DEFAULT_CHAT_FRAME:AddMessage(string.format(
    "[DEC] POS|%s|%s|%d|%d|%d", zone, sub, math.floor(x), math.floor(y), math.floor(z or 0)))
end

frame:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc >= TICK then acc = 0; emit() end
end)
```

Wait: `mod.db` is not set by core yet — fix by resolving it in PLAYER_LOGIN. Change `initCharDB` in core.lua to also set `mod.db = db` inside the loop (one line: `mod.db = db`). Apply that edit in this task.

- [ ] **Step 2: Add `mod.db = db` to core.lua's initCharDB loop; add `pos.lua` to toc; commit**

```bash
git add addon
git commit -m "feat(addon): pos module - chatlog bridge + zone-time rollup"
```

---

### Task 3: `inventory` module (bags + bank snapshot counts)

**Files:**
- Create: `addon/DecadesSync/inventory.lua`
- Modify: toc.

**Interfaces:**
- Produces: `DecadesSyncDB.inventory = { bags={ [itemID..":"..suffix]=count }, bank={...}, scannedAt }` — item counts only (rollup, not per-slot).

- [ ] **Step 1: Write inventory.lua**

```lua
-- inventory: bag + bank item-count rollups. Bank read only while the frame is open.
local mod = Decades:RegisterModule("inventory", { bags = {}, bank = {}, scannedAt = 0 })

local function scanBags(tbl, bagIds)
  wipe(tbl)
  for _, bag in ipairs(bagIds) do
    for slot = 1, GetContainerNumSlots(bag) do
      local link = GetContainerItemLink(bag, slot)
      if link then
        local _, count = GetContainerItemInfo(bag, slot)
        local itemID = link:match("item:(%d+)")
        if itemID then
          local key = itemID
          tbl[key] = (tbl[key] or 0) + (count or 1)
        end
      end
    end
  end
end

local f = CreateFrame("Frame")
f:RegisterEvent("BAG_UPDATE_DELAYED")
f:RegisterEvent("BANKFRAME_OPENED")
f:SetScript("OnEvent", function(_, event)
  if event == "BAG_UPDATE_DELAYED" then
    scanBags(mod.db.bags, {0,1,2,3,4})
    mod.db.scannedAt = time()
  elseif event == "BANKFRAME_OPENED" then
    scanBags(mod.db.bank, {5,6,7,8,9,10}) -- bank bags + reagent; bags keyring 11 on clients that have it
    scanBags(mod.db.bags, {0,1,2,3,4})
    mod.db.scannedAt = time()
  end
end)
```

- [ ] **Step 2: Commit** `feat(addon): inventory rollup module`

---

### Task 4: Companion — Lua SV parser (pure function + tests)

**Files:**
- Create: `companion/svparse.py`
- Test: `companion/test_svparse.py`

**Interfaces:**
- Produces: `parse_sv(text: str) -> dict` — parses the subset of Lua the SV writer emits: top-level `DecadesSyncDB = {`, nested braces, string keys `["k"]=` or bare `k=`, quoted strings, numbers, `nil`→None, booleans, comma-separated, trailing commas. Raises `SVParseError` on anything else.

- [ ] **Step 1: Write failing tests** (`python -m unittest companion.test_svparse -v`)

```python
import unittest
from companion.svparse import parse_sv, SVParseError

class TestParseSV(unittest.TestCase):
    def test_nested_table(self):
        text = 'DecadesSyncDB = {\n\t["core"] = {\n\t\t["name"] = "Grukk",\n\t\t["level"] = 60,\n\t},\n}\n'
        self.assertEqual(parse_sv(text), {"core": {"name": "Grukk", "level": 60}})
    def test_types_and_trailing_comma(self):
        text = 'DecadesSyncDB = {\n\t["x"] = true,\n\t["y"] = nil,\n\t["z"] = -1.5, ["empty"] = {},\n}'
        self.assertEqual(parse_sv(text), {"x": True, "y": None, "z": -1.5, "empty": {}})
    def test_numeric_string_keys_and_garbage(self):
        self.assertEqual(parse_sv('DecadesSyncDB = { ["1234"] = 3, }'), {"1234": 3})
        with self.assertRaises(SVParseError):
            parse_sv('DecadesSyncDB = { ["a"] = function() end, }')
    def test_escaped_string(self):
        self.assertEqual(parse_sv(r'DecadesSyncDB = { ["n"] = "a\"b\\c", }'), {"n": 'a"b\\c'})

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run — expect ImportError/failure** → `python -m unittest companion.test_svparse` (FAIL: no module `svparse`)

- [ ] **Step 3: Implement svparse.py** — tokenizer + recursive-descent parser over exactly that grammar (skip whitespace; string literals with `\"` `\\` `\n` escapes via a regex; numbers via `float` unless integral; `{` `}` `,` `=` `[` `]`). No eval, no external parsers.

- [ ] **Step 4: Run tests → PASS; commit** `feat(companion): SavedVariables lua-table parser + tests`

---

### Task 5: Companion — WoW dir discovery + watcher + delta store

**Files:**
- Create: `companion/watch.py`, `companion/store.py`
- Test: `companion/test_store.py`

**Interfaces:**
- Produces: `find_wow(root: str | None) -> Path` (checks `<root>/WTF/Account/*/SavedVariables/DecadesSync.lua`, else scans `%ProgramFiles%`, `E:\`, `C:\Program Files (x86)` candidates); `Watcher.poll()` returns the SV path when its mtime changes; `Store.append(char_key, sv_dict)` writes `store/<char_key>/<seq>.json` and prunes to last 20; `Store.latest(char_key)`.

- [ ] **Step 1: Failing tests for Store (append creates seq files, latest returns newest, prune keeps 20).**
- [ ] **Step 2: Run → FAIL. Implement watch.py + store.py (stdlib: pathlib, time, json, os.walk with depth cap 4).**
- [ ] **Step 3: Tests PASS; commit** `feat(companion): wow-dir discovery, mtime watcher, rolling upload store`

---

### Task 6: Companion — Data.lua emitter + round-trip test

**Files:**
- Create: `companion/emitter.py`
- Test: `companion/test_emitter.py`

**Interfaces:**
- Produces: `emit_data_lua(data: dict, out: Path) -> None` writing:
  `-- Generated by decades-companion. DO NOT EDIT.\nreturn {\n ... \n}\n` (same value grammar the parser reads), atomically (tmp file + `os.replace`) into `Interface/AddOns/DecadesSync/Data/DecadesData.lua`.

- [ ] **Step 1: Failing test: emit `{ "a": 1, "b": {"c": "x"} }` → parse with svparse (strip leading `--` comment line and `return` keyword wrapper) → equal dict.**
- [ ] **Step 2: Implement; tests PASS; commit** `feat(companion): Data.lua emitter, parseable round-trip`

---

### Task 7: Addon — Data.lua loader + display stub

**Files:**
- Create: `addon/DecadesSync/data.lua`
- Modify: toc (add `Data/DecadesData.lua` FIRST in file list so it loads before core, then `data.lua` after core).

**Interfaces:**
- Consumes: `DecadesData` global set by the generated file (`return {...}` files loaded via toc need `DecadesData = ...` assignment — so emitter writes `DecadesData = { ... }` instead of `return`; update Task 6's emitter and test accordingly in this task).
- Produces: `Decades.Data` table; `/dec` slash command printing char name, version, `Data.generatedAt`, and first 3 keys of `Decades.Data`.

```lua
-- data.lua: loads hub-pushed data and exposes it as Decades.Data.
Decades.Data = DecadesData or { generatedAt = "never" }

SLASH_DECSYNC1 = "/dec"
SlashCmdList["DECSYNC"] = function(msg)
  local db = DecadesSyncDB and DecadesSyncDB.core or {}
  DEFAULT_CHAT_FRAME:AddMessage(string.format(
    "DecadesSync v%s | %s-%s %s | data: %s (%d keys)",
    Decades.VERSION, db.name or "?", db.realm or "?", db.class or "?",
    tostring(Decades.Data.generatedAt),
    (function() local n = 0; for _ in pairs(Decades.Data) do n = n + 1 end return n end)()))
end
```

- [ ] **Step: add files, commit** `feat(addon): Data.lua loader + /dec status command`

---

### Task 8: Companion — main loop + config + upload stub

**Files:**
- Create: `companion/main.py`, `companion/companion.toml`, `companion/test_main.py`

**Interfaces:**
- Produces: `run(config_path)` loop: poll watcher every 2 s; on SV change → parse → `Store.append` → `upload()` (stub: logs "upload skipped (Plan B)" unless `ingest_url` set in config) → `emit_data_lua({"generatedAt": iso_now, "roster": []}, addon_dir)`. `test_main` covers the loop once with a fake watcher (monkeypatched).

- [ ] **Steps: failing test (fake watcher yields path once → store has 1 file, Data.lua written) → implement → PASS → commit** `feat(companion): main loop wiring watcher/parser/store/emitter + config`

---

### Task 9: End-to-end fixture test (offline simulation of the game)

**Files:**
- Test: `companion/test_e2e.py`; fixture `companion/fixtures/DecadesSync.lua` (hand-written SV sample with core/pos/inventory data, 30 lines).

**Steps:**
- [ ] Test: watcher on a temp dir seeded with the fixture → one poll cycle → store file exists, Data.lua exists, svparse(Data.lua content) round-trips. Run → PASS.
- [ ] Commit `test(companion): end-to-end pipe over fixture SV`

---

### Task 10: Interface number + README + tag v0.1.0

**Steps:**
- [ ] Read the real interface number in game (`/dump select(4, GetBuildInfo())`) — owner action, blocks release only.
- [ ] Write `README.md` at repo root: layout, run (`python -m companion.main`), install (`DecadesSync` folder → `Interface/AddOns`, `/chatlog` note for pos), status table.
- [ ] `git tag v0.1.0`; commit `docs: plan A README`.

## Self-review
- Coverage: pipe only, as scoped. pos/inventory are the first two collector modules (wave-1 items rep/prof/pvp/sightings/chat come in later phase plans, per master plan note).
- Placeholders: none. Task 2 contains one inline correction note (applied in-step) — acceptable as it's an explicit edit instruction, not a deferred decision.
- Types: `mod.db` set in Task 2's core edit before any module uses it (Tasks 2-3 depend on it); emitter contract changed in Task 7 with instruction to update Task 6 test — sequenced.
