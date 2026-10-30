# WoW4_SiMs Daily Driver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a LAN daily driver by Fri 2026-11-06: branded WoWSims-derived Forever sim UI (built from the canonical pushed tree) + offline world map with a fresh tree-16 scrape, one command to start, one command to verify.

**Architecture:** Two static LAN services — sim bundle + DB-embedded wasm on `:8732`, existing map server on `:8731` — glued by `launch.sh`/`verify.sh` at the parent repo root. `.publish/wow4_sims/upstream-classic` is the single sim home; `wow-forever/` is the single map home. All artifacts rebuilt from source; the prebuilt Tree B dist is reference-only.

**Tech Stack:** Go 1.23.4 (wasm + CLI), Vite/TypeScript UI, Python 3 stdlib servers + pytest, Leaflet map app, Wowhead `world-map` HTTP endpoints.

## Global Constraints

- Go lives at `/home/zinko83/tools/go/bin/go` — every shell needs `export PATH=/home/zinko83/tools/go/bin:$PATH`. Go version must stay 1.23.4.
- Python for tests is **`/usr/bin/python3`** (`-m pytest`); the default `python3` (3.14.4) has no pytest.
- `node --test` must be passed a **file, not a directory** (installed node v22.22.1; repo `.nvmrc` says 20.11.1, `engines: node>=20` — build on 22, note any deprecation output in the task report).
- Never `git push --force`, never rewrite history, never delete either sim tree. `dist/` and `node_modules/` stay gitignored — nothing built gets committed.
- The shipped `lib.wasm` and `dist/.../database/db.*` are always one generation built together with `-tags=with_db` — never mix builds.
- Scrapes never destructively overwrite shipped data: capture to `scrape/raw/`, generate to temp files, validate, then swap.
- Brand string is exactly **`WoW4_SiMs · Forever`** (replaceable in one variable — see Task 6).
- Repo roots used throughout: `SIM=/home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic`, `MAP=/home/zinko83/WoW4_SiMs/wow-forever`, `ROOT=/home/zinko83/WoW4_SiMs`. All paths in tasks are relative to these unless absolute.
- Commit messages: `feat:`/`fix:`/`chore:`/`data:` prefix, one logical change each.

---

### Task 1: Toolchain gate + npm + proto + UI bundle build

**Files:**
- Modify: (build outputs only) `node_modules/`, `ui/core/proto/*.ts`, `ui/core/index.ts`, `dist/forever/bundle/*`
- Test: shell assertions below (this is a build task; "green" is exact command outputs)

**Interfaces:**
- Produces: `dist/forever/bundle/.dirstamp` (fresh timestamp) consumed by Task 2's serve/verify; known-good `npm run type-check`.

- [ ] **Step 1: Gate the environment**

```bash
export PATH=/home/zinko83/tools/go/bin:$PATH
cd /home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic
go version && node --version && npm --version && git status --porcelain && git log --oneline -1
```
Expected: `go1.23.4`, `v22.x`, npm prints a version, `git status --porcelain` prints **nothing**, HEAD is `ce1364e`. If dirty or different: STOP, report.

- [ ] **Step 2: Install JS deps**

Run: `make node_modules` (runs `npm ci` against `package-lock.json`; expect minutes, ends with populated `node_modules/`).

- [ ] **Step 3: Generate proto TypeScript**

Run: `make ui/core/proto/api.ts`
Expected: completes via `npx protoc` with no errors; `ui/core/proto/api.ts` exists (`ls -la ui/core/proto/api.ts`).

- [ ] **Step 4: Type-check then build the bundle**

Run: `npm run type-check` → expect exit 0 (no output).
Then run: `make dist/forever/bundle/.dirstamp`
Expected: runs `npx tsc --noEmit`, `npx tsx vite.build-workers.ts`, `npx vite build`, ends with `touch` line and `dist/forever/bundle/` containing `index.html`/js chunks. If `tsc` fails: STOP — report first 20 error lines; do not patch types ad hoc.

- [ ] **Step 5: Commit nothing (verify clean)**

