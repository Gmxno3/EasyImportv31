#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANİMASYON ÜRETİCİ KAPISI (A6-A8 · EIAnim.lua)

  1) SENKRON   veri bloğu anim-library.json ile birebir (build_anim_lua --check)
  2) PARİTE    Lua planı ≡ bağımsız Python referansı (anim-library.json'dan, Lua'ya bakmadan)
  3) DERLEME   üretilen LocalScript fengari'de (Lua 5.3) hatasız yüklenir
  4) DAVRANIŞ  LocalScript sahte bir Roblox ortamında koşar; hover giriş/çıkış, basma ve giriş
               tween'lerinin hedefleri ve AnchorPoint düzeltmesi beklenenle eşleşir
  5) DETERMİNİZM aynı girdi → aynı bayt

Kullanım:  python3 tools/verify_anim.py      Çıkış: 0 = GEÇTİ · 1 = BAŞARISIZ
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

LUA_FILE = os.path.join(ROOT, "runtime", "lua", "EIAnim.lua")
LIB = os.path.join(ROOT, "anim", "anim-library.json")
VENDOR = os.path.join(HERE, "vendor")

RUNNER_JS = r"""
const { lauxlib, lua, lualib, to_luastring } = require('fengari');
const fs = require('fs');
const prog = fs.readFileSync(process.argv[2], 'utf8');
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
const st = lauxlib.luaL_dostring(L, to_luastring(prog));
if (st !== lua.LUA_OK) {
  process.stderr.write('LUA HATASI: ' + (lua.lua_tojsstring(L, -1) || '?') + '\n');
  process.exit(1);
}
"""

# Sahte Roblox ortamı. Yalnız LocalScript'in kullandığı API'nin gerekli parçaları.
MOCK = r"""
local LOG = {}
local function log(...)
  local parts = {}
  for i = 1, select('#', ...) do parts[#parts + 1] = tostring((select(i, ...))) end
  LOG[#LOG + 1] = table.concat(parts, "|")
end
local function fmt(v)
  if type(v) == "table" and v.X then
    if type(v.X) == "table" then return "(" .. tostring(v.X.Scale) .. "," .. tostring(v.X.Offset) .. ")" end
    return "(" .. tostring(v.X) .. "," .. tostring(v.Y) .. ")"
  end
  return tostring(v)
end

local V2MT = { __eq = function(a, b) return a.X == b.X and a.Y == b.Y end }
Vector2 = { new = function(x, y) return setmetatable({ X = x, Y = y }, V2MT) end }
UDim2 = { new = function(xs, xo, ys, yo) return { X = { Scale = xs, Offset = xo }, Y = { Scale = ys, Offset = yo } } end }
Enum = {
  EasingStyle = setmetatable({}, { __index = function(_, k) return k end }),
  EasingDirection = setmetatable({}, { __index = function(_, k) return k end }),
}
TweenInfo = { new = function(d, s, dir, rep, rev, dl) return { d = d, s = s, dir = dir, rep = rep, rev = rev, dl = dl } end }
Color3 = { new = function(r, g, b) return { r = r, g = g, b = b } end,
  fromRGB = function(r, g, b) return { r = r, g = g, b = b } end }
UDim = { new = function(sc, of) return { Scale = sc, Offset = of } end }
UDim2.fromOffset = function(x, y) return { X = { Scale = 0, Offset = x }, Y = { Scale = 0, Offset = y } } end
UDim2.fromScale = function(x, y) return { X = { Scale = x, Offset = 0 }, Y = { Scale = y, Offset = 0 } } end
task = { spawn = function(f) pcall(f) end, wait = function() error("STOP") end }

local function signal(name)
  return { fns = {}, Connect = function(self, f) self.fns[#self.fns + 1] = f; log("CONN", name) end }
end

local function makeInst(cls, name)
  local o = { ClassName = cls, Name = name or cls, attrs = {}, children = {}, Parent = nil,
    AnchorPoint = Vector2.new(0, 0), Size = UDim2.new(0, 120, 0, 40), Position = UDim2.new(0, 20, 0, 80),
    ImageTransparency = 0.15, BackgroundTransparency = 0 }
  if cls == "UIScale" then o.Scale = 1 end
  o.MouseEnter = signal("MouseEnter:" .. o.Name)
  o.MouseLeave = signal("MouseLeave:" .. o.Name)
  o.MouseButton1Down = signal("MouseButton1Down:" .. o.Name)
  o.GetAttribute = function(self, k) return self.attrs[k] end
  o.SetAttribute = function(self, k, v) self.attrs[k] = v end
  o.FindFirstChildOfClass = function(self, c)
    for _, ch in ipairs(self.children) do if ch.ClassName == c then return ch end end
    return nil
  end
  o.FindFirstChildWhichIsA = o.FindFirstChildOfClass
  o.IsA = function(self, c)
    if self.ClassName == c then return true end
    if c == "GuiObject" then return self.ClassName ~= "UIScale" end
    if c == "GuiButton" then return self.ClassName == "TextButton" or self.ClassName == "ImageButton" end
    return false
  end
  return o
end

local ALL = {}
local function addChild(p, c)
  c.Parent = p
  p.children[#p.children + 1] = c
  ALL[#ALL + 1] = c
  return c
end

Instance = { new = function(cls)
  local o = makeInst(cls)
  o.Parent = nil
  return o
end }

local tweenSvc = {
  Create = function(self, obj, info, goal)
    local tw = {}
    tw.Play = function()
      local keys = {}
      for k in pairs(goal) do keys[#keys + 1] = k end
      for _, k in ipairs(keys) do
        local g = goal[k]
        log("TWEEN", obj.Name, obj.ClassName, k, fmt(g), info.d, info.s, info.dir, info.rep, tostring(info.rev))
        obj[k] = g
      end
    end
    return tw
  end,
}
game = { GetService = function(self, n) if n == "TweenService" then return tweenSvc end return nil end }
math.randomseed(1)

local ROOT = makeInst("ScreenGui", "Root")
ROOT.GetDescendants = function(self) return ALL end
script = { Parent = ROOT }
"""

