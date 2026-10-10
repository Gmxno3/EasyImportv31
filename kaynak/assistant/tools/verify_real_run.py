#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A4c — GERÇEK TASARIM UÇTAN UCA KOŞUMU (verify_real_run)

`verify_plugin_v9.py` eklentiyi 7 küçük FIXTURE üzerinde koşturur. Bu kapı aynı karar yolunu
**28 gerçek tasarım export'u** (designs-export/*.json · 4.490 katman) üzerinde koşturur:

  A) YAPI     : v9 (asistan kapalı) ↔ asistan açık. Sadeleştirme hangi katmanları attı,
                sadeleştirme kural kararını değiştiriyor mu?
  B) DAVRANIŞ : asistan kaç katmanda konuştu, hangi kaynaktan, güven dağılımı;
                * ad/etiket sinyalli katmana dokundu mu (dokunmamalı),
                * bağımsız hat (direct) kararıyla aynı mı (düğüm↔RAW hizalama kanıtı),
                * kind uyumu (text/görsel/frame) — `Assist.compatible` ile birebir,
                * model güveni ≥ CONF_MIN mi.
  C) ETİKET   : eklentinin KURAL kararı vs eğitim etiketi (real-exports.jsonl) ve
                MODEL kararı vs eğitim etiketi — gerçek veride uyuşma.
  D) STİL     : tasarım başına stil kararı (anime yanlış pozitifi dâhil).

YOL SÖZLEŞMESİ (bu kapının kritik ayrıntısı): eklentinin kendi koşumunda yollar `simplifyTree`
SONRASI ağaçta numaralanır; eğitim etiketleri ise sadeleştirme ÖNCESİ ağaca aittir (ingest.py
0-tabanlı). Bu yüzden buradaki sürücü, her düğüme **özgün yolu** (sadeleştirme öncesi, 0-tabanlı)
taşıtır: ORIG[item] haritası. Karşılaştırma böylece katman katman kesindir — bu, `verify_plugin_v9`
sürücüsünün kopyası DEĞİL, yalnız bu kapı için yazılmış eşleme ekli sürümüdür.

Kullanım:
    python3 tools/verify_real_run.py                # 28 gerçek tasarım (~4 dk)
    python3 tools/verify_real_run.py --limit 3      # duman testi
    python3 tools/verify_real_run.py --detay        # farklılaşan katmanları yaz
Çıkış: 0 = GEÇTİ · 1 = BAŞARISIZ
"""

import argparse
import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJE = os.path.dirname(ROOT)
EXPORT_DIR = os.path.join(PROJE, "designs-export")
LABELS = os.path.join(ROOT, "datasets", "labels", "real-exports.jsonl")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROJE, "roblox-studio-plugin"))
import verify_plugin_v9 as V          # noqa: E402  (ön blok, saf blok, asistan bloğu, koşum)
import build_rbxmx                    # noqa: E402  (gömülü modül listesi)
from luatable import dumps as lua_dumps   # noqa: E402
from verify_plugin_v9 import LUA_PRELUDE, SIGNAL_KEYS, extract_pure_block, luau_to_lua  # noqa: E402

CONF_MIN = 0.70
TEXT_CLS = {"TextLabel", "TextButton", "TextBox"}
IMG_CLS = {"ImageLabel", "ImageButton"}
FRAME_CLS = {"Frame", "ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame"}

# verify_plugin_v9.LUA_DRIVER + ORIG haritası (sadeleştirme öncesi 0-tabanlı özgün yollar).
DRIVER = r"""
local DOC = __DOC__
local LEARN = __LEARN__
local MODULES_OFF = __MODULES_OFF__

-- Özgün yol haritası: sadeleştirme ÖNCESİ, 0-tabanlı (ingest.py sözleşmesi).
local ORIG, ORIG_KIND, ORIG_CLS = {}, {}, {}
do
  local function w(item, path)
    ORIG[item] = path
    local kids = item.children or {}
    for j = 0, #kids - 1 do w(kids[j + 1], path .. "." .. tostring(j)) end
  end
  w(DOC.root, "0")
end

local gateOpen = (not MODULES_OFF) and Assist.modulesOk() and Assist.docHasEi(DOC)

local stats = { flattened = 0, empty = 0 }
simplifyTree(DOC.root, stats, gateOpen)

local session = Assist.newSession(LEARN)
local active = false
local nRaw = 0
local styleUsed, styleConf = "-", 0
if gateOpen then
  local okPrep, prepErr = pcall(Assist.prepare, session, DOC)
  if okPrep then
    active = true
    nRaw = session.nRaw
    styleUsed, styleConf = session.style, session.conf
  else
    io.write("S\tprepError\t" .. esc(prepErr) .. "\n")
  end
