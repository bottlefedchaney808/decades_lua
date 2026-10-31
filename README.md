# WoW4_SiMs · Forever — LAN daily driver

Two services on this machine, no hosting, no cloud:

| Service | Port | What it is |
|---|---|---|
| Sim site | **8732** | `/forever/` — WoWSims classic engine (Tree A: `.publish/wow4_sims/upstream-classic`) with the Forever 11k-item DB embedded in `lib.wasm` |
| World map | **8731** | `wow-forever/` tile server + world-map UI (places, POIs, gathering nodes, quest log) |

## Launch

```bash
./launch.sh
```

Starts both services in the background (pids + logs under `.run/`), waits until both ports listen, and prints the LAN URLs. It refuses to steal a busy port — kill the old pids in `.run/*.pid` first.

## Verify (green suite)

```bash
./verify.sh
```

Runs every gate and prints `PASS/FAIL <name>` lines; **exit 0 = ship-ready**. Covers: sim go-build, wasm contains the Forever DB (`Dreadnaught Breastplate`), HTTP 200 on the index + all 21 spec pages + wasm MIME check, headless CLI sim smoke (300 iterations, `error.message` empty, DPS > 0), and the map suite (pytest, questlog schema, sha256 manifest, audit, tile HTTP).

## Layout

- `.publish/wow4_sims/upstream-classic/` — the sim repo (Tree A, canonical). Served by `tools/forever_gen/serve_dist.py`.
- `wow-forever/` — the map repo. Served by `serve_tiles.py --host 0.0.0.0`.
- `docs/superpowers/plans/` — the implementation plan; `docs/superpowers/carl/` — the adversarial-review ledger.
- `HANDOFF-*.md`, `AUDIT-*.md` — handoff notes and the map data audit.

## Notes

- Root is served at `dist/` (vite base `/forever/`); `/` redirects to `/forever/`.
- The map UI reads `window.WH_ROUTES` / `WH_VOYAGES` only when those data files are present — with the September datasets it boots unchanged.
- ROOT git history is local-only (origin belongs to the companion project); the sim and map repos push to their own remotes.
