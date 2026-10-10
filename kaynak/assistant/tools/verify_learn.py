#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YEREL ÖĞRENME KAPISI (JS ↔ fengari/Lua 5.3)

Asistanın öğrenmesi SUNUCUSUZ, kullanıcının cihazında çalışır. Figma tarafı `ei-learn.js`,
Studio tarafı `EILearn.lua` kullanır. İki uygulama **bit bit aynı** olmak zorundadır; aksi hâlde
kullanıcı Figma'da öğrettiği bir şeyin Studio'da geçerli olmadığını görür.

Test edilenler:
  1. Aynı olay dizisi → aynı kodlanmış metin (birebir eşitlik)
  2. Kodla-çöz (round-trip) → metin değişmiyor
  3. Sıralama (rankAnim) ve en çok kullanılanlar (topAnims) aynı
  4. Sınıf tercihi (preferredClass) aynı
  5. Budama (prune/fit) aynı ve boyut sınırı korunuyor
  6. EILearn.lua Luau yasaklı API'lerden temiz

Kullanım:  python3 tools/verify_learn.py     (EASYIMPORT_LUA_BIN de desteklenir)
Çıkış: 0 = geçti, 1 = başarısız
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from luatable import dumps as lua_dumps  # noqa: E402
from verify_runtime import luau_lint  # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")
VENDOR = os.path.join(HERE, "vendor")

ANIMS = ["pop_in_scale", "bounce_soft", "shine_sweep", "glow_pulse", "ray_spin",
         "sparkle_twinkle", "hover_lift", "press_squash", "fade_in", "slide_up"]
CONTEXTS = [
    ("cartoon", "ImageButton", "primary", "-"),
    ("anime", "ImageButton", "icon", "glow"),
    ("stud", "Frame", "panel", "-"),
    ("belirsiz", "TextLabel", "title", "-"),
    ("anime", "ImageLabel", "icon", "shine"),
]
RANK_CTX = 0


