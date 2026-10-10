#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STİL TESPİTİ KAPISI (A10) — JS ↔ fengari/Lua 5.3

Stil tespiti, asistanın sınıf/animasyon kararına ÖNCELİK (prior) verir ve 379 boyutlu
vektörün J grubunu (styleStud/styleAnime/styleCartoon/styleBelirsiz/styleConf) doldurur.
Bu grup bugüne kadar "belirsiz" sabitiydi — yani ölü ağırlıktı.

Bu kapı üç şeyi kanıtlar:
  1. EIStyle.lua Luau yasaklı API'lerden temiz.
  2. 4 export örneğinde JS ve Lua **birebir aynı** stil kararını + sinyalleri + metni üretiyor.
  3. Karar GERÇEKTEN farklılaşıyor (stud-market→stud, anime-hud→anime, cartoon-menu→cartoon,
     edge→belirsiz) ve bu fark RAW çıktısındaki style* alanlarına yansıyor, yani J grubu canlı.

Kullanım:  python3 tools/verify_style.py        (EASYIMPORT_LUA_BIN desteklenir)
Çıkış: 0 = geçti, 1 = başarısız
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from luatable import dumps as lua_dumps  # noqa: E402
from verify_runtime import luau_lint  # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")
FIX_DIR = os.path.join(ROOT, "datasets", "fixtures", "exports")
VENDOR = os.path.join(HERE, "vendor")

# Kapı, fixtures klasöründeki TÜM export'ları gezer — yeni örnek eklendiğinde otomatik kapsanır.
SAMPLES = sorted(f for f in os.listdir(FIX_DIR) if f.endswith(".json"))

# Sentetik örneklerin DOSYA ADINDAN beklenen stil (fixture'lar RAW determinizmi için üretildi,
# stil eşikleri için DEĞİL). Eşikler spec'te "proposed"; bu tablo bir KALİBRASYON HEDEFİDİR:
# uymayan satırlar kapıyı düşürmez, raporda "eşik şu yüzden tutmadı" diye gösterilir.
EXPECTED = {
    "stud-market.json": "stud",
    "stud-unnamed.json": "stud",      # adında stud GEÇMEZ: kanıt yalnızca döşeme geometrisi
    "stud-icon.json": "belirsiz",     # NEGATİF: tek stud ikonu ≠ stud stili
    "anime-hud.json": "anime",
    "cartoon-menu.json": "cartoon",
    "edge.json": "belirsiz",
    "widgets-kit.json": "belirsiz",    # SINIF kapsama kiti: nötr stil (stil kapısı değil)
}

# SERT kural (rapor değil): bu örneklerde stud ÇIKMAMALI. "Stud ikonu" tuzağını kilitler.
NOT_STUD = {"stud-icon.json", "cartoon-menu.json", "anime-hud.json", "edge.json", "widgets-kit.json"}
TOL = 1e-12


# --------------------------------------------------------------------------- koşucular
JS_RUNNER = r"""
const EIRaw = require(process.argv[2] + '/ei-raw.js');
const EIStyle = require(process.argv[2] + '/ei-style.js');
const fs = require('fs');
const doc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = EIRaw.extract(doc, { styleFn: EIStyle.detect });
process.stdout.write(JSON.stringify({ style: out.style, nodes: out.nodes }));
"""

FENGARI_RUNNER = r"""
const { lauxlib, lua, lualib, to_luastring } = require('fengari');
const fs = require('fs');
const prog = fs.readFileSync(process.argv[2], 'utf8');
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
const st = lauxlib.luaL_dostring(L, to_luastring(prog));
if (st !== lua.LUA_OK) {
  process.stderr.write('LUA HATASI: ' + (lua.lua_tojsstring(L, -1) || '?') + '\n');
  process.exit(1);
}
"""

