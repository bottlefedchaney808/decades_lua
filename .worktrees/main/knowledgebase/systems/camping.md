# Camping

Last verified: 2026-09-19 · `official`[4] + `wowhead`[15]

Cooking Fire becomes a **Basic Campfire** / campsite. Social pause: sit, rest, buffs, vendors, repairs, profession benches.

## Rules (`official`)[4]

- Place a campfire → campsite. Sit a few moments to get buffs.
- Up to **3** special crafted objects on a Basic camp (Cook upgrades: 5 then 10).
- Each player contributes **one** object. Objects share a **1-hour cooldown**.
- Every profession has **three** objects at different skill levels. Profession grants its buff/utility regardless of which object is placed.
- First objects at **skill 20** (camping NPCs or trainers). Advanced objects from **Blueprint recipes** on dungeon bosses.
- Camp buffs are **variants of class buffs and do not stack** with the matching class buff.
- Location matters: some terrain is a bad rest.

## Unlock (`wowhead` beta)[15]

Around level 5, quest **The Great Outdoors**: `/sit` at the questgiver campfire → train Cooking → craft Basic Campfire (Simple Wood + Flint and Tinder from cooking trainer). Then a 101 quest per trained profession for the tier-1 object.

## Profession objects

Blizzard examples (`official`)[4]: Blacksmith Sharpening Wheel → **Attack Power**; Tailor Faction Banner → **Spirit**; Herbalist Incense Candle → **Intellect**. Alchemist Alchemy Lab; Leatherworker Tanning Rack; Cook upgraded campfires.

Wowhead beta table (`wowhead`)[15] — **conflict** on Sharpening Wheel (Strength vs Attack Power). Treat as parameterized:

| Profession | T1 | T2 | T3 | Buff family |
|---|---|---|---|---|
| Alchemy | Mana Well (Mp5, excl. BoW) | Fermenter | Alchemy Laboratory | mana regen |
| Blacksmithing | Sharpening Wheel | Anvil | Master Forge | AP or Strength — `conflict` |
| Enchanting | Enchanted Lute | Arcane Salvager | Arcane Forge | armor / stats / resists |
| Engineering | Reagent Bot | Repair Bot | Anarchist's Workbench | vendor / repair / recipes |
| Herbalism | Incense Candle | Greenhouse | Seed Hybridizer | Intellect |
| Leatherworking | Camp Tent (rested XP) | Tanning Rack | Sewing Machine | rest / reagents |
| Mining | Lodestone | Rock Garden | Molten Foundry | melee AP |
| Skinning | Camp Chair (2% crit) | Field Guide | Trapper's Workbench | crit |
| Tailoring | Faction Banner | Spinning Wheel | Loom | Spirit |
| Cooking | Basic Campfire (3 slots) | Journeyman (5) + Cookie's Feast | Expert (10) | camp size / food |
| First Aid | First Aid Kit (Stamina) | Toxin Study TBD | Plague Doctor's Lab TBD | stamina |
| Fishing | Fish Bowl (8% stats, excl. BoK) | Fishing Rack | Fishing Hut | stats / fish |

Crafted camp items: craft yields two; consumed on place; place requires profession skill; **anyone** can receive the buff.[15]

Sim note: camping is a raid-buff / world-buff analog. Model as optional raid-buff profile, exclusive with the matching class aura.
