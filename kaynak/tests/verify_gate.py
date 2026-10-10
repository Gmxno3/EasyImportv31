#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: sınıf destek kapısı (v15)
  • destek eşiği altındaki ve pseudo sınıflar ASLA seçilmez (rastgele girdilerle)
  • ham en iyi aday kapıya takılırsa güven 0,69'u geçmez (Studio 0,70 eşiğinin altında kalır)
  • kapı tek kaynak: models.class.elig ile model.json uyumlu
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import train_class as T  # noqa: E402


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    m = json.load(open(os.path.join(ROOT, "assistant", "model", "model.json"), encoding="utf-8"))
    blk = m["models"]["class"]
    classes = blk["classes"]
    elig = blk["elig"]
    closed = {c for c, e in zip(classes, elig) if not e}
    check(len(elig) == len(classes), "kapı listesi sınıf listesiyle aynı uzunlukta")
    check({"ScrollingFrame", "ImageButton", "Item", "DROP", "MERGE", "UIGridLayout"} <= closed,
          "kapalı sınıflar: %s" % ", ".join(sorted(closed)))
    rng = random.Random(15)
    dim = blk["W"] and len(blk["W"][0])
    bad_pick = 0
    bad_conf = 0
    n = 400
    for _ in range(n):
        feat = {}
        for i in rng.sample(range(dim), 40):
            feat[i] = rng.uniform(-3, 3)
        pr = T.predict(blk, {"feat": feat})
        if pr["cls"] in closed:
            bad_pick += 1
        raw_top = max(range(len(classes)), key=lambda c: (pr["probs"][c], -classes.index(classes[c])))
        if not elig[raw_top] and pr["conf"] > 0.69 + 1e-12:
            bad_conf += 1
    check(bad_pick == 0, "%d rastgele girdide kapalı sınıf seçilmedi" % n)
    check(bad_conf == 0, "ham en iyi aday kapıdayken güven 0,69'u geçmedi")
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — destek kapısı kapalı sınıfları ve aşırı güveni engeller")
    return 0


if __name__ == "__main__":
    sys.exit(main())