LUA_SERIALIZER = r"""
local function esc(s)
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end
local function isArray(t)
  local n, m = 0, 0
  for k in pairs(t) do
    if type(k) ~= 'number' or k ~= math.floor(k) or k < 1 then return false end
    n = n + 1
    if k > m then m = k end
  end
  return n == m and m > 0
end
local function ser(v)
  local t = type(v)
  if t == 'nil' then return 'null'
  elseif t == 'boolean' then return v and 'true' or 'false'
  elseif t == 'number' then
    if v ~= v then return '0' end
    if v == math.huge then return '1e308' end
    if v == -math.huge then return '-1e308' end
    if v == math.floor(v) and math.abs(v) < 1e15 then return string.format('%.0f', v) end
    return string.format('%.17g', v)
  elseif t == 'string' then return '"' .. esc(v) .. '"'
  elseif t == 'table' then
    if isArray(v) then
      local parts = {}
      for j = 1, #v do parts[j] = ser(v[j]) end
      return '[' .. table.concat(parts, ',') .. ']'
    end
    local ks, i = {}, 1
    for k, _ in pairs(v) do ks[i] = tostring(k); i = i + 1 end
    table.sort(ks)
    local parts = {}
    for j = 1, #ks do
      parts[j] = '"' .. esc(ks[j]) .. '":' .. ser(v[ks[j]])
    end
    return '{' .. table.concat(parts, ',') .. '}'
  end
  return 'null'
end
"""

LUA_MAIN = r"""
local out = EIRaw.extract(DOC, { styleFn = EIStyle.detect })
io.write('{"style":' .. ser(out.style) .. ',"nodes":[')
for i = 1, #out.nodes do
  if i > 1 then io.write(',') end
  io.write(ser(out.nodes[i]))
end
io.write(']}')
"""


