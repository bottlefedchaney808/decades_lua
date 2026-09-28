"""Decades companion main loop: watcher -> parser -> store -> upload stub -> emitter.

One cycle:

1. resolve the WoW dir (config ``wow_root`` or auto-discovery via
   :func:`companion.watch.find_wow`) and the SavedVariables file
   ``WTF/Account/*/SavedVariables/DecadesSync.lua`` (first glob match);
2. poll the watcher once -- the first poll is the initial sync, later polls
   fire only when the file's mtime changes (the game writes it on logout);
3. on a change: parse the SV text, derive the char key (``name-realm``
   lowercased, ``unknown`` fallback), append a snapshot to the store,
   run the upload stub (offline log, or ``NotImplementedError`` once an
   ``ingest_url`` is configured -- Plan B wires it), and emit
   ``Data/DecadesData.lua`` back into the addon folder.

``run(config_path, once=True)`` performs exactly one poll and returns the
char key used, or ``None`` when nothing changed. ``once=False`` loops
forever sleeping ``poll_seconds`` between polls (no threads). Watcher
state is cached per SV path so repeated ``run`` calls in one process do
not re-report an unchanged file.

The snapshot store lives at ``<config dir>/store/`` (repo default:
``companion/store/``). Usage: ``python -m companion.main [--config PATH]
[--loop]``.
"""
from __future__ import annotations

import argparse
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from companion.emitter import emit_data_lua
from companion.store import Store
from companion.svparse import parse_sv
from companion.watch import Watcher, find_wow

__all__ = ["run", "main", "char_key"]

ADDON_DATA_RELPATH = Path("Interface") / "AddOns" / "DecadesSync" / "Data" / "DecadesData.lua"
SV_GLOB = str(Path("WTF") / "Account" / "*" / "SavedVariables" / "DecadesSync.lua")

# Watchers keyed by resolved SV path: mtime memory must survive across
# separate run() calls in the same process (a fresh Watcher would treat
# every first poll as an initial sync and re-report unchanged files).
_watchers: dict[str, Watcher] = {}


def char_key(sv: object) -> str:
    """Derive the store key from the parsed SV: name-realm lowercased."""
    core = sv.get("core") if isinstance(sv, dict) else None
    if isinstance(core, dict):
        name, realm = core.get("name"), core.get("realm")
        if isinstance(name, str) and isinstance(realm, str) and name and realm:
            return f"{name}-{realm}".lower()
    return "unknown"


def load_config(config_path: str | Path) -> dict:
    """Read companion.toml; fill defaults for missing optional keys."""
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    cfg.setdefault("wow_root", "")
    cfg.setdefault("poll_seconds", 2.0)
    cfg.setdefault("ingest_url", "")
    return cfg


def _cycle(cfg: dict, store_dir: Path) -> str | None:
    """Run one watcher poll; store + emit on change. Returns char key or None."""
    wow = find_wow(cfg["wow_root"] or None)
    matches = wow.glob(SV_GLOB)
    try:
        sv_path = next(matches)
    except StopIteration:  # pragma: no cover - find_wow already proved it exists
        raise FileNotFoundError(f"No {SV_GLOB} under {wow}") from None

    watcher = _watchers.get(str(sv_path))
    if watcher is None:
        watcher = _watchers[str(sv_path)] = Watcher(sv_path)
    if watcher.poll() is None:
        return None

    sv = parse_sv(sv_path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(sv, dict):  # top-level positional-array edge case
        sv = {"value": sv}
    key = char_key(sv)
    Store(store_dir).append(key, sv)
    _upload(cfg, key)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # <wow> sits 4 levels above the SV file: SavedVariables/<account>/Account/WTF
    data_lua = sv_path.parents[4] / ADDON_DATA_RELPATH
    emit_data_lua({"generatedAt": generated_at, "roster": []}, data_lua)
    print(f"synced {key} -> {data_lua}")
    return key


def _upload(cfg: dict, key: str) -> None:
    """Upload stub: offline log now, real ingest lands in Plan B."""
    if cfg.get("ingest_url"):
        raise NotImplementedError("Plan B")
    print(f"upload skipped (offline stub): {key}")


def run(config_path: str | Path, once: bool = True) -> str | None:
    """Run the companion: one poll cycle, or forever when once=False."""
    config_path = Path(config_path)
    cfg = load_config(config_path)
    store_dir = config_path.parent / "store"
    try:
        while True:
            result = _cycle(cfg, store_dir)
            if once:
                return result
            time.sleep(float(cfg.get("poll_seconds", 2.0)))
    except KeyboardInterrupt:
        print("companion stopped")
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m companion.main",
                                     description="Decades Sync companion pipe")
    parser.add_argument("--config", default=str(Path(__file__).with_name("companion.toml")),
                        help="path to companion.toml (default: next to main.py)")
    parser.add_argument("--loop", action="store_true",
                        help="keep polling every poll_seconds instead of one cycle")
    args = parser.parse_args(argv)
    run(args.config, once=not args.loop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
