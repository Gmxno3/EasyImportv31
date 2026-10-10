#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec/features.json -> çalışma zamanı dosyaları üretir  [A1]

Çıktılar:
  runtime/lua/EIFeatures_Spec.lua     (Lua table — Studio'da require edilir, JSON parse gerekmez)
  runtime/js/ei-features-spec.js      (Node + Figma ikisi de kullanabilir)

Böylece üç dil de AYNI spec'i okur; özellik eklemek tek komutla üçünü günceller.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import luatable  # noqa: E402

SPEC_PATH = os.path.join(ROOT, "spec", "features.json")
LUA_OUT = os.path.join(ROOT, "runtime", "lua", "EIFeatures_Spec.lua")
JS_OUT = os.path.join(ROOT, "runtime", "js", "ei-features-spec.js")

# Lua'ya sadece gereken alanlar gider (dosya boyutu için)
KEEP_TOP = ("format", "version", "dim")


def main():
    with open(SPEC_PATH, "r", encoding="utf-8") as fh:
        spec = json.load(fh)

    lua_spec = {k: spec[k] for k in KEEP_TOP if k in spec}
    lua_spec["features"] = spec["features"]

    os.makedirs(os.path.dirname(LUA_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(JS_OUT), exist_ok=True)

    with open(LUA_OUT, "w", encoding="utf-8") as fh:
        fh.write("-- OTOMATİK ÜRETİLDİ — elle düzenleme.\n")
        fh.write("-- Kaynak: spec/features.json  (üretici: tools/build_runtime.py)\n")
        fh.write("-- spec sürümü: %s   vektör boyu: %d\n\n" % (spec["version"], spec["dim"]))
        fh.write("return ")
        fh.write(luatable.dumps(lua_spec))
        fh.write("\n")

    with open(JS_OUT, "w", encoding="utf-8") as fh:
        fh.write("/* OTOMATİK ÜRETİLDİ — elle düzenleme.\n")
        fh.write("   Kaynak: spec/features.json  (üretici: tools/build_runtime.py)\n")
        fh.write("   spec sürümü: %s   vektör boyu: %d */\n" % (spec["version"], spec["dim"]))
        fh.write("var EI_FEATURES_SPEC = ")
        fh.write(json.dumps(lua_spec, ensure_ascii=False, separators=(",", ":")))
        fh.write(";\n")
        fh.write("if (typeof module !== 'undefined' && module.exports) "
                 "{ module.exports = { spec: EI_FEATURES_SPEC }; }\n")

    print("üretildi:")
    print("  %s  (%d bayt)" % (os.path.relpath(LUA_OUT, ROOT), os.path.getsize(LUA_OUT)))
    print("  %s  (%d bayt)" % (os.path.relpath(JS_OUT, ROOT), os.path.getsize(JS_OUT)))
    print("  spec sürümü: %s   vektör boyu: %d" % (spec["version"], spec["dim"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
