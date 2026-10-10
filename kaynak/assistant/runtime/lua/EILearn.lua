-- EasyImport — YEREL ÖĞRENME (Studio tarafı)
--
-- `runtime/js/ei-learn.js`'in BİREBİR karşılığı. Sunucu yok; asistan kullanıcının kendi
-- seçimlerinden kendi cihazında öğrenir. Sayaçlar tamsayıdır, bu yüzden JS ile Lua
-- bit bit aynı sonucu üretir (assistant/tools/verify_learn.py kapısı).
--
-- Studio notu: plugin:SetSetting anahtarı `.` veya `\` İÇERMEMELİ (sessizce başarısız olur).
-- Önerilen anahtar: "EasyImportLearn" — değeri bu modülün encode() çıktısıdır (metin).
--
-- Saf Lua 5.1/Luau: hiçbir Roblox API'si kullanılmaz.

local EILearn = {}

local VERSION = 1
local DEFAULT_CAP = 400
local DEFAULT_SIZE_CAP = 65536

local function sanitize(tok)
  local s = tostring(tok == nil and "-" or tok)
  local out = {}
  for i = 1, #s do
    local b = string.byte(s, i)
    -- A-Z de geçerli: sınıf adları ("TextLabel") küçültülmemeli.
    local ok = (b >= 97 and b <= 122) or (b >= 65 and b <= 90) or (b >= 48 and b <= 57)
      or b == 95 or b == 45 or b == 124 or b == 35
    out[i] = string.char(ok and b or 95)
  end
  local r = table.concat(out)
  if r == "" then r = "-" end
  return r
end

local function lower(s)
  local t = tostring(s == nil and "" or s)
  local out = {}
  for i = 1, #t do
    local b = string.byte(t, i)
    out[i] = string.char((b >= 65 and b <= 90) and (b + 32) or b)
  end
  return table.concat(out)
end

local function toInt(s)
  local n = tonumber(s)
  if not n then return 0 end
  n = math.floor(n)
  if n < 0 then return 0 end
  return n
end

function EILearn.newState()
  return { v = VERSION, anim = {}, cls = {}, events = 0, exports = 0 }
end

function EILearn.ctxKey(style, cls, role, fx)
  return table.concat({ sanitize(lower(style)), sanitize(lower(cls)), sanitize(lower(role)), sanitize(lower(fx)) }, "|")
end

local function ensureAnim(st, ctx)
  if not st.anim[ctx] then st.anim[ctx] = {} end
  return st.anim[ctx]
end

local function ensureCls(st, ctx)
  if not st.cls[ctx] then st.cls[ctx] = {} end
  return st.cls[ctx]
end

function EILearn.recordAnim(st, ctx, animId, accepted)
  local m = ensureAnim(st, ctx)
  local id = sanitize(animId)
  if not m[id] then m[id] = { 0, 0 } end
  if accepted then m[id][1] = m[id][1] + 1 else m[id][2] = m[id][2] + 1 end
  st.events = st.events + 1
  return st
end

function EILearn.recordClass(st, ctx, clsName, n)
  local m = ensureCls(st, ctx)
  local id = sanitize(clsName)
  if not m[id] then m[id] = 0 end
  m[id] = m[id] + (n == nil and 1 or n)
  st.events = st.events + 1
  return st
end

function EILearn.exportBump(st)
  st.exports = st.exports + 1
  return st
end

-- Yumuşatılmış kabul oranı: (2c+1) / (2(c+r)+2). Yalnızca tamsayı girdi → iki dilde birebir.
function EILearn.scoreAnim(st, ctx, animId)
  local m = st.anim[ctx]
  local e = m and m[sanitize(animId)] or nil
  if not e then return 0.5 end
  local c, r = e[1], e[2]
  return (2 * c + 1) / (2 * (c + r) + 2)
end

function EILearn.obsOf(st, ctx, animId)
  local m = st.anim[ctx]
  local e = m and m[sanitize(animId)] or nil
  if not e then return 0 end
  return e[1] + e[2]
end

function EILearn.totalOf(st, ctx)
  local t = 0
  local a = st.anim[ctx] or {}
  for _, e in pairs(a) do t = t + e[1] + e[2] end
  local c = st.cls[ctx] or {}
  for _, n in pairs(c) do t = t + n end
  return t
end

-- Sıralama: skor ↓ · toplam gözlem ↓ · id ↑  (son ölçüt kararlılık için ŞART:
-- Lua'nın table.sort'u kararlı DEĞİLDİR.)
function EILearn.rankAnim(st, ctx, candidates)
  local list = {}
  for i = 1, #candidates do list[i] = candidates[i] end
  table.sort(list, function(a, b)
    local sa = EILearn.scoreAnim(st, ctx, a)
    local sb = EILearn.scoreAnim(st, ctx, b)
    if sa ~= sb then return sa > sb end
    local ta = EILearn.obsOf(st, ctx, a)
    local tb = EILearn.obsOf(st, ctx, b)
    if ta ~= tb then return ta > tb end
    local ia, ib = sanitize(a), sanitize(b)
    return ia < ib
  end)
  return list
end

function EILearn.topAnims(st, ctx, k)
  local m = st.anim[ctx] or {}
  local ids = {}
  for id in pairs(m) do ids[#ids + 1] = id end
  table.sort(ids, function(a, b)
    local ca = m[a][1] - m[a][2]
    local cb = m[b][1] - m[b][2]
    if ca ~= cb then return ca > cb end
    local oa = m[a][1] + m[a][2]
    local ob = m[b][1] + m[b][2]
    if oa ~= ob then return oa > ob end
    return a < b
  end)
  local out = {}
  local n = k == nil and 5 or k
  for i = 1, math.min(n, #ids) do out[i] = ids[i] end
  return out
end

function EILearn.preferredClass(st, ctx)
  local m = st.cls[ctx] or {}
  local best, bn = nil, 0
  for k, v in pairs(m) do
    if v > bn or (v == bn and best ~= nil and k < best) then
      best, bn = k, v
    end
  end
  if best == nil then return nil end
  return { cls = best, n = bn }
end

function EILearn.prune(st, maxCtx)
  local cap = maxCtx == nil and DEFAULT_CAP or maxCtx
  local seen, keys = {}, {}
  local function add(k)
    if not seen[k] then seen[k] = true; keys[#keys + 1] = k end
  end
  for k in pairs(st.anim) do add(k) end
  for k in pairs(st.cls) do add(k) end
  if #keys <= cap then return st end
  table.sort(keys, function(a, b)
    local ta, tb = EILearn.totalOf(st, a), EILearn.totalOf(st, b)
    if ta ~= tb then return ta < tb end
    return a < b
  end)
  for i = 1, #keys - cap do
    st.anim[keys[i]] = nil
    st.cls[keys[i]] = nil
  end
  return st
end

function EILearn.countContexts(st)
  local seen, n = {}, 0
  for k in pairs(st.anim) do if not seen[k] then seen[k] = true; n = n + 1 end end
  for k in pairs(st.cls) do if not seen[k] then seen[k] = true; n = n + 1 end end
  return n
end

function EILearn.encode(st)
  local lines = { "ei-learn v" .. VERSION, "events " .. st.events, "exports " .. st.exports }
  local animRows, clsRows = {}, {}
  for ctx, m in pairs(st.anim) do
    for id, e in pairs(m) do
      animRows[#animRows + 1] = "anim " .. ctx .. " " .. id .. " " .. e[1] .. " " .. e[2]
    end
  end
  table.sort(animRows)
  for ctx, m in pairs(st.cls) do
    for cn, n in pairs(m) do
      clsRows[#clsRows + 1] = "cls " .. ctx .. " " .. cn .. " " .. n
    end
  end
  table.sort(clsRows)
  for i = 1, #animRows do lines[#lines + 1] = animRows[i] end
  for i = 1, #clsRows do lines[#lines + 1] = clsRows[i] end
  return table.concat(lines, "\n")
end

function EILearn.decode(text)
  local st = EILearn.newState()
  local t = tostring(text == nil and "" or text)
  for line in string.gmatch(t .. "\n", "([^\n]*)\n") do
    local parts = {}
    for w in string.gmatch(line, "[^ ]+") do parts[#parts + 1] = w end
    if parts[1] == "events" then
      st.events = toInt(parts[2])
    elseif parts[1] == "exports" then
      st.exports = toInt(parts[2])
    elseif parts[1] == "anim" and #parts >= 5 then
      ensureAnim(st, sanitize(parts[2]))[sanitize(parts[3])] = { toInt(parts[4]), toInt(parts[5]) }
    elseif parts[1] == "cls" and #parts >= 4 then
      ensureCls(st, sanitize(parts[2]))[sanitize(parts[3])] = toInt(parts[4])
    end
  end
  return st
end

function EILearn.byteLen(s)
  local n = 0
  local t = tostring(s or "")
  for i = 1, #t do
    local b = string.byte(t, i)
    if b < 128 then n = n + 1 elseif b < 2048 then n = n + 2 else n = n + 3 end
  end
  return n
end

function EILearn.fit(st, maxCtx, maxBytes)
  local cap = maxCtx == nil and DEFAULT_CAP or maxCtx
  local maxB = maxBytes == nil and DEFAULT_SIZE_CAP or maxBytes
  while EILearn.countContexts(st) > cap do EILearn.prune(st, cap) end
  local n = cap
  local guard = 0
  while EILearn.byteLen(EILearn.encode(st)) > maxB and n > 1 and guard < 64 do
    n = math.max(1, math.floor(n * 0.75))
    EILearn.prune(st, n)
    guard = guard + 1
  end
  return st
end

function EILearn.stats(st)
  local enc = EILearn.encode(st)
  local animRows, clsRows = 0, 0
  for line in string.gmatch(enc .. "\n", "([^\n]*)\n") do
    if string.sub(line, 1, 5) == "anim " then animRows = animRows + 1 end
    if string.sub(line, 1, 4) == "cls " then clsRows = clsRows + 1 end
  end
  return {
    version = VERSION,
    contexts = EILearn.countContexts(st),
    animRows = animRows,
    clsRows = clsRows,
    events = st.events,
    bytes = EILearn.byteLen(enc)
  }
end

EILearn.VERSION = VERSION
EILearn.DEFAULT_CAP = DEFAULT_CAP
EILearn.DEFAULT_SIZE_CAP = DEFAULT_SIZE_CAP
EILearn.sanitize = sanitize

return EILearn
