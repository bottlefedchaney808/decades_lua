"""Tests for companion.store and companion.watch (plan Task 5)."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from companion.store import Store
from companion.watch import Watcher, find_wow


def make_sv(wow_root: Path, account: str = "ACC1") -> Path:
    """Create <wow_root>/WTF/Account/<account>/SavedVariables/DecadesSync.lua."""
    sv = wow_root / "WTF" / "Account" / account / "SavedVariables" / "DecadesSync.lua"
    sv.parent.mkdir(parents=True, exist_ok=True)
    sv.write_text("DecadesSyncDB = {\n}\n", encoding="utf-8")
    return sv


class TempDirMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


class TestStore(TempDirMixin):
    def setUp(self):
        super().setUp()
        self.store = Store(self.root)

    def test_append_creates_zero_padded_seq_files(self):
        p1 = self.store.append("Grukk-Feathermoon", {"core": {"name": "Grukk"}})
        p2 = self.store.append("Grukk-Feathermoon", {"core": {"name": "Grukk"}, "n": 2})
        p3 = self.store.append("Grukk-Feathermoon", {"n": 3})
        char_dir = self.root / "Grukk-Feathermoon"
        names = sorted(p.name for p in char_dir.glob("*.json"))
        self.assertEqual(names, ["0001.json", "0002.json", "0003.json"])
        self.assertEqual(p1.name, "0001.json")
        self.assertEqual(p2.name, "0002.json")
        self.assertEqual(p3.name, "0003.json")
        data = json.loads((char_dir / "0001.json").read_text(encoding="utf-8"))
        self.assertEqual(data, {"core": {"name": "Grukk"}})

    def test_latest_returns_newest(self):
        self.store.append("c", {"seq": 1})
        self.store.append("c", {"seq": 2})
        self.store.append("c", {"seq": 3})
        self.assertEqual(self.store.latest("c"), {"seq": 3})

    def test_latest_empty_returns_none(self):
        self.assertIsNone(self.store.latest("nobody"))

    def test_prune_keeps_last_20(self):
        for i in range(1, 26):
            self.store.append("c", {"i": i})
        files = sorted((self.root / "c").glob("*.json"))
        self.assertEqual(len(files), 20)
        self.assertEqual(files[0].name, "0006.json")
        self.assertEqual(files[-1].name, "0025.json")
        self.assertEqual(self.store.latest("c"), {"i": 25})

    def test_chars_have_independent_seqs(self):
        self.store.append("a", {"x": 1})
        self.store.append("b", {"x": 1})
        self.assertTrue((self.root / "a" / "0001.json").exists())
        self.assertTrue((self.root / "b" / "0001.json").exists())


class TestFindWow(TempDirMixin):
    def setUp(self):
        super().setUp()
        self._tmp2 = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp2.cleanup)
        self.other = Path(self._tmp2.name)

    def test_explicit_root_with_sv(self):
        make_sv(self.root)
        self.assertEqual(find_wow(str(self.root)), self.root)

    def test_explicit_root_without_sv_falls_through_to_scan(self):
        make_sv(self.other)
        found = find_wow(str(self.root), candidates=[str(self.other)])
        self.assertEqual(found, self.other)

    def test_scan_finds_nested_install(self):
        wow = self.root / "World of Warcraft" / "_classic_"
        make_sv(wow)
        found = find_wow(None, candidates=[str(self.root)])
        self.assertEqual(found, wow)

    def test_scan_depth_cap_4(self):
        wow = self.root.joinpath(*"abcde")  # 5 levels below the candidate
        make_sv(wow)
        with self.assertRaises(FileNotFoundError):
            find_wow(None, candidates=[str(self.root)])

    def test_no_match_raises(self):
        with self.assertRaises(FileNotFoundError):
            find_wow(None, candidates=[str(self.root)])


class TestWatcher(TempDirMixin):
    def setUp(self):
        super().setUp()
        self.sv = make_sv(self.root)

    def test_first_poll_is_initial_sync(self):
        w = Watcher(self.sv)
        self.assertEqual(w.poll(), Path(self.sv))

    def test_no_change_returns_none(self):
        w = Watcher(self.sv)
        w.poll()
        self.assertIsNone(w.poll())

    def test_mtime_change_detected_then_quiet(self):
        w = Watcher(self.sv)
        w.poll()
        st = self.sv.stat()
        os.utime(self.sv, (st.st_atime, st.st_mtime + 5))
        self.assertEqual(w.poll(), Path(self.sv))
        self.assertIsNone(w.poll())

    def test_missing_then_created(self):
        sv2 = self.root / "WTF" / "Account" / "X" / "SavedVariables" / "DecadesSync.lua"
        sv2.parent.mkdir(parents=True, exist_ok=True)
        w = Watcher(sv2)
        self.assertIsNone(w.poll())
        sv2.write_text("DecadesSyncDB = {\n}\n", encoding="utf-8")
        self.assertEqual(w.poll(), Path(sv2))

    def test_delete_returns_none(self):
        w = Watcher(self.sv)
        w.poll()
        self.sv.unlink()
        self.assertIsNone(w.poll())


if __name__ == "__main__":
    unittest.main()
