--[[
    ============================================================================
    EasyImport Studio Plugin v5 — Figma JSON + Görsel Galerisi & Otomatik Eşleştirici
    ============================================================================
    v5 değişiklikleri:
      * Galeri artık ServerStorage + StarterGui'nin tamamını tarar (EasyImport_* çıktıları hariç).
      * Katman adında button/btn/buton kelimesi geçen görseller ImageButton olur (_button etiketi de çalışır).
      * Yeni sınıf etiketleri: _TextBox, _VideoFrame, _Frame (+ mevcut _ScrollingFrame, _CanvasGroup, _ViewportFrame ...).
      * Yenilenmiş premium arayüz.

    v3 değişiklikleri (FigBloxUI'den cımbızla alınanlar + kendi çözümlerimiz):

    GALERİ (görseller görünmüyor sorunu)
      * Artımlı tarama: her değişiklikte tüm kutucukları silip yeniden yaratmaz.
        (Eski sürüm Workspace'teki HER nesne eklenişinde galeriyi baştan kuruyordu;
         80 görselde sürekli yeniden yüklenip boş/titrek görünüyordu.)
      * Debounce (0.3 sn) + sadece Decal/Texture/ImageLabel/ImageButton olaylarını dinler.
      * Taranan yerler: ServerStorage, ReplicatedStorage (tam), Workspace (kök + 1 seviye
        + "Loaded"/"FigBloxUI_Images" klasörleri)  -> Asset Manager "Insert" nereye
        düşerse düşsün bulunur.
      * Yüklenemeyen küçük resimlere ⏳ rozeti (moderasyon / yükleme bekliyor).
      * Boş/0 Texture'lar ve nerede kaç görsel bulunduğu tanılama olarak gösterilir.
      * Büyük galeri (alanın ~%42'si), "sadece boşta olanlar" filtresi, kullanılan
        görsellerde ✓ rozeti.

    80 GÖRSEL / ÇOK FRAME SORUNU
      * Aynı PNG'yi kullanan tüm ImageLabel'lar TEK satırda gruplanır; bir kez atarsın,
        hepsi güncellenir. (Figma tarafı zaten aynı görselleri tek PNG yapar.)
      * Kompakt 30px satırlar, "satıra tıkla -> galeriden tıkla -> otomatik sonraki satır".
      * Roblox tarafında da frame sadeleştirme: dolgusu/çizgisi/köşesi olmayan boş
        sarmalayıcı frame'ler silinir, çocukları yukarı taşınır (eski JSON'lar için).
      * Build sonrası otomatik eşleştirme çalışır: isim, Figma node-id sonekı ve
        tekil içerme kuralıyla.
--]]

if not plugin then
	warn("[EasyImport] Bu script bir Roblox Studio Eklentisi (Plugin) olarak çalıştırılmalıdır.")
	return
end

local Plugin = plugin
local HttpService = game:GetService("HttpService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local StarterGui = game:GetService("StarterGui")
local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- <<EASYIMPORT_MODULES>>

-- <<PURE_BEGIN>> (Roblox API'sine bağlı olmayan saf mantık; test edilebilir)

local function normalizeName(s)
	local t = string.lower(tostring(s or ""))
	t = string.gsub(t, "^images/", "")
	t = string.gsub(t, "%.png$", "")
	t = string.gsub(t, "[^a-z0-9]", "")
	return t
end

-- "Star_1-3.png" -> "1-3"  (Figma node-id soneki; EasyImport dosya adlarının sonunda bulunur)
local function figmaIdSuffix(s)
	local t = string.lower(tostring(s or ""))
	t = string.gsub(t, "^images/", "")
	t = string.gsub(t, "%.png$", "")
	local suf = string.match(t, "_([%w%-]+)$")
	if suf and #suf >= 3 and string.find(suf, "%d") and string.find(suf, "%-") then
		return suf
	end
	return nil
end

local function isTaggedName(name)
	local lower = string.lower(tostring(name or ""))
	if string.sub(lower, 1, 1) == "#" or string.sub(lower, 1, 4) == "img:" then
		return true
	end
	for _, tag in ipairs({ "_button", "_scroll", "_canvas", "_aspect", "_hover", "_clicked", "_input", "_textbox", "_image", "_lock" }) do
		if string.find(lower, tag, 1, true) then
			return true
		end
	end
	-- sınıf adı adın içinde doğrudan geçiyorsa (alt çizgi şart değil): "KQWEAMKFWImageButton"
	for _, w in ipairs({ "imagebutton", "imagelabel", "textbutton", "textlabel", "textbox", "scrollingframe", "viewportframe", "canvasgroup", "videoframe" }) do
		if string.find(lower, w, 1, true) then
			return true
		end
	end
	return false
end

local function hasVisibleFill(item, imageCounts)
	if type(item.fills) ~= "table" then
		return false
	end
	for _, f in ipairs(item.fills) do
		if f.type == "SOLID" then
			if (tonumber(f.opacity) or 1) > 0.001 then
				return true
			end
		elseif f.type == "GRADIENT" or f.type == "GRADIENT_OTHER" then
			return true
		elseif imageCounts and f.type == "IMAGE" then
			if (tonumber(f.opacity) or 1) > 0.001 then
				return true
			end
		end
	end
	return false
end

local function childrenInside(item)
	local w, h = tonumber(item.w) or 0, tonumber(item.h) or 0
	if type(item.children) ~= "table" then
		return true
	end
	for _, c in ipairs(item.children) do
		local cx, cy = tonumber(c.x) or 0, tonumber(c.y) or 0
		local cw, ch = tonumber(c.w) or 0, tonumber(c.h) or 0
		if math.abs(tonumber(c.rot) or 0) > 0.01 then
			return false
		end
		if cx < -1 or cy < -1 or cx + cw > w + 1 or cy + ch > h + 1 then
			return false
		end
	end
	return true
end

-- Dolgu/çizgi/köşe/etiket/opaklık/dönüş taşımayan frame = görsel olarak hiçbir şey katmaz.
local function isPlainWrapper(ch, imageCounts)
	if ch.kind ~= "frame" or ch.image or ch.text then
		return false
	end
	if isTaggedName(ch.name) or hasVisibleFill(ch, imageCounts) or ch.stroke then
		return false
	end
	if ch.radius == "full" or (type(ch.radius) == "number" and ch.radius > 0) then
		return false
	end
	if (tonumber(ch.opacity) or 1) < 0.999 or math.abs(tonumber(ch.rot) or 0) > 0.01 then
		return false
	end
	if ch.clips and not childrenInside(ch) then
		return false
	end
	return true
end

-- Alttan yukarı sadeleştirir. stats.flattened / stats.empty sayaçlarını artırır.
local function simplifyTree(item, stats, imageCounts)
	if type(item.children) ~= "table" then
		return
	end
	local out = {}
	for _, ch in ipairs(item.children) do
		simplifyTree(ch, stats, imageCounts)
		if isPlainWrapper(ch, imageCounts) then
			if type(ch.children) == "table" and #ch.children > 0 then
				local ox, oy = tonumber(ch.x) or 0, tonumber(ch.y) or 0
				for _, gc in ipairs(ch.children) do
					gc.x = (tonumber(gc.x) or 0) + ox
					gc.y = (tonumber(gc.y) or 0) + oy
					table.insert(out, gc)
				end
				stats.flattened += 1
			else
				stats.empty += 1
			end
		else
			table.insert(out, ch)
		end
	end
	item.children = out
end

-- groups: { { fileName, name, assigned } }, images: { { assetId, name } }
-- Sonuç: eşleşme listesi { {group=, assetId=} } ve eşleşmeyenlerin adları
local function computeMatches(groups, images)
	local byNorm, bySuffix, list = {}, {}, {}
	for _, img in ipairs(images) do
		local n = normalizeName(img.name)
		if n ~= "" and not byNorm[n] then
			byNorm[n] = img
		end
		local suf = figmaIdSuffix(img.name)
		if suf then
			bySuffix[suf] = bySuffix[suf] or {}
			table.insert(bySuffix[suf], img)
		end
		table.insert(list, { norm = n, img = img })
	end

	local matches, unmatched = {}, {}
	for _, g in ipairs(groups) do
		if not g.assigned or g.assigned == "" then
			local found = nil
			local fileNorm = normalizeName(g.fileName)
			local nameNorm = normalizeName(g.name)

			-- 1) birebir isim
			if fileNorm ~= "" and byNorm[fileNorm] then
				found = byNorm[fileNorm]
			end
			-- 2) Figma node-id soneki (tekil olmalı)
			if not found then
				local suf = figmaIdSuffix(g.fileName)
				if suf and bySuffix[suf] and #bySuffix[suf] == 1 then
					found = bySuffix[suf][1]
				end
			end
			-- 3) tekil içerme (kısa/anlamsız isimlerde yanlış eşleşmeyi önlemek için >= 4 karakter)
			if not found then
				local candidates = {}
				for _, e in ipairs(list) do
					if #e.norm >= 4 then
						local hit = (fileNorm ~= "" and (string.find(fileNorm, e.norm, 1, true) or string.find(e.norm, fileNorm, 1, true)))
							or (fileNorm == "" and nameNorm ~= "" and (string.find(nameNorm, e.norm, 1, true) or string.find(e.norm, nameNorm, 1, true)))
						if hit then
							table.insert(candidates, e.img)
						end
					end
				end
				if #candidates == 1 then
					found = candidates[1]
				end
			end

			if found then
				table.insert(matches, { group = g, assetId = found.assetId })
			else
				table.insert(unmatched, (g.fileName ~= "" and g.fileName) or g.name)
			end
		end
	end
	return matches, unmatched
end

-- <<PURE_END>>

-- ============ RENKLER & KÜÇÜK YARDIMCILAR ============

local COL = {
	bg = Color3.fromRGB(15, 16, 21),
	card = Color3.fromRGB(21, 22, 29),
	card2 = Color3.fromRGB(27, 29, 38),
	panel = Color3.fromRGB(14, 15, 20),
	row = Color3.fromRGB(27, 29, 38),
	rowActive = Color3.fromRGB(58, 46, 112),
	text = Color3.fromRGB(236, 238, 244),
	muted = Color3.fromRGB(138, 143, 161),
	ok = Color3.fromRGB(52, 211, 153),
	warn = Color3.fromRGB(251, 191, 36),
	bad = Color3.fromRGB(248, 113, 113),
	purple = Color3.fromRGB(139, 108, 255),
	purpleSoft = Color3.fromRGB(185, 166, 255),
	indigo = Color3.fromRGB(124, 92, 245),
	green = Color3.fromRGB(27, 29, 38),
	blue = Color3.fromRGB(59, 130, 246),
	red = Color3.fromRGB(46, 29, 35),
	stroke = Color3.fromRGB(39, 42, 53),
	gold = Color3.fromRGB(255, 205, 70),
	off = Color3.fromRGB(43, 46, 58),
}

local MONO = Enum.Font.RobotoMono

local function corner(inst, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r or 6)
	c.Parent = inst
	return c
end

local function addStroke(inst, color, thickness, transparency)
	local st = Instance.new("UIStroke")
	st.Color = color or COL.stroke
	st.Thickness = thickness or 1
	st.Transparency = transparency or 0
	st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	st.Parent = inst
	return st
end

local function addGradient(inst, c0, c1, rotation)
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new(c0, c1)
	g.Rotation = rotation or 0
	g.Parent = inst
	return g
end

local function makeLabel(parent, text, size, bold, color)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Text = text
	l.Font = bold and Enum.Font.GothamBold or Enum.Font.Gotham
	l.TextSize = size or 12
	l.TextColor3 = color or COL.text
	l.TextXAlignment = Enum.TextXAlignment.Left
	l.TextYAlignment = Enum.TextYAlignment.Center
	l.Parent = parent
	return l
end

local function makeButton(parent, text, color, textSize)
	local b = Instance.new("TextButton")
	b.Text = text
	b.Font = Enum.Font.GothamBold
	b.TextSize = textSize or 11
	b.BackgroundColor3 = color
	b.TextColor3 = Color3.new(1, 1, 1)
	b.AutoButtonColor = true
	b.BorderSizePixel = 0
	b.Parent = parent
	corner(b, 7)
	addStroke(b, Color3.new(1, 1, 1), 1, 0.88)
	return b
end

-- Küçük etiket (CHIP): mono yazı, otomatik genişlik
local function makeChip(parent, text, bg, fg, strokeColor)
	local c = Instance.new("TextLabel")
	c.AutomaticSize = Enum.AutomaticSize.X
	c.Size = UDim2.new(0, 0, 0, 22)
	c.BackgroundColor3 = bg or COL.card2
	c.BorderSizePixel = 0
	c.Text = text
	c.Font = MONO
	c.TextSize = 10
	c.TextColor3 = fg or COL.muted
	c.Parent = parent
	corner(c, 6)
	if strokeColor then
		addStroke(c, strokeColor, 1, 0)
	end
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 9)
	pad.PaddingRight = UDim.new(0, 9)
	pad.Parent = c
	return c
end

-- Kart görünümlü düğme (ikincil)
local function makeCardButton(parent, text, fg, bg, strokeColor)
	local b = Instance.new("TextButton")
	b.Text = text
	b.Font = Enum.Font.GothamMedium
	b.TextSize = 13
	b.TextColor3 = fg or COL.text
	b.BackgroundColor3 = bg or COL.card2
	b.AutoButtonColor = true
	b.BorderSizePixel = 0
	b.Parent = parent
	corner(b, 10)
	addStroke(b, strokeColor or COL.stroke, 1, 0)
	return b
end

