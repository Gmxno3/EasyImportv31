#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2 KAPISI — RAW ÇIKARICI DETERMİNİZM TESTİ  [A2]

Aynı Figma export dökümanı için JS (ei-raw.js) ve Lua (EIRaw.lua) çıkarıcıları
BİREBİR aynı RAW kayıtlarını üretmek ZORUNDADIR. Studio'da çalışacak olan
Lua sürümü olduğu için bu test, A1'in determinizm kapısı kadar kritiktir.

Lua, Node içinde çalışan gerçek bir Lua 5.3 VM (fengari, tools/vendor altında
gömülü) ile koşturulur. Ağ erişimi yoktur.

Kullanım:
    python tools/verify_extract.py
    EASYIMPORT_LUA_BIN=lua5.3 python tools/verify_extract.py

Çıkış: 0 = geçti, 1 = başarısız
"""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from luatable import dumps as lua_dumps  # noqa: E402
from verify_runtime import luau_lint        # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")
FIX_DIR = os.path.join(ROOT, "datasets", "fixtures", "exports")
VENDOR = os.path.join(HERE, "vendor")

# Tüm fixture'lar (yeni örnek eklendiğinde kapı otomatik kapsar)
SAMPLES = sorted(f for f in os.listdir(FIX_DIR) if f.endswith(".json"))

TOL_ABS = 1e-12
TOL_REL = 1e-12

# ---------------------------------------------------------------------------
JS_RUNNER = r"""
const EIRaw = require(process.argv[2] + '/ei-raw.js');
const fs = require('fs');
const doc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = EIRaw.extract(doc);
process.stdout.write(JSON.stringify({ gui: out.gui, nodes: out.nodes }));
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

# Lua tarafının çıktıyı JSON olarak yazması için minimal bir serileştirici.
# (yalnızca test içindir; gönderilen çalışma zamanına girmez)
LUA_SERIALIZER = r"""
local function esc(s)
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end
local function ser(v)
  local t = type(v)
  if t == 'nil' then return 'null'
  elseif t == 'boolean' then return v and 'true' or 'false'
  elseif t == 'number' then
    if v ~= v then return '0' end
    if v == math.huge then return '1e308' end
    if v == -math.huge then return '-1e308' end
    return string.format('%.17g', v)
  elseif t == 'string' then return '"' .. esc(v) .. '"'
  elseif t == 'table' then
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

LUA_MAIN = """
local out = EIRaw.extract(DOC)
io.write('{"gui":' .. ser(out.gui) .. ',"nodes":[')
for i = 1, #out.nodes do
  if i > 1 then io.write(',') end
  io.write(ser(out.nodes[i]))
