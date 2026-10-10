#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: Framewisp benzeri parametreli efektler (sahte Roblox ortamında)
  • _smooth: buton üzerine gelince hover ölçeği, basınca press ölçeği, çıkınca 1'e döner
  • _gleam: metin üzerinde parlak bant UIGradient.Offset ile -1 → 1 kayar; süre = sweep parametresi
  • _fall: süre = seconds parametresi (kaydırıcıdan)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import verify_anim as V  # noqa: E402

EXTRA = r"""
NumberSequenceKeypoint = { new = function(t, v) return { t = t, v = v } end }
NumberSequence = { new = function(list) return { kp = list } end }
ColorSequence = { new = function(c) return { c = c } end }
"""


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n" + EXTRA
        + "ROOT.children = {}\n"
        + "local function mk(cls, name, id)\n"
        + "  local o = makeInst(cls, name); o.attrs.EI_Id = id; o.ZIndex = 1; addChild(ROOT, o)\n"
        + "  o.FindFirstChild = function(self, n) for _, c in ipairs(self.children) do if c.Name == n then return c end end return nil end\n"
        + "  o.GetChildren = function(self) return self.children end\n"
        + "  o.MouseButton1Up = o.MouseButton1Up or { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f end }\n"
        + "  return o\n"
        + "end\n"
        + "local BTN = mk('TextButton', 'Buton', 1)\n"
        + "local TXT = mk('TextLabel', 'Yazi', 2)\n"
        + "local CONT = mk('Frame', 'Hazine', 3)\n"
        + "local BIND = {\n"
        + "  { id = 1, fx = 'smooth', params = { hover = 1.2, press = 0.8 } },\n"
        + "  { id = 2, fx = 'gleam', params = { sweep = 2, pause = 0.5, width = 0.2 } },\n"
        + "  { id = 3, fx = 'fall', params = { count = 4, seconds = 8, fade = 0.5, smallest = 0.5, largest = 0.9 } },\n"
        + "}\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, {})\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "LOG[#LOG + 1] = 'MARK|enter'\n"
        + "for _, f in ipairs(BTN.MouseEnter.fns) do f() end\n"
        + "LOG[#LOG + 1] = 'MARK|down'\n"
        + "for _, f in ipairs(BTN.MouseButton1Down.fns) do f() end\n"
        + "LOG[#LOG + 1] = 'MARK|leave'\n"
        + "for _, f in ipairs(BTN.MouseLeave.fns) do f() end\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "parametreli efekt betiği derlenir ve yüklenir")
    secs = {}
    cur = "pre"
    for ln in out.split("\n"):
        if ln.startswith("MARK|"):
            cur = ln[5:]
            secs[cur] = []
        elif ln:
            secs.setdefault(cur, []).append(ln)

    enter = [ln for ln in secs.get("enter", []) if ln.startswith("TWEEN|UIScale|UIScale|Scale|")]
    check(enter and enter[-1].split("|")[4] == "1.2", "_smooth: üzerine gelince ölçek hover=1.2 (%s)" % (enter and enter[-1].split("|")[4]))
    down = [ln for ln in secs.get("down", []) if ln.startswith("TWEEN|UIScale|UIScale|Scale|")]
    check(down and down[-1].split("|")[4] == "0.8", "_smooth: basınca ölçek press=0.8 (%s)" % (down and down[-1].split("|")[4]))
    leave = [ln for ln in secs.get("leave", []) if ln.startswith("TWEEN|UIScale|UIScale|Scale|")]
    check(leave and leave[-1].split("|")[4] == "1", "_smooth: çıkınca ölçek 1'e döner (%s)" % (leave and leave[-1].split("|")[4]))

    gl = [ln for ln in out.split("\n") if ln.startswith("TWEEN|UIGradient|UIGradient|Offset|")]
    check(len(gl) >= 1 and gl[0].split("|")[4] == "(1,0)" and gl[0].split("|")[5] == "2",
          "_gleam: metin bandı Offset (1,0)'a 2 sn'de kayar (%s)" % (gl and gl[0]))

    fall = [ln for ln in out.split("\n") if ln.startswith("TWEEN|Frame|Frame|Position|")]
    check(len(fall) >= 1 and fall[0].split("|")[5] == "8.0" or (len(fall) >= 1 and float(fall[0].split("|")[5]) == 8),
          "_fall: düşme süresi kaydırıcıdan 8 sn (%s)" % (fall and fall[0].split("|")[5]))
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — büyüme, metin parıltısı ve kaydırıcı süreleri sahte Roblox'ta çalışır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
