# Decades Sync — Plan A (addon + companion pipe)

A World of Warcraft addon (`DecadesSync`) that rolls guild data into
SavedVariables, and a stdlib-only Python companion that watches the SV file,
parses it to JSON, stores snapshots, and writes `Data.lua` back for the addon
to read on next login. This is **Plan A** of the Decades guild hub: proving
the offline data loop end-to-end. See [docs/plans](docs/plans) and
[docs/specs](docs/specs) for the master plan and specifications.

## Layout

| Path | What it is |
| --- | --- |
| `addon/DecadesSync/` | Lua 5.1 addon (namespace `Decades`, SV table `DecadesSyncDB`): core, `pos`, `inventory`, Data.lua loader |
| `companion/` | Stdlib-only Python 3.11+: SV parser, WoW-dir discovery + watcher, rolling JSON store, Data.lua emitter, main loop |
| `companion/store/` | Local snapshots written by the companion (`<char-key>/<NNNN>.json`, last 20 kept) |
| `companion/fixtures/` | Hand-written SavedVariables sample used by the e2e test |

## Status

| Piece | State |
| --- | --- |
| Addon → SV collection (core / pos / inventory) | done |
| Companion offline pipe (watch → parse → store → emit) | done |
| Firebase ingest (Plan B) | pending |
| Interface number in-game check (`/dump select(4, GetBuildInfo())`) | pending |

## Run the companion

Requires Python 3.11+ (uses stdlib `tomllib`). No third-party packages.

```bash
# one sync cycle
python -m companion.main --config companion/companion.toml

# daemon: poll every poll_seconds (default 2.0)
python -m companion.main --config companion/companion.toml --loop
```

Configuration (`companion/companion.toml`):

| Key | Meaning |
| --- | --- |
| `wow_root` | Explicit WoW install dir; empty = auto-discover (`WTF/Account/*/SavedVariables/DecadesSync.lua`) |
| `poll_seconds` | Poll interval in `--loop` mode |
| `ingest_url` | Hub endpoint; empty = offline stub (upload skipped with a log line). Any value raises until Plan B wires it |

What one cycle does: poll the SV file → on change, parse it, derive the char
key (`name-realm`, lowercased), append `companion/store/<char-key>/<NNNN>.json`,
run the upload stub, and write
`<wow>/Interface/AddOns/DecadesSync/Data/DecadesData.lua` (atomic replace) for
the addon to read at next login.

## Install the addon

1. Copy `addon/DecadesSync/` into your WoW `Interface/AddOns/` directory.
2. Enable **Decades Sync** on the character selection screen.
3. In game, run `/chatlog` — the `pos` module's live-position lines
   (`[DEC] POS|zone|sub|x|y|z`) go to `Logs/WoWChatLog.txt`.
4. `/dec status` prints character, version, and the generatedAt stamp of the
   last data the companion pushed.

## Testing

```bash
python -m unittest discover -s companion -p "test_*.py"
```

Covers the SV parser, watcher/store, emitter round-trip, main loop, and the
end-to-end fixture test (fixture SV → store snapshot + Data.lua).
