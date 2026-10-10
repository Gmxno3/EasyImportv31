#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyImport Asistan — ÖZELLİK DEĞERLENDİRİCİ (Python / referans uygulama)  [A1]

spec/features.json dosyasını OKUR ve bir RAW sözlüğünü sabit uzunlukta özellik
vektörüne çevirir. JS ve Lua sürümleri bununla BİREBİR aynı sonucu vermek zorundadır;
tools/verify_runtime.py bunu zorunlu tutar.

Kullanım:
    import ei_features
    vec = ei_features.compute(spec, raw)     # -> list[float], len == spec["dim"]
"""
import math

EPS = 1e-6
_LN10 = math.log(10.0)


def log10(x):
    """Tüm dillerde aynı: ln(x)/ln(10)."""
    return math.log(x) / _LN10


def asnum(v):
    """RAW değerini güvenli sayıya çevirir. None/str/bool -> 0.0/1.0, NaN -> 0.0."""
    if v is None:
        return 0.0
    if v is True:
        return 1.0
    if v is False:
        return 0.0
    if isinstance(v, (int, float)):
        x = float(v)
        if x != x:            # NaN
            return 0.0
        if x == float("inf"):
            return 1e12
        if x == float("-inf"):
            return -1e12
        return x
    return 0.0


def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _divisor(raw, f):
    d = f.get("d")
    if d is None:
        return 1.0
    if isinstance(d, str):
        dv = asnum(raw.get(d))
    else:
        dv = asnum(d)
    if dv == 0.0:
        return 1.0
    return dv


def _num(raw, f):
    x = asnum(raw.get(f.get("src")))
    norm = f.get("norm", "id")

    if norm == "id":
        return x
    if norm == "clamp01":
        return clamp(x, 0.0, 1.0)
    if norm == "log1p":
        return log10(1.0 + (x if x > 0.0 else 0.0))
    if norm == "log":
        lo = f.get("lo", -6.0)
        hi = f.get("hi", 6.0)
        return clamp(log10(x if x > EPS else EPS), lo, hi)

    dv = _divisor(raw, f)
    adv = dv if dv > 0.0 else -dv
    if adv == 0.0:
        adv = 1.0
    if norm == "div":
        return x / adv
    if norm == "divlog":
        lo = f.get("lo", -6.0)
        hi = f.get("hi", 6.0)
        return clamp(log10((x if x > EPS else EPS) / adv), lo, hi)
    return x


def compute(spec, raw):
    """RAW sözlüğü -> özellik vektörü (list[float])."""
    out = []
    for f in spec["features"]:
        k = f["k"]
        if k == "num":
            out.append(_num(raw, f))
        elif k == "bool":
            out.append(1.0 if raw.get(f["src"]) else 0.0)
        elif k == "token":
            toks = raw.get(f["src"])
            out.append(1.0 if (isinstance(toks, dict) and toks.get(f["t"])) else 0.0)
        elif k == "onehot":
            v = raw.get(f["src"])
            for val in f["values"]:
                out.append(1.0 if v == val else 0.0)
        elif k == "bucket":
            x = asnum(raw.get(f["src"]))
            edges = f["edges"]
            idx = len(edges)
            for i, e in enumerate(edges):
                if x <= e:
                    idx = i
                    break
            for i in range(len(edges) + 1):
                out.append(1.0 if i == idx else 0.0)
        else:
            raise ValueError("bilinmeyen tur: %s" % k)
    return out


def load_spec(path):
    import json
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