end
io.write(']}\\n')
"""


# ---------------------------------------------------------------------------
def run_js(path):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(JS_RUNNER)
        tmp = fh.name
    try:
        r = subprocess.run(["node", tmp, JS_DIR, path],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("node hatası:\n" + (r.stderr or "")[:2000])
        return json.loads(r.stdout)
    finally:
        os.unlink(tmp)


def run_lua(path, lua_bin=None):
    with open(os.path.join(LUA_DIR, "EIRaw.lua"), encoding="utf-8") as fh:
        lib_src = fh.read()
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    prog = (
        LUA_SERIALIZER + "\n"
        "local EIRaw = (function()\n" + lib_src + "\nend)()\n"
        "local DOC = " + lua_dumps(doc) + "\n"
        + LUA_MAIN
    )

    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(prog)
            tmp_lua = fh.name
        try:
            r = subprocess.run([lua_bin, tmp_lua], capture_output=True,
                               text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError("%s hatası:\n%s" % (lua_bin, (r.stderr or "")[:2000]))
            raw = r.stdout
        finally:
            os.unlink(tmp_lua)
    else:
        if not os.path.isdir(os.path.join(VENDOR, "fengari")):
            raise RuntimeError("fengari bulunamadı: %s" % VENDOR)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(FENGARI_RUNNER)
            tmp_js = fh.name
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(prog)
            tmp_lua = fh.name
        try:
            env = dict(os.environ)
            env["NODE_PATH"] = VENDOR
            r = subprocess.run(["node", tmp_js, tmp_lua], capture_output=True,
                               text=True, timeout=300, env=env)
            if r.returncode != 0:
                raise RuntimeError("fengari hatası:\n" + (r.stderr or "")[:3000])
            raw = r.stdout
        finally:
            os.unlink(tmp_js)
            os.unlink(tmp_lua)
    return json.loads(raw.strip().split("\n")[0])


# ---------------------------------------------------------------------------
def cmp_val(x, y, path, bad):
    if isinstance(x, bool) or isinstance(y, bool):
        if bool(x) != bool(y):
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
        denom = max(abs(float(x)), abs(float(y)))
        rel = d / denom if denom > 0 else 0.0
        if d > TOL_ABS and rel > TOL_REL:
            bad.append((path, x, y))
        return
    if x != y:
        bad.append((path, x, y))


def main():
    lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
    print("=" * 70)
    print("A2 KAPISI — RAW ÇIKARICI (JS vs %s)" % (lua_bin or "fengari/Lua 5.3"))
    print("  tolerans: abs %.0e / rel %.0e" % (TOL_ABS, TOL_REL))
    print("=" * 70)

    # 0) Luau kısıtları — Lua çalışma zamanı Studio'da derlenemeyecek bir
    #    şey içeremez.
    hits = luau_lint(os.path.join(LUA_DIR, "EIRaw.lua"))
    if hits:
        print("  [!!] EIRaw.lua — Luau ihlali (%d):" % len(hits))
        for ln, txt, why in hits[:8]:
            print("      satır %-5d %-40s %s" % (ln, txt, why))
        print("-" * 70)
        print("SONUÇ: BAŞARISIZ — Luau uyumluluğu")
        return 1
    print("  [OK] luau-lint -> EIRaw.lua temiz")

    failed = False
    for name in SAMPLES:
        path = os.path.join(FIX_DIR, name)
        if not os.path.isfile(path):
            print("  [!!] %-18s bulunamadı" % name)
            failed = True
            continue
        try:
            js = run_js(path)
        except Exception as exc:
            print("  [!!] %-18s JS hata: %s" % (name, exc))
            failed = True
            continue
        try:
            lua = run_lua(path, lua_bin)
        except Exception as exc:
            print("  [!!] %-18s LUA hata: %s" % (name, str(exc)[:500]))
            failed = True
            continue

        bad = []
        cmp_val(js, lua, name, bad)
        n_nodes = len(js.get("nodes", []))
        n_keys = len(js["nodes"][0]) if n_nodes else 0
        if bad:
            failed = True
            print("  [XX] %-18s %3d düğüm x %3d alan — BAŞARISIZ (%d fark)"
                  % (name, n_nodes, n_keys, len(bad)))
            for p, a, b in bad[:8]:
                sa = json.dumps(a, ensure_ascii=False)[:60]
                sb = json.dumps(b, ensure_ascii=False)[:60]
                print("        %-46s %s != %s" % (p[:46], sa, sb))
            if len(bad) > 8:
                print("        ... ve %d fark daha" % (len(bad) - 8))
        else:
            print("  [OK] %-18s %3d düğüm x %3d alan — birebir aynı"
                  % (name, n_nodes, n_keys))
            g = js["gui"]
            print("        karanlık=%.2f muted=%.2f hue=%.2f efek=%.2f "
                  "grad=%.2f reuse=%.2f img=%.2f 3D=%.2f shine=%.2f"
                  % (g["darknessIndex"], g["mutedBaseRate"], g["hueDiversity"],
                     g["effectDensity"], g["gradientRate"], g["reuseRate"],
                     g["imageDrivenRate"], g["darkerUnderlayRate"],
                     g["shineFrameRate"]))

    print("-" * 70)
    if failed:
        print("SONUÇ: BAŞARISIZ — Lua ve JS aynı RAW'ı üretmiyor")
        return 1
    print("SONUÇ: GEÇTİ — iki dil de birebir aynı RAW'ı üretiyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
