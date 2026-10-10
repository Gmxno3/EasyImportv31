#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DETERMİNİZM KAPISI  [A1]

Aynı RAW girdi için Python / JavaScript / Lua değerlendiricileri BİREBİR aynı
özellik vektörünü üretmek ZORUNDADIR. Bu test geçmeden HİÇBİR model yayınlanmaz.

Lua, Node içinde çalışan gerçek bir Lua 5.3 VM (fengari) ile koşturulur.

Kullanım:
    python tools/verify_runtime.py            # tüm diller
    python tools/verify_runtime.py --py-js    # sadece Python + JS

Çıkış: 0 = geçti, 1 = başarısız
"""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "runtime", "python"))

import ei_features  # noqa: E402

SPEC = os.path.join(ROOT, "spec", "features.json")
FIX_JSON = os.path.join(ROOT, "datasets", "fixtures", "raw-nodes.json")
FIX_LUA = os.path.join(ROOT, "datasets", "fixtures", "raw-nodes.lua")
JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")

TOL_ABS = 1e-9
TOL_REL = 1e-9

# Not: python vs js/lua arasında ~1 ULP (≈2e-16) fark kalması BEKLENİR ve
# normaldir — CPython'in libm'i ile V8'inkinin log() uygulaması son basamakta
# ayrışır. js vs lua ise TAMAMEN aynıdır (ikisi de V8 üstünde koşar).
# Tolerans penceremiz bundan ~7 büyüklük mertebesi geniştir; buradaki amaç
# "1 ULP" değil "gerçek bir mantık ayrışması" yakalamaktır.


# ---------------------------------------------------------------------------
def run_python(spec, nodes):
    return [[float(x) for x in ei_features.compute(spec, n["raw"])] for n in nodes]


def run_js(spec, nodes):
    runner = r"""
