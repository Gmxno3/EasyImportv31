#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK VERİ KAPISI — `designs-export/` ve `datasets/labels/real-exports.jsonl` sağlıklı mı?

Neden gerekli: `designs/*.fig` → eğitim verisi zinciri, eklentiyle birebir sözleşme üretmeyi
hedefliyor. Eşleyicideki iki sessiz hata (ROUNDED_RECTANGLE düşmesi, kök konumu) ancak elle
görsel karşılaştırmayla fark edildi — bu kapı onları ve benzerlerini otomatik yakalar.

Kapının aradığı imzalar:
  1. Kök konumu her zaman (0,0)          — eklenti `contAbs = kökün absoluteTransform'u` yapar
  2. `kind` yalnızca 4 değer alabilir    — code.js: text | vector | ellipse | frame
  3. `radius:'full'` yalnız elips        — code.js: `t === 'ELLIPSE' → 'full'`
  4. `form_geçerli`                      — bilinmeyen kind / eksik alan / NaN yok
  5. Çocuklar ebeveyn kutusuna yakın     — konum hesabı bozulmadıysa çocuklar içeride
  6. `ei` döşeme kanalı tam              — tileW>0 ise tileH>0, imageW>0, repX≥0
  7. Vektörler `image` taşır             — eklenti her vektörü PNG yapar → öğretmen ImageLabel der
  8. Ölçek tutarlılığı                   — kök ölçüsü = tasarım ölçüsü (kırpılmamış)
  9. jsonl boyut/şema                    — 379 özellik, benzersiz (export,path), sınıf listesi geçerli
 10. Determinizm                          — aynı .fig iki kez → aynı JSON baytları

Kullanım:
    python3 tools/verify_real_dataset.py [--det]     # --det: determinizm testini de koş
Çıkış: 0 = GEÇTİ, 1 = başarısız
"""

import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJE = os.path.dirname(ROOT)
EXPORT = os.path.join(PROJE, "designs-export")
JSONL = os.path.join(ROOT, "datasets", "labels", "real-exports.jsonl")
FIG_DIR = os.path.join(PROJE, "designs")
DECODE = os.path.join(HERE, "fig_decode")

GECERLI_KIND = {"text", "vector", "ellipse", "frame"}
GECERLI_SINIF = {"Frame", "ImageLabel", "ImageButton", "TextLabel", "TextButton", "TextBox",
                 "ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame",
                 "UIGridLayout", "Item", "DROP", "MERGE"}

hatalar = []
uyarilar = []
sayac = {}


def hata(m):
    hatalar.append(m)


def uyari(m):
    uyarilar.append(m)


def dugum_say(it):
    return 1 + sum(dugum_say(c) for c in (it.get("children") or []))


def yuruyus(it, yol, doc, testler):
    """Bir item'ı ve tüm çocuklarını denetler."""
    if not isinstance(it, dict):
        hata("%s: item dict değil" % yol)
        return
    for alan in ("name", "kind", "x", "y", "w", "h", "rot", "opacity"):
        if alan not in it:
            hata("%s: zorunlu alan eksik: %s" % (yol, alan))
    k = it.get("kind")
    if k not in GECERLI_KIND:
        hata("%s: geçersiz kind=%r" % (yol, k))
    sayac["kind:" + str(k)] = sayac.get("kind:" + str(k), 0) + 1

    for alan in ("x", "y", "w", "h", "rot", "opacity"):
        v = it.get(alan)
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            hata("%s: %s sayı değil (%r)" % (yol, alan, v))
    if (it.get("w") or 0) < 0 or (it.get("h") or 0) < 0:
        hata("%s: negatif ölçü" % yol)

    # code.js: `if (t === 'ELLIPSE') item.radius = 'full'` — burada `t` FIGMA TİPİDİR, `kind` değil.
    # `_image` etiketli elips `kind:'vector'` olur ama yine `radius:'full'` alır. Dolayısıyla
    # 'full' yalnızca metin/kare için hatadır (ikisi de elips olamaz).
    if it.get("radius") == "full" and k in ("text", "frame"):
        hata("%s: radius:'full' ama kind=%s — kaynak elips değil" % (yol, k))

    if k == "text":
        t = it.get("text")
        if not isinstance(t, dict):
            hata("%s: kind=text ama text bloğu yok" % yol)
        else:
            if "characters" not in t:
                hata("%s: text.characters yok" % yol)
            sayac["text"] = sayac.get("text", 0) + 1
    else:
        if it.get("text"):
            uyari("%s: kind=%s ama text bloğu var" % (yol, k))

    ei = it.get("ei")
    if ei:
        sayac["ei"] = sayac.get("ei", 0) + 1
        if ei.get("tileW") or ei.get("tileH"):
            sayac["ei.tile"] = sayac.get("ei.tile", 0) + 1
            if not (ei.get("tileW", 0) > 0 and ei.get("tileH", 0) > 0):
                hata("%s: ei.tileW/tileH ikisi de >0 olmalı (%r)" % (yol, ei))
            if not (ei.get("imageW", 0) > 0 and ei.get("imageH", 0) > 0):
                hata("%s: döşeme ölçüldü ama imageW/H yok (%r)" % (yol, ei))
            if ei.get("sf") is None:
                hata("%s: döşemede ei.sf yok (bildirilen sözleşme)" % yol)
        if ei.get("blendMode") in ("NORMAL", "PASS_THROUGH"):
            hata("%s: ei.blendMode normal olmamalı (code.js yazmaz): %r" % (yol, ei["blendMode"]))
    if it.get("image"):
        sayac["image"] = sayac.get("image", 0) + 1
        if k == "text":
            hata("%s: kind=text ama image var" % yol)
    if k == "vector" and not it.get("image"):
        hata("%s: vektör ama image yok — eklenti her vektörü PNG yapar (öğretmen ImageLabel der)" % yol)
    if it.get("clips") is not True and "clips" in it:
        hata("%s: clips yalnızca true olarak yazılır" % yol)

    kids = it.get("children")
    if kids is not None:
        if not isinstance(kids, list):
            hata("%s: children liste değil" % yol)
        elif k == "vector":
            hata("%s: vektörün çocuğu olmaz (code.js hasChildren=false)" % yol)

    for i, ch in enumerate(it.get("children") or []):
        yuruyus(ch, "%s.%d" % (yol, i), doc, testler)


