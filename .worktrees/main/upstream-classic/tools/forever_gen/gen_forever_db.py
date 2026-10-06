#!/usr/bin/env python3
"""
Forever db.json generator.

Source: Wowhead gear-planner payload for product `forever` (classicplus),
captured at $TEMP/forever_pages/*.json from
  https://nether.wowhead.com/forever/data/gear-planner?dv=100
Wago build 1.60.1.69913 (ItemSparse etc.) for cross-checks.

Output: assets/database/db.json (UIItem/UIEnchant/... proto JSON, camelCase)
Matching the classic 1.12 sim: ratings converted to flat %/points using the
1.12 combatratings table (assets/db_inputs/basestats/combatratings.txt, lvl 60).
"""
import json, os, re, csv, sys
from collections import Counter

PAGES = r"C:\Users\bottl\AppData\Local\Temp\forever_pages"
OUT = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic\assets\database\forever_draft"
os.makedirs(OUT, exist_ok=True)

# ---------- proto enum maps ----------
STAT = {  # gearplanner key -> proto Stat index
    "str": 0, "agi": 1, "sta": 2, "int": 3, "spi": 4,
    "splpwr": 5,
    "firsplpwr": 7, "frosplpwr": 8, "shasplpwr": 11,
    "mp5": 12, "manargn": 12,
    "hitrtng": 13,          # spell hit rating -> converted
    "critstrkrtng": 14,     # spell crit rating -> converted
    "hastertng": 15,        # haste rating -> converted
    "splhastepct": 15,
    "splpen": 16,
    "atkpwr": 17, "feratkpwr": 43, "mleatkpwr": 17,
    "hitrtng_melee": 18,
    "mlehitpct": 18, "rgdhitpct": 18,   # ranged hit uses melee hit path in 1.12
    "critstrkrtng_melee": 19,
    "mlecritstrkpct": 19, "rgdcritstrkpct": 19,
    "rgdhastepct": 20,
    "armorpenrtng": 21, "exprtng": 22,
    "mana": 23,
    "armor": 26, "armorbonus": 40,
    "rgdatkpwr": 27,
    "defrtng": 28,          # defense rating -> converted (defense skill)
    "def": 28,
    "blockrtng": 29,
    "blockpct": 29,
    "dodgepct": 31,         # converted
    "parryrtng": 32,        # converted
    "arcres": 35, "firres": 36, "frores": 37, "natres": 38, "holres": 39,
    "health": 34,
    "splheal": 41,
    "spldmg": 42,
}
# keys that are NOT item stats (metadata/pricing/etc.)
NONSTAT = {"itemset","itemSquishEraId","displayid","classes","races","appearances",
           "reqlevel","reqfaction","reqrep","reqskill","reqskillrank","reqspell",
           "buyprice","sellprice","avgbuyout","maxcount","dura","shares","cooldown",
           "slotbak","dmgtype1","sourcemore","dmgrange","dps","mledps","rgddps",
           "classes","resipct","skillBuff","rage"}

INVTYPE_TO_ITEMTYPE = {
    1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:11,12:12,
    13:13,14:14,15:14,16:14,17:13,18:14,19:14,20:14,21:13,22:13,23:14,
    25:14,26:14,28:12,
}
WEAPON_SUBCLASS = {0:1,1:1,4:4,5:4,6:6,7:9,8:9,10:8,13:3,15:2,16:0,20:0}
RANGED_SUBCLASS = {2:1,3:3,16:6,18:2,19:8}
# class 4 (armor): subclass -> armorType (empirical from classic db)
ARMOR_SUBCLASS = {1:1,2:2,3:3,4:4}
# sheathtype -> HandType (empirical; 1=twohand for 2H weapons, 3=onehand)
SHEATH = {1:4, 2:4, 3:2, 7:2, 8:1}
CLASSMASK_BITS = {1:9,2:4,4:2,8:6,16:5,64:7,128:3,256:8,1024:1}  # bit -> proto Class