FIXTURES = [
    # id, name, cls, depth, parentLayout
    (1, "Ana_Panel", "Frame", 1, False),
    (2, "Baslik_Text", "TextLabel", 2, False),
    (3, "Buton_button", "TextButton", 1, False),
    (4, "Kapat_X", "ImageButton", 2, False),
    (5, "Ikon_ImageLabel", "ImageLabel", 1, False),
    (6, "Card_Primary_button", "TextButton", 1, False),
    (7, "Lbl_Icon", "ImageButton", 1, False),
    (8, "Liste_Item_button", "TextButton", 1, True),   # UIListLayout'lu kapta → pivot düzeltilmez
]

STYLES = ["stud", "anime", "cartoon", "belirsiz"]


def fixture_program(style):
    lines = []
    lines.append("ROOT.children = {}")
    lines.append("local LAYOUT_PARENT = addChild(ROOT, makeInst('Frame', 'Layout'))")
    lines.append("addChild(LAYOUT_PARENT, makeInst('UIListLayout', 'UIListLayout'))")
    for fid, name, cls, depth, layout in FIXTURES:
        parent = "LAYOUT_PARENT" if layout else "ROOT"
        lines.append("do local e = makeInst(%r, %r); e.attrs.EI_Id = %d; addChild(%s, e) end"
                     % (cls, name, fid, parent))
    # Lua tarafında plan için de depth/cls/name listesi (Python ile aynı)
    lines.append("local ELEMS = {}")
    for fid, name, cls, depth, layout in FIXTURES:
        lines.append("ELEMS[#ELEMS + 1] = { id = %d, name = %r, cls = %r, depth = %d }" % (fid, name, cls, depth))
    lines.append("local PLAN = EIAnim.plan(ELEMS, %r)" % style)
    lines.append("for _, b in ipairs(PLAN) do log('PLAN', b.id, b.cls, b.role, b.show or '-', b.hover or '-', b.press or '-') end")
    lines.append("for _, l in ipairs(LOG) do io.write(l, '\\n') end")
    lines.append("local SRC = EIAnim.buildSource(PLAN)")
    lines.append("log('SRCLEN', #SRC)")
    return "\n".join(lines)


def lua_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_lua_program(prog):
    """Lua çıktısı io.write → OUT tamponu; JS koşucusu OUT'u senkron dosyaya yazar.
    (fengari'de io.open yok; stdout süreç sonunda kesilebiliyordu.)"""
    prelude = ("local __B = {}\n"
               "io.write = function(...) for i = 1, select('#', ...) do __B[#__B + 1] = tostring((select(i, ...))) end end\n")
    prog = prelude + prog + "\nOUT = table.concat(__B)\n"
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


def module_src():
    return open(LUA_FILE, encoding="utf-8").read()


def lua_plan_and_source(style):
    """Lua planını ve üretilen kaynağı çalıştırır. Çıktı: (plan_lines, source_text, log_lines)"""
    marker = "\n"
    prog = (
        "local EIAnim = (function()\n" + module_src() + "\nend)()\n"
        + "local SRC_OUT = nil\n"
        + MOCK
        + "\n" + fixture_program(style) + "\n"
        + "io.write('@@SRC_BEGIN\\n', SRC, '\\n@@SRC_END\\n')\n"
    )
    out = run_lua_program(prog)
    head = out.split("@@SRC_BEGIN", 1)[0]
    plan = [ln for ln in head.split("\n") if ln.startswith("PLAN|")]
    src = out.split("@@SRC_BEGIN\n", 1)[1].split("\n@@SRC_END", 1)[0] if "@@SRC_BEGIN" in out else ""
    return plan, src, out


