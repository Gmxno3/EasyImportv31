-- EasyImport Asistan — ÖZELLİK DEĞERLENDİRİCİ (Lua / Luau — Roblox Studio)  [A1]
--
-- spec/features.json (build_runtime.py tarafından EIFeatures_Spec.lua olarak üretilir)
-- dosyasını okur ve bir RAW tablosunu sabit uzunlukta özellik vektörüne çevirir.
--
-- Python ve JS sürümleriyle BİREBİR aynı sonucu vermek ZORUNDADIR.
-- tools/verify_runtime.py bunu fengari (gerçek Lua 5.3) ile zorunlu tutar.
--
-- Roblox'ta:
--   local Spec = require(script.Parent.EIFeatures_Spec)
--   local EIFeatures = require(script.Parent.EIFeatures)
--   local vec = EIFeatures.compute(Spec, raw)
--
-- Saf Lua 5.1/Lua 5.3 uyumlu; hiçbir Roblox API'si kullanmaz (test edilebilirlik için).

local EIFeatures = {}

local EPS  = 1e-6
local LN10 = math.log(10)

local function log10(x)
  return math.log(x) / LN10
end

local function asnum(v)
  if v == nil then return 0.0 end
  if v == true then return 1.0 end
  if v == false then return 0.0 end
  if type(v) == "number" then
    if v ~= v then return 0.0 end          -- NaN
    if v == math.huge then return 1e12 end
    if v == -math.huge then return -1e12 end
    return v
  end
  return 0.0
end

local function clamp(x, lo, hi)
  if x < lo then return lo end
  if x > hi then return hi end
  return x
end

local function divisor(raw, f)
  local d = f.d
  if d == nil then return 1.0 end
  local dv
  if type(d) == "string" then dv = asnum(raw[d]) else dv = asnum(d) end
  if dv == 0.0 then return 1.0 end
  return dv
end

local function num(raw, f)
  local x = asnum(raw[f.src])
  local norm = f.norm or "id"

  if norm == "id" then return x end
  if norm == "clamp01" then return clamp(x, 0.0, 1.0) end
  if norm == "log1p" then
    local xx = x
    if xx < 0.0 then xx = 0.0 end
    return log10(1.0 + xx)
  end
  if norm == "log" then
    local lo = f.lo
    if lo == nil then lo = -6.0 end
    local hi = f.hi
    if hi == nil then hi = 6.0 end
    local xx = x
    if xx < EPS then xx = EPS end
    return clamp(log10(xx), lo, hi)
  end

  local dv = divisor(raw, f)
  local adv = dv
  if adv < 0 then adv = -adv end
  if adv == 0.0 then adv = 1.0 end

  if norm == "div" then return x / adv end
  if norm == "divlog" then
    local lo = f.lo
    if lo == nil then lo = -6.0 end
    local hi = f.hi
    if hi == nil then hi = 6.0 end
    local xx = x
    if xx < EPS then xx = EPS end
    return clamp(log10(xx / adv), lo, hi)
  end
  return x
end

function EIFeatures.compute(spec, raw)
  local out = {}
  local n = 0
  local feats = spec.features
  for i = 1, #feats do
    local f = feats[i]
    local k = f.k
    if k == "num" then
      n = n + 1; out[n] = num(raw, f)
    elseif k == "bool" then
      n = n + 1
      if raw[f.src] then out[n] = 1.0 else out[n] = 0.0 end
    elseif k == "token" then
      n = n + 1
      local toks = raw[f.src]
      if toks and toks[f.t] then out[n] = 1.0 else out[n] = 0.0 end
    elseif k == "onehot" then
      local v = raw[f.src]
      local vals = f.values
      for j = 1, #vals do
        n = n + 1
        if v == vals[j] then out[n] = 1.0 else out[n] = 0.0 end
      end
    elseif k == "bucket" then
      local x = asnum(raw[f.src])
      local edges = f.edges
      local cnt = #edges
      local idx = cnt
      for e = 1, cnt do
        if x <= edges[e] then idx = e - 1; break end
      end
      for b = 0, cnt do
        n = n + 1
        if b == idx then out[n] = 1.0 else out[n] = 0.0 end
      end
    else
      error("bilinmeyen tur: " .. tostring(k))
    end
  end
  return out
end

EIFeatures.asnum = asnum
EIFeatures.log10 = log10
EIFeatures.clamp = clamp

return EIFeatures
