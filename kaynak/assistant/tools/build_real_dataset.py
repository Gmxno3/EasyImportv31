#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK VERİ HATTI — `designs/*.fig`  →  eğitim verisi (jsonl)

Neden var: `assistant/DURUM.md` §6 "gerçek veri eksikliği" diyordu. Bu betik `designs/`
klasöründeki gerçek Figma dosyalarından, Figma'yı hiç açmadan, eğitim verisini üretir ve
`datasets/labels/real-exports.jsonl` olarak yazar. Tek komut, deterministik.

Zincir:
    designs/*.fig
      │  assistant/tools/fig_decode/to_wispfree.mjs   (kiwi → wispfree v9 sözleşmesi)
      ▼  designs-export/*.json + designs-export/images/*.png
      │  assistant/tools/ingest.py                    (RAW + öğretmen etiketi + 379 özellik)
      ▼  datasets/labels/real-exports.jsonl
      │  assistant/tools/train_class.py               (softmax, LOO)
      ▼  model/model.json → export_model.py → .lua/.js → build_rbxmx.py → .rbxmx

Kullanım:
    python3 tools/build_real_dataset.py                 # üret (önbellek varsa atlar)
    python3 tools/build_real_dataset.py --zorla         # baştan üret
    python3 tools/build_real_dataset.py --sadece-veri   # export'ları üret, jsonl'i yazma

Ön koşul: `tools/fig_decode/` içinde `npm install` bir kez çalıştırılmış olmalı.
Çıkış: 0 = başarılı
"""

import os
import glob
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # assistant/
PROJE = os.path.dirname(ROOT)                # depo kökü
FIG_DIR = os.path.join(PROJE, "designs")
OUT_DIR = os.path.join(PROJE, "designs-export")
JSONL = os.path.join(ROOT, "datasets", "labels", "real-exports.jsonl")
DECODE_DIR = os.path.join(HERE, "fig_decode")


def calistir(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:] if r.stdout else "", file=sys.stderr)
        print(r.stderr[-2000:] if r.stderr else "", file=sys.stderr)
        raise SystemExit("[HATA] komut başarısız: %s" % " ".join(map(str, cmd)))
    return r.stdout


def main():
    args = sys.argv[1:]
    zorla = "--zorla" in args
    sadece_veri = "--sadece-veri" in args

    figler = sorted(glob.glob(os.path.join(FIG_DIR, "*.fig")))
    if not figler:
        print("[HATA] designs/*.fig bulunamadı: %s" % FIG_DIR)
        return 1
    import fig_deps  # bağımlılık bekçisi: eksikse kendisi kurar (npm install)
    if not fig_deps.garanti(otomatik="--npm-yok" not in args):
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)

    print("=" * 70)
    print("GERÇEK VERİ HATTI — %d dosya" % len(figler))
    print("=" * 70)

    # 1) kiwi → wispfree sözleşmesi
    for f in figler:
        ad = os.path.basename(f)
        cikti = os.path.join(OUT_DIR, os.path.splitext(ad)[0].replace(".fig", "") + "*")
        if not zorla and glob.glob(cikti + ".json"):
            print("  [=] %-42s (önbellek)" % ad)
            continue
        out = calistir(["node", "to_wispfree.mjs", os.path.relpath(f, DECODE_DIR), "-o", os.path.relpath(OUT_DIR, DECODE_DIR), "--sessiz"],
                       cwd=DECODE_DIR)
        print("  [OK] %-42s" % ad)

    jsonlar = sorted(glob.glob(os.path.join(OUT_DIR, "*.json")))
    print("  [i] %d tasarım JSON'u · %d görsel" % (
        len(jsonlar), len(glob.glob(os.path.join(OUT_DIR, "images", "*.png")))))

    if sadece_veri:
        return 0

    # 2) ingest → jsonl
    print("-" * 70)
    out = calistir([sys.executable, os.path.join(HERE, "ingest.py")] + jsonlar + ["-o", JSONL], cwd=ROOT)
    for satir in out.strip().splitlines()[-6:]:
        print("  " + satir)

    # 3) özet
    n = sum(1 for _ in open(JSONL, encoding="utf-8"))
    print("-" * 70)
    print("SONUÇ: %d eğitim örneği → %s" % (n, os.path.relpath(JSONL, PROJE)))
    print("Sonraki: python3 tools/train_class.py datasets/labels/bootstrap.jsonl datasets/labels/real-exports.jsonl -o model/model.json --eval --loo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
