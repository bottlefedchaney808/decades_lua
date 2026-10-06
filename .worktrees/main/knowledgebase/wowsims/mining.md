# How Wowhead / WoWSims mine Forever data

Last verified: 2026-09-19

Do **not** scrape HTML. Use the same two public feeds WoWSims already wired in `upstream-classic/tools/database`.

## Feeds

| Source | URL | What |
|---|---|---|
| Wago DB2 CSV | `https://wago.tools/db2/ItemSparse/csv?build=1.60.1.69913` | Forever client items (Classic Beta product `wow_classic_beta`, patch **1.60.1**) |
| Wago builds API | `https://wago.tools/api/builds` | Pick latest `wow_classic_beta` version starting `1.60.` |
| Wowhead gear planner | `https://nether.wowhead.com/forever/data/gear-planner?dv=100` | Item/spell dump Wowhead uses |
| Wowhead item tooltip | `https://nether.wowhead.com/forever/tooltip/item/{id}?lvl=60` | JSON tooltip |
| Wowhead spell tooltip | `https://nether.wowhead.com/forever/tooltip/spell/{id}` | JSON tooltip |

Wago table list: `https://wago.tools/db2` with build `1.60.1.69913`. Spell tables to pull next: `SpellName`, `SpellEffect`, `SpellMisc`, `SpellLevels`.

## In-repo ingest

```
cd upstream-classic
go run tools/database/gen_db/*.go -outDir=./assets -gen=wago-db2-items
go run tools/database/gen_db/*.go -outDir=./assets -gen=wowhead-gearplannerdb
go run tools/database/gen_db/*.go -outDir=./assets -gen=wowhead-spells -minId=1 -maxId=1400000
go run tools/database/gen_db/*.go -outDir=./assets -gen=db
```

URLs in `gen_db/main.go` and `wowhead_tooltips.go` already point at **forever** + build **1.60.1.69913**.

Blizzard obfuscates **loot item stats** until an item is looted in beta. Spells, set bonuses, and DB2 tables are still public. Filter leftover SoD `Engrave *` rows.

## Client flavor

Forever beta = Battle.net Game Version **World of Warcraft: Forever Beta** = Wago `wow_classic_beta` 1.60.1.x