end

local rows, nModel = {}, 0
local function rec(item, path)
  local clean, tags = parseLayerTags(item.name)
  local cls0 = decideClass(item, tags)
  local cls, source, conf, ctx, direct = cls0, "-", 0, "-", "-"
  local raw = active and session.byNode[item] or nil
  if raw then
    local vec = EIFeatures.compute(EIFeaturesSpec, raw)
    local pred = EIModel.predict(vec)
    direct = pred.cls
    local a = Assist.decide(session, item, tags)
    if a then
      cls, source, conf, ctx = a.cls, a.source, a.conf or 0, a.ctx or "-"
      nModel = nModel + 1
    end
  end
  if active then Assist.noteCorrection(session, item, tags) end
  rows[#rows + 1] = table.concat({
    "R", ORIG[item] or path, esc(clean), esc(cls0), esc(cls), esc(source),
    string.format("%.6f", conf), esc(ctx), esc(direct), signalsOf(tags),
    tostring(item.kind or ""), (item.image and "img" or "-"),
    tostring(item.w or 0), tostring(item.h or 0)
  }, "\t")
  local kids = item.children or {}
  for i = 1, #kids do rec(kids[i], path .. "." .. tostring(i)) end
end
rec(DOC.root, "0")

local st = session.stats or {}
io.write("S\tstyle\t" .. esc(styleUsed) .. "\t" .. string.format("%.6f", styleConf) .. "\n")
io.write("S\tactive\t" .. tostring(active) .. "\tnRaw\t" .. tostring(nRaw) .. "\n")
io.write("S\tstats\t" .. tostring(st.predicts) .. "\t" .. tostring(st.model) .. "\t"
  .. tostring(st.learned) .. "\t" .. tostring(st.rejected) .. "\t" .. tostring(st.corrections) .. "\n")
