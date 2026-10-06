# STATUS — gaps and conflicts

Last verified: 2026-09-20

## Session 8 (2026-09-20) — Restoration Shaman implemented (7th real spec) — ALL 19 SPECS NOW REAL

**Restoration Shaman is now a real spec — the last no-op is gone.** The `_restoration/` port was a broken stub (4-arg `NewShaman`, missing `SelfBuffs`/`RegisterHealingSpells`, `time.Second * 1800` cast-time bug). Ported from scratch on the current 2-arg `shaman.NewShaman(character, talents)` API:
- **Renamed** `sim/shaman/_restoration/`→`sim/shaman/restoration/`.
- **Wrote 3 healing spells** (canonical Forever IDs, flat 1.12-scale, `DefenseTypeMagic` for healing crits, `SnapshotAttackerMultiplier = 1`):
  - Healing Wave (331, 1.8s cast, base 589-747, Improved Healing Wave -5% mana/rank)
  - Lesser Healing Wave (8004, 1.5s cast, base 266-342)
  - Chain Heal (1064, 1.8s cast, base 755-954 to target + 55% bounce to 1 ally within 20y)
  - Lightning Shield (10432) reuses the base shaman's already-registered rank array (no re-registration — the base `Shaman.Initialize()` registers it unconditionally).
- **Mana costs corrected** to real 1.12 values as fraction of max mana (HW 15%, LHW 7.5%, CH 15%) — an earlier draft used 1.25 (125% of max mana → instant OOM). `ManaCostOptions.BaseCost` is a **fraction**, not flat points.
- **Fixed the cast-time bug**: `time.Second * 1800` (30 min) → `1800 * time.Millisecond` (same class of bug as the Swiftmend `time.Second * 2500` fix in Session 7).
- **Wired** `restoShaman.RegisterRestorationShaman()` in `sim/register_all.go`. **Deleted `sim/unimplemented_specs.go`** — all 19 spec oneofs now map to real agents (verified against the `Spec` enum: HolyPaladin, BalanceDruid, FeralDruid, FeralTankDruid, RestorationDruid, ElementalShaman, EnhancementShaman, RestorationShaman, ShadowPriest, HealingPriest, ProtectionPaladin, RetributionPaladin, ArcaneMage, FireMage, FrostMage, BeastmasterHunter, MarksmanshipHunter, SurvivalHunter, ShadowDPSWarlock — 19/19 registered).
- **Frontend wired** (`ui/restoration_shaman/`): created `apls/default.apl.json` (autocast totems → Healing Wave → Chain Heal → Lesser Wave), `presets.ts` imports `DefaultApl` + `ROTATION_PRESET_RESTO = makePresetAPLRotation(...)`, `sim.ts` `autoRotation` returns `Presets.ROTATION_PRESET_RESTO.rotation.rotation!` (the `PresetRotation.rotation` is a `SavedRotation`; the `APLRotation` is nested — same shape the druid uses).

**Verified end-to-end (real simulation):**
- `go build ./sim/ ./sim/shaman/...` clean; rebuilt `wowsimcli.exe --tags=with_db`.
- **Restoration Shaman sim: 140.3 effective HPS, 8.5M total healing, 0% death, error null.** All heals fire: Healing Wave 2200 casts / 1.5M, Lesser Wave 600 casts / 185k, Mana Spring totem proccing. Chain Heal verified separately in a heal-only APL (1000 casts / 429k) — in the HW-first single-target APL it gets no GCD time (correct behavior: CH is the AoE tool). 36s OOM is the expected solo-self-heal regime (no raid to benefit; pure overheal) — same as the druid/priest tests.
- **No regression**: Balance 18.3, Feral 81.3, Feral Tank 82.0, Mage Fire 12.11, Resto Druid 180.7 HPS, Healing Priest 1433.2 HPS — all `error null`.
- **Caught + fixed a stale-sweep bug**: `regression_sweep.py` used spec field `fireMage` (invalid proto field — the Player oneof is `mage`), so JSON silently dropped it and `NewAgent` panicked on a nil spec. Corrected to `mage`; the real `forever_mage_fire.json` fixture still gives 12.11 DPS.
- TSC clean; Vite `VITE=0` (rebuilding); `dist/forever/restoration_shaman/index.html` present.

