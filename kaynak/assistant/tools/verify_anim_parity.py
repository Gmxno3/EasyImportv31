#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANİMASYON PARİTE KAPISI — EIAnim.lua ≡ ei-anim.js

Aynı girdiler (sabit öğe listesi, stil, öğrenme durumu) iki dilde koşulur; şunlar BAYT birebir
aynı olmalıdır: seçim planı · seçenek sıraları (options) · üretilen LocalScript kaynağı.
Öğrenme durumu bir ei-learn v1 metni olarak verilir (her iki dilde de aynı decode).
Ayrıca öğrenme gözlemi, varsayılanı değiştirmeli (kabul edilen öne geçer).

Kullanım: python3 tools/verify_anim_parity.py     (çıkış 0 = GEÇTİ)
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_anim_lua as B  # noqa: E402

LUA_ANIM = os.path.join(ROOT, "runtime", "lua", "EIAnim.lua")
LUA_LEARN = os.path.join(ROOT, "runtime", "lua", "EILearn.lua")
JS_ANIM = os.path.join(ROOT, "runtime", "js", "ei-anim.js")
JS_LEARN = os.path.join(ROOT, "runtime", "js", "ei-learn.js")
VENDOR = os.path.join(HERE, "vendor")

# (id, ad, sınıf, derinlik, üst öğe kimliği | None)
ELEMENTS = [
    (1, "Ana_Panel", "Frame", 1, None),
    (2, "Baslik_Text", "TextLabel", 2, 1),
    (3, "Buton_button", "TextButton", 1, None),
    (4, "Kapat_X", "ImageButton", 2, 1),
    (5, "Ikon_ImageLabel", "ImageLabel", 1, None),
    (6, "Card_Primary_button", "TextButton", 1, None),
    (7, "Lbl_Icon", "ImageButton", 1, None),
    (8, "Liste_card_Item", "Frame", 2, 1),
    # P1: kaskad (aynı üst öğe 20'de 3 buton), seçim (üst 21'de 2 sekme), döngü (CTA + ikon)
    (9, "Shop_Card_button", "TextButton", 2, 20),
    (10, "Shop_Card2_button", "TextButton", 2, 20),
    (11, "Shop_Card3_button", "TextButton", 2, 20),
    (12, "Tab_Weapons_button", "TextButton", 2, 21),
    (13, "Tab_Armor_button", "TextButton", 2, 21),
    (14, "CTA_primary_button", "ImageButton", 1, None),
    (15, "Ikon_icon", "ImageLabel", 1, None),
    (16, "Kart_border_Frame", "Frame", 1, None),
    # etiketler: _pop (giriş), _lift (hover), _bell (dikkat/döngü), _glow yalnız buton olmayan öğede (yok sayılır)
    (17, "Kart_pop_fade_Frame", "Frame", 1, None),
    (18, "Buton_lift_button", "TextButton", 1, None),
    (19, "Zil_bell_ImageLabel", "ImageLabel", 1, None),
    (20, "Parlama_glow_Frame", "Frame", 2, None),
    # efektler: para yağmuru, basınca patlama, dev hale (orb önce gelir, sweep sonra)
    (21, "Hazine_coin_Frame", "Frame", 1, None),
    (22, "Buton_burst_button", "TextButton", 1, None),
    (23, "Panel_orb_sweep_Frame", "Frame", 1, None),
    (24, "Coin_fx_ImageLabel", "ImageLabel", 2, 21),
    (25, "Buton_smooth_button", "TextButton", 1, None),
    (26, "Yazi_gleam_TextLabel", "TextLabel", 1, None),
]
STYLES = ["stud", "anime", "cartoon", "belirsiz"]
CLASSES = ["TextButton", "ImageButton", "Frame", "TextLabel", "ImageLabel"]
ROLES = ["button", "close-button", "primary-button", "panel", "card", "label", "icon"]
CATS = ["giris", "hover", "basma"]
RUNNER = r"""
const fs = require('fs');
const path = require('path');
const learnPath = process.argv[2], animPath = process.argv[3], progPath = process.argv[4];
global.EILearn = require(learnPath);
const EIAnim = require(animPath);
const prog = JSON.parse(fs.readFileSync(progPath, 'utf8'));
const out = [];
for (const st of prog.styles) {
  for (const lname of prog.learnNames) {
    const learn = lname === 'none' ? null : global.EILearn.decode(prog.learn[lname]);
    const plan = EIAnim.plan(prog.elements, st, learn);
    for (const b of plan) out.push('PLAN|' + [st, lname, b.id, b.cls, b.role, b.show || '-', b.hover || '-', b.press || '-'].join('|'));
    out.push('SRC|' + st + '|' + lname);
    out.push(EIAnim.buildSource(plan));
    out.push('ENDSRC');
  }
}
for (const st of prog.styles) for (const lname of prog.learnNames) {
  const learn = lname === 'none' ? null : global.EILearn.decode(prog.learn[lname]);
  for (const c of prog.classes) for (const r of prog.roles) for (const cat of prog.cats) {
    out.push('OPT|' + [st, lname, c, r, cat, EIAnim.options(c, r, cat, st, learn).join(',')].join('|'));
  }
}
for (const st of prog.styles) for (const lname of prog.learnNames) {
  const learn = lname === 'none' ? null : global.EILearn.decode(prog.learn[lname]);
  for (const pe of EIAnim.decideRanked(prog.elements, st, learn)) {
    for (const cat of ['giris', 'hover', 'basma']) {
      if (pe.rank[cat]) out.push('DEC|' + [st, lname, pe.id, cat, pe.rank[cat].join(',')].join('|'));
    }
  }
  for (const b of EIAnim.decideBindings(prog.elements, st, learn)) {
    out.push('CHO|' + [st, lname, b.id, b.show || '-', b.hover || '-', b.press || '-', b.loop || '-', b.selA || '-',
      (b.sel === undefined ? '-' : String(b.sel)), (b.delay || 0).toFixed(3), b.fx || '-'].join('|'));
  }
}
process.stdout.write(out.join('\n') + '\n');
"""

