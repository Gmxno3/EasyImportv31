#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: tasarım öğesiyle efekt (sahte Roblox ortamında)
  • kapsayıcıdaki "fx" şablonu gizlenir; yağmur, şablonun KOPYALARINI düşürür (Clone + Position tween)
  • buton basınca patlama: şablonun 10 kopyası merkezden dağılır
  • dev hale: sürekli nefes alır (Size, RepeatCount -1)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import verify_anim as V  # noqa: E402


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n"
        + "ROOT.children = {}\n"
        + "local function mk(cls, name, id)\n"
        + "  local o = makeInst(cls, name); o.attrs.EI_Id = id; o.ZIndex = 1; addChild(ROOT, o)\n"
        + "  o.FindFirstChild = function(self, n) for _, c in ipairs(self.children) do if c.Name == n then return c end end return nil end\n"
        + "  o.GetChildren = function(self) return self.children end\n"
        + "  o.MouseButton1Down = o.MouseButton1Down or { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f end }\n"
        + "  return o\n"
        + "end\n"
        + "local CONT = mk('Frame', 'Hazine', 1)\n"
        + "local TPL = makeInst('ImageLabel', 'Coin_fx'); TPL.attrs.EI_Id = 4; TPL.ZIndex = 1; addChild(CONT, TPL)\n"
        + "TPL.Clone = function(self) local c = makeInst('ImageLabel', 'Coin_clone'); return c end\n"
        + "local BTN = mk('TextButton', 'Buton', 2); mk('Frame', 'Hale', 3)\n"
        + "local BTPL = makeInst('ImageLabel', 'Ikon_fx'); BTPL.attrs.EI_Id = 5; BTPL.ZIndex = 1; addChild(BTN, BTPL)\n"
        + "BTPL.Clone = function(self) return makeInst('ImageLabel', 'Burst_clone') end\n"
        + "local BIND = { { id = 1, fx = 'fall' }, { id = 4, fx = 'tpl' }, { id = 2, fx = 'burst' }, { id = 5, fx = 'tpl' }, { id = 3, fx = 'orb' } }\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, {})\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "LOG[#LOG + 1] = 'VIS|' .. tostring(TPL.Visible)\n"
        + "LOG[#LOG + 1] = 'MARK|press'\n"
        + "local function byName(n) for _, d in ipairs(ALL) do if d.Name == n then return d end end end\n"
        + "for _, f in ipairs(byName('Buton').MouseButton1Down.fns) do f() end\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "şablonlu efekt LocalScript'i derlenir ve yüklenir")
    lines = [ln for ln in out.split("\n") if ln]
    pre, post, seen = [], [], False
    for ln in lines:
        if ln.startswith("MARK|press"):
            seen = True
            continue
        (post if seen else pre).append(ln)

    check(any(ln == "VIS|false" for ln in pre), "şablon (Coin_fx) gizlendi (Visible = false)")
    rain = [ln for ln in pre if ln.startswith("TWEEN|Coin_clone|ImageLabel|Position|")]
    check(len(rain) >= 1, "yağmur: şablonun kopyası (Coin_clone) düşer (Position tween'i: %d)" % len(rain))
    check(any(ln.startswith("TWEEN|Coin_clone|") and "|Rotation|" in ln for ln in pre),
          "yağmur: kopyalar döner (Rotation)")
    burst = [ln for ln in post if ln.startswith("TWEEN|Burst_clone|ImageLabel|Position|")]
    check(len(burst) >= 10, "patlama: basınca düğmenin içindeki şablonun 10 kopyası dağılır (%d)" % len(burst))
    orb = [ln for ln in pre if ln.startswith("TWEEN|Frame|Frame|Size|") and ln.split("|")[8] == "-1"]
    check(len(orb) >= 1, "dev hale: Size tween'i sonsuz tekrar (RepeatCount -1)")
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — tasarım öğesi kopyalanır, arka planda oynar, basınca patlar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
