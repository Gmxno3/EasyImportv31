#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A4 KAPISI — v9 DAVRANIŞ DONDURMASI + ASİSTANIN DEVREYE GİRMESİ

İki bölüm, tek amaç: **yeni asistan kodunun eski çıktıyı bozmadığını kanıtlamak** ve
devreye girdiğinde doğru yerde konuştuğunu göstermek.

  A) v9 DONDURMA (altın dosya)
     Eklentinin gerçek saf bloğu (simplifyTree → parseLayerTags → decideClass) her fixture için
     birebir altın kararları üretmeli. Ayrıca `ei` alanları KALDIRILMIŞ hâlde de aynı kararlar
     çıkmalı ve asistan HİÇ çağrılmamalı (sayılar: predicts=0).

  B) ASİSTAN (yalnızca `ei` varken)
     * Stil: `EIStyle` çıktısı `verify_style.py` EXPECTED tablosuyla aynı.
     * Ad/etiket sinyali olan katmanda asistan kararı DEĞİŞTİRMİYOR (kullanıcının etiketi kazanır).
     * Asistanın konuştuğu her katmanda sınıf, üç dilli hattın (EIRaw → EIFeatures → EIModel)
     * doğrudan sonucuyla aynı ve güven ≥ CONF_MIN ve kind-uyumlu.
     * Öğrenilmiş düzeltme kararı gerçekten değiştiriyor ve kaynağı "ogrenme" oluyor.
     * Düğüm ↔ RAW eşlemesi tam (hizalama kayıyor ise sessizce yanlış özellik üretilmesin).

  C) PAKET BÜTÜNLÜĞÜ
     * Paketlenmiş kaynak (modüller gömülü) fengari'de derleniyor + luau-lint temiz.
     * 7 modül gömülü (EIAnim dâhil); gömme deterministik (iki kez üretim aynı bayt).
     * `build_rbxmx.py --check` senkron diyor (diskteki .rbxmx = kaynaktan üretilen).

Kullanım:
    python3 tools/verify_plugin_v9.py              # kapı
    python3 tools/verify_plugin_v9.py --update     # altın dosyayı yeniden üret (BİLİNÇLİ değişiklikte)
Çıkış: 0 = GEÇTİ · 1 = BAŞARISIZ
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLUGIN_DIR = os.path.join(os.path.dirname(ROOT), "roblox-studio-plugin")
PLUGIN_LUA = os.path.join(PLUGIN_DIR, "EasyImportStudioPlugin.lua")
FIX_DIR = os.path.join(ROOT, "datasets", "fixtures", "exports")
GOLDEN = os.path.join(ROOT, "datasets", "golden", "v9_decisions.json")

sys.path.insert(0, HERE)
sys.path.insert(0, PLUGIN_DIR)

from luatable import dumps as lua_dumps          # noqa: E402
from verify_teacher import luau_to_lua, run_fengari, extract_pure_block  # noqa: E402
from verify_runtime import luau_lint              # noqa: E402
from verify_style import EXPECTED                 # noqa: E402  (stil kalibrasyon hedefi tek kaynak)
import build_rbxmx                                # noqa: E402

SAMPLES = sorted(f for f in os.listdir(FIX_DIR) if f.endswith(".json"))
SIGNAL_KEYS = ["forceClass", "isButton", "isNameButton", "isInput", "isScroll", "isScrollX",
               "isScrollY", "isVideo", "isViewport", "isCanvas", "isHover", "isClicked"]
ASSIST_CONF_MIN = 0.70


# ------------------------------------------------------------------ Lua programı
LUA_PRELUDE = r"""
local function esc(s)
  s = tostring(s == nil and "" or s)
  s = s:gsub("\\", "\\\\"):gsub("\t", "\\t"):gsub("\n", "\\n"):gsub("\r", "\\r")
  return s
end

local SIGNAL_KEYS = { __SIGNAL_KEYS__ }

local function signalsOf(tags)
  local out = {}
  for i = 1, #SIGNAL_KEYS do
    local k = SIGNAL_KEYS[i]
    if tags[k] then
      out[#out + 1] = (k == "forceClass") and ("force:" .. tostring(tags[k])) or k
    end
  end
  return table.concat(out, ",")
end
"""

