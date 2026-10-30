# WoW4_SiMs Daily Driver — Design

**Date:** 2026-10-30 · **Status:** approved by user (brainstorm session) · **Target: ready Fri 2026-11-06**

## Goal

A personal, LAN-only daily driver: brand-themede WoWSims-derived Forever simulation UI plus the offline world map with fresh interactive data, started with one command, kept honest by an automated verify suite.

## Decisions (from user)

| Question | Answer |
|---|---|
| Ready for whom? | Own daily driver — LAN, reliability over polish, no public hosting |
| Sim UI | Reuse stock WoWSims UI; re-skin + brand pass ("make it ours") — brand + theme only, no component surgery |
| Map interactables | Fresh tree-16 rescrape is **required** (places ~894, POIs ~4,469, nodes ~32.9k incl. fish/leather/cloth, + routes/voyages) |
| Name | "WoW4_SiMs · Forever" (default; trivially changeable) |
| Approach | #1: Tree A canonical, rebuild everything downstream |

## Architecture

- **Sim** `:8732` — static server over `.publish/wow4_sims/upstream-classic/dist/forever` (bundle + `lib.wasm` with embedded Forever DB + assets), `application/wasm` MIME, LAN bind.
- **Map** `:8731` — existing `wow-forever/serve_tiles.py` (tiles archive + data files).
- **Launcher** — `launch.sh` at repo root starts both, prints URLs; `verify.sh` runs the full green-check suite. No new frameworks.
- **Canonical repo** = Tree A `.publish/wow4_sims` (GitHub `bottlefedchaney808/wow4_sims`, pushed `ce1364e`). Tree B (`.worktrees/main/upstream-forever`) is read-only reference; bundle banked at `/home/zinko83/sim-backups/upstream-forever-2026-10-30.bundle`. Nothing gets deleted.

## Build pipeline (all from source; dist/ stays gitignored)

`npm ci` → proto codegen → `vite build` bundle → `GOOS=js GOARCH=wasm go build -tags=with_db ./sim/wasm/` → `make copydb`. The makefile already targets `dist/forever` (BASE_DIR=forever). The `tools/forever_gen/*` scripts carry dead `E:\` paths — not used, not fixed (documented as deprecated). The wasm and the db pair must always be built together in one pass (never mix generations).

## Brand + theme pass (merge-friendly only)

- Makefile/spec-page titles: "Classic X Simulator" → "WoW4_SiMs · Forever X"
- `ui/index_template.html` header/brand, homepage card list
- Strip wowsims social/footer links; favicon set
- Dark WoW-Forever palette via `ui/scss/shared/_variables.scss`
- No layout surgery, no component rebuilds → upstream-mergeable

## Map refresh

- New `wow-forever/scrape_worldmap.py` (no scraper exists today): pulls Wowhead Forever `world-map` datasets (config `tree:16`, dv from live config; browser-UA required) → writes `data/places.js|pois.js|nodes.js` in the existing `window.WH_*` formats + new `data/routes.js|voyages.js`.
- UI: fish/leather/cloth join node toggles; routes/voyages as toggleable polylines; index.html counts updated.
- Honesty guards mandatory: `version_manifest.py` dataset_version + footer hash, `audit.py` re-based to new counts, all existing tests stay green. A failed/partial scrape never overwrites a shipped dataset (write-to-temp + validate + swap).

## Error handling

- Scrape: temp-dir capture → validate counts/shape → atomic swap; on any failure keep old data and exit non-zero.
- Sim: dist is rebuilt as one generation (wasm+db+bundle together); verify.sh greps a Forever item name in the shipped wasm to catch vanilla regressions.
- Ports: launcher fails fast if :8731/:8732 busy.

## Verification ("green" = done)

1. `go build --tags=with_db ./cmd/wowsimcli/` clean; fixture run 300 iterations, `error null`, DPS > 0.
2. HTTP: index/spec pages 200; `lib.wasm` 200 with `application/wasm`; `Dreadnaught Breastplate` present in shipped wasm AND dist db.
3. **Browser checklist (first time ever):** all 20 spec pages + raid + detailed_results load; one gear sim completes with results.
4. Map: `pytest tests/` + `node --test tests/questlog_schema.test.js` + `node verify_sha256.js` + `audit.py` all pass against the new datasets.
5. `verify.sh` runs 1–4 end to end.

## Out of scope

Talents (no data source — unchanged), public hosting, custom UI components, Zephras Isle tiles (stretch: time-boxed URL-pinning spike), companion/`Sync-appware-lora` project, parent↔origin/main history reconciliation.

## Stretch (time-boxed, cannot block delivery)

- Zephras Isle tiles from v3 CDN (URL pattern unpinned).
- Talent endpoint research spike (2h).