-- Anahtar (toggle) çizimi: (track, setOn)
local function makeSwitch(parent, w, h)
	w = w or 38
	h = h or 22
	local track = Instance.new("Frame")
	track.AnchorPoint = Vector2.new(1, 0.5)
	track.Position = UDim2.new(1, -14, 0.5, 0)
	track.Size = UDim2.new(0, w, 0, h)
	track.BorderSizePixel = 0
	track.Parent = parent
	corner(track, h // 2)
	local k = h - 6
	local knob = Instance.new("Frame")
	knob.Size = UDim2.new(0, k, 0, k)
	knob.BackgroundColor3 = Color3.new(1, 1, 1)
	knob.BorderSizePixel = 0
	knob.Parent = track
	corner(knob, k // 2)
	local function setOn(on)
		track.BackgroundColor3 = on and COL.purple or COL.off
		knob.Position = on and UDim2.new(1, -(k + 3), 0.5, -k // 2) or UDim2.new(0, 3, 0.5, -k // 2)
	end
	setOn(false)
	return track, setOn
end

-- Numaralı adım rozeti (eski liste satırları için bırakıldı)
local function makeStepBadge(parent, n, x, y)
	local f = Instance.new("Frame")
	f.Position = UDim2.new(0, x, 0, y)
	f.Size = UDim2.new(0, 18, 0, 18)
	f.BackgroundColor3 = Color3.new(1, 1, 1)
	f.BorderSizePixel = 0
	f.Parent = parent
	corner(f, 9)
	addGradient(f, COL.purple, COL.indigo, 45)
	local t = makeLabel(f, tostring(n), 10, true, Color3.new(1, 1, 1))
	t.Size = UDim2.new(1, 0, 1, 0)
	t.TextXAlignment = Enum.TextXAlignment.Center
	return f
end

-- ============ TOOLBAR & WIDGET ============

local toolbar = Plugin:CreateToolbar("EasyImport UI")
local toggleButton = toolbar:CreateButton(
	"EasyImport",
	"Figma JSON -> Roblox UI & Görsel Galerisi Panelini Aç",
	"rbxassetid://11422155683"
)
toggleButton.ClickableWhenViewportHidden = true

local widgetInfo = DockWidgetPluginGuiInfo.new(Enum.InitialDockState.Right, true, false, 520, 800, 380, 520)
local widget = Plugin:CreateDockWidgetPluginGui("EasyImportStudioWidget_v30", widgetInfo)
widget.Title = "EasyImport Pro · Roblox Studio"

toggleButton.Click:Connect(function()
	widget.Enabled = not widget.Enabled
end)

-- ============ ARAYÜZ ============

local rootFrame = Instance.new("Frame")
rootFrame.Size = UDim2.new(1, 0, 1, 0)
rootFrame.BackgroundColor3 = COL.bg
rootFrame.BorderSizePixel = 0
rootFrame.Parent = widget

-- Alt şerit (sabit)
do
	local ft = Instance.new("Frame")
	ft.AnchorPoint = Vector2.new(0, 1)
	ft.Position = UDim2.new(0, 0, 1, 0)
	ft.Size = UDim2.new(1, 0, 0, 34)
	ft.BackgroundColor3 = COL.bg
	ft.BorderSizePixel = 0
	ft.ZIndex = 5
	ft.Parent = rootFrame
	local line = Instance.new("Frame")
	line.Size = UDim2.new(1, 0, 0, 1)
	line.BackgroundColor3 = COL.stroke
	line.BorderSizePixel = 0
	line.ZIndex = 5
	line.Parent = ft
	local dot = makeLabel(ft, "●", 9, false, COL.ok)
	dot.Position = UDim2.new(0, 20, 0, 1)
	dot.Size = UDim2.new(0, 12, 1, -1)
	dot.ZIndex = 5
	local st = makeLabel(ft, "Roblox Studio · Hazır", 11, false, COL.muted)
	st.Font = MONO
	st.Position = UDim2.new(0, 36, 0, 1)
	st.Size = UDim2.new(0.5, -36, 1, -1)
	st.ZIndex = 5
	local ver = makeLabel(ft, "EasyImport / v30", 11, false, COL.muted)
	ver.Font = MONO
	ver.TextXAlignment = Enum.TextXAlignment.Right
	ver.Position = UDim2.new(0.5, 0, 0, 1)
	ver.Size = UDim2.new(0.5, -20, 1, -1)
	ver.ZIndex = 5
end

-- Kaydırılabilir sayfa
local page = Instance.new("ScrollingFrame")
page.Size = UDim2.new(1, 0, 1, -34)
page.BackgroundTransparency = 1
page.BorderSizePixel = 0
page.ScrollBarThickness = 6
page.ScrollBarImageColor3 = COL.off
page.CanvasSize = UDim2.new(0, 0, 0, 0)
page.AutomaticCanvasSize = Enum.AutomaticSize.Y
page.ScrollingDirection = Enum.ScrollingDirection.Y
page.Parent = rootFrame

do
	local lay = Instance.new("UIListLayout")
	lay.Padding = UDim.new(0, 14)
	lay.SortOrder = Enum.SortOrder.LayoutOrder
	lay.Parent = page
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 20)
	pad.PaddingRight = UDim.new(0, 26)
	pad.PaddingTop = UDim.new(0, 18)
	pad.PaddingBottom = UDim.new(0, 24)
	pad.Parent = page
end

local function section(height, order)
	local f = Instance.new("Frame")
	f.BackgroundTransparency = 1
	f.BorderSizePixel = 0
	f.Size = UDim2.new(1, 0, 0, height)
	f.LayoutOrder = order
	f.Parent = page
	return f
end

local function cardFrame(parent, radius)
	local f = Instance.new("Frame")
	f.BackgroundColor3 = COL.card
	f.BorderSizePixel = 0
	f.Parent = parent
	corner(f, radius or 12)
	addStroke(f, COL.stroke, 1, 0)
	return f
end

-- 1) Başlık
do
	local hd = section(54, 1)
	local logo = Instance.new("Frame")
	logo.BackgroundColor3 = Color3.fromRGB(36, 30, 71)
	logo.Size = UDim2.new(0, 52, 0, 52)
	logo.BorderSizePixel = 0
	logo.Parent = hd
	corner(logo, 14)
	addStroke(logo, Color3.fromRGB(74, 61, 148), 1, 0)
	local lgt = makeLabel(logo, "⇄", 24, true, COL.purpleSoft)
	lgt.Size = UDim2.new(1, 0, 1, 0)
	lgt.TextXAlignment = Enum.TextXAlignment.Center

	local title = makeLabel(hd, "EasyImport", 22, true, COL.text)
	title.Position = UDim2.new(0, 68, 0, 2)
	title.Size = UDim2.new(0, 124, 0, 26)
	local sub = makeLabel(hd, "Figma → Roblox Studio", 12, false, COL.muted)
	sub.Position = UDim2.new(0, 68, 0, 32)
	sub.Size = UDim2.new(0, 240, 0, 16)
	local tag = makeChip(hd, "STUDIO", COL.card2, COL.muted)
	tag.Font = Enum.Font.GothamBold
	tag.AnchorPoint = Vector2.new(1, 0)
	tag.Position = UDim2.new(1, 0, 0, 0)
	tag.Size = UDim2.new(0, 0, 0, 24)
end

-- 2) Adım göstergesi
do
	local stp = section(26, 2)
	local steps = {
		{ "✓", "Hazırla", true, 0 },
		{ "✓", "Dışa aktar", true, 0.36 },
		{ "03", "İçe aktar", false, 0.72 },
	}
	for i, s in ipairs(steps) do
		local item = Instance.new("Frame")
		item.BackgroundTransparency = 1
		item.Position = UDim2.new(s[4], 0, 0, 0)
		item.Size = UDim2.new(0, 120, 1, 0)
		item.Parent = stp
		local dot = makeLabel(item, s[1], 10, true, s[3] and COL.ok or Color3.new(1, 1, 1))
		dot.Font = s[3] and Enum.Font.GothamBold or MONO
		dot.Size = UDim2.new(0, 24, 0, 24)
		dot.TextXAlignment = Enum.TextXAlignment.Center
		dot.BackgroundTransparency = 0
		dot.BackgroundColor3 = s[3] and Color3.fromRGB(18, 58, 44) or COL.purple
		corner(dot, 12)
		local lb = makeLabel(item, s[2], 12, not s[3], s[3] and COL.muted or COL.text)
		lb.Position = UDim2.new(0, 32, 0, 0)
		lb.Size = UDim2.new(1, -32, 0, 24)
		if i < #steps then
			local ln = Instance.new("Frame")
			ln.BackgroundColor3 = COL.stroke
			ln.BorderSizePixel = 0
			ln.Position = UDim2.new(s[4], 112, 0, 12)
			ln.Size = UDim2.new(0.36, -128, 0, 1)
			ln.Parent = stp
		end
	end
end

-- 3) Bölüm başlığı: JSON'dan arayüz oluştur
do
	local tb = section(50, 3)
	local t = makeLabel(tb, "JSON’dan arayüz oluştur", 18, true, COL.text)
	t.Size = UDim2.new(1, -130, 0, 24)
	local s = makeLabel(tb, "Figma çıktısını yapıştır, Studio’da UI’ını oluştur.", 12, false, COL.muted)
	s.Position = UDim2.new(0, 0, 0, 28)
	s.Size = UDim2.new(1, 0, 0, 18)
	local c = makeChip(tb, "01 / İÇE AKTAR", COL.card2, COL.muted)
	c.AnchorPoint = Vector2.new(1, 0)
	c.Position = UDim2.new(1, 0, 0, 0)
end

-- 4) JSON kartı
local jsonBox, jsonStateLabel
do
	local sec = section(150, 4)
	local card = cardFrame(sec, 12)
	card.Size = UDim2.new(1, 0, 1, 0)
	local hdr = makeLabel(card, "[]  JSON", 11, false, COL.muted)
	hdr.Font = MONO
	hdr.Position = UDim2.new(0, 14, 0, 0)
	hdr.Size = UDim2.new(0.5, 0, 0, 34)
	jsonStateLabel = makeLabel(card, "Veri bekleniyor", 11, false, COL.muted)
	jsonStateLabel.Font = MONO
	jsonStateLabel.TextXAlignment = Enum.TextXAlignment.Right
	jsonStateLabel.Position = UDim2.new(0.5, 0, 0, 0)
	jsonStateLabel.Size = UDim2.new(0.5, -14, 0, 34)
	local div = Instance.new("Frame")
	div.Position = UDim2.new(0, 0, 0, 34)
	div.Size = UDim2.new(1, 0, 0, 1)
	div.BackgroundColor3 = COL.stroke
	div.BorderSizePixel = 0
	div.Parent = card
	local ln = makeLabel(card, "1", 11, false, Color3.fromRGB(85, 90, 107))
	ln.Font = MONO
	ln.Position = UDim2.new(0, 14, 0, 46)
	ln.Size = UDim2.new(0, 16, 0, 16)
	ln.TextXAlignment = Enum.TextXAlignment.Right

	jsonBox = Instance.new("TextBox")
	jsonBox.Position = UDim2.new(0, 42, 0, 44)
	jsonBox.Size = UDim2.new(1, -56, 1, -54)
	jsonBox.BackgroundTransparency = 1
	jsonBox.ClearTextOnFocus = false
	jsonBox.MultiLine = true
	jsonBox.TextWrapped = false
	jsonBox.TextXAlignment = Enum.TextXAlignment.Left
	jsonBox.TextYAlignment = Enum.TextYAlignment.Top
	jsonBox.Font = Enum.Font.Code
	jsonBox.TextSize = 12
	jsonBox.TextColor3 = Color3.fromRGB(216, 180, 254)
	jsonBox.Text = ""
	jsonBox.PlaceholderText = "Figma Plugin’den kopyaladığın JSON’u buraya yapıştır…"
	jsonBox.PlaceholderColor3 = Color3.fromRGB(100, 106, 126)
	jsonBox.ClipsDescendants = true
	jsonBox.BorderSizePixel = 0
	jsonBox.Parent = card

	jsonBox:GetPropertyChangedSignal("Text"):Connect(function()
		local n = #jsonBox.Text
		if n > 0 then
			jsonStateLabel.Text = string.format("Veri hazır · %d karakter", n)
			jsonStateLabel.TextColor3 = COL.ok
		else
			jsonStateLabel.Text = "Veri bekleniyor"
			jsonStateLabel.TextColor3 = COL.muted
		end
	end)
end

-- v4: Responsive ölçek (UIScale) + AspectRatio seçenekleri (Studio'da kalıcı)
local SCALE_MODES = { "Fit", "Fill", "Width", "Height" }
local SCALE_MODE_TR = { Fit = "Sığdır", Fill = "Doldur", Width = "Genişlik", Height = "Yükseklik" }
local OPT = {
	responsive = Plugin:GetSetting("EasyImport_Responsive") ~= false,
	aspect = Plugin:GetSetting("EasyImport_Aspect") ~= false,
	offset = Plugin:GetSetting("EasyImport_Offset") ~= false,
	scaleMode = Plugin:GetSetting("EasyImport_ScaleMode") or "Fit",
}
if not SCALE_MODE_TR[OPT.scaleMode] then OPT.scaleMode = "Fit" end

-- 5) Scale / Offset anahtarları: arayüzden kaldırıldı. OPT.responsive / OPT.offset değerleri
-- Studio ayarından okunmaya devam eder (varsayılan: açık).

-- 6) UI oluştur
local buildButton
do
	local sec = section(46, 6)
	buildButton = Instance.new("TextButton")
	buildButton.Text = "◈   UI oluştur"
	buildButton.Font = Enum.Font.GothamBold
	buildButton.TextSize = 14
	buildButton.TextColor3 = Color3.new(1, 1, 1)
	buildButton.BackgroundColor3 = COL.purple
	buildButton.AutoButtonColor = true
	buildButton.BorderSizePixel = 0
	buildButton.Size = UDim2.new(1, 0, 1, 0)
	buildButton.Parent = sec
	corner(buildButton, 11)
end

-- 7) Konsol
local statusLabel, statusBadge
do
	local card = cardFrame(page, 12)
	card.LayoutOrder = 7
	card.AutomaticSize = Enum.AutomaticSize.Y
	card.Size = UDim2.new(1, 0, 0, 78)
	local lay = Instance.new("UIListLayout")
	lay.Padding = UDim.new(0, 10)
	lay.SortOrder = Enum.SortOrder.LayoutOrder
	lay.Parent = card
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 16)
	pad.PaddingRight = UDim.new(0, 16)
	pad.PaddingTop = UDim.new(0, 12)
	pad.PaddingBottom = UDim.new(0, 14)
	pad.Parent = card

	local head = Instance.new("Frame")
	head.BackgroundTransparency = 1
	head.Size = UDim2.new(1, 0, 0, 22)
	head.LayoutOrder = 1
	head.Parent = card
	local k = makeLabel(head, "KONSOL", 10, false, COL.muted)
	k.Font = MONO
	k.Size = UDim2.new(0.5, 0, 1, 0)
	statusBadge = makeChip(head, "HAZIR", Color3.fromRGB(18, 58, 44), COL.ok)
	statusBadge.AnchorPoint = Vector2.new(1, 0)
	statusBadge.Position = UDim2.new(1, 0, 0, 0)

	statusLabel = makeLabel(card, "› Hazır. JSON yapıştırıp “UI oluştur”a bas.", 12, false, COL.ok)
	statusLabel.Font = MONO
	statusLabel.LayoutOrder = 2
	statusLabel.AutomaticSize = Enum.AutomaticSize.Y
	statusLabel.Size = UDim2.new(1, 0, 0, 16)
	statusLabel.TextWrapped = true
	statusLabel.TextYAlignment = Enum.TextYAlignment.Top
end

local function setStatus(text, color)
	color = color or COL.ok
	statusLabel.Text = "› " .. tostring(text)
	statusLabel.TextColor3 = color
	if color == COL.warn then
		statusBadge.Text, statusBadge.TextColor3, statusBadge.BackgroundColor3 = "UYARI", COL.warn, Color3.fromRGB(60, 48, 16)
	elseif color == COL.bad then
		statusBadge.Text, statusBadge.TextColor3, statusBadge.BackgroundColor3 = "HATA", COL.bad, Color3.fromRGB(62, 28, 32)
	elseif color == COL.muted then
		statusBadge.Text, statusBadge.TextColor3, statusBadge.BackgroundColor3 = "BİLGİ", COL.muted, COL.card2
	else
		statusBadge.Text, statusBadge.TextColor3, statusBadge.BackgroundColor3 = "HAZIR", COL.ok, Color3.fromRGB(18, 58, 44)
	end
end

-- 8) Ayırıcı
do
	local d = section(1, 8)
	d.BackgroundTransparency = 0
	d.BackgroundColor3 = COL.stroke
end

-- 9) Galeri başlığı
local galleryHeader
do
	local sec = section(46, 9)
	local t = makeLabel(sec, "Galeri", 18, true, COL.text)
	t.Size = UDim2.new(1, -130, 0, 24)
	galleryHeader = makeLabel(sec, "0 görsel · 0 boşta", 12, false, COL.muted)
	galleryHeader.Position = UDim2.new(0, 0, 0, 28)
	galleryHeader.Size = UDim2.new(1, 0, 0, 18)
	local c = makeChip(sec, "02 / EŞLEŞTİR", COL.card2, COL.muted)
	c.AnchorPoint = Vector2.new(1, 0)
	c.Position = UDim2.new(1, 0, 0, 0)
end

-- 10) Galeri düğmeleri
local autoMatchBtn, refreshGalleryBtn, cleanDecalsBtn
local DECAL_LABEL = "🗑  Decal sil"
do
	local sec = section(42, 10)
	autoMatchBtn = makeCardButton(sec, "🔗  İsimden eşleştir")
	autoMatchBtn.Size = UDim2.new(0.52, -4, 1, 0)
	refreshGalleryBtn = makeCardButton(sec, "⛶  Tara")
	refreshGalleryBtn.Position = UDim2.new(0.52, 2, 0, 0)
	refreshGalleryBtn.Size = UDim2.new(0.2, -4, 1, 0)
	cleanDecalsBtn = makeCardButton(sec, DECAL_LABEL, COL.bad, COL.red, Color3.fromRGB(86, 44, 52))
	cleanDecalsBtn.Position = UDim2.new(0.72, 2, 0, 0)
	cleanDecalsBtn.Size = UDim2.new(0.28, -2, 1, 0)
end

-- 11) Filtre satırı
local filterBtn, setFilterVisual
do
	local sec = section(26, 11)
	local l = makeLabel(sec, "Yüklenen görselleri arayüzünle eşleştir.", 12, false, COL.muted)
	l.Size = UDim2.new(0.6, 0, 1, 0)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	filterBtn = Instance.new("TextButton")
	filterBtn.Text = ""
	filterBtn.AutoButtonColor = false
	filterBtn.BackgroundTransparency = 1
	filterBtn.AnchorPoint = Vector2.new(1, 0)
	filterBtn.Position = UDim2.new(1, 0, 0, 0)
	filterBtn.Size = UDim2.new(0, 190, 1, 0)
	filterBtn.Parent = sec
	local fl = makeLabel(filterBtn, "Sadece boşta", 12, false, COL.text)
	fl.TextXAlignment = Enum.TextXAlignment.Right
	fl.Size = UDim2.new(1, -92, 1, 0)
	local fs = makeLabel(filterBtn, "KAPALI", 9, false, COL.muted)
	fs.Font = MONO
	fs.Position = UDim2.new(1, -88, 0, 0)
	fs.Size = UDim2.new(0, 44, 1, 0)
	fs.TextXAlignment = Enum.TextXAlignment.Center
	local _, setSw = makeSwitch(filterBtn, 38, 22)
	local tr = filterBtn:FindFirstChildOfClass("Frame")
	if tr then tr.Position = UDim2.new(1, 0, 0.5, 0) end
	setSw(false)
	setFilterVisual = function(on)
		fs.Text = on and "AÇIK" or "KAPALI"
		fs.TextColor3 = on and COL.purpleSoft or COL.muted
		setSw(on)
	end
