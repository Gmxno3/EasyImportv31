#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
to_preview — `wispfree` JSON'dan PNG önizleme üretir (SIFIR bağımlılık).

Amaç: `to_wispfree.mjs` eşleyicisinin geometrisini GÖZLE doğrulamak. Figma thumbnail'ı yanına
konunca koordinat/ölçek/sıralama hatası anında görülür — Roblox çalıştırmaya gerek yok.

Bu bir renderer DEĞİL: kutu + dolgu + kontur + görsel yer tutucusu + metin çubuğu çizer.
UICorner/UIStroke/UIGradient/gölge/layout/glyph YOK. Amaç görsel birebir eşleşme değil,
**geometrik** doğrulama.

Kullanım:
    python3 to_preview.py <json...> -o <cikti-klasoru> [--olcek 0.5]
"""

import json
import os
import struct
import sys
import zlib


# ------------------------------------------------------------------ PNG yazıcı (saf stdlib)
class Tuval:
    def __init__(self, w, h, arka=(20, 22, 28)):
        self.w, self.h = w, h
        self.px = bytearray(arka * (w * h))

    def cerceve(self, x, y, r, g, b, a=1.0):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b
        else:
            self.px[i] = int(self.px[i] * (1 - a) + r * a)
            self.px[i + 1] = int(self.px[i + 1] * (1 - a) + g * a)
            self.px[i + 2] = int(self.px[i + 2] * (1 - a) + b * a)

    def dikdortgen(self, x, y, w, h, r, g, b, a=1.0):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w + 0.5)), min(self.h, int(y + h + 0.5))
        if x1 <= x0 or y1 <= y0:
            return
        # tek renkli satırı hızlı yaz
        if a >= 1.0:
            satir = bytes((r, g, b)) * (x1 - x0)
            for yy in range(y0, y1):
                i = (yy * self.w + x0) * 3
                self.px[i:i + (x1 - x0) * 3] = satir
        else:
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    self.cerceve(xx, yy, r, g, b, a)

    def cerceveCiz(self, x, y, w, h, r, g, b, kalinlik=1):
        kal = max(1, int(kalinlik))
        self.dikdortgen(x, y, w, kal, r, g, b)
        self.dikdortgen(x, y + h - kal, w, kal, r, g, b)
        self.dikdortgen(x, y, kal, h, r, g, b)
        self.dikdortgen(x + w - kal, y, kal, h, r, g, b)

    def png(self, yol):
        ham = bytearray()
        for yy in range(self.h):
            ham.append(0)
            ham += self.px[yy * self.w * 3:(yy + 1) * self.w * 3]

        def parca(tip, veri):
            c = struct.pack(">I", len(veri)) + tip + veri
            return c + struct.pack(">I", zlib.crc32(tip + veri) & 0xFFFFFFFF)

        open(yol, "wb").write(
            b"\x89PNG\r\n\x1a\n"
            + parca(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
            + parca(b"IDAT", zlib.compress(bytes(ham), 6))
            + parca(b"IEND", b"")
        )


# ------------------------------------------------------------------ çizim
def sayi(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def solid_renk(f):
    if not isinstance(f, dict) or f.get("type") != "SOLID":
        return None
    c = f.get("color") or {}
    a = sayi(f.get("opacity", 1), 1.0)
    return int(c.get("r", 0)), int(c.get("g", 0)), int(c.get("b", 0)), max(0.0, min(1.0, a))


def ciz(item, t, ox, oy, olcek, derinlik=0, sinir=40):
    """ox/oy: ebeveynin tuval üzerindeki köşesi (relatif konumları mutlaklaştırır)."""
    if not isinstance(item, dict) or derinlik > sinir:
        return 0
    x = ox + sayi(item.get("x")) * olcek
    y = oy + sayi(item.get("y")) * olcek
    w = sayi(item.get("w")) * olcek
    h = sayi(item.get("h")) * olcek
    op = max(0.0, min(1.0, sayi(item.get("opacity", 1), 1.0)))
    n = 0
    if w < 0.6 or h < 0.6:
        return 0

    fills = item.get("fills") or []
    if isinstance(fills, dict):
        fills = [fills]
    renk = solid_renk(fills[-1]) if fills else None

    if item.get("kind") == "text":
        metin = str((item.get("text") or {}).get("characters") or "")
        if metin.strip():
            # metni okunabilir kılmak için çubuk + metin uzunluğuna göre genişlik
            fs = max(2.0, sayi((item.get("text") or {}).get("fontSize"), 16) * olcek)
            c = (item.get("text") or {}).get("color") or {}
            col = (int(c.get("r", 255)), int(c.get("g", 255)), int(c.get("b", 255)), op)
            uzunluk = min(w, max(fs * 0.45 * len(metin), fs))
            t.dikdortgen(x, y, uzunluk, max(1.0, fs * 0.62), col[0], col[1], col[2], col[3])
            n += 1
        return n

    if item.get("image"):
        t.dikdortgen(x, y, w, h, 42, 62, 96, 0.9 * op)
        t.cerceveCiz(x, y, w, h, 90, 150, 210)
        n += 1
    elif renk:
        t.dikdortgen(x, y, w, h, renk[0], renk[1], renk[2], renk[3] * op)
        n += 1

    st = item.get("stroke")
    if not st and item.get("strokes"):
        st = item["strokes"][-1]
    if isinstance(st, dict):
        c = st.get("color") or {}
        t.cerceveCiz(x, y, w, h, int(c.get("r", 0)), int(c.get("g", 0)), int(c.get("b", 0)),
                     max(1.0, sayi(st.get("weight"), 1) * olcek))

    for ch in item.get("children") or []:
        n += ciz(ch, t, x, y, olcek, derinlik + 1, sinir)
    return n


def main():
    a = sys.argv[1:]
    if "-o" not in a:
        print(__doc__)
        return 1
    oi = a.index("-o")
    outdir = a[oi + 1]
    olcek = 0.5
    if "--olcek" in a:
        olcek = float(a[a.index("--olcek") + 1])
    girdiler = [v for i, v in enumerate(a) if i not in (oi, oi + 1) and (i == 0 or a[i - 1] != "--olcek") and v != "--olcek"]
    girdiler = [g for g in girdiler if g.endswith(".json")]
    os.makedirs(outdir, exist_ok=True)

    for p in girdiler:
        doc = json.load(open(p, encoding="utf-8"))
        W = int(sayi(doc.get("width"), 800) * olcek)
        H = int(sayi(doc.get("height"), 600) * olcek)
        t = Tuval(max(1, W), max(1, H))
        n = ciz(doc.get("root") or {}, t, 0, 0, olcek)
        ad = os.path.splitext(os.path.basename(p))[0].replace(" ", "_") + ".png"
        t.png(os.path.join(outdir, ad))
        print("  %-52s %3d öğe" % (ad, n))


if __name__ == "__main__":
    sys.exit(main())
