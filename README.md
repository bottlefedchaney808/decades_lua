# Decades Sync

The Decades guild's in-game data link for **WoW Forever**: a small addon that
collects guild data while you play, and a desktop companion that turns it into
snapshots and pushes roster data back into the game. Built as part of the
[Decades Guild Hub](docs/specs/2026-09-28-guild-sync-design.md) — signups,
loot ledger, parses, the sim link and the map all ride on this pipe.

**Status: v0.1.0 — the offline loop works end-to-end.** Everything stays on your
PC until the Firebase backend lands (Plan B). No accounts, no upload, nothing
leaves your machine in this version.

---

## Setup walkthrough (about 5 minutes)

You do three things: put the addon in the game, install Python, run the
companion. Steps 1–2 are one-time.

### 1. Install the addon

1. Find your WoW Forever install folder (the one with `_classic_era_` or
   `WoW.exe` in it). If you're not sure, in the Battle.net app:
   **game icon → Settings (gear) → Show in Explorer**.
2. In this repo, open the `addon` folder. Copy the **`DecadesSync`** folder
   into `<WoW install>\Interface\AddOns\`.
   - If `Interface\AddOns` doesn't exist, create both folders.
   - End state: `<WoW install>\Interface\AddOns\DecadesSync\DecadesSync.toc`
     plus the `.lua` files and a `Data` folder.
3. Start the game. On the character screen, bottom-left **AddOns**: make sure
   **Decades Sync** is ticked, and tick **Load out of date AddOns** too, until
   we pin the Forever interface number.
4. Log in on your raid character and type:
   - `/chatlog` — turns on chat logging; the position module writes its lines
     to `Logs\WoWChatLog.txt` (this is how live position leaves the game).
   - `/dec` — prints your character, addon version, and the timestamp of the
     last data the companion pushed (`never` until you finish setup).

That's the game side done. The addon quietly records into its SavedVariables
file whenever you log out or `/reload`.

### 2. Install Python (one time)

The companion needs **Python 3.11 or newer**, no other dependencies.

- Easiest: open a terminal (`Win` key, type `powershell`, Enter) and run:
  `winget install Python.Python.3.14`
- Or download from [python.org](https://www.python.org/downloads/) — on the
  first installer screen, **tick "Add python.exe to PATH"** before Install.

Check it worked — new terminal, run `python --version`. It should print
`Python 3.14.x` (or higher).

### 3. Run the companion

1. Get this repo onto your PC (Clone/Download ZIP, or `git clone`) and open a
   terminal in it.
2. First, try auto-discovery — it scans common install locations for a
   `WTF/Account/*/SavedVariables/DecadesSync.lua`:

   ```bash
   python -m companion.main
   ```

3. **If it says it can't find your WoW folder**, open
   `companion/companion.toml` in Notepad and put your install path between the
   quotes:

   ```toml
   wow_root = "E:/Games/WoW Forever"
   ```

   (Forward slashes are fine. This is the folder containing `WTF` and
   `Interface`.)
4. Run it again. Expected first-run output:

   ```
   synced grukk-<yourrealm> -> ...\Interface\AddOns\DecadesSync\Data\DecadesData.lua
   upload skipped (offline stub): grukk-<yourrealm>
   ```

   "upload skipped" is correct — nothing leaves your PC until Plan B.
5. To leave it running while you play (it syncs every time you log out or
   `/reload`):

   ```bash
   python -m companion.main --loop
   ```

   Or make a `sync.bat` next to the repo with that one line and double-click it.

### Verify the whole loop

1. In game, type `/reload` (this makes the game write the SavedVariables file).
2. The companion window (if `--loop`) should print `synced <name>-<realm> ...`.
3. In game, type `/dec` — it should now show `data: <today's date>` instead of
   `never`.

If all three happened, the pipe works: game → companion → back into the game.

---

## What it collects today

| Module | Data | Where it goes |
| --- | --- | --- |
| core | character, realm, class, level, guild, rank, alts | local snapshot |
| pos | zone time ("typically found in"), hearth location, live position | local snapshot + `Logs\WoWChatLog.txt` |
| inventory | bag + bank item counts | local snapshot |

Snapshots land in `companion/store/<name>-<realm>/NNNN.json` (last 20 kept).
Roster data flows back into `Interface\AddOns\DecadesSync\Data\DecadesData.lua`.

Coming in later phases (spec): loot ledger + RCLootCouncil, reputation,
professions, PvP rivalries, sightings, chat history, signups, parses, the sim
link — all through this same pipe, then synced to the guild backend.

## Troubleshooting

- **Companion can't find WoW** → set `wow_root` in `companion/companion.toml`
  (step 3.3).
- **Companion never syncs** → SavedVariables only get written on logout or
  `/reload`. Log in, `/reload`, watch the window.
- **Addon doesn't appear in-game** → check the folder is
  `Interface\AddOns\DecadesSync` (not `DecadesSync\DecadesSync`), and Load out
  of date AddOns is ticked.
- **`/dec` still says `data: never`** → run the companion *after* your first
  `/reload`, then check `/dec` again (the game reads `Data.lua` at login/reload).
- **Python `tomllib` errors** → you're on Python < 3.11; reinstall 3.14.

## For developers

```bash
python -m unittest discover -s companion -p "test_*.py"   # 38 tests
```

- `addon/DecadesSync/` — Lua 5.1, no libraries; namespace `Decades`, SV `DecadesSyncDB`
- `companion/` — stdlib-only Python: `svparse` (SV→JSON), `watch`/`store`, `emitter` (JSON→Data.lua), `main`
- Plans: [docs/plans](docs/plans) · Spec: [docs/specs](docs/specs)

Known open items: Forever interface number needs an in-game read
(`/dump select(4, GetBuildInfo())`); `BAG_UPDATE_DELAYED` needs verifying on
the 1.60-era client.