end

-- 12) Galeri kutusu (ızgara + boş durum)
local galleryScroll, galleryEmpty, galleryHint
do
	local sec = section(236, 12)
	local box = cardFrame(sec, 12)
	box.Size = UDim2.new(1, 0, 1, 0)
	box.ClipsDescendants = true

	galleryScroll = Instance.new("ScrollingFrame")
	galleryScroll.Size = UDim2.new(1, 0, 1, 0)
	galleryScroll.BackgroundTransparency = 1
	galleryScroll.CanvasSize = UDim2.new(0, 0, 0, 0)
	galleryScroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
	galleryScroll.ScrollBarThickness = 6
	galleryScroll.BorderSizePixel = 0
	galleryScroll.ScrollBarImageColor3 = COL.purple
	galleryScroll.Visible = false
	galleryScroll.Parent = box

	local galleryGrid = Instance.new("UIGridLayout")
	galleryGrid.CellSize = UDim2.new(0, 58, 0, 60)
	galleryGrid.CellPadding = UDim2.new(0, 4, 0, 4)
	galleryGrid.SortOrder = Enum.SortOrder.LayoutOrder
	galleryGrid.Parent = galleryScroll

	local galleryPad = Instance.new("UIPadding")
	galleryPad.PaddingTop = UDim.new(0, 8)
	galleryPad.PaddingLeft = UDim.new(0, 8)
	galleryPad.PaddingBottom = UDim.new(0, 8)
	galleryPad.Parent = galleryScroll

	galleryEmpty = Instance.new("Frame")
	galleryEmpty.Size = UDim2.new(1, 0, 1, 0)
	galleryEmpty.BackgroundTransparency = 1
	galleryEmpty.ZIndex = 2
	galleryEmpty.Parent = box

	local ico = Instance.new("Frame")
	ico.Position = UDim2.new(0, 20, 0, 20)
	ico.Size = UDim2.new(0, 44, 0, 44)
	ico.BackgroundColor3 = COL.card2
	ico.BorderSizePixel = 0
	ico.ZIndex = 2
	ico.Parent = galleryEmpty
	corner(ico, 10)
	local icoT = makeLabel(ico, "🖼", 20, false, COL.muted)
	icoT.Size = UDim2.new(1, 0, 1, 0)
	icoT.TextXAlignment = Enum.TextXAlignment.Center
	icoT.ZIndex = 2

	local t1 = makeLabel(galleryEmpty, "Henüz görsel bulunamadı.", 14, true, COL.text)
	t1.Position = UDim2.new(0, 76, 0, 20)
	t1.Size = UDim2.new(1, -96, 0, 22)
	t1.ZIndex = 2
	local t2 = makeLabel(galleryEmpty, "Görsellerini yükledikten sonra “Tara”ya bas.", 12, false, COL.muted)
	t2.Position = UDim2.new(0, 76, 0, 42)
	t2.Size = UDim2.new(1, -96, 0, 20)
	t2.ZIndex = 2
	t2.TextTruncate = Enum.TextTruncate.AtEnd

	local stepsTxt = {
		"Figma’dan indirdiğin ZIP’i çıkar.",
		"Asset Manager → Bulk Import ile PNG’leri yükle.",
		"Yüklenenleri seç → Sağ tık → Insert (ServerStorage veya StarterGui).",
	}
	for i, txt in ipairs(stepsTxt) do
		local y = 82 + (i - 1) * 26
		local bd = makeLabel(galleryEmpty, tostring(i), 10, false, COL.muted)
		bd.Font = MONO
		bd.Position = UDim2.new(0, 20, 0, y)
		bd.Size = UDim2.new(0, 20, 0, 20)
		bd.TextXAlignment = Enum.TextXAlignment.Center
		bd.BackgroundTransparency = 0
		bd.BackgroundColor3 = COL.card2
		bd.ZIndex = 2
		corner(bd, 10)
		local tx = makeLabel(galleryEmpty, txt, 12, false, COL.text)
		tx.Position = UDim2.new(0, 50, 0, y)
		tx.Size = UDim2.new(1, -70, 0, 20)
		tx.ZIndex = 2
		tx.TextTruncate = Enum.TextTruncate.AtEnd
	end

	local dv = Instance.new("Frame")
	dv.Position = UDim2.new(0, 20, 0, 168)
	dv.Size = UDim2.new(1, -40, 0, 1)
	dv.BackgroundColor3 = COL.stroke
	dv.BorderSizePixel = 0
	dv.ZIndex = 2
	dv.Parent = galleryEmpty

	galleryHint = makeLabel(galleryEmpty, "", 10, false, COL.muted)
	galleryHint.Font = MONO
	galleryHint.Position = UDim2.new(0, 20, 0, 178)
	galleryHint.Size = UDim2.new(1, -40, 1, -186)
	galleryHint.TextWrapped = true
	galleryHint.TextXAlignment = Enum.TextXAlignment.Left
	galleryHint.TextYAlignment = Enum.TextYAlignment.Top
	galleryHint.ZIndex = 2
end

-- 13) Benzersiz görseller başlığı
local listHeader, listHelp, listChip
do
	local sec = section(46, 13)
	listHeader = makeLabel(sec, "Benzersiz görseller", 18, true, COL.text)
	listHeader.Size = UDim2.new(1, -110, 0, 24)
	listHelp = makeLabel(sec, "Satıra tıkla → içindeki görseli tekli aç.", 12, false, COL.muted)
	listHelp.Position = UDim2.new(0, 0, 0, 28)
	listHelp.Size = UDim2.new(1, 0, 0, 18)
	listHelp.TextTruncate = Enum.TextTruncate.AtEnd
	listChip = makeChip(sec, "0 PNG", COL.card2, COL.muted)
	listChip.AnchorPoint = Vector2.new(1, 0)
	listChip.Position = UDim2.new(1, 0, 0, 0)
end

-- 14) Benzersiz görsel listesi (+ boş durum)
local listSec, listScroll, listEmpty
do
	listSec = section(112, 14)
	local box = cardFrame(listSec, 12)
	box.Size = UDim2.new(1, 0, 1, 0)
	box.ClipsDescendants = true

	listScroll = Instance.new("ScrollingFrame")
	listScroll.Size = UDim2.new(1, 0, 1, 0)
	listScroll.BackgroundTransparency = 1
	listScroll.CanvasSize = UDim2.new(0, 0, 0, 0)
	listScroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
	listScroll.ScrollBarThickness = 6
	listScroll.BorderSizePixel = 0
	listScroll.ScrollBarImageColor3 = COL.purple
	listScroll.Visible = false
	listScroll.Parent = box

	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 2)
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = listScroll

	local listPad = Instance.new("UIPadding")
	listPad.PaddingTop = UDim.new(0, 6)
	listPad.PaddingLeft = UDim.new(0, 6)
	listPad.PaddingRight = UDim.new(0, 6)
	listPad.PaddingBottom = UDim.new(0, 6)
	listPad.Parent = listScroll

	listEmpty = Instance.new("Frame")
	listEmpty.Size = UDim2.new(1, 0, 1, 0)
	listEmpty.BackgroundTransparency = 1
	listEmpty.Parent = box
	local ic = makeLabel(listEmpty, "🖼", 20, false, COL.muted)
	ic.Position = UDim2.new(0, 0, 0, 14)
	ic.Size = UDim2.new(1, 0, 0, 26)
	ic.TextXAlignment = Enum.TextXAlignment.Center
	local e1 = makeLabel(listEmpty, "Henüz benzersiz görsel yok", 14, true, COL.text)
	e1.Position = UDim2.new(0, 0, 0, 46)
	e1.Size = UDim2.new(1, 0, 0, 22)
	e1.TextXAlignment = Enum.TextXAlignment.Center
	local e2 = makeLabel(listEmpty, "Aynı PNG’yi kullananlar birlikte görüntülenir.", 12, false, COL.muted)
	e2.Position = UDim2.new(0, 0, 0, 70)
	e2.Size = UDim2.new(1, 0, 0, 20)
	e2.TextXAlignment = Enum.TextXAlignment.Center
end

-- ============ DURUM ============

local groups = {} -- sıralı: { key, fileName, name, instances, assigned, row, dot, thumb, idBox, nameLabel }
local groupByKey = {}
local activeGroup = nil
local pendingAsset = nil
local hideUsed = false

local assignGroup -- ileri tanım (aşağıda atanır)
local galleryTiles = {} -- assetId -> { tile, stroke, usedMark, name }
local galleryImages = {}
local lastDiag = ""

local function assetIdFromImageString(s)
	local id = string.match(tostring(s or ""), "%d+")
	if id and id ~= "0" then
		return id
	end
	return nil
end

-- ============ GALERİ ============

local function usedAssetSet()
	local used = {}
	for _, g in ipairs(groups) do
		if g.assigned and g.assigned ~= "" then
			used[g.assigned] = true
		end
	end
	return used
end

local function updateGalleryMarks()
	local used = usedAssetSet()
	local total, free = 0, 0
	for id, t in pairs(galleryTiles) do
		total += 1
		local isUsed = used[id] == true
		if not isUsed then
			free += 1
		end
		t.usedMark.Visible = isUsed
		t.tile.Visible = not (hideUsed and isUsed)
		t.stroke.Color = (id == pendingAsset) and COL.gold or COL.stroke
		t.stroke.Thickness = (id == pendingAsset) and 2.5 or 1
	end
	galleryHeader.Text = string.format("%d görsel · %d boşta", total, free)
end

-- Bir Decal/Texture/ImageLabel için görünen ad: genel adlarda ebeveyn adını dene
local GENERIC_NAMES = { decal = true, texture = true, imagelabel = true, imagebutton = true, image = true }

local function displayNameFor(desc)
	local name = tostring(desc.Name or "")
	if GENERIC_NAMES[string.lower(name)] and desc.Parent and desc.Parent ~= game then
		local p = desc.Parent
		if p ~= Workspace and p ~= ServerStorage and p ~= ReplicatedStorage and p ~= StarterGui then
			name = p.Name
		end
	end
	name = string.gsub(name, "^Images/", "")
	return name
end

-- Başkasına ait olduğu için galeriden hariç tutulan görsel adları (küçük harf, içerir).
local EXCLUDED_GALLERY_NAMES = { "baseplate" }
local function isExcludedGalleryName(name)
	local low = string.lower(name)
	for _, w in ipairs(EXCLUDED_GALLERY_NAMES) do
		if string.find(low, w, 1, true) then return true end
	end
	return false
end

local function considerImage(desc, images, seen, diag)
	local assetId
	if desc:IsA("Decal") or desc:IsA("Texture") then
		assetId = desc.Texture
		diag.decals += 1
	elseif desc:IsA("ImageLabel") or desc:IsA("ImageButton") then
		assetId = desc.Image
		diag.imagelabels += 1
	else
		return
	end
	local id = assetIdFromImageString(assetId)
	if not id then
		diag.empty += 1
		return
	end
	local name = displayNameFor(desc)
	if isExcludedGalleryName(name) then
		return
	end
	if seen[id] then
		return
	end
	seen[id] = true
	table.insert(images, { assetId = id, name = name })
end

local function isImageHolderClass(inst)
	return inst:IsA("Decal") or inst:IsA("Texture") or inst:IsA("ImageLabel") or inst:IsA("ImageButton")
end

local function scanForImages()
	local images, seen = {}, {}
	local diag = { decals = 0, imagelabels = 0, empty = 0, ss = 0, rs = 0, ws = 0, sg = 0 }

	local function scanTree(root)
		for _, desc in ipairs(root:GetDescendants()) do
			considerImage(desc, images, seen, diag)
		end
	end

	local before = #images
	scanTree(ServerStorage)
	diag.ss = #images - before
	before = #images
	scanTree(ReplicatedStorage)
	diag.rs = #images - before

	before = #images
	for _, child in ipairs(Workspace:GetChildren()) do
		if not child:IsA("Terrain") and not child:IsA("Camera") then
			considerImage(child, images, seen, diag)
			if child.Name == "Loaded" or child.Name == "FigBloxUI_Images" then
				scanTree(child)
			else
				for _, gc in ipairs(child:GetChildren()) do
					considerImage(gc, images, seen, diag)
				end
			end
		end
	end
	diag.ws = #images - before

	-- v5: StarterGui'nin TAMAMI taranır (Asset Manager'dan eklenen görseller nereye düşerse düşsün).
	-- EasyImport'un kendi ürettiği ScreenGui'ler (EasyImport_*) hariç tutulur; böylece atanan görseller galeriye geri sızmaz.
	local function insideOwnOutput(inst)
		local p = inst
		while p and p ~= StarterGui do
			if p.Parent == StarterGui and string.sub(p.Name, 1, 11) == "EasyImport_" then
				return true
			end
			p = p.Parent
		end
		return false
	end
	before = #images
	for _, d in ipairs(StarterGui:GetDescendants()) do
		if isImageHolderClass(d) and not insideOwnOutput(d) then
			considerImage(d, images, seen, diag)
		end
	end
	diag.sg = #images - before

	table.sort(images, function(a, b)
		return string.lower(a.name) < string.lower(b.name)
	end)
	return images, diag
end

local function createTile(img)
	local tile = Instance.new("TextButton")
	tile.Name = img.assetId
	tile.Text = ""
	tile.AutoButtonColor = true
	tile.BackgroundColor3 = COL.card
	tile.BorderSizePixel = 0
	tile.Parent = galleryScroll
	corner(tile, 7)

	local stroke = Instance.new("UIStroke")
	stroke.Color = COL.stroke
	stroke.Thickness = 1
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Parent = tile

	local thumb = Instance.new("ImageLabel")
	thumb.Size = UDim2.new(1, -6, 1, -18)
	thumb.Position = UDim2.new(0, 3, 0, 3)
	thumb.BackgroundTransparency = 1
	thumb.Image = "rbxassetid://" .. img.assetId
	thumb.ScaleType = Enum.ScaleType.Fit
	thumb.Parent = tile

	local caption = Instance.new("TextLabel")
	caption.Size = UDim2.new(1, -4, 0, 13)
	caption.Position = UDim2.new(0, 2, 1, -14)
	caption.BackgroundTransparency = 1
	caption.Text = img.name
	caption.Font = Enum.Font.Gotham
	caption.TextColor3 = Color3.fromRGB(210, 215, 230)
	caption.TextSize = 9
	caption.TextTruncate = Enum.TextTruncate.AtEnd
	caption.Parent = tile

	local usedMark = Instance.new("TextLabel")
	usedMark.Size = UDim2.new(0, 14, 0, 14)
	usedMark.Position = UDim2.new(1, -15, 0, 1)
	usedMark.BackgroundColor3 = Color3.fromRGB(22, 130, 78)
	usedMark.Text = "✓"
	usedMark.Font = Enum.Font.GothamBold
	usedMark.TextSize = 10
	usedMark.TextColor3 = Color3.new(1, 1, 1)
	usedMark.Visible = false
	usedMark.ZIndex = 3
	usedMark.Parent = tile
	corner(usedMark, 7)

	-- Yüklenemeyen küçük resim = büyük ihtimalle yükleme/moderasyon bekliyor
	local pendingMark = Instance.new("TextLabel")
	pendingMark.Size = UDim2.new(1, -6, 1, -18)
	pendingMark.Position = UDim2.new(0, 3, 0, 3)
	pendingMark.BackgroundTransparency = 1
	pendingMark.Text = "⏳"
	pendingMark.TextSize = 18
	pendingMark.TextColor3 = COL.warn
	pendingMark.Visible = false
	pendingMark.ZIndex = 2
	pendingMark.Parent = tile

	local function checkLoaded()
		local ok, loaded = pcall(function()
			return thumb.IsLoaded
		end)
		pendingMark.Visible = ok and not loaded
	end
	pcall(function()
		thumb:GetPropertyChangedSignal("IsLoaded"):Connect(checkLoaded)
	end)
	task.delay(6, function()
		if thumb.Parent then
			checkLoaded()
		end
	end)

	tile.MouseButton1Click:Connect(function()
		local g = activeGroup
		if g then
			pendingAsset = nil
			assignGroup(g, img.assetId, true)
		else
			if pendingAsset == img.assetId then
				pendingAsset = nil
			else
				pendingAsset = img.assetId
			end
			updateGalleryMarks()
		end
	end)

	galleryTiles[img.assetId] = { tile = tile, stroke = stroke, usedMark = usedMark, name = img.name, caption = caption }
