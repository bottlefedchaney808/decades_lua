#!/usr/bin/env python3
"""Repoint local /classic/ asset+sim-link paths -> /forever/ (quote-prefixed only,
so external https://wowhead.com/classic links are untouched), install Forever db.json,
back up the SoD db.json."""
import os, re, shutil, json

ROOT = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic"
UI = os.path.join(ROOT, "ui")
DBDIR = os.path.join(ROOT, "assets", "database")
FOREVER_DB = os.path.join(DBDIR, "forever_draft", "db.json")

files = [
    "index_template.html",
    "index.html",
    "core/proto_utils/database.ts",
    "core/components/gear_picker/utils.ts",
    "core/proto_utils/enchants.ts",
    "core/proto_utils/utils.ts",
]

changed = {}
for rel in files:
    p = os.path.join(UI, rel)
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    s = open(p, encoding="utf-8").read()
    before = s
    # quote-prefixed local paths: "/classic/  and  '/classic/  -> /forever/
    s = s.replace('"/classic/', '"/forever/').replace("'/classic/", "'/forever/")
    # nether tooltip product (leftover items) -> forever
    s = s.replace("nether.wowhead.com/classic/tooltip", "nether.wowhead.com/forever/tooltip")
    if s != before:
        open(p, "w", encoding="utf-8").write(s)
        changed[rel] = len(re.findall(r"/forever/", s)) - len(re.findall(r"/forever/", before))
    ext = re.findall(r"wowhead\.com/classic", s)
    if ext:
        print(f"  NOTE {rel}: {len(ext)} external wowhead.com/classic links preserved")

print("Repointed files:", changed)

cur = os.path.join(DBDIR, "db.json")
if os.path.exists(cur):
    bak = os.path.join(DBDIR, "db.sod_backup.json")
    shutil.copy2(cur, bak)
    print("Backed up SoD db.json ->", bak)
shutil.copy2(FOREVER_DB, cur)
print("Installed Forever db.json ->", cur)
d = json.load(open(cur, encoding="utf-8"))
print("Installed db.json: items=%d suffixes=%d enchants=%d" % (len(d["items"]), len(d["randomSuffixes"]), len(d["enchants"])))
