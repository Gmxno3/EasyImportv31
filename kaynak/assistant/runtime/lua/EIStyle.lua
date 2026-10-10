-- EasyImport — STİL TESPİTİ (A10) — Studio tarafı
--
-- `runtime/js/ei-style.js`'in BİREBİR karşılığı. Aynı sinyaller, aynı ağırlıklar, aynı eşikler,
-- aynı karar. `tools/verify_style.py` iki dilin çıktısını (stil + güven + metin + 379 boyutlu
-- vektör) karşılaştırır; fark varsa kapı geçmez.
--
-- Kullanıcı tanımı (ARASTIRMA Bölüm C1/C1b):
--   STUD    = tespit: (ad tokenı VEYA doku tekrarı VEYA döşeme) VE buton/header üzerinde → güven 1.0
--   ANIME   = en iyi ışıklandırma + yüksek detay + koyu taban + çok renk, doku orta
--   CARTOON = doku ağırlıklı, efekti az, detay düşük
--   BELİRSİZ= eşikler tutmadı VEYA skor farkı < 0.12
--
-- Saf Lua: Roblox API'si yok. Yalnızca +,-,*,/ ve tamsayı biçimlendirme (string.format('%d')).
-- NOT: Luau'da `tostring(100)` ile Lua 5.3'te `tostring(100.0)` FARKLI yazar; bu yüzden
-- metin üretiminde tostring DEĞİL, tamsayı biçimlendirme kullanılır.

local EIStyle = {}

local VERSION = "ei-style-1"

-- GÜÇLÜ ad kanıtı (ARASTIRMA C1c: topluluk adlandırması + Türkçe "civili/civi")
local STUD_TOKENS = { "stud", "studs", "studded", "studtexture", "studpattern", "studtile",
                      "studbg", "studsui", "studs3x3", "civi", "civili" }
-- ZAYIF ad kanıtı: tek başına yetmez (her dokulu tasarımda geçebilir)
local STUD_WEAK_TOKENS = { "brick", "tugla", "texture", "pattern", "desen" }
-- Rakip stil niteleyicileri: "AnimeTexture" ANIME'in dokusudur, stud'un degil.
local COMPETING_STYLE_TOKENS = { "anime", "cartoon", "kawaii", "chibi", "manga", "toon", "cizgi" }
local BUTTON_HEADER_TOKENS = { "button", "btn", "buton", "header", "top", "title", "nav", "bar", "tab" }
local LIGHT_BLEND = { SCREEN = 1, ADD = 1, LINEAR_DODGE = 1, COLOR_DODGE = 1, LIGHTEN = 1, OVERLAY = 1, SOFT_LIGHT = 1 }

local W = {
  glow = 0.30, gradient = 0.24, radial = 0.18, multiStop = 0.12, lightLayer = 0.10, darkness = 0.06,
  dNodes = 0.40, dDepth = 0.30, dEffect = 0.30,
  tImage = 0.40, tTile = 0.25, tTexture = 0.15, tVector = 0.10, tReuse = 0.10,
  aLight = 0.40, aDetail = 0.22, aDark = 0.18, aHue = 0.12, aMuted = 0.08,
  cTexture = 0.45, cEffect = 0.25, cGradient = 0.18, cDetail = 0.12,
  animeLightMin = 0.55, animeDetailMin = 0.55, animeDarkMin = 0.50,
  cartoonTextureMin = 0.40, cartoonEffectMax = 0.40, cartoonDetailMax = 0.35,
  studEffectMax = 0.25, studReuseMin = 0.50, studImageMin = 0.50,
  studUniqueTexMax = 2,
  studUniqueTexHardMax = 3,
  studEvidenceMin = 4,
  studNameScopeMin = 2,
  studEffectVeto = 0.60,
  studDetailVeto = 0.62,
  studTileRateMin = 0.15,
  studGeoSpreadMin = 3,          -- kac dugumde OLCULMUS kare doseme hucresi "yayilmis" sayilir
  studGridMin = 2, studGridMax = 8,
  marginMin = 0.12
}

-- NaN güvenliği: NaN karşılaştırmaları her zaman false döndüğü için ters mantık kullanılır.
local function clamp01(x) if not (x > 0) then return 0 end if x > 1 then return 1 end return x end
local function num(v, d) if type(v) == "number" and v == v then return v end return d end
local function maxi(a, b) if a > b then return a else return b end end
local function log10(x) return math.log(x > 0 and x or 1e-12) / math.log(10) end
local function iv(x) if not (x == x) or x == math.huge or x == -math.huge then return 0 end return math.floor(x + 0.5) end
-- JS: String(iv(x)) — ikisi de tam sayı metni (tostsering TUZAĞI: Lua 5.3 "32.0" yazar)
local function itos(v) return string.format("%d", v) end

