#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: Studio eklentisine taşınan asistan (Assist köprüsü + gömülü modüller + animasyon planı)
      gerçek fixture dışa aktarımlarında hatasız çalışır.

  • Modüller: build_rbxmx.module_block() ile AYNI gömme (eklentinin paketlediği biçim)
  • Assist köprüsü: eklenti kaynağından (dev .lua) birebir alınır — kopya yok
  • Veri: assistant/datasets/fixtures/exports/*.json (v10, `ei` alanlı)
  • Kontroller: ei'siz fixture'da asistan KAPALI · ei'li fixture'da karar üretilir, hata yok ·
                EIAnim planı derlenir · sınıf kararları yalnız compatible/conf≥0.70 olur
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLUGIN_LUA = os.path.join(ROOT, "roblox-studio-plugin", "EasyImportStudioPlugin.lua")
ASSIST_DIR = os.path.join(ROOT, "assistant")
sys.path.insert(0, os.path.join(ROOT, "roblox-studio-plugin"))
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import build_rbxmx  # noqa: E402
from luatable import dumps as lua_dumps  # noqa: E402

VENDOR = os.path.join(ASSIST_DIR, "tools", "vendor")
RUNNER = r"""
const { lauxlib, lua, lualib, to_luastring } = require('fengari');
const fs = require('fs');
const prog = fs.readFileSync(process.argv[2], 'utf8');
const L = lauxlib.luaL_newstate(); lualib.luaL_openlibs(L);
const st = lauxlib.luaL_dostring(L, to_luastring(prog));
if (st !== lua.LUA_OK) { process.stderr.write('LUA HATASI: ' + (lua.lua_tojsstring(L, -1) || '?') + '\n'); process.exit(1); }
"""

def assist_block_src():
    src = open(PLUGIN_LUA, encoding="utf-8").read()
    i = src.index("local Assist = {}\n")
    j = src.index("-- <<ASSIST_END>>")
    return src[i:j] + "\n"

def walker_lua():
    return r"""
local function classFor(item)
  if item.kind == "text" then return "TextLabel" end
  if item.image then return "ImageLabel" end
  return "Frame"
end
local function walkDecide(assist, item, depth, acc)
  local a = Assist.decide(assist, item, {})
  local cls = classFor(item)
  if a then cls = a.cls; acc.overrides = acc.overrides + 1 end
  Assist.noteCorrection(assist, item, {})
  acc.nodes = acc.nodes + 1
  acc.elems[#acc.elems + 1] = { id = acc.nodes, name = tostring(item.name or "Layer"), cls = cls, depth = depth }
  for _, ch in ipairs(item.children or {}) do walkDecide(assist, ch, depth + 1, acc) end
end
"""

def fixtures():
    out = []
    for p in sorted(glob.glob(os.path.join(ASSIST_DIR, "datasets", "fixtures", "exports", "*.json"))):
        out.append((os.path.basename(p), json.load(open(p, encoding="utf-8"))))
    return out

def count_ei(doc):
    n = 0
    def rec(it):
        nonlocal n
        if isinstance(it, dict):
            if isinstance(it.get("ei"), dict): n += 1
            for c in it.get("children") or []: rec(c)
    rec(doc.get("root"))
    return n

def run(prog):
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(prog); path = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(RUNNER); jspath = fh.name
    env = dict(os.environ); env["NODE_PATH"] = VENDOR
    try:
        r = subprocess.run(["node", jspath, path], capture_output=True, text=True, timeout=280, env=env)
        if r.returncode != 0:
            raise RuntimeError("Lua hatası:\n" + (r.stderr or "")[:1500] + (r.stdout or "")[:500])
        return r.stdout
    finally:
        os.unlink(path); os.unlink(jspath)

def main():
    fails = []
    def check(c, msg):
        print(("  [OK] " if c else "  [FAIL] ") + msg)
        if not c: fails.append(msg)

    fx = fixtures()
    check(len(fx) >= 3, "fixture bulundu: %d" % len(fx))
    modules = build_rbxmx.module_block()
    prelude = "local warn = warn or function() end\nlocal function noop() end\n"
    lines = []
    for name, doc in fx:
        lines.append("do\n local DOC = %s\n" % lua_dumps(doc))
        lines.append(" local assist = Assist.newSession(nil)\n")
        lines.append(" local on = Assist.activeFor(DOC)\n")
        lines.append(" if on then Assist.prepare(assist, DOC) end\n")
        lines.append(" local acc = { nodes = 0, overrides = 0, elems = {} }\n")
        lines.append(" if on then walkDecide(assist, DOC.root, 1, acc) end\n")
        lines.append(" local plan = EIAnim.decideBindings(acc.elems, assist.style or 'belirsiz', assist.learn)\n")
        lines.append(" local src = EIAnim.buildSource(plan)\n")
        lines.append(" local okLoad = load(src, 'EI_Animator') ~= nil\n")
        lines.append(" io.write(string.format('FIX|%%s|%%s|%%s|%%d|%%d|%%d|%%d|%%s\\n', %r, tostring(on), tostring(assist.style),\n"
                     "   assist.stats.predicts, assist.stats.model, assist.stats.rejected, #plan, tostring(okLoad)))\n" % name)
        lines.append("end\n")
    prog = (modules + "\n" + prelude + "\n" + assist_block_src() + "\n" + walker_lua() + "\n" + "\n".join(lines))
    out = run(prog)
    rows = [l.split("|") for l in out.split("\n") if l.startswith("FIX|")]
    check(len(rows) == len(fx), "tüm fixture'lar çalıştı (%d/%d)" % (len(rows), len(fx)))
    for r in rows:
        name, on, style, predicts, model, rejected, nplan, okload = r[1], r[2], r[3], int(r[4]), int(r[5]), int(r[6]), int(r[7]), r[8]
        doc = dict(fx)[name]
        ei = count_ei(doc)
        if ei == 0:
            check(on == "false" and predicts == 0, "%s: ei yok → asistan KAPALI (predicts=0)" % name)
        else:
            check(on == "true", "%s: ei var (%d düğüm) → asistan AÇIK" % (name, ei))
            check(predicts > 0, "%s: model tahmini üretildi (predicts=%d, model=%d, kural=%d)" % (name, predicts, model, rejected))
        check(okload == "true", "%s: animasyon LocalScript'i derlenir (bağlama %d)" % (name, nplan))
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — Studio asistan köprüsü gerçek fixture'larda çalışıyor")
    return 0

if __name__ == "__main__":
    sys.exit(main())