def run_generated(src, style):
    """Üretilen LocalScript'i sahte ortamda koştur + sürücü: hover giriş/çıkış ve basma tetikle."""
    driver = (
        "local function find(id) for _, d in ipairs(ALL) do if d.attrs.EI_Id == id then return d end end end\n"
        "for id = 1, 8 do\n"
        "  local e = find(id)\n"
        "  if e and e.MouseEnter then\n"
        "    for _, f in ipairs(e.MouseEnter.fns) do f() end\n"
        "    for _, f in ipairs(e.MouseLeave.fns) do f() end\n"
        "    for _, f in ipairs(e.MouseButton1Down.fns) do f() end\n"
        "  end\n"
        "end\n"
        "for _, d in ipairs(ALL) do if d.attrs.EI_Id == 3 then log('POS3', d.Position.X.Offset, d.Position.Y.Offset, d.AnchorPoint.X, d.AnchorPoint.Y) end end\n"
        "for _, d in ipairs(ALL) do if d.attrs.EI_Id == 8 then log('POS8', d.Position.X.Offset, d.Position.Y.Offset, d.AnchorPoint.X, d.AnchorPoint.Y) end end\n"
        "for _, l in ipairs(LOG) do io.write(l, '\\n') end\n"
    )
    prog = (
        "local EIAnim = (function()\n" + module_src() + "\nend)()\n"
        + MOCK + "\n" + fixture_program(style) + "\n"
        + "local chunk, err = load(SRC, 'EI_Animator')\n"
        + "if not chunk then io.write('LOADERR|' .. tostring(err) .. '\\n') return end\n"
        + "chunk()\n"
        + "LOG = LOG\n"
        + driver
    )
    return run_lua_program(prog)


# ----------------------------------------------------------------- Python referansı
def role_of(name, cls):
    n = name.lower()
    if cls in ("TextButton", "ImageButton"):
        if any(w in n for w in ("close", "kapat")) or n.endswith("_x"):
            return "close-button"
        if "primary" in n:
            return "primary-button"
        if "icon" in n:
            return "icon-button"
        return "button"
    if "card" in n:
        return "card"
    if any(w in n for w in ("modal", "popup")):
        return "modal"
    if any(w in n for w in ("title", "baslik")):
        return "title"
    if any(w in n for w in ("icon", "ikon")):
        return "icon"
    if "tab" in n:
        return "tab"
    if any(w in n for w in ("panel", "frame")):
        return "panel"
    if cls == "TextLabel":
        return "label"
    if cls == "ImageLabel":
        return "icon"
    return "panel"


STYLE_BIAS = {"cartoon": {"basma": 1.3}}


def pick_py(anims, cat, cls, role, style):
    bias = STYLE_BIAS.get(style, {}).get(cat, 1)
    for pss in (1, 2):
        best, best_sc = None, -1
        for aid in sorted(anims):
            a = anims[aid]
            if a["cat"] == cat and cls in a["cls"] and (pss == 2 or role in a["roles"]):
                sc = a["beauty"] * bias
                if sc > best_sc:
                    best, best_sc = aid, sc
        if best is not None:
            return best
    return None


def plan_py(anims, style):
    out = []
    for fid, name, cls, depth, _layout in FIXTURES:
        role = role_of(name, cls)
        is_btn = cls in ("TextButton", "ImageButton")
        show = pick_py(anims, "giris", cls, role, style) if depth <= 1 else None
        hover = pick_py(anims, "hover", cls, role, style) if is_btn else None
        press = pick_py(anims, "basma", cls, role, style) if is_btn else None
        if show or hover or press:
            out.append("PLAN|%d|%s|%s|%s|%s|%s" % (fid, cls, role, show or "-", hover or "-", press or "-"))
    return out