end

local function refreshGallery()
	local images, diag = scanForImages()
	local seen = {}
	for i, img in ipairs(images) do
		seen[img.assetId] = true
		if not galleryTiles[img.assetId] then
			createTile(img)
		end
		local t = galleryTiles[img.assetId]
		t.tile.LayoutOrder = i
		t.caption.Text = img.name
	end
	for id, t in pairs(galleryTiles) do
		if not seen[id] then
			t.tile:Destroy()
			galleryTiles[id] = nil
			if pendingAsset == id then
				pendingAsset = nil
			end
		end
	end
	galleryImages = images

	lastDiag = string.format(
		"ServerStorage:%d · StarterGui:%d · ReplicatedStorage:%d · Workspace:%d  (Decal/Texture:%d, ImageLabel/Button:%d, boş:%d)",
		diag.ss, diag.sg, diag.rs, diag.ws, diag.decals, diag.imagelabels, diag.empty
	)

	if #images == 0 then
		galleryEmpty.Visible = true
		galleryScroll.Visible = false
		galleryHint.Text = string.format(
			"Taranan: ServerStorage · StarterGui · ReplicatedStorage · Workspace\nDecal/Texture: %d · ImageLabel/ImageButton: %d · Boş: %d",
			diag.decals, diag.imagelabels, diag.empty
		) .. (diag.empty > 0 and "\n⚠ Boş Texture'lı Decal var: görsel henüz yüklenmemiş/moderasyonda olabilir." or "")
	else
		galleryEmpty.Visible = false
		galleryScroll.Visible = true
	end
	updateGalleryMarks()
end

-- Debounce: toplu Insert/silme olaylarında tek tarama
local refreshQueued = false
local function scheduleRefresh()
	if refreshQueued then
		return
	end
	refreshQueued = true
	task.delay(0.3, function()
		refreshQueued = false
		refreshGallery()
	end)
end

local function isImageHolder(inst)
	return inst:IsA("Decal") or inst:IsA("Texture") or inst:IsA("ImageLabel") or inst:IsA("ImageButton")
end

-- ============ GÖRSEL GRUPLARI (aynı PNG = tek satır) ============

local rowCounter = 0

local function setActiveGroup(g)
	activeGroup = g
	for _, other in ipairs(groups) do
		if other.row and other.row.Parent then
			other.row.BackgroundColor3 = (other == g) and COL.rowActive or COL.row
		end
	end
end

local function refreshGroupVisual(g)
	local has = g.assigned and g.assigned ~= ""
	g.dot.Text = has and "✓" or "•"
	g.dot.TextColor3 = has and COL.ok or COL.warn
	g.thumb.Image = has and ("rbxassetid://" .. g.assigned) or "rbxasset://textures/ui/GuiImagePlaceholder.png"
	g.thumb.ImageTransparency = has and 0 or 0.4
	if g.idBox.Text ~= (g.assigned or "") and not g.idBox:IsFocused() then
		g.idBox.Text = g.assigned or ""
	end
end

