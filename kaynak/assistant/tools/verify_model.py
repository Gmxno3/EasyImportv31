#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3b — MODEL KAPISI (verify_model)

    model/model.json + datasets/labels/*.jsonl

Üç şeyi kanıtlar:
  1. ŞEKİL  : format/version/dim, 14 sınıf SABİT sırada, W (C×D), b (C), norm (D),
              checksum yeniden hesaplandığında meta.checksum ile aynı,
              stil öncülleri spec/style-rules.json ile birebir aynı.
  2. KARARLILIK: aynı veri + aynı komut → BAYT BİREBİR aynı model.json (yeniden eğitip karşılaştırır).
  3. KABUL  : dağıtılan modelde top-1 ≥ %85 · top-3 ≥ %95 (PLAN §M1).

Kullanım:
    python3 tools/verify_model.py [--quiet]
Çıkış: 0 = geçti, 1 = başarısız
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import eval as EI_EVAL       # noqa: E402  (load_model)
import train_class as T      # noqa: E402

MODEL = os.path.join(ROOT, "model", "model.json")
LABELS = os.path.join(ROOT, "datasets", "labels")
TOP1_MIN, TOP3_MIN = 0.85, 0.95


def recompute_checksum(doc):
    """train_class.export_model ile aynı blok sırası ve aynı json biçimi."""
    blocks = [{"n": "W", "d": doc["W"]}, {"n": "b", "d": doc["b"]},
              {"n": "mean", "d": doc["norm"]["mean"]}, {"n": "std", "d": doc["norm"]["std"]}]
    h = hashlib.sha256()
    for blk in blocks:
        h.update(json.dumps(blk, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return "sha256:" + h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    problems, notes = [], []

    print("=" * 74)
    print("MODEL KAPISI (A3b) — model.json")
    print("=" * 74)
    if not os.path.exists(MODEL):
        print("  [!!] %s yok — önce: python3 tools/train_class.py --eval" % MODEL)
        return 1

    obj, doc = EI_EVAL.load_model(MODEL)
    rows = T.load_rows([os.path.join(LABELS, f) for f in sorted(os.listdir(LABELS))
                        if f.endswith(".jsonl")], len(doc["W"][0]))
    print("  [OK] biçim %s v%d · %d sınıf · %d boyut · %d satır veri"
          % (obj["format"], obj["version"], len(doc["classes"]), len(doc["W"][0]), len(rows)))

    # 1) ŞEKİL ---------------------------------------------------------------
    if doc["classes"] != T.CLASSES:
        problems.append("sınıf listesi/sırası sabit 14'lük listeden farklı")
    else:
        print("  [OK] sınıf listesi: 14 sınıf, sabit sıra")
    free = [c for c in doc["classes"] if all(r["cls"] != c for r in rows)]
    if free:
        notes.append("eğitim verisinde hiç örneği olmayan sınıflar: " + ", ".join(free))
    cs = (obj.get("meta") or {}).get("checksum")
    rc = recompute_checksum(doc)
    if cs != rc:
        problems.append("checksum uyuşmuyor: meta %s ≠ yeniden %s" % (cs, rc))
    else:
        print("  [OK] checksum: %s" % rc)

    # 1b) ÇÖKÜŞ İMZASI (regresyon) -----------------------------------------
    # 2026-10: uç bir eğitim satırı (10.000.000 px genişlik) standardizasyonu patlatınca
    # model tüm ağırlıkları sıfırlıyor ve tahminler tek sınıfa çöküyordu (top-1 %3.95).
    # Bu üç imza bir daha geçmesin diye kapıya alındı.
    wnorm_bad = [i for i, row in enumerate(doc["W"])
                 if max(abs(x) for x in row) == 0.0]
    b_all_zero = all(x == 0.0 for x in doc["b"])
    stds = doc["norm"]["std"]
    std_max = max(stds)
    clipz = float(doc.get("clipZ", 0.0))
    if wnorm_bad or b_all_zero:
        problems.append("W/b çökmüş: %d sınıfın ağırlık satırı tamamen sıfır, b hepsi sıfır=%s"
                        % (len(wnorm_bad), b_all_zero))
    else:
        print("  [OK] ağırlıklar canlı: %d sınıfın tamamı sıfırdan farklı ağırlık taşıyor"
              % len(doc["W"]))
    if std_max > 1e6:
        problems.append("std patlaması: en büyük std %.3g (>1e6) — uç satır standardizasyonu bozmuş"
                        % std_max)
    else:
        print("  [OK] standardizasyon sağlam: en büyük std %.3g (≤1e6)" % std_max)
    if clipz <= 0.0:
        problems.append("clipZ yok/sıfır — gömülü tahminde z kırpması olmadan uç girdi logitleri patlatır")
    else:
        print("  [OK] clipZ: ±%.1f (eğitim ve gömülü tahmin aynı adımı uygular)" % clipz)

    with open(os.path.join(ROOT, "spec", "style-rules.json"), encoding="utf-8") as fh:
        priors = json.load(fh).get("_stylePriors") or {}
    priors.pop("_desc", None)
    if doc.get("stylePriors") != priors:
        problems.append("stil öncülleri spec/style-rules.json ile aynı değil")
    else:
        print("  [OK] stil öncülleri spec ile birebir (%s)"
              % ", ".join(sorted(k for k in priors if k != "_desc")))

    # 2) KARARLILIK ---------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "model.json")
        cmd = [sys.executable, os.path.join(HERE, "train_class.py"), "--eval", "-o", tmp]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("yeniden eğitim başarısız:\n" + (r.stdout + r.stderr)[-1500:])
        else:
            a_bytes = open(MODEL, "rb").read()
            b_bytes = open(tmp, "rb").read()
            if a_bytes != b_bytes:
                problems.append("model.json BAYT kararlı değil: yeniden eğitim %d bayt, dosya %d bayt"
                                % (len(b_bytes), len(a_bytes)))
                for i, (x, y) in enumerate(zip(a_bytes, b_bytes)):
                    if x != y:
                        problems.append("  ilk fark %d. bayt: %r ≠ %r" % (i, x, y))
                        break
            else:
                print("  [OK] kararlılık: aynı veri + aynı komut → %d bayt BİREBİR aynı" % len(a_bytes))

    # 3) KABUL --------------------------------------------------------------
    rep = T.accuracy(rows, doc)
    ok = rep["top1"] >= TOP1_MIN and rep["top3"] >= TOP3_MIN
    line = ("  [%s] kabul: top-1 %.2f%% (≥ %.0f%%) · top-3 %.2f%% (≥ %.0f%%)"
            % ("OK" if ok else "!!", 100 * rep["top1"], 100 * TOP1_MIN,
               100 * rep["top3"], 100 * TOP3_MIN))
    print(line)
    if not ok:
        problems.append("kabul eşiği tutmadı")
    notes.append("veri kural-öğretmeni etiketi (kendi kendine damıtma): %100 bu veri için beklenen; "
                 "GERÇEK kullanıcı export'larıyla ölçüm panel verisiyle yapılacak")

    if notes and not a.quiet:
        for n in notes:
            print("  [i] " + n)
    print("-" * 74)
    if problems:
        for p in problems:
            print("  [!!] " + p)
        print("SONUÇ: BAŞARISIZ")
        return 1
    print("SONUÇ: GEÇTİ — model şekli, kararlılığı ve kabul eşiği tamam")
    return 0


if __name__ == "__main__":
    sys.exit(main())
