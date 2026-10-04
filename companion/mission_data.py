"""Read serialized DCS tables as data, never execute authored Lua.

Promoted from the mission-identity round-trip prototype.
"""
import re

class LuaData:
    """Bounded data-only subset used by serialized DCS mission tables."""
    def __init__(self, text):
        self.text, self.pos = text, 0

    def skip(self):
        while True:
            m = re.match(r'\s+|--\[(=*)\[', self.text[self.pos:])
            if m:
                self.pos += m.end()
                if m.group(1) is not None:
                    end = self.text.index(']' + m.group(1) + ']', self.pos)
                    self.pos = end + len(m.group(1)) + 2
            elif self.text.startswith('--', self.pos):
                end = self.text.find('\n', self.pos)
                self.pos = len(self.text) if end < 0 else end + 1
            else:
                return

    def take(self, token):
        self.skip()
        if not self.text.startswith(token, self.pos):
            raise ValueError(f'Expected {token!r} at {self.pos}; unsupported Lua data')
        self.pos += len(token)

    def value(self, depth=0):
        if depth > 100:
            raise ValueError('Table nesting too deep')
        self.skip()
        c = self.text[self.pos:self.pos + 1]
        if c == '{':
            self.pos += 1
            result, index = {}, 1
            while True:
                self.skip()
                if self.text.startswith('}', self.pos):
                    self.pos += 1
                    return result
                if self.text.startswith('[', self.pos) and not re.match(r'\[(=*)\[', self.text[self.pos:]):
                    self.pos += 1
                    key = self.value(depth + 1)
                    self.take(']')
                    self.take('=')
                else:
                    m = re.match(r'([A-Za-z_]\w*)\s*=', self.text[self.pos:])
                    if m:
                        key = m.group(1)
                        self.pos += m.end()
                    else:
                        key, index = index, index + 1
                if key in result:
                    raise ValueError('Duplicate table key')
                result[key] = self.value(depth + 1)
                self.skip()
                if self.text[self.pos:self.pos + 1] in (',', ';'):
                    self.pos += 1
        if c in ('"', "'"):
            self.pos += 1
            out = []
            while self.pos < len(self.text):
                ch = self.text[self.pos]
                self.pos += 1
                if ch == c:
                    return ''.join(out)
                if ch != '\\':
                    out.append(ch)
                    continue
                ch = self.text[self.pos]
                self.pos += 1
                if ch.isdigit():
                    digits = ch
                    while len(digits) < 3 and self.text[self.pos:self.pos + 1].isdigit():
                        digits += self.text[self.pos]
                        self.pos += 1
                    out.append(chr(int(digits)))
                elif ch in 'abfnrtv':
                    out.append(dict(zip('abfnrtv', '\a\b\f\n\r\t\v'))[ch])
                elif ch in ('\\', '"', "'", '\n'):
                    out.append(ch)
                elif ch == '\r':
                    if self.text[self.pos:self.pos + 1] == '\n':
                        self.pos += 1
                    out.append('\n')
                else:
                    raise ValueError(f'Unsupported escape {ch!r}')
            raise ValueError('Unterminated string')
        m = re.match(r'\[(=*)\[', self.text[self.pos:])
        if m:
            self.pos += m.end()
            end_token = ']' + m.group(1) + ']'
            end = self.text.index(end_token, self.pos)
            value = self.text[self.pos:end]
            self.pos = end + len(end_token)
            return value[1:] if value.startswith('\n') else value
        m = re.match(r'-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|true\b|false\b|nil\b', self.text[self.pos:])
        if not m:
            raise ValueError(f'Executable or unsupported Lua at {self.pos}')
        self.pos += m.end()
        token = m.group()
        if token in ('true', 'false', 'nil'):
            return {'true': True, 'false': False, 'nil': None}[token]
        number = float(token)
        if not float('-inf') < number < float('inf'):
            raise ValueError('Nonfinite number')
        return int(number) if number.is_integer() else number

    def assignment(self, name):
        self.take(name)
        self.take('=')
        result = self.value()
        self.skip()
        if self.pos != len(self.text):
            raise ValueError('Trailing executable or unsupported Lua')
        return result


    def mission(self):
        return self.assignment('mission')

def serialize(value):
    if isinstance(value, dict):
        return '{\n' + ''.join(f'[{serialize(k)}]={serialize(v)},\n' for k, v in value.items()) + '}'
    if isinstance(value, str):
        return '"' + ''.join('\\%03d' % ord(c) if ord(c) < 32 else '\\' + c if c in '\\"' else c for c in value) + '"'
    if value is None:
        return 'nil'
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)

