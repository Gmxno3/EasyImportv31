-- EasyImport Asistan — RAW ÇIKARICI (Lua / Luau — Roblox Studio)  [A2]
--
-- Girdi : plugin'in ürettiği `wispfree v9` dökümanı (format/version/name/
--         width/height/root) — Studio'ya gelen JSON'un çözülmüş tablosu.
-- Çıktı : her düğüm için bir RAW kaydı + GUI düzeyi özet.
--
-- JS (ei-raw.js) ve Python (ei_raw.py) sürümleriyle BİREBİR aynı sonucu
-- vermek ZORUNDADIR; tools/verify_extract.py bunu zorunlu tutar.
--
-- Roblox'ta:
--   local EIRaw = require(script.Parent.EIRaw)
--   local out   = EIRaw.extract(doc)          -- { nodes = {...}, gui = {...} }
--   local vec   = EIFeatures.compute(Spec, out.nodes[i])
--
-- Saf Lua 5.1 / Luau uyumlu; hiçbir Roblox API'si kullanmaz.

local EIRaw = {}

local EPS = 1e-9

-- ---------------------------------------------------------------------------
-- 1) SÖZLÜKLER — build_features.py ile AYNI SIRADA (indeks = ağırlık indeksi)
-- ---------------------------------------------------------------------------
local NAME_TOKENS = {
  "button","btn","buton","icon","close","exit","play","start","settings",
  "option","menu","back","next","prev","tab","nav","footer","header",
  "panel","bg","background","overlay","modal","popup","dialog","card",
  "slot","item","inventory","bag","shop","list","grid","scroll","content",
  "container","wrapper","divider","frame","label","text","title","desc",
  "value","count","timer","tooltip","badge","avatar","profile",
  "bar","hp","health","mana","energy","xp","level","coin","gem","gold",
  "progress","fill","loader","slider","toggle","check","reward","currency",
  "glow","ray","rays","shine","shining","sparkle","sparkles","star","stars",
  "twinkle","particle","flare","bloom","vignette","noise","grain","dust",
  "smoke","fog","ring","pulse","aura","beam","streak","gloss","shimmer",
  "glint","blur","halo","neon","emission","energy2","magic","fx","effect",
  "stud","studs","brick","civi","civili","texture","pattern",
  "isik","parlama","parilti","huzme","toz","duman","halka","efekt",
}

-- Sıralıdır — ilk eşleşme kazanır. pairs() sırası garantili olmadığı için
-- sözlük DEĞİL dizi kullanıyoruz (üç dilde aynı sonuç şart).
local FX_TOKENS_ORDERED = {
  {"glow","glow"}, {"bloom","glow"}, {"halo","glow"}, {"neon","glow"},
  {"emission","glow"}, {"isik","glow"}, {"parlama","glow"}, {"efekt","glow"},
  {"fx","glow"}, {"effect","glow"},
  {"ray","rays"}, {"rays","rays"},
  {"huzme","beam"}, {"beam","beam"}, {"streak","beam"},
  {"shine","shine"}, {"shining","shine"}, {"shimmer","shine"}, {"parilti","shine"},
  {"sparkle","sparkle"}, {"sparkles","sparkle"}, {"twinkle","sparkle"},
  {"particle","sparkle"},
  {"star","star"}, {"stars","star"},
  {"flare","flare"},
  {"vignette","vignette"},
  {"noise","noise"}, {"grain","noise"},
  {"dust","dust"}, {"toz","dust"},
  {"smoke","smoke"}, {"fog","smoke"}, {"duman","smoke"},
  {"ring","ring"}, {"pulse","ring"}, {"halka","ring"},
  {"aura","aura"}, {"magic","aura"},
  {"gloss","gloss"}, {"glint","gloss"},
  {"blur","blur"},
}

-- Stud / doku tokenları (kullanıcı: "stud kullanılmışsa Stud'a girer")
local STUD_TOKENS = {
  stud = true, studs = true, brick = true, civi = true,
  civili = true, texture = true, pattern = true,
}

local FX_TOKEN_KIND = {}
for _i = 1, #FX_TOKENS_ORDERED do
  FX_TOKEN_KIND[FX_TOKENS_ORDERED[_i][1]] = FX_TOKENS_ORDERED[_i][2]
end

-- ---------------------------------------------------------------------------
-- 2) SAYI YARDIMCILARI
-- ---------------------------------------------------------------------------
local function amax(a, b) if a > b then return a end return b end
local function amin(a, b) if a < b then return a end return b end
local function clamp01(x) if x < 0 then return 0 end if x > 1 then return 1 end return x end
local function round(x) return math.floor(x + 0.5) end

local function isNum(x) return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge end
local function num(x, dflt)
  if isNum(x) then return x end
  if dflt ~= nil then return dflt end
  return 0
end

-- ---------------------------------------------------------------------------
-- 3) METİN YARDIMCILARI — yerel ayardan bağımsız (JS/Python ile BİREBİR)
-- ---------------------------------------------------------------------------
-- Türkçe harflerin UTF-8 bayt çiftleri
local TR_LOWER = {            -- küçük harfin 2. baytı -> 1. bayt
  [0xA7] = 0xC3,              -- ç
  [0x9F] = 0xC4,              -- ğ
  [0xB1] = 0xC4,              -- ı
  [0xB6] = 0xC3,              -- ö
  [0x9F] = 0xC5,              -- ş  (C5 9F)
  [0xBC] = 0xC3,              -- ü
}
-- Not: yukarıdaki tablo yalnızca belge amaçlıdır; gerçek mantık aşağıda
-- bayt bayt yazılmıştır (çakışan anahtar olmasın diye).

local function byteAt(s, i)
  if i > #s then return nil end
  return string.byte(s, i)
end

-- [a-z0-9A-ZçğıöşüÇĞİÖŞÜ] -> kelime karakteri mi?
local function isWordCharByte(b1, b2)
  if b1 >= 48 and b1 <= 57 then return true, 1 end            -- 0-9
  if b1 >= 97 and b1 <= 122 then return true, 1 end           -- a-z
  if b1 >= 65 and b1 <= 90 then return true, 1 end            -- A-Z
  if b2 then
    if b1 == 0xC3 then
      if b2 == 0xA7 or b2 == 0x87 or b2 == 0xB6 or b2 == 0x96
         or b2 == 0xBC or b2 == 0x9C then return true, 2 end  -- ç Ç ö Ö ü Ü
    elseif b1 == 0xC4 then
      if b2 == 0x9F or b2 == 0x9E or b2 == 0xB1 or b2 == 0xB0 then return true, 2 end -- ğ Ğ ı İ
    elseif b1 == 0xC5 then
      if b2 == 0x9F or b2 == 0x9E then return true, 2 end     -- ş Ş
    end
  end
  return false, 1
end

