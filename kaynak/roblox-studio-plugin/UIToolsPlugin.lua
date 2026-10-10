-- UI Tools — EasyImport paketinin ikinci eklentisi. Görsel dili EasyImport Studio paneliyle aynıdır.
-- Hizala · Taşı · Konum/boyut · Sınıf değiştir · Scale/Offset · Öznitelik/etiket temizle.
-- Her işlem Ctrl+Z ile geri alınır. Mantık UIToolsCore'da (saf Lua); bu dosya Studio bağlantısı ve arayüz.

local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local CollectionService = game:GetService("CollectionService")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local StudioService = game:GetService("StudioService")
local Core = require(script:WaitForChild("UIToolsCore"))

local toolbar = plugin:CreateToolbar("UI Tools")
local toggle = toolbar:CreateButton("UIToolsToggle", "UI Tools panelini aç / kapat", "")
local info = DockWidgetPluginGuiInfo.new(Enum.InitialDockState.Right, false, false, 262, 640, 236, 360)
local widget = plugin:CreateDockWidgetPluginGui("EasyImportUITools", info)
widget.Title = "UI Tools · v30"
toggle.Click:Connect(function() widget.Enabled = not widget.Enabled end)

-- EasyImport Studio paneliyle aynı palet
local COL = {
	bg = Color3.fromRGB(15, 16, 21), card = Color3.fromRGB(21, 22, 29), row = Color3.fromRGB(27, 29, 38),
	field = Color3.fromRGB(14, 15, 20), stroke = Color3.fromRGB(38, 41, 51),
	text = Color3.fromRGB(255, 255, 255), muted = Color3.fromRGB(200, 205, 218),
	ok = Color3.fromRGB(52, 211, 153), warn = Color3.fromRGB(251, 191, 36), bad = Color3.fromRGB(248, 113, 113),
	purple = Color3.fromRGB(185, 164, 255), indigo = Color3.fromRGB(124, 92, 245),
	purpleSoft = Color3.fromRGB(185, 166, 255), danger = Color3.fromRGB(48, 26, 32),
	-- Eflatun (lila-mor): ana düğmeler (Convert, Scale) bu tonu kullanır
	lilac = Color3.fromRGB(198, 156, 255), lilacDeep = Color3.fromRGB(176, 128, 250),
}

-- true yaparsan danger dışındaki TÜM düğmeler eflatun olur (hizala, oklar, ızgara dahil)
local ALL_BUTTONS_LILAC = false

-- Kalıcı ayarlar
local state = {
	target = plugin:GetSetting("UT_target") or "parent",  -- "parent" | "selection"
	grid = tonumber(plugin:GetSetting("UT_grid")) or 1,    -- 0 kapalı; 1, 4, 8 px
}
local GRID_CYCLE = { 1, 4, 8, 0 }
local STEP_MIN, STEP_MAX = 1, 50

-- ---------------------------------------------------------------- yapı yardımcıları
local function make(class, props, parent)
	local o = Instance.new(class)
	for k, v in pairs(props or {}) do o[k] = v end
	if parent then o.Parent = parent end
	return o
end

local function corner(inst, r)
	make("UICorner", { CornerRadius = UDim.new(0, r or 8) }, inst)
end

