#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3 KAPISI — ÖĞRETMEN BİREBİRLİĞİ (Lua ↔ Python)

Model etiketleri **mevcut kural motorundan** öğreniyor (öğretmen). Öğretmenin Python
karşılığı (`rules_teacher.py`) ile Studio eklentisinin GERÇEK Lua kodu (`parseLayerTags` +
`decideClass`, `-- <<PURE_BEGIN>> … <<PURE_END>>` arası) birebir aynı karar vermek zorundadır.
Aksi hâlde model, Studio'da hiç uygulanmayacak bir kuralı öğrenir.

Bu test üç şeyi kanıtlar:
  1. Eklentinin tamamı Lua olarak **derlenebiliyor** (sözdizimi).
  2. Eklenti Luau yasaklı API'leri içermiyor (luau-lint).
  3. 4 export örneği + 40 zorlu ad → Lua ve Python **aynı** (temiz ad, sınıf) çiftini üretiyor.

Kullanım:
    python3 tools/verify_teacher.py
    EASYIMPORT_LUA_BIN=lua5.3 python3 tools/verify_teacher.py   # sistem Lua'sı varsa

Çıkış: 0 = geçti, 1 = başarısız
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import rules_teacher  # noqa: E402
from luatable import dumps as lua_dumps  # noqa: E402
from verify_runtime import luau_lint  # noqa: E402

PLUGIN_LUA = os.path.join(os.path.dirname(ROOT), "roblox-studio-plugin", "EasyImportStudioPlugin.lua")
FIX_DIR = os.path.join(ROOT, "datasets", "fixtures", "exports")
# Tüm fixture'lar (yeni örnek eklendiğinde kapı otomatik kapsar)
SAMPLES = sorted(f for f in os.listdir(FIX_DIR) if f.endswith(".json"))

# ---------------------------------------------------------------------------
# ZORLU AD LİSTESİ — kural motorunun bütün dallarını ve dil tuzaklarını hedefler
# (her satır: ad, kind, image?, scroll?)
# ---------------------------------------------------------------------------
TRICKY = [
    ("Play_Button", "frame", None, None),
    ("PlayButton", "frame", None, None),
    ("play btn", "frame", None, None),
    ("Buton", "frame", None, None),
    ("Top_buttons", "frame", None, None),           # çoğul → düğme DEĞİL
    ("Hero_images", "frame", None, None),           # çoğul → görsel sınıfı zorlamaz
    ("Close_Button", "frame", "Close_1-3.png", None),
    ("closebtn", "frame", "closebtn_1-4.png", None),
    ("icon_home", "frame", "home_1-5.png", None),
    ("Player_Name", "text", None, None),            # "_Name" bilinen ek değil → korunur
    ("Score_Label", "text", None, None),            # "_Label" korunur (listedeki "textlabel" değil)
    ("Score_TextLabel", "text", None, None),        # açık sınıf → zorlar
    ("hp_bar", "frame", None, None),
    ("KQWEAMKFWImageButton", "frame", "x_1-6.png", None),
    ("İMAGEBUTTON", "frame", "y_1-7.png", None),    # Türkçe İ → i sayılır
    ("ıcon", "frame", "z_1-8.png", None),           # Türkçe ı → i sayılır
    ("Aspect_Frame", "frame", None, None),
    ("#img_art", "frame", "art_1-9.png", None),
    ("img:hero", "frame", "hero_1-10.png", None),
    ("", "text", None, None),                       # boş ad → "Element"
    ("   ", "frame", None, None),                   # yalnızca boşluk
    ("Item_List", "frame", None, "VERTICAL"),
    ("_scroll", "frame", None, None),
    ("Canvas_Group", "frame", None, None),
    ("MyViewport", "frame", None, None),
    ("vpf", "frame", None, None),
    ("Video_BG", "frame", None, None),
    ("input_field", "text", None, None),
    ("Chat_Textbox", "text", None, None),
    ("Filter_box", "text", None, None),
    ("Hover_Glow", "frame", None, None),
    ("Clicked_State", "frame", None, None),
    ("Ignore_Me", "frame", None, None),
    ("Nodim_Panel", "frame", None, None),
    ("divider_1px", "frame", None, None),
    ("UIGrid_Item", "frame", None, None),
    ("Gray_Overlay", "frame", None, None),
    ("Sadə_ad", "frame", None, None),               # ASCII dışı harf
    ("sekme\tile\ttab", "frame", None, None),       # metin içinde sekme
    ("satır\nkırık", "text", None, None),           # metin içinde yeni satır
    ("quote\"ve\\ters", "frame", None, None),       # kaçış karakterleri
]


# ---------------------------------------------------------------------------
FENGARI_RUNNER = r"""
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

# Lua çıktısını güvenle taşımak için minik serileştirici (metin kaçışları dahil)
LUA_SERIALIZER = r"""
local function esc(s)
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end
"""

LUA_MAIN = r"""
local out = {}
for i = 1, #ITEMS do
  local it = ITEMS[i]
  local clean, tags = parseLayerTags(it.name)
  local cls = decideClass(it, tags)
  out[i] = '["' .. esc(clean) .. '","' .. esc(cls) .. '"]'
