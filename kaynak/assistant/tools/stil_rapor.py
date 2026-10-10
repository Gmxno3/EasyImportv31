#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STIL RAPORU — A12 kalibrasyon aracı (etiket geldikçe eşikleri gerçek veriyle ayarlama)

    python3 tools/stil_rapor.py
        → sinyal tablosu (etiket yokken: ölçüm modu)

    python3 tools/stil_rapor.py --etiketler designs-export/_rapor/stil-etiketleri.json
        → uyuşma + karışıklık matrisi + anime/cartoon/margin eşik taraması

Etiket dosyası biçimi (bkz. STIL-SORULARI.md):

    { "<fig dosya adı uzantısız>": "stud|anime|cartoon|belirsiz|karışık", ... }

Örnek: { "AnimeHUD (1)": "anime", "stud frame templates": "stud", "OS1File": "belirsiz" }

Çıktı: designs-export/_rapor/stil-rapor.md

Kısıt (karar günlüğü): tarama YALNIZCA anime/cartoon/margin eşiklerini dener.
Stud kuralı gevşetilmez. Rapor SONUÇ-only'dir — eşik uygulaması ayrı adımdır
(uygula zinciri: ei-style.js + EIStyle.lua + spec/style-rules.json → verify_style →
verify_generalization → verify_real_run → build_rbxmx.py --check).
"""
import argparse
import itertools
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPORTS = os.path.join(ROOT, "..", "designs-export")
DESIGNS = os.path.join(ROOT, "..", "designs")
RAPOR = os.path.join(EXPORTS, "_rapor", "stil-rapor.md")

# Sinyal tablosunda gösterilecek anahtar sinyaller
ANAHTAR_SINYALLER = [
    ("lightingIndex", "ışık"), ("detailIndex", "detay"), ("darknessIndex", "koyuluk"),
    ("textureIndex", "doku"), ("effectDensity", "efekt"), ("gradientRate", "gradyan"),
    ("hueDiversity", "renkçeşit"), ("mutedBaseRate", "sönükbaz"),
    ("reuseRate", "dokutroeid"), ("nNodes", "katman"),
]

# Taranacak eşikler (yalnızca anime/cartoon/margin — stud ölçüm-only)
GRID = {
    "animeLightMin": [0.30, 0.40, 0.50, 0.55],
    "animeDetailMin": [0.30, 0.40, 0.50, 0.55],
    "animeDarkMin": [0.30, 0.40, 0.50],
    "cartoonTextureMin": [0.20, 0.30, 0.40],
    "cartoonEffectMax": [0.40, 0.60, 0.80],
    "cartoonDetailMax": [0.35, 0.50, 0.65],
    "marginMin": [0.05, 0.12, 0.20],
}


def dump(grid_path=None):
    # Not: yardımcı .cjs uzantılı — Node'un ESM tespitinin (yorumlardaki "export'"
    # gibi sözcükler) .js dosyasını ESM sanmasını önlemek için.
    cmd = ["node", os.path.join(HERE, "stil_dump.cjs"), EXPORTS]
    if grid_path:
        cmd += ["--grid", grid_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit(1)
    return json.loads(r.stdout)


def design_of(export_name, basenames):
    """'{fig}__{node}' → fig dosya adı (uzantısız). En uzun eşleşen önek kazanır."""
    for b in sorted(basenames, key=len, reverse=True):
        if export_name.startswith(b + "__"):
            return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etiketler", help="design→style JSON dosyası")
    args = ap.parse_args()

    basenames = sorted(
        f[:-4] for f in os.listdir(DESIGNS) if f.endswith(".fig")
    ) if os.path.isdir(DESIGNS) else []

    data = dump()
    exports = data["exports"]

    etiketler = {}
    if args.etiketler:
        etiketler = json.load(open(args.etiketler, encoding="utf-8"))
        tanimsiz = sorted(set(etiketler) - set(basenames))
        if tanimsiz:
            print("[uyarı] etikette olup designs/ içinde olmayan adlar (atlanıyor): %s"
                  % ", ".join(tanimsiz))
            for t in tanimsiz:
                etiketler.pop(t, None)

    satirlar = []
    for e in exports:
        d = design_of(e["export"], basenames)
        e["design"] = d
        e["truth"] = etiketler.get(d) if d else None
        satirlar.append(e)

    # ---------- rapor ----------
    L = []
    L.append("# Stil Raporu — gerçek tasarımlar üzerinde kalibrasyon aracı (A12)")
    L.append("")
    L.append("Tarih: 2026-10-08 · kaynak: `designs-export/` (%d export) · motor: `EIStyle` (JS kanonu)"
             % len(satirlar))
    if args.etiketler:
        L.append("Etiket: `%s` (%d tasarım)" % (args.etiketler, len(etiketler)))
    else:
        L.append("Etiket: **yok** — ölçüm modu (sinyal tablosu)")
    L.append("")
    L.append("> Kısıt: eşik taraması **yalnızca anime/cartoon/margin** içindir; stud kuralı")
    L.append("> gevčetilmez (weak keyword tek başına stud saymaz; hücre tekdüzeliği/kare koşulu")
    L.append("> ve `fewTextures` zorunluluğu yerinde durur).")
    L.append("")

    # --- sinyal tablosu (tasarım bazlı, uniq) ---
    L.append("## 1. Sinyal tablosu (tasarım bazlı)")
    L.append("")
    baslik = ["Tasarım", "Etiket", "Karar"] + [k for k, _ in ANAHTAR_SINYALLER]
    L.append("| " + " | ".join(baslik) + " |")
    L.append("|" + "|".join(["---"] * len(baslik)) + "|")
    by_design = {}
    for e in satirlar:
        by_design.setdefault(e["design"], []).append(e)
    for d in sorted(by_design):
        es = by_design[d]
        kararlar = Counter(e["style"] for e in es)
        karar = ", ".join("%s×%d" % kv for kv in kararlar.most_common())
        # tasarım-ortası sinyaller (medyan yerine ortalama — okunabilir)
        def ort(key):
            vs = [e["signals"].get(key, 0) for e in es]
            return sum(vs) / len(vs)
        hucre = [d or "?", (etiketler.get(d) or "—"), karar]
        hucre += ["%.2f" % ort(k) for k, _ in ANAHTAR_SINYALLER]
        L.append("| " + " | ".join(hucre) + " |")
    L.append("")

    if not args.etiketler:
        L.append("## 2. Etiket yok — bu tablo tek başına yeterli.")
        L.append("")
        L.append("Etiket dosyası hazırlanınca: `python3 tools/stil_rapor.py --etiketler "
                 "designs-export/_rapor/stil-etiketleri.json`")
        open(RAPOR, "w", encoding="utf-8").write("\n".join(L) + "\n")
        print("ölçüm modu: %d export · %d tasarım → %s" % (len(satirlar), len(by_design), RAPOR))
        return

    # --- uyuşma ---
    eslesen = sum(1 for e in satirlar if e["truth"] and e["style"] == e["truth"])
    toplam = sum(1 for e in satirlar if e["truth"])
    L.append("## 2. Uyuşma (export bazlı)")
    L.append("")
    L.append("Etiketli export: **%d** · uyuşan **%d** (%%%.1f)" % (toplam, eslesen, 100.0 * eslesen / max(toplam, 1)))
    L.append("")

    # karışıklık matrisi
    L.append("### Karışıklık matrisi (satır=etiket, sütun=karar)")
    L.append("")
    truths = sorted(set(e["truth"] for e in satirlar if e["truth"]))
    styles = ["stud", "anime", "cartoon", "belirsiz"]
    L.append("| etiket \\ karar | " + " | ".join(styles) + " |")
    L.append("|---|" + "|".join(["---"] * len(styles)) + "|")
    for t in truths:
        row = [sum(1 for e in satirlar if e["truth"] == t and e["style"] == s) for s in styles]
        L.append("| %s | %s |" % (t, " | ".join(str(x) for x in row)))
    L.append("")

    # yanlışlar
    yanlis = [e for e in satirlar if e["truth"] and e["style"] != e["truth"]]
    if yanlis:
        L.append("### Uyuşmayanlar (%d)" % len(yanlis))
        L.append("")
        L.append("| Export | Etiket | Karar | ışık/detay/koyuluk | doku/efekt |")
        L.append("|---|---|---|---|---|")
        for e in yanlis:
            s = e["signals"]
            L.append("| %s | %s | %s | %.2f / %.2f / %.2f | %.2f / %.2f |" % (
                e["export"], e["truth"], e["style"],
                s.get("lightingIndex", 0), s.get("detailIndex", 0), s.get("darknessIndex", 0),
                s.get("textureIndex", 0), s.get("effectDensity", 0)))
        L.append("")

    # --- eşik taraması ---
    L.append("## 3. Eşik taraması (anime/cartoon/margin)")
    L.append("")
    keys = list(GRID)
    combos = [dict(zip(keys, v)) for v in itertools.product(*[GRID[k] for k in keys])]
    grid_path = os.path.join(HERE, "_stil_grid.json")
    json.dump(combos, open(grid_path, "w"))
    try:
        scan = dump(grid_path)
    finally:
        os.unlink(grid_path)

    def agreement(decisions):
        ok = tot = 0
        for e, dec in zip(satirlar, decisions):
            if not e["truth"]:
                continue
            tot += 1
            if dec == e["truth"]:
                ok += 1
        return ok, tot

    # mevcut karar (ilk satır = etiketli export sırası)
    mevcut_ok, mevcut_tot = agreement([e["style"] for e in satirlar])
    L.append("Mevcut eşikler: **%d/%d** (%%%.1f)" % (mevcut_ok, mevcut_tot, 100.0 * mevcut_ok / max(mevcut_tot, 1)))
    L.append("")
    L.append("Taranan kombinasyon: **%d**" % len(combos))
    L.append("")
    skorlar = []
    for g in scan["grid"]:
        ok, tot = agreement(g["decisions"])
        skorlar.append((ok / max(tot, 1), ok, tot, g["overrides"]))
    skorlar.sort(key=lambda x: (-x[0], -x[1]))
    L.append("| # | uyuşma | en iyi eşikler |")
    L.append("|---|---|---|")
    for i, (oran, ok, tot, ov) in enumerate(skorlar[:8], 1):
        L.append("| %d | %d/%d (%%%.1f) | `%s`" % (
            i, ok, tot, 100.0 * oran,
            ", ".join("%s=%s" % kv for kv in sorted(ov.items()))))
    L.append("")
    en_iyi = skorlar[0]
    if en_iyi[0] > mevcut_ok / max(mevcut_tot, 1) + 0.001:
        L.append("**Öneri:** tarama mevcut eşiklerden iyi bir ayar buldu — ama applying "
                 "öncesi sinyallerin gerçekten ayrıştığına bak (bkz. §1 tablo).")
    else:
        L.append("**Öneri:** tarama mevcut eşikleri geçemedi — bu, sinyallerin bu korpusta "
                 "etiketleri taşımadığını gösterir (eşik ayarı ile çözülemez; sinyal eklemek "
                 "veya belirsiz bırakmak gerekir).")
    L.append("")
    L.append("Uygulama zinciri (onaydan sonra): `ei-style.js` + `EIStyle.lua` + "
             "`spec/style-rules.json` → `verify_style` → `verify_generalization` → "
             "`verify_real_run` → `build_rbxmx.py --check`.")
    L.append("")

    open(RAPOR, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("etiketli mod: %d/%d etiketli export · uyuşma %d/%d (%%%.1f) · en iyi tarama %d/%d → %s"
          % (toplam, len(satirlar), eslesen, toplam, 100.0 * eslesen / max(toplam, 1),
             en_iyi[1], en_iyi[2], RAPOR))


if __name__ == "__main__":
    main()