local function stroke(inst, color)
	make("UIStroke", { Color = color or COL.stroke, Thickness = 1, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, inst)
end

local setStatus -- ileri tanım (konsol kartında atanır)

local order = 0
local function nextOrder() order = order + 1; return order end

local root = make("ScrollingFrame", {
	Name = "UT_Root", Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = COL.bg, BorderSizePixel = 0,
	CanvasSize = UDim2.new(0, 0, 0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y,
	ScrollBarThickness = 4, ScrollBarImageColor3 = COL.purple,
}, widget)
make("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 8) }, root)
make("UIPadding", {
	PaddingTop = UDim.new(0, 12), PaddingBottom = UDim.new(0, 12),
	PaddingLeft = UDim.new(0, 10), PaddingRight = UDim.new(0, 10),
}, root)

local function label(text, name, color, size, parent, bold)
	return make("TextLabel", {
		Name = name or "Label", Text = text, Font = bold and Enum.Font.GothamBold or Enum.Font.GothamMedium,
		TextSize = size or 11, TextColor3 = color or COL.text, BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 16), TextXAlignment = Enum.TextXAlignment.Left,
		LayoutOrder = nextOrder(),
	}, parent or root)
end

local function chip(text, parent, color, bg)
	local c = make("TextLabel", {
		Name = "UT_Chip", Text = text, Font = Enum.Font.Code, TextSize = 9, TextColor3 = color or COL.muted,
		BackgroundColor3 = bg or COL.row, BorderSizePixel = 0, Size = UDim2.new(0, 0, 0, 18),
		AutomaticSize = Enum.AutomaticSize.X, TextXAlignment = Enum.TextXAlignment.Center,
	}, parent)
	make("UIPadding", { PaddingLeft = UDim.new(0, 7), PaddingRight = UDim.new(0, 7) }, c)
	corner(c, 6)
	stroke(c)
	return c
end

-- Bölüm kartı: başlık solda, "01 / ADI" chip'i sağda (EasyImport düzeni)
local function card(title, chipText)
	local box = make("Frame", {
		Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, BackgroundColor3 = COL.card,
		BorderSizePixel = 0, LayoutOrder = nextOrder(),
	}, root)
	corner(box, 10)
	stroke(box)
	make("UIPadding", { PaddingTop = UDim.new(0, 9), PaddingBottom = UDim.new(0, 9), PaddingLeft = UDim.new(0, 10), PaddingRight = UDim.new(0, 10) }, box)
	make("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 6) }, box)
	local head = make("Frame", { Size = UDim2.new(1, 0, 0, 20), BackgroundTransparency = 1, LayoutOrder = 0 }, box)
	make("TextLabel", {
		Text = title, Font = Enum.Font.GothamBold, TextSize = 12, TextColor3 = COL.text,
		BackgroundTransparency = 1, Size = UDim2.new(0.7, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Left,
	}, head)
	if chipText then
		local c = chip(chipText, head)
		c.AnchorPoint = Vector2.new(1, 0.5)
		c.Position = UDim2.new(1, 0, 0.5, 0)
	end
	return box
end

local function row(parent, height)
	local f = make("Frame", { Size = UDim2.new(1, 0, 0, height or 26), BackgroundTransparency = 1, LayoutOrder = nextOrder() }, parent)
	make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 5), SortOrder = Enum.SortOrder.LayoutOrder }, f)
	return f
end

-- style: "normal" | "primary" | "danger"
local function button(name, text, parent, widthScale, onClick, style)
	if ALL_BUTTONS_LILAC and style ~= "danger" then style = "primary" end
	local bg = COL.row
	if style == "primary" then bg = COL.lilac elseif style == "danger" then bg = COL.danger end
	local b = make("TextButton", {
		Name = name, Text = text, Font = Enum.Font.GothamMedium, TextSize = 11,
		TextColor3 = COL.text, BackgroundColor3 = bg, BorderSizePixel = 0, AutoButtonColor = true,
		Size = UDim2.new(widthScale or 1, -5, 1, 0), LayoutOrder = nextOrder(),
	}, parent)
	if style == "primary" then
		-- eflatun zeminde yazı: saf beyaz, kalın, hafif koyu gölge (açık zeminde okunsun)
		b.TextColor3 = Color3.new(1, 1, 1)
		b.Font = Enum.Font.GothamBold
		b.TextStrokeColor3 = Color3.fromRGB(70, 40, 130)
		b.TextStrokeTransparency = 0.55
	end
	corner(b, 7)
	if style ~= "primary" then stroke(b) end
	if style == "primary" then
		make("UIGradient", { Color = ColorSequence.new(COL.lilac, COL.lilacDeep), Rotation = 90 }, b)
	end
	b.MouseButton1Click:Connect(onClick)
	return b
end

local function textbox(name, text, parent, pos, size)
	local t = make("TextBox", {
		Name = name, Text = text, Font = Enum.Font.Code, TextSize = 11, TextColor3 = COL.text,
		PlaceholderColor3 = COL.muted, BackgroundColor3 = COL.field, BorderSizePixel = 0,
		ClearTextOnFocus = false, Position = pos, Size = size,
	}, parent)
	corner(t, 6)
	stroke(t)
	return t
end

-- ---------------------------------------------------------------- başlık & seçim
local head = make("Frame", { Size = UDim2.new(1, 0, 0, 44), BackgroundTransparency = 1, LayoutOrder = nextOrder() }, root)
local logo = make("Frame", { Size = UDim2.new(0, 34, 0, 34), Position = UDim2.new(0, 0, 0, 5), BackgroundColor3 = Color3.fromRGB(35, 29, 68), BorderSizePixel = 0 }, head)
corner(logo, 9)
stroke(logo, Color3.fromRGB(58, 47, 120))
make("TextLabel", { Text = "⇄", Font = Enum.Font.GothamBold, TextSize = 18, TextColor3 = COL.purpleSoft, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, 0) }, logo)
make("TextLabel", {
	Name = "UT_Title", Text = "UI Tools v30", Font = Enum.Font.GothamBold, TextSize = 16, TextColor3 = COL.text,
	BackgroundTransparency = 1, Position = UDim2.new(0, 44, 0, 4), Size = UDim2.new(1, -110, 0, 20),
	TextXAlignment = Enum.TextXAlignment.Left,
}, head)
make("TextLabel", {
	Text = "Hizala · Taşı · Düzenle", Font = Enum.Font.GothamMedium, TextSize = 10, TextColor3 = COL.muted,
	BackgroundTransparency = 1, Position = UDim2.new(0, 44, 0, 24), Size = UDim2.new(1, -110, 0, 14),
	TextXAlignment = Enum.TextXAlignment.Left,
}, head)
local studioTag = chip("STUDIO", head)
studioTag.AnchorPoint = Vector2.new(1, 0.5)
studioTag.Position = UDim2.new(1, 0, 0.5, 0)

local selCard = make("Frame", { Size = UDim2.new(1, 0, 0, 34), BackgroundColor3 = COL.card, BorderSizePixel = 0, LayoutOrder = nextOrder() }, root)
corner(selCard, 10)
stroke(selCard)
local selInfo = make("TextLabel", {
	Name = "UT_SelInfo", Text = "Seçili değil", Font = Enum.Font.GothamMedium, TextSize = 11, TextColor3 = COL.muted,
	BackgroundTransparency = 1, Position = UDim2.new(0, 12, 0, 0), Size = UDim2.new(1, -90, 1, 0),
	TextXAlignment = Enum.TextXAlignment.Left,
}, selCard)
local selChip = chip("YOK", selCard)
selChip.AnchorPoint = Vector2.new(1, 0.5)
selChip.Position = UDim2.new(1, -8, 0.5, 0)

