#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: P1 davranışları üretilen LocalScript'te (sahte Roblox ortamında)
  • kalıcı seçim grubu: tıklama seçimi taşır; önceki seçim kapanır; aynı öğeye tekrar tıklama bırakır
  • sürekli döngü: döngü tween'i RepeatCount = -1 ile kurulur
  • kaskad: gecikme (TweenInfo.delay) bağlamadan gelir
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import build_anim_lua as B  # noqa: E402
import verify_anim as V  # noqa: E402
from verify_anim_spec import lua_val  # noqa: E402


def specs_for(ids):
    anims, _ = B.convert(json.load(open(B.LIB, encoding="utf-8")))
    return {"_Animasyon %d" % (i + 1): {"tracks": anims[aid]["tracks"]} for i, aid in enumerate(ids)}


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    names = ["select_outline_pop", "loop_wiggle_icon", "enter_fade"]
    specs = specs_for(names)
    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n"
        + "Color3 = { new = function(r, g, b) return { r = r, g = g, b = b } end, fromRGB = function(r, g, b) return { r = r, g = g, b = b } end }\n"
        + "local _ti = TweenInfo.new\n"
        + "TweenInfo.new = function(d, s, dir, rep, rev, dl) LOG[#LOG + 1] = 'DELAY|' .. tostring(dl) .. '|' .. tostring(rep); return _ti(d, s, dir, rep, rev, dl) end\n"
        + "ROOT.children = {}\n"
        + "local function mk(cls, name, id)\n"
        + "  local o = makeInst(cls, name); o.attrs.EI_Id = id; addChild(ROOT, o)\n"
        + "  o.MouseButton1Click = { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f end }\n"
        + "  return o\n"
        + "end\n"
        + "mk('TextButton', 'Tab_A', 12); mk('TextButton', 'Tab_B', 13)\n"
        + "mk('ImageLabel', 'Ikon', 5); mk('TextLabel', 'Baslik', 3)\n"
        + "local BIND = { { id = 12, selA = '_Animasyon 1', sel = 21 }, { id = 13, selA = '_Animasyon 1', sel = 21 },"
        + " { id = 5, loop = '_Animasyon 2' }, { id = 3, show = '_Animasyon 3', delay = 0.12 } }\n"
        + "local SPECS = " + lua_val(specs) + "\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, SPECS)\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "local function byName(n) for _, d in ipairs(ALL) do if d.Name == n then return d end end end\n"
        + "local function click(n) local d = byName(n); for _, f in ipairs(d.MouseButton1Click.fns) do f() end end\n"
        + "LOG[#LOG + 1] = 'MARK|click A'; click('Tab_A')\n"
        + "LOG[#LOG + 1] = 'MARK|click B'; click('Tab_B')\n"
        + "LOG[#LOG + 1] = 'MARK|click B again'; click('Tab_B')\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "üretilen LocalScript (P1 bağlamaları ile) derlenir ve yüklenir")
    lines = [ln for ln in out.split("\n") if ln]
    # bölümleri MARK'lara göre ayır
    sections, cur = {}, None
    for ln in lines:
        if ln.startswith("MARK|"):
            cur = ln[5:]
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(ln)

    def thickness_goals(sec):
        return [ln.split("|")[4] for ln in sec if ln.startswith("TWEEN|") and "|Thickness|" in ln]

    gA = thickness_goals(sections.get("click A", []))
    gB = thickness_goals(sections.get("click B", []))
    gBB = thickness_goals(sections.get("click B again", []))
    check(gA == ["3"], "A'ya tıklama: çerçeve açılır (kalınlık → 3) %s" % gA)
    check(gB == ["0", "3"], "B'ye tıklama: A kapanır (0), B açılır (3) %s" % gB)
    check(gBB == ["0"], "B'ye tekrar tıklama: seçim bırakılır (0) %s" % gBB)

    loop_lines = [ln for ln in lines if ln.startswith("TWEEN|Ikon|") and "|Rotation|" in ln]
    check(loop_lines and loop_lines[0].split("|")[4] == "-6", "döngü: ikon Rotation → -6 (sallanma)")
    check(any(ln.startswith("DELAY|") and ln.split("|")[2] == "-1" for ln in lines),
          "döngü TweenInfo'su RepeatCount = -1 (sürekli)")
    check(any(ln == "DELAY|0.12|0" for ln in lines),
          "kaskad: gecikme 0.12 TweenInfo'ya geçer (sıralı giriş)")

    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — P1 seçim grubu, sürekli döngü ve kaskad sahte Roblox'ta çalışır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
