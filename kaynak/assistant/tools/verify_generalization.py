#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3c — GENELLEME KAPISI (verify_generalization)

NEDEN AYRI BİR KAPI?
  `train_class.py --loo` katları **export** (alt-frame) düzeyinde ayırır. 28 export'un 18'i
  aynı 10 `.fig` dosyasının alt-frame'leridir → kardeş katmanlar eğitimde kalır, ölçüm iyimser
  çıkar (export-LOO %95.67). Bu kapı katları **tasarım dosyası** düzeyinde ayırır: dosyanın
  TAMAMI (o dosyanın bütün export'ları) dışta kalır. Kardeş sızıntısı olmadığı için dürüst.

İKİ ÖLÇÜM:
  1. tüm katmanlar           — genel sağlamlık
  2. JENERİK isimli katmanlar — ÜRETİMDE MODELİN GERÇEKTEN KONUŞTUĞU altküme.
     `Assist.decide` (roblox-studio-plugin/EasyImportStudioPlugin.lua) ad/etiket sinyali olan
     katmana dokunmaz (ASSIST_SIGNAL_TAGS) → model yalnızca "Frame 12", "Rectangle 8", "Group 11"
     gibi jenerik isimli katmanlarda karar verir. Bu yüzden asıl kabul ölçütü budur:
     **PLAN §A3: etiketsiz katmanlarda ≥ %85 top-1.**

DÜRÜSTLÜK NOTU: gerçek export'ların etiketi `src=rule-teacher` (kural motorunun kendi kararı).
Bu ölçüm "insan gerçeği" değil, **öğretmenle uyuşma**dır. İnsan etiketli ilk gerçek veri
geldiğinde bu kapı aynı şekilde çalışır; tek fark etiketin kaynağı olur.

Kullanım:
    python3 tools/verify_generalization.py               # 10 gerçek dosya katı (~6 dk)
    python3 tools/verify_generalization.py --folds 3     # hızlı duman testi (~2 dk)
    python3 tools/verify_generalization.py --all         # sentetik dosyalar dâhil tüm katlar (~10 dk)
Çıkış: 0 = geçti, 1 = başarısız
"""
import argparse
import collections
import json
import math
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import feature_index          # noqa: E402
import train_class as T       # noqa: E402

LABELS = os.path.join(ROOT, "datasets", "labels")
TOP1_MIN = 0.85               # PLAN §A3 — etiketsiz katmanlarda top-1 tabanı

# Kural motorunun isimden sınıf çıkaramadığı adlar (üretimde model burada konuşur).
GENEL = re.compile(r"^(Frame|Rectangle|Group|Vector|Ellipse|Union|Star|Polygon|Line"
                   r"|Component|Slice|Mask)\s*\d*$")

# Gerçek tasarım dosyaları (designs/*.fig → export öneki). Sentetikler dışta.
GERCEK = {"Ang3lzHUD (1)", "AnimeHUD (1)", "FlashyAnimeUI", "Indexx (2)", "OS1File", "OS2File",
          "RebirthUI", "Slots Anime UI (1)", "stud frame templates", "wtever (1)"}


def dosya_anahtari(row):
    """Satırın geldiği tasarım dosyası: 'X__Alt' → 'X' · sentetik 'StudMarket_x' → 'StudMarket'."""
    e = row.get("export") or "?"
    if "__" in e:
        return e.split("__")[0]
    return e.split("_")[0] if "_" in e else e


def jenerik(row):
    return bool(GENEL.match((row.get("clean") or row.get("name") or "").strip()))


def egit(rows, dim):
    t = T.train(rows, dim, T.DEFAULTS["epochs"], T.DEFAULTS["lr"], T.DEFAULTS["momentum"],
                T.DEFAULTS["l2"], T.DEFAULTS["patience"], T.DEFAULTS["val_frac"],
                T.DEFAULTS["seed"], log=False)
    return {"classes": T.CLASSES, "W": t["W"], "b": t["b"],
            "norm": {"mean": t["mean"], "std": t["std"]},
            "stylePriors": {}, "clipZ": T.CLIP_Z}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, default=0, help="ilk N kat (varsayılan: hepsi)")
    ap.add_argument("--all", action="store_true", help="sentetik dosyalar da kat olsun")
    a = ap.parse_args()

    spec = feature_index.load_spec()
    dim = spec["dim"]
    T.name2index(spec)
    paths = [os.path.join(LABELS, f) for f in sorted(os.listdir(LABELS)) if f.endswith(".jsonl")]
    rows = T.load_rows(paths, dim)

    gruplar = collections.defaultdict(list)
    for r in rows:
        gruplar[dosya_anahtari(r)].append(r)
    if not a.all:
        gruplar = collections.OrderedDict((k, v) for k, v in gruplar.items() if k in GERCEK)
    adlar = sorted(gruplar)
    if a.folds:
        adlar = adlar[:a.folds]

    print("=" * 74)
    print("GENELLEME KAPISI (A3c) — kat: TASARIM DOSYASI (kardeş sızıntısı yok)")
    print("=" * 74)
    print("  veri       : %d satır · %d dosya · boyut %d" % (len(rows), len(gruplar), dim))
    print("  katlar     : %d (%s)" % (len(adlar), "gerçek dosyalar" if not a.all else "tümü"))
    print("  jenerik    : %d satır (modelin üretimde konuştuğu altküme)"
          % sum(1 for r in rows if jenerik(r)))

    tum, jen, taban, karis = [], [], [], collections.Counter()
    t0 = time.time()
    for i, ad in enumerate(adlar, 1):
        disarida = [r for r in rows if dosya_anahtari(r) != ad]
        tutulan = gruplar[ad]
        m = egit(disarida, dim)
        sa = T.accuracy(tutulan, m)
        tum.append(sa["top1"])
        g = [r for r in tutulan if jenerik(r)]
        gj = "  -  "
        if g:
            sg = T.accuracy(g, m)
            jen.append(sg["top1"])
            maj = collections.Counter(r["cls"] for r in disarida).most_common(1)[0][0]
            taban.append(sum(1 for r in g if r["cls"] == maj) / len(g))
            for r in g:
                p = T.predict(m, r)
                karis[(r["cls"], p["cls"])] += 1
            gj = "%6.2f%% (%d)" % (100 * sg["top1"], len(g))
        print("  [%2d/%d · dışta %-26s] tümü %6.2f%% · jenerik %s · %.0f sn"
              % (i, len(adlar), ad[:26], 100 * sa["top1"], gj, time.time() - t0))

    ort_tum = sum(tum) / len(tum)
    print("-" * 74)
    print("  dosya-LOO tüm katmanlar : top-1 %.2f%% (%d kat)" % (100 * ort_tum, len(tum)))
    if jen:
        ort_jen = sum(jen) / len(jen)
        ort_tab = sum(taban) / len(taban)
        print("  dosya-LOO jenerik       : top-1 %.2f%% · çoğunluk tabanı %.2f%% (%+.2f puan)"
              % (100 * ort_jen, 100 * ort_tab, 100 * (ort_jen - ort_tab)))
        en_iyi = karis.most_common(3)
        print("  jenerik karışma (ilk 3) : %s"
              % ", ".join("%s→%s×%d" % (x[0], x[1], n) for x, n in en_iyi))
        ok = ort_jen >= TOP1_MIN
        print("  [%s] kabul (PLAN §A3): jenerik top-1 %.2f%% (≥ %.0f%%)"
              % ("OK" if ok else "!!", 100 * ort_jen, 100 * TOP1_MIN))
    else:
        ok = False
        print("  [!!] jenerik katman bulunamadı — katlar yanlış seçilmiş")
    print("-" * 74)
    print("  [i] etiket kaynağı kural-öğretmen → bu ölçüm öğretmenle UYUŞMA; insan etiketi gelince özdeş çalışır")
    print("  [i] süre %.1f dk · deterministik (aynı veri + aynı komut = aynı sayı)"
          % ((time.time() - t0) / 60))
    if ok:
        print("SONUÇ: GEÇTİ — model görülmemiş TASARIM DOSYASINDA da kararını koruyor")
        return 0
    print("SONUÇ: BAŞARISIZ — jenerik katmanlarda top-1 eşiğin altında")
    return 1


if __name__ == "__main__":
    sys.exit(main())