-- ---------------------------------------------------------------- geometri
local function px(u, p) return u.Scale * p + u.Offset end

local function parentSize(o)
	local p = o.Parent
	if p and p:IsA("GuiObject") then return p.AbsoluteSize.X, p.AbsoluteSize.Y end
	local cam = workspace.CurrentCamera
	if cam then return cam.ViewportSize.X, cam.ViewportSize.Y end
	return 0, 0
end

local function rectOf(o, pw, ph)
	local w, h = px(o.Size.X, pw), px(o.Size.Y, ph)
	return {
		x = px(o.Position.X, pw) - o.AnchorPoint.X * w,
		y = px(o.Position.Y, ph) - o.AnchorPoint.Y * h,
		w = w, h = h,
	}
end

local function setTopLeft(o, x, y, pw, ph)
	local w, h = px(o.Size.X, pw), px(o.Size.Y, ph)
	local ax, ay = x + o.AnchorPoint.X * w, y + o.AnchorPoint.Y * h
	local p = o.Position
	o.Position = UDim2.new(p.X.Scale, ax - p.X.Scale * pw, p.Y.Scale, ay - p.Y.Scale * ph)
end

local function setSize(o, w, h, pw, ph)
	local s = o.Size
	o.Size = UDim2.new(s.X.Scale, math.max(0, w) - s.X.Scale * pw, s.Y.Scale, math.max(0, h) - s.Y.Scale * ph)
end

local LAYOUTS = { UIListLayout = true, UIGridLayout = true, UITableLayout = true, UIPageLayout = true }
local function layoutControlled(o)
	local p = o.Parent
	if not p then return false end
	for _, c in ipairs(p:GetChildren()) do
		if LAYOUTS[c.ClassName] then return true end
	end
	return false
end

