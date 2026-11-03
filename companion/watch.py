"""WoW install discovery and SavedVariables mtime watcher.

`find_wow` locates a WoW directory containing our SavedVariables file:
an explicit root is checked first, then a bounded os.walk (depth <= 4)
over the usual install locations. `Watcher` polls the SV file's mtime and
reports it once per change (first poll counts as the initial sync).
"""
from __future__ import annotations

import os
from pathlib import Path

SV_GLOBS = (
    "WTF/Account/*/*/*/SavedVariables/DecadesSync.lua",  # SavedVariablesPerCharacter
    "WTF/Account/*/SavedVariables/DecadesSync.lua",      # leftover account-wide
)
MAX_DEPTH = 4


def iter_sv(wow_dir: Path):
    """Yield DecadesSync.lua paths under a WoW root (per-char first)."""
    seen: set[Path] = set()
    for pattern in SV_GLOBS:
        for p in wow_dir.glob(pattern):
            if p not in seen:
                seen.add(p)
                yield p


def _default_candidates() -> list[str]:
    cands: list[str] = []
    pf = os.environ.get("ProgramFiles")
    if pf:
        cands.append(pf)
    cands.append("E:\\")
    cands.append("C:\\Program Files (x86)")
    return cands


def _has_sv(wow_dir: Path) -> bool:
    try:
        next(iter_sv(wow_dir))
    except (StopIteration, OSError, PermissionError):
        return False
    return True


def _scan(candidate: str) -> Path | None:
    """Depth-capped walk of candidate looking for the SV file. 0 on skip."""
    base = Path(candidate)
    base_depth = len(base.resolve().parts)
    for dirpath, dirnames, _filenames in os.walk(base, onerror=lambda _e: None):
        here = Path(dirpath)
        depth = len(here.resolve().parts) - base_depth
        if depth >= MAX_DEPTH:
            dirnames[:] = []  # do not descend below the cap
        if _has_sv(here):
            return here
    return None


def find_wow(root: str | None, candidates: list[str] | None = None) -> Path:
    """Return the WoW directory holding DecadesSync SavedVariables.

    Checks <root> first when given, then each candidate (defaults:
    %ProgramFiles%, E:\\, C:\\Program Files (x86)) with a depth-capped
    os.walk. Raises FileNotFoundError when nothing matches.
    """
    if root:
        r = Path(root)
        if _has_sv(r):
            return r
    for cand in candidates if candidates is not None else _default_candidates():
        if not cand:
            continue
        found = _scan(cand)
        if found is not None:
            return found
    raise FileNotFoundError(
        "No WoW install with WTF/Account/<acc>/<realm>/<char>/SavedVariables/DecadesSync.lua found"
    )


class Watcher:
    """Polls one SavedVariables file; returns its path once per mtime change."""

    def __init__(self, sv_path: Path | str) -> None:
        self.path = Path(sv_path)
        self._last_mtime: float | None = None

    def poll(self) -> Path | None:
        """Return the SV path when it changed since the last poll, else None.

        The first poll after construction is the initial sync: it reports
        the path if the file exists (caller parses + stores the baseline).
        """
        try:
            mtime = self.path.stat().st_mtime
        except OSError:  # missing or unreadable
            self._last_mtime = None
            return None
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            return self.path
        return None
