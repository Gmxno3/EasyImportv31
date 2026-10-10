// Lua dosyasını fengari (Lua 5.3 VM) içinde çalıştırır; son değeri stdout'a yazar.
const fs = require('fs');
const path = require('path');
const { lua, lauxlib, lualib, to_luastring, to_jsstring } = require(process.env.FENGARI || require('path').join(__dirname, '../../assistant/tools/vendor/fengari/fengari.js'));
const file = process.argv[2];
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
// Ortak yardımcı: __SRC[name] ile modül kaynakları enjekte edilir
const pre = process.argv.slice(3).map(p => {
  const [k, f] = p.split('=');
  return `__SRC[${JSON.stringify(k)}] = ${JSON.stringify(fs.readFileSync(f, 'utf8'))}`;
}).join('\n');
const code = `__SRC = {}\n${pre}\n` + fs.readFileSync(file, 'utf8');
const st = lauxlib.luaL_dostring(L, to_luastring(code));
if (st !== 0) {
  console.log('LUA HATASI: ' + to_jsstring(lua.lua_tostring(L, -1)));
  process.exit(1);
}
const out = lua.lua_gettop(L) > 0 ? to_jsstring(lua.lua_tostring(L, -1) || to_luastring('')) : '';
fs.writeSync(1, out + '\n');