local function selectedGuis()
	local out = {}
	for _, o in ipairs(Selection:Get()) do
		if o:IsA("GuiObject") then out[#out + 1] = o end
	end
	return out
end

local function selectedAll()
	return Selection:Get()
end

local function positionable()
	local list, skipped = {}, 0
	for _, o in ipairs(selectedGuis()) do
		local pw, ph = parentSize(o)
		if layoutControlled(o) or pw <= 0 or ph <= 0 then
			skipped = skipped + 1
		else
			list[#list + 1] = { o = o, pw = pw, ph = ph }
		end
	end
	return list, skipped
end

local function skipNote(n)
	if n > 0 then return string.format(" (%d öğe layout/boyut yüzünden atlandı)", n) end
	return ""
end

local function withHistory(name, fn)
	ChangeHistoryService:SetWaypoint("UI Tools: önce " .. name)
	local ok, err = pcall(fn)
	ChangeHistoryService:SetWaypoint("UI Tools: " .. name)
	if not ok then setStatus("Hata: " .. tostring(err), COL.bad) end
	return ok
end

-- ---------------------------------------------------------------- konsol (durum kartı)
local consoleCard = make("Frame", { Size = UDim2.new(1, 0, 0, 58), BackgroundColor3 = COL.card, BorderSizePixel = 0, LayoutOrder = nextOrder() }, root)
corner(consoleCard, 10)
stroke(consoleCard)
make("TextLabel", {
	Text = "KONSOL", Font = Enum.Font.Code, TextSize = 9, TextColor3 = COL.muted, BackgroundTransparency = 1,
	Position = UDim2.new(0, 10, 0, 6), Size = UDim2.new(0.6, 0, 0, 14), TextXAlignment = Enum.TextXAlignment.Left,
}, consoleCard)
local statusChip = chip("HAZIR", consoleCard, COL.ok, Color3.fromRGB(16, 44, 34))
statusChip.AnchorPoint = Vector2.new(1, 0)
statusChip.Position = UDim2.new(1, -8, 0, 4)
local status = make("TextLabel", {
	Name = "UT_Status", Text = "› Bir GUI öğesi seç.", Font = Enum.Font.Code, TextSize = 11, TextColor3 = COL.ok,
	BackgroundTransparency = 1, Position = UDim2.new(0, 10, 0, 24), Size = UDim2.new(1, -20, 1, -28),
	TextXAlignment = Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Top, TextWrapped = true,
}, consoleCard)

setStatus = function(text, color)
	color = color or COL.muted
	status.Text = "› " .. tostring(text)
	status.TextColor3 = color
	if color == COL.warn then
		statusChip.Text, statusChip.TextColor3, statusChip.BackgroundColor3 = "UYARI", COL.warn, Color3.fromRGB(52, 40, 12)
	elseif color == COL.bad then
		statusChip.Text, statusChip.TextColor3, statusChip.BackgroundColor3 = "HATA", COL.bad, Color3.fromRGB(56, 22, 24)
	elseif color == COL.ok then
		statusChip.Text, statusChip.TextColor3, statusChip.BackgroundColor3 = "TAMAM", COL.ok, Color3.fromRGB(16, 44, 34)
	else
		statusChip.Text, statusChip.TextColor3, statusChip.BackgroundColor3 = "BİLGİ", COL.muted, COL.row
	end
end
setStatus("Bir GUI öğesi seç.", COL.muted)

-- ---------------------------------------------------------------- HİZALA
local ALIGN = {
	{ "left", "Sol" }, { "hcenter", "Yatay Orta" }, { "right", "Sağ" },
	{ "top", "Üst" }, { "vcenter", "Dikey Orta" }, { "bottom", "Alt" },
}

local function alignSelected(mode)
	local list, skipped = positionable()
	if #list == 0 then return setStatus("Hizalanacak konumlandırılabilir bir öğe seç." .. skipNote(skipped), COL.warn) end
	local useParent = (state.target == "parent") or #list == 1
	if not useParent then
		local p0 = list[1].o.Parent
		for i = 2, #list do
			if list[i].o.Parent ~= p0 then
				return setStatus("Seçim farklı üst öğelerde. Hedefi 'Üst öğe' yap ya da aynı üst öğedeki öğeleri seç.", COL.warn)
			end
		end
	end
	local ok = withHistory("hizala " .. mode, function()
		if useParent then
			for _, e in ipairs(list) do
				local r = rectOf(e.o, e.pw, e.ph)
				local res = Core.align({ r }, mode, { x = 0, y = 0, w = e.pw, h = e.ph })
				setTopLeft(e.o, res[1].x, res[1].y, e.pw, e.ph)
			end
		else
			local rects = {}
			for i, e in ipairs(list) do rects[i] = rectOf(e.o, e.pw, e.ph) end
			local res = Core.align(rects, mode)
			for i, e in ipairs(list) do setTopLeft(e.o, res[i].x, res[i].y, e.pw, e.ph) end
		end
	end)
	if ok then setStatus(#list .. " öğe hizalandı." .. skipNote(skipped), COL.ok) end
end

-- ---------------------------------------------------------------- DAĞIT (v22)
local function distributeSelected(axis)
	local list, skipped = positionable()
	if #list < 3 then return setStatus("Dağıtmak için en az 3 konumlandırılabilir öğe seç." .. skipNote(skipped), COL.warn) end
	local p0 = list[1].o.Parent
	for i = 2, #list do
		if list[i].o.Parent ~= p0 then
			return setStatus("Dağıtma için öğeler aynı üst öğede olmalı.", COL.warn)
		end
	end
	local ok = withHistory("dağıt " .. axis, function()
		local rects = {}
		for i, e in ipairs(list) do rects[i] = rectOf(e.o, e.pw, e.ph) end
		local res, err = Core.distribute(rects, axis)
		if not res then error(err) end
		for i, e in ipairs(list) do setTopLeft(e.o, res[i].x, res[i].y, e.pw, e.ph) end
	end)
	if ok then setStatus(#list .. " öğe eşit aralıkla dağıtıldı." .. skipNote(skipped), COL.ok) end
end

local alignCard = card("Hizala", "01 / HİZALA")
local targetChip
local function refreshTarget()
	targetChip.Text = state.target == "parent" and "HEDEF · ÜST ÖĞE" or "HEDEF · SEÇİM"
end
targetChip = make("TextButton", {
	Name = "UT_Target", Text = "", Font = Enum.Font.Code, TextSize = 9, TextColor3 = COL.purpleSoft,
	BackgroundColor3 = Color3.fromRGB(42, 33, 80), BorderSizePixel = 0, AutoButtonColor = true,
	Size = UDim2.new(0, 0, 0, 18), AutomaticSize = Enum.AutomaticSize.X, Position = UDim2.new(0, 0, 0, 0),
}, alignCard)
make("UIPadding", { PaddingLeft = UDim.new(0, 7), PaddingRight = UDim.new(0, 7) }, targetChip)
corner(targetChip, 6)
targetChip.MouseButton1Click:Connect(function()
	state.target = state.target == "parent" and "selection" or "parent"
	plugin:SetSetting("UT_target", state.target)
	refreshTarget()
end)
refreshTarget()
for i = 1, 6, 3 do
	local r = row(alignCard, 24)
	for j = i, i + 2 do
		local m = ALIGN[j]
		button("UT_Align_" .. m[1], m[2], r, 1 / 3, function() alignSelected(m[1]) end)
	end
end
local distRow = row(alignCard, 24)
button("UT_Dist_h", "Yatay dağıt", distRow, 0.5, function() distributeSelected("h") end)
button("UT_Dist_v", "Dikey dağıt", distRow, 0.5, function() distributeSelected("v") end)

-- ---------------------------------------------------------------- TAŞI (kaydırıcı + değer kutusu)
local moveCard = card("Taşı", "02 / TAŞI")

local sliderRow = make("Frame", { Size = UDim2.new(1, 0, 0, 24), BackgroundTransparency = 1, LayoutOrder = nextOrder() }, moveCard)
make("TextLabel", {
	Text = "Adım", Font = Enum.Font.GothamMedium, TextSize = 11, TextColor3 = COL.muted,
	BackgroundTransparency = 1, Size = UDim2.new(0, 36, 1, 0), TextXAlignment = Enum.TextXAlignment.Left,
}, sliderRow)
-- track: tutması kolay, satır boyunda saydam alan. rail: görünen çubuk (iki ucundan 7 px içeride),
-- böylece tutamaç (14 px) hiçbir zaman kartın / panelin dışına taşmaz.
local track = make("TextButton", {
	Name = "UT_StepTrack", Text = "", AutoButtonColor = false, BackgroundTransparency = 1, BorderSizePixel = 0,
	Position = UDim2.new(0, 40, 0, 0), Size = UDim2.new(1, -40 - 58, 1, 0), Active = true,
}, sliderRow)
local rail = make("Frame", {
	Name = "UT_StepRail", BackgroundColor3 = COL.row, BorderSizePixel = 0,
	Position = UDim2.new(0, 7, 0.5, -3), Size = UDim2.new(1, -14, 0, 6),
}, track)
corner(rail, 3)
local fill = make("Frame", { Name = "UT_StepFill", BackgroundColor3 = COL.lilac, BorderSizePixel = 0, Size = UDim2.new(0, 0, 1, 0) }, rail)
corner(fill, 3)
local knob = make("Frame", {
	Name = "UT_StepKnob", BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
	Size = UDim2.new(0, 14, 0, 14), Position = UDim2.new(0, 0, 0.5, 0), ZIndex = 2,
}, rail)
corner(knob, 7)
local stepBox = textbox("UT_Step", plugin:GetSetting("UT_step") or "1", sliderRow,
	UDim2.new(1, -52, 0, 0), UDim2.new(0, 52, 1, 0))
stepBox.TextXAlignment = Enum.TextXAlignment.Center

local function stepValue()
	local v = tonumber(stepBox.Text)
	if not v or v <= 0 then return 1 end
	return v
end

-- persist=false: sürükleme sırasında diske yazma (her karede SetSetting yavaş); bırakınca yazılır.
local function showStep(v, persist)
	local frac = Core.valueToFrac(v, STEP_MIN, STEP_MAX)
	fill.Size = UDim2.new(frac, 0, 1, 0)
	knob.Position = UDim2.new(frac, 0, 0.5, 0)
	stepBox.Text = Core.formatValue(v)
	if persist ~= false then plugin:SetSetting("UT_step", stepBox.Text) end
end
showStep(stepValue())

-- KÖK NEDEN (eski sürüm): UserInputService:GetMouseLocation() Studio ANA penceresine göre konum verir;
-- AbsolutePosition ise plugin penceresine göredir. İki koordinat sistemi uyuşmadığı için tutamaç
-- panelin dışında/yanlış yerde ilerliyordu. UserInputService.InputChanged de plugin penceresi
-- üzerindeki fare hareketini güvenilir iletmez.
-- ÇÖZÜM: PluginGui:GetRelativeMousePosition() — pencerenin sol-üstüne göre konum; basma plugin
-- penceresinde başladıysa fare pencere dışına çıksa bile güncellenmeye devam eder.
local dragging = false
local dragConn
local lastStep

local function sliderFromMouse()
	local okM, m = pcall(function() return widget:GetRelativeMousePosition() end)
	if not okM or not m then return end
	local frac = (m.X - rail.AbsolutePosition.X) / math.max(1, rail.AbsoluteSize.X)
	local v = Core.sliderToValue(frac, STEP_MIN, STEP_MAX, 1)
	if v ~= lastStep then
		lastStep = v
		showStep(v, false)
	end
end

local function stopDrag()
	if dragConn then dragConn:Disconnect(); dragConn = nil end
	if dragging then
		dragging = false
		plugin:SetSetting("UT_step", stepBox.Text)
	end
end

local function startDrag(input)
	stopDrag()
	dragging = true
	lastStep = nil
	sliderFromMouse()
	-- fare pencere dışında olsa da konumu her karede oku
	dragConn = RunService.Heartbeat:Connect(function()
		if dragging then sliderFromMouse() end
	end)
	-- bırakma nerede olursa olsun (pencere dışı dahil) bu girdi nesnesi End durumuna geçer
	input.Changed:Connect(function()
		if input.UserInputState == Enum.UserInputState.End then stopDrag() end
	end)
end

track.InputBegan:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 then startDrag(input) end
end)
track.InputEnded:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 then stopDrag() end
end)
widget.WindowFocusReleased:Connect(stopDrag)
widget:GetPropertyChangedSignal("Enabled"):Connect(function()
	if not widget.Enabled then stopDrag() end
end)

stepBox.FocusLost:Connect(function()
	local v = tonumber(stepBox.Text)
	if v and v > 0 then showStep(v) else showStep(1) end
end)

local function shiftSelection(dx, dy)
	local list, skipped = positionable()
	if #list == 0 then return setStatus("Taşınacak konumlandırılabilir bir öğe seç." .. skipNote(skipped), COL.warn) end
	local ok = withHistory("taşı", function()
		for _, e in ipairs(list) do
			local r = rectOf(e.o, e.pw, e.ph)
			local res = Core.shiftRects({ r }, dx, dy, state.grid)
			setTopLeft(e.o, res[1].x, res[1].y, e.pw, e.ph)
		end
	end)
	if ok then setStatus(#list .. " öğe taşındı." .. skipNote(skipped), COL.ok) end
end

local arrows = row(moveCard, 24)
button("UT_Shift_left", "←", arrows, 0.25, function() shiftSelection(-stepValue(), 0) end)
button("UT_Shift_up", "↑", arrows, 0.25, function() shiftSelection(0, -stepValue()) end)
button("UT_Shift_down", "↓", arrows, 0.25, function() shiftSelection(0, stepValue()) end)
button("UT_Shift_right", "→", arrows, 0.25, function() shiftSelection(stepValue(), 0) end)

-- Ok tuşları (v22): yalnız UI Tools penceresi odaktayken. Kod yazarken ok tuşları öğeyi taşımaz.
local windowFocused = false
widget.WindowFocused:Connect(function() windowFocused = true end)
widget.WindowFocusReleased:Connect(function() windowFocused = false end)
local KEY_DIR = {
	[Enum.KeyCode.Left] = { -1, 0 }, [Enum.KeyCode.Right] = { 1, 0 },
	[Enum.KeyCode.Up] = { 0, -1 }, [Enum.KeyCode.Down] = { 0, 1 },
}
UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed or not windowFocused or not widget.Enabled then return end
	if input.UserInputType ~= Enum.UserInputType.Keyboard then return end
	local d = KEY_DIR[input.KeyCode]
	if not d then return end
	local typing = false
	pcall(function() typing = UserInputService:GetFocusedTextBox() ~= nil end)
	if typing then return end
	shiftSelection(d[1] * stepValue(), d[2] * stepValue())
end)

local gridBtn
local function refreshGrid()
	gridBtn.Text = state.grid == 0 and "Izgara · kapalı" or ("Izgara · " .. state.grid .. " px")
end
local gridRow = row(moveCard, 24)
gridBtn = button("UT_Grid", "", gridRow, 1, function()
	local idx = 1
	for i, v in ipairs(GRID_CYCLE) do if v == state.grid then idx = i end end
	state.grid = GRID_CYCLE[(idx % #GRID_CYCLE) + 1]
	plugin:SetSetting("UT_grid", state.grid)
	refreshGrid()
end)
refreshGrid()

-- ---------------------------------------------------------------- KONUM & BOYUT (2x2, etiket solda)
local fieldCard = card("Konum & Boyut", "03 / ALAN")
local fields = {}

local function applyField(key, value)
	local list, skipped = positionable()
	if #list == 0 then return setStatus("Önce bir öğe seç." .. skipNote(skipped), COL.warn) end
	local ok = withHistory("konum/boyut", function()
		for _, e in ipairs(list) do
			local r = rectOf(e.o, e.pw, e.ph)
			if key == "X" then setTopLeft(e.o, value, r.y, e.pw, e.ph)
			elseif key == "Y" then setTopLeft(e.o, r.x, value, e.pw, e.ph)
			elseif key == "W" then setSize(e.o, value, r.h, e.pw, e.ph); setTopLeft(e.o, r.x, r.y, e.pw, e.ph)
			elseif key == "H" then setSize(e.o, r.w, value, e.pw, e.ph); setTopLeft(e.o, r.x, r.y, e.pw, e.ph)
			end
		end
	end)
	if ok then setStatus(key .. " = " .. Core.formatValue(value) .. " uygulandı.", COL.ok) end
end

local function fieldPair(parent, key, xScale)
	local lbl = make("TextLabel", {
		Text = key, Font = Enum.Font.GothamMedium, TextSize = 11, TextColor3 = COL.muted, BackgroundTransparency = 1,
		Position = UDim2.new(xScale, 0, 0, 0), Size = UDim2.new(0, 14, 1, 0), TextXAlignment = Enum.TextXAlignment.Left,
	}, parent)
	local tb = textbox("UT_Field_" .. key, "", parent, UDim2.new(xScale, 16, 0, 0), UDim2.new(0.5, -22, 1, 0))
	fields[key] = tb
	tb.FocusLost:Connect(function()
		local v = tonumber(tb.Text)
		if v then applyField(key, v) else setStatus("Sayı gir: " .. key, COL.warn) end
	end)
	return lbl
end

for _, pairRow in ipairs({ { "X", "Y" }, { "W", "H" } }) do
	local r = make("Frame", { Size = UDim2.new(1, 0, 0, 24), BackgroundTransparency = 1, LayoutOrder = nextOrder() }, fieldCard)
	fieldPair(r, pairRow[1], 0)
	fieldPair(r, pairRow[2], 0.5)
end

local function refreshFields()
	local list = positionable()
	local e = list[1]
	for key, tb in pairs(fields) do
		if e then
			local r = rectOf(e.o, e.pw, e.ph)
			local v = (key == "X" and r.x) or (key == "Y" and r.y) or (key == "W" and r.w) or r.h
			tb.Text = Core.formatValue(math.floor(v * 100 + 0.5) / 100)
		else
			tb.Text = ""
		end
	end
end

-- ---------------------------------------------------------------- SINIF DEĞİŞTİR
local classCard = card("Sınıf Değiştir", "04 / SINIF")
local function changeSelectionClass(toClass)
	local targets = selectedGuis()
	if #targets == 0 then return setStatus("Sınıfı değişecek bir GUI öğesi seç.", COL.warn) end
	local done, failed, warned = {}, {}, {}
	local ok = withHistory("sınıf " .. toClass, function()
		for _, o in ipairs(targets) do
			local plan, err = Core.classChangePlan(o.ClassName, toClass)
			if not plan then
				failed[#failed + 1] = o.Name .. ": " .. err
			else
				local n = Instance.new(toClass)
				for _, p in ipairs(plan.copy) do
					pcall(function() n[p] = o[p] end)
				end
				for k, v in pairs(o:GetAttributes()) do n:SetAttribute(k, v) end
				for _, c in ipairs(o:GetChildren()) do c.Parent = n end
				n.Parent = o.Parent
				o:Destroy()
				done[#done + 1] = n
				for _, w in ipairs(plan.warnings) do warned[#warned + 1] = w end
			end
		end
		if #done > 0 then Selection:Set(done) end
	end)
	if not ok then return end
	local msg = #done .. " öğe " .. toClass .. " oldu."
	if #warned > 0 then msg = msg .. " Uyarı: " .. table.concat(warned, ", ") .. "." end
	if #failed > 0 then msg = msg .. " Atlandı: " .. table.concat(failed, "; ") end
	setStatus(msg, #failed > 0 and COL.warn or COL.ok)
end

-- Her sınıf: üstte Studio'nun Explorer ikonu (ortada), altında düğme; düğme yazısı sınıf adı.
-- İkon: StudioService:GetClassIcon (Image + ImageRectOffset + ImageRectSize), tema uyumlu.
local function setClassIcon(img, className)
	local okI, d = pcall(function() return StudioService:GetClassIcon(className) end)
	if okI and d and d.Image then
		img.Image = d.Image
		img.ImageRectOffset = d.ImageRectOffset
		img.ImageRectSize = d.ImageRectSize
	end
end

local classGrid = make("Frame", {
	Name = "UT_ClassGrid", Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y,
	BackgroundTransparency = 1, LayoutOrder = nextOrder(),
}, classCard)
make("UIGridLayout", {
	CellSize = UDim2.new(0.5, -4, 0, 46), CellPadding = UDim2.new(0, 8, 0, 8),
	SortOrder = Enum.SortOrder.LayoutOrder, FillDirectionMaxCells = 2,
}, classGrid)

for _, cls in ipairs(Core.CLASS_ORDER) do
	local cell = make("Frame", { Name = "UT_ClassCell_" .. cls, BackgroundTransparency = 1, LayoutOrder = nextOrder() }, classGrid)
	make("UIListLayout", {
		FillDirection = Enum.FillDirection.Vertical, HorizontalAlignment = Enum.HorizontalAlignment.Center,
		VerticalAlignment = Enum.VerticalAlignment.Top, SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 4),
	}, cell)
	local icon = make("ImageLabel", {
		Name = "UT_ClassIcon_" .. cls, BackgroundTransparency = 1, BorderSizePixel = 0,
		Size = UDim2.new(0, 16, 0, 16), LayoutOrder = 1,
	}, cell)
	setClassIcon(icon, cls)
	local btn = button("UT_Class_" .. cls, cls, cell, 1, function() changeSelectionClass(cls) end, "primary")
	btn.Size = UDim2.new(1, 0, 0, 24)
	btn.LayoutOrder = 2
end

-- ---------------------------------------------------------------- ÖLÇEK
local scaleCard = card("Ölçek", "05 / SCALE")
local function convertSelected(toScale)
	local list, skipped = positionable()
	if #list == 0 then return setStatus("Dönüştürülecek bir öğe seç." .. skipNote(skipped), COL.warn) end
	local ok = withHistory(toScale and "offset to scale" or "scale to offset", function()
		for _, e in ipairs(list) do
			local o, pw, ph = e.o, e.pw, e.ph
			local px_, py_ = px(o.Position.X, pw), px(o.Position.Y, ph)
			local w, h = px(o.Size.X, pw), px(o.Size.Y, ph)
			if toScale then
				o.Position = UDim2.new(Core.toScale(px_, pw), 0, Core.toScale(py_, ph), 0)
				o.Size = UDim2.new(Core.toScale(w, pw), 0, Core.toScale(h, ph), 0)
			else
				o.Position = UDim2.new(0, px_, 0, py_)
				o.Size = UDim2.new(0, w, 0, h)
			end
		end
	end)
	if ok then setStatus(#list .. " öğe " .. (toScale and "Offset → Scale" or "Scale → Offset") .. " çevrildi." .. skipNote(skipped), COL.ok) end
end
local scaleRow = row(scaleCard, 24)
button("UT_Scale_toScale", "Offset to Scale", scaleRow, 0.5, function() convertSelected(true) end, "primary")
button("UT_Scale_toOffset", "Scale to Offset", scaleRow, 0.5, function() convertSelected(false) end, "primary")

-- ---------------------------------------------------------------- TEMİZLE
local cleanCard = card("Temizle", "06 / TEMİZLE")
local function clearAttributes()
	local targets = selectedAll()
	if #targets == 0 then return setStatus("Öznitelikleri silinecek bir öğe seç.", COL.warn) end
	local n = 0
	local ok = withHistory("öznitelikleri temizle", function()
		for _, o in ipairs(targets) do
			for k in pairs(o:GetAttributes()) do
				o:SetAttribute(k, nil)
				n = n + 1
			end
		end
	end)
	if ok then setStatus(n .. " öznitelik silindi.", n > 0 and COL.ok or COL.muted) end
end
local function clearTags()
	local targets = selectedAll()
	if #targets == 0 then return setStatus("Etiketleri silinecek bir öğe seç.", COL.warn) end
	local n = 0
	local ok = withHistory("etiketleri temizle", function()
		for _, o in ipairs(targets) do
			for _, tag in ipairs(CollectionService:GetTags(o)) do
				CollectionService:RemoveTag(o, tag)
				n = n + 1
			end
		end
	end)
	if ok then setStatus(n .. " etiket silindi.", n > 0 and COL.ok or COL.muted) end
end
local cleanRow = row(cleanCard, 24)
button("UT_Attr_clear", "Remove all Attributes", cleanRow, 0.5, clearAttributes, "danger")
button("UT_Tag_clear", "Remove All Tags", cleanRow, 0.5, clearTags, "danger")

-- ---------------------------------------------------------------- seçim izleme
-- ---------------------------------------------------------------- YERLEŞİM (UILayout) (v27)
-- Seçili UI öğelerine UILayout / UIPadding / UICorner / UIStroke / UIAspectRatioConstraint ekler.
-- Mevcut varsa yenisi açılmaz, değerleri güncellenir (çift eklenmez). Geri alma: ChangeHistoryService.
local layoutCard = card("Yerleşim (UILayout)", "07 / YERLEŞİM")
local function numOf(box, dflt)
	local v = tonumber(box and box.Text or "")
	if v == nil then return dflt end
	return v
end
local function ensureChild(o, class)
	local c = o:FindFirstChildOfClass(class)
	if not c then
		c = Instance.new(class)
		c.Parent = o
	end
	return c
end
local layoutBoxes = {}
local function applyLayout(kind)
	local targets = selectedGuis()
	if #targets == 0 then return setStatus("Yerleşim eklenecek bir UI öğesi seç.", COL.warn) end
	local pad = numOf(layoutBoxes.pad, 8)
	local space = numOf(layoutBoxes.space, 6)
	local radius = numOf(layoutBoxes.radius, 8)
	local thick = numOf(layoutBoxes.stroke, 2)
	local ok = withHistory("yerleşim " .. kind, function()
		for _, o in ipairs(targets) do
			if kind == "list_v" or kind == "list_h" then
				local l = ensureChild(o, "UIListLayout")
				l.FillDirection = kind == "list_v" and Enum.FillDirection.Vertical or Enum.FillDirection.Horizontal
				l.Padding = UDim.new(0, space)
			elseif kind == "grid" then
				local g = ensureChild(o, "UIGridLayout")
				g.CellSize = UDim2.new(0, 80, 0, 80)
				g.CellPadding = UDim2.new(0, space, 0, space)
			elseif kind == "pad" then
				local p = ensureChild(o, "UIPadding")
				local v = UDim.new(0, pad)
				p.PaddingLeft, p.PaddingRight, p.PaddingTop, p.PaddingBottom = v, v, v, v
			elseif kind == "corner" then
				ensureChild(o, "UICorner").CornerRadius = UDim.new(0, radius)
			elseif kind == "stroke" then
				local st = ensureChild(o, "UIStroke")
				st.Thickness = thick
				st.Color = COL.text
			elseif kind == "aspect" then
				ensureChild(o, "UIAspectRatioConstraint").AspectRatio = 1
			end
		end
	end)
	if ok then setStatus(#targets .. " öğeye " .. kind .. " uygulandı.", COL.ok) end
end
-- Yalnızca yerleşim ve dolguyu kaldırır (köşe/çerçeve/oran tasarımın parçası olabilir; onlara dokunmaz).
local function removeLayouts()
	local targets = selectedGuis()
	if #targets == 0 then return setStatus("Yerleşimleri kaldırılacak bir öğe seç.", COL.warn) end
	local n = 0
	local ok = withHistory("yerleşimleri kaldır", function()
		for _, o in ipairs(targets) do
			for _, class in ipairs({ "UIListLayout", "UIGridLayout", "UIPadding" }) do
				local c = o:FindFirstChildOfClass(class)
				while c do
					c:Destroy()
					n = n + 1
					c = o:FindFirstChildOfClass(class)
				end
			end
		end
	end)
	if ok then setStatus(n .. " yerleşim/dolgu kaldırıldı.", n > 0 and COL.ok or COL.muted) end
end
local layoutRow1 = row(layoutCard, 24)
button("UT_Layout_list_v", "Dikey liste", layoutRow1, 1 / 3, function() applyLayout("list_v") end)
button("UT_Layout_list_h", "Yatay liste", layoutRow1, 1 / 3, function() applyLayout("list_h") end)
button("UT_Layout_grid", "Izgara", layoutRow1, 1 / 3, function() applyLayout("grid") end)
local layoutRow2 = row(layoutCard, 24)
button("UT_Layout_pad", "Dolgu", layoutRow2, 1 / 3, function() applyLayout("pad") end)
button("UT_Layout_corner", "Köşe", layoutRow2, 1 / 3, function() applyLayout("corner") end)
button("UT_Layout_stroke", "Çerçeve", layoutRow2, 1 / 3, function() applyLayout("stroke") end)
local layoutRow3 = row(layoutCard, 24)
button("UT_Layout_aspect", "Oran 1:1", layoutRow3, 1 / 2, function() applyLayout("aspect") end)
button("UT_Layout_clear", "Yerleşim/dolgu kaldır", layoutRow3, 1 / 2, function() removeLayouts() end)
local layoutRow4 = row(layoutCard, 26)
layoutBoxes.pad = textbox("UT_Layout_pad_v", "8", layoutRow4, UDim2.new(0, 0, 0, 2), UDim2.new(0.25, -4, 1, -4))
layoutBoxes.space = textbox("UT_Layout_space_v", "6", layoutRow4, UDim2.new(0.25, 2, 0, 2), UDim2.new(0.25, -4, 1, -4))
layoutBoxes.radius = textbox("UT_Layout_radius_v", "8", layoutRow4, UDim2.new(0.5, 4, 0, 2), UDim2.new(0.25, -4, 1, -4))
layoutBoxes.stroke = textbox("UT_Layout_stroke_v", "2", layoutRow4, UDim2.new(0.75, 6, 0, 2), UDim2.new(0.25, -6, 1, -4))

local function refreshInfo()
	local list = selectedAll()
	if #list == 0 then
		selInfo.Text = "Seçili değil"
		selChip.Text = "YOK"
	elseif #list == 1 then
		local o = list[1]
		selInfo.Text = (o.ClassName or "?") .. " · " .. (o.Name or "?")
		selChip.Text = "SEÇİLİ"
	else
		selInfo.Text = #list .. " öğe seçili"
		selChip.Text = #list .. " SEÇİLİ"
	end
	refreshFields()
end
Selection.SelectionChanged:Connect(refreshInfo)
refreshInfo()