# Karar yolu — eklentinin buildNode akışının birebir izdüşümü (assist kapısı dâhil).
LUA_DRIVER = r"""
local DOC = __DOC__
local LEARN = __LEARN__
local MODULES_OFF = __MODULES_OFF__

-- v9 yolu: modüller gömülü DEĞİLKEN (eski eklenti) sadeleştirme bayrağı da kapalıdır.
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
    -- Bağımsız referans: aynı hattı doğrudan çağır (düğüm↔RAW hizalamasını da kanıtlar)
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
    "R", path, esc(clean), esc(cls0), esc(cls), esc(source), string.format("%.6f", conf),
    esc(ctx), esc(direct), signalsOf(tags), tostring(item.kind or ""), (item.image and "img" or "-")
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
local learnText = ""
if not MODULES_OFF and EILearn and session.learn then learnText = EILearn.encode(session.learn) end
io.write("S\tlearn\t" .. esc(learnText) .. "\n")
io.write("S\trows\t" .. tostring(#rows) .. "\tnModel\t" .. tostring(nModel) .. "\n")
io.write(table.concat(rows, "\n") .. "\n")
"""


def plugin_source():
    with open(PLUGIN_LUA, encoding="utf-8") as fh:
        return fh.read()


def extract_assist_block(src):
    a = src.index("-- <<ASSIST_BEGIN>>")
    b = src.index("-- <<ASSIST_END>>")
    return src[a:b]


def build_program(src, doc, learn, modules=True):
    """Eklentinin karar yolunu fengari'de koşturur.

    modules=False → modüller gömülü değil (v9 eklentisinin birebir durumu); asistan kapalı kalır.
    modules=True  → paketlenmiş .rbxmx'in durumu.
    """
    pure_src, _full = extract_pure_block(PLUGIN_LUA)
    pure_src, _ = luau_to_lua(pure_src)
    assist_src = extract_assist_block(src)
    mod_lines = []
    if modules:
        for name, fname in build_rbxmx.MODULES:
            with open(os.path.join(build_rbxmx.ASSIST_LUA_DIR, fname), encoding="utf-8") as fh:
                body = fh.read().rstrip("\n")
            mod_lines.append("local %s = (function()\n%s\nend)()" % (name, body))
    prelude = LUA_PRELUDE.replace("__SIGNAL_KEYS__", lua_dumps(SIGNAL_KEYS))
    driver = (LUA_DRIVER
              .replace("__DOC__", lua_dumps(doc))
              .replace("__MODULES_OFF__", "false" if modules else "true")
              .replace("__LEARN__", lua_dumps(learn) if learn is not None else "nil"))
    return "\n".join([prelude, pure_src, "\n".join(mod_lines), assist_src, driver])


def run_lua(prog):
    out = run_fengari(prog)
    rows, summary = [], {}
    for line in out.split("\n"):
        if not line:
            continue
        p = line.split("\t")
        if p[0] == "R":
            rows.append(p[1:])
        elif p[0] == "S":
            summary.setdefault(p[1], p[2:])
    # BÜTÜNLÜK KAPISI: sürücü "S rows N" ile kaç satır ürettiğini bildirir. Gelen satır sayısı
    # tutmuyorsa çıktı taşınırken kesilmiştir (bkz. verify_teacher.run_fengari notu) — sessizce
    # eksik veriyle ölçüm yapmak yerine burada gürültü çıkarılır.
    if summary.get("rows"):
        beklenen = int(summary["rows"][0])
        if beklenen != len(rows):
            raise RuntimeError("koşum çıktısı EKSİK: sürücü %d satır bildirdi, %d satır geldi"
                               % (beklenen, len(rows)))
    return rows, summary