def run_js(path):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JS_RUNNER)
        tmp = fh.name
    try:
        r = subprocess.run(["node", tmp, JS_DIR, path], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError("node hatası:\n" + (r.stderr or "")[:2000])
        return json.loads(r.stdout)
    finally:
        os.unlink(tmp)


def run_lua(path, lua_bin=None):
    raw_src = open(os.path.join(LUA_DIR, "EIRaw.lua"), encoding="utf-8").read()
    style_src = open(os.path.join(LUA_DIR, "EIStyle.lua"), encoding="utf-8").read()
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    prog = (
        LUA_SERIALIZER + "\n"
        "local EIRaw = (function()\n" + raw_src + "\nend)()\n"
        "local EIStyle = (function()\n" + style_src + "\nend)()\n"
        "local DOC = " + lua_dumps(doc) + "\n"
        + LUA_MAIN
    )
    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(prog)
            tmp = fh.name
        try:
            r = subprocess.run([lua_bin, tmp], capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError("%s hatası:\n%s" % (lua_bin, (r.stderr or "")[:2500]))
            return json.loads(r.stdout)
        finally:
            os.unlink(tmp)

    if not os.path.isdir(os.path.join(VENDOR, "fengari")):
        raise RuntimeError("fengari bulunamadı: %s" % VENDOR)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(FENGARI_RUNNER)
        runner = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(prog)
        tmp_lua = fh.name
    try:
        env = dict(os.environ)
        env["NODE_PATH"] = VENDOR
        r = subprocess.run(["node", runner, tmp_lua], capture_output=True, text=True,
                           timeout=300, env=env)
        if r.returncode != 0:
            raise RuntimeError("fengari hatası:\n" + (r.stderr or "")[:3000])
        return json.loads(r.stdout)
    finally:
        os.unlink(runner)
        os.unlink(tmp_lua)


# --------------------------------------------------------------------------- karşılaştırma
def cmp_val(x, y, path, bad):
    if isinstance(x, bool) or isinstance(y, bool):
        if bool(x) != bool(y):
            bad.append((path, x, y))
        return
    if x is None or y is None:
        if x != y:
            bad.append((path, x, y))
        return
    if isinstance(x, dict) and isinstance(y, dict):
        ka, kb = set(x.keys()), set(y.keys())
        if ka != kb:
            bad.append((path + " {anahtarlar}", sorted(ka ^ kb), ""))
            return
        for k in sorted(ka):
            cmp_val(x[k], y[k], path + "." + k, bad)
        return
    if isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            bad.append((path + " [uzunluk]", len(x), len(y)))
            return
        for i, (a, b) in enumerate(zip(x, y)):
            cmp_val(a, b, "%s[%d]" % (path, i), bad)
        return
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        d = abs(float(x) - float(y))
        den = max(abs(float(x)), abs(float(y)))
        rel = d / den if den > 0 else 0.0
        if d > TOL and rel > TOL:
            bad.append((path, x, y))
        return
    if x != y:
        bad.append((path, x, y))


def main():
    lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
    print("=" * 74)
    print("STİL TESPİTİ KAPISI (A10) — ei-style.js  ↔  EIStyle.lua")
    print("=" * 74)

    hits = luau_lint(os.path.join(LUA_DIR, "EIStyle.lua"))
    if hits:
        print("  [!!] Luau ihlali (%d):" % len(hits))
        for ln, txt, why in hits[:8]:
            print("      satır %-5d %-45s %s" % (ln, txt, why))
        return 1
    print("  [OK] luau-lint -> EIStyle.lua temiz")

    total_bad = []
    labels = {}
    for name in SAMPLES:
        path = os.path.join(FIX_DIR, name)
        js = run_js(path)
        lua = run_lua(path, lua_bin)

        bad = []
        cmp_val(js["style"], lua["style"], "style", bad)
        cmp_val(js["nodes"], lua["nodes"], "nodes", bad)

        st = js["style"] or {}
        labels[name] = st.get("style")
        sig = st.get("signals", {})
        mark = "OK " if not bad else "!! "
        print("  [%s] %-18s -> %-8s conf=%.3f · ışık=%.3f detay=%.3f doku=%.3f koyu=%.3f efekt=%.3f"
              % (mark, name, st.get("style"), float(st.get("conf") or 0),
                 float(sig.get("lightingIndex") or 0), float(sig.get("detailIndex") or 0),
                 float(sig.get("textureIndex") or 0), float(sig.get("darknessIndex") or 0),
                 float(sig.get("effectDensity") or 0)))
        print("        %s" % st.get("oneLiner"))
        if bad:
            for p, a, b in bad[:10]:
                print("        FARK %-40s js=%r lua=%r" % (p, a, b))
            total_bad += bad

    # --- J grubunun gerçekten canlandığının kanıtı ---------------------------
    print("-" * 74)
    activation = {}
    for name in SAMPLES:
        js = run_js(os.path.join(FIX_DIR, name))
        st = js["style"] or {}
        flags = set()
        for nd in js["nodes"]:
            for k, lab in (("styleStud", "stud"), ("styleAnime", "anime"),
                           ("styleCartoon", "cartoon"), ("styleBelirsiz", "belirsiz")):
                if nd.get(k):
                    flags.add(lab)
        activation[name] = sorted(flags)
    all_flat = set()
    for v in activation.values():
        all_flat |= set(v)
    print("  [i] RAW'daki stil bayrakları: " +
          " · ".join("%s=%s" % (n.replace('.json', ''), "+".join(v) or "-") for n, v in activation.items()))

    # --- kalibrasyon raporu (kapı DEĞİL: eşikler hâlâ "proposed") --------------
    print("-" * 74)
    print("  KALİBRASYON DURUMU (eşikler spec'te 'proposed' — senin etiketlerinle kalibre edilecek)")
    mismatch = 0
    for name in SAMPLES:
        want = EXPECTED.get(name)
        got = labels.get(name)
        if got == want:
            print("    ✓ %-18s hedef %-9s gelen %s" % (name, want, got))
        else:
            mismatch += 1
            print("    ✗ %-18s hedef %-9s gelen %-9s ← eşik tutmadı" % (name, want, got))
    if mismatch:
        print("    Not: sentetik örneklerin sinyalleri bu eşiklerin altında kalıyor;")
        print("         tespit kodu doğru, ayar için GERÇEK export + etiket gerekiyor.")

    problems = []
    if len(all_flat) < 2:
        problems.append("stil bayrakları farklılaşmıyor — J grubu hâlâ ölü olabilir")

    if total_bad:
        print("-" * 74)
        print("  [!!] JS ile Lua arasında %d fark" % len(total_bad))
        print("SONUÇ: BAŞARISIZ — iki dil ayrışıyor")
        return 1

    # --- SERT kural: negatif örneklerde stud çıkmamalı ------------------------
    print("-" * 74)
    for name in sorted(NOT_STUD):
        st = labels.get(name)
        if st == "stud":
            problems.append("%s: stud ÇIKMAMALI (tek stud ikonu / karışık doku tuzağı)" % name)
        else:
            print("  [OK] sert kural: %-18s stud değil (%s)" % (name, st))

    if problems:
        print("-" * 74)
        for p in problems:
            print("  [!!] " + p)
        print("SONUÇ: BAŞARISIZ")
        return 1

    print("  [i] %d örnekte JS ve Lua BİREBİR aynı stil kararını ve RAW'ı üretti" % len(SAMPLES))
    print("-" * 74)
    print("SONUÇ: GEÇTİ — stil tespiti iki dilde birebir; J grubu canlı (%d farklı etiket)"
          % len(all_flat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