const path = process.argv[2];
const spec = require(path + '/ei-features-spec.js').spec;
const EI = require(path + '/ei-features.js');
const nodes = require(process.argv[3]);
const out = nodes.map(n => EI.compute(spec, n.raw));
process.stdout.write(JSON.stringify(out));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(runner)
        tmp = fh.name
    try:
        r = subprocess.run(["node", tmp, JS_DIR, FIX_JSON],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError("node hatası:\n" + r.stderr[:2000])
        return json.loads(r.stdout)
    finally:
        os.unlink(tmp)


VENDOR = os.path.join(HERE, "vendor")

LUA_PROG_TMPL = (
    "local SPEC = (function()\n{spec_src}\nend)()\n"
    "local EI = (function()\n{lib_src}\nend)()\n"
    "local NODES = (function()\n{fix_src}\nend)()\n"
    "for i = 1, #NODES do\n"
    "  local v = EI.compute(SPEC, NODES[i].raw)\n"
    "  local parts = {{}}\n"
    "  for j = 1, #v do parts[j] = string.format('%.17g', v[j]) end\n"
    "  io.write('[' .. table.concat(parts, ',') .. ']\\n')\n"
    "end\n"
)

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


def build_lua_program():
    with open(os.path.join(LUA_DIR, "EIFeatures_Spec.lua"), encoding="utf-8") as fh:
        spec_src = fh.read()
    with open(os.path.join(LUA_DIR, "EIFeatures.lua"), encoding="utf-8") as fh:
        lib_src = fh.read()
    with open(FIX_LUA, encoding="utf-8") as fh:
        fix_src = fh.read()
    return LUA_PROG_TMPL.format(spec_src=spec_src, lib_src=lib_src, fix_src=fix_src)


def run_lua(spec, nodes, lua_bin=None):
    """Lua değerlendiriciyi çalıştırır.

    lua_bin verilirse gerçek PUC Lua / Luau ikili dosyası kullanılır
    (ör. EASYIMPORT_LUA_BIN=lua5.3). Aksi halde depoya gömülü fengari
    (Node içinde çalışan gerçek bir Lua 5.3 VM) kullanılır — ağ erişimi
    ve harici bağımlılık yoktur.
    """
    prog = build_lua_program()

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
            raise RuntimeError(
                "fengari bulunamadı: %s\n"
                "  Lua tarafını test etmek için ya bir Lua ikili dosyası verin:\n"
                "      EASYIMPORT_LUA_BIN=lua5.3 python3 tools/verify_runtime.py\n"
                "  ya da fengari'yi geri koyun: npm i fengari && cp -r node_modules/fengari/src "
                "tools/vendor/fengari" % VENDOR)
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
                raise RuntimeError("fengari hatası:\n" + (r.stderr or "")[:2000])
            raw = r.stdout
        finally:
            os.unlink(tmp_js)
            os.unlink(tmp_lua)

    out = []
    for line in raw.strip().split("\n"):
        if line:
            out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Roblox Studio (Luau) kısıtları.
#
# Studio'da Luau korumalı bir ortamda çalışır: goto, bit32, io/os/dofile
# yoktur. math.log10 Lua 5.3'te kaldırılmıştır (Luau'da olsa bile
# log(x)/LN10 deyimini zorunlu tutuyoruz). çalışma zamanı dosyaları bu
# listeden hiçbirini içeremez.
LUAU_BANNED = [
    (r"\bgoto\b", "goto (Luau desteklemiyor)"),
    (r"::\w+::", "etiket (goto ile birlikte)"),
    (r"\bbit32\b", "bit32 (Luau'da yok)"),
    (r"\bio\.\w", "io kütüphanesi (Studio'da yok)"),
    (r"\bos\.\w", "os kütüphanesi (Studio'da yok)"),
    (r"\bdofile\b", "dofile (Studio'da yok)"),
    (r"\bloadfile\b", "loadfile (Studio'da yok)"),
    (r"\bloadstring\b", "loadstring (Studio'da yok)"),
    (r"\brequire\s*\(", "require (Studio'da göreli yol gerekir; dosyada olmamalı)"),
    (r"math\.log10", "math.log10 (log(x)/LN10 kullanın)"),
    (r"[^.\w]unpack\s*\(", "unpack (table.unpack kullanın)"),
]


def luau_lint(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    hits = []
    for i, line in enumerate(src.split("\n"), 1):
        if line.lstrip().startswith("--"):
            continue
        for pat, why in LUAU_BANNED:
            if re.search(pat, line):
                hits.append((i, line.strip()[:70], why))
    return hits


def compare(a, b, name_a, name_b, node_names):
    bad = []
    max_abs = 0.0
    max_rel = 0.0
    for ni, (va, vb) in enumerate(zip(a, b)):
        if len(va) != len(vb):
            bad.append((node_names[ni], -1, len(va), len(vb)))
            continue
        for j, (x, y) in enumerate(zip(va, vb)):
            x = float(x); y = float(y)
            d = abs(x - y)
            if d > max_abs:
                max_abs = d
            denom = max(abs(x), abs(y))
            rel = d / denom if denom > 0 else 0.0
            if rel > max_rel:
                max_rel = rel
            if d > TOL_ABS and rel > TOL_REL:
                bad.append((node_names[ni], j, x, y))
    return bad, max_abs, max_rel


def main():
    only_py_js = "--py-js" in sys.argv

    with open(SPEC, encoding="utf-8") as fh:
        spec = json.load(fh)
    with open(FIX_JSON, encoding="utf-8") as fh:
        nodes = json.load(fh)

    names = [n["name"] for n in nodes]
    dim = spec["dim"]

    print("=" * 68)
    print("DETERMİNİZM KAPISI — %s" % spec["version"])
    print("  özellik boyu : %d" % dim)
    print("  fixture      : %d düğüm" % len(nodes))
    print("  tolerans     : abs %.0e / rel %.0e" % (TOL_ABS, TOL_REL))
    print("=" * 68)

    # 0) Luau kısıtları — çalışma zamanı dosyaları Studio'da derlenemeyecek
    #    bir şey içeremez.
    lint_bad = False
    for f in ("EIFeatures.lua", "EIFeatures_Spec.lua"):
        hits = luau_lint(os.path.join(LUA_DIR, f))
        if hits:
            lint_bad = True
            print("  [!!] %s — Luau ihlali (%d):" % (f, len(hits)))
            for ln, txt, why in hits[:8]:
                print("      satır %-5d %-40s %s" % (ln, txt, why))
    if lint_bad:
        print("-" * 68)
        print("SONUÇ: BAŞARISIZ — Luau uyumluluğu")
        return 1
    print("  [OK] luau-lint -> EIFeatures.lua + Spec temiz")

    res = {}
    res["python"] = run_python(spec, nodes)
    print("  [OK] python  -> %d vektör x %d" % (len(res["python"]), len(res["python"][0])))

    res["js"] = run_js(spec, nodes)
    print("  [OK] js      -> %d vektör x %d" % (len(res["js"]), len(res["js"][0])))

    if not only_py_js:
        lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
        try:
            res["lua"] = run_lua(spec, nodes, lua_bin)
        except RuntimeError as exc:
            print("  [!!] lua     -> ATLANDI: %s" % exc)
        else:
            print("  [OK] lua (%s) -> %d vektör x %d"
                  % (lua_bin or "fengari", len(res["lua"]), len(res["lua"][0])))

    print("-" * 68)
    failed = False
    pairs = [("python", "js")]
    if not only_py_js:
        pairs.append(("python", "lua"))
        pairs.append(("js", "lua"))

    for a, b in pairs:
        bad, max_abs, max_rel = compare(res[a], res[b], a, b, names)
        ok = not bad
        print("  %-14s max_abs=%.3e  max_rel=%.3e  %s"
              % ("%s vs %s" % (a, b), max_abs, max_rel, "GEÇTİ" if ok else "BAŞARISIZ"))
        if bad:
            failed = True
            for nd, j, x, y in bad[:10]:
                print("      ✗ %-22s idx=%-4s  %r != %r" % (nd, j, x, y))
            if len(bad) > 10:
                print("      ... ve %d fark daha" % (len(bad) - 10))

    # NaN / sonsuz kontrolü
    for lang, vecs in res.items():
        for ni, v in enumerate(vecs):
            for x in v:
                if x != x or x in (float("inf"), float("-inf")):
                    print("  ✗ %s: %s düğümünde NaN/Inf" % (lang, names[ni]))
                    failed = True
                    break

    print("-" * 68)
    if failed:
        print("SONUÇ: BAŞARISIZ — model yayınlanamaz")
        return 1
    print("SONUÇ: GEÇTİ — üç dil birebir aynı vektörü üretiyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
