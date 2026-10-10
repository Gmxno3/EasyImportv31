#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: JSON animasyon tanımlarından Lua üretimi (EIAnim.buildSourceSpec)

  • "_Animasyon N" adları Lua'da güvenli anahtara çevrilir (boşluk → alt çizgi)
  • Üretilen LocalScript derlenir ve sahte Roblox ortamında çalışır:
      giriş tween'i, hover giriş/çıkış ve basma bağlantıları beklendiği gibi
  • Tanımı olmayan referans (_Animasyon 9) sessizce düşer; betik bozulmaz
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "assistant", "tools"))
import build_anim_lua as B  # noqa: E402
import verify_anim as V  # noqa: E402


def specs_from_library(lib_ids):
    anims, _ = B.convert(json.load(open(B.LIB, encoding="utf-8")))
    out = {}
    for i, aid in enumerate(lib_ids, 1):
        out["_Animasyon %d" % i] = {"src": aid, "tracks": anims[aid]["tracks"]}
    return out


def lua_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return "%.6g" % v
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, dict):
        return "{" + ", ".join("[%s] = %s" % (lua_val(k), lua_val(x)) for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "{" + ", ".join(lua_val(x) for x in v) + "}"
    raise TypeError(type(v))


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    specs = specs_from_library(["enter_fade", "press_flash", "hover_scale_up"])
    specs_lua = lua_val({k: {"tracks": v["tracks"]} for k, v in specs.items()})
    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n"
        + "ROOT.children = {}\n"
        + "local F = makeInst('Frame', 'Ana_Panel'); F.attrs.EI_Id = 1; addChild(ROOT, F)\n"
        + "local L = makeInst('TextLabel', 'Baslik'); L.attrs.EI_Id = 2; addChild(ROOT, L)\n"
        + "local BT = makeInst('TextButton', 'Buton_button'); BT.attrs.EI_Id = 3; addChild(ROOT, BT)\n"
        + "local BIND = { { id = 1, show = '_Animasyon 1' }, { id = 2, show = '_Animasyon 9' },"
        + " { id = 3, show = '_Animasyon 1', hover = '_Animasyon 3', press = '_Animasyon 2' } }\n"
        + "local SPECS = " + specs_lua + "\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, SPECS)\n"
        + "io.write('SRCBEGIN\\n', SRC, '\\nSRCEND\\n')\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "for _, d in ipairs(ALL) do\n"
        + "  if d.attrs.EI_Id == 3 then\n"
        + "    for _, f in ipairs(d.MouseEnter.fns) do f() end\n"
        + "    for _, f in ipairs(d.MouseLeave.fns) do f() end\n"
        + "    for _, f in ipairs(d.MouseButton1Down.fns) do f() end\n"
        + "  end\n"
        + "end\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "üretilen LocalScript derlenir ve yüklenir")
    src = out.split("SRCBEGIN\n", 1)[1].split("\nSRCEND", 1)[0] if "SRCBEGIN" in out else ""
    check('["_Animasyon_1"]' in src and '["_Animasyon_2"]' in src and '["_Animasyon_3"]' in src,
          "anahtarlar boşluksuz: _Animasyon_1/2/3")
    check("_Animasyon 1" not in src and "_Animasyon 9" not in src,
          "boşluklu ad (_Animasyon 1) ve bilinmeyen referans (_Animasyon 9) betikte yok")
    lines = [ln for ln in out.split("\n") if ln and not ln.startswith(("SRC", "LOADERR"))]
    lines = [ln for ln in lines if ln.startswith(("TWEEN|", "CONN|"))]
    check(any(ln.startswith("TWEEN|Ana_Panel|") for ln in lines), "giriş (show) tween'i Ana_Panel'e uygulandı")
    check(not any(ln.startswith("TWEEN|Baslik|") for ln in lines), "bilinmeyen referanslı Baslik'e tween YOK (düşürüldü)")
    check(any("MouseEnter:Buton_button" in ln for ln in lines), "hover giriş bağlandı")
    check(any("MouseLeave:Buton_button" in ln for ln in lines), "hover çıkış bağlandı")
    check(any("MouseButton1Down:Buton_button" in ln for ln in lines), "basma bağlandı")
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — JSON animasyon tanımı → Lua LocalScript (sahte Roblox'ta)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
