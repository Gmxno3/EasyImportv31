#!/bin/sh
# UI Tools testlerini çalıştırır (fengari = Lua 5.3 VM; Roblox dışı, mock ortam).
# Kullanım: sh run.sh   (kökten bağımsız çalışır)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/../../roblox-studio-plugin"
VENDOR="$HERE/../../assistant/tools/vendor"
export NODE_PATH="$VENDOR"
echo "== çekirdek (UIToolsCore)"; node "$HERE/run.js" "$HERE/test_core.lua" core="$ROOT/UIToolsCore.lua"
echo "== plugin (UIToolsPlugin + mock Roblox)"; node "$HERE/run.js" "$HERE/test_plugin.lua" core="$ROOT/UIToolsCore.lua" plugin="$ROOT/UIToolsPlugin.lua"
echo "== mutasyon (bilinçli hatalar yakalanmalı; çalıştırmak için: python3 mutate.py)"
