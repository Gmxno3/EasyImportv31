#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAPI: etkileşim (sahte Roblox ortamında)
  • _panel başlangıçta kapalı; _open açar; _close (parametresiz) en yakın paneli kapatır
  • _tab: aynı _tabgroup içinde biri açılınca diğerleri kapanır; ilk sekme başlangıçta açık
  • açılan panelde içindeki öğelerin giriş animasyonu yeniden oynar (her _open'da)
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

EXTRA = r"""
Color3 = { new = function(r, g, b) return { r = r, g = g, b = b } end, fromRGB = function(r, g, b) return { r = r, g = g, b = b } end }
local function ff(self, n) for _, c in ipairs(self.children) do if c.Name == n then return c end end return nil end
local function isDesc(self, anc) local p = self.Parent while p do if p == anc then return true end p = p.Parent end return false end
"""


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    anims, _ = B.convert(json.load(open(B.LIB, encoding="utf-8")))
    specs = {"_Animasyon 1": {"tracks": anims["enter_fade"]["tracks"]}}
    prog = (
        "local EIAnim = (function()\n" + V.module_src() + "\nend)()\n"
        + V.MOCK + "\n" + EXTRA
        + "ROOT.children = {}\n"
        + "local function mk(cls, name, id, parent)\n"
        + "  local o = makeInst(cls, name); o.attrs.EI_Id = id; o.ZIndex = 1; o.FindFirstChild = ff; o.IsDescendantOf = isDesc\n"
        + "  o.MouseButton1Click = { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f end }\n"
        + "  addChild(parent or ROOT, o); return o\n"
        + "end\n"
        + "local ANA = mk('Frame', 'Ana', 1)\n"
        + "local SHOP = mk('Frame', 'Shop', 10); SHOP.Visible = false\n"
        + "local KAPAT = mk('TextButton', 'Kapat', 11, SHOP)\n"
        + "local AC = mk('TextButton', 'Ac', 12)\n"
        + "local GRUP = mk('Frame', 'Grup', 20)\n"
        + "local SILAH = mk('TextButton', 'Silah', 13, GRUP)\n"
        + "local ZIRH = mk('TextButton', 'Zirh', 14, GRUP)\n"
        + "local SP = mk('Frame', 'Silah_panel', 15); SP.Visible = false\n"
        + "local ZP = mk('Frame', 'Zirh_panel', 16); ZP.Visible = false\n"
        + "local BIND = { { id = 11, show = '_Animasyon 1' } }\n"
        + "local SPECS = " + lua_val(specs) + "\n"
        + "local ACTIONS = { { id = 12, kind = 'open', target = 10 }, { id = 11, kind = 'close' },\n"
        + "  { id = 13, kind = 'tab', target = 15 }, { id = 14, kind = 'tab', target = 16 } }\n"
        + "local SRC = EIAnim.buildSourceSpec(BIND, SPECS, { actions = ACTIONS, panels = { 10, 15, 16 }, groups = { 20 } })\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "local function vis(o) LOG[#LOG + 1] = 'VIS|' .. o.Name .. '|' .. tostring(o.Visible) end\n"
        + "chunk()\n"
        + "LOG[#LOG + 1] = 'MARK|init'; vis(SHOP); vis(SP); vis(ZP); vis(AC)\n"
        + "LOG[#LOG + 1] = 'MARK|open'; for _, f in ipairs(AC.MouseButton1Click.fns) do f() end; vis(SHOP)\n"
        + "LOG[#LOG + 1] = 'MARK|close'; for _, f in ipairs(KAPAT.MouseButton1Click.fns) do f() end; vis(SHOP)\n"
        + "LOG[#LOG + 1] = 'MARK|tab2'; for _, f in ipairs(ZIRH.MouseButton1Click.fns) do f() end; vis(SP); vis(ZP)\n"
        + "LOG[#LOG + 1] = 'MARK|tab1'; for _, f in ipairs(SILAH.MouseButton1Click.fns) do f() end; vis(SP); vis(ZP)\n"
        + "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    out = V.run_lua_program(prog)
    check("LOADERR" not in out, "etkileşim betiği derlenir ve yüklenir")
    secs, cur = {}, "pre"
    for ln in out.split("\n"):
        if ln.startswith("MARK|"):
            cur = ln[5:]
            secs[cur] = []
        elif ln:
            secs.setdefault(cur, []).append(ln)

    def v(sec, name):
        for ln in secs.get(sec, []):
            if ln.startswith("VIS|%s|" % name):
                return ln.split("|")[2]
        return None

    check(v("init", "Shop") == "false", "başlangıçta _panel (Shop) kapalı")
    check(v("init", "Silah_panel") == "true" and v("init", "Zirh_panel") == "false",
          "başlangıçta ilk sekme paneli açık, diğeri kapalı")
    check(v("open", "Shop") == "true", "_open:Shop → panel açılır")
    check(v("close", "Shop") == "false", "_close (parametresiz) → en yakın panel kapanır")
    check(v("tab2", "Zirh_panel") == "true" and v("tab2", "Silah_panel") == "false",
          "_tab: ikinci sekme açılır, birinci kapanır")
    check(v("tab1", "Silah_panel") == "true" and v("tab1", "Zirh_panel") == "false",
          "_tab: birinci sekme geri açılır, ikinci kapanır")
    replay = [ln for ln in secs.get("open", []) if ln.startswith("TWEEN|Kapat|")]
    check(len(replay) >= 1, "açılan panelde içteki öğenin giriş animasyonu yeniden oynar (%d)" % len(replay))
    # chunk() çalışırken (MARK|init'ten önce) başlangıç animasyonları kaydedilir
    init_tw = [ln for ln in secs.get("pre", []) if ln.startswith("TWEEN|Kapat|")]
    check(len(init_tw) >= 1, "giriş animasyonu başlangıçta da bir kez oynar (%d)" % len(init_tw))
    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — paneller, sekmeler ve yeniden oynatılan girişler sahte Roblox'ta çalışır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
