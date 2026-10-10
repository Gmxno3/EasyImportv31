#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EKSTRA KÜTÜPHANE (v22) — ikon paketinden efekt simgeleri üretir.

Girdi : core-icon-pack zip'i (Icons New2/<Kategori>/<Ad>/<64px|64w>/*.png)
Çıktı :
  • kutuphane/EkstraKutuphane/<kimlik>.png  — Asset Manager'a TOPLU yüklenecek (dosya adı = Decal adı)
  • kutuphane/ekstra-kutuphane.json         — dizin (kimlik, kategori, ad, varyant, geniş mi)
  • assistant/runtime/js/ei-ekstra.js       — Figma panelinin gömülü dizini ve küçük resimleri (64 px)

Kimlik: ikon_<kategori>_<ad>_<varyant>[_w]   (ASCII, küçük harf, kararlı)
Kullanım: python3 tools/build_ekstra.py <zip>
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
import base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # work/
LIB_DIR = os.path.join(ROOT, "kutuphane", "EkstraKutuphane")
INDEX = os.path.join(ROOT, "kutuphane", "ekstra-kutuphane.json")
RUNTIME = os.path.join(ROOT, "assistant", "runtime", "js", "ei-ekstra.js")
SIZES = {"256px": False, "256w": True, "64px": False, "64w": True}  # klasör → geniş mi (256 tercih; yoksa 64)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("kullanım: python3 tools/build_ekstra.py <icon-pack.zip>")
    zpath = sys.argv[1]
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(zpath) as z:
        z.extractall(tmp)
    base = None
    for dp, dn, fn in os.walk(tmp):
        if os.path.basename(dp) == "Icons New2":
            base = dp
            break
    if not base:
        raise SystemExit("zip içinde 'Icons New2' klasörü yok")

    entries, thumbs, seen = [], {}, set()
    # Her simge için en yüksek çözünürlük: 256 varsa o, yoksa 64. (Kimlikler iki boyutta da aynı.)
    best = {}
    ident_by_key = {}
    for dp, dn, fn in os.walk(base):
        for f in sorted(fn):
            if not f.lower().endswith(".png"):
                continue
            rel = os.path.relpath(dp, base).split(os.sep)
            if len(rel) != 3 or rel[2] not in SIZES:
                continue                                  # yalnız <Kategori>/<Ad>/<64px|64w>
            cat, name, folder = rel
            core = re.sub(r"\s*\d+px\.png$", "", f, flags=re.I)   # boyut ve uzantıyı ayır (256px / 64px ortak)
            wide = SIZES[folder]
            stem = slug(core)
            if not stem.startswith(slug(name)):          # ad zaten varyant adında yoksa öne ekle
                stem = slug(name) + "_" + stem
            key = (cat, name, core, wide)                 # aynı simgenin 64px ve 256px sürümü AYNI kimliği paylaşır
            if key in ident_by_key:
                ident = ident_by_key[key]
            else:
                ident = "ikon_%s_%s%s" % (slug(cat), stem, "_w" if wide else "")
                n = 2
                while ident in seen:                      # gerçekten farklı iki simge aynı adı alırsa sıra numarası
                    ident = "ikon_%s_%s_%d%s" % (slug(cat), stem, n, "_w" if wide else "")
                    n += 1
                seen.add(ident)
                ident_by_key[key] = ident
            px = int(folder[:folder.index("p") if "p" in folder else folder.index("w")]) if folder[0].isdigit() else 0
            prev = best.get(ident)
            if prev is None or px > prev[0]:
                best[ident] = (px, os.path.join(dp, f), core, cat, name, wide)

    from PIL import Image
    os.makedirs(LIB_DIR, exist_ok=True)
    for ident, (px, path, core, cat, name, wide) in sorted(best.items()):
        entries.append({"id": ident, "cat": cat, "name": name, "label": core,
                        "wide": wide, "file": ident + ".png", "src": path, "px": px})
        shutil.copyfile(path, os.path.join(LIB_DIR, ident + ".png"))
        im = Image.open(path).convert("RGBA")
        im.thumbnail((64, 64), Image.LANCZOS)                      # önizleme: 256'dan düzgün küçültme
        buf = __import__("io").BytesIO(); im.save(buf, "WEBP", quality=88, method=6)   # saydam, küçük (önizleme)
        thumbs[ident] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    entries.sort(key=lambda e: e["id"])
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, "w", encoding="utf-8") as fh:
        json.dump({"count": len(entries), "items": [{k: v for k, v in e.items() if k != "src"} for e in entries]},
                  fh, ensure_ascii=False, indent=1)
    index_js = [{k: v for k, v in e.items() if k not in ("src", "file")} for e in entries]
    with open(RUNTIME, "w", encoding="utf-8") as fh:
        fh.write("// EKSTRA KÜTÜPHANE (otomatik üretildi: tools/build_ekstra.py) — ikon dizini + 64 px küçük resimler.\n")
        fh.write("var EKSTRA_INDEX = " + json.dumps(index_js, ensure_ascii=False, separators=(",", ":")) + ";\n")
        fh.write("var EKSTRA_THUMBS = " + json.dumps(thumbs, separators=(",", ":")) + ";\n")
    shutil.rmtree(tmp, ignore_errors=True)
    cats = {}
    for e in entries:
        cats[e["cat"]] = cats.get(e["cat"], 0) + 1
    print("[OK] %d simge · kategoriler: %s" % (len(entries), ", ".join("%s %d" % kv for kv in sorted(cats.items()))))
    print("[OK] kütüphane klasörü: %s" % LIB_DIR)


if __name__ == "__main__":
    main()