local function hasTok(toks, list)
  if type(toks) ~= "table" then return false end
  for i = 1, #list do
    if toks[list[i]] == true then return true end
  end
  return false
end

-- ---------------------------------------------------------------------------
-- Sinyaller — hepsi 0..1
-- ---------------------------------------------------------------------------
-- Zayıf stud adı kanıtı: düğüm adlarında brick/texture/pattern/desen/tugla geçiyor mu?
local function hasTokAll(raws, list)
  for i = 1, #raws do
    if hasTok(raws[i].nameTokens, list) then return true end
  end
  return false
end

function EIStyle.signals(gui, raws)
  local n = #raws
  local s = {
    hasStud = false, lightingIndex = 0, detailIndex = 0, darknessIndex = 0, mutedBaseRate = 0,
    hueDiversity = 0, accentPopRate = 0, textureIndex = 0, effectDensity = 0, gradientRate = 0,
    reuseRate = 0, imageDrivenRate = 0, darkerUnderlayRate = 0, shineFrameRate = 0,
    glowRate = 0, tileRate = 0, textureEffectRate = 0, vectorDecorRate = 0,
    radialRate = 0, multiStopRate = 0, lightLayerRate = 0,
    maxDepth = 0, nNodes = 0
  }
  if n == 0 then return s end

  local nGlow, nTile, nTexEff, nVecDec, nGrad, nRadial, nMulti, nLight = 0, 0, 0, 0, 0, 0, 0, 0
  local maxDepth = 0
  local nameStud, repeatUse, tileCell, onButtonOrHeader = false, false, false, false
  local weakOnBH = false
  -- STUD v3 kanıt sayaçları (ARASTIRMA C1c)
  local nStudName, nStudTileGeo, nStudGeoBH, studGridOk = 0, 0, 0, false
  local studCellMin, studCellMax = 0, 0

  for i = 1, n do
    local r = raws[i]
    local toks = r.nameTokens
    local tokStud = hasTok(toks, STUD_TOKENS)
    local reuse = num(r.imageReuse, 0)
    local tile = (r.imageTile == true)
    local hasImg = (r.hasImageFill == true) or (reuse > 0)
    local onBH = hasTok(toks, BUTTON_HEADER_TOKENS)

    -- Zayif kanit: rakip stil niteleyicisi varsa (or. "AnimeTexture") stud sayilmaz.
    local tokWeak = hasTok(toks, STUD_WEAK_TOKENS) and not hasTok(toks, COMPETING_STYLE_TOKENS)
    if tokStud then nameStud = true; nStudName = nStudName + 1 end
    -- Dokunun BUTON/HEADER uzerinde olmasi ZORUNLU (kural yaziliydi, kod uygulamiyordu)
    if tokWeak and onBH and hasImg then weakOnBH = true end
    if reuse >= 2 then repeatUse = true end
    if tile then tileCell = true end
    if onBH and hasImg and (tokStud or reuse >= 2 or tile) then onButtonOrHeader = true end

    -- GEOMETRİ kanıtı: küçük KARE döşeme hücresi ölçülmüş (Figma scalingFactor × görsel px)
    local geo = (r.studTileGeo == true)
    if geo then
      nStudTileGeo = nStudTileGeo + 1
      local cc = num(r.tileCellW, 0)
      if cc > 0 then
        if studCellMin > 0 then studCellMin = (cc < studCellMin) and cc or studCellMin else studCellMin = cc end
        studCellMax = (cc > studCellMax) and cc or studCellMax
      end
      if onBH then nStudGeoBH = nStudGeoBH + 1 end
      local gn, gv = num(r.tileGridN, 0), num(r.tileGridNv, 0)
      if (gn >= W.studGridMin and gn <= W.studGridMax) or
         (gv >= W.studGridMin and gv <= W.studGridMax) then studGridOk = true end
    end

    if r.hasGlowPattern == true then nGlow = nGlow + 1 end
    if tile then nTile = nTile + 1 end
    if r.textureLike == true then nTexEff = nTexEff + 1 end
    if r.isVectorKind == true and r.isFx ~= true and r.isText ~= true then nVecDec = nVecDec + 1 end
    if r.hasGradient == true then
      nGrad = nGrad + 1
      if r.gradType == "RADIAL" then nRadial = nRadial + 1 end
      if num(r.gradStops, 0) >= 3 then nMulti = nMulti + 1 end
    end
    if r.blendMode and LIGHT_BLEND[r.blendMode] == 1 then nLight = nLight + 1 end
    local d = num(r.depth, 0)
    if d > maxDepth then maxDepth = d end
  end

  s.glowRate = nGlow / n
  s.tileRate = nTile / n
  s.textureEffectRate = nTexEff / n
  s.vectorDecorRate = nVecDec / n
  s.radialRate = nGrad > 0 and (nRadial / nGrad) or 0
  s.multiStopRate = nGrad > 0 and (nMulti / nGrad) or 0
  s.lightLayerRate = nLight / n

  s.darknessIndex = clamp01(num(gui.darknessIndex, 0))
  s.mutedBaseRate = clamp01(num(gui.mutedBaseRate, 0))
  s.hueDiversity = clamp01(num(gui.hueDiversity, 0))
  s.accentPopRate = clamp01(num(gui.accentPopRate, 0))
  s.effectDensity = clamp01(num(gui.effectDensity, 0))
  s.gradientRate = clamp01(num(gui.gradientRate, 0))
  s.reuseRate = clamp01(num(gui.reuseRate, 0))
  s.imageDrivenRate = clamp01(num(gui.imageDrivenRate, 0))
  s.darkerUnderlayRate = clamp01(num(gui.darkerUnderlayRate, 0))
  s.shineFrameRate = clamp01(num(gui.shineFrameRate, 0))
  s.maxDepth = maxDepth
  s.nNodes = n

  s.lightingIndex = clamp01(
    W.glow * s.glowRate + W.gradient * s.gradientRate + W.radial * s.radialRate +
    W.multiStop * s.multiStopRate + W.lightLayer * s.lightLayerRate + W.darkness * s.darknessIndex)

  local nrm = clamp01(log10(maxi(1, n)) / 3)
  local drm = clamp01(maxDepth / 8)
  s.detailIndex = clamp01(W.dNodes * nrm + W.dDepth * drm + W.dEffect * s.effectDensity)

  s.textureIndex = clamp01(
    W.tImage * s.imageDrivenRate + W.tTile * s.tileRate + W.tTexture * s.textureEffectRate +
    W.tVector * s.vectorDecorRate + W.tReuse * s.reuseRate)

  -- STUD TESPİTİ — kanıt gücü ayrımı (ayrıntılı gerekçe: ei-style.js aynı blok)
  s.fewTextures = (num(gui.nUniqueImages, 0) <= W.studUniqueTexMax) and (num(gui.nImages, 0) > 0)
  s.studTileRate = clamp01(nStudTileGeo / n)
  s.studCellUniform = (nStudTileGeo > 0 and studCellMin > 0 and (studCellMax / studCellMin) <= 1.25)
  s.studCellPx = (nStudTileGeo > 0) and studCellMin or 0
  s.nStudTileGeo = nStudTileGeo; s.nStudName = nStudName

  -- ------------------------------------------------------------------
  -- STUD TESPİTİ v3 — KANIT MERDİVENİ (ARASTIRMA C1c) — JS ile birebir
  -- ------------------------------------------------------------------
  local strongName = (nStudName >= W.studNameScopeMin) or (nStudName >= 1 and nStudTileGeo >= 1)
  local strongGeo = (nStudGeoBH >= 1)
  -- GUCLU geometri (yayilim): doku olculmus ve birden cok dugumde tekrar ediyor, baska doku YOK.
  local strongGeoSpread = (nStudTileGeo >= W.studGeoSpreadMin) and s.fewTextures
  local weak = hasTokAll(raws, STUD_WEAK_TOKENS)
  local ev = 0
  if strongName then ev = ev + 3 end
  if strongGeo then ev = ev + 3 end
  if weak then ev = ev + 1 end
  if studGridOk then ev = ev + 1 end
  if s.reuseRate >= W.studReuseMin then ev = ev + 1 end
  if s.fewTextures then ev = ev + 1 end
  if s.imageDrivenRate >= W.studImageMin then ev = ev + 1 end
  if s.studTileRate >= W.studTileRateMin then ev = ev + 1 end
  if s.studCellUniform then ev = ev + 1 end
  if s.shineFrameRate > 0 then ev = ev + 0.5 end
  if s.darkerUnderlayRate > 0 then ev = ev + 0.5 end
  if s.effectDensity <= W.studEffectMax then ev = ev + 0.5 end
  if s.detailIndex <= 0.55 then ev = ev + 0.5 end

  local veto = (num(gui.nUniqueImages, 0) > W.studUniqueTexHardMax) or
               (s.effectDensity > W.studEffectVeto) or (s.detailIndex > W.studDetailVeto)
  s.studEvidence = ev; s.studStrongName = strongName; s.studStrongGeo = strongGeo
  s.studWeakName = weak; s.studWeakOnBH = weakOnBH; s.studVeto = veto; s.studGeoSpread = strongGeoSpread
  -- `weak` TEK BASINA yetmez: buton/header kosulu ZORUNLU (kanit merdiveni belgesi).
  s.hasStud = strongName or
    (ev >= W.studEvidenceMin and (not veto) and
     (strongGeo or strongGeoSpread or weakOnBH or s.studTileRate >= W.studTileRateMin))
  s._studName = nameStud; s._studRepeat = repeatUse; s._studTile = tileCell; s._studOnBH = onButtonOrHeader
  return s
