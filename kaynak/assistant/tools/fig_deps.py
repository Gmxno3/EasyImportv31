#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fig_decode bağımlılık bekçisi

`fig_decode/node_modules` depoda TUTULMAZ (bkz. .gitignore): fig-kiwi, kiwi-schema ve pako
npm ile yeniden üretilir. Ama eksikken hattın sessizce kırılması (MODULE_NOT_FOUND) yerine
bu bekçi eksikliği görür ve **kendisi kurar**; kurulum mümkün değilse tek satırlık net
Türkçe yönerge verir.

Kullanım (diğer araçların içinden):
    import fig_deps
    fig_deps.garanti()          # hazırsa True; eksikse npm install dener
    fig_deps.garanti(False)     # --npm-yok: kurmadan yalnız kontrol
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECODE = os.path.join(HERE, "fig_decode")
NM = os.path.join(DECODE, "node_modules")
# Decoder'ın gerçekten kullandığı üç paket (decode.mjs: pako, kiwi-schema, fig-kiwi).
GEREKLI = ("pako", "kiwi-schema", "fig-kiwi")


def eksikler():
    return [p for p in GEREKLI if not os.path.isdir(os.path.join(NM, *p.split("/")))]


def kur(sessiz=False):
    """npm install (yalnız bu klasörde, package.json + package-lock ile)."""
    if not os.path.exists(os.path.join(DECODE, "package.json")):
        return False
    if not sessiz:
        print("  [i] fig_decode bağımlılıkları kuruluyor (npm install · ~2,5 MB)…")
    r = subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--loglevel=error"],
                       cwd=DECODE, capture_output=True, text=True)
    if r.returncode != 0:
        if not sessiz:
            print("  [!!] npm install başarısız:\n%s" % (r.stderr or r.stdout)[-800:])
        return False
    return not eksikler()


def garanti(otomatik=True, sessiz=False):
    """Bağımlılıklar hazır mı? Değilse (izin varsa) kurar. False → çağıran durmalı."""
    if not eksikler():
        return True
    if otomatik and kur(sessiz=sessiz):
        if not sessiz:
            print("  [OK] fig_decode bağımlılıkları kuruldu (%s)" % ", ".join(GEREKLI))
        return True
    print("  [HATA] fig_decode bağımlılıkları eksik: %s" % ", ".join(eksikler()))
    print("         Elle kur:  cd assistant/tools/fig_decode && npm install")
    print("         (neden depoda yok: .gitignore — npm ile yeniden üretilir)")
    return False


if __name__ == "__main__":
    sys.exit(0 if garanti(otomatik="--npm-yok" not in sys.argv) else 1)
