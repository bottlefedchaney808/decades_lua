#!/usr/bin/env bash
# Green suite for WoW4_SiMs daily driver. Exit 0 = ship-ready.
set -u
export PATH=/home/zinko83/tools/go/bin:$PATH
ROOT="$(cd "$(dirname "$0")" && pwd)"
SIM="$ROOT/.publish/wow4_sims/upstream-classic"
MAP="$ROOT/wow-forever"
ok=0
chk() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS $name"; else echo "FAIL $name"; ok=1; fi; }
chk "sim:go-build"      bash -c "cd '$SIM' && go build -tags=with_db -o /tmp/wowsimcli ./cmd/wowsimcli/"
chk "sim:wasm-forever"  grep -q "Dreadnaught Breastplate" "$SIM/dist/forever/lib.wasm"
chk "sim:http-index"    curl -sf -o /dev/null "http://127.0.0.1:8732/forever/"
chk "sim:http-wasm"     bash -c "curl -sf -o /dev/null -w '%{content_type}' 'http://127.0.0.1:8732/forever/lib.wasm' | grep -q application/wasm"
chk "sim:cli-smoke"     bash -c "cd '$SIM' && /tmp/wowsimcli sim --infile cmd/wowsimcli/input.json --outfile /tmp/smoke.json && /usr/bin/python3 -c \"import json;r=json.load(open('/tmp/smoke.json'));err=(r.get('error') or {}).get('message') or '';assert not err and r['raidMetrics']['dps']['avg']>0\""
chk "map:pytest"        bash -c "cd '$MAP' && /usr/bin/python3 -m pytest tests/ -q"
chk "map:questlog"      bash -c "cd '$MAP' && node --test tests/questlog_schema.test.js"
chk "map:sha256"        bash -c "cd '$MAP' && node verify_sha256.js"
chk "map:audit"         bash -c "cd '$MAP' && /usr/bin/python3 audit.py"
chk "map:http"          curl -sf -o /dev/null "http://127.0.0.1:8731/index.html"
for spec in balance_druid feral_druid feral_tank_druid restoration_druid \
  elemental_shaman enhancement_shaman restoration_shaman warden_shaman \
  hunter mage rogue holy_paladin protection_paladin retribution_paladin \
  healing_priest shadow_priest warlock warrior tank_warrior raid detailed_results; do
  chk "sim:http-$spec" curl -sf -o /dev/null "http://127.0.0.1:8732/forever/${spec}/index.html"
done
exit "$ok"
