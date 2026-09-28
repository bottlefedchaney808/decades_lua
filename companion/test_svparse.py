import unittest
from companion.svparse import parse_sv, SVParseError

class TestParseSV(unittest.TestCase):
    def test_nested_table(self):
        text = 'DecadesSyncDB = {\n\t["core"] = {\n\t\t["name"] = "Grukk",\n\t\t["level"] = 60,\n\t},\n}\n'
        self.assertEqual(parse_sv(text), {"core": {"name": "Grukk", "level": 60}})
    def test_types_and_trailing_comma(self):
        text = 'DecadesSyncDB = {\n\t["x"] = true,\n\t["y"] = nil,\n\t["z"] = -1.5, ["empty"] = {},\n}'
        self.assertEqual(parse_sv(text), {"x": True, "y": None, "z": -1.5, "empty": {}})
    def test_numeric_string_keys_and_garbage(self):
        self.assertEqual(parse_sv('DecadesSyncDB = { ["1234"] = 3, }'), {"1234": 3})
        with self.assertRaises(SVParseError):
            parse_sv('DecadesSyncDB = { ["a"] = function() end, }')
    def test_escaped_string(self):
        self.assertEqual(parse_sv(r'DecadesSyncDB = { ["n"] = "a\"b\\c", }'), {"n": 'a"b\\c'})

    def test_positional_array_becomes_list(self):
        text = 'DecadesSyncDB = {\n\t["roster"] = {\n\t\t{\n\t\t\t["name"] = "Grukk",\n\t\t},\n\t\t{\n\t\t\t["name"] = "Ulu",\n\t\t},\n\t},\n}\n'
        self.assertEqual(parse_sv(text), {"roster": [{"name": "Grukk"}, {"name": "Ulu"}]})
    def test_mixed_table_stays_dict(self):
        # 1..n sequential integer keys -> list; anything else stays a dict with string keys
        self.assertEqual(parse_sv('DecadesSyncDB = { [1]="a", [2]="b", }'), ["a", "b"])
        self.assertEqual(parse_sv('DecadesSyncDB = { [1]="a", ["x"]="b", }'), {"1": "a", "x": "b"})
    def test_scalar_array(self):
        self.assertEqual(parse_sv('DecadesSyncDB = { 1, 2, 3, }'), [1, 2, 3])

if __name__ == "__main__":
    unittest.main()