end

local function pct(x) return itos(iv(clamp01(x) * 100)) .. "%" end

-- Tamsayı aritmetiğiyle iki ondalık: JS `String()` ile birebir aynı metin.
local function f2(x)
  local v = iv(clamp01(x) * 100)
  local s = itos(v)
  while #s < 3 do s = "0" .. s end
  return string.sub(s, 1, #s - 2) .. "." .. string.sub(s, #s - 1)
end

-- ---------------------------------------------------------------------------
-- Karar
-- ---------------------------------------------------------------------------
function EIStyle.decide(s)
  local out = {
    version = VERSION,
    stud = false, anime = false, cartoon = false, belirsiz = true,
    style = "belirsiz", conf = 0,
    scores = { stud = 0, anime = 0, cartoon = 0 },
    signals = s, oneLiner = ""
  }
  if s.nNodes == 0 then
    out.oneLiner = "Boş GUI: stil belirsiz."
    return out
  end

  -- 1) STUD — tespit, override yok
  if s.hasStud then
    out.stud = true; out.belirsiz = false
    out.style = "stud"; out.conf = 1
    out.scores = { stud = 1, anime = 0, cartoon = 0 }
    out.oneLiner = "Stud: kanıt " .. itos(s.studEvidence * 2) .. "/20 · "
      .. (s.studStrongName and "ad" or (s.studStrongGeo and "döşeme geometrisi" or "doku"))
      .. (s.studStrongGeo and " + buton/header" or "")
      .. " · hücre " .. itos(s.studCellPx) .. "px"
      .. " · doku tekrarı " .. pct(s.reuseRate)
      .. " · efekt " .. f2(s.effectDensity)
    return out
  end

  local a = W.aLight * s.lightingIndex + W.aDetail * s.detailIndex + W.aDark * s.darknessIndex +
            W.aHue * s.hueDiversity + W.aMuted * s.mutedBaseRate
  local c = W.cTexture * s.textureIndex + W.cEffect * (1 - s.effectDensity) +
            W.cGradient * (1 - s.gradientRate) + W.cDetail * (1 - s.detailIndex)
  out.scores.anime = a; out.scores.cartoon = c
  local margin = a > c and (a - c) or (c - a)
  local sum = a + c

  local animeRule = (s.lightingIndex >= W.animeLightMin) and
                    (s.detailIndex >= W.animeDetailMin) and
                    (s.darknessIndex >= W.animeDarkMin)
  local cartoonRule = (s.textureIndex >= W.cartoonTextureMin) and
                      (s.effectDensity <= W.cartoonEffectMax) and
                      (s.detailIndex <= W.cartoonDetailMax)

  local eligible = nil
  if animeRule and cartoonRule then eligible = nil
  elseif animeRule then eligible = "anime"
  elseif cartoonRule then eligible = "cartoon" end

  if eligible and margin >= W.marginMin then
    out[eligible] = true; out.belirsiz = false
    out.style = eligible
    out.conf = sum > 0 and clamp01((eligible == "anime" and a or c) / sum) or 0.5
    out.oneLiner = (eligible == "anime" and "Anime" or "Cartoon") .. ": "
      .. "ışık " .. f2(s.lightingIndex) .. " · detay " .. f2(s.detailIndex) .. " · koyuluk " .. f2(s.darknessIndex)
      .. " · doku " .. f2(s.textureIndex) .. " · efekt " .. f2(s.effectDensity)
    return out
  end

  out.conf = eligible and clamp01(1 - (margin / W.marginMin)) or 0
  if eligible then
    out.oneLiner = "Belirsiz: " .. (eligible == "anime" and "anime" or "cartoon") .. " eşikleri tuttu ama fark küçük ("
      .. f2(margin) .. " < " .. f2(W.marginMin) .. ")."
  else
    out.oneLiner = "Belirsiz: hiçbir stil eşiği tutmadı (ışık " .. f2(s.lightingIndex) .. " · detay " .. f2(s.detailIndex)
      .. " · doku " .. f2(s.textureIndex) .. " · efekt " .. f2(s.effectDensity) .. ")."
  end
  return out
end

-- EIRaw kancası: (gui, flat, raws) → stil tablosu
function EIStyle.detect(gui, flat, raws)
  return EIStyle.decide(EIStyle.signals(gui, raws or {}))
end

EIStyle.VERSION = VERSION
EIStyle.WEIGHTS = W
EIStyle.STUD_TOKENS = STUD_TOKENS
EIStyle.BUTTON_HEADER_TOKENS = BUTTON_HEADER_TOKENS

return EIStyle