def main():
    fails = []

    def check(cond, msg):
        print(("  [OK] " if cond else "  [FAIL] ") + msg)
        if not cond:
            fails.append(msg)

    print("== 1) senkron")
    lib = json.load(open(LIB, encoding="utf-8"))
    anims, _rep = B.convert(lib)
    check(B.splice(module_src(), B.render_block(anims)) == module_src(),
          "EIAnim.lua veri bloğu kütüphane ile senkron")

    print("== 2) seçim paritesi (Lua ≡ bağımsız Python)")
    for style in STYLES:
        lua_plan, src, _out = lua_plan_and_source(style)
        py_plan = plan_py(anims, style)
        check(lua_plan == py_plan,
              "stil=%s: %d bağlama, Lua == Python" % (style, len(py_plan)))
        if lua_plan != py_plan:
            print("     lua:", lua_plan)
            print("     py :", py_plan)

    print("== 3) LocalScript derlenir (fengari / Lua 5.3)")
    src_probe = None
    for style in STYLES:
        _p, src, _o = lua_plan_and_source(style)
        src_probe = src
        assert "]==]" not in src
        prog = ("local ok, err = load([==[" + src + "]==], 'EI_Animator')\n"
                "if not ok then io.write('SYNTAX|' .. tostring(err)) else io.write('LOADOK') end\n")
        res = run_lua_program(prog)
        check(res.strip() == "LOADOK", "stil=%s kaynağı derlenir (%d bayt)" % (style, len(src)))
        check("__ANIMS__" not in src and "__BINDINGS__" not in src, "stil=%s şablon yer tutucuları dolu" % style)

    print("== 4) davranış (sahte Roblox ortamı)")
    _p, src, _o = lua_plan_and_source("anime")
    out = run_generated(src, "anime")
    check("LOADERR" not in out and "SYNTAX" not in out, "LocalScript sahte ortamda yüklenir")
    lines = [ln for ln in out.split("\n") if ln]
    tweens = [ln for ln in lines if ln.startswith("TWEEN|")]
    conns = [ln for ln in lines if ln.startswith("CONN|")]
    check(any(t.startswith("TWEEN|Buton_button|") for t in tweens), "buton giriş (show) tween'i üretildi")
    check(not any(t.startswith("TWEEN|Baslik_Text|") for t in tweens), "TextLabel derinlik 2: giriş yok")
    check(any("MouseEnter:Buton_button" in c for c in conns), "buton MouseEnter bağlandı")
    check(any("MouseLeave:Buton_button" in c for c in conns), "buton MouseLeave bağlandı")
    check(any("MouseButton1Down:Buton_button" in c for c in conns), "buton basma (MouseButton1Down) bağlandı")
    check(not any("MouseEnter:Ana_Panel" in c for c in conns), "Frame'e hover bağlanmadı")
    check(not any("MouseEnter:Baslik_Text" in c for c in conns), "TextLabel'e hover bağlanmadı")
    # Buton: Position (20,80), Size (120,40) → pivot (0.5,0.5) ile sol-üst köşe aynı kalmalı:
    #   yeni ofset = eski + Size/2 → X: 20+60 = 80, Y: 80+20 = 100
    pos3 = [ln.split("|") for ln in lines if ln.startswith("POS3|")]
    check(pos3 and pos3[0][3:5] == ["0.5", "0.5"], "buton pivotu (0,0)→(0.5,0.5) yapıldı")
    check(pos3 and float(pos3[0][1]) == 80 and float(pos3[0][2]) == 100,
          "pivot düzeltmesi sol-üst köşeyi korudu: X 20→80, Y 80→100 (görüntülenen %s,%s)"
          % (pos3[0][1], pos3[0][2]) if pos3 else "POS3 yok")
    pos8 = [ln.split("|") for ln in lines if ln.startswith("POS8|")]
    check(pos8 and float(pos8[0][1]) == 20 and float(pos8[0][2]) == 80 and pos8[0][3:5] == ["0", "0"],
          "UIListLayout'lu kapta pivot/konum DEĞİŞMEDİ")
    # hover_glow: from 0.15 → to 0. Sahte buton hover öncesi ImageTransparency=0.15 ile başlar.
    #   giriş (MouseEnter) → to = 0 · çıkış (MouseLeave) → hover öncesi = 0.15 (from değeri DEĞİL, gerçek başlangıç)
    btn_it = [t.split("|") for t in tweens if t.startswith("TWEEN|Buton_button|") and "|ImageTransparency|" in t]
    check(len(btn_it) >= 2 and btn_it[0][4] == "0" and btn_it[1][4] == "0.15",
          "hover_glow: giriş 0'a, çıkış hover öncesi 0.15'e döner (görülen hedefler: %s)"
          % [b[4] for b in btn_it[:2]])
    scale_btn = [t.split("|") for t in tweens if t.startswith("TWEEN|UIScale|") and "Scale|" in t]
    check(len(scale_btn) >= 3, "UIScale tween'leri üretildi (%d)" % len(scale_btn))

    print("== 5) determinizm")
    _p2, src2, _o2 = lua_plan_and_source("anime")
    check(src == src2, "aynı girdi → aynı LocalScript baytı")

    print()
    if fails:
        print("SONUÇ: BAŞARISIZ (%d kontrol)" % len(fails))
        return 1
    print("SONUÇ: GEÇTİ — seçim paritesi · derleme · davranış · determinizm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