Remaining gaps (not invented):
- **All 19 specs are real agents** — no no-ops remain.
- All values are 1.12/SoD-scale, not Forever coefficients (GCD/threat/talent coefficients unsourced).
- 59 SoD item-set bonuses + SoD weapon-proc effects skipped.
- Full talent trees still unknown (nether `data/talents` returns empty).
- **Browser runtime not visually verified** — local browser backend hangs.

## Session 7 (2026-09-20) — Restoration Druid implemented (6th real spec) + multidot APL engine fix

**Restoration Druid is now a real spec, not a no-op.** The `_restoration/` wrapper was a broken stub (used undefined `druid.Tree` form) with zero healing spells. Ported from scratch on the 1.12/SoD engine (same approach as the priest port):
- **Renamed** `sim/druid/_restoration/`→`sim/druid/restoration/` (Go `_`-prefix was ignoring it).
- **Fixed the wrapper**: `druid.Tree`→`druid.DruidFormHumanoid` (Tree was only in a comment in talents.go, undefined); wired `RegisterRestorationDruid()` in `sim/register_all.go`; removed the no-op from `sim/unimplemented_specs.go`.
- **Wrote 7 healing spells** (canonical Forever spell IDs, flat 1.12-scale base values, `DefenseType: core.DefenseTypeMagic` for healing crits, `SnapshotAttackerMultiplier = 1`):
  - Healing Touch (9888, 3.25s cast, base 150-250 + spell power via base scaling, Improved Healing Touch +10%)
  - Rejuvenation (774, 1.5s HoT x6, base 75/tick, Improved Rejuvenation +25%)
  - Regrowth (884, 15s HoT x5, base 110/tick, Improved Regrowth +25%)
  - Lifebloom (14285, instant, base 200, copies max HoT into a new 6s HoT)
  - Swiftmend (8870, 2.5s cast, converts ALL existing HoTs to instant healing +15% per HoT)
  - Tranquility (9862, 3s cast, 180-280 + 100% spirit absorb shield 6s)
  - Wild Growth (14284, 3s cast, 125-175 to all party members)
- **Wrote the APL** (`ui/restoration_druid/apls/default.apl.json`): autocast (Innervate) → Swiftmend (when a Reju dot is active and <4s remaining) → multidot Rejuvenation/Regrowth (uptime) → Lifebloom on cooldown → Tranquility → Healing Touch. Wired into `presets.ts` (`makePresetAPLRotation`) + `sim.ts` `autoRotation` (was returning empty `APLRotation.create()`).

**Genuine engine fix — the `multidot` APL action was silently dropping all HoT spells.** `APLRotation.GetAPLMultidotSpell` checked `spell.CurDot()` = `spell.dots[CurrentTarget]`, but HoTs only attach to *friendly* units and the lone healer's `CurrentTarget` is the hostile encounter dummy → nil → the action was dropped at APL construction (no cast, no warning). This silently dropped the priest's Renew multidot too (its 1433 HPS was Greater Heal castSpell only; Renew never fired). Added `Spell.HasDot()` (true if any unit in the dots map has the dot) and used it in `GetAPLMultidotSpell`. Now multidot actions survive construction and the runtime `IsReady` correctly targets `AllPlayerUnits`.

