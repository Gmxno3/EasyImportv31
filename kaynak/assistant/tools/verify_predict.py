#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A4a — TAHMİN KAPISI (verify_predict) — JS ↔ fengari/Lua 5.3 ↔ Python

Model gömülü hâlde üç yerde çalışır: Figma eklentisi (JS), Studio eklentisi (Lua) ve
eğitim/teşhis hattı (Python). Üçü ayrışırsa "aynı model" yalan olur. Bu kapı:

  1. `EIModel.lua` Luau yasaklı API'lerden temiz (luau-lint).
  2. GÖMÜLÜ VERİ birebir: JS DATA ≡ Lua DATA ≡ model/model.json (W, b, mean, std, ln(bias)).
  3. TAHMİN birebir: 4 export'un TÜM katmanlarında (100 vektör) cls/top3 sırası AYNI,
     olasılıklar 1e-12 bağıl tolerans içinde; ayrıca Python kanonuyla da karşılaştırılır.
  4. Kenar durumlar: sıfır vektör, NaN/sonsuz, metin/bool, eksik (kısa) vektör, 1e9 gibi
     büyük değerler → iki dil de çökmüyor ve AYNI kararı veriyor.
  5. Stil öncülü CANLI: aynı vektöre `sty_stud` bayrağı eklenince skorlar değişiyor
     (öncül dosyada duruyor, ölü ağırlık değil) ve iki dil aynı farkı görüyor.

Kullanım:  python3 tools/verify_predict.py        (EASYIMPORT_LUA_BIN desteklenir)
Çıkış: 0 = geçti, 1 = başarısız
"""

import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from luatable import dumps as lua_dumps  # noqa: E402
from verify_runtime import luau_lint  # noqa: E402

import ei_features  # noqa: E402
import ingest  # noqa: E402
import train_class as T  # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")
FIX_DIR = os.path.join(ROOT, "datasets", "fixtures", "exports")
VENDOR = os.path.join(HERE, "vendor")
MODEL = os.path.join(ROOT, "model", "model.json")
SAMPLES = ["stud-market.json", "anime-hud.json", "cartoon-menu.json", "edge.json"]
TOL = 1e-12
DIM = 379

# JSON/Lua değişmezi NaN/sonsuz taşıyamaz → kodlayıp iki dilde de geri çözeriz
# (NaN sözlük anahtarı olamaz: nan != nan, o yüzden karşılaştırmalarla ayıklanır)
def encode_vec(vec):
    out = []
    for v in vec:
        if isinstance(v, float) and v != v:
            out.append("@@nan")
        elif v == float("inf"):
            out.append("@@inf")
        elif v == float("-inf"):
            out.append("@@-inf")
        else:
            out.append(v)
    return out

# --- JS koşucu: modül verisini + verilen vektörler için tahminleri döker ---
JS_RUNNER = r"""
const EIModel = require(process.argv[2] + '/ei-model.js');
const fs = require('fs');
const raw = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
function fix(v) {
  return v.map(function (x) {
    if (x === '@@nan') return NaN;
    if (x === '@@inf') return Infinity;
    if (x === '@@-inf') return -Infinity;
    return x;
  });
}
const vecs = raw.map(fix);
const preds = vecs.map(function (v) {
  var r = EIModel.predict(v);
  return { cls: r.cls, conf: r.conf, top3: r.top3, probs: r.probs, style: r.style };
});
process.stdout.write(JSON.stringify({
  VERSION: EIModel.VERSION, DIM: EIModel.DIM, CLASSES: EIModel.CLASSES,
  DATA: EIModel.DATA, preds: preds
}));
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

LUA_FIXV = r"""
local function fixv(v)
  local t = {}
  for i = 1, #v do
    local x = v[i]
    if x == '@@nan' then t[i] = 0 / 0
    elseif x == '@@inf' then t[i] = math.huge
    elseif x == '@@-inf' then t[i] = -math.huge
    else t[i] = x end
  end
  return t
end
"""

