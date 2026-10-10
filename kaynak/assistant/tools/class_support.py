#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINIF DESTEĞİ (v15) — model/model.json meta.support

Eğitim etiketlerinde her sınıftan kaç örnek olduğunu sayar ve model meta'sına yazar:
    meta.support     : {sınıf: örnek sayısı}   (datasets/labels/*.jsonl)
    meta.minSupport  : eşik (varsayılan 20)
    meta.pseudo      : Roblox sınıfı olmayan etiketler (asla tahmin edilmez)

Ağırlıklar değişmez; yalnızca hangi sınıfların güvenilir biçimde tahmin edilebileceği belirlenir.
export_model.py bu alanlardan çalışma zamanı kapısını üretir:
    desteği eşiğin altındaki sınıf seçilmez; en iyi aday kapıya takılırsa güven 0,69'da sınırlanır.

Kullanım:  python3 tools/class_support.py          (yazar)
           python3 tools/class_support.py --check   (meta uyumlu mu? çıkış 0/1)
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, "model", "model.json")
LABELS = sorted(glob.glob(os.path.join(ROOT, "datasets", "labels", "*.jsonl")))
MIN_SUPPORT = 20
PSEUDO = ["DROP", "Item", "MERGE", "UIGridLayout"]


def count_support():
    counts = {}
    for path in LABELS:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                cls = json.loads(ln).get("cls")
                if cls:
                    counts[cls] = counts.get(cls, 0) + 1
    return counts


def build_meta(model_meta, classes):
    counts = count_support()
    support = {c: int(counts.get(c, 0)) for c in classes}
    return dict(model_meta, support=support, minSupport=MIN_SUPPORT, pseudo=PSEUDO)


def elig_list(classes, support):
    """Tahmin kapısı: pseudo değil ve destek eşiğinde (veya üstünde) olan sınıflar."""
    return [(c not in PSEUDO) and int(support.get(c, 0)) >= MIN_SUPPORT for c in classes]


def main():
    check = "--check" in sys.argv
    obj = json.load(open(MODEL, encoding="utf-8"))
    classes = obj["models"]["class"]["classes"]
    want = build_meta(obj["meta"], classes)
    if check:
        ok = all(obj["meta"].get(k) == want[k] for k in ("support", "minSupport", "pseudo")) \
            and obj["models"]["class"].get("elig") == elig_list(classes, want["support"])
        print("[%s] meta.support %s" % ("OK" if ok else "FAIL", "etiketlerle uyumlu" if ok else "ETİKETLERLE UYUMSUZ"))
        for c in classes:
            print("   %-14s %5d %s" % (c, want["support"][c], "" if want["support"][c] >= MIN_SUPPORT and c not in PSEUDO else "(kapalı)"))
        sys.exit(0 if ok else 1)
    obj["meta"] = want
    obj["models"]["class"]["elig"] = elig_list(classes, want["support"])
    with open(MODEL, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, sort_keys=True, indent=1)
    print("[OK] meta.support ve models.class.elig yazıldı (eşik %d, pseudo %s)" % (MIN_SUPPORT, ", ".join(PSEUDO)))
    for c in classes:
        print("   %-14s %5d" % (c, want["support"][c]))


if __name__ == "__main__":
    main()