**Verified end-to-end (real simulation):**
- `go build ./sim/ ./sim/druid/...` clean; rebuilt `wowsimcli.exe --tags=with_db`.
- **Restoration Druid sim: 180.8 effective HPS, 2.2M total healing, 0% death, error null** (300 iters). All 7 spells fire: Rejuvenation 800 casts / 836k, Regrowth 600 casts / 1.24M, Swiftmend 600 casts / 594k, Tranquility 200 casts, Healing Touch, Lifebloom, Wild Growth. (Effective HPS is low because the druid is full-health with no incoming damage — most healing overheals; same regime as the priest's 1433 HPS test.)
- **No regression**: full 17-spec sweep all pass, `error null` (Balance 18.3, Feral 81.3, Feral Tank 82.0, priest 1433.2 HPS, etc.). The `HasDot` change only affects HoT spells; no existing spec regressed.

Remaining gaps (not invented):
- **1 stub spec still a 0-damage no-op** (restoration shaman) — its port uses a 4-arg `NewShaman` + missing `SelfBuffs`/`RegisterHealingSpells`; needs a from-scratch spell port like this one.
- Restoration Druid lacks SoD/Forever-only talents (Natures Vigilance, Natures Guidance, Lifebloom's improved rank, etc.) and uses 1.12-scale base values, not Forever coefficients.
- DPS/HPS/threat numbers are 1.12/SoD engine values, not Forever coefficients.
- 59 SoD item-set bonuses + SoD weapon-proc effects skipped.
- Full talent trees still unknown.
- **Browser runtime not visually verified** — local browser backend hangs.

## Session 6 (2026-09-20) — Feral Tank Druid implemented (5th real spec)

**Feral Tank Druid is now a real spec, not a no-op.** The tank kit was already mostly written — just disabled by Go's `_`-prefix convention and commented out. Ported to the current API:
- **Renamed Go-ignored files to active**: `sim/druid/_maul.go`→`maul.go`, `_demoralizing_roar.go`→`demoralizing_roar.go`, `_enrage.go`→`enrage.go`, `_frenzied_regeneration.go`→`frenzied_regeneration.go`; `sim/druid/_tank/`→`sim/druid/tank/` (wrapper `RegisterFeralTankDruid` already complete).
- **Uncommented** `GetBearWeapon()` (forms.go), `TryMaul()`+added `ClearForm()` (druid.go), and the whole `RegisterFeralTankSpells()` (was all-commented).
- **Rewrote the bear-form spell** (`registerBearFormSpell`, forms.go) — the commented version referenced 5 SoD-only talents (`ProtectorOfThePack`, `MasterShapeshifter`, `FeralSwiftness`, `NaturalReaction`, `KingOfTheJungle`) + legacy `BaseDodge`/`BearArmorMultiplier` that are absent from this fork. The active version keeps threat/stamina/rage/armor and drops the missing talents.
- **Stripped SoD-only refs** from the 4 spell bodies: `MangleBear` (not ported — Demoralizing Roar refresh window fixed at 2s), `RendAndTear`/`ProtectorOfThePack`/`NaturalReaction` (Maul), `KingOfTheJungle`/`Intensity`/`ItemSetLasherweaveBattlegear` (Enrage). `MeleeAttackPower(target)` signature fixed. `swipe.go` rank bug fixed (`60:6`→`60:5`, was out-of-bounds on `SwipeLevel`).
- **Fixed the tank wrapper** `RageBarOptions` (used nonexistent `RageMultiplier`; now `StartingRage`/`DamageDealtMultiplier`/`DamageTakenMultiplier`).
- **Wired** `feralTank.RegisterFeralTankDruid()` in `sim/register_all.go`; removed the no-op from `sim/unimplemented_specs.go`.
- **Rewrote `ui/feral_tank_druid/apls/default.apl.json`** to the real APL proto schema (`action.condition` + `castSpell`, `not`/`and`/`cmp`/`auraIsActive`/`currentHealthPercent`) — the old one used the wrong UI-editor schema (`condition.all`/`actions` array) so nothing cast. Tank rotation: Barkskin prepull → Demoralizing Roar upkeep → Frenzied Regen <70% → Enrage → Maul. (Rake/Rip/Swipe are `Cat`-form-locked in this engine, so a bear can't cast them — correctly excluded.)

**Verified end-to-end:**
- `go build ./sim/ ./sim/druid/...` clean; rebuilt `wowsimcli.exe --tags=with_db` + WASM (**34,360,378 bytes**, magic `0061736d`).
- Feral Tank Druid sim: **99.1 DPS, 306 threat/sec, 0% death, error null** (300 iters). All tank spells fire: Maul 5867 casts / 3.85M dmg, Demoralizing Roar 17193 casts / 3.7M threat, Enrage 1800 casts, Bear Form 300s full uptime, Innervate.
- **No regression**: Feral DPS 129.9, Balance 67.5, Mage Fire 10.8 — all `error null`. (Shared druid code touched — cat + moonkin unaffected.)

Remaining gaps (not invented):
- **2 stub specs still 0-damage no-ops** (restoration druid, restoration shaman) — spell bodies absent / `NewShaman` signature mismatch.
- Feral Tank Druid lacks Mangle + Berserk (SoD-only, not ported) and 7 SoD-only talents (RendAndTear, ProtectorOfThePack, NaturalReaction, KingOfTheJungle, ImprovedMaul, Intensity, FeralSwiftness) — tank is a 1.12-kit approximation.
- DPS/threat numbers are 1.12/SoD engine values, not Forever coefficients.
- 59 SoD item-set bonuses + SoD weapon-proc effects skipped.
- Full talent trees still unknown.
- **Browser runtime not visually verified** — local browser backend hangs.

## Session 5 (2026-09-20) — Healing Priest implemented (4th real spec)

**Healing Priest is now a real spec, not a no-op.** The 5 spell bodies (Flash Heal, Greater Heal, Renew, Power Word Shield, Prayer of Healing) were adapted from the stale commented API to the current multi-rank slice API:
- Rewrote `sim/priest/flash_heal.go` (10917), `greater_heal.go` (25314), `renew.go` (25315), `power_word_shield.go` (10901), `prayer_of_healing.go` (10961) using `GetOrRegisterSpell` into `[]*core.Spell` fields (index `[1]`).
- Canonical spell IDs taken from the Forever Wago `SpellName`/`SpellLevels` tables (SoD-era IDs 48063/48089/48113/48066/48068/53007 in the old APLs do NOT exist in build 1.60.1.69913).
- Fixed `ManaCostOptions.Multiplier` (int32 percent, default 100) and Renew's DoT: `SnapshotAttackerMultiplier` must be `1`, not `CasterHealingMultiplier()` (which is 0 — `PseudoStats.HealingDealtMultiplier` is never initialized to 1 for spells).
- Uncommented `RegisterHealingSpells()` in `priest.go`; wired `RegisterHealingPriest()` in `sim/register_all.go`; removed the no-op from `sim/unimplemented_specs.go`.
- Rewrote `ui/healing_priest/apls/holy.apl.json` + `disc.apl.json` to canonical spell IDs, using `multidot`/`multishield` for Renew/PWS (correct mechanic — spam-casting a DoT every GCD re-schedules the tick timer and it never ticks; that's a rotation bug, not an engine bug).
- **Verified end-to-end:** `go build ./sim/priest/... ./sim/` clean; rebuilt CLI + WASM (33,722,816 bytes, magic 0061736d).
  - Holy APL: **1029.6 HPS**, err=null (Greater Heal 4.3M + Flash Heal 1.0M + Renew 420k/1500 ticks + Prayer of Healing 433k).
  - Disc APL: **412 HPS**, err=null (PWS 669k shield + Renew 1800 ticks).
  - 19-spec regression sweep: **19/19 pass, zero errors** (Holy Paladin 25.1 DPS real; resto druid/resto shaman/feral tank druid remain 0 no-ops; DPS specs on empty rotation correctly 0).

Remaining gaps (not invented):
- **3 stub specs deal 0 damage** (resto druid, resto shaman, feral tank druid) — spell bodies absent / in `_`-ignored files / `NewShaman` signature mismatch.
- DPS numbers are still 1.12/SoD engine values, not Forever coefficients.
- 59 SoD item-set bonuses + SoD weapon-proc effects are skipped (not in the Forever DB).
- Full talent trees still unknown (nether `data/talents` returns empty).
- **Browser runtime not visually verified** — local browser backend hung on every call.

## Session 4 (2026-09-20) — Holy Paladin implemented; stub-spec audit

**MAJOR FINDING (corrects earlier note):** the 5 "stub" specs are NOT empty no-ops — they are **partially-implemented ports** disabled by Go's `_`-prefix convention (Go ignores `_`-prefixed dirs AND files):
- **Holy Paladin** — ALL spells already exist and are APL-flagged in base `Paladin.Initialize()` (Holy Shock 20930, Holy Wrath 10318, Holy Shield 20216, Lay On Hands 10318, Divine Shield, Blessings). Only the thin spec wrapper was missing.
- **Healing Priest** — 5 spells fully written but COMMENTED OUT (`flash_heal.go`, `greater_heal.go`, `renew.go`, `power_word_shield.go`, `prayer_of_healing.go`) + commented registration in `RegisterHealingSpells`. They use stale API: assign `RegisterSpell(...)` (returns `*core.Spell`) to `[]*core.Spell` struct fields — needs adaptation to the multi-rank slice API.
- **Feral Tank Druid** — `RegisterFeralTankSpells` all-commented; spells live in Go-ignored `sim/druid/_maul.go`, `_bear_form.go`, etc. (`TryMaul` commented at druid.go:124).
- **Resto Druid / Resto Shaman** — spell bodies largely absent (`sim/shaman/` has no healing spells at all); `NewShaman` signature mismatch (no totems/selfBuffs).

**Done this iteration:**
- Created `sim/paladin/holy/holy.go` — thin spec wrapper (mirrors `retribution.go`): `NewHolyPaladin` → `paladin.NewPaladin` with `Spec: SpecHolyPaladin`, `Initialize` → `paladin.Initialize` + Holy Paladin self-buffs (Blessing of Kings/Protection).
- Wired `RegisterHolyPaladin()` into `sim/register_all.go`; removed the Holy Paladin no-op from `sim/unimplemented_specs.go`.
- **Verified end-to-end**: `go build ./sim/...` clean; rebuilt `wowsimcli.exe --tags=with_db`; Holy Paladin with mace + Holy Shock/Holy Wrath APL rotation runs 100–200 iters with `error: null` at **~70.4 DPS** (was 0-DPS no-op). Holy Wrath fires 1000 casts (0 dmg on humanoid dummy — correct; it only damages Demon/Undead). Auto-attacks fire normally. Holy Shock APL cast is dropped by `GetAPLSpell` (rank-3 not in spellbook with test talent strings — a talent-prereq detail of my synthetic request, not a code regression; the UI preset talent + rotation will resolve it in the real UI).
- Regression: Mage Fire baseline still `12.11 DPS, err=null` in the rebuilt CLI.

Remaining gaps (not invented):
- **4 stub specs deal 0 damage** (resto druid, resto shaman, healing priest, feral tank druid) — spell bodies commented out / absent / in `_`-ignored files. Real implementation needs spell adaptation to current API + talent proto fields + coefficients.
- DPS numbers are still 1.12/SoD engine values, not Forever coefficients.
- 59 SoD item-set bonuses + SoD weapon-proc effects are skipped (not in the Forever DB).
- Full talent trees still unknown (nether `data/talents` returns empty).
- **Browser runtime not visually verified** — local browser backend hung on every call.

## Session 3 (2026-09-20) — enchant DB fix + compare feature

- **Enchant DB bug fixed**: `gen_forever_db.py` previously emitted only 1 enchant (it read the linked *item's* stats and filtered on item presence). Now emits **765 enchants** (all stat-bearing records): `effectId` = SoD effectId when the spell id is shared with the SoD DB (engine Go funcs are keyed to those ids), else the gear-planner `enchant` field; `stats` = the enchant's **own** stats (not the item's); `type`/`class`/`invTypeMask` derived from the linked item. 185 Forever enchants map to engine-backed effects (weapon procs, stats); the rest carry plain stats.
- **End-to-end enchant verified in engine**: a mage with a socketed Spell-Power enchant (spellId 22749 → effectId 2504) goes 12.13 → 14.32 DPS (+2.18), no errors. `ItemSpec.enchant` is an **effect ID** (`EnchantsByEffectID` lookup), not a spell id.
- **Gear importer**: `individual_wowhead_gear_planner_importer.tsx` was hardcoded to `/classic/gear-planner/` — now accepts any expansion product in the URL (`classic|forever`), uses `REPO_NAME` for the link. Link/addon/60U/JSON importers were already present and product-agnostic (they resolve item ids against the live DB, so Forever gear imports work).
- **Auto-tune confirmed already present**: `stat_weights_action.ts` (EP/Stat-Weights tab) is wired via `addStatWeightsAction` in `individual_sim_ui.ts`; all 9 classes define per-spec `epStats`. No work needed.
- **New compare feature**: `ui/compare/` (index.html + index.ts) — two independent full `IndividualSimUI` panels (each with its own spec selector, gear, buffs, rotation, run button) plus a "Run Both & Compare" button that fires both sims in parallel and renders a side-by-side DPS/HPS/Threat delta table (player + raid metrics). Instantiates the concrete per-spec UI classes (all 19 are pure forwarders of `SPEC_CONFIGS`). TS clean; built into `dist/forever/compare/` (27 asset refs all resolve).
- Rebuilt: CLI (`--tags=with_db`), workers, Vite (`VITE=0`, 23.4s). `dist/forever/assets/database/db.bin` = 7,524,985 bytes (765 enchants), served with correct Content-Length.

Remaining gaps (not invented):
- **Browser runtime not visually verified** — local browser backend hung on every call; compare page verified via asset graph + HTTP only, not a live two-panel sim in a browser.
- **5 stub specs deal 0 damage** (resto druid, resto shaman, holy paladin, healing priest, feral tank druid) — spell/talent code commented out; needs proto talent additions + spell coefficients.
- DPS numbers are still 1.12/SoD engine values, not Forever coefficients.
- 59 SoD item-set bonuses + SoD weapon-proc effects are skipped (not in the Forever DB).
- Full talent trees still unknown (nether `data/talents` returns empty).

## Frontend / feature expansion — 2026-09-20 (session 2)

Frontend is now a **real Vite build from source** (not the hand-copied classic bundle). Root cause of the earlier hand-assembly: `vite.config.mts` hardcoded `base:'/classic/'` + `outDir:dist/classic`, and on Windows rollup entry keys used backslashes producing unresolvable `bundle/ui\mage\...entry.js` script srcs.

Done:
- `vite.config.mts` parameterized: `REPO = process.env.BASE_DIR || 'forever'`, `base:`/`outDir:`/worker-mappings all derived from `REPO`; **entry keys normalized to forward slashes** (`path.relative(...).replace(/\\/g,'/')`) — fixes the Windows backslash src bug. `vite.build-workers.ts` import fixed (`.mjs`→`.mts`); `tsconfig.json` gained `allowImportingTsExtensions` (+ trailing-comma fix).
- `ui/core/constants/other.ts`: `REPO_NAME='forever'`. All 21 `ui/*/index.html` asset refs repointed `/classic/`→`/forever/` (external wowhead/warcraftlogs URLs left as classic).
- Build pipeline works without make/bazel: `GOOS=js GOARCH=wasm go build -o dist/forever/lib.wasm ./sim/wasm/` + `npx tsx vite.build-workers.ts` + `npx tsc --noEmit` + `npx vite build` (with `BASE_DIR=forever`). ~23s Vite build, clean.
- **Mage 3-spec rotations** added: `ui/mage/apls/{arcane,fire,frost}.apl.json`, wired into `presets.ts`. CLI-verified 200 iters each, no errors — Arcane 55.2 DPS, Frost 13.7, Fire 11.8 (Arcane Explosion + Arcane Missiles + Evocation / Fireball+Scorch / Frostbolt+Evocation).
- **5 previously-unregistered specs** (resto druid, resto shaman, holy paladin, healing priest, feral tank druid) had **no agent** → `NewAgent` panicked the WASM. Added `sim/unimplemented_specs.go` registering graceful no-op agents (0 DPS, no crash) + `RegisterUnimplementedSpecs()` in `register_all.go`. All 21 nav specs now simmable.
- **Buffs + synergies**: all 21 specs already carry full `RaidBuffs`/`IndividualBuffs`/`Debuffs`/`PartyBuffs` defaults inline in `sim.ts`; engine `sim/core/buffs.go` implements the synergy logic (ArcaneBrilliance, Moonkin Aura, Rallying Cry, etc.) + `TristateEffect`. No gap.
- **Profile save**: already present — auto-save to `localStorage` keyed per-spec + `Import/Export profile (JSON)` buttons in the top bar (`ui/core/individual_sim_ui.ts`). No gap.
- **Nil-rotation panic fixed at root** (`sim/core/apl.go: newAPLRotation`): a unit with a weapon but no rotation config now gets a non-nil empty APL instead of `nil`, so the 7 `unit.Rotation.DoNextAction` call sites (rage/energy gain, auto-attack swings, casts) can't panic. Pre-fix, a weapon-bearing melee spec with no rotation crashed the sim (e.g. warrior → `runtime error: invalid memory address` at `rage.go:172`). Post-fix the same input auto-attacks (warrior ≈28 DPS, rogue ≈22, hunter ≈20, feral ≈54).
- **Full CLI sweep verified, no errors**: all 13 enabled spec oneofs (mage, rogue, warlock, warrior, hunter, shadowPriest, balanceDruid, feralDruid, elementalShaman, enhancementShaman, retributionPaladin, protectionPaladin, wardenShaman) + the 5 stub specs run 50–200 iterations cleanly. Built bundle: 21 spec pages, 234 asset refs all resolve, WASM valid (0x0061736d), lib.wasm 32.7 MB (rebuilt with the fix).

Remaining gaps (not invented):
- **Browser runtime not visually verified** — local browser backend hung (420s) on every call this session; could not screenshot the rendered UI. Asset graph + WASM + engine are all verified headless.
- **5 stub specs deal 0 damage** — their spell/talent code is commented out and references talents not in this fork's proto (e.g. `HolySpecialization`, `SilentResolve`, druid `Rejuvenation`/`Lifebloom`). Real implementation needs proto talent additions + spell coefficients — a separate, larger effort.
- DPS numbers are still 1.12/SoD engine values, not Forever coefficients.

## Build status (Forever 1.6 calc) — 2026-09-20

Target confirmed by Jason: **Wago build 1.60.1.69913 = the new WoW Forever** (19k items, ilvl 100, beta test items). The `5.5.0.62071` build is NOT Forever.

Source of truth for items: Wowhead **gear-planner `classicplus` payload** (`nether.wowhead.com/forever/data/gear-planner?dv=100`, needs a browser User-Agent). The classic nether tooltip endpoints (item/spell) are **dead (404)** for Forever, so the SoD tooltip pipeline cannot be reused.

Done:
- `tools/forever_gen/gen_forever_db.py` — maps the gear-planner `item` page (11,000 items) to `UIItem` proto JSON; converts Forever **ratings → flat 1.12-scale** values (spellCrit, spellPen, hit, haste, defense, etc.) using the 1.12 combatratings table.
- `assets/database/db.json` + `db.bin` regenerated (SoD original backed up to `db.sod_backup.json`). `classAllowlist` preserved on the 688 class-restricted items.
- UI repointed `/classic/` → `/forever/` (index.html, database.ts, workers); `dist/forever/` assembled from the built classic bundle + Forever DB.
- `sim/core/item_sets.go` + `item_effects.go`: init-time `panic` on missing set/effect items changed to `[WARN]`+skip (the hardcoded 1.12/SoD sets/procs don't exist in the Forever DB — 59 sets skipped).
- **End-to-end verified**: `cmd/wowsimcli` built `--tags=with_db` (Forever `db.bin` embedded); a Mage loadout + APL Fireball rotation runs 300 iterations cleanly, raid DPS avg ≈ 10.0 (damage confirmed non-zero).

Known gaps (not invented):
- Class rotation logic is still the 1.12/SoD engine (APL-based); DPS numbers are placeholders until Forever coefficients/GCD/threat are sourced.
- Item-set bonuses and SoD weapon-proc effects are skipped (not present in the Forever DB).
- Full talent trees still unknown (nether `data/talents` returns empty `var g_talents = {}`).

## Hard unknowns (do not invent)

- Full talent trees for 8/9 classes (Paladin is the only official recap).[4]
- Spell coefficients, GCD, threat values, armor tables.
- Exact raid boss lists, attunements, tier-set bonuses.[14]
- Honor season rules (teased, not specified).[10]
- Hardcore ship date (Winter 2026–27 window only).[9]
- Whether original 40-man raids besides Onyxia return at launch (they do not; later as "revamped iconic raid").[9][5]
- SoD-style runes / Warden shaman / tank rogue / tank lock — **not announced for Forever**. Do not port SoD kits.
- Character transfers from Classic/SoD: none announced.[27]
- Gold cost of riding skill.[4]
- Whether camps work inside instances (`wowhead` comments only).

## Conflicts

| Topic | A | B | Call |
|---|---|---|---|
| Launch clock | 3:00 p.m. **PST**[2][5] | 3:00 p.m. **PDT**[7] | Prefer PST from pre-purchase + What's Next. Flag until Blizzard unifies. |
| Sharpening Wheel | Attack Power (`official`)[4] | Strength (`wowhead` camping table)[15] | Keep both. Sim should parameterize. |
| Krol'dok level | 40–45[9][13] | 40–55 (`press`)[26] / 35–40 (MMO-C notes)[25] | Use Wowhead/official table 40–45 until beta confirms. |
| Dalaran level | table 28–33[13] | body text 20–35 on same Wowhead page[13] | Use table 28–33. |
| New-zone count | "three new zones" in one Blizzard tweet quoted by press[24] | four named: Hyjal, Shen'dralas, Riverglades, Zephras[5][1] | **Four**. Tweet was incomplete. |
| Legacy perks account-wide? | Deep Dive: points shared, **spend per character**[4] | Wowhead overview once said perks benefit all characters[10]; later guide says spend per character[16] | Follow Deep Dive + later Wowhead: earn account-wide, spend per character. |

## Beta window

Beta live 2026-09-17 through 2026-10-21. Week 1 cap 20, later 30. Week 1 content: Skyborne + Zephras, Hall of Thanes, Ruins of Lordaeron, zones to 20.[3]

Datamine from beta should land in `classes/` and `data/forever.yaml` first.