Run: `git status --porcelain` → Expected: empty (everything built is gitignored; if not, add the missing path to `.gitignore`, commit `chore: gitignore build artifact <path>`).

### Task 2: Forever wasm + db pair build (one generation)

**Files:**
- Create: `dist/forever/lib.wasm` (built), `dist/forever/assets/database/*` (copied)
- Test: content assertions below

**Interfaces:**
- Consumes: Task 1's fresh `node_modules`/proto.
- Produces: `dist/forever/lib.wasm` with embedded Forever DB (proof: `Dreadnaught Breastplate` string present), `dist/forever/assets/database/db.json` with 11,000 items — consumed by Tasks 3, 4, 6.

- [ ] **Step 1: Rebuild db.bin/db.json from the installed Forever db.json (idempotent)**

```bash
export PATH=/home/zinko83/tools/go/bin:$PATH
cd /home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic
go run ./tools/forever_gen/regen_db.go
```
Expected log lines: `Parsed Forever db: items=11000 suffixes=1738 enchants=765` then `Wrote assets/database/db.bin and assets/database/db.json`. If items != 11000: STOP, report.

- [ ] **Step 2: Build the DB-embedded wasm**

Run: `mkdir -p dist/forever && GOOS=js GOARCH=wasm go build -tags=with_db -o ./dist/forever/lib.wasm ./sim/wasm/`
Expected: exit 0, `lib.wasm` ≥ 20 MB (`ls -la dist/forever/lib.wasm`).

- [ ] **Step 3: Prove the Forever DB is inside**

Run: `grep -ac "Dreadnaught Breastplate" dist/forever/lib.wasm`
Expected: nonzero count (≥1). Reference: Tree B's proven build has 2. Zero means the db tag didn't take — STOP, report.

- [ ] **Step 4: Copy the db pair into dist**

Run: `make copydb` then check:

```bash
/usr/bin/python3 -c "import json;d=json.load(open('dist/forever/assets/database/db.json'));ids=[i['id'] for i in d['items']];print(len(ids), max(ids))"
```
Expected: `11000 286554` (or higher max). 

- [ ] **Step 5: Confirm `git status --porcelain` still empty** (dist + assets/database/db.bin/db.json are tracked? — `db.json`/`db.bin` ARE tracked: if Step 1 changed their bytes, commit `data(db): regen db.bin from committed db.json` and push; if unchanged, clean.)

### Task 3: Serve the sim site + HTTP smoke

**Files:**
- Create: `tools/forever_gen/serve_dist.py` (Linux replacement for the E:\-pathed `serve.py`)
- Modify: `tools/forever_gen/serve.py` and `tools/forever_gen/assemble_dist.py` + `repoint_and_install.py` headers only — prepend a `# DEPRECATED (2026-10-30): Windows-era assembly path; makefile now builds dist/forever directly. See docs/superpowers/specs/2026-10-30-...` comment line

**Interfaces:**
- Consumes: Task 2's `dist/forever`.
- Produces: `serve_dist.py <port>` serving `dist/forever/` with `application/wasm` MIME on `0.0.0.0`; used by Task 11's `launch.sh` as the sim service.

- [ ] **Step 1: Write the server**

```python
#!/usr/bin/env python3
"""Serve dist/forever/ for LAN daily use. Usage: serve_dist.py [port] (default 8732)."""
import http.server, os, sys, socketserver

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8732
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "dist", "forever")

class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".wasm": "application/wasm", ".json": "application/json"}
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.abspath(ROOT), **kw)
    def log_message(self, *a):
        pass

class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with TCPServer(("0.0.0.0", PORT), H) as httpd:
        print(f"serving {os.path.abspath(ROOT)} on 0.0.0.0:{PORT}")
        httpd.serve_forever()
```

- [ ] **Step 2: Run it and smoke HTTP**

