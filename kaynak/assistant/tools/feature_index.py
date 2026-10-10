#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÖZELLİK İNDEKSİ — spec/features.json'dan okunabilir adlar ve gruplar

`ei_features.compute()` 379 boyutlu bir **sayı listesi** üretir. Eğitim, raporlama ve
"hangi özellik kararı etkiledi" analizi için bu listeyi adlara ve gruplara bağlamak gerekir.

- `names(spec)`  → 379 ad (index'teki `offset`/`count` alanlarından)
- `groups(spec)` → 379 grup harfi (A…K) — gruplu atıf (OGRENME-MOTORU §7.4) için
- `sparse(spec, vec, ndigits=4)` → yalnızca sıfır olmayan {ad: değer} sözlüğü (JSONL boyutu için)

Tek doğruluk kaynağı spec'tir; burada hiçbir özellik elle tekrarlanmaz.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC_PATH = os.path.join(ROOT, "spec", "features.json")


def load_spec(path=None):
    with open(path or SPEC_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def names(spec):
    """379 adlı liste — index'teki offset/count ile birebir hizalı."""
    out = []
    for f in spec["index"]:
        n, k, cnt = f["n"], f["k"], f.get("count", 1)
        if cnt == 1:
            out.append(n)
        elif k == "onehot":
            # ei_features.compute: f["values"] sırasıyla genişler
            feat = _feat_by_name(spec, n)
            for v in feat["values"]:
                out.append("%s#%s" % (n, v))
        elif k == "bucket":
            feat = _feat_by_name(spec, n)
            edges = feat["edges"]
            for i in range(len(edges) + 1):
                out.append("%s#b%d" % (n, i))
        else:
            for i in range(cnt):
                out.append("%s#%d" % (n, i))
    return out


def groups(spec):
    out = []
    for f in spec["index"]:
        out.extend([f["g"]] * f.get("count", 1))
    return out


def sparse(spec, vec, ndigits=4):
    """Sıfır olmayan boyutları {ad: değer} olarak döndürür (kararlı sırayla)."""
    nm = names(spec)
    if len(nm) != len(vec):
        raise ValueError("vektör boyu %d, ad sayısı %d" % (len(vec), len(nm)))
    out = {}
    for i, x in enumerate(vec):
        if x:
            out[nm[i]] = round(float(x), ndigits)
    return out


_FEAT_CACHE = {}


def _feat_by_name(spec, name):
    key = id(spec)
    if key not in _FEAT_CACHE:
        _FEAT_CACHE[key] = {f["n"]: f for f in spec["features"]}
    return _FEAT_CACHE[key][name]


def main():
    spec = load_spec()
    nm = names(spec)
    gr = groups(spec)
    assert len(nm) == spec["dim"], "ad sayısı (%d) != spec dim (%d)" % (len(nm), spec["dim"])
    assert len(gr) == spec["dim"]
    print("boyut: %d · grup dağılımı:" % len(nm))
    from collections import Counter
    for g, c in sorted(Counter(gr).items()):
        print("   %s: %d" % (g, c))
    print("ilk 3:", nm[:3], "· son 3:", nm[-3:])


if __name__ == "__main__":
    main()
