#!/usr/bin/env python3
"""Assemble dist/forever/ from the built classic bundle (Bazel unavailable):
copy bundle -> repoint /classic/ -> /forever/ in text files -> drop SoD db_inputs
-> install Forever db.json + leftover_db.json + db.bin."""
import os, re, shutil, json

ROOT = r"E:\WoW4_SiMs\.worktrees\main\upstream-classic"
SRC = os.path.join(ROOT, "dist", "classic")
DST = os.path.join(ROOT, "dist", "forever")
DBSRC = os.path.join(ROOT, "assets", "database")

# Clean DST (keep lib.wasm that `make wasm` produced)
if os.path.isdir(DST):
    for f in os.listdir(DST):
        p = os.path.join(DST, f)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif f != "lib.wasm":
            os.remove(p)
else:
    os.makedirs(DST)

def is_text(p):
    e = p.lower()
    return e.endswith((".html", ".js", ".css", ".json", ".svg", ".txt", ".webmanifest"))

count = {"repointed": 0, "files": 0}
for root, dirs, files in os.walk(SRC):
    # skip db_inputs (SoD tooltips, 100MB+) and the big wasm (we keep ours)
    relroot = os.path.relpath(root, SRC)
    if relroot.startswith("db_inputs") or "db_inputs" in relroot.split(os.sep):
        continue
    for f in files:
        s = os.path.join(root, f)
        d = os.path.join(DST, os.path.relpath(s, SRC))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if f == "lib.wasm":
            continue  # keep the freshly built dist/forever/lib.wasm
        if is_text(s) and os.path.getsize(s) < 8_000_000:
            data = open(s, encoding="utf-8", errors="surrogatepass").read()
            new = data.replace("/classic/", "/forever/")
            if new != data:
                count["repointed"] += len(re.findall(r"/classic/", data))
            open(d, "w", encoding="utf-8", errors="surrogatepass").write(new)
            count["files"] += 1
        else:
            shutil.copy2(s, d)

print("Copied+repointed:", count)

# Install Forever DB into dist/forever/assets/database/
dbdst = os.path.join(DST, "assets", "database")
os.makedirs(dbdst, exist_ok=True)
shutil.copy2(os.path.join(DBSRC, "db.json"), os.path.join(dbdst, "db.json"))
shutil.copy2(os.path.join(DBSRC, "db.bin"), os.path.join(dbdst, "db.bin"))
# leftover_db.json: SoD leftovers not in Forever (harmless; items absent from equip load it)
if os.path.exists(os.path.join(DBSRC, "leftover_db.json")):
    shutil.copy2(os.path.join(DBSRC, "leftover_db.json"), os.path.join(dbdst, "leftover_db.json"))

# Verify
d = json.load(open(os.path.join(dbdst, "db.json"), encoding="utf-8"))
print("dist/forever db.json: items=%d suffixes=%d" % (len(d["items"]), len(d["randomSuffixes"])))
# sanity: no /classic/ left in key entry files
idx = open(os.path.join(DST, "index.html"), encoding="utf-8", errors="ignore").read()
print("index.html /classic/ remaining:", idx.count("/classic/"), " /forever/ count:", idx.count("/forever/"))
print("dist/forever/lib.wasm size:", os.path.getsize(os.path.join(DST, "lib.wasm")))
