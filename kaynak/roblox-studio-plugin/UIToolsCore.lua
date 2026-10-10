-- UIToolsCore — UI Tools eklentisinin saf (Roblox'a bağımlı olmayan) hesapları.
-- Burada Instance/Enum yok: her şey düz sayı ve tablo. Test edilebilir olması için böyle tutuldu.
-- Koordinatlar piksel cinsindendir; {x, y, w, h} = sol-üst köşe + boyut.

local Core = {}

Core.ALIGN_MODES = { "left", "hcenter", "right", "top", "vcenter", "bottom" }
local VALID_ALIGN = {}
for _, m in ipairs(Core.ALIGN_MODES) do VALID_ALIGN[m] = true end

local function set(list)
	local s = {}
	for _, v in ipairs(list) do s[v] = true end
	return s
end

-- Kutu: verilen dikdörtgenlerin birleşik sınırı.
function Core.boundingBox(rects)
	local minX, minY, maxX, maxY = math.huge, math.huge, -math.huge, -math.huge
	for _, r in ipairs(rects) do
		if r.x < minX then minX = r.x end
		if r.y < minY then minY = r.y end
		if r.x + r.w > maxX then maxX = r.x + r.w end
		if r.y + r.h > maxY then maxY = r.y + r.h end
	end
	return { x = minX, y = minY, w = maxX - minX, h = maxY - minY }
end

-- Hizalama. container nil ise seçimin sınırına hizalanır. Boyut değişmez.
-- Dönüş: her öğe için yeni sol-üst {x, y}.
function Core.align(rects, mode, container)
	if not VALID_ALIGN[mode] then
		return nil, "bilinmeyen hizalama: " .. tostring(mode)
	end
	local out = {}
	if #rects == 0 then return out end
	local c = container or Core.boundingBox(rects)
	for i, r in ipairs(rects) do
		local x, y = r.x, r.y
		if mode == "left" then x = c.x
		elseif mode == "hcenter" then x = c.x + (c.w - r.w) / 2
		elseif mode == "right" then x = c.x + c.w - r.w
		elseif mode == "top" then y = c.y
		elseif mode == "vcenter" then y = c.y + (c.h - r.h) / 2
		elseif mode == "bottom" then y = c.y + c.h - r.h
		end
		out[i] = { x = x, y = y }
	end
	return out
end

-- Dağıtma (v22): en az 3 öğe. Uç öğeler yerinde kalır; aradakiler eşit boşlukla yerleşir.
-- axis: "h" (yatay, x/w) | "v" (dikey, y/h). Dönüş: her öğe için {x, y} (girdi sırası korunur).
function Core.distribute(rects, axis)
	if axis ~= "h" and axis ~= "v" then return nil, "bilinmeyen eksen: " .. tostring(axis) end
	local n = #rects
	if n < 3 then return nil, "dağıtma için en az 3 öğe gerekir" end
	local pos = axis == "h" and "x" or "y"
	local size = axis == "h" and "w" or "h"
	local order = {}
	for i = 1, n do order[i] = i end
	table.sort(order, function(a, b)
		if rects[a][pos] ~= rects[b][pos] then return rects[a][pos] < rects[b][pos] end
		return a < b
	end)
	local first, last = rects[order[1]], rects[order[n]]
	-- boşluk = (uçtan uca açıklık - TÜM öğelerin boyutu toplamı) / boşluk sayısı
	local span = (last[pos] + last[size]) - first[pos]
	local total = 0
	for k = 1, n do total = total + rects[order[k]][size] end
	local gap = (span - total) / (n - 1)
	local out = {}
	for i, r in ipairs(rects) do out[i] = { x = r.x, y = r.y } end
	local cursor = first[pos] + first[size]
	for k = 2, n - 1 do
		local idx = order[k]
		local v = cursor + gap
		if axis == "h" then out[idx].x = v else out[idx].y = v end
		cursor = v + rects[idx][size]
	end
	return out
end

-- Izgaraya yuvarlama. step <= 0 ise değere dokunmaz.
function Core.roundToGrid(v, step)
	if not step or step <= 0 then return v end
	return math.floor(v / step + 0.5) * step
end

-- Ok tuşu taşıması. dx/dy piksel; step > 0 ise sonuç ızgaraya oturur.
function Core.shiftRects(rects, dx, dy, step)
	local out = {}
	for i, r in ipairs(rects) do
		out[i] = { x = Core.roundToGrid(r.x + dx, step), y = Core.roundToGrid(r.y + dy, step) }
	end
	return out
end

-- Piksel -> Scale. parentPx <= 0 ise nil (üst öğe boyutu bilinmiyorsa dönüşüm yapılamaz).
function Core.toScale(px, parentPx)
	if not parentPx or parentPx <= 0 then return nil end
	return px / parentPx
end

-- Scale -> piksel.
function Core.toPixels(scale, parentPx)
	return scale * parentPx
end

-- Sınıf yetenekleri: hangi özellikler hangi sınıfta var.
local BASE = { "Name", "Position", "Size", "AnchorPoint", "Rotation", "ZIndex", "LayoutOrder",
	"Visible", "BackgroundColor3", "BackgroundTransparency", "BorderSizePixel", "BorderColor3",
	"ClipsDescendants", "AutomaticSize" }
local TEXT = { "Text", "TextColor3", "TextSize", "Font", "TextXAlignment", "TextYAlignment",
	"TextScaled", "TextWrapped", "TextTransparency", "RichText" }
local IMAGE = { "Image", "ImageColor3", "ImageTransparency", "ScaleType", "ImageRectOffset", "ImageRectSize" }
local SCROLL = { "CanvasSize", "ScrollBarThickness", "ScrollingDirection", "ScrollBarImageColor3" }
local BTN = { "AutoButtonColor", "Active", "Selectable" }

local function join(...)
	local out = {}
	for _, list in ipairs({ ... }) do
		for _, v in ipairs(list) do out[#out + 1] = v end
	end
	return out
end

Core.CLASSES = {
	Frame = { props = join(BASE) },
	CanvasGroup = { props = join(BASE, { "GroupTransparency" }) },
	ScrollingFrame = { props = join(BASE, SCROLL) },
	ViewportFrame = { props = join(BASE, { "Ambient", "LightColor" }) },
	TextLabel = { props = join(BASE, TEXT) },
	TextButton = { props = join(BASE, TEXT, BTN) },
	TextBox = { props = join(BASE, TEXT, { "PlaceholderText", "PlaceholderColor3", "ClearTextOnFocus" }) },
	ImageLabel = { props = join(BASE, IMAGE) },
	ImageButton = { props = join(BASE, IMAGE, BTN) },
}

-- Sınıf sırası: arayüzde gösterilecek liste.
Core.CLASS_ORDER = { "Frame", "TextLabel", "TextButton", "TextBox", "ImageLabel", "ImageButton",
	"ScrollingFrame", "CanvasGroup", "ViewportFrame" }

-- Sınıf değiştirme planı.
-- copy:    hedefte de olan özellikler (kaynaktan kopyalanır)
-- dropped: yalnızca kaynakta olan özellikler (kaybolur)
-- gained:  yalnızca hedefte olan özellikler (varsayılan değer alır)
-- warnings: kullanıcıya gösterilecek kayıp uyarıları
function Core.classChangePlan(fromClass, toClass)
	local src, dst = Core.CLASSES[fromClass], Core.CLASSES[toClass]
	if not src then return nil, "desteklenmeyen kaynak sınıf: " .. tostring(fromClass) end
	if not dst then return nil, "desteklenmeyen hedef sınıf: " .. tostring(toClass) end
	if fromClass == toClass then return nil, "öğe zaten " .. toClass end
	local srcSet, dstSet = set(src.props), set(dst.props)
	local plan = { copy = {}, dropped = {}, gained = {}, warnings = {} }
	for _, p in ipairs(src.props) do
		if dstSet[p] then plan.copy[#plan.copy + 1] = p
		else plan.dropped[#plan.dropped + 1] = p end
	end
	for _, p in ipairs(dst.props) do
		if not srcSet[p] then plan.gained[#plan.gained + 1] = p end
	end
	local dropSet = set(plan.dropped)
	if dropSet.Text then plan.warnings[#plan.warnings + 1] = "metin silinecek" end
	if dropSet.Image then plan.warnings[#plan.warnings + 1] = "resim silinecek" end
	if dropSet.CanvasSize then plan.warnings[#plan.warnings + 1] = "kaydırma ayarları silinecek" end
	return plan
end

-- Kaydırıcı: 0..1 arasındaki konum (frac) -> [min, max] aralığında adımlı değer.
function Core.sliderToValue(frac, min, max, step)
	if frac < 0 then frac = 0 elseif frac > 1 then frac = 1 end
	local raw = min + frac * (max - min)
	if step and step > 0 then
		raw = min + math.floor((raw - min) / step + 0.5) * step
	end
	if raw < min then raw = min elseif raw > max then raw = max end
	return raw
end

-- Değer -> kaydırıcı konumu (0..1). Dolgu ve tutamaç için.
function Core.valueToFrac(v, min, max)
	if max <= min then return 0 end
	local f = (v - min) / (max - min)
	if f < 0 then return 0 elseif f > 1 then return 1 end
	return f
end

-- Kaydırıcı değeri -> metin (tam sayıysa ondalıksız).
function Core.formatValue(v)
	if v == math.floor(v) then return string.format("%d", v) end
	return (string.format("%.2f", v):gsub("%.?0+$", ""))
end

return Core