end
io.write('[' .. table.concat(out, ',') .. ']\n')
"""


VENDOR = os.path.join(HERE, "vendor")

# ---------------------------------------------------------------------------
# Luau → Lua 5.3 uyarlaması (YALNIZCA TEST İÇİN)
# ---------------------------------------------------------------------------
# Eklenti Luau'ya özel `+=` / `-=` / `*=` / `/=` / `%=` / `..=` operatörlerini kullanıyor.
# Gömülü Lua 5.3 VM'i (fengari) bunları derleyemez. Aşağıdaki dönüşüm bunları **anlamsal olarak
# birebir eşdeğer** uzun forma çevirir:  `a.b += 1`  →  `a.b = a.b + 1`
# Gerçek eklenti dosyası DEĞİŞMEZ; yalnızca test kopyası dönüştürülür.
_RE_COMPOUND_ANY = re.compile(
    r'(?<![\w.:"\'])([A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[[^\]]*\])*)\s*(\+|-|\*|/|%|\.\.)=')


def luau_to_lua(src):
    """`LHS op= RHS` → `LHS = LHS op RHS` (satır içi `if ... then X += 1 end` dâhil).

    Dönüşüm semantik olarak birebir; yalnızca test kopyasında uygulanır.
    """
    def repl(m):
        lhs, op = m.group(1), m.group(2)
        return "%s = %s %s " % (lhs, lhs, op)

    return _RE_COMPOUND_ANY.subn(repl, src)


FENGARI_RUNNER = r"""
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

# Lua çıktısını güvenle taşımak için minik serileştirici (metin kaçışları dahil)
LUA_SERIALIZER = r"""
local function esc(s)
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end
"""

LUA_MAIN = r"""
local out = {}
for i = 1, #ITEMS do
  local it = ITEMS[i]
  local clean, tags = parseLayerTags(it.name)
  local cls = decideClass(it, tags)
  out[i] = '["' .. esc(clean) .. '","' .. esc(cls) .. '"]'
end
io.write('[' .. table.concat(out, ',') .. ']\n')
"""


VENDOR = os.path.join(HERE, "vendor")

