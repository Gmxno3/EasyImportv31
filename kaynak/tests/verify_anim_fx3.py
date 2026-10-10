#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: birden çok efekt resmi (şablon) → her parça bunlardan rastgele birini kopyalar.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import verify_anim as V  # noqa: E402

PROG_EXTRA = r"""
local function ff(self, n) for _, c in ipairs(self.children) do if c.Name == n then return c end end return nil end
"""


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n" + PROG_EXTRA
        + "ROOT.children = {}\n"
        + "local C = makeInst('Frame', 'Hazine', 1); C.attrs.EI_Id = 1; C.ZIndex = 1; C.FindFirstChild = ff; C.GetChildren = function(self) return self.children end; addChild(ROOT, C)\n"
        + "local A = makeInst('ImageLabel', 'fx_Hazine_1'); A.attrs.EI_FxTpl = true; A.ZIndex = 1; addChild(C, A)\n"
        + "A.Clone = function(self) return makeInst('ImageLabel', 'Kopya_A') end\n"
        + "local B = makeInst('ImageLabel', 'fx_Hazine_2'); B.attrs.EI_FxTpl = true; B.ZIndex = 1; addChild(C, B)\n"
        + "B.Clone = function(self) return makeInst('ImageLabel', 'Kopya_B') end\n"
        + "local BIND = { { id = 1, fx = 'burst' } }\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, {}, {})\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "şablonlu efekt betiği derlenir")
    # her parça için tek konum (Position) tween'i; diğer satırlar döndürme/saydamlık
    a = sum(1 for ln in out.split("\n") if ln.startswith("TWEEN|Kopya_A|") and "|Position|" in ln)
    b = sum(1 for ln in out.split("\n") if ln.startswith("TWEEN|Kopya_B|") and "|Position|" in ln)
    check(a >= 1 and b >= 1, "patlama iki şablondan da kopya üretir (A=%d, B=%d)" % (a, b))
    check(a + b == 10, "toplam 10 parça (konum tween'i sayısı: %d)" % (a + b))
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — birden çok efekt resmi rastgele kopyalanır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