```bash
cd /home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic
/usr/bin/python3 tools/forever_gen/serve_dist.py 8732 &
sleep 1
curl -sf -o /dev/null -w "index:%{http_code}\n" http://127.0.0.1:8732/
curl -sf -o /dev/null -w "wasm:%{http_code} %{content_type}\n" http://127.0.0.1:8732/lib.wasm
curl -sf -o /dev/null -w "spec:%{http_code}\n" http://127.0.0.1:8732/feral_druid/index.html
curl -sf -o /dev/null -w "db:%{http_code}\n" http://127.0.0.1:8732/assets/database/db.json
```
Expected: four 200s; `wasm:200 application/wasm`. (If bundle routes differ — check `ls dist/forever/` and adjust the spec-page path in the checklist in Task 5, not the server.)

- [ ] **Step 3: Kill it (`kill %1`), commit**

`git add tools/forever_gen/` → commit `feat(tools): Linux serve_dist.py for dist/forever; deprecate Windows assembly scripts` → push (`git push origin main`).

### Task 4: Headless engine smoke (wowsimcli, 300 iterations)

**Files:** none (verification task)
**Interfaces:** Consumes Task 2's `assets/database/db.bin` (embedded via `-tags=with_db`).

- [ ] **Step 1: Build the CLI**

```bash
export PATH=/home/zinko83/tools/go/bin:$PATH
cd /home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic
go build -tags=with_db -o /tmp/wowsimcli ./cmd/wowsimcli/
```
Expected: exit 0.

- [ ] **Step 2: Run the Forever fixture**