def load_doc(name):
    with open(os.path.join(FIX_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def doc_has_ei(doc):
    """Dökümanda (kök dâhil) herhangi bir düğümde `ei` yan kanalı var mı?"""
    found = [False]

    def rec(item):
        if found[0] or not isinstance(item, dict):
            return
        if isinstance(item.get("ei"), dict):
            found[0] = True
            return
        for ch in item.get("children") or []:
            rec(ch)

    rec(doc.get("root"))
    return found[0]


def strip_ei(doc):
    """`ei` yan kanalını tüm ağaçtan siler (v9 export'unun birebir eşdeğeri)."""
    out = copy.deepcopy(doc)

    def rec(item):
        if not isinstance(item, dict):
            return
        item.pop("ei", None)
        for ch in item.get("children") or []:
            rec(ch)

    rec(out.get("root"))
    return out


# ------------------------------------------------------------------------- kapı
def main():
    update = "--update" in sys.argv
    problems, notes = [], []

    print("=" * 74)
    print("A4 KAPISI — v9 DONDURMA + ASİSTAN DEVREYE GİRME")
    print("=" * 74)

    src = plugin_source()
    print("  [OK] kaynak: %s (%d satır)" % (os.path.relpath(PLUGIN_LUA, os.path.dirname(ROOT)),
                                           src.count("\n") + 1))

    # ---- A) v9 dondurma (altın dosya) ----
    golden = None
    if os.path.exists(GOLDEN):
        with open(GOLDEN, encoding="utf-8") as fh:
            golden = json.load(fh)
    fresh = {}
    for name in SAMPLES:
        doc = load_doc(name)
        rows, _sum = run_lua(build_program(src, doc, None, modules=False))
        fresh[name] = rows
    if update or golden is None:
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        with open(GOLDEN, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"format": "ei-v9-golden", "version": 1, "fixtures": fresh},
                      fh, ensure_ascii=False, sort_keys=True, indent=1)
            fh.write("\n")
        print("  [i] altın dosya yazıldı: %s (%d fixture, %d katman)"
              % (os.path.relpath(GOLDEN, os.path.dirname(ROOT)), len(fresh),
                 sum(len(v) for v in fresh.values())))
        golden = {"fixtures": fresh}

    if golden.get("fixtures") != fresh:
        for name in SAMPLES:
            g, f = golden["fixtures"].get(name), fresh.get(name)
            if g != f:
                problems.append("%s: v9 kararları altın dosyadan farklı (%s satır vs %s)"
                                % (name, len(g or []), len(f or [])))
                for i, (a, b) in enumerate(zip(g or [], f or [])):
                    if a != b:
                        problems.append("    ilk fark #%d: altın %r ≠ şimdi %r" % (i, a, b))
                        break
                break
    else:
        print("  [OK] v9 dondurma (modüller kapalı): %d fixture × %d katman altın dosyayla BİREBİR"
              % (len(fresh), sum(len(v) for v in fresh.values())))

    # ---- A2) `ei` YOKKEN: aynı kararlar + asistan hiç çağrılmıyor ----
    for name in SAMPLES:
        doc = strip_ei(load_doc(name))
        rows, summary = run_lua(build_program(src, doc, None, modules=True))
        st = summary.get("stats", ["0", "0", "0", "0", "0"])
        active = summary.get("active", ["false"])[0]
        if rows != golden["fixtures"].get(name):
            problems.append("%s: `ei` silinince kararlar değişti (asistan sızıyor!)" % name)
        if active != "false" or st[0] != "0":
            problems.append("%s: `ei` yokken asistan devrede (active=%s predicts=%s)"
                            % (name, active, st[0]))
    if not any(p.startswith("S") for p in problems):
        print("  [OK] `ei` YOKKEN: %d fixture'da kararlar aynı, asistan hiç hesaplamadı (predicts=0)"
              % len(SAMPLES))

    # ---- B) `ei` VARKEN: asistan nerede konuşuyor? ----
    total_rows, total_model, total_learned, overrides, kept = 0, 0, 0, 0, 0
    style_mismatch = []
    for name in SAMPLES:
        doc = load_doc(name)
        rows, summary = run_lua(build_program(src, doc, None, modules=True))
        st = summary.get("stats", ["0", "0", "0", "0", "0"])
        style = summary.get("style", ["-", "0"])
        active = summary.get("active", ["false"])[0] == "true"
        ei_here = doc_has_ei(doc)
        if active != ei_here:
            problems.append("%s: `ei` %s ama asistan %s (beklenen: %s)"
                            % (name, "var" if ei_here else "yok",
                               "devrede" if active else "kapalı",
                               "devrede" if ei_here else "kapalı"))
            continue
        if not ei_here:
            # `ei` yoksa çıktı v9 olmalı — hem kararlar hem de düğüm kümesi birebir
            if rows != golden["fixtures"].get(name):
                problems.append("%s: `ei` yokken kararlar v9 altınından farklı" % name)
            elif rows != fresh.get(name):
                problems.append("%s: `ei` yokken modülsüz koşuyla aynı değil" % name)
            continue

        total_rows += len(rows)
        total_model += int(st[1])
        total_learned += int(st[2])
        # Gated v9 hatası düzeltmesi: asistan modunda görsel dolgulu frame'ler korunur →
        # katman sayısı v9 yolundan ASLA az olamaz (en az bir fixture'da artmalı, aşağıda).
        v9n = len(fresh.get(name) or [])
        if len(rows) < v9n:
            problems.append("%s: asistan modunda katman kaybı (%d < v9 %d)" % (name, len(rows), v9n))
        if len(rows) > v9n:
            kept += len(rows) - v9n
        for r in rows:
            path, cls0, cls, source, conf, direct, sig = r[0], r[2], r[3], r[4], r[5], r[7], r[8]
            if direct == "-":
                problems.append("%s: %s düğümü RAW'da bulunamadı (hizalama kaydı)" % (name, path))
                break
            if sig != "" and cls != cls0:
                problems.append("%s: %s ad/etiket sinyali var (%s) ama asistan sınıfı değiştirdi (%s→%s)"
                                % (name, path, sig, cls0, cls))
            if source != "-":
                if source not in ("model", "ogrenme"):
                    problems.append("%s: %s bilinmeyen karar kaynağı: %s" % (name, path, source))
                if cls != direct:
                    problems.append("%s: %s asistan sınıfı (%s) doğrudan hat sonucuyla (%s) aynı değil"
                                    % (name, path, cls, direct))
                if float(conf) < ASSIST_CONF_MIN:
                    problems.append("%s: %s güven eşiğin altında: %s" % (name, path, conf))
                overrides += 1
        want_style = EXPECTED.get(name)
        if want_style and style[0] != want_style:
            style_mismatch.append("%s: beklenen %s, gelen %s" % (name, want_style, style[0]))
    if style_mismatch:
        problems.extend("stil uyuşmazlığı — " + m for m in style_mismatch)
    else:
        print("  [OK] stil: `ei` taşıyan fixture'larda EXPECTED tablosuyla aynı")
    if kept > 0:
        print("  [OK] kilitli v9 hatası düzeltildi: asistan modunda %d görsel dolgulu frame korundu" % kept)
    else:
        problems.append("görsel dolgulu frame düzeltmesi hiç etki etmedi (gated yol kopuk olabilir)")
    if overrides >= 5:
        print("  [OK] asistan %d/%d katmanda konuştu (model %d · öğrenilmiş %d) · sinyalli katmana dokunmadı"
              % (overrides, total_rows, total_model, total_learned))
    else:
        problems.append("asistan neredeyse hiç konuşmuyor (%d/%d) — `ei` ölçümü ya da özellik hattı kopuk"
                        % (overrides, total_rows))

    # ---- B2) öğrenilmiş düzeltme kararı değiştiriyor mu? ----
    def alt_class(cls):
        return {"ImageLabel": "ImageButton", "ImageButton": "ImageLabel", "Frame": "CanvasGroup",
                "CanvasGroup": "Frame", "TextLabel": "TextButton", "TextButton": "TextLabel"}.get(cls)

    probe = None
    for name in SAMPLES:
        doc = load_doc(name)
        if not doc_has_ei(doc):
            continue
        rows, _s = run_lua(build_program(src, doc, None, modules=True))
        for r in rows:
            if r[4] == "model" and alt_class(r[7]):
                probe = (name, r[0], r[6], r[7], r[3], alt_class(r[7]))
                break
        if probe:
            break
    if not probe:
        problems.append("öğrenme testi için uygun katman bulunamadı (kaynak=model, alternatif sınıfı olan)")
    else:
        name, path, ctx, pred_cls, cls0, target = probe
        learn = {"v": 1, "anim": {}, "cls": {ctx: {target: 3}}, "events": 1, "exports": 0}
        rows, summary = run_lua(build_program(src, load_doc(name), learn, modules=True))
        hit = next((r for r in rows if r[0] == path), None)
        if not hit:
            problems.append("öğrenme testi: %s/%s satırı bulunamadı" % (name, path))
        elif hit[3] == target and hit[4] == "ogrenme":
            print("  [OK] öğrenilmiş düzeltme: %s · %s — bağlam %s → %s (model %s demişti)"
                  % (name, path, ctx, target, pred_cls))
        else:
            problems.append("öğrenilmiş düzeltme kararı değiştirmedi: %s/%s → sınıf %s kaynak %s"
                            % (name, path, hit[3], hit[4]))
        # düzeltme sayacı: açık etiketli ve modelin farklı düşündüğü katmanlar sayılmalı
        corr = int(summary.get("stats", ["0", "0", "0", "0", "0"])[4])
        notes.append("%s: %d düzeltme kaydedildi (açık etiket ≠ model tahmini)" % (name, corr))

    # ---- C) paket bütünlüğü ----
    bundled = build_rbxmx.inject_modules(src)
    lua_bundled, _conv = luau_to_lua(bundled)
    probe_prog = ("local chunk, err = load([=====[\n" + lua_bundled + "\n]=====])\n"
                  "if not chunk then io.write('HATA: ' .. tostring(err)) os.exit(1) end\nio.write('OK')\n")
    out = run_fengari(probe_prog)
    if out.strip() != "OK":
        problems.append("paketlenmiş kaynak derlenmiyor: " + out.strip()[:400])
    else:
        print("  [OK] paketlenmiş kaynak (modüller gömülü) fengari'de derleniyor")
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(bundled)
        tmp_lua = fh.name
    try:
        lint = luau_lint(tmp_lua)          # yol alır
    finally:
        os.unlink(tmp_lua)
    if lint:
        problems.append("paketlenmiş kaynak luau-lint'ten geçmedi: %s" % (lint[:3],))
    else:
        print("  [OK] paketlenmiş kaynak luau-lint temiz")
    missing = [n for n, _f in build_rbxmx.MODULES
               if ("local %s = (function()" % n) not in bundled]
    if missing:
        problems.append("pakete gömülmeyen modüller: " + ", ".join(missing))
    else:
        print("  [OK] %d modül pakete gömülü: %s"
              % (len(build_rbxmx.MODULES), ", ".join(n for n, _ in build_rbxmx.MODULES)))
    again = build_rbxmx.inject_modules(src)
    if again != bundled:
        problems.append("gömme deterministik değil (iki üretim farklı)")
    else:
        print("  [OK] gömme deterministik: iki üretim aynı (%d KB)" % (len(bundled) // 1024))
    # .rbxmx'i baştan sona çöz: XML kaçışı ve gömülü kaynak birebir mi?
    import xml.etree.ElementTree as ET
    rbxmx_path = os.path.join(PLUGIN_DIR, "EasyImportStudioPlugin.rbxmx")
    try:
        root_el = ET.parse(rbxmx_path).getroot()
        src_el = root_el.find(".//ProtectedString[@name='Source']")
        disk_src = src_el.text if src_el is not None else None
        if disk_src is None:
            problems.append(".rbxmx içinde Source bulunamadı")
        elif disk_src != bundled:
            problems.append(".rbxmx içindeki kaynak, üretilen kaynaktan farklı (%d vs %d karakter)"
                            % (len(disk_src), len(bundled)))
        else:
            print("  [OK] .rbxmx çözüldü: XML geçerli ve gömülü kaynak üretilenle birebir (%d KB)"
                  % (len(disk_src) // 1024))
    except Exception as exc:                     # noqa: BLE001
        problems.append(".rbxmx çözülemedi: %s" % exc)

    r = subprocess.run([sys.executable, os.path.join(PLUGIN_DIR, "build_rbxmx.py"), "--check"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        problems.append("build_rbxmx --check: " + (r.stdout or r.stderr)[-300:])
    else:
        print("  " + (r.stdout.strip().splitlines() or [""])[-1])

    print("-" * 74)
    for n in notes:
        print("  [i] " + n)
    if problems:
        for p in problems[:20]:
            print("  [!!] " + p)
        if len(problems) > 20:
            print("  [!!] … %d sorun daha" % (len(problems) - 20))
        print("SONUÇ: BAŞARISIZ — %d sorun" % len(problems))
        return 1
    print("SONUÇ: GEÇTİ — v9 dondurulmuş · asistan %d katmanda devrede · paket bütünlüğü tamam"
          % overrides)
    return 0


if __name__ == "__main__":
    sys.exit(main())