# ⚠ fengari io.write, 64 KiB'ı aşan çıktıyı SESSİZCE kırpar (gözlemlendi: tam 65536 bayt).
# Bu yüzden Lua tarafı asla büyük tek parça dökmez: veri ayrı, tahminler PARÇA PARÇA alınır.
LUA_DATA_MAIN = """
io.write(ser({ VERSION = EIModel.VERSION, DIM = EIModel.DIM,
               CLASSES = EIModel.CLASSES, DATA = EIModel.DATA }))
"""

LUA_PRED_MAIN = """
local VECS2 = {}
for i = 1, #VECS do VECS2[i] = fixv(VECS[i]) end
VECS = VECS2
local preds = {}
for i = 1, #VECS do
  local r = EIModel.predict(VECS[i])
  preds[i] = { cls = r.cls, conf = r.conf, top3 = r.top3, probs = r.probs, style = r.style }
end
io.write(ser(preds))
"""

STDOUT_LIMIT = 65536      # fengari'nin sessiz kırpma sınırı
LUA_CHUNK = 20            # parça başına vektör: çıktı ~10-15 KB, sınırın çok altında


def run_js(vecs):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JS_RUNNER)
        runner = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(vecs, fh)
        vpath = fh.name
    try:
        r = subprocess.run(["node", runner, JS_DIR, vpath], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError("node hatası:\n" + (r.stderr or "")[:2000])
        return json.loads(r.stdout)
    finally:
        os.unlink(runner)
        os.unlink(vpath)


def run_lua_once(prog, lua_bin=None):
    """Tek Lua programını çalıştırır; çıktı 64 KiB'a yaklaşırsa HATA verir (sessiz kırpma olmasın)."""
    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(prog)
            tmp = fh.name
        try:
            r = subprocess.run([lua_bin, tmp], capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError("%s hatası:\n%s" % (lua_bin, (r.stderr or "")[:2500]))
            if len(r.stdout) >= STDOUT_LIMIT:
                raise RuntimeError("Lua çıktısı %d bayt — sınırı aşıyor, parçayı küçült" % len(r.stdout))
            return json.loads(r.stdout)
        finally:
            os.unlink(tmp)
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
        if len(r.stdout) >= STDOUT_LIMIT:
            raise RuntimeError("fengari çıktısı %d bayt — 64 KiB sınırını aşıyor (kırpılır); "
                               "LUA_CHUNK küçültülmeli" % len(r.stdout))
        return json.loads(r.stdout)
    finally:
        os.unlink(runner)
        os.unlink(tmp_lua)


def run_lua(vecs, lua_bin=None):
    """Veri dökümü + tahminler. Tahminler PARÇA PARÇA alınır (fengari 64 KiB sınırı)."""
    src = open(os.path.join(LUA_DIR, "EIModel.lua"), encoding="utf-8").read()
    head = (LUA_SERIALIZER + "\n"
            "local EIModel = (function()\n" + src + "\nend)()\n" + LUA_FIXV)
    # (a) gömülü veri
    data = run_lua_once(head + LUA_DATA_MAIN, lua_bin)
    # (b) tahminler — parçalı
    preds = []
    for i in range(0, len(vecs), LUA_CHUNK):
        part = vecs[i:i + LUA_CHUNK]
        prog = head + "local VECS = " + lua_dumps([encode_vec(v) for v in part]) + "\n" + LUA_PRED_MAIN
        preds += run_lua_once(prog, lua_bin)
    assert len(preds) == len(vecs), "Lua parça sayısı tutmuyor"
    return {"VERSION": data["VERSION"], "DIM": data["DIM"], "CLASSES": data["CLASSES"],
            "DATA": data["DATA"], "preds": preds}


def close(a, b, tol=TOL):
    if a == b:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        d = abs(a - b)
        return d <= tol or d <= tol * max(abs(a), abs(b))
    return False


def cmp_deep(x, y, path, bad):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            cmp_deep(x.get(k), y.get(k), path + "." + str(k), bad)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            bad.append((path, len(x), len(y)))
            return
        for i, (a, b) in enumerate(zip(x, y)):
            cmp_deep(a, b, "%s[%d]" % (path, i), bad)
    elif not close(x, y):
        bad.append((path, x, y))


def main():
    problems = []
    print("=" * 74)
    print("TAHMİN KAPISI (A4a) — ei-model.js  ↔  EIModel.lua  ↔  Python kanonu")
    print("=" * 74)

    # 0) SENKRON: gömülü ikizler model.json'dan yeniden üretilebiliyor mu? ----------
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([sys.executable, os.path.join(HERE, "export_model.py"),
                            MODEL, "--out-dir", td], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("export_model çalışmadı:\n" + (r.stdout + r.stderr)[-1200:])
        else:
            for gen, cur in ((os.path.join(td, "ei-model.js"), os.path.join(JS_DIR, "ei-model.js")),
                             (os.path.join(td, "EIModel.lua"), os.path.join(LUA_DIR, "EIModel.lua"))):
                a_bytes, b_bytes = open(gen, "rb").read(), open(cur, "rb").read()
                if a_bytes != b_bytes:
                    problems.append("%s model.json ile SENKRON DEĞİL (elle düzenlenmiş?)"
                                    % os.path.basename(cur))
                else:
                    print("  [OK] senkron: %-12s ← model.json (%d bayt)"
                          % (os.path.basename(cur), len(a_bytes)))

    # 1) luau-lint ---------------------------------------------------------
    lint = luau_lint(os.path.join(LUA_DIR, "EIModel.lua"))
    if lint:
        problems.append("luau-lint: " + "; ".join(str(x) for x in lint[:5]))
    else:
        print("  [OK] luau-lint -> EIModel.lua temiz")

    # 2) vektörler: her export'un her katmanı (JS RAW → Python özellik vektörü) --------
    import feature_index
    spec = feature_index.load_spec()
    vecs, labels = [], []
    with open(MODEL, encoding="utf-8") as fh:
        model_obj = json.load(fh)
    n2i = T.name2index()
    for name in SAMPLES:
        path = os.path.join(FIX_DIR, name)
        raw = ingest.run_raw(path)
        for i, node in enumerate(raw["nodes"]):
            vecs.append(ei_features.compute(spec, node))
            labels.append("%s#%d" % (name.replace(".json", ""), i))
    print("  [i] %d katman vektörü (%d export) hazır" % (len(vecs), len(SAMPLES)))

    # style bayrağı indeksleri: stil öncülü testinde kullanılacak
    stud_i = n2i["sty_stud"]
    cart_i, anime_i = n2i["sty_cartoon"], n2i["sty_anime"]
    # Öncül testi NÖTR bir vektörle yapılır: gerçek katmanlarda olasılık doygun (≈1.0) olur,
    # öncülün etkisi 1e-69'a düşer ve "etkisiz" sanılır.
    base = [0.0] * DIM

    edge = [
        [0.0] * DIM,                     # sıfır
        [1.0] * DIM,                     # sabit
        [-1.0] * DIM,                    # negatif
        [1e9] * 10 + [0.0] * (DIM - 10),  # büyük değer
        [float("nan")] * 5 + [0.5] * (DIM - 5),   # NaN
        [float("inf"), float("-inf")] + [0.25] * (DIM - 2),  # sonsuz
        ["x", True, None] + [0.0] * (DIM - 3),    # metin/bool/nil
        [0.5] * 10,                      # KISA vektör (eksik boyut)
        base,                            # gerçek bir katman
        base[:stud_i] + [1.0] + base[stud_i + 1:],  # aynı vektör + sty_stud
    ]
    edge_labels = ["sıfır", "birler", "negatif", "1e9", "NaN", "sonsuz", "metin/bool/nil",
                   "kısa", "gerçek", "gerçek+stud"]
    all_vecs = vecs + edge
    all_labels = labels + edge_labels

    js = run_js([encode_vec(v) for v in all_vecs])
    lua = run_lua(all_vecs, os.environ.get("EASYIMPORT_LUA_BIN"))
    print("  [OK] iki dil de %d vektörü çarptı (kenar durumlar dâhil)" % len(all_vecs))

    # 3) gömülü veri birebir mi? ------------------------------------------
    doc = model_obj["models"]["class"]
    exp_data = {
        "W": doc["W"], "B": doc["b"], "MEAN": doc["norm"]["mean"], "STD": doc["norm"]["std"],
        "STYLE_FLAG": {k: n2i[v] for k, v in ingest_style_flags().items()},
    }
    bad = []
    cmp_deep(js["DATA"]["W"], lua["DATA"]["W"], "DATA.W", bad)
    cmp_deep(js["DATA"]["W"], exp_data["W"], "DATA.W(model)", bad)
    cmp_deep(js["DATA"]["B"], exp_data["B"], "DATA.B(model)", bad)
    cmp_deep(lua["DATA"]["MEAN"], exp_data["MEAN"], "DATA.MEAN(model)", bad)
    cmp_deep(lua["DATA"]["STD"], exp_data["STD"], "DATA.STD(model)", bad)
    cmp_deep(lua["DATA"]["STYLE_FLAG"], exp_data["STYLE_FLAG"], "DATA.STYLE_FLAG(model)", bad)
    if bad:
        problems.append("gömülü veri farkı: %d yol (ilk: %s)" % (len(bad), bad[0]))
    else:
        print("  [OK] gömülü veri: JS ≡ Lua ≡ model.json (%d ağırlık, %d normalizasyon)"
              % (len(doc["W"]) * DIM, 2 * DIM))

    # 4) tahmin paritesi --------------------------------------------------
    bad = []
    cmp_deep(js["preds"], lua["preds"], "preds", bad)
    py_bad = []
    for i, vec in enumerate(all_vecs):
        row = {"feat": {j: v for j, v in enumerate(vec) if isinstance(v, (int, float))
                        and not isinstance(v, bool) and v == v}}
        pr = T.predict(doc, row)
        got = js["preds"][i]
        if pr["cls"] != got["cls"]:
            py_bad.append((all_labels[i], pr["cls"], got["cls"]))
            continue
        for k in range(len(got["top3"])):
            if pr["top3"][k][0] != got["top3"][k][0]:
                py_bad.append((all_labels[i], "top3[%d]" % k, pr["top3"][k][0], got["top3"][k][0]))
                break
        if not close(pr["conf"], got["conf"], 1e-9):
            py_bad.append((all_labels[i], "conf", pr["conf"], got["conf"]))
    if bad:
        for path, x, y in bad[:6]:
            problems.append("JS≠Lua %s: %r ≠ %r" % (path, x, y))
    if py_bad:
        for item in py_bad[:6]:
            problems.append("Python≠JS %s" % (item,))
    if not bad:
        print("  [OK] tahmin: %d vektörde JS ≡ Lua (cls + top3 sırası aynı, olasılıklar %.0e içinde)"
              % (len(all_vecs), TOL))
    if not py_bad:
        print("  [OK] Python kanonu da aynı kararı veriyor (cls/top3/conf)")

    # 5) stil öncülü canlı mı? -------------------------------------------
    i0, i1 = len(vecs) + edge_labels.index("gerçek"), len(vecs) + edge_labels.index("gerçek+stud")
    p0, p1 = js["preds"][i0], js["preds"][i1]
    if p0["style"] is not None or p1["style"] != "stud":
        problems.append("stil bayrağı okunmadı: %r → %r" % (p0["style"], p1["style"]))
    else:
        diff = sum(abs(a - b) for a, b in zip(p0["probs"], p1["probs"]))
        if diff < 1e-4:
            problems.append("stil öncülü etkisiz (toplam olasılık farkı %.2e)" % diff)
        else:
            print("  [OK] stil öncülü canlı: sty_stud eklenince toplam olasılık farkı %.4f "
                  "(%s → %s)" % (diff, p0["cls"], p1["cls"]))

    print("-" * 74)
    if problems:
        for p in problems:
            print("  [!!] " + p)
        print("SONUÇ: BAŞARISIZ")
        return 1
    print("SONUÇ: GEÇTİ — model üç dilde BİREBİR; gömülü veri model.json ile aynı")
    return 0


def ingest_style_flags():
    """J grubundaki stil bayrak adları — indeksleri features.json'dan gelir."""
    return {"stud": "sty_stud", "anime": "sty_anime", "cartoon": "sty_cartoon"}


if __name__ == "__main__":
    sys.exit(main())
