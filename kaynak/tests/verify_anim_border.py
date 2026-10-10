#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: kenarlık dönüşü (loop_border_spin) — UIStroke içindeki UIGradient sonsuz döner.
  • kenarlık/gradyan yoksa oluşturulur; varsa mevcut gradyan kullanılır
  • Rotation 0 → 360, RepeatCount -1 (kesintisiz)
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


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    anims, _ = B.convert(json.load(open(B.LIB, encoding="utf-8")))
    specs = {"_Animasyon 1": {"tracks": anims["loop_border_spin"]["tracks"]}}
    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n"
        + "Color3 = { new = function(r, g, b) return { r = r, g = g, b = b } end, fromRGB = function(r, g, b) return { r = r, g = g, b = b } end }\n"
        + "ROOT.children = {}\n"
        + "local A = makeInst('Frame', 'Kart_Yok', 30); A.attrs.EI_Id = 30; addChild(ROOT, A)\n"
        + "local B2 = makeInst('Frame', 'Kart_Var', 31); B2.attrs.EI_Id = 31; addChild(ROOT, B2)\n"
        + "local st = makeInst('UIStroke', 'UIStroke'); addChild(B2, st)\n"
        + "local gr = makeInst('UIGradient', 'UIGradient'); addChild(st, gr)\n"
        + "local BIND = { { id = 30, loop = '_Animasyon 1' }, { id = 31, loop = '_Animasyon 1' } }\n"
        + "local SPECS = " + lua_val(specs) + "\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, SPECS)\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "kenarlık animasyonu derlenir ve yüklenir")
    tw = [ln.split("|") for ln in out.split("\n") if ln.startswith("TWEEN|UIGradient|")]
    check(len(tw) == 2, "iki öğe için iki gradyan tween'i (yoksa oluşturulan + mevcut): %d" % len(tw))
    check(all(t[3] == "Rotation" and t[4] == "360" for t in tw), "gradyan Rotation → 360 döner")
    check(all(t[8] == "-1" for t in tw), "tekrar sonsuz (RepeatCount -1)")
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — kenarlık gradyanı sonsuz döner (sahte Roblox)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