# ---------- 1.12 combat ratings (lvl 60) for rating->flat conversion ----------
# columns: weapon skill, defense skill, dodge, parry, block, hit melee, hit ranged,
#  hit spell, crit melee, crit ranged, crit spell, hit taken melee/ranged/spell,
#  crit taken..., haste melee, haste ranged, haste spell
def load_ratings():
    p = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic\assets\db_inputs\basestats\combatratings.txt"
    rows = {}
    with open(p, encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t")
        hdr = next(r)
        for row in r:
            if row[0] == "60":
                vals = [float(x) for x in row[1:]]
                rows = dict(zip(hdr[1:], vals))
    return rows
R = load_ratings()

def rating_to_flat(kind, rating):
    """Convert a 1.12-style rating to flat value. kind in hit_spell/crit_spell/haste/def/dodge/parry/block/hit_melee/crit_melee"""
    m = {
        "hit_spell": (R["hit spell"], "%"),
        "crit_spell": (R["crit spell"], "%"),
        "haste": (R["haste spell"], "%"),
        "hit_melee": (R["hit melee"], "%"),
        "crit_melee": (R["crit melee"], "%"),
        "def": (R["defense skill"], "pt"),
        "dodge": (R["dodge"], "%"),
        "parry": (R["parry"], "%"),
        "block": (R["block"], "%"),
    }
    per, unit = m[kind]
    v = rating / per
    return round(v, 4) if unit == "%" else round(v, 4)

def build_stats(sd):
    arr = [0.0]*44
    n = 0
    for k, v in sd.items():
        if k in NONSTAT or not v:
            continue
        if k in ("dmgmin1","dmgmax1","dmgmax1","mlespeed","rgddmgmin","rgddmgmax","rgdspeed","sheathtype","armorbonus"):
            continue
        if k == "armor":
            arr[26] = float(v); n += 1; continue
        if k == "armorbonus":
            arr[40] = float(v); n += 1; continue
        if k in STAT:
            idx = STAT[k]
            if k in ("hitrtng","critstrkrtng","hastertng","defrtng","dodgertng","parryrtng","blockrtng","armorpenrtng","exprtng"):
                # ratings: convert to flat using 1.12 tables
                kindmap = {"hitrtng":"hit_spell","critstrkrtng":"crit_spell","hastertng":"haste","defrtng":"def","dodgertng":"dodge","parryrtng":"parry","blockrtng":"block"}
                if k in kindmap:
                    arr[idx] = rating_to_flat(kindmap[k], float(v)); n += 1
                else:
                    arr[idx] = float(v); n += 1  # armorpen/expr are flat in 1.12
            else:
                arr[idx] = float(v); n += 1
    return arr, n

# ---------- load pages ----------
item = json.load(open(f"{PAGES}/item.json", encoding="utf-8"))
renchant = json.load(open(f"{PAGES}/randomEnchant.json", encoding="utf-8"))
enchant = json.load(open(f"{PAGES}/enchant.json", encoding="utf-8"))
isets = json.load(open(f"{PAGES}/itemSet.json", encoding="utf-8"))
base = json.load(open(f"{PAGES}/baseStats.json", encoding="utf-8"))

# effect ids the sim engine actually implements (Go), so we keep no-stat enchants
# that still fire an engine effect func (scopes, striking, oils, ...)
GO_EFFECTS = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic\sim\common\enchant_effects.go"
with open(GO_EFFECTS, encoding="utf-8") as f:
    go_src = f.read()
go_enchant_effects = set(int(x) for x in re.findall(r"NewEnchantEffect\((\d+)", go_src))
go_weapon_effects = set(int(x) for x in re.findall(r"AddWeaponEffect\((\d+)", go_src))

items_out = []
icons = {}
suffixes = {}
stats_used = Counter()
dropped = Counter()
nstats = 0

for gid, g in item.items():
    iid = g["id"]
    inv = g.get("inventoryType")
    if inv is None or inv not in INVTYPE_TO_ITEMTYPE:
        dropped[f"inv{inv}"] += 1
        continue
    itype = INVTYPE_TO_ITEMTYPE[inv]
    sd = g.get("stats") or {}
    cls = g.get("class")
    sub = g.get("subclass")

    arr, cnt = build_stats(sd)
    for i,v in enumerate(arr):
        if v: stats_used[i] += 1
    nstats += cnt

    rec = {
        "id": iid,
        "name": g.get("name") or f"item {iid}",
        "icon": g.get("icon") or "",
        "type": itype,
        "stats": arr,
        "ilvl": int(g.get("itemLevel") or 1),
        "phase": 1,
        "quality": int(g.get("quality") or 0),
        "weaponSkills": [0.0]*16,
    }
    if g.get("icon"): icons[iid] = {"id": iid, "name": rec["name"], "icon": g["icon"]}

    # class allowlist
    cm = g.get("classMask")
    if cm:
        allow = sorted(CLASSMASK_BITS[b] for b in CLASSMASK_BITS if cm & (1<<b))
        if allow and allow != [9]:  # 9? no: 1535=all classes -> skip
            if cm != 1535:
                rec["classAllowlist"] = allow

    # weapon / ranged
    if cls == 2:
        if sub in RANGED_SUBCLASS:
            rec["rangedWeaponType"] = RANGED_SUBCLASS[sub]
            rec["weaponDamageMin"] = float(sd.get("rgddmgmin") or 0)
            rec["weaponDamageMax"] = float(sd.get("rgddmgmax") or 0)
            rec["weaponSpeed"] = float(sd.get("rgdspeed") or 0)
        elif sub in WEAPON_SUBCLASS:
            rec["weaponType"] = WEAPON_SUBCLASS[sub]
            sheath = sd.get("sheathtype")
            rec["handType"] = SHEATH.get(sheath, 2)
            rec["weaponDamageMin"] = float(sd.get("dmgmin1") or 0)
            rec["weaponDamageMax"] = float(sd.get("dmgmax1") or 0)
            rec["weaponSpeed"] = float(sd.get("mlespeed") or 0)
    elif cls == 4:
        if sub in ARMOR_SUBCLASS:
            rec["armorType"] = ARMOR_SUBCLASS[sub]
        elif sub == 6:  # shield
            rec["type"] = 13
            rec["weaponType"] = 7
            rec["handType"] = 3
            rec["armorType"] = 1
    elif cls == 11:  # quiver/ammo -> trinket-ish container
        rec["type"] = 12

    # set
    setid = sd.get("itemset")
    if setid:
        rec["setId"] = int(setid)
        sname = isets.get(str(setid))
        if sname:
            rec["setName"] = sname.get("name") or ""

    items_out.append(rec)

# random suffixes
for sid, s in renchant.items():
    arr, _ = build_stats(s.get("stats") or {})
    if any(arr):
        suffixes[s["id"]] = {"id": s["id"], "name": s.get("name") or "", "stats": arr}

# ---------- enchants ----------
# Strategy:
#  1. Enchants whose spell id also exists in the SoD/1.12 DB are MIRRORED from
#     the SoD record (its effectId is the SoD-era id the engine Go funcs are
#     registered against; its stats array follows the SoD convention of
#     leaving engine-handled effects empty). 185/821 match by spell or name.
#  2. The rest are emitted from the gear-planner record itself: effectId from
#     the `enchant` field, stats from the record's own stats.
sod_db = json.load(open(r"E:\WoW4_SiMs\.worktrees\main\upstream-classic\assets\database\db.sod_backup.json"))
sod_by_spell = {e["spellId"]: e for e in sod_db["enchants"] if e.get("spellId")}
sod_by_name = {e["name"]: e for e in sod_db["enchants"]}

ench_out = []
seen_eff = set()
for eid, e in enchant.items():
    spell = e.get("spell") or 0
    effid = e.get("enchant") or 0
    if not effid and not spell:
        continue
    sod = sod_by_spell.get(spell) or sod_by_name.get(e.get("name") or "")
    if sod:
        rec = {
            "effectId": sod["effectId"],
            "spellId": int(spell) if spell else sod.get("spellId", 0),
            "name": e.get("name") or sod.get("name") or "",
            "icon": e.get("icon") or sod.get("icon") or "",
            "type": sod.get("type", 0),
            "stats": list(sod.get("stats") or [0.0]*44),
            "quality": int(e.get("quality") or 0),
        }
        if sod.get("extra_types"): rec["extraTypes"] = sod["extra_types"]
        if sod.get("enchantType") is not None: rec["enchantType"] = sod["enchantType"]
    else:
        arr, _ = build_stats(e.get("stats") or {})
        iid = e.get("item")
        it = item.get(str(iid))
        itype = INVTYPE_TO_ITEMTYPE.get(it.get("inventoryType"), 0) if it else 0
        name = e.get("name") or ""
        etype = 0
        if "Kit" in name: etype = 3
        elif "Shield" in name: etype = 2
        elif "2H" in name: etype = 1
        rec = {
            "effectId": int(effid),
            "spellId": int(spell) if spell else int(effid),
            "name": name,
            "icon": e.get("icon") or "",
            "type": itype,
            "stats": arr,
            "quality": int(e.get("quality") or 0),
        }
        if etype: rec["enchantType"] = etype
    if rec["effectId"] in seen_eff:
        continue  # keep first record per effect id (UI map is effectId-keyed)
    seen_eff.add(rec["effectId"])
    ench_out.append(rec)

db = {
    "items": items_out,
    "randomSuffixes": list(suffixes.values()),
    "enchants": ench_out,
    "zones": [],
    "npcs": [],
    "factions": [],
    "itemIcons": list(icons.values()),
    "spellIcons": [],
    "encounters": [],
}
outp = f"{OUT}/db.json"
with open(outp, "w", encoding="utf-8") as f:
    json.dump(db, f)

print(f"items: {len(items_out)}  suffixes: {len(suffixes)}  enchants: {len(ench_out)}")
print(f"dropped: {dict(dropped)}")
print(f"stat index usage: { {i: stats_used[i] for i in sorted(stats_used) } }")
print(f"total stat entries: {nstats}")
print(f"written: {outp}")