io.write("S\trows\t" .. tostring(#rows) .. "\tnModel\t" .. tostring(nModel) .. "\n")
io.write("S\tflat\t" .. tostring(stats.flattened) .. "\t" .. tostring(stats.empty) .. "\n")
io.write(table.concat(rows, "\n") .. "\n")
"""


def program(src, doc, modules):
    """verify_plugin_v9.build_program ile aynı düzen; yalnız sürücü farklı (özgün yol haritalı)."""
    pure_src, _full = extract_pure_block(V.PLUGIN_LUA)
    pure_src, _ = luau_to_lua(pure_src)
    assist_src = V.extract_assist_block(src)
    mod_lines = []
    if modules:
        for name, fname in build_rbxmx.MODULES:
            with open(os.path.join(build_rbxmx.ASSIST_LUA_DIR, fname), encoding="utf-8") as fh:
                body = fh.read().rstrip("\n")
            mod_lines.append("local %s = (function()\n%s\nend)()" % (name, body))
    prelude = LUA_PRELUDE.replace("__SIGNAL_KEYS__", lua_dumps(SIGNAL_KEYS))
    driver = (DRIVER
              .replace("__DOC__", lua_dumps(doc))
              .replace("__MODULES_OFF__", "false" if modules else "true")
              .replace("__LEARN__", "nil"))
    return "\n".join([prelude, pure_src, "\n".join(mod_lines), assist_src, driver])


def uyumlu(kind, image, cls):
    """`Assist.compatible` ile birebir: kind='text' → metin; image → görsel; aksi hâlde frame."""
    if kind == "text":
        return cls in TEXT_CLS
    if image:
        return cls in IMG_CLS
    return cls in FRAME_CLS


def ei_var_mi(doc):
    """Dökümanda (kök dâhil) herhangi bir düğümde `ei` ölçüm kanalı var mı?"""
    bulundu = [False]

    def rec(item):
        if bulundu[0] or not isinstance(item, dict):
            return
        if isinstance(item.get("ei"), dict):
            bulundu[0] = True
            return
        for ch in item.get("children") or []:
            rec(ch)

    rec(doc.get("root"))
    return bulundu[0]


def etiketleri_yukle():
    out = {}
    with open(LABELS, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out[(r["export"], r["path"])] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--detay", action="store_true")
    a = ap.parse_args()

    src = V.plugin_source()
    dosyalar = sorted(f for f in os.listdir(EXPORT_DIR) if f.endswith(".json"))
    if a.limit:
        dosyalar = dosyalar[:a.limit]
    etiket = etiketleri_yukle()

    print("=" * 74)
    print("A4c — GERÇEK TASARIM UÇTAN UCA KOŞUMU (%d tasarım)" % len(dosyalar))
    print("=" * 74)

    hata, notlar = [], []
    top = collections.Counter()
    stil_satirlari = []
    t0 = time.time()

    for i, dosya in enumerate(dosyalar, 1):
        with open(os.path.join(EXPORT_DIR, dosya), encoding="utf-8") as fh:
            doc = json.load(fh)
        export = doc.get("name") or os.path.splitext(dosya)[0]
        rows_off, _s1 = V.run_lua(program(src, doc, modules=False))    # v9 yolu
        rows_on, summ = V.run_lua(program(src, doc, modules=True))     # asistan yolu

        off = {r[0]: r for r in rows_off}
        on = {r[0]: r for r in rows_on}

        stil, stil_conf = summ.get("style", ["-", "0"])[:2]
        aktif = summ.get("active", ["false"])[0] == "true"
        ei_var = ei_var_mi(doc)
        stil_satirlari.append((export, stil, float(stil_conf), aktif))

        if not ei_var:
            # `ei` = ÖLÇÜM kanalı (code.js §"v10 görsel ölçümü": ölçüm yoksa hiç yazılmaz; v9 sözleşmesi).
            # Böyle bir export'ta asistan KAPALI kalmalı ve çıktı v9 ile BİREBİR aynı olmalı.
            top["v9export"] += 1
            pred = int(summ.get("stats", ["0"])[0] or 0)
            fark = [p for p in set(off) | set(on)
                    if off.get(p) != on.get(p)]
            if aktif or pred != 0:
                hata.append("%s: `ei` yokken asistan konuştu (aktif=%s, predicts=%d)"
                            % (export, aktif, pred))
            if fark:
                hata.append("%s: `ei` yokken çıktı v9'dan farklı (%d katman): %s"
                            % (export, len(fark), fark[:3]))
            else:
                top["v9ayni"] += 1
            print("  [%2d/%d] %-30s v9 export (`ei` yok) · katman %4d · asistan kapalı ✅ · "
                  "çıktı v9 ile birebir"
                  % (i, len(dosyalar), export[:30], len(on)))
            top["katman"] += len(on)
            top["v9katman"] += len(off)
            continue

        if not aktif:
            hata.append("%s: `ei` VAR ama asistan devreye girmedi (prep başarısız: %s)"
                        % (export, (summ.get("prepError") or ["-"])[0][:120]))
            continue
        eksik_satir = [r for r in rows_on if len(r) < 13]
        if eksik_satir:
            hata.append("%s: satır biçimi eksik (%s)" % (export, eksik_satir[0][:3]))

        # --- B) davranış ---
        degisen, konusulan = 0, 0
        sinyal_ihlali, hiza_hatasi, kind_hatasi, dusuk_guven = [], [], [], []
        # --- A) yapı ve kural kararı oynadı mı ---
        sadece_v9 = sorted(set(off) - set(on))
        sadece_asistan = sorted(set(on) - set(off))
        kural_oynadi = [(p, off[p][2], on[p][2]) for p in set(off) & set(on) if off[p][2] != on[p][2]]

        # --- C) etiket uyumu ---
        kural_uyan = kural_top = model_uyan = model_top = ad_uyan = 0
        for path, r in on.items():
            _p, clean, cls0, cls, source, conf, _ctx, direct, signals, kind, img, _w, _h = r
            conf = float(conf)
            top["source:" + source] += 1
            if source in ("model", "ogrenme"):
                konusulan += 1
                if source == "model":
                    if direct != cls:
                        hiza_hatasi.append((path, direct, cls))
                    if conf < CONF_MIN - 1e-9:
                        dusuk_guven.append((path, conf))
                if not uyumlu(kind, img == "img", cls):
                    kind_hatasi.append((path, kind, img, cls))
            if signals and (cls != cls0 or source != "-"):
                sinyal_ihlali.append((path, signals, cls0, cls, source))
            if cls != cls0:
                degisen += 1
                if a.detay:
                    print("   ~ %-20s %-12s %s → %s (%s %.2f)" % (export[:20], path, cls0, cls, source, conf))
            e = etiket.get((export, path))
            if not e:
                continue
            kural_top += 1
            if clean == (e.get("clean") or ""):
                ad_uyan += 1
            if cls0 == e["cls"]:
                kural_uyan += 1
            if source in ("model", "ogrenme"):
                model_top += 1
                if cls == e["cls"]:
                    model_uyan += 1

        top["katman"] += len(on)
        top["v9katman"] += len(off)
        top["degisen"] += degisen
        top["konusulan"] += konusulan
        top["kural_uyan"] += kural_uyan
        top["kural_top"] += kural_top
        top["model_uyan"] += model_uyan
        top["model_top"] += model_top
        top["ad_uyan"] += ad_uyan
        top["sadece_v9"] += len(sadece_v9)
        top["sadece_asistan"] += len(sadece_asistan)
        top["kural_oynadi"] += len(kural_oynadi)
        top["etiket_kapsam_disi"] += max(0, sum(1 for (ex, _p) in etiket if ex == export) - len(on))

        print("  [%2d/%d] %-30s katman %4d · sadeleştirme %+d/%+d · asistan %3d karar (%d katman) · "
              "kural-etiket %s · model-etiket %s"
              % (i, len(dosyalar), export[:30], len(on), len(sadece_asistan), -len(sadece_v9),
                 degisen, konusulan,
                 ("%d/%d" % (kural_uyan, kural_top)) if kural_top else "  -  ",
                 ("%d/%d" % (model_uyan, model_top)) if model_top else "  -  "))

        if sinyal_ihlali:
            hata.append("%s: ad/etiket sinyalli katmana dokunuldu: %s" % (export, sinyal_ihlali[:3]))
        if hiza_hatasi:
            hata.append("%s: düğüm↔RAW hizası kaymış: %s" % (export, hiza_hatasi[:3]))
        if kind_hatasi:
            hata.append("%s: kind uyumsuz karar: %s" % (export, kind_hatasi[:3]))
        if dusuk_guven:
            hata.append("%s: güven eşiğin altında konuştu: %s" % (export, dusuk_guven[:3]))
        if kural_oynadi and a.detay:
            for p, x, y in kural_oynadi[:5]:
                print("   ! kural kararı oynadı: %s %s → %s (sadeleştirme yan etkisi)" % (p, x, y))

    # ---- özet ----
    print("-" * 74)
    print("  katman: %d (asistan açık) · %d (v9) · sadeleştirme farkı: yalnız-v9 %d, yalnız-asistan %d"
          % (top["katman"], top["v9katman"], top["sadece_v9"], top["sadece_asistan"]))
    print("  tasarım: %d `ei`li · %d v9 export (`ei` yok → asistan kapalı, çıktı birebir aynı: %d)"
          % (len(dosyalar) - top["v9export"], top["v9export"], top["v9ayni"]))
    print("  kural kararı iki koşumda oynadı: %d katman" % top["kural_oynadi"])
    print("  asistan %d katmanda konuştu · %d katmanda sonucu değiştirdi"
          % (top["konusulan"], top["degisen"]))
    print("  karar kaynağı: %s"
          % ", ".join("%s=%d" % (k.split(":", 1)[1], n) for k, n in sorted(top.items())
                      if k.startswith("source:") and n))
    if top["kural_top"]:
        print("  hizalama kanıtı: etiketle eşleşen %d katmanda ad uyuşması %d (%.2f%%)"
              % (top["kural_top"], top["ad_uyan"], 100.0 * top["ad_uyan"] / top["kural_top"]))
        print("  KURAL kararı vs eğitim etiketi : %d/%d (%.2f%%)"
              % (top["kural_uyan"], top["kural_top"], 100.0 * top["kural_uyan"] / top["kural_top"]))
    if top["model_top"]:
        print("  MODEL kararı vs eğitim etiketi : %d/%d (%.2f%%)"
              % (top["model_uyan"], top["model_top"], 100.0 * top["model_uyan"] / top["model_top"]))
    if top["etiket_kapsam_disi"]:
        notlar.append("%d katmanın etiket karşılığı yok (sadeleştirmenin attığı boş/sarmalayıcılar)"
                      % top["etiket_kapsam_disi"])

    # ---- D) stil ----
    ozet = collections.Counter(s for _e, s, _c, _a in stil_satirlari)
    print("  stil: %s" % ", ".join("%s=%d" % kv for kv in sorted(ozet.items())))
    for export, stil, conf, _a in stil_satirlari:
        if stil != "belirsiz":
            print("      %-34s %-8s %.2f" % (export[:34], stil, conf))
    anime_fp = [e for e, s, _c, _a in stil_satirlari
                if s == "stud" and ("FlashyAnimeUI" in e or "AnimeHUD" in e or "Slots Anime" in e)]
    if anime_fp:
        hata.append("anime tasarımında stud yanlış pozitifi: %s" % anime_fp)

    print("-" * 74)
    for h in hata:
        print("  [!!] " + h)
    for n in notlar:
        print("  [i] " + n)
    print("  [i] süre %.1f dk · koşum eklentinin KENDİ karar yoludur (kopya değil, kaynak metin)"
          % ((time.time() - t0) / 60))
    if hata:
        print("SONUÇ: BAŞARISIZ — %d hata" % len(hata))
        return 1
    print("SONUÇ: GEÇTİ — asistan gerçek tasarımlarda doğru yerde konuşuyor, sınırı aşmıyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
