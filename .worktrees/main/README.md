# WoW4_SiMs — Forever

Full WoWSims stack (Classic engine), rebranded for **World of Warcraft: Forever**.

## Run

Sim is served from `upstream-classic/dist`:

http://127.0.0.1:8080/classic/

Same grid as [wowsims.com/classic](https://www.wowsims.com/classic/) / [SoD](https://www.wowsims.com/sod/): every spec page, raid sim, gear/talents/APL, WASM combat core.

Combat math is still **1.12 Classic** until we regenerate `assets/database` from Forever Wago `1.60.1.69913` + Wowhead forever tooltips. See [`knowledgebase/wowsims/mining.md`](knowledgebase/wowsims/mining.md).

## Layout

- `upstream-classic/` — WoWSims engine (Go WASM + Vite UI)
- `knowledgebase/` — sourced Forever facts, Mage FFB vs SoD, class gaps