Run: `/tmp/wowsimcli --input cmd/wowsimcli/input.json` (if flag name differs, `--help` and adjust; the known-good invocation from the 2026-10-29 audit used this fixture).
Expected: iterations complete (300/300 or fixture's setting), `"error": null` / `error None` in output, aggregate DPS > 0. Record the DPS line in the task report. `No item with id` = db generation bug → STOP, report.

### Task 5: First-ever browser verification (manual checklist)

**Files:**
- Create: `docs/BROWSER-VERIFY.md` (in SIM repo; the checked checklist, committed)

**Interfaces:** Consumes Task 3's server on `:8732`.

- [ ] **Step 1: Start `serve_dist.py 8732`, open `http://<LAN-IP>:8732/` in a browser. Create `docs/BROWSER-VERIFY.md` with this checklist and check each box as it passes:**

```markdown
# Browser verification (first run: date, by)
- [ ] Homepage loads, cards for all specs listed
- [ ] Each of: balance_druid feral_druid feral_tank_druid restoration_druid elemental_shaman enhancement_shaman restoration_shaman warden_shaman hunter mage rogue holy_paladin protection_paladin retribution_paladin healing_priest shadow_priest warlock warrior tank_warrior raid detailed_results → page loads, wasm boots (no console errors), gear picker populated with items
- [ ] Feral Druid: pick any grey→white item → stats panel updates
- [ ] Feral Druid: click Simulate → results table with DPS > 0, no console errors
- [ ] One heal sim (Restoration Druid): Simulate → HPS > 0
- [ ] db asset loaded from network tab: assets/database/db.json → 200
```

- [ ] **Step 2: Anything failing → file-level report in the doc (page, console error verbatim). A red item is Task 6's entry criteria too — fix before branding.**
- [ ] **Step 3: Commit `docs: first browser verification of dist/forever site` (push).**

### Task 6: Brand + theme pass ("WoW4_SiMs · Forever")

**Files:**
- Modify: `makefile` (2 sed title rules: `Classic $(title) Simulator` / `CLASSIC $(title) Simulator` → `WoW4_SiMs Forever $(title)`)
- Modify: `ui/index_template.html` (page `<title>` template, header brand text)
- Modify: `ui/core/components/social_links.ts` (remove wowsims links), `ui/core/components/sim_header.tsx` / `sim_title_dropdown.tsx` (brand string)
- Modify: `ui/scss/shared/_variables.scss` (palette), `ui/index.ts` (homepage card group headers if they say "Classic")
- Modify: `assets/favicon_io/*` (replace with generated favicon set; generate a simple "W4" PNG via ImageMagick or PIL — include the one-liner used in the commit body)

**Interfaces:**
- Produces: rebuilt `dist/forever` carrying the brand (verified in Step 5). No code interfaces.

- [ ] **Step 1: Brand constants.** `grep -rn "wowsims\|WoWSims\|CLASSIC\|Classic" ui/index_template.html ui/core/components/social_links.ts makefile | head -30` — edit each hit per Files above. Titles become `WoW4_SiMs Forever <Title>`. Keep every internal URL path (`/forever/`, spec dirs) untouched.
- [ ] **Step 2: Theme.** In `ui/scss/shared/_variables.scss` change the `$color-*`/bootstrap overrides to the Forever dark palette: background `#0d0f14`, panel `#161a22`, accent gold `#c8a24b`, secondary teal `#3f8f8a`. Only variable edits, no new selectors. If the palette is bootstrap-var-based (`grep -rn "^\$dark\|data-bs-theme" ui/scss/`), change the mapped values only.
- [ ] **Step 3: Rebuild everything as one generation**

```bash
make dist/forever/bundle/.dirstamp && GOOS=js GOARCH=wasm go build -tags=with_db -o ./dist/forever/lib.wasm ./sim/wasm/ && make copydb
```

- [ ] **Step 4: Re-run Task 5's browser checklist (fresh tab, hard reload) + `grep -c "Dreadnaught" dist/forever/lib.wasm` (nonzero) + `curl -s http://127.0.0.1:8732/ | grep -c WoW4_SiMs` (≥1).**
- [ ] **Step 5: Commit `feat(ui): WoW4_SiMs brand + Forever dark palette (theme pass, upstream-mergeable)` and push.**

### Task 7: Pin the world-map endpoints (map scrape, phase 1)

**Files:**
- Create: `scrape/raw/*.json` captures in MAP; `scrape/ENDPOINTS.md`
- Test: `curl` evidence recorded in ENDPOINTS.md

**Interfaces:**
- Produces: exact URLs + one saved raw JSON sample per dataset (places, pois, nodes, routes, voyages) consumed by Tasks 8–9.

- [ ] **Step 1: Reproduce the 2026-10-29 audit's live probe** (config seen: `tree:16`, `tileVersion:"v3"`). With a browser UA:

```bash
mkdir -p /home/zinko83/WoW4_SiMs/wow-forever/scrape/raw
cd /home/zinko83/WoW4_SiMs/wow-forever/scrape/raw
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
curl -sH "User-Agent: $UA" "https://www.wowhead.com/forever/world-map" -o page.html
grep -o '"staticPath":"[^"]*"\|"tileVersion":"[^"]*"\|tree[":=]*16\|dataVersion[":=]*[0-9]*' page.html | sort -u
```
Then discover the JSON routes the page itself calls (look for `world-map` api paths / `nether` endpoints in `page.html`; candidates to try with UA header, in order, saving each success into `raw/`): the api path grepped from the page; then `?tree=16` config variants. Record **working URLs** in `scrape/ENDPOINTS.md` with response byte counts.
- [ ] **Step 2: Acceptance: for each of places/pois/nodes/routes/voyages a saved raw capture exists whose shape contains counts matching the 2026-10-29 audit (≈894 places, ≈4,469 pois, ≈99 node groups ≈32.9k pts, 160 routes, 14 voyages — ±5%). Some datasets may arrive in one config document — record that instead.**
- [ ] **Step 3: If any dataset 403s to curl: log exact headers tried; try `Referer: https://www.wowhead.com/` + cookie-less retry. Still 403 → STOP task 7+, report (the week's fallback: ship Sept data + partial new datasets that work; note in HANDOFF).**
- [ ] **Step 4: Commit `data(scrape): endpoint captures + ENDPOINTS.md` in MAP.**

### Task 8: Dataset writer core (TDD)

**Files:**
- Create: `scrape/write_datasets.py`, `tests/test_write_datasets.py`
- Modify: `version_manifest.py` (add routes.js/voyages.js entries), `index.html` footer handled in Task 10

**Interfaces:**
- Consumes: none (pure writer; inputs are dicts).
- Produces: `write_places(obj) -> str`, `write_pois(list) -> str`, `write_nodes(dict) -> str`, `write_routes(list) -> str` — emit byte-compatible `window.WH_*` formats; `build_all(captures_dir, out_dir)` returning counts dict `{"places":int,"pois":int,"nodes":int,"routes":int,"voyages":int}`. Task 9 calls these.

- [ ] **Step 1: Write failing tests** — `tests/test_write_datasets.py`:

```python
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scrape"))
import write_datasets as w

def test_write_places_matches_shipped_format(tmp_path):
    obj = {"zones": [{"n": "Durotar", "ll": [0.449758, 0.467089], "mz": 0}]}
    out = w.write_places(obj)
    assert out.startswith("window.WH_PLACES=")
    assert json.loads(out.split("=", 1)[1].strip().rstrip(";")) == obj

def test_write_pois_and_nodes_and_routes(tmp_path):
    assert w.write_pois([{"n": "Inn", "c": "innkeeper", "ll": [0.1, 0.2]}]).startswith("window.WH_POIS=[")
    assert w.write_nodes({"herb-x": {"n": "X", "pts": [[0.1, 0.2]]}}).startswith("window.WH_NODES=")
    assert w.write_routes([]).startswith("window.WH_ROUTES=")

def test_counts_validation(tmp_path):
    try:
        w.build_all(str(tmp_path / "none"), str(tmp_path))
        assert False, "expected SystemExit on missing captures"
    except SystemExit as e:
        assert str(e)  # non-empty failure reason
```

- [ ] **Step 2: Run, confirm red:** `/usr/bin/python3 -m pytest tests/test_write_datasets.py -q` → 4 failures (import error).
- [ ] **Step 3: Implement `scrape/write_datasets.py`** — writer uses `json.dumps(obj, ensure_ascii=False)` + exact `window.WH_*=` prefixes and trailing `;`? **Match shipped files exactly**: first run `tail -c 50 data/places.js; tail -c 50 data/pois.js; tail -c 50 data/nodes.js` and copy their exact terminator into the writers; `build_all` reads the capture filenames pinned in Task 7's ENDPOINTS.md, calls the four writers, asserts each capture's counts ≥ 90% of the 2026-09-20 baseline counts (hard-coded dict in the module), writes only to a temp dir and returns counts; on any shortfall it raises `SystemExit` before writing (test 3's path when dir empty).
- [ ] **Step 4: Green:** `/usr/bin/python3 -m pytest tests/test_write_datasets.py -q` → 4 passed. Also run the full map suite to be safe: `/usr/bin/python3 -m pytest tests/ -q` (was 42 passed, now 46).
- [ ] **Step 5: Commit `feat(scrape): dataset writers with baseline-count guard (TDD)`.**

### Task 9: Endpoint adapter → regenerate shipped datasets + guards

**Files:**
- Create: `scrape/adapt_captures.py` (maps Task 7 raw JSON → writer inputs)
- Modify: `data/places.js`, `data/pois.js`, `data/nodes.js`; create `data/routes.js`, `data/voyages.js`
- Modify: `version_manifest.py` + regenerate manifest/`dataset_version` + `index.html` footer hash (guard test enforces match); `audit.py` baseline counts

**Interfaces:**
- Consumes: `write_datasets.build_all` + capture files (Tasks 7–8).
- Produces: shipped `data/*.js` new generation; `audit.py` PASS with new counts.

- [ ] **Step 1: Write `scrape/adapt_captures.py`**: load each saved raw capture (shape per ENDPOINTS.md), map each field to the writer input keys — mapping table goes in the module docstring as `endpoint_key → WH key` rows (derive by `jq keys`/python inspection of the captures; e.g. zones list → `{"n","ll","mz"}`; pois → `{"n","c","ll","npc","side"}`; nodes grouped by category into `"herb-<slug>"`/`"ore-<slug>"`/`"fish-<slug>"`/`"leather-<slug>"`/`"cloth-<slug>"` keys, preserving existing slug style from `data/nodes.js`). Coordinates: keep the endpoint's 0–1 normalized lat/lng like shipped files; if the endpoint serves pixel coords, convert with canvas constants in `audit.py` (document formulas in docstring).
- [ ] **Step 2: Generate to temp, validate, swap:**

```bash
cd /home/zinko83/WoW4_SiMs/wow-forever
/usr/bin/python3 scrape/adapt_captures.py --dry-run   # prints counts dict only
/usr/bin/python3 scrape/adapt_captures.py --write     # temp files -> validate -> mv into data/
```
Expected counts ≈ Task 7 Step 2 numbers. 
- [ ] **Step 3: Update guards and pass the suite:** bump `audit.py` expected-count floors to the new numbers (keep its spot-checks working: landmark names may change IDs — re-pick 20 spot-check landmarks that exist in the new data, same as before); rerun:
`/usr/bin/python3 audit.py && /usr/bin/python3 -m pytest tests/ -q && node --test tests/questlog_schema.test.js && node verify_sha256.js`
Expected: all pass; manifest/footer-hash test forces updating the `dataset_version` + `index.html` footer in the same commit — do it with the same command the guard documents (`version_manifest.py` regenerating).
- [ ] **Step 4: Commit `data(map): tree-16 refresh — places/pois/nodes + routes/voyages datasets` + push if MAP has a remote (`git remote -v`; if no remote, note in HANDOFF).**

### Task 10: Map UI — new node categories + routes/voyages layers + counts

**Files:**
- Modify: `index.html` (node toggle groups from data prefixes; new layers for WH_ROUTES/WH_VOYAGES; overlay counts in footer/labels)

**Interfaces:** Consumes `window.WH_ROUTES/WH_VOYAGES` + new-prefixed `WH_NODES` keys (Task 9).

- [ ] **Step 1: Locate the toggle builder:** `grep -n "WH_NODES\|herb-\|ore-" index.html | head` — the existing per-category toggle loop groups node keys by prefix. Confirm it auto-includes new `fish-/leather-/cloth-` prefixes once present (label from the dataset's `n` field). If labels are hardcoded, add the three.
- [ ] **Step 2: Routes/voyages polylines:** mirror the existing polylines/patterns block in `index.html` (grep `L.polyline`): draw each route as `L.polyline(latlngs, {color, weight: 2, opacity: .6})` in two new LayerGroups toggled from the layers control; voyages dashed (`dashArray: "6 6"`).
- [ ] **Step 3: Update hardcoded counts** (`grep -n "1,285\|17,637\|305\|256" index.html` and README) to new totals from Task 9 output.
- [ ] **Step 4: Manual verify:** `/usr/bin/python3 serve_tiles.py` → browser → toggles show fish/leather/cloth points; routes render as polylines; questlog + search still work. Re-run Step 3.3 suite from Task 9 (footer hash must stay green).
- [ ] **Step 5: Commit `feat(map): fish/leather/cloth toggles + routes/voyages layers + fresh counts`.**

### Task 11: `launch.sh` + `verify.sh` at ROOT

**Files:**
- Create: `launch.sh`, `verify.sh`, `README.md` (ROOT — currently none), modify nothing

**Interfaces:**
- Consumes: `.publish/wow4_sims/upstream-classic/tools/forever_gen/serve_dist.py` (Task 3), `wow-forever/serve_tiles.py`.
- Produces: `launch.sh` → sim :8732 + map :8731 (background, pids in `.run/`, logs in `.run/*.log`); `verify.sh` → exits 0 only when every check passes, prints `PASS/FAIL <name>` lines.

- [ ] **Step 1: Write `verify.sh`:**

```bash
#!/usr/bin/env bash
# Green suite for WoW4_SiMs daily driver. Exit 0 = ship-ready.
set -u
export PATH=/home/zinko83/tools/go/bin:$PATH
ROOT="$(cd "$(dirname "$0")" && pwd)"
SIM="$ROOT/.publish/wow4_sims/upstream-classic"
MAP="$ROOT/wow-forever"
ok=1
chk() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS $name"; else echo "FAIL $name"; ok=0; fi; }
chk "sim:go-build"      bash -c "cd '$SIM' && go build -tags=with_db -o /tmp/wowsimcli ./cmd/wowsimcli/"
chk "sim:wasm-forever"  grep -q "Dreadnaught Breastplate" "$SIM/dist/forever/lib.wasm"
chk "sim:http-index"    curl -sf -o /dev/null "http://127.0.0.1:8732/"
chk "sim:http-wasm"     bash -c "curl -sf -o /dev/null -w '%{content_type}' 'http://127.0.0.1:8732/lib.wasm' | grep -q application/wasm"
chk "sim:cli-smoke"     bash -c "cd '$SIM' && /tmp/wowsimcli --input cmd/wowsimcli/input.json"
chk "map:pytest"        bash -c "cd '$MAP' && /usr/bin/python3 -m pytest tests/ -q"
chk "map:questlog"      bash -c "cd '$MAP' && node --test tests/questlog_schema.test.js"
chk "map:sha256"        bash -c "cd '$MAP' && node verify_sha256.js"
chk "map:audit"         bash -c "cd '$MAP' && /usr/bin/python3 audit.py"
chk "map:http"          curl -sf -o /dev/null "http://127.0.0.1:8731/index.html"
exit $ok
```
(The exact wasm MIME assertion and wowsimcli flag were established in Tasks 2–4; if Task 4 changed the flag, mirror the change here in this file's first edit, not silently.)

- [ ] **Step 2: Write `launch.sh`:**

```bash
#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"; mkdir -p "$ROOT/.run"
for p in 8732 8731; do
  if ss -ltn "sport = :$p" | grep -q LISTEN; then echo "port $p already busy — not stealing it"; exit 1; fi
done
/usr/bin/python3 "$ROOT/.publish/wow4_sims/upstream-classic/tools/forever_gen/serve_dist.py" 8732 >"$ROOT/.run/sim.log" 2>&1 &
echo $! > "$ROOT/.run/sim.pid"
/usr/bin/python3 "$ROOT/wow-forever/serve_tiles.py" >"$ROOT/.run/map.log" 2>&1 &
echo $! > "$ROOT/.run/map.pid"
echo "sim: http://$(hostname -I | awk '{print $1}'):8732/   map: http://$(hostname -I | awk '{print $1}'):8731/"
```
(If `serve_tiles.py` hardcodes 8731, keep it; otherwise pass the port. Check its `--help`/argv in Step 3.)

- [ ] **Step 3: `chmod +x launch.sh verify.sh`; ROOT `.gitignore` gets `.run/`; run `./launch.sh`, `./verify.sh` → 11 PASS lines; kill pids; commit `feat(root): launch.sh + verify.sh daily-driver harness`; commit README (map+sim ports, verify usage) `docs(root): README`.**

### Task 12: Handoff, push, done-criteria audit

**Files:** Create `HANDOFF-2026-11-06.md` (ROOT); update `.publish/wow4_sims` gitlink if it moved.

- [ ] **Step 1: Run `./verify.sh` with both services up → 11 PASS. Re-run Task 5 browser checklist end to end on the final build; paste results into the handoff.**
- [ ] **Step 2: Push everything: SIM repo (`git push`), MAP repo (push if remote exists), ROOT master (local only — origin/main belongs to the companion project; do NOT push master; note it in the handoff).**
- [ ] **Step 3: `HANDOFF-2026-11-06.md`: what shipped, verify.sh output, browser checklist, known gaps (1.12-scale values, no talents, Zephras stretch status, no-map-remote note), how to relaunch.** Commit `docs: daily-driver handoff 2026-11-06`.

## Stretch tasks (time-boxed — never block Tasks 1–12)

- **S1 (2h cap): Zephras Isle v3 tiles.** Pin the tile URL pattern from the world-map page/CDN config captured in Task 7 (`staticPath /images/wow/classicplus/world-map/v3`); download z2–z7 (~159 tiles); extend `convert_tiles.py`; add `zephras` pack to `version_manifest.py`. If URL not pinned in 2h: stop, document findings in HANDOFF.
- **S2 (2h cap): talents endpoint hunt** — revisit `data/talents`, talent-calc JSON, and any in-page talent payloads found in `page.html` (Task 7). Findings only; implementation is next week.