LUA_PROG = r"""
local EILearn = (function()
%(learn)s
end)()
local EIAnim = (function()
%(anim)s
end)()
local prog = %(prog)s
local out = {}
local function emit(s) out[#out + 1] = s end
for _, st in ipairs(prog.styles) do
  for _, lname in ipairs(prog.learnNames) do
    local learn = nil
    if lname ~= "none" then learn = EILearn.decode(prog.learn[lname]) end
    local plan = EIAnim.plan(prog.elements, st, learn)
    for _, b in ipairs(plan) do
      emit(table.concat({ "PLAN", st, lname, tostring(b.id), b.cls, b.role, b.show or "-", b.hover or "-", b.press or "-" }, "|"))
    end
    emit("SRC|" .. st .. "|" .. lname)
    emit(EIAnim.buildSource(plan))
    emit("ENDSRC")
  end
end
for _, st in ipairs(prog.styles) do
  for _, lname in ipairs(prog.learnNames) do
    local learn = nil
    if lname ~= "none" then learn = EILearn.decode(prog.learn[lname]) end
    for _, c in ipairs(prog.classes) do
      for _, r in ipairs(prog.roles) do
        for _, cat in ipairs(prog.cats) do
          local list = EIAnim.options(c, r, cat, st, learn)
          emit("OPT|" .. st .. "|" .. lname .. "|" .. c .. "|" .. r .. "|" .. cat .. "|" .. table.concat(list, ","))
        end
      end
    end
  end
end
for _, st in ipairs(prog.styles) do
  for _, lname in ipairs(prog.learnNames) do
    local learn = nil
    if lname ~= "none" then learn = EILearn.decode(prog.learn[lname]) end
    for _, pe in ipairs(EIAnim.decideRanked(prog.elements, st, learn)) do
      for _, cat in ipairs({ "giris", "hover", "basma" }) do
        local l = pe.rank[cat]
        if l then
          emit("DEC|" .. st .. "|" .. lname .. "|" .. tostring(pe.id) .. "|" .. cat .. "|" .. table.concat(l, ","))
        end
      end
    end
    for _, b in ipairs(EIAnim.decideBindings(prog.elements, st, learn)) do
      emit(table.concat({ "CHO", st, lname, tostring(b.id), b.show or "-", b.hover or "-", b.press or "-",
        b.loop or "-", b.selA or "-", b.sel ~= nil and tostring(b.sel) or "-", string.format("%%.3f", b.delay or 0),
        b.fx or "-" }, "|"))
    end
  end
end
io.write(table.concat(out, "\n"), "\n")
"""