# ---------------------------------------------------------------------------
# Luau → Lua 5.3 uyarlaması (YALNIZCA TEST İÇİN)
# ---------------------------------------------------------------------------
# Eklenti Luau'ya özel `+=` / `-=` / `*=` / `/=` / `%=` / `..=` operatörlerini kullanıyor.
# Gömülü Lua 5.3 VM'i (fengari) bunları derleyemez. Aşağıdaki dönüşüm bunları **anlamsal olarak
# birebir eşdeğer** uzun forma çevirir:  `a.b += 1`  →  `a.b = a.b + 1`
# Gerçek eklenti dosyası DEĞİŞMEZ; yalnızca test kopyası dönüştürülür.
def run_fengari(program):
    """Programı fengari (gömülü Lua 5.3) ile koşturur; sistem Lua'sı varsa onu kullanır."""
    lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(program)
            prog_lua = fh.name
        try:
            r = subprocess.run([lua_bin, prog_lua], capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError("%s hatası:\n%s\n%s"
                                   % (lua_bin, (r.stdout or "")[:2000], (r.stderr or "")[:2000]))
            return r.stdout
        finally:
            os.unlink(prog_lua)

    if not os.path.isdir(os.path.join(VENDOR, "fengari")):
        raise RuntimeError("fengari bulunamadı: %s" % VENDOR)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(FENGARI_RUNNER)
        runner = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(program)
        prog = fh.name
    # ÇIKTI BORUYLA DEĞİL DOSYAYLA TAŞINIR (2026-10 dersi):
    # fengari `io.write` -> `fs.writeSync(1, …)`. fd 1 bir BORU iken Node onu non-blocking yapar ve
    # yazma yarıda kesilir; fengari bunu yutup devam eder → çıktı SESSİZCE kısalır.
    # Ölçüm: 1044 satırlık gerçek tasarım koşumu boruyla 615 satır geldi (65.647 bayt),
    # dosyayla 1044 satır (110.434 bayt). Bu yüzden her zaman geçici DOSYA kullanılır.
    try:
        env = dict(os.environ)
        env["NODE_PATH"] = VENDOR
        with tempfile.TemporaryFile() as out_fh, tempfile.TemporaryFile() as err_fh:
            r = subprocess.run(["node", runner, prog], stdout=out_fh, stderr=err_fh,
                               timeout=300, env=env)
            out_fh.seek(0)
            err_fh.seek(0)
            stdout = out_fh.read().decode("utf-8", "replace")
            stderr = err_fh.read().decode("utf-8", "replace")
        if r.returncode != 0:
            raise RuntimeError("fengari hatası:\n%s\n%s" % (stdout[:2000], stderr[:2000]))
        return stdout
    finally:
        os.unlink(runner)
        os.unlink(prog)


def extract_pure_block(path):
    src = open(path, encoding="utf-8").read()
    a = src.index("-- <<PURE_BEGIN>>")
    b = src.index("-- <<PURE_END>>")
    return src[a:b], src


def flatten_items(doc):
    """Export dökümanındaki tüm katmanları (kök dâhil) sırayla düzleştirir."""
    out = []

    def rec(item):
        out.append(item)
        for ch in item.get("children") or []:
            rec(ch)

    rec(doc["root"])
    return out


def simplify(item):
    """Lua tarafına giden minimal katman: karar yalnızca bu alanlara bakıyor."""
    return {
        "name": item.get("name"),
        "kind": item.get("kind"),
        "image": item.get("image"),
        "scroll": item.get("scroll"),
    }


def main():
    print("=" * 74)
    print("A3 KAPISI — ÖĞRETMEN (Studio Lua  ↔  Python rules_teacher)")
    print("=" * 74)
    if not os.path.exists(PLUGIN_LUA):
        print("  [!!] eklenti bulunamadı: %s" % PLUGIN_LUA)
        return 1

    pure_src, full_src = extract_pure_block(PLUGIN_LUA)
    pure_src, _pure_conv = luau_to_lua(pure_src)
    print("  [OK] saf blok çıkarıldı (%d satır)" % pure_src.count("\n"))

    # --- 1) Eklentinin tamamı derleniyor mu? (çalıştırmadan yalnızca derleme) ---
    # Not: eklentinin içinde [==[ ... ]==] geçtiği için uzun parantez seviyesi 5 seçildi.
    lua_src, converted = luau_to_lua(full_src)
    compile_probe = (
        "local chunk, err = load([=====[\n" + lua_src + "\n]=====])\n"
        "if not chunk then io.write('HATA: ' .. tostring(err)) os.exit(1) end\n"
        "io.write('OK')\n"
    )
    out = run_fengari(compile_probe)
    if out.strip().startswith("HATA"):
        print("  [!!] eklenti derlenemedi:\n" + out[:1500])
        return 1
    print("  [OK] eklenti derlendi (sözdizimi temiz; %d Luau operatörü test için uzun forma çevrildi)"
          % converted)

    # --- 2) Luau yasaklı API'ler ---
    hits = luau_lint(PLUGIN_LUA)
    if hits:
        print("  [!!] Luau ihlali (%d):" % len(hits))
        for ln, txt, why in hits[:8]:
            print("      satır %-5d %-45s %s" % (ln, txt, why))
        return 1
    print("  [OK] luau-lint -> eklenti temiz")

    # --- 3) Karşılaştırma ---
    items = []
    for name in SAMPLES:
        with open(os.path.join(FIX_DIR, name), encoding="utf-8") as fh:
            doc = json.load(fh)
        for it in flatten_items(doc):
            items.append(simplify(it))
    sample_n = len(items)
    for ad, kind, image, scroll in TRICKY:
        items.append({"name": ad, "kind": kind, "image": image, "scroll": scroll})

    lua_items = lua_dumps(items)
    program = pure_src + "\n" + LUA_SERIALIZER + "\nlocal ITEMS = " + lua_items + "\n" + LUA_MAIN
    raw = run_fengari(program)
    lua_res = [tuple(x) for x in json.loads(raw)]
    py_res = [rules_teacher.classify(it) for it in items]

    if len(lua_res) != len(py_res):
        print("  [!!] sonuç sayısı uyuşmuyor: lua=%d python=%d" % (len(lua_res), len(py_res)))
        return 1

    bad = []
    for i, (l, p) in enumerate(zip(lua_res, py_res)):
        if tuple(l) != tuple(p):
            bad.append((i, items[i], p, l))

    print("  [OK] %d örnek katman (4 export: %d + zorlu ad: %d) karşılaştırıldı"
          % (len(items), sample_n, len(TRICKY)))

    if bad:
        print("-" * 74)
        print("  [!!] %d FARK bulundu:" % len(bad))
        for i, it, p, l in bad[:15]:
            print("      #%-4d ad=%-28r" % (i, (it.get("name") or "")[:28]))
            print("           python: %-16s %s" % p[1], repr(p[0]))
            print("           lua   : %-16s %s" % l[1], repr(l[0]))
        print("-" * 74)
        print("SONUÇ: BAŞARISIZ — öğretmen iki dilde ayrışıyor")
        return 1

    # Kapsama raporu: hangi sınıflar üretildi?
    from collections import Counter
    dist = Counter(c for _, c in py_res)
    print("  [i] üretilen sınıf dağılımı: " + ", ".join("%s=%d" % kv for kv in sorted(dist.items())))
    print("-" * 74)
    print("SONUÇ: GEÇTİ — Lua ve Python birebir aynı kararı veriyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
