"""Deterministic parser for the SavedVariables Lua-table subset the DecadesSync addon emits.

Grammar (anything outside it raises SVParseError):

    file    := IDENT '=' table
    table   := '{' [entry {',' entry} [',']] '}'
    entry   := '[' STRING ']' '=' value
             | '[' NUMBER ']' '=' value
             | IDENT '=' value
             | value                      -- positional; auto-indexed 1..n
    value   := STRING | NUMBER | 'true' | 'false' | 'nil' | table

Strings support exactly the escapes \" \\ \n. Numbers become int when
integral, float otherwise. No eval, no external libraries.
"""

import re

__all__ = ["parse_sv", "SVParseError"]


class SVParseError(ValueError):
    """Raised when the text is not valid SavedVariables Lua for this grammar."""


_ESCAPES = {'"': '"', "\\": "\\", "n": "\n"}

_TOKEN_RE = re.compile(
    r"""
      (?P<ws>\s+)
    | (?P<string>"(?:\\.|[^"\\\n])*")
    | (?P<number>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
    | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<punct>[{}\[\]=,])
    """,
    re.VERBOSE,
)

_INTEGRAL_RE = re.compile(r"-?\d+\Z")


def _decode_string(raw: str, pos: int) -> str:
    """Decode a quoted literal's escape sequences; reject unknown escapes."""
    body = raw[1:-1]
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            if i + 1 >= len(body) or body[i + 1] not in _ESCAPES:
                raise SVParseError(f"unsupported escape at offset {pos + i}: {body[i:i + 2]!r}")
            out.append(_ESCAPES[body[i + 1]])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _maybe_list(table: dict):
    """Convert a table whose keys are exactly the integers 1..n to a list.

    WoW's SV writer emits arrays as positional entries (or explicit [1]=..[n]=);
    round-tripping them as dicts would break every consumer. Anything else --
    mixed, sparse, non-sequential -- stays a dict with string keys.
    """
    if not table:
        return table
    n = len(table)
    if all(k.isdigit() and 1 <= int(k) <= n for k in table) and len({int(k) for k in table}) == n:
        return [table[str(i)] for i in range(1, n + 1)]
    return table


Token = tuple  # (kind, value, offset)


MAX_DEPTH = 200
"""Nesting deeper than any real SavedVariables table; guards the mutual
recursion in parse_table/parse_value (CARL R1-F3) and adversarial input."""


def _tokenize(text: str):
    """Yield (kind, value, offset) lazily; ws tokens are dropped (CARL R1-F4:
    a materialized token list peaked ~30x the input size on multi-MB SVs)."""
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if m is None:
            snippet = text[pos:pos + 20]
            raise SVParseError(f"unexpected character at offset {pos}: {snippet!r}")
        if m.lastgroup != "ws":
            yield (m.lastgroup, m.group(), pos)
        pos = m.end()


class _Parser:
    def __init__(self, tokens, max_depth: int = MAX_DEPTH):
        self._it = iter(tokens)
        self._buf: list[Token] = []  # 1-token lookahead
        self.max_depth = max_depth
        self.depth = 0

    def _peek(self) -> Token:
        if not self._buf:
            try:
                self._buf.append(next(self._it))
            except StopIteration:
                return ("eof", "", -1)
        return self._buf[0]

    def _next(self, kind: str | None = None, value: str | None = None) -> Token:
        tok_kind, tok_value, pos = self._peek()
        if tok_kind == "eof":
            raise SVParseError(f"unexpected end of input (wanted {value or kind})")
        if kind is not None and tok_kind != kind:
            raise SVParseError(f"expected {kind} at offset {pos}, got {tok_value!r}")
        if value is not None and tok_value != value:
            raise SVParseError(f"expected {value!r} at offset {pos}, got {tok_value!r}")
        self._buf.pop(0)
        return tok_kind, tok_value, pos

    def parse_file(self) -> dict:
        _, name, _ = self._next("ident")
        self._next(value="=")
        result = self.parse_table()
        if self._peek()[0] != "eof":
            _, tok_value, pos = self._peek()
            raise SVParseError(f"trailing input at offset {pos}: {tok_value!r}")
        return result

    def parse_table(self):
        self.depth += 1
        if self.depth > self.max_depth:
            raise SVParseError(f"nesting too deep (>{self.max_depth})")
        self._next(value="{")
        table = {}
        auto = 0  # positional-entry auto index (1-based, Lua semantics)
        while True:
            kind, value, pos = self._peek()
            if kind == "punct" and value == "}":
                self._next()
                break
            auto += 1
            self.parse_entry(table, auto)
            kind, value, pos = self._next()
            if kind == "punct" and value == ",":
                continue
            if kind == "punct" and value == "}":
                break
            raise SVParseError(f"expected ',' or '}}' at offset {pos}, got {value!r}")
        self.depth -= 1
        return _maybe_list(table)
    def parse_entry(self, table: dict, auto: int) -> None:
        kind, value, pos = self._peek()
        if kind == "punct" and value == "[":
            self._next()
            nxt_kind, raw, spos = self._next()
            self._next(value="]")
            self._next(value="=")
            if nxt_kind == "string":
                key = _decode_string(raw, spos)
            elif nxt_kind == "number" and _INTEGRAL_RE.match(raw):
                key = str(int(raw))
            else:
                raise SVParseError(f"expected string or integer key at offset {spos}, got {raw!r}")
        elif kind == "ident" and value not in ("true", "false", "nil"):
            self._next()
            key = value
            self._next(value="=")
        else:
            key = str(auto)  # positional entry: value with no key
        table[key] = self.parse_value()

    def parse_value(self):
        kind, value, pos = self._peek()
        if kind == "string":
            self._next()
            return _decode_string(value, pos)
        if kind == "number":
            self._next()
            return int(value) if _INTEGRAL_RE.match(value) else float(value)
        if kind == "punct" and value == "{":
            return self.parse_table()
        if kind == "ident" and value in ("true", "false", "nil"):
            self._next()
            return {"true": True, "false": False, "nil": None}[value]
        raise SVParseError(f"expected a value at offset {pos}, got {value!r}")


def parse_sv(text: str) -> dict | list:
    """Parse SavedVariables Lua text ('Name = { ... }') into a dict.

    Raises SVParseError for any construct outside the supported grammar.
    """
    return _Parser(_tokenize(text)).parse_file()