def run_lua(prog_lua):
    """Lua çıktısı io.write → OUT tamponu; JS koşucusu OUT'u senkron dosyaya yazar.
    (fengari'de io.open yok; stdout süreç sonunda kesilebiliyordu.)"""
    prelude = ("local __B = {}\n"
               "io.write = function(...) for i = 1, select('#', ...) do __B[#__B + 1] = tostring((select(i, ...))) end end\n")
    prog = prelude + prog_lua + "\nOUT = table.concat(__B)\n"
    fd, outp = tempfile.mkstemp(suffix=".out"); os.close(fd)
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(prog)
        path = fh.name
    runner = (
        "const { lauxlib, lua, lualib, to_luastring } = require('fengari');\n"
        "const fs = require('fs');\n"
        "const prog = fs.readFileSync(process.argv[2], 'utf8');\n"
        "const L = lauxlib.luaL_newstate(); lualib.luaL_openlibs(L);\n"
        "const st = lauxlib.luaL_dostring(L, to_luastring(prog));\n"
        "if (st !== lua.LUA_OK) { process.stderr.write('LUA HATASI: ' + (lua.lua_tojsstring(L, -1) || '?') + '\\n'); process.exit(1); }\n"
        "lua.lua_getglobal(L, to_luastring('OUT'));\n"
        "fs.writeFileSync(process.argv[3], lua.lua_tojsstring(L, -1) || '');\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(runner); jspath = fh.name
    env = dict(os.environ)
    env["NODE_PATH"] = VENDOR
    try:
        r = subprocess.run(["node", jspath, path, outp], capture_output=True, text=True, timeout=300, env=env)
        if r.returncode != 0:
            raise RuntimeError("fengari/Lua hatası:\n" + (r.stderr or "")[:2000])
        return open(outp, encoding="utf-8").read()
    finally:
        os.unlink(path); os.unlink(jspath); os.unlink(outp)


def run_js(prog_json):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(prog_json, fh, ensure_ascii=False); progp = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(RUNNER); rp = fh.name
    try:
        r = subprocess.run(["node", rp, JS_LEARN, JS_ANIM, progp], capture_output=True, text=True, timeout=280)
        if r.returncode != 0:
            raise RuntimeError("JS hatası: " + (r.stderr or "")[:1500])
        return r.stdout
    finally:
        os.unlink(progp); os.unlink(rp)


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def learned_text(anims, style="anime"):
    """TextButton/button/basma için: statik sıranın SONUNCUSU 3 kez kabul, ilki 2 kez ret."""
    cand = B_static(anims, "basma", "TextButton", "button", style)
    first, last = cand[0], cand[-1]
    ctx = "%s|%s|%s|%s" % (style, "textbutton", "button", "basma")
    return "ei-learn v1\nevents 5\nanim %s %s 3 0\nanim %s %s 0 2\n" % (ctx, last, ctx, first)


def learned_text_pick(anims, style):
    """learned_text'teki kabul edilen animasyon: statik sıranın son öğesi (basma, TextButton/button)."""
    return B_static(anims, "basma", "TextButton", "button", style)[-1]


def B_static(anims, cat, cls, role, style):
    bias = {"cartoon": {"basma": 1.3}}.get(style, {}).get(cat, 1)
    for pss in (1, 2):
        lst = [aid for aid in sorted(anims) if anims[aid]["cat"] == cat and cls in anims[aid]["cls"]
               and (pss == 2 or role in anims[aid]["roles"])]
        if lst:
            return sorted(lst, key=lambda x: (-(anims[x]["beauty"] * bias), x))
    return []


def parse(out):
    """Çıktıyı ayrıştır: {PLAN: [...], SRC: {key: text}, OPT: [...]}"""
    res = {"PLAN": [], "SRC": {}, "OPT": [], "DEC": [], "CHO": []}
    lines = out.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("PLAN|"):
            res["PLAN"].append(ln)
        elif ln.startswith("OPT|"):
            res["OPT"].append(ln)
        elif ln.startswith("DEC|"):
            res["DEC"].append(ln)
        elif ln.startswith("CHO|"):
            res["CHO"].append(ln)
        elif ln.startswith("SRC|"):
            key = ln[4:]
            body = []
            i += 1
            while i < len(lines) and lines[i] != "ENDSRC":
                body.append(lines[i]); i += 1
            res["SRC"][key] = "\n".join(body)
        i += 1
    return res


def main():
    fails = []

    def check(c, m):
        print(("  [OK] " if c else "  [FAIL] ") + m)
        if not c:
            fails.append(m)

    anims, _ = B.convert(json.load(open(B.LIB, encoding="utf-8")))
    learn_names = ["none", "learned"]
    prog_json = {
        "styles": STYLES,
        "learnNames": learn_names,
        "learn": {"learned": learned_text(anims)},
        "elements": [{"id": a, "name": b, "cls": c, "depth": d, "parent": pp} for a, b, c, d, pp in ELEMENTS],
        "classes": CLASSES, "roles": ROLES, "cats": CATS,
    }
    lua_learn = open(LUA_LEARN, encoding="utf-8").read()
    lua_anim = open(LUA_ANIM, encoding="utf-8").read()
    lua_prog_table = json.dumps(prog_json, ensure_ascii=False)
    # Lua tablosu: JSON'u doğrudan Lua literal olarak gömmek yerine programı kur
    lua_table = (
        "{ styles = {" + ",".join(lua_str(s) for s in STYLES) + "}, "
        + "learnNames = {" + ",".join(lua_str(s) for s in learn_names) + "}, "
        + "learn = { learned = " + lua_str(prog_json["learn"]["learned"]) + " }, "
        + "elements = {" + ",".join(
            "{ id = %d, name = %s, cls = %s, depth = %d%s }" % (a, lua_str(b), lua_str(c), d,
                                                                 "" if pp is None else ", parent = %d" % pp)
            for a, b, c, d, pp in ELEMENTS) + "}, "
        + "classes = {" + ",".join(lua_str(s) for s in CLASSES) + "}, "
        + "roles = {" + ",".join(lua_str(s) for s in ROLES) + "}, "
        + "cats = {" + ",".join(lua_str(s) for s in CATS) + "} }"
    )
    lua_prog = LUA_PROG % {"learn": lua_learn, "anim": lua_anim, "prog": lua_table}
    lua_out = parse(run_lua(lua_prog))
    js_out = parse(run_js(prog_json))

    print("== 1) öğrenme durumu (ei-learn v1) iki dilde de geçerli")
    check(lua_out["PLAN"] and js_out["PLAN"], "plan satırları üretildi (Lua %d · JS %d)"
          % (len(lua_out["PLAN"]), len(js_out["PLAN"])))

    print("== 2) seçim planı birebir")
    check(lua_out["PLAN"] == js_out["PLAN"], "plan satırları Lua == JS (%d satır)" % len(lua_out["PLAN"]))

    print("== 3) seçenek sıraları birebir")
    check(lua_out["OPT"] == js_out["OPT"], "options Lua == JS (%d kombinasyon)" % len(lua_out["OPT"]))

    print("== 4) LocalScript kaynağı baytı birebir")
    check(set(lua_out["SRC"]) == set(js_out["SRC"]), "aynı kaynak anahtarları")
    for key in sorted(lua_out["SRC"]):
        check(lua_out["SRC"][key] == js_out["SRC"].get(key), "kaynak %s Lua == JS (%d bayt)"
              % (key, len(lua_out["SRC"][key])))

    print("== 5) öğrenme varsayılanı değiştirir (kabul görene öncelik)")
    static_first = B_static(anims, "basma", "TextButton", "button", "anime")[0]
    learned_last = B_static(anims, "basma", "TextButton", "button", "anime")[-1]
    lopt = [ln for ln in lua_out["OPT"] if ln.startswith("OPT|anime|learned|TextButton|button|basma|")]
    jopt = [ln for ln in js_out["OPT"] if ln.startswith("OPT|anime|learned|TextButton|button|basma|")]
    lfirst = lopt[0].split("|")[-1].split(",")[0] if lopt else None
    jfirst = jopt[0].split("|")[-1].split(",")[0] if jopt else None
    check(lfirst == learned_last and jfirst == learned_last,
          "öğrenmeden sonra ilk seçenek kabul edilen (%s) — statik ilk (%s) değil" % (learned_last, static_first))
    base = [ln for ln in lua_out["OPT"] if ln.startswith("OPT|anime|none|TextButton|button|basma|")]
    check(base and base[0].split("|")[-1].split(",")[0] == static_first,
          "öğrenme yokken ilk seçenek statik sıradaki (%s) — v10 davranışı korunuyor" % static_first)

    print("== 6) tasarım kararları (madde 3) Lua ≡ JS birebir")
    check(lua_out["DEC"] == js_out["DEC"] and len(lua_out["DEC"]) > 0,
          "sıralı öneriler Lua == JS (%d satır)" % len(lua_out["DEC"]))
    check(lua_out["CHO"] == js_out["CHO"] and len(lua_out["CHO"]) > 0,
          "seçilen bağlamalar Lua == JS (%d satır)" % len(lua_out["CHO"]))

    def cho(lst, style, learn, eid):
        for ln in lst:
            p = ln.split("|")
            if p[1] == style and p[2] == learn and p[3] == str(eid):
                return {"show": p[4], "hover": p[5], "press": p[6]}
        return None

    def dec(lst, style, learn, eid, cat):
        for ln in lst:
            p = ln.split("|")
            if p[1] == style and p[2] == learn and p[3] == str(eid) and p[4] == cat:
                return p[5].split(",") if p[5] else []
        return None

    print("== 7) madde 3 davranışları")
    # kapat butonu (id 4, ImageButton, close-button): yalnızca hover, basma YOK
    for st in STYLES:
        check(dec(lua_out["DEC"], st, "none", 4, "basma") is None and dec(lua_out["DEC"], st, "none", 4, "hover"),
              "stil=%s: kapat butonunda basma önerisi yok, hover var" % st)
    # tutarlılık (≥%50 çoğunluk): TextButton öğelerinin en sık seçilen hover'ı, öğelerin yarısından fazlasında
    tb_ids = [e[0] for e in ELEMENTS if e[2] == "TextButton"]
    for st in STYLES:
        picks = []
        for eid in tb_ids:
            c = cho(lua_out["CHO"], st, "none", eid)
            if c and c["hover"] != "-":
                picks.append(c["hover"])
        top = max(set(picks), key=lambda x: (picks.count(x), x)) if picks else None
        check(top is not None and picks.count(top) * 2 >= len(tb_ids),
              "stil=%s: TextButton hover çoğunluğu (%s: %d/%d)" % (st, top, picks.count(top) if top else 0, len(tb_ids)))
    # stil: anime'de giriş paneli anahtar sözcüklü (yaylı) animasyon almalı
    a = cho(lua_out["CHO"], "anime", "none", 1)
    check(a and any(t in a["show"] for t in ("elastic", "flip", "rotate", "bounce", "pop", "spring", "grow", "swing")),
          "anime: ana panel girişi yaylı/dönen (%s)" % (a and a["show"]))
    a = cho(lua_out["CHO"], "stud", "none", 1)
    check(a and any(t in a["show"] for t in ("fade", "scale_up", "shrink_only", "glow", "lift", "brighten", "soft", "reveal")),
          "stud: ana panel girişi sade (%s)" % (a and a["show"]))
    # öğrenme önceliği: learned durumunda id 3 basma = öğrenilen (kabul edilen) animasyon
    learned_pick = learned_text_pick(anims, "anime")
    b = cho(lua_out["CHO"], "anime", "learned", 3)
    check(b and b["press"] == learned_pick,
          "öğrenme tutarlılığı geçersiz kılar: anime/learned basma = %s (beklenen %s)" % (b and b["press"], learned_pick))

    print("== 8) P1: kaskad · seçim grubu · döngü (Lua ve JS aynı)")
    def chofull(lst, style, learn, eid):
        for ln in lst:
            p = ln.split("|")
            if p[1] == style and p[2] == learn and p[3] == str(eid):
                return {"show": p[4], "hover": p[5], "press": p[6], "loop": p[7], "selA": p[8], "sel": p[9], "delay": p[10],
                        "fx": p[11] if len(p) > 11 else "-"}
        return None
    for label, out in (("Lua", lua_out), ("JS", js_out)):
        c9 = chofull(out["CHO"], "anime", "none", 9)
        c10 = chofull(out["CHO"], "anime", "none", 10)
        c11 = chofull(out["CHO"], "anime", "none", 11)
        check(c9 and c10 and c11 and [c9["delay"], c10["delay"], c11["delay"]] == ["0.000", "0.060", "0.120"],
              "%s kaskad: 3 kardeş buton sırayla girer (0, 0.06, 0.12)" % label)
        t12 = chofull(out["CHO"], "anime", "none", 12)
        t13 = chofull(out["CHO"], "anime", "none", 13)
        check(t12 and t13 and t12["selA"] != "-" and t12["sel"] == t13["sel"] == "21",
              "%s seçim: aynı üst öğedeki iki sekme aynı seçim grubunda (%s)" % (label, t12 and t12["selA"]))
        c14 = chofull(out["CHO"], "anime", "none", 14)
        c5 = chofull(out["CHO"], "anime", "none", 5)
        # anime'de "rotate" stil bonusu alır: ikon sallanma (wiggle) ya da dönüş (rotate) olabilir
        check(c14 and c14["loop"] != "-" and c5 and c5["loop"] in ("loop_wiggle_icon", "loop_rotate_slow"),
              "%s döngü: CTA (%s) yanıp söner, ikon (%s) sürekli sallanır" % (label, c14 and c14["loop"], c5 and c5["loop"]))
        loops = sum(1 for ln in out["CHO"] if ln.split("|")[1] == "anime" and ln.split("|")[2] == "none"
                    and ln.split("|")[7] not in ("-", "loop_border_spin", "attention_bell_ring"))
        check(loops <= 3, "%s döngü üst sınırı (otomatik): %d ≤ 3" % (label, loops))
        c16 = chofull(out["CHO"], "anime", "none", 16)
        check(c16 and c16["loop"] == "loop_border_spin", "%s kenarlık: adında 'border' geçen öğe kenarlık dönüşü alır (%s)" % (label, c16 and c16["loop"]))
        c4 = chofull(out["CHO"], "anime", "none", 4)
        check(c4 and c4["selA"] == "-" and c4["loop"] == "-", "%s kapat butonu: seçim/döngü yok" % label)

    print("== 9) etiketler (Framewisp benzeri _etiket)")
    for label, out in (("Lua", lua_out), ("JS", js_out)):
        c17 = chofull(out["CHO"], "anime", "none", 17)
        check(c17 and c17["show"] == "enter_pop_scale", "%s etiket _pop: giriş enter_pop_scale (%s)" % (label, c17 and c17["show"]))
        c18 = chofull(out["CHO"], "anime", "none", 18)
        check(c18 and c18["hover"] == "hover_lift", "%s etiket _lift: buton hover hover_lift (%s)" % (label, c18 and c18["hover"]))
        c19 = chofull(out["CHO"], "anime", "none", 19)
        check(c19 and c19["loop"] == "attention_bell_ring", "%s etiket _bell: dikkat animasyonu döngü slotunda (%s)" % (label, c19 and c19["loop"]))
        c20 = chofull(out["CHO"], "anime", "none", 20)
        check(c20 is None or c20["hover"] == "-", "%s etiket _glow: buton olmayan öğede hover yok sayılır (satır: %s)" % (label, "yok" if c20 is None else c20["hover"]))

    print("== 10) efektler (ad etiketi → UI efekti)")
    for label, out in (("Lua", lua_out), ("JS", js_out)):
        c21 = chofull(out["CHO"], "anime", "none", 21)
        check(c21 and c21["fx"] == "fall", "%s efekt _coin: yağan para (%s)" % (label, c21 and c21["fx"]))
        c24 = chofull(out["CHO"], "anime", "none", 24)
        check(c24 and c24["fx"] == "tpl", "%s şablon _fx: tasarım öğesi kopyalanır, gizlenir (%s)" % (label, c24 and c24["fx"]))
        c22 = chofull(out["CHO"], "anime", "none", 22)
        check(c22 and c22["fx"] == "burst", "%s efekt _burst: basınca patlama (%s)" % (label, c22 and c22["fx"]))
        c23 = chofull(out["CHO"], "anime", "none", 23)
        check(c23 and c23["fx"] == "orb", "%s efekt: iki etiketten ilki kazanır (orb, sweep değil) (%s)" % (label, c23 and c23["fx"]))

    print("== 11) Framewisp benzeri: _smooth / _gleam ve varsayılan parametreler")
    for label, out in (("Lua", lua_out), ("JS", js_out)):
        c25 = chofull(out["CHO"], "anime", "none", 25)
        check(c25 and c25["fx"] == "smooth", "%s _smooth: buton büyüme efekti (%s)" % (label, c25 and c25["fx"]))
        c26 = chofull(out["CHO"], "anime", "none", 26)
        check(c26 and c26["fx"] == "gleam", "%s _gleam: metin parıltısı (%s)" % (label, c26 and c26["fx"]))

    # Varsayılan efekt parametreleri: Lua FX_DEFAULTS ≡ JS FX_DEFAULTS (iki ayrı kaynakta tutulur)
    import re as _re
    lua_src = open(LUA_ANIM, encoding="utf-8").read()
    js_src = open(JS_ANIM, encoding="utf-8").read()
    def _parse_defaults(txt, opener):
        i = txt.index(opener) + len(opener)
        depth, j = 1, i
        while depth:
            c = txt[j]
            depth += 1 if c == "{" else (-1 if c == "}" else 0)
            j += 1
        body = txt[i:j - 1]
        out = {}
        for m in _re.finditer(r"(\w+)\s*[=:]\s*\{([^{}]*)\}", body):
            pairs = _re.findall(r"(\w+)\s*[=:]\s*([0-9.]+)", m.group(2))
            out[m.group(1)] = {k: float(v) for k, v in pairs}
        return out
    lua_def = _parse_defaults(lua_src, "local FX_DEFAULTS = {")
    js_def = _parse_defaults(js_src, "var FX_DEFAULTS = {")
    check(lua_def and lua_def == js_def and len(lua_def) == 7,
          "varsayılan efekt parametreleri Lua ≡ JS (%d efekt)" % len(lua_def))

    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d)" % len(fails)); return 1
    print("SONUÇ: GEÇTİ — animasyon planı, seçenekler, LocalScript ve tasarım kararları Lua ≡ JS birebir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
