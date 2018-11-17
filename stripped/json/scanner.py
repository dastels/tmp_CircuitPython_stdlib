"""JSON token scanner
"""
import re
try:
    from _json import make_scanner as c_make_scanner
except ImportError:
    c_make_scanner = None


class Match:                                                                    ###
    def __init__(self, end, groups):                                            ###
        self._end = end                                                         ###
        self._groups = groups                                                   ###
    def end(self):                                                              ###
        return self._end                                                        ###
    def groups(self):                                                           ###
        return self._groups                                                     ###
class NUMBER_RE:                                                                ###
    REGEX = re.compile(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?')            ###
    CHARS = ['-', '+', '.', 'e', 'E'] + [chr(i) for i in range(ord('0'), ord('9') + 1)]  ###
    def match(s, pos):                                                          ###
        i = pos                                                                 ###
        try:                                                                    ###
            while True:                                                         ###
                if s[i] not in NUMBER_RE.CHARS:                                 ###
                    break                                                       ###
                i += 1                                                          ###
        except IndexError:                                                      ###
            pass                                                                ###
        if i == pos:                                                            ###
            return None                                                         ###
        res = NUMBER_RE.REGEX.match(s[pos:i])                                   ###
        if not res:                                                             ###
            return None                                                         ###
        end = pos + len(res.group(0))                                           ###
        return Match(end, (res.group(1), res.group(2), res.group(3)))           ###
                                                                                ###

def py_make_scanner(context):
    parse_object = context.parse_object
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    parse_constant = context.parse_constant
    object_hook = context.object_hook
    object_pairs_hook = context.object_pairs_hook
    memo = context.memo

    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration(idx)

        if nextchar == '"':
            return parse_string(string, idx + 1, strict)
        elif nextchar == '{':
            return parse_object((string, idx + 1), strict,
                _scan_once, object_hook, object_pairs_hook, memo)
        elif nextchar == '[':
            return parse_array((string, idx + 1), _scan_once)
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            return None, idx + 4
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            return True, idx + 4
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            return False, idx + 5

        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = parse_int(integer)
            return res, m.end()
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            return parse_constant('NaN'), idx + 3
        elif nextchar == 'I' and string[idx:idx + 8] == 'Infinity':
            return parse_constant('Infinity'), idx + 8
        elif nextchar == '-' and string[idx:idx + 9] == '-Infinity':
            return parse_constant('-Infinity'), idx + 9
        else:
            raise StopIteration(idx)

    def scan_once(string, idx):
        try:
            return _scan_once(string, idx)
        finally:
            memo.clear()

    return _scan_once

make_scanner = c_make_scanner or py_make_scanner