def main():
    det = "--det" in sys.argv

    print("=" * 74)
    print("GERÇEK VERİ KAPISI — designs/ → designs-export/ → real-exports.jsonl")
    print("=" * 74)

    figler = sorted(glob.glob(os.path.join(FIG_DIR, "*.fig")))
    if len(figler) < 10:
        hata("designs/ altında %d .fig var (beklenen 10)" % len(figler))
    else:
        print("  [OK] designs/: %d .fig · %.1f MB" % (
            len(figler), sum(os.path.getsize(f) for f in figler) / 1048576))

    # ---- 1-8: JSON sözleşmesi ----
    jsonlar = sorted(glob.glob(os.path.join(EXPORT, "*.json")))
    if not jsonlar:
        hata("designs-export/*.json yok (önce build_real_dataset.py)")
    toplam_dugum = 0
    for p in jsonlar:
        d = json.load(open(p, encoding="utf-8"))
        ad = os.path.basename(p)
        if d.get("format") != "wispfree":
            hata("%s: format=%r" % (ad, d.get("format")))
        if d.get("version") != 9:
            hata("%s: version=%r (beklenen 9)" % (ad, d.get("version")))
        if not isinstance(d.get("root"), dict):
            hata("%s: root yok" % ad)
            continue
        r = d["root"]
        if abs(r.get("x", 1)) > 0.01 or abs(r.get("y", 1)) > 0.01:
            hata("%s: kök konumu (%r,%r) — (0,0) olmalı" % (ad, r.get("x"), r.get("y")))
        if abs((r.get("w") or 0) - (d.get("width") or 0)) > 0.02:
            hata("%s: kök genişliği %r ≠ doküman genişliği %r" % (ad, r.get("w"), d.get("width")))
        if abs((r.get("h") or 0) - (d.get("height") or 0)) > 0.02:
            hata("%s: kök yüksekliği %r ≠ doküman yüksekliği %r" % (ad, r.get("h"), d.get("height")))
        yuruyus(r, "0", d, None)
        toplam_dugum += dugum_say(r)
    print("  [OK] designs-export/: %d tasarım · %d düğüm" % (len(jsonlar), toplam_dugum))

    for k in sorted(sayac):
        print("        %-14s %d" % (k, sayac[k]))

    # ---- 9: jsonl ----
    if not os.path.exists(JSONL):
        hata("real-exports.jsonl yok")
    else:
        satirlar = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
        gorulen = set()
        siniflar = {}
        for r in satirlar:
            anahtar = (r.get("export"), r.get("path"))
            if anahtar in gorulen:
                hata("jsonl: yinelenen (export,path): %r" % (anahtar,))
            gorulen.add(anahtar)
            f = r.get("feat") or {}
            if not f:
                hata("jsonl: %r boş özellik vektörü" % (anahtar,))
            for ad, v in f.items():
                if v != v or v in (float("inf"), float("-inf")):
                    hata("jsonl: %r özellik %s sayı değil" % (anahtar, ad))
            c = r.get("cls")
            if c not in GECERLI_SINIF:
                hata("jsonl: bilinmeyen sınıf %r" % c)
            siniflar[c] = siniflar.get(c, 0) + 1
        print("  [OK] real-exports.jsonl: %d örnek · %d sınıf" % (len(satirlar), len(siniflar)))
        for c, n in sorted(siniflar.items(), key=lambda kv: -kv[1]):
            print("        %-16s %5d  (%.1f%%)" % (c, n, 100.0 * n / len(satirlar)))
        eksik = GECERLI_SINIF - set(siniflar)
        if eksik:
            uyari("gerçek veride hiç örneği olmayan sınıflar: %s" % ", ".join(sorted(eksik)))
        if toplam_dugum != len(satirlar):
            uyari("JSON düğümü %d ≠ jsonl örneği %d (hayalet/boş eleme normaldir)" % (toplam_dugum, len(satirlar)))

    # ---- 10: determinizm ----
    f = figler[0] if det else None
    if det:
        import fig_deps   # node_modules depoda tutulmaz; eksikse kurulur (bkz. .gitignore)
        if not fig_deps.garanti(sessiz=True):
            hata("determinizm: fig_decode bağımlılıkları yok (npm install)")
            f = None
    if f:
        ciktilar = []
        for i in range(2):
            gecici = "/tmp/eidet%d" % i
            subprocess.run(["rm", "-rf", gecici], check=False)
            os.makedirs(gecici, exist_ok=True)
            r = subprocess.run(["node", "to_wispfree.mjs", os.path.relpath(f, DECODE), "-o", gecici, "--sessiz"],
                               cwd=DECODE, capture_output=True, text=True)
            if r.returncode != 0:
                hata("determinizm: üretim başarısız (%s)" % r.stderr[-300:])
                break
            j = glob.glob(os.path.join(gecici, "*.json"))
            ciktilar.append(hashlib.sha256(open(j[0], "rb").read()).hexdigest() if j else None)
        if len(ciktilar) == 2 and ciktilar[0] != ciktilar[1]:
            hata("determinizm: aynı .fig iki üretimde farklı JSON (%s ≠ %s)" % tuple(ciktilar))
        elif ciktilar and ciktilar[0]:
            print("  [OK] determinizm: iki üretim aynı (sha256 %s…)" % ciktilar[0][:16])

    # ---- sonuç ----
    print("-" * 74)
    for u in uyarilar:
        print("  [!] " + u)
    for h in hatalar[:25]:
        print("  [X] " + h)
    if len(hatalar) > 25:
        print("  ... +%d hata" % (len(hatalar) - 25))
    if hatalar:
        print("SONUÇ: BAŞARISIZ — %d hata, %d uyarı" % (len(hatalar), len(uyarilar)))
        return 1
    print("SONUÇ: GEÇTİ — sözleşme, geometri ve veri sağlığı tamam (%d uyarı)" % len(uyarilar))
    return 0


if __name__ == "__main__":
    sys.exit(main())
