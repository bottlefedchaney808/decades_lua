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
from companion.svparse import SVParseError, parse_sv
from companion.watch import Watcher, find_wow, iter_sv

__all__ = ["run", "main", "char_key"]

ADDON_DATA_RELPATH = Path("Interface") / "AddOns" / "DecadesSync" / "Data" / "DecadesData.lua"

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


def _cycle(cfg: dict, store_dir: Path, wow: Path | None = None) -> str | None:
    """Run one watcher poll; store + emit on change. Returns char key or None."""
    wow = wow or find_wow(cfg["wow_root"] or None)
    matches = sorted(iter_sv(wow))
    if not matches:
        raise FileNotFoundError(f"No DecadesSync.lua SavedVariables under {wow}")

    synced = None
    for sv_path in matches:  # every account gets a chance (CARL R1-F10)
        watcher = _watchers.get(str(sv_path))
        if watcher is None:
            watcher = _watchers[str(sv_path)] = Watcher(sv_path)
        if watcher.poll() is None:
            continue

        text = _read_stable(sv_path)  # CARL R1-F2: don't parse a mid-write file
        if text is None:
            _watchers.pop(str(sv_path), None)  # retry next cycle
            continue
        try:
            sv = parse_sv(text)  # strict utf-8 (CARL R1-F12)
        except (SVParseError, RecursionError):
            _watchers.pop(str(sv_path), None)  # CARL R1-F2: retry next cycle
            continue
        if not isinstance(sv, dict):  # top-level positional-array edge case
            sv = {"value": sv}
        key = char_key(sv)
        Store(store_dir).append(key, sv)
        _upload(cfg, key)
        generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data_lua = wow / ADDON_DATA_RELPATH
        _emit_with_retry({"generatedAt": generated_at, "roster": []}, data_lua)
        print(f"synced {key} -> {data_lua}")
        synced = key
    return synced


def _read_stable(sv_path: Path, attempts: int = 4, settle: float = 0.25) -> str | None:
    """Read the SV only when its size+mtime have settled (CARL R1-F2).

    The game writes SavedVariables at logout/reload; a poll landing mid-write
    used to parse a partial file and lose the snapshot forever. Returns the
    text once stable, or None if still churning after `attempts`.
    """
    last = None
    for _ in range(attempts):
        try:
            st = sv_path.stat()
            snap = (st.st_mtime_ns, st.st_size)
            if snap == last:
                return sv_path.read_text(encoding="utf-8")
            last = snap
        except OSError:
            return None
        time.sleep(settle)
    return None


def _emit_with_retry(data: dict, out: Path, attempts: int = 3, backoff: float = 0.5) -> None:
    """Emit Data.lua, tolerating a transiently-locked target (CARL R1-F7).

    Windows refuses os.replace while another process (AV scan, editor, the
    game itself) holds the target without FILE_SHARE_DELETE. Retry briefly,
    then give up for this cycle -- the next sync rewrites it anyway.
    """
    for i in range(attempts):
        try:
            emit_data_lua(data, out)
            return
        except PermissionError:
            if i == attempts - 1:
                print(f"WARN: {out.name} locked, skipped this cycle", file=sys.stderr)
                return
            time.sleep(backoff)


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
    wow = find_wow(cfg["wow_root"] or None)  # resolve once (CARL R1-F5)
    backoff = float(cfg.get("poll_seconds", 2.0))
    try:
        while True:
            try:
                result = _cycle(cfg, store_dir, wow=wow)
            except (OSError, RecursionError, NotImplementedError) as exc:
                if once:
                    raise
                print(f"WARN: cycle failed ({type(exc).__name__}: {exc}); retrying",
                      file=sys.stderr)  # CARL R1-F1: one bad cycle never kills the loop
                time.sleep(backoff)
                backoff = min(30.0, backoff * 2)
                continue
            backoff = float(cfg.get("poll_seconds", 2.0))
            if once:
                return result
            time.sleep(backoff)
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