# --------------------------------------------------------------------------- ortak olay dizisi
def build_events():
    """Deterministik olay listesi (sabit LCG — iki dil aynı veriyi alır)."""
    events = []
    seed = 12345
    for i in range(600):
        seed = (seed * 1103515245 + 12345) % (2 ** 31)
        ctx = CONTEXTS[seed % len(CONTEXTS)]
        anim = ANIMS[(seed // 7) % len(ANIMS)]
        accepted = ((seed // 13) % 10) < 7          # ~%70 kabul
        events.append({"kind": "anim", "ctx": ctx, "anim": anim, "ok": accepted})
        if i % 40 == 0:
            seed = (seed * 1103515245 + 12345) % (2 ** 31)
            events.append({"kind": "cls", "ctx": CONTEXTS[seed % len(CONTEXTS)],
                           "cls": ["ImageLabel", "TextLabel", "Frame"][(seed // 3) % 3]})
    return events


def build_crowd():
    """Budama testi için 300 bağlamlık kalabalık (olay listesi)."""
    events = []
    for i in range(300):
        ctx = ["belirsiz", "Frame", "slot%d" % i, "-"]
        events.append({"kind": "anim", "ctx": ctx, "anim": ANIMS[i % len(ANIMS)], "ok": True})
        if i % 5 == 0:
            events.append({"kind": "anim", "ctx": ctx, "anim": ANIMS[(i + 3) % len(ANIMS)], "ok": False})
    return events


# --------------------------------------------------------------------------- JS koşucusu
JS_RUNNER = r"""
const EILearn = require(process.argv[2] + '/ei-learn.js');
const payload = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));

function apply(events) {
  const st = EILearn.newState();
  for (const e of events) {
    const ctx = EILearn.ctxKey(e.ctx[0], e.ctx[1], e.ctx[2], e.ctx[3]);
    if (e.kind === 'anim') EILearn.recordAnim(st, ctx, e.anim, e.ok);
    else EILearn.recordClass(st, ctx, e.cls, 1);
  }
  return st;
}

const st = apply(payload.events);
const enc = EILearn.encode(st);
const rt = EILearn.encode(EILearn.decode(enc));

const ranks = payload.rankCtxs.map(c => {
  const ctx = EILearn.ctxKey(c[0], c[1], c[2], c[3]);
  return { ctx: ctx, rank: EILearn.rankAnim(st, ctx, payload.candidates),
           top: EILearn.topAnims(st, ctx, 4),
           pref: EILearn.preferredClass(st, ctx) };
});

const crowd = apply(payload.crowd);
const crowdBefore = EILearn.encode(crowd);
EILearn.fit(crowd, 40, 4096);
const crowdAfter = EILearn.encode(crowd);

process.stdout.write(JSON.stringify({
  enc: enc, roundtrip: rt === enc, stats: EILearn.stats(st),
  ranks: ranks,
  crowdBytesBefore: EILearn.byteLen(crowdBefore),
  crowdBytesAfter: EILearn.byteLen(crowdAfter),
  crowdCtx: EILearn.countContexts(crowd),
  crowdEnc: crowdAfter
}));
"""


# --------------------------------------------------------------------------- Lua koşucusu
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

LUA_SERIALIZER = r"""
local function esc(s)
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end
local function isArray(t)
  local n, m = 0, 0
  for k in pairs(t) do
    if type(k) ~= 'number' or k ~= math.floor(k) or k < 1 then return false end
    n = n + 1
    if k > m then m = k end
  end
  return n == m and m > 0
end

local function ser(v)
  local t = type(v)
  if t == 'nil' then return 'null'
  elseif t == 'boolean' then return v and 'true' or 'false'
  elseif t == 'number' then
    if v ~= v then return '0' end
    if v == math.huge then return '1e308' end
    if v == -math.huge then return '-1e308' end
    if v == math.floor(v) and math.abs(v) < 1e15 then return string.format('%.0f', v) end
    return string.format('%.17g', v)
  elseif t == 'string' then return '"' .. esc(v) .. '"'
  elseif t == 'table' then
    if isArray(v) then
      local parts = {}
      for j = 1, #v do parts[j] = ser(v[j]) end
      return '[' .. table.concat(parts, ',') .. ']'
    end
    local ks, i = {}, 1
    for k, _ in pairs(v) do ks[i] = tostring(k); i = i + 1 end
    table.sort(ks)
    local parts = {}
    for j = 1, #ks do
      parts[j] = '"' .. esc(ks[j]) .. '":' .. ser(v[ks[j]])
    end
    return '{' .. table.concat(parts, ',') .. '}'
  end
  return 'null'
end
"""

LUA_MAIN = r"""
local function apply(events)
  local st = EILearn.newState()
  for i = 1, #events do
    local e = events[i]
    local c = e.ctx
    local ctx = EILearn.ctxKey(c[1], c[2], c[3], c[4])
    if e.kind == 'anim' then EILearn.recordAnim(st, ctx, e.anim, e.ok)
    else EILearn.recordClass(st, ctx, e.cls, 1) end
  end
  return st
end

local st = apply(EVENTS)
local enc = EILearn.encode(st)
local rt = EILearn.encode(EILearn.decode(enc))

local ranks = {}
for i = 1, #RANK_CTXS do
  local c = RANK_CTXS[i]
  local ctx = EILearn.ctxKey(c[1], c[2], c[3], c[4])
  local r = EILearn.rankAnim(st, ctx, CANDIDATES)
  local top = EILearn.topAnims(st, ctx, 4)
  local pref = EILearn.preferredClass(st, ctx)
  ranks[i] = { ctx = ctx, rank = r, top = top, pref = pref }
end

local crowd = apply(CROWD)
local crowdBefore = EILearn.encode(crowd)
EILearn.fit(crowd, 40, 4096)
local crowdAfter = EILearn.encode(crowd)

io.write(ser({
  enc = enc, roundtrip = (rt == enc), stats = EILearn.stats(st),
  ranks = ranks,
  crowdBytesBefore = EILearn.byteLen(crowdBefore),
  crowdBytesAfter = EILearn.byteLen(crowdAfter),
  crowdCtx = EILearn.countContexts(crowd),
  crowdEnc = crowdAfter
}))
"""


def _run(node_args, program=None, env_extra=None):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(node_args)
        runner = fh.name
    files = [runner]
    try:
        args = ["node", runner]
        if program is not None:
            with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh2:
                fh2.write(program)
                files.append(fh2.name)
            args.append(files[-1])
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        r = subprocess.run(args, capture_output=True, text=True, timeout=300, env=env)
        if r.returncode != 0:
            raise RuntimeError((r.stdout or "")[:1500] + "\n" + (r.stderr or "")[:2500])
        return r.stdout
    finally:
        for f in files:
            os.unlink(f)


def run_js(events, crowd, payload_path):
    with open(payload_path, "w", encoding="utf-8") as fh:
        json.dump({"events": events, "crowd": crowd,
                   "candidates": ANIMS, "rankCtxs": [list(c) for c in CONTEXTS]}, fh)
    out = _run(JS_RUNNER, None)
    # JS koşucusu argümanları kendi içinde okur; aşağıdaki sarmalayıcı ile verilir
    return json.loads(out)


def run_lua(events, crowd, lua_bin=None):
    src = open(os.path.join(LUA_DIR, "EILearn.lua"), encoding="utf-8").read()
    lua_src = src.replace("return EILearn", "return EILearn")   # dosya zaten return ediyor
    prog = (
        LUA_SERIALIZER + "\n"
        "local EILearn = (function()\n" + lua_src + "\nend)()\n"
        "local EVENTS = " + lua_dumps(events) + "\n"
        "local CROWD = " + lua_dumps(crowd) + "\n"
        "local CANDIDATES = " + lua_dumps(ANIMS) + "\n"
        "local RANK_CTXS = " + lua_dumps([list(c) for c in CONTEXTS]) + "\n"
        + LUA_MAIN
    )
    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(prog)
            tmp = fh.name
        try:
            r = subprocess.run([lua_bin, tmp], capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                raise RuntimeError((r.stdout or "")[:1500] + "\n" + (r.stderr or "")[:2500])
            return json.loads(r.stdout)
        finally:
            os.unlink(tmp)

    if not os.path.isdir(os.path.join(VENDOR, "fengari")):
        raise RuntimeError("fengari bulunamadı: %s" % VENDOR)
    out = _run(FENGARI_RUNNER, prog, {"NODE_PATH": VENDOR})
    return json.loads(out)


def main():
    lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
    print("=" * 74)
    print("YEREL ÖĞRENME KAPISI — ei-learn.js  ↔  EILearn.lua")
    print("=" * 74)

    # --- luau-lint ---
    hits = luau_lint(os.path.join(LUA_DIR, "EILearn.lua"))
    if hits:
        print("  [!!] Luau ihlali (%d):" % len(hits))
        for ln, txt, why in hits[:8]:
            print("      satır %-5d %-45s %s" % (ln, txt, why))
        return 1
    print("  [OK] luau-lint -> EILearn.lua temiz")

    events = build_events()
    crowd = build_crowd()
    print("  [i] olay dizisi: %d animasyon/sınıf olayı · budama testi: %d bağlam"
          % (len(events), 300))

    # JS koşucusunu argümanlarla çalıştır
    payload_path = os.path.join(tempfile.gettempdir(), "ei_learn_payload.json")
    with open(payload_path, "w", encoding="utf-8") as fh:
        json.dump({"events": events, "crowd": crowd,
                   "candidates": ANIMS, "rankCtxs": [list(c) for c in CONTEXTS]}, fh)

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JS_RUNNER)
        runner = fh.name
    try:
        r = subprocess.run(["node", runner, JS_DIR, payload_path],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print("  [!!] JS hatası:\n" + (r.stderr or "")[:2000])
            return 1
        js = json.loads(r.stdout)
    finally:
        os.unlink(runner)
        os.unlink(payload_path)
    print("  [OK] js  -> %d bağlam · %d bayt · %d olay"
          % (js["stats"]["contexts"], js["stats"]["bytes"], js["stats"]["events"]))

    lua = run_lua(events, crowd, lua_bin)
    print("  [OK] lua -> %d bağlam · %d bayt · %d olay"
          % (lua["stats"]["contexts"], lua["stats"]["bytes"], lua["stats"]["events"]))

    # --- karşılaştırma ---
    bad = []

    def cmp(a, b, what):
        if a != b:
            bad.append(what)

    cmp(js["enc"], lua["enc"], "kodlanmış metin (encode)")
    cmp(js["roundtrip"], lua["roundtrip"], "round-trip bayrağı")
    cmp(js["crowdEnc"], lua["crowdEnc"], "budama sonrası metin")
    cmp(js["crowdCtx"], lua["crowdCtx"], "budama sonrası bağlam sayısı")
    cmp(js["stats"], lua["stats"], "istatistikler")
    cmp(js["ranks"], lua["ranks"], "sıralama + tercih sonuçları")
    cmp(js["crowdBytesBefore"], lua["crowdBytesBefore"], "kalabalık metin boyu (önce)")

    if bad:
        print("-" * 74)
        print("  [!!] %d alanda FARK:" % len(bad))
        for w in bad:
            print("      - " + w)
        if js["enc"] != lua["enc"]:
            a, b = js["enc"].split("\n"), lua["enc"].split("\n")
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else "<yok>"
                y = b[i] if i < len(b) else "<yok>"
                if x != y:
                    print("      ilk fark satır %d:\n        js : %s\n        lua: %s" % (i, x, y))
                    break
        print("-" * 74)
        print("SONUÇ: BAŞARISIZ")
        return 1

    # --- ek kontroller (JS tarafından) ---
    problems = []
    if not js["roundtrip"]:
        problems.append("kodla-çöz metni değiştirdi")
    if js["crowdCtx"] > 40:
        problems.append("budama 40 bağlam sınırını aşmadı (%d)" % js["crowdCtx"])
    if js["crowdBytesAfter"] > 4096:
        problems.append("boyut sınırı aşıldı (%d bayt)" % js["crowdBytesAfter"])
    if js["crowdBytesBefore"] <= js["crowdBytesAfter"]:
        problems.append("budama hiç küçültmedi")

    print("  [i] kodlanmış boyut: %d bayt (%d olay, %d bağlam) — fazlasıyla küçük"
          % (js["stats"]["bytes"], js["stats"]["events"], js["stats"]["contexts"]))
    print("  [i] budama: %d bağlam/%d bayt → %d bağlam/%d bayt (sınır 40 bağlam · 4096 bayt)"
          % (300, js["crowdBytesBefore"], js["crowdCtx"], js["crowdBytesAfter"]))

    if problems:
        print("-" * 74)
        for p in problems:
            print("  [!!] " + p)
        print("SONUÇ: BAŞARISIZ")
        return 1

    print("-" * 74)
    print("SONUÇ: GEÇTİ — iki dilde öğrenme BİREBİR aynı (kodlama, sıralama, budama)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
