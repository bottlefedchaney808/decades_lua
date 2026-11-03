"""Rolling JSON store: one directory per character, last N snapshots kept.

Layout: <root>/<char_key>/<seq>.json where <seq> is a zero-padded 4-digit
counter (0001, 0002, ...). `append` writes the next snapshot and prunes the
character's directory to the newest KEEP entries.
"""
from __future__ import annotations

import json
from pathlib import Path

KEEP = 20


def _seq_of(path: Path) -> int:
    """0007.json -> 7. Unparsable names sort as 0."""
    try:
        return int(path.stem)
    except ValueError:
        return 0


class Store:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def _char_dir(self, char_key: str) -> Path:
        d = self.root / char_key
        d.mkdir(parents=True, exist_ok=True)
        return d

    def append(self, char_key: str, sv_dict: dict) -> Path:
        """Write the next snapshot for char_key, prune to KEEP, return its path."""
        d = self._char_dir(char_key)
        seq = max((_seq_of(p) for p in d.glob("*.json")), default=0) + 1
        path = d / f"{seq:04d}.json"
        tmp = d / f"{seq:04d}.json.tmp"
        tmp.write_text(json.dumps(sv_dict, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
        self.prune(char_key)
        return path

    def latest(self, char_key: str) -> dict | None:
        """Newest snapshot for char_key, or None if the character has none."""
        d = self.root / char_key
        if not d.is_dir():
            return None
        seqs = sorted(d.glob("*.json"), key=_seq_of)
        if not seqs:
            return None
        return json.loads(seqs[-1].read_text(encoding="utf-8"))

    def prune(self, char_key: str, keep: int = KEEP) -> None:
        """Keep only the newest `keep` snapshots for char_key."""
        d = self.root / char_key
        if not d.is_dir():
            return
        for path in sorted(d.glob("*.json"), key=_seq_of, reverse=True)[keep:]:
            path.unlink()
