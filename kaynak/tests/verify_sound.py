#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: hover ve tıklama sesleri (sahte Roblox ortamında)
  • her GuiButton: üzerine gelince UzerineGelmeSesi (139719503904449) çalar
  • tıklayınca KullanSesi (87437544236708) çalar
  • animasyon bağlaması olmasa bile çalışır (ayrı EI_Sesler betiği)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import verify_anim as V  # noqa: E402

EXTRA = r"""
local _ni = Instance.new
Instance.new = function(cls)
  local o = _ni(cls)
  if cls == "Sound" then
    o.Play = function(self) LOG[#LOG + 1] = "PLAY|" .. tostring(self.SoundId) end
    o.Destroy = function(self) end
    o.Ended = { Connect = function(self, f) end }
  end
  return o
end
"""


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    src = V.module_src()
    prog = (
        "local EIAnim = (function()\n" + src + "\nend)()\n"
        + V.MOCK + "\n" + EXTRA
        + "ROOT.children = {}\n"
        + "local function mk(cls, name, id)\n"
        + "  local o = makeInst(cls, name); o.attrs.EI_Id = id; addChild(ROOT, o)\n"
        + "  o.MouseButton1Click = { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f end }\n"
        + "  return o\n"
        + "end\n"
        + "local BTN = mk('TextButton', 'Buton', 1); mk('Frame', 'Panel', 2)\n"
        + "local SRC = EIAnim.buildSoundSource()\n"
        + "local chunk, err = load(SRC, 'EI_Sesler')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "LOG[#LOG + 1] = 'MARK|enter'\n"
        + "for _, f in ipairs(BTN.MouseEnter.fns) do f() end\n"
        + "LOG[#LOG + 1] = 'MARK|click'\n"
        + "for _, f in ipairs(BTN.MouseButton1Click.fns) do f() end\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "ses betiği derlenir ve yüklenir")
    secs = {}
    cur = "pre"
    for ln in out.split("\n"):
        if ln.startswith("MARK|"):
            cur = ln[5:]
            secs[cur] = []
        elif ln:
            secs.setdefault(cur, []).append(ln)
    check("PLAY|rbxassetid://139719503904449" in secs.get("enter", []),
          "üzerine gelince hover sesi çalar (139719503904449)")
    check("PLAY|rbxassetid://87437544236708" in secs.get("click", []),
          "tıklayınca tıklama sesi çalar (87437544236708)")
    check(not any(l.startswith("PLAY|") for l in secs.get("pre", [])),
          "yükleme anında ses çalmaz")
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — hover ve tıklama sesleri hazır ID'lerle çalışır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
