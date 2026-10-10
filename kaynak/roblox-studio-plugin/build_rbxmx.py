#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyImport Studio eklentisi — .lua → .rbxmx paketleyici

Neden var: Eklenti iki dosyada yaşıyor — `EasyImportStudioPlugin.lua` (okunabilir kaynak)
ve `EasyImportStudioPlugin.rbxmx` (Studio'ya kurulan paket). İkisi elle ayrı ayrı
güncellendiğinde kaçınılmaz olarak ayrışıyor ve kullanıcı **eski eklentiyi** kuruyor.

Bu betik .lua'yı tek doğruluk kaynağı kabul eder, .rbxmx'i ondan üretir.

Ayrıca **asistan modüllerini** (`assistant/runtime/lua/*.lua`) .lua içindeki
`-- <<EASYIMPORT_MODULES>>` işaretine gömer (A4b): EIRaw · EIStyle · EIFeatures_Spec · EIFeatures ·
EIModel · EILearn. Geliştirme .lua'sında bu modüller YOKTUR; asistan yalnızca paketlenmiş
.rbxmx içinde çalışır (gömülü değilse `Assist` sessizce devre dışı kalır ve v9 davranışı korunur).
Gömme deterministiktir: aynı modül baytları → aynı paket (zaman damgası yazılmaz, yalnız sha256).

Kullanım:
    python3 build_rbxmx.py            # .rbxmx'i .lua'dan üret (yazar)
    python3 build_rbxmx.py --check    # yazmadan doğrula (senkron mu?) — çıkış 0/1

Kaçış kuralı (mevcut dosyadan doğrulandı): XML metin düğümünde yalnızca
`&`, `<`, `>` kaçırılır; tırnaklar kaçırılmaz.
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LUA_PATH = os.path.join(HERE, "EasyImportStudioPlugin.lua")
RBXMX_PATH = os.path.join(HERE, "EasyImportStudioPlugin.rbxmx")
ASSIST_LUA_DIR = os.path.join(os.path.dirname(HERE), "assistant", "runtime", "lua")
MODULES_MARKER = "-- <<EASYIMPORT_MODULES>>"

# (Lua'da görünecek ad, dosya) — sıra ÖNEMLİ: hepsi saf Lua 5.3 uyumlu olmak zorunda.
MODULES = [
    ("EIRaw", "EIRaw.lua"),
    ("EIStyle", "EIStyle.lua"),
    ("EIFeaturesSpec", "EIFeatures_Spec.lua"),
    ("EIFeatures", "EIFeatures.lua"),
    ("EIModel", "EIModel.lua"),
    ("EILearn", "EILearn.lua"),
    ("EIAnim", "EIAnim.lua"),
]

HEADER = (
    '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
    "  <External>null</External>\n"
    "  <External>nil</External>\n"
    '  <Item class="Script" referent="RBX_EASYIMPORT_PLUGIN_01">\n'
    "    <Properties>\n"
    '      <string name="Name">EasyImportStudioPlugin</string>\n'
    '      <ProtectedString name="Source">'
)

# EasyImport öğesinin kapanışı (mevcut .rbxmx ile birebir; sonda satır sonu YOK).
FOOTER_EI = (
    "</ProtectedString>\n"
    "    </Properties>\n"
    "  </Item>\n"
)

# İkinci eklenti: UI Tools (ayrı araç çubuğu düğmesi + dock paneli).
# Aynı .rbxmx içinde ikinci üst düzey Script olarak gelir; kullanıcı tek dosyayı kurar, iki eklenti yüklenir.
UITOOLS_PLUGIN_FILE = "UIToolsPlugin.lua"
UITOOLS_CORE_FILE = "UIToolsCore.lua"   # UITools Script'inin alt ModuleScript'i (require(script.UIToolsCore))
UITOOLS_SCRIPT_REF = "RBX_UITOOLS_PLUGIN_01"
UITOOLS_CORE_REF = "RBX_UITOOLS_CORE_01"
FOOTER = "</roblox>"


def xml_escape(text):
    """XML metin düğümü kaçışı — mevcut .rbxmx dosyasıyla birebir uyumlu."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def module_block():
    """Gömülü asistan modülleri bloğunu üretir (deterministik)."""
    parts = ["-- >>> GÖMÜLÜ ASİSTAN MODÜLLERİ — build_rbxmx.py üretir; ELLE DÜZENLEMEYİN >>>"]
    digest = hashlib.sha256()
    for name, fname in MODULES:
        path = os.path.join(ASSIST_LUA_DIR, fname)
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        digest.update(fname.encode("utf-8"))
        digest.update(src.encode("utf-8"))
        parts.append("-- --- %s ← assistant/runtime/lua/%s ---" % (name, fname))
        parts.append("local %s = (function()" % name)
        parts.append(src.rstrip("\n"))
        parts.append("end)()")
    parts.append("-- modül özeti sha256: %s" % digest.hexdigest())
    parts.append("-- <<< GÖMÜLÜ ASİSTAN MODÜLLERİ <<<")
    return "\n".join(parts)


def inject_modules(lua_source):
    """İşaret satırını gömülü modül bloğuyla değiştirir; işaret yoksa hata."""
    lines = lua_source.split("\n")
    hit = [i for i, ln in enumerate(lines) if ln.startswith(MODULES_MARKER)]
    if len(hit) != 1:
        raise RuntimeError("işaret bir kez bulunmalı: %s (bulunan: %d)" % (MODULES_MARKER, len(hit)))
    out = lines[:hit[0]] + module_block().split("\n") + lines[hit[0] + 1:]
    return "\n".join(out)


def uitools_block():
    """UI Tools eklentisi: Script (UIToolsPlugin) + alt ModuleScript (UIToolsCore). Deterministik."""
    def read(name):
        with open(os.path.join(HERE, name), "r", encoding="utf-8") as fh:
            return fh.read()
    plugin_src = read(UITOOLS_PLUGIN_FILE)
    core_src = read(UITOOLS_CORE_FILE)
    return (
        '  <Item class="Script" referent="%s">\n' % UITOOLS_SCRIPT_REF
        + "    <Properties>\n"
        + '      <string name="Name">UIToolsPlugin</string>\n'
        + '      <ProtectedString name="Source">' + xml_escape(plugin_src) + "</ProtectedString>\n"
        + "    </Properties>\n"
        + '    <Item class="ModuleScript" referent="%s">\n' % UITOOLS_CORE_REF
        + "      <Properties>\n"
        + '        <string name="Name">UIToolsCore</string>\n'
        + '        <ProtectedString name="Source">' + xml_escape(core_src) + "</ProtectedString>\n"
        + "      </Properties>\n"
        + "    </Item>\n"
        + "  </Item>\n"
    )


def build(lua_source):
    """Tam .rbxmx metni: EasyImport eklentisi + UI Tools eklentisi."""
    return HEADER + xml_escape(inject_modules(lua_source)) + FOOTER_EI + uitools_block() + FOOTER


def main():
    check = "--check" in sys.argv

    with open(LUA_PATH, "r", encoding="utf-8") as fh:
        lua_source = fh.read()

    generated = build(lua_source)

    if check:
        if not os.path.exists(RBXMX_PATH):
            print("[!!] .rbxmx yok — '%s' çalıştır" % os.path.basename(__file__))
            return 1
        with open(RBXMX_PATH, "r", encoding="utf-8") as fh:
            current = fh.read()
        if current == generated:
            print("[OK] .rbxmx, .lua + gömülü modüller ile SENKRON (%d satır Lua, %d modül, %d KB)"
                  % (lua_source.count("\n") + 1, len(MODULES), len(generated) // 1024))
            return 0
        # farkın ilk yerini göster
        import difflib
        diff = list(difflib.unified_diff(
            current.split("\n"), generated.split("\n"),
            fromfile=".rbxmx (diskte)", tofile=".rbxmx (.lua'dan üretilen)", lineterm="", n=0))
        print("[!!] .rbxmx GERIDE KALMIŞ — %d fark satırı" % len(diff))
        for line in diff[:12]:
            print("     " + line[:110])
        print("     Düzeltmek için: python3 " + os.path.basename(__file__))
        return 1

    with open(RBXMX_PATH, "w", encoding="utf-8") as fh:
        fh.write(generated)
    print("[OK] .rbxmx üretildi: %d karakter (%d KB) · %d satır Lua + %d gömülü modül"
          % (len(generated), len(generated) // 1024, lua_source.count("\n") + 1, len(MODULES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