local function updateListHeader()
	local filled = 0
	for _, g in ipairs(groups) do
		if g.assigned and g.assigned ~= "" then
			filled += 1
		end
	end
	local uses = 0
	for _, g in ipairs(groups) do
		uses += #g.instances
	end
	if #groups == 0 then
		listChip.Text = "0 PNG"
	else
		listChip.Text = string.format("%d/%d dolu · %d kullanım", filled, #groups, uses)
	end
	listChip.TextColor3 = (#groups > 0 and filled == #groups) and COL.ok or COL.muted
	listEmpty.Visible = #groups == 0
	listScroll.Visible = #groups > 0
	listSec.Size = UDim2.new(1, 0, 0, #groups == 0 and 112 or 236)
end

assignGroup = function(g, assetId, advance)
	local imageStr = "rbxassetid://" .. assetId
	for _, inst in ipairs(g.instances) do
		if inst.Parent then
			pcall(function()
				inst.Image = imageStr
			end)
		end
	end
	g.assigned = assetId
	refreshGroupVisual(g)
	updateListHeader()
	updateGalleryMarks()

	if advance then
		local startIdx = table.find(groups, g) or 0
		local nextG = nil
		for step = 1, #groups do
			local cand = groups[((startIdx + step - 1) % #groups) + 1]
			if cand ~= g and (not cand.assigned or cand.assigned == "") then
				nextG = cand
				break
			end
		end
		if nextG then
			setActiveGroup(nextG)
			local idx = table.find(groups, nextG) or 1
			listScroll.CanvasPosition = Vector2.new(0, math.max(0, (idx - 1) * 32 - 32))
		else
			setActiveGroup(nil)
		end
	end
end

local function clearImageList()
	for _, child in ipairs(listScroll:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	groups = {}
	groupByKey = {}
	activeGroup = nil
	rowCounter = 0
	updateListHeader()
	updateGalleryMarks()
end

local function createGroupRow(g)
	local row = Instance.new("TextButton")
	row.Size = UDim2.new(1, 0, 0, 30)
	row.BackgroundColor3 = COL.row
	row.BorderSizePixel = 0
	row.Text = ""
	row.AutoButtonColor = false
	row.LayoutOrder = g.order
	row.Parent = listScroll
	corner(row, 7)
	g.row = row

	local dot = makeLabel(row, "•", 14, true, COL.warn)
	dot.Position = UDim2.new(0, 2, 0, 0)
	dot.Size = UDim2.new(0, 14, 1, 0)
	dot.TextXAlignment = Enum.TextXAlignment.Center
	g.dot = dot

	local thumb = Instance.new("ImageLabel")
	thumb.Position = UDim2.new(0, 18, 0.5, -12)
	thumb.Size = UDim2.new(0, 24, 0, 24)
	thumb.BackgroundColor3 = COL.panel
	thumb.BorderSizePixel = 0
	thumb.Image = "rbxasset://textures/ui/GuiImagePlaceholder.png"
	thumb.ImageTransparency = 0.4
	thumb.ScaleType = Enum.ScaleType.Fit
	thumb.Parent = row
	corner(thumb, 4)
	g.thumb = thumb

	local title = g.name
	if g.fileName ~= "" then
		title = g.fileName
	end
	local nameLabel = makeLabel(row, title, 10, true)
	nameLabel.Position = UDim2.new(0, 46, 0, 0)
	nameLabel.Size = UDim2.new(0.38, -46, 1, 0)
	nameLabel.TextTruncate = Enum.TextTruncate.AtEnd
	g.nameLabel = nameLabel

	local idBox = Instance.new("TextBox")
	idBox.Position = UDim2.new(0.38, 0, 0.5, -10)
	idBox.Size = UDim2.new(0.34, -4, 0, 20)
	idBox.PlaceholderText = "Asset ID"
	idBox.PlaceholderColor3 = Color3.fromRGB(110, 120, 145)
	idBox.ClearTextOnFocus = false
	idBox.Font = Enum.Font.Code
	idBox.TextSize = 10
	idBox.BackgroundColor3 = COL.panel
	idBox.TextColor3 = Color3.new(1, 1, 1)
	idBox.Text = ""
	idBox.BorderSizePixel = 0
	idBox.Parent = row
	corner(idBox, 4)
	g.idBox = idBox

	local selectBtn = makeButton(row, "Seç", COL.blue, 10)
	selectBtn.Position = UDim2.new(0.72, 0, 0.5, -10)
	selectBtn.Size = UDim2.new(0.18, -2, 0, 20)

	local clearBtn = makeButton(row, "×", Color3.fromRGB(96, 56, 68), 12)
	clearBtn.Position = UDim2.new(0.9, 0, 0.5, -10)
	clearBtn.Size = UDim2.new(0.1, -4, 0, 20)

	row.MouseButton1Click:Connect(function()
		if pendingAsset then
			local id = pendingAsset
			pendingAsset = nil
			assignGroup(g, id, false)
			return
		end
		if activeGroup == g then
			setActiveGroup(nil)
		else
			setActiveGroup(g)
		end
	end)

	idBox.FocusLost:Connect(function()
		local id = assetIdFromImageString(idBox.Text)
		if id then
			assignGroup(g, id, false)
		else
			idBox.Text = g.assigned or ""
		end
	end)

	selectBtn.MouseButton1Click:Connect(function()
		local live = {}
		for _, inst in ipairs(g.instances) do
			if inst.Parent then
				table.insert(live, inst)
			end
		end
		if #live > 0 then
			Selection:Set(live)
		end
	end)

	clearBtn.MouseButton1Click:Connect(function()
		for _, inst in ipairs(g.instances) do
			if inst.Parent then
				pcall(function()
					inst.Image = ""
				end)
			end
		end
		g.assigned = nil
		refreshGroupVisual(g)
		updateListHeader()
		updateGalleryMarks()
	end)
end

-- Motor her ImageLabel/ImageButton için çağırır. Aynı dosya adı = aynı grup.
local function registerImage(inst, elementName, expectedFileName)
	local key
	if expectedFileName and expectedFileName ~= "" then
		key = "f:" .. string.lower(tostring(expectedFileName))
	else
		rowCounter += 1
		key = "u:" .. rowCounter -- dosya adı yoksa asla birleştirme
	end

	local g = groupByKey[key]
	if not g then
		g = {
			key = key,
			fileName = expectedFileName or "",
			name = elementName,
			instances = {},
			assigned = nil,
			order = #groups + 1,
		}
		groupByKey[key] = g
		table.insert(groups, g)
		createGroupRow(g)
		refreshGroupVisual(g)
	end
	table.insert(g.instances, inst)
	if #g.instances > 1 then
		g.nameLabel.Text = string.format("%s  ×%d", (g.fileName ~= "" and g.fileName or g.name), #g.instances)
	end
end

-- ============ OTOMATİK EŞLEŞTİRME & DECAL TEMİZLEME ============

local function runAutoMatch(silent)
	if #galleryImages == 0 then
		refreshGallery()
	end
	if #galleryImages == 0 then
		if not silent then
			setStatus("Galeride görsel yok! Önce Asset Manager'da görsellere Sağ Tık > Insert de.\n" .. lastDiag, COL.warn)
		end
		return 0
	end
	if #groups == 0 then
		if not silent then
			setStatus("Önce JSON'dan UI oluştur; sonra eşleştir.", COL.warn)
		end
		return 0
	end

	local matches, unmatched = computeMatches(groups, galleryImages)
	for _, m in ipairs(matches) do
		assignGroup(m.group, m.assetId, false)
	end

	-- aktif satırı ilk boş satıra al
	for _, g in ipairs(groups) do
		if not g.assigned or g.assigned == "" then
			setActiveGroup(g)
			break
		end
	end

	local msg = string.format("✨ Otomatik eşleştirme: %d yeni satır atandı. Toplam %d / %d dolu.", #matches, (function()
		local n = 0
		for _, g in ipairs(groups) do
			if g.assigned and g.assigned ~= "" then
				n += 1
			end
		end
		return n
	end)(), #groups)
	if #unmatched > 0 then
		local shown = {}
		for i = 1, math.min(4, #unmatched) do
			table.insert(shown, unmatched[i])
		end
		msg ..= "\nEşleşmeyen: " .. table.concat(shown, ", ") .. (#unmatched > 4 and (" …+" .. (#unmatched - 4)) or "")
	end
	setStatus(msg, #unmatched == 0 and COL.ok or COL.warn)
	return #matches
end

autoMatchBtn.MouseButton1Click:Connect(function()
	runAutoMatch(false)
end)

refreshGalleryBtn.MouseButton1Click:Connect(function()
	refreshGallery()
	setStatus("Galeri yenilendi. " .. lastDiag, COL.muted)
end)

filterBtn.MouseButton1Click:Connect(function()
	hideUsed = not hideUsed
	setFilterVisual(hideUsed)
	updateGalleryMarks()
end)

local cleanArmed = false
cleanDecalsBtn.MouseButton1Click:Connect(function()
	if not cleanArmed then
		cleanArmed = true
		cleanDecalsBtn.Text = "Emin misin?"
		task.delay(3, function()
			cleanArmed = false
			cleanDecalsBtn.Text = DECAL_LABEL
		end)
		return
	end
	cleanArmed = false
	cleanDecalsBtn.Text = DECAL_LABEL
	ChangeHistoryService:SetWaypoint("Before EasyImport Decal Cleanup")
	local removed = 0
	local function wipe(container)
		for _, d in ipairs(container:GetChildren()) do
			if d:IsA("Decal") or d:IsA("Texture") then
				d:Destroy()
				removed += 1
			end
		end
	end
	wipe(Workspace)
	wipe(ServerStorage)
	for _, root in ipairs({ ServerStorage, Workspace, ReplicatedStorage }) do
		for _, folderName in ipairs({ "Loaded", "FigBloxUI_Images" }) do
			local f = root:FindFirstChild(folderName)
			if f then
				for _, d in ipairs(f:GetDescendants()) do
					if d:IsA("Decal") or d:IsA("Texture") then
						d:Destroy()
						removed += 1
					end
				end
			end
		end
	end
	ChangeHistoryService:SetWaypoint("After EasyImport Decal Cleanup")
	refreshGallery()
	setStatus("🧹 " .. removed .. " geçici Decal temizlendi. (Atanan Asset ID'ler ImageLabel'larda kalır.)", COL.muted)
end)

-- ============ WISPFREE HİYERARŞİK UI KURUCU MOTORU ============

local FONT_FAMILY_MAP = {
	{ keys = { "inter", "gotham", "sf pro", "plus jakarta", "manrope", "dm sans", "geist" }, family = "GothamSSm.json" },
	{ keys = { "montserrat", "poppins", "outfit", "urbanist", "lexend", "syne" }, family = "Montserrat.json" },
	{ keys = { "builder", "rubik", "figtree", "work sans" }, family = "BuilderSans.json" },
	{ keys = { "roboto mono", "jetbrains", "fira code", "consolas", "courier", "space mono" }, family = "RobotoMono.json" },
	{ keys = { "roboto", "open sans", "lato", "noto" }, family = "Roboto.json" },
	{ keys = { "ubuntu", "quicksand" }, family = "Ubuntu.json" },
	{ keys = { "nunito", "mulish" }, family = "Nunito.json" },
	{ keys = { "fredoka", "baloo" }, family = "FredokaOne.json" },
	{ keys = { "bangers", "komika" }, family = "Bangers.json" },
	{ keys = { "luckiest", "titan one" }, family = "LuckiestGuy.json" },
	{ keys = { "oswald", "bebas", "anton", "impact", "teko" }, family = "Oswald.json" },
	{ keys = { "merriweather", "lora", "serif", "georgia", "times", "playfair" }, family = "Merriweather.json" },
	{ keys = { "comic", "patrick" }, family = "ComicNeueAngular.json" },
	{ keys = { "press start", "pixel", "arcade", "vt323" }, family = "PressStart2P.json" },
	{ keys = { "orbitron", "michroma", "rajdhani" }, family = "Michroma.json" },
	{ keys = { "titillium", "exo", "kanit" }, family = "TitilliumWeb.json" },
}

local function mapFontFamilyAsset(fam)
	local f = string.lower(tostring(fam or ""))
	for _, row in ipairs(FONT_FAMILY_MAP) do
		for _, k in ipairs(row.keys) do
			if string.find(f, k, 1, true) then
				return "rbxasset://fonts/families/" .. row.family
			end
		end
	end
	return "rbxasset://fonts/families/GothamSSm.json"
end

local function mapFontWeightEnum(w)
	local n = tonumber(w) or 400
	if n <= 150 then return Enum.FontWeight.Thin end
	if n <= 250 then return Enum.FontWeight.ExtraLight end
	if n <= 350 then return Enum.FontWeight.Light end
	if n <= 450 then return Enum.FontWeight.Regular end
	if n <= 550 then return Enum.FontWeight.Medium end
	if n <= 650 then return Enum.FontWeight.SemiBold end
	if n <= 750 then return Enum.FontWeight.Bold end
	if n <= 850 then return Enum.FontWeight.ExtraBold end
	return Enum.FontWeight.Heavy
end

-- v4: Etiketler TAM KELİME olarak eşleşir ("Top_buttons" artık TextButton yapmaz) ve yalnızca
-- bilinen ekler adtan silinir ("Player_Name" -> "Player_Name" kalır; eski sürüm "Player" yapıyordu).
local KNOWN_SUFFIX = {}
for _, w in ipairs({ "scrollingframe", "viewportframe", "canvasgroup", "textbutton", "textlabel", "imagebutton", "imagelabel",
	"scrollx", "scrolly", "scroll", "textbox", "button", "btn", "canvas", "aspect", "hover", "clicked", "input", "image",
	"frame", "lock", "ignore", "exclude", "uilist", "uigrid", "gray", "vpf", "box", "keep", "nodim", "viewport",
	"videoframe", "video" }) do
	KNOWN_SUFFIX[w] = true
end

-- v5: Katman adından düğme algısı (görseller için). "Play_Button", "PlayButton", "play btn", "Buton" ...
-- Tam kelime eşleşir; "Top_buttons" gibi çoğul/başka kelimeler düğme sayılmaz.
local BUTTON_WORDS = { button = true, btn = true, buton = true }
local function nameSaysButton(rawName)
	local spaced = string.gsub(tostring(rawName or ""), "(%l)(%u)", "%1 %2") -- camelCase ayır
	for w in string.gmatch(string.lower(spaced), "%a+") do
		if BUTTON_WORDS[w] then
			return true
		end
		-- "playbutton" / "closebtn" gibi birleşik yazımlar
		if #w > 6 and string.sub(w, -6) == "button" then return true end
		if #w > 4 and string.sub(w, -3) == "btn" then return true end
	end
	return false
end

local function parseLayerTags(rawName)
	local name = tostring(rawName or "Layer")
	local lower = string.lower(name)
	local tok = {}
	for w in string.gmatch(lower, "_(%a+)") do tok[w] = true end
	-- Sınıf adı adın İÇİNDE doğrudan geçiyorsa (alt çizgi olsa da olmasa da) o sınıf seçilir.
	-- Türkçe İ/ı harfleri i sayılır. Kısa kelimeler (button, image, frame...) için hâlâ "_" gerekir.
	local flat = string.gsub(lower, "\xC4\xB0", "i")
	flat = string.gsub(flat, "\xC4\xB1", "i")
	flat = string.gsub(flat, "i\xCC\x87", "i")
	for _, w in ipairs({ "imagebutton", "imagelabel", "textbutton", "textlabel", "textbox", "scrollingframe", "viewportframe", "canvasgroup", "videoframe" }) do
		if string.find(flat, w, 1, true) then tok[w] = true end
	end
	local tags = {
		isButton = (tok.button or tok.btn) and true or false,
		isViewport = (tok.viewport or tok.viewportframe or tok.vpf) and true or false,
		forceClass = (tok.imagebutton and "ImageButton")
			or (tok.imagelabel and "ImageLabel")
			or (tok.textbutton and "TextButton")
			or (tok.textlabel and "TextLabel")
			or (tok.scrollingframe and "ScrollingFrame")
			or (tok.canvasgroup and "CanvasGroup")
			or (tok.viewportframe and "ViewportFrame")
			or (tok.textbox and "TextBox")
			or (tok.videoframe and "VideoFrame")
			or (tok.frame and "Frame")
			or nil,
		isNameButton = nameSaysButton(name),
		isVideo = (tok.video or tok.videoframe) and true or false,
		isScroll = (tok.scroll or tok.scrollx or tok.scrolly or tok.scrollingframe) and true or false,
		isScrollX = tok.scrollx and true or false,
		isScrollY = tok.scrolly and true or false,
		isCanvas = (tok.canvas or tok.canvasgroup) and true or false,
		isAspect = tok.aspect and true or false,
		isHover = tok.hover and true or false,
		isClicked = tok.clicked and true or false,
		isInput = (tok.input or tok.textbox or tok.box) and true or false,
	}
	local clean = string.gsub(name, "^#", "")
	clean = string.gsub(clean, "^img:", "")
	clean = string.gsub(clean, "_(%a+)", function(w)
		if KNOWN_SUFFIX[string.lower(w)] then return "" end
		return nil
	end)
	clean = string.gsub(clean, "^%s*(.-)%s*$", "%1")
	if clean == "" then clean = "Element" end
	return clean, tags
end

local Assist = {}
Assist.VERSION = "ei-assist-1"
Assist.CONF_MIN = 0.70          -- PLAN §M1: bu eşiğin altında kural motoru kazanır
Assist.LEARN_MIN = 2            -- öğrenilmiş düzeltme en az bu gözlemle devreye girer
Assist.KEY = "EasyImportLearn"  -- Studio ayar anahtarı: nokta ve ters bölü YASAK (sessiz başarısızlık)

-- Ad/etiketten gelen sinyaller: biri bile varsa kararı kural motoru verir (v9 yolu).
local ASSIST_SIGNAL_TAGS = {
	"forceClass", "isButton", "isNameButton", "isInput", "isScroll", "isScrollX", "isScrollY",
	"isVideo", "isViewport", "isCanvas", "isHover", "isClicked",
}

function Assist.modulesOk()
	return type(EIRaw) == "table" and type(EIStyle) == "table" and type(EIFeaturesSpec) == "table"
		and type(EIFeatures) == "table" and type(EIModel) == "table" and type(EILearn) == "table"
end

-- Tek kaynak kapı: asistan bu dökümanda çalışacak mı? (`ei` yan kanalı + gömülü modüller)
function Assist.activeFor(doc)
	return Assist.modulesOk() and Assist.docHasEi(doc)
end

function Assist.disabledReason()
	if Assist.modulesOk() then return nil end
	return "asistan modülleri gömülü değil — eklentiyi build_rbxmx.py ile paketleyin"
end

function Assist.signals(tags)
	local out = {}
	for i = 1, #ASSIST_SIGNAL_TAGS do
		local k = ASSIST_SIGNAL_TAGS[i]
		if tags and tags[k] then out[#out + 1] = k end
	end
	return out
end

-- Kural motorunun forceClass kapısıyla AYNI uyumluluk mantığı (bkz. decideClass).
function Assist.compatible(item, cls)
	if type(cls) ~= "string" or cls == "" then return false end
	local textOk = (cls == "TextLabel" or cls == "TextButton" or cls == "TextBox")
	local imgOk = (cls == "ImageLabel" or cls == "ImageButton")
	local frameOk = (cls == "ScrollingFrame" or cls == "CanvasGroup" or cls == "ViewportFrame"
		or cls == "VideoFrame" or cls == "Frame")
	local kind = item and item.kind
	if kind == "text" then return textOk end
	if item and item.image then return imgOk end
	return frameOk
end

function Assist.newSession(learnState)
	return {
		ok = Assist.modulesOk(),
		style = "belirsiz", conf = 0, scores = {},
		byNode = {}, nRaw = 0, gui = {},
		-- Öğrenme durumu: verilmezse boş durum (EILearn gömülü değilse nil — o zaman ok=false).
		learn = learnState or (EILearn and EILearn.newState() or nil),
		cache = {}, dirty = false,
		stats = { predicts = 0, model = 0, learned = 0, rejected = 0, corrections = 0 },
	}
end

-- `ei` yan kanalı var mı? v9 kapısı: yoksa asistan hiç hesaplama yapmaz.
function Assist.docHasEi(doc)
	local found = false
	local function rec(item)
		if found or type(item) ~= "table" then return end
		if type(item.ei) == "table" then found = true return end
		local kids = item.children or {}
		for i = 1, #kids do
			rec(kids[i])
			if found then return end
		end
	end
	if doc then rec(doc.root) end
	return found
end

-- Döküman hazırlığı: RAW + stil + düğüm↔RAW eşlemesi (kimlikle; ızgara dönüşümü sırayı bozsa da doğru).
function Assist.prepare(session, doc)
	if not session.ok then return session end
	local raw = EIRaw.extract(doc)
	local nodes = raw.nodes or {}
	session.nRaw = #nodes
	local k = 0
	local function walk(item)
		if type(item) ~= "table" then return end
		k = k + 1
		session.byNode[item] = nodes[k]
		local kids = item.children or {}
		for i = 1, #kids do walk(kids[i]) end
	end
	if doc then walk(doc.root) end
	local ok, st = pcall(function()
		return EIStyle.decide(EIStyle.signals(raw.gui or {}, nodes))
	end)
	if ok and type(st) == "table" then
		session.style = st.style or "belirsiz"
		session.conf = st.conf or 0
		session.scores = st.scores or {}
	end
	session.gui = raw.gui or {}
	return session
end

-- Düğüm bilgisi (tembel): RAW → 379 özellik → model tahmini. Düğüm başına bir kez.
function Assist.nodeInfo(session, item)
	local info = session.cache[item]
	if info then return info end
	local raw = session.byNode[item]
	info = { raw = raw, pred = nil, fx = "-" }
	if type(raw) == "table" then
		if type(raw.fxKind) == "string" and raw.fxKind ~= "" then info.fx = raw.fxKind end
		local okv, vec = pcall(function() return EIFeatures.compute(EIFeaturesSpec, raw) end)
		if okv and type(vec) == "table" then
			local okp, pred = pcall(function() return EIModel.predict(vec) end)
			if okp and type(pred) == "table" then info.pred = pred end
		end
	end
	session.cache[item] = info
	return info
end

-- Öğrenme bağlamı: stil | (asistanın düşündüğü) sınıf | rol | fx. Rol §A7'de gelecek.
function Assist.ctx(session, cls, fx)
	return EILearn.ctxKey(session.style, cls or "-", "-", fx or "-")
end

-- Karar: nil → kural motoru (v9). Aksi hâlde sınıf önerisi + kaynağı.
function Assist.decide(session, item, tags)
	if not session.ok then return nil end
	if #Assist.signals(tags) > 0 then return nil end          -- ad/etiket sinyali → kural motoru
	local info = Assist.nodeInfo(session, item)
	if not info.pred then return nil end
	session.stats.predicts = session.stats.predicts + 1
	local ctx = Assist.ctx(session, info.pred.cls, info.fx)
	local pref = EILearn.preferredClass(session.learn, ctx)
	if pref and (pref.n or 0) >= Assist.LEARN_MIN and Assist.compatible(item, pref.cls) then
		session.stats.learned = session.stats.learned + 1
		return { cls = pref.cls, source = "ogrenme", conf = pref.n, top3 = info.pred.top3, ctx = ctx }
	end
	if (info.pred.conf or 0) >= Assist.CONF_MIN and Assist.compatible(item, info.pred.cls) then
		session.stats.model = session.stats.model + 1
		return { cls = info.pred.cls, source = "model", conf = info.pred.conf, top3 = info.pred.top3, ctx = ctx }
	end
	session.stats.rejected = session.stats.rejected + 1
	return nil
end

-- Kullanıcı açık sınıf etiketi yazdıysa (`_ImageButton`) ve asistan farklı düşündüyse bu bir
-- DÜZELTMEdir → cihazda sayılır. Soru sorulmaz, panel açılmaz (KARARLAR §2).
function Assist.noteCorrection(session, item, tags)
	if not session.ok or not (tags and tags.forceClass) then return false end
	local info = Assist.nodeInfo(session, item)
	if not info.pred or info.pred.cls == tags.forceClass then return false end
	if not Assist.compatible(item, tags.forceClass) then return false end
	EILearn.recordClass(session.learn, Assist.ctx(session, info.pred.cls, info.fx), tags.forceClass, 1)
	session.stats.corrections = session.stats.corrections + 1
	session.dirty = true
	return true
end

-- Stil önseli: animasyon/dekor önerileri bu etikete göre seçilir (§A7/A8). Sınıf önseli zaten
-- modelin içinde (J grubu bayrakları → STYLE_LOG_BIAS).
function Assist.statusLine(session)
	if not session.ok then return "asistan: " .. tostring(Assist.disabledReason()) end
	local s = session.stats
	return string.format("asistan: stil %s (%d%%) · model %d · öğrenilmiş %d · kural %d · düzeltme %d",
		tostring(session.style), math.floor((session.conf or 0) * 100 + 0.5),
		s.model, s.learned, s.rejected, s.corrections)
end
-- <<ASSIST_END>>

-- <<ASSIST_END>>

-- Yerel öğrenme durumu (cihazda; sunucu YOK). Anahtar: Assist.KEY (nokta/ters bölü içermez).
local LEARN_STATE = nil
if Assist.modulesOk() then
	local okGet, saved = pcall(function() return Plugin:GetSetting(Assist.KEY) end)
	if okGet and type(saved) == "string" and #saved > 0 then
		local okDec, st = pcall(function() return EILearn.decode(saved) end)
		if okDec and type(st) == "table" then LEARN_STATE = st end
	end
	if not LEARN_STATE then LEARN_STATE = EILearn.newState() end
end


-- ============ RENKLER & KÜÇÜK YARDIMCILAR ============

local LAST_ASSIST_LINE = nil

-- Öğrenme durumu eklenti ayarında kalıcıdır (SetSetting; bu sürümde Figma'dan bağımsız). Bozuk veri sessizce yok sayılır.
local function loadLearnState()
	local ok, text = pcall(function() return Plugin:GetSetting(Assist.KEY) end)
	if ok and type(text) == "string" and text ~= "" and type(EILearn) == "table" then
		local okD, st = pcall(function() return EILearn.decode(text) end)
		if okD and type(st) == "table" then return st end
	end
	return nil
end

local function saveLearnState(learn)
	if type(EILearn) ~= "table" or type(learn) ~= "table" then return false end
	local ok = pcall(function()
		local fitted = EILearn.fit(learn, 400, 60000)
		Plugin:SetSetting(Assist.KEY, EILearn.encode(fitted or learn))
	end)
	return ok
end

-- v4: Duyarlı ölçek betiği (ScreenGui içine LocalScript olarak yazılır). Ayarlar ScreenGui Attribute'larından okunur.
local RESPONSIVE_SCRIPT = [==[
-- EasyImport: Duyarlı ölçek. UI'nin UIScale değerini ekran boyutuna göre günceller.
-- ScreenGui Attribute'ları: DesignWidth, DesignHeight, ScaleMode (Fit | Fill | Width | Height), MinScale, MaxScale
local gui = script.Parent
local root = gui:FindFirstChildWhichIsA("GuiObject")
local us = root and root:FindFirstChildOfClass("UIScale")
if not us then
	return
end

local function update()
	local vp = gui.AbsoluteSize
	if vp.X <= 0 or vp.Y <= 0 then
		return
	end
	local dw = math.max(1, tonumber(gui:GetAttribute("DesignWidth")) or 1920)
	local dh = math.max(1, tonumber(gui:GetAttribute("DesignHeight")) or 1080)
	local mode = gui:GetAttribute("ScaleMode")
	local minS = tonumber(gui:GetAttribute("MinScale")) or 0.2
	local maxS = tonumber(gui:GetAttribute("MaxScale")) or 3
	if maxS < minS then
		maxS = minS
	end
	local sx, sy = vp.X / dw, vp.Y / dh
	local s
	if mode == "Fill" then
		s = math.max(sx, sy)
	elseif mode == "Width" then
		s = sx
	elseif mode == "Height" then
		s = sy
	else
		s = math.min(sx, sy)
	end
	us.Scale = math.clamp(s, minS, maxS)
end

gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(update)
for _, a in ipairs({ "DesignWidth", "DesignHeight", "ScaleMode", "MinScale", "MaxScale" }) do
	gui:GetAttributeChangedSignal(a):Connect(update)
end
update()
task.defer(update)
]==]

local function buildEasyImportHierarchy(doc, opts)
	local guiName = "EasyImport_" .. tostring(doc.name or "UI"):gsub("[^%w_]", "_")
	clearImageList()
	LAST_ASSIST_LINE = nil

	-- A4b: asistan oturumu. `ei` yoksa (v9 export'ları) hazırlık bile yapılmaz → çıktı değişmez.
	LEARN_STATE = LEARN_STATE or loadLearnState()
	local assist = Assist.newSession(LEARN_STATE)
	local assistOn = Assist.activeFor(doc)
	local assistOverrides = 0
	if assistOn then
		local okPrep, prepErr = pcall(Assist.prepare, assist, doc)
		if not okPrep then
			assistOn = false
			warn("[EasyImport] Asistan hazırlığı başarısız, v9 kararlarına dönüldü: " .. tostring(prepErr))
		end
	end

	-- v4: ScreenGui en sonda StarterGui'ye taşınır; oluşturma yarıda hata verirse önceki UI silinmez.
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = guiName
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	local totalCreated = 0
	local textTotal, textStyled = 0, 0
	local SHADOW_BLUR_SCALE = 1 -- UIShadow bulanıklığı Figma'dan sert/yumuşak gelirse değiştir
	-- false: yazı gölgesi kopya TextLabel ile çizilir (yazının/X'in arkasında koyu kutu çıkmaz).
	-- true: native UIShadow (Text modu) denenir; bazı Studio sürümlerinde yazı kutusunu gölgeli dikdörtgen çizebilir.
	local NATIVE_TEXT_SHADOW = false
	local OFFSET_MODE = true -- true: Figma pikselleri birebir (tam piksel). false: ekrana göre ölçekli. (Panelde anahtar yok; Studio ayarından okunur)
	local MATCH_FIGMA_WRAP = true -- true: Figma'daki satır kırılmasını (dar kutuda alt satıra sarma) taklit et
	local FIT_TEXT_WIDTH = true -- true: otomatik genişlikli tek satır yazılarda Figma'daki yazı genişliğine uyacak TextSize'ı hesapla
	local wrapCache = {}
	local TEXT_STROKE_SCALE = 1 -- yazı stroke'u çok kalın/ince geliyorsa bunu değiştir (örn. 0.7 veya 1.5)
	local imageOrderCounter = 0
	local frameCounter = 0
	local animIdCounter = 0
	local animBindings = {} -- v11: JSON'daki düğüm animasyon seçimleri (item.anim)
	local actionList, panelList, groupList = {}, {}, {} -- v12: etkileşim, paneller, sekmeler
	local animMode = type(doc.anims) == "table" -- JSON animasyon tanımları varsa tüm öğelere EI_Id (seçim grupları için)
	opts = opts or {}
	OFFSET_MODE = opts.offset ~= false
	local OPT_RESPONSIVE = opts.responsive ~= false
	local OPT_ASPECT = opts.aspect ~= false
	local OPT_SCALEMODE = opts.scaleMode or "Fit"
	local rootInst = nil

	-- v9: UIShadow oluşturucu. textMode=true: gölge kutudan değil yazı glif'lerinden düşer (ApplyShadowMode.Text)
	local function makeUIShadow(sd, parentInst, opv, textMode, zi)
		local sdc = sd.color or { r = 0, g = 0, b = 0 }
		return pcall(function()
			local us = Instance.new("UIShadow")
			if textMode then us.Mode = Enum.ApplyShadowMode.Text end
			us.Color = Color3.fromRGB(sdc.r or 0, sdc.g or 0, sdc.b or 0)
			us.Transparency = math.clamp(1 - (tonumber(sd.opacity) or 1) * opv, 0, 1)
			us.BlurRadius = UDim.new(0, (tonumber(sd.blur) or 0) * SHADOW_BLUR_SCALE)
			us.Offset = UDim2.fromOffset(tonumber(sd.x) or 0, tonumber(sd.y) or 0)
			us.Spread = UDim2.fromOffset(tonumber(sd.spread) or 0, tonumber(sd.spread) or 0)
			pcall(function() us.ZIndex = zi or 1 end)
			us.Parent = parentInst
		end)
	end

	-- v6: kaydırma alanındaki eş boyutlu kartları UIGridLayout slotlarına çevir (dokümandaki "slot Frame" mantığı)
	local function detectGrid(item)
		local kids = item.children
		if type(kids) ~= "table" or #kids < 4 then return kids, nil end
		local counts, cands = {}, {}
		for _, c in ipairs(kids) do
			local cw0, ch0 = tonumber(c.w) or 0, tonumber(c.h) or 0
			if c.kind ~= "text" and cw0 > 8 and ch0 > 8 then
				local key = tostring(math.floor((cw0 + 1.5) / 3)) .. "x" .. tostring(math.floor((ch0 + 1.5) / 3))
				counts[key] = (counts[key] or 0) + 1
				table.insert(cands, { c = c, key = key })
			end
		end
		local bestKey, bestN = nil, 0
		for k, n in pairs(counts) do
			if n > bestN then bestKey, bestN = k, n end
		end
		if bestN < 4 then return kids, nil end
		local cards, isCard = {}, {}
		for _, e in ipairs(cands) do
			if e.key == bestKey then table.insert(cards, e.c); isCard[e.c] = true end
		end
		table.sort(cards, function(a, b) return (tonumber(a.y) or 0) < (tonumber(b.y) or 0) end)
		local cw, chh = tonumber(cards[1].w) or 1, tonumber(cards[1].h) or 1
		local rows, cur, curY = {}, nil, 0
		for _, c in ipairs(cards) do
			local cy = tonumber(c.y) or 0
			if not cur or cy - curY > chh * 0.5 then cur = {}; table.insert(rows, cur); curY = cy end
			table.insert(cur, c)
		end
		local ordered, gx, gy, cols = {}, {}, {}, 0
		local minX, minY = math.huge, math.huge
		for ri, r in ipairs(rows) do
			table.sort(r, function(a, b) return (tonumber(a.x) or 0) < (tonumber(b.x) or 0) end)
			cols = math.max(cols, #r)
			for i, c in ipairs(r) do
				table.insert(ordered, c)
				minX = math.min(minX, tonumber(c.x) or 0)
				minY = math.min(minY, tonumber(c.y) or 0)
				if r[i + 1] then table.insert(gx, (tonumber(r[i + 1].x) or 0) - ((tonumber(c.x) or 0) + (tonumber(c.w) or 0))) end
			end
			if rows[ri + 1] then
				table.insert(gy, (tonumber(rows[ri + 1][1].y) or 0) - ((tonumber(r[1].y) or 0) + (tonumber(r[1].h) or 0)))
			end
		end
		local function median(t)
			if #t == 0 then return 0 end
			table.sort(t)
			return t[math.ceil(#t / 2)]
		end
		-- kart olmayanlar bir karta ait değilse ızgara kurulamaz
		local slotOf = {}
		local slots = {}
		for _, c in ipairs(ordered) do
			local sl = { name = c.name, kind = "frame", x = 0, y = 0, w = cw, h = chh, rot = 0, opacity = 1, fills = {}, children = {} }
			slotOf[c] = sl
			table.insert(slots, sl)
		end
		for _, c in ipairs(kids) do
			if isCard[c] then
				local cc = table.clone(c)
				cc.x, cc.y = 0, 0
				table.insert(slotOf[c].children, cc)
			else
				local ox = (tonumber(c.x) or 0) + (tonumber(c.w) or 0) / 2
				local oy = (tonumber(c.y) or 0) + (tonumber(c.h) or 0) / 2
				local host = nil
				for _, cd in ipairs(ordered) do
					local cx, cy = tonumber(cd.x) or 0, tonumber(cd.y) or 0
					if ox >= cx and ox <= cx + (tonumber(cd.w) or 0) and oy >= cy and oy <= cy + (tonumber(cd.h) or 0) then host = cd; break end
				end
				if not host then return kids, nil end
				local cc = table.clone(c)
				cc.x = (tonumber(c.x) or 0) - (tonumber(host.x) or 0)
				cc.y = (tonumber(c.y) or 0) - (tonumber(host.y) or 0)
				table.insert(slotOf[host].children, cc)
			end
		end
		return slots, { cw = cw, ch = chh, gx = median(gx), gy = median(gy), cols = cols, padL = minX, padT = minY }
	end

	local function buildNode(item, parent, pW, pH, isRoot, zIdx, inGrid)
		local cleanName, tags = parseLayerTags(item.name)

		local cls = "Frame"
		if item.kind == "text" then
			if tags.isInput then cls = "TextBox"
			elseif tags.isButton then cls = "TextButton"
			else cls = "TextLabel" end
		elseif item.image then
			-- v5: _button etiketi VEYA katman adında "button/btn/buton" kelimesi -> ImageButton
			cls = (tags.isButton or tags.isNameButton) and "ImageButton" or "ImageLabel"
		elseif tags.isScroll then
			cls = "ScrollingFrame"
		elseif item.scroll and item.scroll ~= "NONE" then
			cls = "ScrollingFrame"
		elseif tags.isVideo then
			cls = "VideoFrame"
		elseif tags.isViewport then
			cls = "ViewportFrame"
		elseif tags.isCanvas then
			cls = "CanvasGroup"
		elseif tags.isButton then
			cls = "TextButton"
		end

		-- v5: açık sınıf etiketi (_ImageLabel, _TextButton ...) yalnızca uyumluysa uygulanır
		if tags.forceClass then
			local fc = tags.forceClass
			local textOk = (fc == "TextLabel" or fc == "TextButton" or fc == "TextBox")
			local imgOk = (fc == "ImageLabel" or fc == "ImageButton")
			local frameOk = (fc == "ScrollingFrame" or fc == "CanvasGroup" or fc == "ViewportFrame" or fc == "VideoFrame" or fc == "Frame")
			if (item.kind == "text" and textOk) or (item.image and imgOk) or (not item.image and item.kind ~= "text" and frameOk) then
				cls = fc
			end
		end

		-- A4b: asistan yalnızca `ei` varken ve ad/etiket sinyali yokken konuşur (v9 aksi hâlde aynen).
		if assistOn then
			local a = Assist.decide(assist, item, tags)
			if a then
				cls = a.cls
				assistOverrides = assistOverrides + 1
			end
			Assist.noteCorrection(assist, item, tags)
		end

		local inst = Instance.new(cls)
		inst.Name = cleanName
		-- A6-A8 / v11: animasyon bağlaması için kimlik. Asistan modunda veya düğümde animasyon seçimi varsa.
		local interactive = type(item.action) == "table" or item.panel or item.tabgroup
		if assistOn or animMode or type(item.anim) == "table" or interactive then
			animIdCounter = animIdCounter + 1
			inst:SetAttribute("EI_Id", animIdCounter)
			-- v12: etkileşim kayıtları
			if type(item.action) == "table" then
				table.insert(actionList, { id = animIdCounter, kind = item.action.kind, targetName = item.action.target })
			end
			if item.panel then
				table.insert(panelList, animIdCounter)
				inst.Visible = false -- paneller başlangıçta kapalı; _open / _tab ile açılır
			end
			if item.tabgroup then table.insert(groupList, animIdCounter) end
			if type(item.anim) == "table" then
				local a = item.anim
				-- v13: Figma panelinden yüklenen efekt resimleri → gizli şablon ImageLabel'ları (adı = dosya adı).
				-- Resimler ZIP'te aynı klasörde; "İsimden eşleştir" ImageLabel'lara ID'yi bu adla atar.
				if type(item.anim.fxImages) == "table" then
					for _, nm in ipairs(item.anim.fxImages) do
						if type(nm) == "string" and nm ~= "" then
							local tplImg = Instance.new("ImageLabel")
							tplImg.Name = nm
							tplImg.BackgroundTransparency = 1
							tplImg.BorderSizePixel = 0
							tplImg.Size = UDim2.fromOffset(64, 64)
							tplImg.Visible = false
							tplImg:SetAttribute("EI_FxTpl", true)
							tplImg.Parent = inst
						end
					end
				end
				-- seçim grubu: üst öğenin EI_Id'si (kalıcı _select kardeşleri birlikte yönetir)
				local pid = (parent and parent:GetAttribute("EI_Id")) or 0
				table.insert(animBindings, { id = animIdCounter, show = a.show, hover = a.hover, press = a.press,
					loop = a.loop, selA = a.selA, sel = a.selA and pid or nil, delay = a.delay, fx = a.fx, params = a.params })
			end
		end
		inst.BorderSizePixel = 0
		inst.ZIndex = zIdx
		inst.LayoutOrder = zIdx
		if tags.isHover or tags.isClicked then
			inst.Visible = false
		end
		if item.clips then
			inst.ClipsDescendants = true
		end

		local w = tonumber(item.w) or 100
		local h = tonumber(item.h) or 100
		local x = tonumber(item.x) or 0
		local y = tonumber(item.y) or 0

		if isRoot then
			inst.AnchorPoint = Vector2.new(0.5, 0.5)
			inst.Position = UDim2.fromScale(0.5, 0.5)
			if OFFSET_MODE then
				inst.Size = UDim2.fromOffset(math.floor(w + 0.5), math.floor(h + 0.5))
			else
				inst.Size = UDim2.fromScale(0.88, 0.88)
			end
		elseif OFFSET_MODE then
			if item.kind == "text" then
				inst.Position = UDim2.fromOffset(math.floor(x + 0.5), math.floor(y + 0.5))
				inst.Size = UDim2.fromOffset(w, h)
			else
				inst.Position = UDim2.fromOffset(math.floor(x + 0.5), math.floor(y + 0.5))
				inst.Size = UDim2.fromOffset(math.floor(w + 0.5), math.floor(h + 0.5))
			end
		elseif pW > 0 and pH > 0 then
			inst.Position = UDim2.fromScale(x / pW, y / pH)
			inst.Size = UDim2.fromScale(w / pW, h / pH)
		else
			inst.Position = UDim2.fromOffset(x, y)
			inst.Size = UDim2.fromOffset(w, h)
		end

		if item.rot and math.abs(tonumber(item.rot) or 0) > 0.01 then
			inst.Rotation = tonumber(item.rot)
		end

		local fills = type(item.fills) == "table" and item.fills or {}
		local solidFill, gradFill = nil, nil
		for _, f in ipairs(fills) do
			if f.type == "SOLID" then solidFill = f
			elseif f.type == "GRADIENT" or f.type == "GRADIENT_OTHER" then gradFill = f end
		end

		local nodeOp = tonumber(item.opacity) or 1

		if item.kind ~= "text" and (solidFill or gradFill) then
			if solidFill and not gradFill then
				local sc = solidFill.color or { r = 255, g = 255, b = 255 }
				local fOp = (tonumber(solidFill.opacity) or 1) * nodeOp
				inst.BackgroundColor3 = Color3.fromRGB(sc.r or 255, sc.g or 255, sc.b or 255)
				inst.BackgroundTransparency = math.clamp(1 - fOp, 0, 1)
			elseif gradFill then
				local gOp = (tonumber(gradFill.opacity) or 1) * nodeOp
				inst.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
				inst.BackgroundTransparency = math.clamp(1 - gOp, 0, 1)
			end
		else
			inst.BackgroundTransparency = 1
		end

		if cls == "ScrollingFrame" then
			inst.AutomaticCanvasSize = Enum.AutomaticSize.Y
			inst.CanvasSize = UDim2.new(0, 0, 0, 0)
			inst.ScrollBarThickness = 6
			local sdir = tostring(item.scroll or "")
			if tags.isScrollX then sdir = "HORIZONTAL" elseif tags.isScrollY then sdir = "VERTICAL" end
			if sdir == "HORIZONTAL" or sdir == "HORIZONTAL_SCROLLING" then
				inst.ScrollingDirection = Enum.ScrollingDirection.X
				inst.AutomaticCanvasSize = Enum.AutomaticSize.X
			elseif sdir == "BOTH" or sdir == "BOTH_SCROLLING" then
				inst.ScrollingDirection = Enum.ScrollingDirection.XY
				inst.AutomaticCanvasSize = Enum.AutomaticSize.XY
			else
				inst.ScrollingDirection = Enum.ScrollingDirection.Y
			end
		end

		-- ImageLabel / ImageButton -> Görsel Gereken Elemanlar listesine ekle!
		if cls == "ImageLabel" or cls == "ImageButton" then
			inst.Image = ""
			inst.ScaleType = Enum.ScaleType.Stretch
			if nodeOp < 1 then
				inst.ImageTransparency = math.clamp(1 - nodeOp, 0, 1)
			end
			imageOrderCounter += 1
			registerImage(inst, cleanName, item.image or "")
		end

		-- TextLabel / TextButton / TextBox
		if item.kind == "text" and item.text then
			local t = item.text
			textTotal += 1
			if t.stroke or t.gradient or t.segments or t.shadow then textStyled += 1 end
			local tc = t.color or { r = 255, g = 255, b = 255 }
			local fontAsset = mapFontFamilyAsset(t.fontFamily)
			local weightEnum = mapFontWeightEnum(t.fontWeight)
			local styleEnum = t.italic and Enum.FontStyle.Italic or Enum.FontStyle.Normal

			local function escRich(s)
				s = tostring(s or "")
				s = string.gsub(s, "&", "&amp;")
				s = string.gsub(s, "<", "&lt;")
				s = string.gsub(s, ">", "&gt;")
				return s
			end
			local function caseFix(s)
				s = tostring(s or "")
				if t.textCase == "UPPER" then return string.upper(s)
				elseif t.textCase == "LOWER" then return string.lower(s) end
				return s
			end
			inst.RichText = true
			local richStr
			if type(t.segments) == "table" and #t.segments > 1 then
				local parts = {}
				local baseSize = tonumber(t.fontSize) or 16
				for _, sg in ipairs(t.segments) do
					local c = sg.color or tc
					local attrs = string.format('color="#%02x%02x%02x"', math.floor(c.r or 255), math.floor(c.g or 255), math.floor(c.b or 255))
					if tonumber(sg.fontSize) and math.abs(tonumber(sg.fontSize) - baseSize) > 0.5 then
						attrs = attrs .. ' size="' .. tostring(math.floor(tonumber(sg.fontSize) + 0.5)) .. '"'
					end
					if tonumber(sg.fontWeight) and tonumber(sg.fontWeight) ~= tonumber(t.fontWeight) then
						attrs = attrs .. ' weight="' .. tostring(math.floor(tonumber(sg.fontWeight))) .. '"'
					end
					if sg.fontFamily and sg.fontFamily ~= t.fontFamily then
						attrs = attrs .. ' family="' .. tostring(mapFontFamilyAsset(sg.fontFamily)) .. '"'
					end
					table.insert(parts, "<font " .. attrs .. ">" .. escRich(caseFix(sg.text)) .. "</font>")
				end
				richStr = table.concat(parts)
			else
				richStr = escRich(caseFix(t.characters))
			end
			if t.decoration == "UNDERLINE" then richStr = "<u>" .. richStr .. "</u>"
			elseif t.decoration == "STRIKETHROUGH" then richStr = "<s>" .. richStr .. "</s>" end
			inst.Text = richStr
			pcall(function()
				inst.FontFace = Font.new(fontAsset, weightEnum, styleEnum)
			end)
			inst.TextSize = tonumber(t.fontSize) or 16
			if t.fit then inst.TextScaled = true end -- v12: _fit

			-- v8: Roblox bazı fontları farklı genişlikte çizer; otomatik genişlikli tek satır yazıda Figma genişliğine uyacak boyutu bul
			if FIT_TEXT_WIDTH and t.autoW and not t.segments and (tonumber(t.lines) or 1) <= 1 and (tonumber(item.w) or 0) > 8 then
				pcall(function()
					local TS = game:GetService("TextService")
					local gp = Instance.new("GetTextBoundsParams")
					gp.Text = caseFix(t.characters)
					gp.Font = inst.FontFace
					gp.Size = inst.TextSize
					gp.RichText = false
					gp.Width = 100000
					local bw = TS:GetTextBoundsAsync(gp).X
					if bw > 0 then
						local ratio = (tonumber(item.w) or bw) / bw
						if ratio > 0.8 and ratio < 1.25 and math.abs(ratio - 1) > 0.02 then
							inst.TextSize = math.clamp(math.floor(inst.TextSize * ratio + 0.5), 1, 100)
						end
					end
				end)
			end
			inst.TextColor3 = Color3.fromRGB(tc.r or 255, tc.g or 255, tc.b or 255)
			inst.TextTransparency = math.clamp(1 - nodeOp, 0, 1)
			inst.TextWrapped = (t.wrap ~= false)
			inst.RichText = true

			-- v3: yazı gradient'i (UIGradient yazıyı boyar, bu yüzden metin rengi beyaz)
			if type(t.gradient) == "table" then
				inst.TextColor3 = Color3.new(1, 1, 1)
				gradFill = t.gradient
			end

			if t.align == "CENTER" then inst.TextXAlignment = Enum.TextXAlignment.Center
			elseif t.align == "RIGHT" then inst.TextXAlignment = Enum.TextXAlignment.Right
			else inst.TextXAlignment = Enum.TextXAlignment.Left end

			if t.vAlign == "CENTER" then inst.TextYAlignment = Enum.TextYAlignment.Center
			elseif t.vAlign == "BOTTOM" then inst.TextYAlignment = Enum.TextYAlignment.Bottom
			else inst.TextYAlignment = Enum.TextYAlignment.Top end

			-- v8: tek satırlık kutuda yazıyı dikey ortala (Figma ve Roblox satır yüksekliği farklı olsa da glifler aynı yerde durur)
			if (tonumber(t.lines) or 1) <= 1 and (tonumber(item.h) or 0) <= (tonumber(t.fontSize) or 16) * 1.8 then
				inst.TextYAlignment = Enum.TextYAlignment.Center
			end

			-- v7: Figma'da metin dar kutuda alt satıra sarılıyorsa Roblox'ta da aynı satır sayısına gelene kadar genişliği daralt
			if MATCH_FIGMA_WRAP and (tonumber(t.lines) or 1) > 1 and cls ~= "TextBox" and w > 8 then
				local plain = caseFix(t.characters)
				local wkey = plain .. "|" .. tostring(t.fontFamily) .. "|" .. tostring(t.fontWeight) .. "|" .. tostring(inst.TextSize) .. "|" .. tostring(math.floor(w)) .. "|" .. tostring(t.lines)
				local bestW = wrapCache[wkey]
				if bestW == nil then
					bestW = false
					pcall(function()
						local TS = game:GetService("TextService")
						local gp = Instance.new("GetTextBoundsParams")
						gp.Text = plain
						gp.Font = inst.FontFace
						gp.Size = inst.TextSize
						gp.RichText = false
						gp.Width = 100000
						local one = TS:GetTextBoundsAsync(gp).Y
						if one > 0 then
							for wpx = math.floor(w), 8, -2 do
								gp.Width = wpx
								local ln = math.floor(TS:GetTextBoundsAsync(gp).Y / one + 0.5)
								if ln >= t.lines then
									bestW = wpx
									break
								end
							end
						end
					end)
					wrapCache[wkey] = bestW
				end
				if bestW and bestW < w - 1 then
					local ratio = bestW / w
					local sz0 = inst.Size
					inst.Size = UDim2.new(sz0.X.Scale * ratio, sz0.X.Offset * ratio, sz0.Y.Scale, sz0.Y.Offset)
					local fAl = (t.align == "CENTER" and 0.5) or (t.align == "RIGHT" and 1) or 0
					if fAl > 0 then
						local ps0 = inst.Position
						local shift = (w - bestW) * fAl
						if OFFSET_MODE or not (pW > 0 and pH > 0) then
							inst.Position = UDim2.new(ps0.X.Scale, ps0.X.Offset + shift, ps0.Y.Scale, ps0.Y.Offset)
						else
							inst.Position = UDim2.new(ps0.X.Scale + shift / pW, ps0.X.Offset, ps0.Y.Scale, ps0.Y.Offset)
						end
					end
				end
			end
		elseif cls == "TextButton" then
			inst.Text = ""
			inst.AutoButtonColor = false
		end

		-- UICorner
		if item.radius == "full" then
			local cr = Instance.new("UICorner")
			cr.CornerRadius = UDim.new(1, 0)
			cr.Parent = inst
		elseif type(item.radius) == "number" and item.radius > 0 then
			local cr = Instance.new("UICorner")
			cr.CornerRadius = UDim.new(0, math.round(item.radius))
			cr.Parent = inst
		end

		-- v6/v9: native UIShadow (katmanın kendi dolu kutusunun gölgeleri; Figma'daki tüm drop shadow'lar)
		if item.kind ~= "text" and not item.image and (solidFill or gradFill) and item.shadowTag then
			local sl = item.shadows
			if type(sl) ~= "table" and type(item.shadow) == "table" then sl = { item.shadow } end
			if type(sl) == "table" then
				for zi, sd in ipairs(sl) do
					makeUIShadow(sd, inst, nodeOp, false, zi)
				end
			end
		end

		-- v5: gradient yardımcısı
		local function buildGradient(g)
			if type(g) ~= "table" or type(g.stops) ~= "table" or #g.stops < 2 then return nil end
			local stops = table.clone(g.stops)
			table.sort(stops, function(a, b) return (tonumber(a.pos) or 0) < (tonumber(b.pos) or 0) end)
			if (tonumber(stops[1].pos) or 0) > 0 then
				table.insert(stops, 1, { pos = 0, color = stops[1].color, opacity = stops[1].opacity })
			end
			if (tonumber(stops[#stops].pos) or 1) < 1 then
				local last = stops[#stops]
				table.insert(stops, { pos = 1, color = last.color, opacity = last.opacity })
			end
			local cK, tK = {}, {}
			for _, s in ipairs(stops) do
				local pos = math.clamp(tonumber(s.pos) or 0, 0, 1)
				local c = s.color or { r = 255, g = 255, b = 255 }
				table.insert(cK, ColorSequenceKeypoint.new(pos, Color3.fromRGB(c.r or 255, c.g or 255, c.b or 255)))
				table.insert(tK, NumberSequenceKeypoint.new(pos, math.clamp(1 - (tonumber(s.opacity) or 1), 0, 1)))
			end
			local gr = Instance.new("UIGradient")
			gr.Rotation = tonumber(g.angle) or 0
			pcall(function()
				gr.Color = ColorSequence.new(cK)
				gr.Transparency = NumberSequence.new(tK)
			end)
			return gr
		end

		-- v5: birden fazla / gradient stroke (frame, görsel dışı) - Figma sırasıyla, her biri ayrı UIStroke
		local strokesDone = false
		if item.kind ~= "text" and type(item.strokes) == "table" and #item.strokes > 0 and (tonumber(item.strokeWeight) or 0) > 0 then
			strokesDone = true
			local posEnum = Enum.BorderStrokePosition.Inner
			if item.strokeAlign == "OUTSIDE" then posEnum = Enum.BorderStrokePosition.Outer
			elseif item.strokeAlign == "CENTER" then posEnum = Enum.BorderStrokePosition.Center end
			for si, sp in ipairs(item.strokes) do
				local us = Instance.new("UIStroke")
				pcall(function() us.ZIndex = si end) -- Roblox: aynı ZIndex'te çizim sırası belirsiz; Figma sırasını koru
				us.Thickness = tonumber(item.strokeWeight) or 1
				us.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
				pcall(function() us.BorderStrokePosition = posEnum end)
				us.Transparency = math.clamp(1 - (tonumber(sp.opacity) or 1) * nodeOp, 0, 1)
				if sp.type == "GRADIENT" then
					us.Color = Color3.new(1, 1, 1)
					local ug = buildGradient(sp)
					if ug then ug.Parent = us end
				else
					local c = sp.color or { r = 255, g = 255, b = 255 }
					us.Color = Color3.fromRGB(c.r or 255, c.g or 255, c.b or 255)
				end
				us.Parent = inst
			end
		end

		-- UIStroke (eski tek stroke)
		if (not strokesDone) and item.stroke and (tonumber(item.stroke.weight) or 0) > 0 then
			local st = item.stroke
			local stc = st.color or { r = 255, g = 255, b = 255 }
			local stOp = (tonumber(st.opacity) or 1) * nodeOp
			local stroke = Instance.new("UIStroke")
			stroke.Color = Color3.fromRGB(stc.r or 255, stc.g or 255, stc.b or 255)
			stroke.Thickness = tonumber(st.weight) or 1
			stroke.Transparency = math.clamp(1 - stOp, 0, 1)
			stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
			stroke.Parent = inst
		end

		-- v3: yazı stroke'u (Contextual = glif kenarına çizer)
		if item.kind == "text" and item.text and type(item.text.stroke) == "table" and (tonumber(item.text.stroke.weight) or 0) > 0 then
			local ts = item.text.stroke
			local tsc = ts.color or { r = 0, g = 0, b = 0 }
			local w0 = tonumber(ts.weight) or 1
			local thick = w0
			if ts.align == "CENTER" or ts.align == "INSIDE" then thick = w0 * 0.5 end
			thick = math.max(0.5, thick * TEXT_STROKE_SCALE)
			local tstroke = Instance.new("UIStroke")
			tstroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
			tstroke.Color = Color3.fromRGB(tsc.r or 0, tsc.g or 0, tsc.b or 0)
			if type(ts.gradient) == "table" then
				tstroke.Color = Color3.new(1, 1, 1)
				local tg = buildGradient(ts.gradient)
				if tg then tg.Parent = tstroke end
			end
			tstroke.Thickness = thick
			tstroke.Transparency = math.clamp(1 - (tonumber(ts.opacity) or 1) * nodeOp, 0, 1)
			pcall(function() tstroke.LineJoinMode = Enum.LineJoinMode.Round end)
			tstroke.Parent = inst
		end

		-- UIGradient
		if gradFill and type(gradFill.stops) == "table" and #gradFill.stops >= 2 then
			local stops = table.clone(gradFill.stops)
			table.sort(stops, function(a, b) return (tonumber(a.pos) or 0) < (tonumber(b.pos) or 0) end)
			if (tonumber(stops[1].pos) or 0) > 0 then
				table.insert(stops, 1, { pos = 0, color = stops[1].color, opacity = stops[1].opacity })
			end
			if (tonumber(stops[#stops].pos) or 1) < 1 then
				local last = stops[#stops]
				table.insert(stops, { pos = 1, color = last.color, opacity = last.opacity })
			end

			local cKps, tKps = {}, {}
			for _, s in ipairs(stops) do
				local pos = math.clamp(tonumber(s.pos) or 0, 0, 1)
				local sc = s.color or { r = 255, g = 255, b = 255 }
				local sOp = tonumber(s.opacity) or 1
				table.insert(cKps, ColorSequenceKeypoint.new(pos, Color3.fromRGB(sc.r or 255, sc.g or 255, sc.b or 255)))
				table.insert(tKps, NumberSequenceKeypoint.new(pos, math.clamp(1 - sOp, 0, 1)))
			end

			local gr = Instance.new("UIGradient")
			gr.Rotation = tonumber(gradFill.angle) or 0
			pcall(function()
				gr.Color = ColorSequence.new(cKps)
				gr.Transparency = NumberSequence.new(tKps)
			end)
			gr.Parent = inst
		end

		-- v9: yazı gölgesi. Önce native UIShadow (ApplyShadowMode.Text: blur'lu gölge dahil). Studio sürümü desteklemezse kopya TextLabel'a düş.
		if item.kind == "text" and item.text and (cls == "TextLabel" or cls == "TextButton")
			and (type(item.text.shadows) == "table" or type(item.text.shadow) == "table") then
			local tsl = item.text.shadows
			if type(tsl) ~= "table" then tsl = { item.text.shadow } end
			local nativeOk = false
			if NATIVE_TEXT_SHADOW then
				for zi, sd in ipairs(tsl) do
					if makeUIShadow(sd, inst, nodeOp, true, zi) then nativeOk = true end
				end
			end
			if not nativeOk then
				local shd = tsl[1]
				local sc2 = shd.color or { r = 0, g = 0, b = 0 }
				local copy
				if cls == "TextLabel" then
					copy = inst:Clone()
					for _, ch in ipairs(copy:GetChildren()) do
						if ch:IsA("UIGradient") or ch:IsA("UIStroke") or ch:IsA("UIShadow") then ch:Destroy() end
					end
				else
					-- TextButton: tıklanabilir kopya olmasın; aynı görünümlü TextLabel üret
					copy = Instance.new("TextLabel")
					for _, prop in ipairs({ "AnchorPoint", "Position", "Size", "Rotation", "ZIndex", "FontFace", "TextSize", "TextWrapped",
						"TextXAlignment", "TextYAlignment", "LineHeight", "TextScaled", "TextTruncate" }) do
						pcall(function() copy[prop] = inst[prop] end)
					end
					copy.BackgroundTransparency = 1
					copy.BorderSizePixel = 0
				end
				copy.Name = cleanName .. "_Shadow"
				copy.BackgroundTransparency = 1
				copy.RichText = false
				copy.Text = tostring(item.text.characters or "")
				if item.text.textCase == "UPPER" then copy.Text = string.upper(copy.Text)
				elseif item.text.textCase == "LOWER" then copy.Text = string.lower(copy.Text) end
				copy.TextColor3 = Color3.fromRGB(sc2.r or 0, sc2.g or 0, sc2.b or 0)
				copy.TextTransparency = math.clamp(1 - (tonumber(shd.opacity) or 1) * nodeOp, 0, 1)
				local p0 = copy.Position
				copy.Position = UDim2.new(p0.X.Scale, p0.X.Offset + (tonumber(shd.x) or 0), p0.Y.Scale, p0.Y.Offset + (tonumber(shd.y) or 0))
				copy.Parent = parent
			end
		end

		-- v4: UIAspectRatioConstraint. Kök + _aspect etiketliler + (seçenek açıksa) görseller en-boy oranını korur.
		-- Oran, gerçekte kullanılan (yuvarlanmış) piksel boyutundan hesaplanır; böylece 1 px kayma/bulanıklık olmaz.
		local wantAspect = tags.isAspect or (isRoot and not OFFSET_MODE)
		if OPT_ASPECT and (isRoot or ((cls == "ImageLabel" or cls == "ImageButton") and not inGrid)) then
			wantAspect = true
		end
		if wantAspect then
			local rw, rh = w, h
			if OFFSET_MODE then
				rw, rh = math.floor(w + 0.5), math.floor(h + 0.5)
			end
			if rw >= 1 and rh >= 1 then
				local ar = Instance.new("UIAspectRatioConstraint")
				ar.Name = "EI_AspectRatio"
				ar.AspectRatio = rw / rh
				ar.AspectType = Enum.AspectType.FitWithinMaxSize
				ar.DominantAxis = Enum.DominantAxis.Width
				ar.Parent = inst
			end
		end

		-- v4: Responsive ölçek. Kök sabit piksel boyutunda kalır; UIScale ekrana göre büyütüp küçültür.
		if isRoot and OFFSET_MODE and OPT_RESPONSIVE then
			local us = Instance.new("UIScale")
			us.Name = "EI_ResponsiveScale"
			us.Scale = 1
			us.Parent = inst
		end

		inst.Parent = parent
		if isRoot then rootInst = inst end
		totalCreated += 1
		if cls == "Frame" then frameCounter += 1 end

		local kids = item.children
		local gridInfo = nil
		local createdGrid = false

		-- v6: Auto Layout -> UIListLayout / UIGridLayout (+ UIPadding)
		if type(item.layout) == "table" and type(kids) == "table" and #kids > 0 and not item.nolist then
			local lo = item.layout
			local horizontal = (lo.mode == "HORIZONTAL")
			if (tonumber(lo.pl) or 0) > 0 or (tonumber(lo.pr) or 0) > 0 or (tonumber(lo.pt) or 0) > 0 or (tonumber(lo.pb) or 0) > 0 then
				local up = Instance.new("UIPadding")
				up.PaddingLeft = UDim.new(0, tonumber(lo.pl) or 0)
				up.PaddingRight = UDim.new(0, tonumber(lo.pr) or 0)
				up.PaddingTop = UDim.new(0, tonumber(lo.pt) or 0)
				up.PaddingBottom = UDim.new(0, tonumber(lo.pb) or 0)
				up.Parent = inst
			end
			local c1 = kids[1]
			local sameSize = false
			if lo.wrap and #kids > 1 then
				sameSize = true
				for _, c in ipairs(kids) do
					if math.abs((tonumber(c.w) or 0) - (tonumber(c1.w) or 0)) > 1.5 or math.abs((tonumber(c.h) or 0) - (tonumber(c1.h) or 0)) > 1.5 then
						sameSize = false
						break
					end
				end
			end
			local function alignH(v) if v == "CENTER" then return Enum.HorizontalAlignment.Center elseif v == "MAX" then return Enum.HorizontalAlignment.Right end return Enum.HorizontalAlignment.Left end
			local function alignV(v) if v == "CENTER" then return Enum.VerticalAlignment.Center elseif v == "MAX" then return Enum.VerticalAlignment.Bottom end return Enum.VerticalAlignment.Top end
			if lo.wrap and sameSize then
				local gl = Instance.new("UIGridLayout")
				gl.CellSize = UDim2.fromOffset(tonumber(c1.w) or 50, tonumber(c1.h) or 50)
				local g1, g2 = tonumber(lo.gap) or 0, tonumber(lo.wrapGap) or 0
				gl.CellPadding = horizontal and UDim2.fromOffset(g1, g2) or UDim2.fromOffset(g2, g1)
				gl.FillDirection = horizontal and Enum.FillDirection.Horizontal or Enum.FillDirection.Vertical
				gl.SortOrder = Enum.SortOrder.LayoutOrder
				gl.Parent = inst
				createdGrid = true
			else
				local ll = Instance.new("UIListLayout")
				ll.FillDirection = horizontal and Enum.FillDirection.Horizontal or Enum.FillDirection.Vertical
				ll.SortOrder = Enum.SortOrder.LayoutOrder
				ll.Padding = UDim.new(0, tonumber(lo.gap) or 0)
				if horizontal then
					ll.HorizontalAlignment = alignH(lo.primary)
					ll.VerticalAlignment = alignV(lo.counter)
				else
					ll.VerticalAlignment = alignV(lo.primary)
					ll.HorizontalAlignment = alignH(lo.counter)
				end
				if lo.wrap then pcall(function() ll.Wraps = true end) end
				if lo.primary == "SPACE_BETWEEN" then
					pcall(function()
						if horizontal then ll.HorizontalFlex = Enum.UIFlexAlignment.SpaceBetween
						else ll.VerticalFlex = Enum.UIFlexAlignment.SpaceBetween end
					end)
				end
				ll.Parent = inst
			end
		elseif cls == "ScrollingFrame" and type(kids) == "table" and not item.nolist then
			-- v6: Auto Layout'u olmayan kaydırma alanında eş boyutlu kartlar -> UIGridLayout
			kids, gridInfo = detectGrid(item)
			if gridInfo then
				local up = Instance.new("UIPadding")
				up.PaddingLeft = UDim.new(0, math.max(0, gridInfo.padL))
				up.PaddingTop = UDim.new(0, math.max(0, gridInfo.padT))
				up.Parent = inst
				local gl = Instance.new("UIGridLayout")
				gl.CellSize = UDim2.fromOffset(gridInfo.cw, gridInfo.ch)
				gl.CellPadding = UDim2.fromOffset(gridInfo.gx, gridInfo.gy)
				gl.FillDirection = Enum.FillDirection.Horizontal
				gl.SortOrder = Enum.SortOrder.LayoutOrder
				gl.StartCorner = Enum.StartCorner.TopLeft
				pcall(function() gl.FillDirectionMaxCells = gridInfo.cols end)
				gl.Parent = inst
				createdGrid = true
			end
		end

		if type(kids) == "table" then
			for idx, ch in ipairs(kids) do
				buildNode(ch, inst, w, h, false, idx, createdGrid)
			end
		end
	end

	buildNode(doc.root, screenGui, tonumber(doc.width) or 800, tonumber(doc.height) or 600, true, 1)

	-- v4: responsive ölçek betiği + ayarlar
	local respInfo = nil
	if OFFSET_MODE and OPT_RESPONSIVE and rootInst then
		local dW = math.max(1, math.floor((tonumber(doc.width) or 800) + 0.5))
		local dH = math.max(1, math.floor((tonumber(doc.height) or 600) + 0.5))
		screenGui:SetAttribute("DesignWidth", dW)
		screenGui:SetAttribute("DesignHeight", dH)
		screenGui:SetAttribute("ScaleMode", OPT_SCALEMODE)
		screenGui:SetAttribute("MinScale", 0.2)
		screenGui:SetAttribute("MaxScale", 3)
		local okS = pcall(function()
			local sc = Instance.new("LocalScript")
			sc.Name = "EI_ResponsiveScaler"
			sc.Source = RESPONSIVE_SCRIPT
			sc.Parent = screenGui
		end)
		respInfo = { w = dW, h = dH, mode = OPT_SCALEMODE, scriptOk = okS }
	end

	-- A6-A8: animasyon LocalScript'i (yalnız asistan modu + modül gömülüyse). Hata v9'u etkilemez.
	local animInfo = nil
	-- v11: JSON'daki animasyon tanımları (doc.anims) + düğüm seçimleri → LocalScript. Kütüphaneye bağlı değil;
	--      asistan modu kapalıyken bile çalışır (animasyon kullanıcının açık seçimidir).
	local runtimeNeeded = (#animBindings > 0 or #actionList > 0 or #panelList > 0)
	if runtimeNeeded and EIAnim then
		-- Eylem hedeflerini (panel adı) EI_Id'ye çevir; bulunamazsa hedef boş kalır (eylem sessizce etkisiz).
		local actionTargets = {}
		for _, a in ipairs(actionList) do
			local tid = nil
			if type(a.targetName) == "string" and a.targetName ~= "" then
				for _, d in ipairs(screenGui:GetDescendants()) do
					if d.Name == a.targetName then
						tid = d:GetAttribute("EI_Id")
						if not tid then
							animIdCounter = animIdCounter + 1
							tid = animIdCounter
							d:SetAttribute("EI_Id", tid)
						end
						break
					end
				end
			end
			table.insert(actionTargets, { id = a.id, kind = a.kind, target = tid })
		end
		local okS, errS = pcall(function()
			local animScript = Instance.new("LocalScript")
			animScript.Name = "EI_Animator"
			animScript.Source = EIAnim.buildSourceSpec(animBindings, doc.anims or {}, {
				actions = actionTargets, panels = panelList, groups = groupList })
			animScript.Parent = screenGui
			local fxCount = 0
			for _, b in ipairs(animBindings) do if b.fx then fxCount = fxCount + 1 end end
			animInfo = { elements = #animBindings, bindings = #animBindings, actions = #actionList, panels = #panelList, fx = fxCount }
		end)
		if not okS then
			warn("[EasyImport] Animasyon betiği üretilemedi: " .. tostring(errS))
		end
	elseif assistOn and EIAnim then
		local okA, errA = pcall(function()
			local elements = {}
			for _, d in ipairs(screenGui:GetDescendants()) do
				local id = d:GetAttribute("EI_Id")
				if id then
					local depth, p = 0, d
					while p and p ~= screenGui do
						depth = depth + 1
						p = p.Parent
					end
					local pp = d.Parent
					local pid = (pp and pp:GetAttribute("EI_Id")) or 0
					table.insert(elements, { id = id, name = d.Name, cls = d.ClassName, depth = depth, parent = pid })
				end
			end
			local plan = EIAnim.decideBindings(elements, assist.style or "belirsiz", assist.learn)
			local animScript = Instance.new("LocalScript")
			animScript.Name = "EI_Animator"
			animScript.Source = EIAnim.buildSource(plan)
			animScript.Parent = screenGui
			animInfo = { elements = #elements, bindings = #plan }
		end)
		if not okA then
			warn("[EasyImport] Animasyon üretimi atlandı: " .. tostring(errA))
		end
	end

	-- Sesler (hover + tıklama): her GuiButton için. ID'ler EIAnim içinde sabit; animasyondan bağımsız.
	if EIAnim then
		local hasButton = false
		for _, d in ipairs(screenGui:GetDescendants()) do
			if d:IsA("GuiButton") then
				hasButton = true
				break
			end
		end
		if hasButton then
			pcall(function()
				local soundScript = Instance.new("LocalScript")
				soundScript.Name = "EI_Sesler"
				soundScript.Source = EIAnim.buildSoundSource()
				soundScript.Parent = screenGui
			end)
		end
	end

	-- v4: başarıyla oluştu -> eski kopyayı sil, yenisini StarterGui'ye koy
	local existing = StarterGui:FindFirstChild(guiName)
	if existing then
		existing:Destroy()
	end
	screenGui.Parent = StarterGui
	Selection:Set({ screenGui })
	if assistOn then
		if assist.dirty then
			saveLearnState(assist.learn)
			assist.dirty = false
		end
		local line = Assist.statusLine(assist)
		if animInfo then
			line = line .. string.format(" · animasyon %d bağlama", animInfo.bindings)
			line = line .. string.format(" · etkileşim %d (panel %d) · efekt %d", animInfo.actions, animInfo.panels, animInfo.fx)
		end
		LAST_ASSIST_LINE = line
	end
	if textTotal > 0 then
		if (tonumber(doc.version) or 0) < 4 then
			warn("[EasyImport] Bu JSON ESKI Figma eklentisiyle alinmis (version " .. tostring(doc.version) .. "). Yazi stroke/gradient/cok renk bilgisi yok. Figma eklentisini guncelleyip JSON'u yeniden al.")
		else
			print("[EasyImport] " .. textTotal .. " yazidan " .. textStyled .. " tanesinde stroke/gradient/cok renk bilgisi var.")
		end
	end
	return totalCreated, imageOrderCounter, guiName, frameCounter, respInfo
end

-- ============ BUTON OLAYLARI ============

buildButton.MouseButton1Click:Connect(function()
	local raw = jsonBox.Text
	if not raw or #raw < 5 then
		setStatus("⚠️ Lütfen önce Figma EasyImport eklentisinden kopyaladığın JSON'u yapıştır!", COL.bad)
		return
	end

	local ok, decoded = pcall(function()
		return HttpService:JSONDecode(raw)
	end)

	if not ok or typeof(decoded) ~= "table" or not decoded.root then
		setStatus("⚠️ Geçersiz JSON! Figma EasyImport eklentisinden aldığın JSON'u tam kopyala.", COL.bad)
		return
	end

	-- Eski/ham JSON'larda da gereksiz sarmalayıcı frame'leri ayıkla
	local simplifyStats = { flattened = 0, empty = 0 }
	local assistActive = Assist.activeFor(decoded)
	simplifyTree(decoded.root, simplifyStats, assistActive)

	ChangeHistoryService:SetWaypoint("Before EasyImport Build")
	local built, a, b, c, d, e = pcall(buildEasyImportHierarchy, decoded, {
		responsive = OPT.responsive,
		offset = OPT.offset,
		aspect = OPT.aspect,
		scaleMode = OPT.scaleMode,
	})
	ChangeHistoryService:SetWaypoint("After EasyImport Build")
	if not built then
		clearImageList()
		setStatus("⚠️ Oluşturma hatası (önceki UI korundu): " .. tostring(a), COL.bad)
		return
	end
	local createdCount, _imgCount, guiName, frameCount, respInfo = a, b, c, d, e

	-- Yeni taramayla galeriyi tazele ve otomatik eşleştir
	refreshGallery()
	local matched = runAutoMatch(true)

	local filled, uses = 0, 0
	for _, g in ipairs(groups) do
		uses += #g.instances
		if g.assigned and g.assigned ~= "" then
			filled += 1
		end
	end

	local msg = string.format(
		"✓ %d nesne (%d frame) — %s\n🖼 %d benzersiz görsel (%d kullanım) · otomatik eşleşen: %d · dolu: %d/%d",
		createdCount, frameCount or 0, tostring(guiName), #groups, uses, matched, filled, #groups
	)
	if simplifyStats.flattened + simplifyStats.empty > 0 then
		msg ..= string.format("\n🧹 Sadeleşen frame: %d · silinen boş: %d", simplifyStats.flattened, simplifyStats.empty)
	end
	if LAST_ASSIST_LINE then
		msg ..= "\n🤖 " .. LAST_ASSIST_LINE
	end
	if respInfo then
		msg ..= string.format("\n📐 Responsive: %d×%d tasarım · mod: %s%s", respInfo.w, respInfo.h, SCALE_MODE_TR[respInfo.mode] or respInfo.mode,
			respInfo.scriptOk and "" or " · ⚠️ betik yazılamadı (UIScale 1'de kaldı)")
	end
	setStatus(msg, (#groups == 0 or filled == #groups) and COL.ok or COL.warn)
end)

-- ============ CANLI DURUM & GALERİ TARAMA DÖNGÜLERİ ============

-- Elle değiştirilen Image özelliklerini listeye yansıt
task.spawn(function()
	while true do
		task.wait(1)
		if widget.Enabled and #groups > 0 then
			local changed = false
			for _, g in ipairs(groups) do
				local live = nil
				for _, inst in ipairs(g.instances) do
					if inst.Parent then
						live = inst
						break
					end
				end
				if live then
					local id = assetIdFromImageString(live.Image)
					if id ~= g.assigned then
						g.assigned = id
						refreshGroupVisual(g)
						changed = true
					end
				end
			end
			if changed then
				updateListHeader()
				updateGalleryMarks()
			end
		end
	end
end)

-- Güvenlik ağı: Texture sonradan atanan Insert'ler ve olay kaçıran durumlar için 5 sn'de bir
task.spawn(function()
	while true do
		task.wait(5)
		if widget.Enabled then
			scheduleRefresh()
		end
	end
end)

refreshGallery()

for _, root in ipairs({ ServerStorage, ReplicatedStorage, Workspace, StarterGui }) do
	root.DescendantAdded:Connect(function(d)
		if isImageHolder(d) then
			scheduleRefresh()
		end
	end)
	root.DescendantRemoving:Connect(function(d)
		if isImageHolder(d) then
			scheduleRefresh()
		end
	end)
end