-- küçük/kelime karakteri mi (camelSplit'in ilk sınıfı: [a-z0-9çğıöşü])
local function isLowerWordByte(b1, b2)
  if b1 >= 48 and b1 <= 57 then return true, 1 end
  if b1 >= 97 and b1 <= 122 then return true, 1 end
  if b2 then
    if b1 == 0xC3 and (b2 == 0xA7 or b2 == 0xB6 or b2 == 0xBC) then return true, 2 end -- ç ö ü
    if b1 == 0xC4 and (b2 == 0x9F or b2 == 0xB1) then return true, 2 end               -- ğ ı
    if b1 == 0xC5 and b2 == 0x9F then return true, 2 end                               -- ş
  end
  return false, 1
end

-- camelSplit'in ikinci sınıfı: [A-ZÇĞÖŞÜ]
local function isUpperSplitByte(b1, b2)
  if b1 >= 65 and b1 <= 90 then return true, 1 end
  if b2 then
    if b1 == 0xC3 and (b2 == 0x87 or b2 == 0x96 or b2 == 0x9C) then return true, 2 end -- Ç Ö Ü
    if b1 == 0xC4 and b2 == 0x9E then return true, 2 end                               -- Ğ
    if b1 == 0xC5 and b2 == 0x9E then return true, 2 end                               -- Ş
  end
  return false, 1
end

-- UTF-8 BAYT uzunluğu (karakter sayısı DEĞİL).
-- Lua'da diziler bayt dizisidir, bu yüzden #s zaten bayt uzunluğudur.
-- JS'in String.length (UTF-16) ile ayrışmaması için üç dilde de bayt sayıyoruz.
local function utf8len(s)
  return #(s or "")
end

local function foldLower(s)
  local out = {}
  local i, n = 1, #s
  while i <= n do
    local b1 = string.byte(s, i)
    local b2 = byteAt(s, i + 1)
    if b1 >= 65 and b1 <= 90 then
      out[#out + 1] = string.char(b1 + 32); i = i + 1
    elseif b1 == 0xC3 and b2 then
      if b2 == 0x87 then out[#out + 1] = "\195\167"            -- Ç -> ç
      elseif b2 == 0xB6 then out[#out + 1] = "\195\182"        -- Ö -> ö
      elseif b2 == 0xBC then out[#out + 1] = "\195\188"        -- Ü -> ü
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    elseif b1 == 0xC4 and b2 then
      if b2 == 0x9E then out[#out + 1] = "\196\159"            -- Ğ -> ğ
      elseif b2 == 0xB0 then out[#out + 1] = "i"               -- İ -> i
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    elseif b1 == 0xC5 and b2 then
      if b2 == 0x9E then out[#out + 1] = "\197\159"            -- Ş -> ş
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    else
      out[#out + 1] = string.char(b1); i = i + 1
    end
  end
  return table.concat(out)
end

local function foldUpper(s)
  local out = {}
  local i, n = 1, #s
  while i <= n do
    local b1 = string.byte(s, i)
    local b2 = byteAt(s, i + 1)
    if b1 >= 97 and b1 <= 122 then
      out[#out + 1] = string.char(b1 - 32); i = i + 1
    elseif b1 == 0xC3 and b2 then
      if b2 == 0xA7 then out[#out + 1] = "\195\135"            -- ç -> Ç
      elseif b2 == 0xB6 then out[#out + 1] = "\195\150"        -- ö -> Ö
      elseif b2 == 0xBC then out[#out + 1] = "\195\156"        -- ü -> Ü
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    elseif b1 == 0xC4 and b2 then
      if b2 == 0x9F then out[#out + 1] = "\196\158"            -- ğ -> Ğ
      elseif b2 == 0xB1 then out[#out + 1] = "I"               -- ı -> I
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    elseif b1 == 0xC5 and b2 then
      if b2 == 0x9F then out[#out + 1] = "\197\158"            -- ş -> Ş
      else out[#out + 1] = s:sub(i, i + 1) end
      i = i + 2
    else
      out[#out + 1] = string.char(b1); i = i + 1
    end
  end
  return table.concat(out)
end

local function hasUpper(s)
  local i, n = 1, #s
  while i <= n do
    local b1 = string.byte(s, i)
    local b2 = byteAt(s, i + 1)
    if b1 >= 65 and b1 <= 90 then return true end
    if b1 == 0xC3 and b2 and (b2 == 0x87 or b2 == 0x96 or b2 == 0x9C) then return true end
    if b1 == 0xC4 and b2 and (b2 == 0x9E or b2 == 0xB0) then return true end
    if b1 == 0xC5 and b2 and b2 == 0x9E then return true end
    if b1 < 0x80 then i = i + 1
    elseif b1 >= 0xC0 then i = i + 2
    else i = i + 1 end
  end
  return false
end

-- karakterleri ayırıcıya göre böler (keepUpper=true ise A-Z ve ÇĞİÖŞÜ de
-- kelime karakteri sayılır — countWords bunu ister)
local function splitWords(s, keepUpper)
  local out = {}
  local cur = {}
  local i, n = 1, #s
  while i <= n do
    local b1 = string.byte(s, i)
    local b2 = byteAt(s, i + 1)
    local ok, len
    if keepUpper then ok, len = isWordCharByte(b1, b2)
    else ok, len = isLowerWordByte(b1, b2) end
    if ok then
      cur[#cur + 1] = s:sub(i, i + len - 1)
      i = i + len
    else
      if #cur > 0 then out[#out + 1] = table.concat(cur); cur = {} end
      i = i + 1
    end
  end
  if #cur > 0 then out[#out + 1] = table.concat(cur) end
  return out
end

-- camelCase ayırıcı: [a-z0-9çğıöşü] + [A-ZÇĞÖŞÜ] arasına boşluk koy
local function camelSplit(s)
  local out = {}
  local i, n = 1, #s
  while i <= n do
    local b1 = string.byte(s, i)
    local b2 = byteAt(s, i + 1)
    local lowOk, lowLen = isLowerWordByte(b1, b2)
    out[#out + 1] = s:sub(i, i + lowLen - 1)
    i = i + lowLen
    if lowOk then
      local c1 = byteAt(s, i)
      local c2 = byteAt(s, i + 1)
      if c1 then
        local upOk, upLen = isUpperSplitByte(c1, c2)
        if upOk then out[#out + 1] = " " end
      end
    end
  end
  return table.concat(out)
end

local function trimStr(s)
  s = s or ""
  local a = s:gsub("^[ \t\r\n]+", "")
  a = a:gsub("[ \t\r\n]+$", "")
  return a
end

local function tokenize(name)
  local out = {}
  local s0 = tostring(name or "")
  if s0 == "" then return out end
  s0 = s0:gsub("\196\176", "i")          -- İ -> i (yerelden bağımsız)
  s0 = camelSplit(s0)
  local s = foldLower(s0)
  local words = splitWords(s, false)
  for _m = 1, #words do
    local base = words[_m]:gsub("[0-9]+$", "")
    if base ~= "" then
      out[base] = true
      if #base > 3 then
        if base:sub(-1) == "s" then out[base:sub(1, -2)] = true end
        if base:sub(-2) == "es" then out[base:sub(1, -3)] = true end
        if base:sub(-3) == "ing" then out[base:sub(1, -4)] = true end
        if base:sub(-2) == "ed" then out[base:sub(1, -3)] = true end
      end
    end
  end
  return out
end

local function hasAny(tokens, list)
  for k, _v in pairs(list) do
    if tokens[k] then return k end
  end
  return nil
end

-- JS: trim -> alfanumerik olmayanları boşluğa çevir -> trim -> /\s+/ ile böl
local function countWords(name)
  local s = trimStr(tostring(name or ""))
  if s == "" then return 0 end
  local parts = splitWords(s, true)
  if #parts == 0 then return 1 end
  return #parts
end

-- ---------------------------------------------------------------------------
-- 4) RENK
-- ---------------------------------------------------------------------------
local function rgb2hsv(r, g, b)
  r = clamp01(num(r) / 255); g = clamp01(num(g) / 255); b = clamp01(num(b) / 255)
  local mx = amax(r, amax(g, b))
  local mn = amin(r, amin(g, b))
  local d = mx - mn
  local h = 0
  if d > EPS then
    if mx == r then
      h = ((g - b) / d) % 6
    elseif mx == g then
      h = (b - r) / d + 2
    else
      h = (r - g) / d + 4
    end
    h = h * 60
    if h < 0 then h = h + 360 end
  end
  local s = 0
  if mx > EPS then s = d / mx end
  return { h = h, s = s, v = mx }
end

local function hsv2rgb(h, s, v)
  local cc = v * s
  local x = cc * (1 - math.abs(((h / 60) % 2) - 1))
  local m = v - cc
  local r, g, b = 0, 0, 0
  if h < 60 then r = cc; g = x
  elseif h < 120 then r = x; g = cc
  elseif h < 180 then g = cc; b = x
  elseif h < 240 then g = x; b = cc
  elseif h < 300 then r = x; b = cc
  else r = cc; b = x end
  return { r = (r + m) * 255, g = (g + m) * 255, b = (b + m) * 255 }
end

local function lum(r, g, b)
  return (0.2126 * num(r) + 0.7152 * num(g) + 0.0722 * num(b)) / 255
end

local function paletteBucket(h, s, v)
  if s < 0.12 then
    if v < 0.16 then return "black" end
    if v > 0.92 then return "white" end
    return "gray"
  end
  if h < 15 then return "red" end
  if h < 45 then return "orange" end
  if h < 70 then return "yellow" end
  if h < 165 then return "green" end
  if h < 200 then return "cyan" end
  if h < 255 then return "blue" end
  if h < 290 then return "purple" end
  if h < 330 then return "pink" end
  if h < 20 then return "brown" end
  return "red"
end

local function quant(color)
  if not color then return "g:0" end
  local hsv = rgb2hsv(color.r, color.g, color.b)
  if hsv.s < 0.12 then return "g:" .. round(hsv.v * 7) end
  return "c:" .. round(hsv.h / 30) .. ":" .. round(hsv.s * 3) .. ":" .. round(hsv.v * 3)
end

local function coefVar(arr)
  if not arr or #arr < 2 then return 0 end
  local s = 0
  for _i = 1, #arr do s = s + arr[_i] end
  local m = s / #arr
  if math.abs(m) < EPS then return 0 end
  local v = 0
  for _i = 1, #arr do local d = arr[_i] - m; v = v + d * d end
  v = v / #arr
  return math.sqrt(v) / math.abs(m)
end

local function hueDist(h1, h2)
  local d = math.abs(h1 - h2) % 360
  if d > 180 then return 360 - d end
  return d
end

-- ---------------------------------------------------------------------------
-- 5) AĞAÇ
-- ---------------------------------------------------------------------------
local function itemW(it) return num(it and it.w, 0) end
local function itemH(it) return num(it and it.h, 0) end

local function flatten(root)
  local flat = {}
  local function rec(item, parent, depth, si, nSib)
    if not item then return end
    flat[#flat + 1] = {
      item = item, parent = parent, depth = depth, si = si, nSib = nSib
    }
    local kids = item.children or {}
    for _i = 1, #kids do
      rec(kids[_i], item, depth + 1, _i - 1, #kids)
    end
  end
  rec(root, nil, 0, 0, 1)
  for _i = 1, #flat do flat[_i].i = _i - 1 end
  return flat
end

-- ---------------------------------------------------------------------------
-- 6) BOYUT KÜMELERİ (grup C — tüm GUI'yi karşılaştır)
--
--    w/h, belgenin kısa kenarının %2'sine yuvarlanır. Kümeler (üye sayısı
--    AZALAN, sonra alan AZALAN) sıralanır; rank 0 = en sık kullanılan boyut.
-- ---------------------------------------------------------------------------
local function buildClusters(flat, docMin)
  local q = amax(1, docMin * 0.02)
  local map = {}
  local order = {}
  for _i = 1, #flat do
    local it = flat[_i].item
    local w, h = itemW(it), itemH(it)
    local key = round(w / q) .. ":" .. round(h / q)
    local c = map[key]
    if not c then
      c = { key = key, n = 0, w = 0, h = 0, area = 0, members = {} }
      map[key] = c
      order[#order + 1] = key
    end
    c.n = c.n + 1
    c.members[#c.members + 1] = _i - 1
    if w * h > c.area then c.area = w * h; c.w = w; c.h = h end
  end
  local clusters = {}
  for _o = 1, #order do clusters[#clusters + 1] = map[order[_o]] end
  table.sort(clusters, function(a, b)
    -- Lua'nın table.sort'u kararlı DEĞİLDİR: eşitlikte üçüncü bir anahtar
    -- (küme anahtarı) ile kırıyoruz, yoksa JS ile sıra ayrışır.
    if b.n ~= a.n then return b.n < a.n end
    if b.area ~= a.area then return b.area < a.area end
    return a.key < b.key
  end)
  for _ci = 1, #clusters do clusters[_ci].rank = _ci - 1 end
  return { byKey = map, list = clusters }
end

-- ---------------------------------------------------------------------------
-- 7) GÖRSEL DOSYA ADI
--    Plugin dedupe'u aynı görseli aynı adla verir; aynı adın birden fazla
--    düğümde geçmesi = DOKU (Stud tespitinin kalbi).
-- ---------------------------------------------------------------------------
local function imageFileOf(it)
  if not it then return nil end
  if type(it.image) == "string" and it.image ~= "" then return it.image end
  local fills = it.fills or {}
  for _i = 1, #fills do
    local f = fills[_i]
    if f and f.type == "IMAGE" then
      if type(f.file) == "string" and f.file ~= "" then return f.file end
      if type(f.imageHash) == "string" and f.imageHash ~= "" then return f.imageHash end
      return "@image:" .. (_i - 1)
    end
  end
  return nil
end

-- ---------------------------------------------------------------------------
-- 8) TEK DÜĞÜM
-- ---------------------------------------------------------------------------
local function nodeRaw(flat, k0, ctx)
  local rec = flat[k0 + 1]
  local it = rec.item
  local ei = it.ei or {}

  local w, h = itemW(it), itemH(it)
  local area = w * h
  local aspect = 20.0
  if h > EPS then aspect = w / h end
  local minDim, maxDim = amin(w, h), amax(w, h)
  local x, y = num(it.x, 0), num(it.y, 0)

  local parent = rec.parent
  local parentW, parentH
  if parent then parentW, parentH = itemW(parent), itemH(parent)
  else parentW, parentH = w, h end
  local parentArea = parentW * parentH
  if parentArea <= 0 then parentArea = 1 end

  local raw = {}

  -- ---- GRUP B: geometri ---------------------------------------------------
  raw.w = w; raw.h = h
  raw.area = area
  raw.areaRatio = area / ((ctx.docArea > 0) and ctx.docArea or 1)
  raw.aspect = aspect
  raw.minDim = minDim; raw.maxDim = maxDim
  raw.rot = num(it.rot, 0)
  raw.docW = ctx.docW; raw.docH = ctx.docH
  raw.docMin = ctx.docMin; raw.docMax = ctx.docMax

  local cx = (x + w / 2) / ((ctx.docW > 0) and ctx.docW or 1)
  local cy = (y + h / 2) / ((ctx.docH > 0) and ctx.docH or 1)
  raw.cx = clamp01(cx); raw.cy = clamp01(cy)
  local dx, dy = cx - 0.5, cy - 0.5
  raw.distCenter = clamp01(math.sqrt(dx * dx + dy * dy) / 0.7071067811865476)
  raw.edgeTop = clamp01(1 - y / ((ctx.docH > 0) and ctx.docH or 1))
  raw.edgeBottom = clamp01(1 - ((ctx.docH - (y + h)) / ((ctx.docH > 0) and ctx.docH or 1)))
  raw.edgeLeft = clamp01(1 - x / ((ctx.docW > 0) and ctx.docW or 1))
  raw.edgeRight = clamp01(1 - ((ctx.docW - (x + w)) / ((ctx.docW > 0) and ctx.docW or 1)))
  local col = "c"
  if cx < 0.3333333 then col = "l" elseif cx > 0.6666667 then col = "r" end
  local row = "m"
  if cy < 0.3333333 then row = "t" elseif cy > 0.6666667 then row = "b" end
  raw.cornerRegion = row .. col

  -- ---- GRUP C: bağlam -----------------------------------------------------
  local q = amax(1, ctx.docMin * 0.02)
  local ckey = round(w / q) .. ":" .. round(h / q)
  local clus = ctx.clusters.byKey[ckey]
  raw.clusterRank = clus and clus.rank or 0
  raw.clusterCount = clus and clus.n or 1
  raw.clusterSingleton = (clus ~= nil) and (clus.n == 1) or false
  raw.clusterW = clus and clus.w or w
  raw.clusterH = clus and clus.h or h
  raw.clusterAspect = aspect
  if clus and clus.h > EPS then raw.clusterAspect = clus.w / clus.h end
  raw.nSameSize = clus and clus.n or 1

  raw.parentW = parentW; raw.parentH = parentH; raw.parentArea = parentArea

  local kids = (parent and parent.__eiKids) or { k0 }
  local sumW, sumH = 0, 0
  for _s = 1, #kids do
    sumW = sumW + itemW(flat[kids[_s] + 1].item)
    sumH = sumH + itemH(flat[kids[_s] + 1].item)
  end
  local nk = (#kids > 0) and #kids or 1
  raw.sibMeanW = sumW / nk
  raw.sibMeanH = sumH / nk

  local areas = {}
  for _s = 1, #kids do
    local ki = flat[kids[_s] + 1].item
    areas[#areas + 1] = itemW(ki) * itemH(ki)
  end
  raw.sibSizeVar = clamp01(coefVar(areas))

  raw.maxW = ctx.maxW; raw.maxH = ctx.maxH; raw.maxDepth = ctx.maxDepth

  local ar = ctx.areaRankOf[k0] or 0
  raw.sizeRank = 0
  if ctx.n > 1 then raw.sizeRank = ar / (ctx.n - 1) end
  raw.sizePercentile = 1
  if ctx.n > 1 then raw.sizePercentile = ar / ctx.n end

  local tol = amax(2, ctx.docMin * 0.01)
  local alX, alY = false, false
  for _s = 1, #kids do
    if kids[_s] ~= k0 then
      local oj = flat[kids[_s] + 1].item
      if math.abs((num(oj.x, 0) + itemW(oj) / 2) - (x + w / 2)) <= tol then alX = true end
      if math.abs((num(oj.y, 0) + itemH(oj) / 2) - (y + h / 2)) <= tol then alY = true end
    end
  end
  raw.alignedX = alX; raw.alignedY = alY

  raw.depth = rec.depth
  raw.nSiblings = rec.nSib

  -- ---- GRUP A: ad ---------------------------------------------------------
  local nm = tostring(it.name or "")
  local toks = tokenize(nm)
  local tokOut = {}
  for _ti = 1, #NAME_TOKENS do
    if toks[NAME_TOKENS[_ti]] then tokOut[NAME_TOKENS[_ti]] = true end
  end
  raw.nameTokens = tokOut
  raw.name = nm
  raw.hasUnderscoreTag = (string.find(nm, "_", 1, true) ~= nil)
  raw.nameHasDigit = (string.find(nm, "%d") ~= nil)
  raw.isCamel = (string.find(nm, "[a-z0-9][A-Z]") ~= nil)
  raw.nameAllUpper = hasUpper(nm) and (foldUpper(nm) == nm)
  raw.nameLen = utf8len(nm)
  raw.nameEmpty = (trimStr(nm) == "")
  raw.nameWords = countWords(nm)

  -- ---- GRUP D: dolgu & renk ----------------------------------------------
  local fills = it.fills or {}
  local nFills, hasSolid, hasGradient, hasImageFill = 0, false, false, false
  local fillOpacity, fillAlpha = 0, 0
  local fillH, fillS, fillV = 0, 0, 0
  local gradStops, gradType, gradAngle = 0, "LINEAR", 0
  local distinct, nDistinct = {}, 0
  local solidFill = nil
  local gradSeen = false

  for _fi = 1, #fills do
    local f = fills[_fi]
    if f and f.visible ~= false then
      nFills = nFills + 1
      local op = num(f.opacity, 1)
      if op > fillOpacity then fillOpacity = op end
      if f.type == "SOLID" then
        hasSolid = true
        if not solidFill then solidFill = f end
        local hsv = rgb2hsv(f.color and f.color.r, f.color and f.color.g, f.color and f.color.b)
        fillH, fillS, fillV = hsv.h, hsv.s, hsv.v
        fillAlpha = amax(fillAlpha, op * num(f.color and f.color.a, 1))
        local dk = quant(f.color)
        if not distinct[dk] then distinct[dk] = true; nDistinct = nDistinct + 1 end
        raw.paletteBucket = paletteBucket(hsv.h, hsv.s, hsv.v)
      elseif f.type == "GRADIENT" or f.type == "GRADIENT_OTHER" then
        hasGradient = true
        gradSeen = true
        local stops = f.stops or {}
        if #stops > gradStops then
          gradStops = #stops
          gradAngle = num(f.angle, 0)
          if f.type == "GRADIENT" then gradType = "LINEAR" else gradType = "RADIAL" end
        end
        for _si = 1, #stops do
          local sc = stops[_si].color or {}
          local sh = rgb2hsv(sc.r, sc.g, sc.b)
          if sh.v > fillV * 0.999 or fillV == 0 then
            fillH, fillS, fillV = sh.h, sh.s, sh.v
          end
          local dk2 = quant(sc)
          if not distinct[dk2] then distinct[dk2] = true; nDistinct = nDistinct + 1 end
        end
        fillAlpha = amax(fillAlpha, op)
        if not raw.paletteBucket then raw.paletteBucket = paletteBucket(fillH, fillS, fillV) end
      elseif f.type == "IMAGE" then
        hasImageFill = true
        fillAlpha = amax(fillAlpha, op)
      end
    end
  end
  raw.nFills = nFills
  raw.hasSolid = hasSolid
  raw.hasGradient = hasGradient
  raw.hasImage = hasImageFill
  raw.isTransparentFill = (nFills == 0) or (fillAlpha < 0.02)
  raw.fillOpacity = clamp01((fillOpacity > 0) and fillOpacity or ((nFills > 0) and 1 or 0))
  raw.fillAlpha = clamp01(fillAlpha)
  raw.fillH = fillH; raw.fillS = fillS; raw.fillV = fillV
  raw.fillIsDark = fillV < 0.45
  raw.fillIsNeon = (fillS > 0.7) and (fillV > 0.7)
  raw.paletteBucket = raw.paletteBucket or "gray"
  raw.gradStops = gradStops
  raw.gradType = gradType
  raw.gradAngleBucket = (((gradAngle % 360) + 360) % 360) / 45
  raw.nDistinctColors = nDistinct
  raw.isMonochrome = true
  if gradSeen or nFills > 0 then
    for dki, _v in pairs(distinct) do
      if string.sub(dki, 1, 2) ~= "g:" then raw.isMonochrome = false end
    end
  end

  -- ---- GRUP E: kontur & köşe ---------------------------------------------
  local stroke = it.stroke
  local strokeW, strokeS, strokeV, strokeH, strokeOpacity = 0, 0, 0, 0, 0
  local hasStroke = false
  if stroke and num(stroke.weight, 0) > 0 then
    hasStroke = true
    strokeW = num(stroke.weight, 0)
    local shsv = rgb2hsv(stroke.color and stroke.color.r,
                         stroke.color and stroke.color.g,
                         stroke.color and stroke.color.b)
    strokeS, strokeV, strokeH = shsv.s, shsv.v, shsv.h
    strokeOpacity = clamp01(num(stroke.opacity, 1))
  elseif num(it.strokeWeight, 0) > 0 and (it.strokes ~= nil) and #it.strokes > 0 then
    hasStroke = true
    strokeW = num(it.strokeWeight, 0)
    local st0 = it.strokes[#it.strokes]
    local shsv2 = rgb2hsv(st0 and st0.color and st0.color.r,
                          st0 and st0.color and st0.color.g,
                          st0 and st0.color and st0.color.b)
    strokeS, strokeV, strokeH = shsv2.s, shsv2.v, shsv2.h
    strokeOpacity = clamp01(num(st0 and st0.opacity, 1))
  end
  raw.hasStroke = hasStroke
  raw.strokeW = strokeW
  raw.strokeAlign = it.strokeAlign or ((stroke ~= nil) and "INSIDE" or "CENTER")
  raw.strokeJoin = ei.join or "MITER"
  raw.hasDash = (ei.dash ~= nil) and (#ei.dash > 0) or false
  raw.strokePerSideDiff = (ei.strokePerSide == true)
  raw.strokeS = strokeS; raw.strokeV = strokeV; raw.strokeH = strokeH
  raw.strokeOpacity = strokeOpacity
  raw.strokeDarkerThanFill = hasStroke and (strokeV < fillV - 0.02) or false
  local fr = hsv2rgb(fillH, fillS, fillV)
  if solidFill and solidFill.color then fr = solidFill.color end
  local sr = { r = 0, g = 0, b = 0 }
  if stroke and stroke.color then sr = stroke.color end
  raw.contrastFS = clamp01(math.abs(lum(fr.r, fr.g, fr.b) - lum(sr.r, sr.g, sr.b)))

  local r = 0
  local radiusIsFull = false
  if it.radius == "full" then r = minDim / 2; radiusIsFull = true
  else r = num(it.radius, 0) end
  raw.r = r
  raw.rPerSideDiff = (ei.rPerSide == true)
  raw.isFullRadius = radiusIsFull or ((minDim > 0) and (r >= minDim / 2 - 0.01)) or false
  raw.isPill = (raw.isFullRadius and (minDim > 0) and ((maxDim / minDim) > 1.6)) or false
  raw.isCircle = (raw.isFullRadius and (math.abs(aspect - 1) < 0.05)) or false
  raw.strokeAndRadius = (hasStroke and (r > 0)) or false
  raw.borderRatio = 0
  if minDim > 0 then raw.borderRatio = clamp01(2 * strokeW / minDim) end

  -- ---- GRUP F: metin ------------------------------------------------------
  local tx = nil
  if it.kind == "text" and it.text then tx = it.text end
  raw.isText = (tx ~= nil)
  if tx then
    local chars = tostring(tx.characters or "")
    raw.textLen = utf8len(chars)
    local tr = trimStr(chars)
    if tr == "" then
      raw.textWords = 0
    else
      local cnt = 1
      for _m in tr:gmatch("%S+") do cnt = cnt + 0 end  -- sayacı aşağıda sayıyoruz
      local n2 = 0
      for _m in tr:gmatch("%S+") do n2 = n2 + 1 end
      raw.textWords = n2
    end
    raw.textHasDigit = (string.find(chars, "%d") ~= nil)
    raw.textIsNumeric = (string.find(chars, "^[0-9 \t\r\n.,:%%+/-]+$") ~= nil) and (tr ~= "")
    raw.textAllUpper = hasUpper(chars) and (foldUpper(chars) == chars) and (#tr > 1)
    raw.fontSize = num(tx.fontSize, 16)
    raw.fontWeight = num(tx.fontWeight, 400)
    raw.italic = (tx.italic == true)
    raw.alignH = tx.align or "LEFT"
    raw.alignV = tx.vAlign or "TOP"
    raw.wrap = (tx.wrap == true)
    raw.nLines = num(tx.lines, 1)
    local thsv = rgb2hsv(tx.color and tx.color.r, tx.color and tx.color.g, tx.color and tx.color.b)
    raw.textV = thsv.v; raw.textS = thsv.s; raw.textH = thsv.h
    raw.textDensity = 0
    if area > 0 then raw.textDensity = clamp01(utf8len(chars) / (area / 1000)) end
  else
    raw.textLen = 0; raw.textWords = 0
    raw.textHasDigit = false; raw.textIsNumeric = false; raw.textAllUpper = false
    raw.fontSize = 0; raw.fontWeight = 0; raw.italic = false
    raw.alignH = "LEFT"; raw.alignV = "TOP"; raw.wrap = false; raw.nLines = 0
    raw.textV = 0; raw.textS = 0; raw.textH = 0; raw.textDensity = 0
  end

  -- ---- GRUP G: ağaç & düzen ----------------------------------------------
  local children = it.children or {}
  raw.nChildren = #children
  raw.hasChildren = (#children > 0)
  local nT, nI, nF = 0, 0, 0
  for _ci = 1, #children do
    local ch = children[_ci]
    if ch.kind == "text" then nT = nT + 1
    elseif ch.kind == "vector" or ch.image then nI = nI + 1
    else nF = nF + 1 end
  end
  raw.nTextChildren = nT; raw.nImageChildren = nI; raw.nFrameChildren = nF
  raw.isLeaf = not raw.hasChildren
  raw.isRoot = (rec.depth == 0)
  raw.siblingIndex = rec.si
  raw.isFirstChild = (rec.si == 0)
  raw.isLastChild = (rec.si == rec.nSib - 1)
  raw.clips = (it.clips == true)
  raw.hasScroll = (it.scroll ~= nil)
  local lay = it.layout
  raw.layoutMode = (lay and lay.mode) or "NONE"
  raw.gap = lay and num(lay.gap, 0) or 0
  raw.padAvg = 0
  if lay then
    raw.padAvg = (num(lay.pl, 0) + num(lay.pr, 0) + num(lay.pt, 0) + num(lay.pb, 0)) / 4
  end
  local cAreas = {}
  for _ci = 1, #children do
    cAreas[#cAreas + 1] = itemW(children[_ci]) * itemH(children[_ci])
  end
  raw.childSizeVar = clamp01(coefVar(cAreas))

  -- ---- GRUP H: efektler ---------------------------------------------------
  local shadows = it.shadows
  if (not shadows) and it.shadow then shadows = { it.shadow } end
  shadows = shadows or {}
  local nShadows, sx, sy, sblur, sspread, salpha, nGlow = 0, 0, 0, 0, 0, 0, 0
  for _si = 1, #shadows do
    local sh = shadows[_si]
    if sh then
      nShadows = nShadows + 1
      sx = sx + num(sh.x, 0); sy = sy + num(sh.y, 0)
      sblur = sblur + num(sh.blur, 0); sspread = sspread + num(sh.spread, 0)
      salpha = amax(salpha, clamp01(num(sh.opacity, 1)))
      if math.abs(num(sh.x, 0)) < 1 and math.abs(num(sh.y, 0)) < 1
         and num(sh.blur, 0) >= 8 and clamp01(num(sh.opacity, 1)) >= 0.3 then
        nGlow = nGlow + 1
      end
    end
  end
  raw.nShadows = nShadows
  raw.shadowOffsetX = sx; raw.shadowOffsetY = sy
  raw.shadowBlur = sblur; raw.shadowSpread = sspread
  raw.shadowAlpha = salpha
  raw.shadowIsMulti = (nShadows > 1)
  raw.hasInnerShadow = (ei.innerShadow == true)
  raw.hasLayerBlur = (ei.layerBlur ~= nil) and (num(ei.layerBlur, 0) > 0) or false
  raw.hasBgBlur = (ei.bgBlur ~= nil) and (num(ei.bgBlur, 0) > 0) or false
  raw.blurRadius = amax(num(ei.layerBlur, 0), num(ei.bgBlur, 0))
  raw.hasGlowPattern = (nGlow > 0)
  raw.nGlow = nGlow
  raw.hasAnyEffect = (nShadows > 0) or raw.hasInnerShadow or raw.hasLayerBlur or raw.hasBgBlur
  raw.opacity = clamp01(num(it.opacity, 1))

  -- ---- GRUP I: FX & doku --------------------------------------------------
  local imgFile = imageFileOf(it)
  local isVectorKind = (it.kind == "vector") or (it.image ~= nil)
  raw.hasImageFill = (imgFile ~= nil)
  raw.isVectorKind = isVectorKind
  raw.imageReuse = 0
  if imgFile then raw.imageReuse = ctx.imageCount[imgFile] or 1 end
  local tileW, tileH = num(ei.tileW, 0), num(ei.tileH, 0)
  local isTile = false
  for _fi = 1, #fills do
    if fills[_fi] and fills[_fi].type == "IMAGE" and fills[_fi].scaleMode == "TILE" then
      isTile = true
    end
  end
  if tileW > 0 and tileH > 0 then isTile = true end
  raw.imageTile = isTile or ((tileW > 0 and tileW < 128) or (tileH > 0 and tileH < 128))

  -- ---- DÖŞEME GEOMETRİSİ (stud tespitinin isimden bağımsız kanıtı) ----
  -- Kaynak: item.ei (yan kanal) — Figma `ImagePaint.scaleMode/scalingFactor` +
  -- `Image.getSizeAsync()`. Hücre px = görsel px × scalingFactor (TILE'da).
  local sfv = num(ei.sf, 0)
  if (tileW <= 0 or tileH <= 0) and sfv > 0 then
    local iaWf, iaHf = num(ei.imageW, 0), num(ei.imageH, 0)
    if iaWf > 0 and iaHf > 0 then tileW = iaWf * sfv; tileH = iaHf * sfv end
  end
  raw.tileCellW = (tileW > 0 and tileW < 4096) and tileW or 0
  raw.tileCellH = (tileH > 0 and tileH < 4096) and tileH or 0
  local cw, ch = raw.tileCellW, raw.tileCellH
  raw.tileCellSquare = (cw > 0 and ch > 0) and (math.abs(cw - ch) <= 1)
  raw.tileCellSmall = raw.tileCellSquare and cw >= 8 and cw <= 96
  raw.tileGridN = (raw.tileCellSmall and w > 0) and round(w / cw) or 0
  raw.tileGridNv = (raw.tileCellSmall and h > 0) and round(h / ch) or 0
  raw.studTileGeo = (raw.tileCellSmall and raw.imageTile and num(raw.imageReuse, 0) >= 2)
  local iaW, iaH = num(ei.imageW, 0), num(ei.imageH, 0)
  raw.imageAspectMatch = false
  if iaW > 0 and iaH > 0 and w > 0 and h > 0 then
    raw.imageAspectMatch = math.abs((iaW / iaH) - (w / h)) < 0.1
  end
  raw.imageLargerParent = false
  if parent then
    raw.imageLargerParent = (w > parentW * 1.05 + 0.5) or (h > parentH * 1.05 + 0.5)
  end
  raw.blendMode = ei.blendMode or "NONE"
  raw.hasStudToken = (hasAny(tokOut, STUD_TOKENS) ~= nil)

  -- shine frame: geniş, üstü örten, beyazımsı gradient, düşük opaklık
  local isShineFrame = false
  if it.kind ~= "text" and (not isVectorKind) and hasGradient then
    local allPale, minStopOpacity = true, 1
    for _fi = 1, #fills do
      local gf = fills[_fi]
      if gf and (gf.type == "GRADIENT" or gf.type == "GRADIENT_OTHER") then
        local sts = gf.stops or {}
        if #sts < 2 then allPale = false; break end
        for _si = 1, #sts do
          local cc = sts[_si].color or {}
          local hh = rgb2hsv(cc.r, cc.g, cc.b)
          if hh.s > 0.15 then allPale = false end
          minStopOpacity = amin(minStopOpacity, num(sts[_si].opacity, 1))
        end
      end
    end
    local coversParent
    if parent then coversParent = (area >= parentArea * 0.10)
    else coversParent = (area >= ctx.docArea * 0.10) end
    isShineFrame = allPale and coversParent and
      (num(it.opacity, 1) < 0.6 or minStopOpacity < 0.5 or fillAlpha < 0.5)
  end
  raw.isShineFrame = isShineFrame

  local fxKind = nil
  for _fk = 1, #FX_TOKENS_ORDERED do
    if tokOut[FX_TOKENS_ORDERED[_fk][1]] then
      fxKind = FX_TOKENS_ORDERED[_fk][2]
      break
    end
  end
  local blendFx = (raw.blendMode ~= "NONE") and (raw.blendMode ~= "NORMAL")
  local isFx = false
  if fxKind then
    isFx = true
  elseif isShineFrame then
    isFx = true; fxKind = "shine"
  elseif imgFile and (blendFx or raw.imageLargerParent or raw.imageReuse == 1)
         and it.kind == "vector" then
    isFx = true; fxKind = "glow"
  elseif isVectorKind and (w >= parentW * 0.98) and (h >= parentH * 0.98)
         and raw.opacity < 0.95 then
    isFx = true; fxKind = "vignette"
  end
  raw.isFx = isFx
  raw.fxKind = fxKind or "glow"
  raw.fxKindSet = fxKind or false   -- nil olursa anahtar kaybolur (JS ile ayrışır)

  raw.textureLike = ((imgFile ~= nil) and
    (raw.imageReuse >= 2 or isTile or (tileW > 0 and tileW < 128)
     or tokOut.texture or tokOut.pattern)) and true or false

  -- ---- GRUP K: ebeveyn bağlamı -------------------------------------------
  raw.parentCls = "NONE"
  raw.parentIsRoot = (parent == nil)
  raw.parentDepth = 0
  if parent then raw.parentDepth = rec.depth - 1 end
  raw.parentHasScroll = (parent ~= nil) and (parent.scroll ~= nil) or false
  if parent then
    local pq = amax(1, ctx.docMin * 0.02)
    local pkey = round(itemW(parent) / pq) .. ":" .. round(itemH(parent) / pq)
    local pc = ctx.clusters.byKey[pkey]
    raw.parentClusterRank = pc and pc.rank or 0
  else
    raw.parentClusterRank = -1
  end

  raw.darkerUnderlay = false
  raw.__i = k0
  return raw
end

-- ---------------------------------------------------------------------------
-- 9) PASS 2 — 3D ALT KATMAN
--    Kullanıcı: "genellikle 3D yapmaya çalışırlar, aynı rengin kapalısını
--    altta geçirerek 3D görünüm verirler."
--
--    YOL 1 renk  : aynı hue (fark <= 12°), üstteki daha açık, alttaki daha koyu.
--    YOL 2 geometri: aynı kutu ama 1..%15 aşağı kaymış düz dolgulu katman.
-- ---------------------------------------------------------------------------
local function boxesCoincide(a, b)
  local aw, ah, bw, bh = itemW(a), itemH(a), itemW(b), itemH(b)
  if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0 then return false end
  if math.abs((aw / ah) - (bw / bh)) > 0.25 then return false end
  local sc = ((aw / bw) + (ah / bh)) / 2
  if sc < 0.8 or sc > 1.25 then return false end
  local acx, acy = num(a.x, 0) + aw / 2, num(a.y, 0) + ah / 2
  local bcx, bcy = num(b.x, 0) + bw / 2, num(b.y, 0) + bh / 2
  local ddx, ddy = acx - bcx, acy - bcy
  local d = math.sqrt(ddx * ddx + ddy * ddy)
  return d <= 0.25 * amax(aw, ah)
end

local function markDarkerUnderlays(flat, raws)
  local groups = {}
  for _i = 1, #flat do
    local it = flat[_i].item
    if it.__eiKids and #it.__eiKids > 1 then groups[#groups + 1] = it.__eiKids end
  end

  for _gi = 1, #groups do
    local grp = groups[_gi]
    for _a = 1, #grp do
      local ia, ra = grp[_a], raws[grp[_a] + 1]
      local ia2 = flat[ia + 1].item
      if (not ra.isText) and (ia2.kind ~= "vector") and (ia2.image == nil) and ra.hasSolid then
        for _b = 1, #grp do
          if _a ~= _b then
            local ib, rb = grp[_b], raws[grp[_b] + 1]
            local ib2 = flat[ib + 1].item
            if (not rb.isText) and boxesCoincide(ia2, ib2) then
              -- YOL 1 — renk
              if ra.hasSolid and rb.hasSolid and ra.fillS >= 0.05 and rb.fillS >= 0.05
                 and rb.fillV > ra.fillV + 0.05 and hueDist(ra.fillH, rb.fillH) <= 12 then
                ra.darkerUnderlay = true
                break
              end
              -- YOL 2 — geometri (stud yüzeyinin altındaki 3D gölge)
              local dy = num(ia2.y, 0) - num(ib2.y, 0)
              if dy > 0.5 and dy <= 0.15 * amax(itemH(ia2), 1) + 8 and ra.nChildren == 0
                 and (rb.hasImageFill or rb.isVectorKind or rb.hasGradient or rb.hasSolid) then
                ra.darkerUnderlay = true
                break
              end
            end
          end
        end
      end
    end
  end
  for _c = 1, #raws do raws[_c].isDarkerUnderlay = (raws[_c].darkerUnderlay == true) end
end

-- ---------------------------------------------------------------------------
-- 10) PASS 3 — GUI DÜZEYİ SİNYALLER (grup J)
-- ---------------------------------------------------------------------------
local function emptyGui()
  return {
    darknessIndex = 0, mutedBaseRate = 0, hueDiversity = 0, accentPopRate = 0,
    effectDensity = 0, gradientRate = 0, reuseRate = 0, imageDrivenRate = 0,
    darkerUnderlayRate = 0, shineFrameRate = 0,
    nNodes = 0, nImages = 0, nUniqueImages = 0, nEffects = 0, nGradients = 0,
    nSolid = 0, nDarkerUnderlay = 0, nShineFrame = 0,
    nStudTile = 0, studTileRate = 0, studCellW = 0, studCellUniform = false,
  }
end

local function guiSummary(flat, raws, imageCount)
  local g = emptyGui()
  local n = #raws
  g.nNodes = n
  if n == 0 then return g end

  local sumV, cntSolid, muted, accent = 0, 0, 0, 0
  local hues = {}
  local nGrad, nImg, nEff, nShine, nUnder = 0, 0, 0, 0, 0
  local nStudTile, cellMin, cellMax = 0, 0, 0
  local imgRefs, uniq = 0, 0
  for _k, _v in pairs(imageCount) do
    uniq = uniq + 1
    imgRefs = imgRefs + imageCount[_k]
  end

  for _i = 1, n do
    local r = raws[_i]
    if r.hasSolid then
      sumV = sumV + r.fillV; cntSolid = cntSolid + 1
      if r.fillS < 0.35 then muted = muted + 1 end
      if r.fillS > 0.6 and r.fillV > 0.6 then accent = accent + 1 end
      hues[r.paletteBucket] = true
    elseif r.hasGradient then
      hues[r.paletteBucket] = true
    end
    -- Kontur ve yazı renkleri de "birden fazla renkli"nin parçası.
    if r.hasStroke and r.strokeS >= 0.12 then
      hues[paletteBucket(r.strokeH, r.strokeS, r.strokeV)] = true
    end
    if r.isText and r.textS >= 0.12 then
      hues[paletteBucket(r.textH, r.textS, r.textV)] = true
    end
    if r.hasGradient then nGrad = nGrad + 1 end
    if r.hasImageFill then nImg = nImg + 1 end
    if r.hasAnyEffect then nEff = nEff + 1 end
    if r.isShineFrame then nShine = nShine + 1 end
    if r.isDarkerUnderlay then nUnder = nUnder + 1 end
    if r.studTileGeo then
      nStudTile = nStudTile + 1
      local cc = num(r.tileCellW, 0)
      if cc > 0 then
        if cellMin > 0 then cellMin = math.min(cellMin, cc) else cellMin = cc end
        cellMax = math.max(cellMax, cc)
      end
    end
  end

  local nHue = 0
  for _h, _v in pairs(hues) do nHue = nHue + 1 end

  g.nSolid = cntSolid
  g.darknessIndex = 0
  if cntSolid > 0 then g.darknessIndex = clamp01(1 - (sumV / cntSolid)) end
  g.mutedBaseRate = 0
  if cntSolid > 0 then g.mutedBaseRate = clamp01(muted / cntSolid) end
  g.accentPopRate = 0
  if cntSolid > 0 then g.accentPopRate = clamp01(accent / cntSolid) end
  g.hueDiversity = clamp01(nHue / 12)
  g.gradientRate = clamp01(nGrad / n)
  g.imageDrivenRate = clamp01(nImg / n)
  g.effectDensity = clamp01(nEff / n)
  g.reuseRate = 0
  if imgRefs > 0 then g.reuseRate = clamp01(1 - (uniq / imgRefs)) end
  g.darkerUnderlayRate = clamp01(nUnder / ((cntSolid > 0) and cntSolid or n))
  g.shineFrameRate = clamp01(nShine / n)
  g.nImages = imgRefs
  g.nUniqueImages = uniq
  g.nStudTile = nStudTile
  g.studTileRate = clamp01(nStudTile / n)
  g.studCellW = (nStudTile > 0) and cellMin or 0
  g.studCellUniform = (nStudTile > 0 and cellMin > 0 and (cellMax / cellMin) <= 1.25)
  g.nGradients = nGrad
  g.nEffects = nEff
  g.nDarkerUnderlay = nUnder
  g.nShineFrame = nShine
  return g
end

local function copyGui(raw, g)
  raw.darknessIndex = g.darknessIndex
  raw.mutedBaseRate = g.mutedBaseRate
  raw.hueDiversity = g.hueDiversity
  raw.accentPopRate = g.accentPopRate
  raw.effectDensity = g.effectDensity
  raw.gradientRate = g.gradientRate
  raw.reuseRate = g.reuseRate
  raw.imageDrivenRate = g.imageDrivenRate
  raw.darkerUnderlayRate = g.darkerUnderlayRate
  raw.shineFrameRate = g.shineFrameRate
  raw.styleStud = false; raw.styleAnime = false
  raw.styleCartoon = false; raw.styleBelirsiz = true
  raw.styleConf = 0
end

local function applyStyle(raw, st)
  raw.styleStud = (st.stud == true)
  raw.styleAnime = (st.anime == true)
  raw.styleCartoon = (st.cartoon == true)
  raw.styleBelirsiz = (st.belirsiz == true)
  raw.styleConf = clamp01(num(st.conf, 0))
end

-- ---------------------------------------------------------------------------
-- 11) ANA ÇIKARICI
-- ---------------------------------------------------------------------------
function EIRaw.extract(doc, opts)
  opts = opts or {}
  local root = doc and doc.root
  if not root then return { nodes = {}, gui = emptyGui(), meta = { docW = 0, docH = 0, n = 0 } } end

  local docW = num(doc.width, itemW(root))
  if docW <= 0 then docW = 1920 end
  local docH = num(doc.height, itemH(root))
  if docH <= 0 then docH = 1080 end
  local docMin, docMax = amin(docW, docH), amax(docW, docH)
  local docArea = docW * docH

  local flat = flatten(root)
  local n = #flat

  local maxW, maxH, maxDepth, maxArea = 0, 0, 0, 0
  local imageCount = {}
  for _i = 1, n do
    local it0 = flat[_i].item
    local w0, h0 = itemW(it0), itemH(it0)
    if w0 > maxW then maxW = w0 end
    if h0 > maxH then maxH = h0 end
    if flat[_i].depth > maxDepth then maxDepth = flat[_i].depth end
    if w0 * h0 > maxArea then maxArea = w0 * h0 end
    it0.__eiKids = {}
  end
  if maxW <= 0 then maxW = 1 end
  if maxH <= 0 then maxH = 1 end
  if maxDepth <= 0 then maxDepth = 1 end

  for _a = 1, n do
    local p = flat[_a].parent
    if p then p.__eiKids[#p.__eiKids + 1] = _a - 1 end
  end

  for _b = 1, n do
    local f = imageFileOf(flat[_b].item)
    if f then imageCount[f] = (imageCount[f] or 0) + 1 end
  end

  local clusters = buildClusters(flat, docMin)

  local byArea = {}
  for _c = 1, n do byArea[_c] = _c - 1 end
  table.sort(byArea, function(x, y)
    local ax = itemW(flat[x + 1].item) * itemH(flat[x + 1].item)
    local ay = itemW(flat[y + 1].item) * itemH(flat[y + 1].item)
    if ax ~= ay then return ax < ay end
    return x < y                                  -- eşitlikte deterministik
  end)
  local areaRankOf = {}
  for _c = 1, n do areaRankOf[byArea[_c]] = _c - 1 end

  local ctx = {
    docW = docW, docH = docH, docMin = docMin, docMax = docMax, docArea = docArea,
    maxW = maxW, maxH = maxH, maxDepth = maxDepth, maxArea = maxArea,
    clusters = clusters, areaRankOf = areaRankOf, imageCount = imageCount, n = n,
  }

  local raws = {}
  for _k = 1, n do raws[_k] = nodeRaw(flat, _k - 1, ctx) end

  markDarkerUnderlays(flat, raws)

  local gui = guiSummary(flat, raws, imageCount)
  for _g = 1, #raws do copyGui(raws[_g], gui) end

  local style = nil
  if type(opts.styleFn) == "function" then
    style = opts.styleFn(gui, flat, raws)
  end
  if style then
    for _s = 1, #raws do applyStyle(raws[_s], style) end
  end

  for _t = 1, n do flat[_t].item.__eiKids = nil end

  return { nodes = raws, gui = gui, style = style, meta = { docW = docW, docH = docH, n = n } }
end

-- ---------------------------------------------------------------------------
EIRaw.tokenize = tokenize
EIRaw.utf8len = utf8len
EIRaw.foldLower = foldLower
EIRaw.foldUpper = foldUpper
EIRaw.hasUpper = hasUpper
EIRaw.splitWords = splitWords
EIRaw.trimStr = trimStr
EIRaw.countWords = countWords
EIRaw.rgb2hsv = rgb2hsv
EIRaw.paletteBucket = paletteBucket
EIRaw.buildClusters = buildClusters
EIRaw.imageFileOf = imageFileOf
EIRaw.NAME_TOKENS = NAME_TOKENS
EIRaw.FX_TOKENS_ORDERED = FX_TOKENS_ORDERED
EIRaw.FX_TOKEN_KIND = FX_TOKEN_KIND
EIRaw.STUD_TOKENS = STUD_TOKENS
EIRaw.emptyGui = emptyGui

return EIRaw
