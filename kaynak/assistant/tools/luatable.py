#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python değer -> Lua table literal (Lua 5.1 / 5.3 / Luau uyumlu)."""

import math


def _esc(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s


def _num(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    x = float(x)
    if x != x:
        return "0"
    if x == math.inf:
        return "1e308"
    if x == -math.inf:
        return "-1e308"
    if x == math.floor(x) and abs(x) < 1e15:
        return "%d" % int(x)
    return "%.17g" % x


def dumps(v, indent=0, _first=True):
    pad = "  " * indent
    pad2 = "  " * (indent + 1)

    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return '"%s"' % _esc(v)

    if isinstance(v, (list, tuple)):
        if not v:
            return "{}"
        parts = [dumps(x, indent + 1, False) for x in v]
        return "{\n" + "".join(pad2 + p + ",\n" for p in parts) + pad + "}"

    if isinstance(v, dict):
        if not v:
            return "{}"
        lines = []
        for k, val in v.items():
            if isinstance(k, str) and k.replace("_", "").isalnum() and not k[0].isdigit():
                key = k
            else:
                key = '[ "%s" ]' % _esc(str(k))
            lines.append("%s%s = %s,\n" % (pad2, key, dumps(val, indent + 1, False)))
        return "{\n" + "".join(lines) + pad + "}"

    raise TypeError("dönüştürülemedi: %r" % type(v))
