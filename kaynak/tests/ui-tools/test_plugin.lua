-- ============ MOCK ROBLOX ORTAMI (yalnız test için) ============
local EVENTS = { MouseButton1Click = true, FocusLost = true, Click = true, SelectionChanged = true, Changed = true, InputBegan = true, InputChanged = true, InputEnded = true, WindowFocusReleased = true, WindowFocused = true }
local CLASS_IS = {
	ScreenGui = { "LayerCollector", "GuiBase2d", "Instance" },
	Frame = { "GuiObject", "GuiBase2d", "Instance" }, TextLabel = { "GuiObject", "GuiBase2d", "Instance" },
	TextButton = { "GuiObject", "GuiBase2d", "Instance" }, TextBox = { "GuiObject", "GuiBase2d", "Instance" },
	ImageLabel = { "GuiObject", "GuiBase2d", "Instance" }, ImageButton = { "GuiObject", "GuiBase2d", "Instance" },
	ScrollingFrame = { "GuiObject", "GuiBase2d", "Instance" }, CanvasGroup = { "GuiObject", "GuiBase2d", "Instance" },
	ViewportFrame = { "GuiObject", "GuiBase2d", "Instance" },
	UIListLayout = { "Instance" }, UIPadding = { "Instance" }, UICorner = { "Instance" },
	UIGridLayout = { "Instance" }, UIAspectRatioConstraint = { "Instance" }, UIStroke = { "Instance" },
	UIGridLayout = { "Instance" },
}
local function V2(x, y) return { X = x, Y = y } end
local function UD(s, o) return { Scale = s, Offset = o } end
local function UDim2n(xs, xo, ys, yo) return { X = UD(xs, xo), Y = UD(ys, yo) } end
local function fire(ev, ...) for _, h in ipairs(ev.handlers) do h(...) end end
local function newEvent() local e = { handlers = {} }; function e:Connect(fn) table.insert(self.handlers, fn); return { Disconnect = function() end } end; return e end

local Enum = setmetatable({}, { __index = function(_, k)
	return setmetatable({}, { __index = function(_, k2) return k .. "." .. k2 end })
end })

local HISTORY = {}
local SETTINGS = {}
local SELECTION = {}
local SELECTION_EV = newEvent()
local Services = {}
local function removeFrom(list, v) for i, x in ipairs(list) do if x == v then table.remove(list, i); return end end end

local Inst = {}
local function newInst(className)
	local o = { _p = {}, _kids = {}, _ev = {}, _attr = {}, ClassName = className, Name = className }
	o._p.Position = UDim2n(0, 0, 0, 0)
	o._p.Size = UDim2n(0, 0, 0, 0)
	o._p.AnchorPoint = V2(0, 0)
	o._p.AbsoluteSize = V2(0, 0)
	o._p.Parent = nil
	return setmetatable(o, Inst)
end
Inst.__index = function(t, k)
	if EVENTS[k] then t._ev[k] = t._ev[k] or newEvent(); return t._ev[k] end
	if k == "IsA" then return function(self, c)
		local is = CLASS_IS[self.ClassName] or {}
		if c == self.ClassName then return true end
		for _, x in ipairs(is) do if x == c then return true end end
		return false
	end end
	if k == "Destroy" then return function(self) if self._p.Parent then removeFrom(self._p.Parent._kids, self) end; self._p.Parent = nil; self._destroyed = true end end
	if k == "GetChildren" then return function(self) local c = {}; for i, x in ipairs(self._kids) do c[i] = x end; return c end end
	if k == "FindFirstChildOfClass" then return function(self, cls) for _, x in ipairs(self._kids) do if x.ClassName == cls then return x end end return nil end end
	if k == "GetDescendants" then return function(self)
		local out = {}
		local function walk(n) for _, c in ipairs(n._kids) do table.insert(out, c); walk(c) end end
		walk(self); return out
	end end
	if k == "FindFirstChildWhichIsA" then return function(self, cls)
		for _, c in ipairs(self._kids) do if c.ClassName == cls or c:IsA(cls) then return c end end
	end end
	if k == "WaitForChild" or k == "FindFirstChild" then return function(self, n)
		for _, c in ipairs(self._kids) do if c.Name == n then return c end end
	end end
	if k == "GetPropertyChangedSignal" then return function(self, n) t._ev["PCS_" .. n] = t._ev["PCS_" .. n] or newEvent(); return t._ev["PCS_" .. n] end end
	if k == "SetAttribute" then return function(self, a, v) self._attr[a] = v end end
	if k == "GetAttributes" then return function(self) local c = {}; for a, v in pairs(self._attr) do c[a] = v end; return c end end
	if k == "GetAttribute" then return function(self, a) return self._attr[a] end end
	return t._p[k]
end
Inst.__newindex = function(t, k, v)
	if k == "Parent" then
		if t._p.Parent then removeFrom(t._p.Parent._kids, t) end
		t._p.Parent = v
		if v then table.insert(v._kids, t) end
	elseif k == "ClassName" or k == "_p" or k == "_kids" or k == "_ev" or k == "_attr" or k == "Name" then
		rawset(t, k, v)
	else
		t._p[k] = v
	end
end
Inst.__index = Inst.__index -- (aynı)
local Instance = { new = function(cls)
	local o = newInst(cls)
	return o
end }

-- Name ve ClassName'i de alanlardan oku
local _idx = Inst.__index
Inst.__index = function(t, k)
	if k == "Name" then return rawget(t, "Name") end
	return _idx(t, k)
end

local function mkService(name, tbl) tbl = tbl or {}; Services[name] = tbl; return tbl end
mkService("Selection", {
	Get = function() return SELECTION end,
	Set = function(_, list) SELECTION = list; fire(SELECTION_EV) end,
	SelectionChanged = SELECTION_EV,
})
local TAGS = {}
mkService("CollectionService", {
	GetTags = function(_, o) local c = {}; for i, t in ipairs(TAGS[o] or {}) do c[i] = t end; return c end,
	AddTag = function(_, o, t) TAGS[o] = TAGS[o] or {}; table.insert(TAGS[o], t) end,
	RemoveTag = function(_, o, t) for i, x in ipairs(TAGS[o] or {}) do if x == t then table.remove(TAGS[o], i); return end end end,
})
local MOUSE = V2(0, 0)
local INPUT_BEGAN = newEvent()
local FOCUSED_TB = nil -- test: odaktaki metin kutusu (nil = yok)
mkService("UserInputService", {
	GetMouseLocation = function() return MOUSE end,
	InputBegan = INPUT_BEGAN,
	InputChanged = newEvent(), InputEnded = newEvent(),
	GetFocusedTextBox = function() return FOCUSED_TB end,
})
local HEARTBEAT = newEvent()
mkService("RunService", { Heartbeat = HEARTBEAT })
local ICON_CALLS = {}
mkService("StudioService", { GetClassIcon = function(_, cls)
	ICON_CALLS[#ICON_CALLS + 1] = cls
	return { Image = "rbxasset://icons/" .. cls, ImageRectOffset = V2(16, 0), ImageRectSize = V2(16, 16) }
end })
mkService("ChangeHistoryService", { SetWaypoint = function(_, n) table.insert(HISTORY, n) end })
local gameObj = { GetService = function(_, n) return Services[n] end }
local camera = { ViewportSize = V2(1920, 1080) }
local workspaceObj = { CurrentCamera = camera }
local pluginObj = {
	CreateToolbar = function(_, n)
		return { CreateButton = function() return { Click = newEvent() } end }
	end,
	CreateDockWidgetPluginGui = function(_, id, info)
		local w = newInst("DockWidgetPluginGui"); w.Name = id; w.Enabled = false; w._p.GetRelativeMousePosition = function() return MOUSE end; WIDGET = w; return w
	end,
	GetSetting = function(_, k) return SETTINGS[k] end,
	SetSetting = function(_, k, v) SETTINGS[k] = v end,
}
local function PluginGuiInfo() return { new = function() return {} end } end

-- Ortam değişkenleri
_G.UDim2 = { new = function(xs, xo, ys, yo) return UDim2n(xs, xo, ys, yo) end }
_G.UDim = { new = function(s, o) return UD(s, o) end }
_G.Vector2 = { new = function(x, y) return V2(x, y) end }
_G.ColorSequence = { new = function(...) return { ... } end }
_G.Color3 = { fromRGB = function(r, g, b) return { R = r, G = g, B = b } end, new = function(r, g, b) return { R = r, G = g, B = b } end }
_G.Enum = Enum
_G.Instance = Instance
_G.DockWidgetPluginGuiInfo = { new = function() return {} end }
_G.game = gameObj
_G.workspace = workspaceObj
_G.plugin = pluginObj
local SCRIPT_CHILDREN = {}
_G.script = { WaitForChild = function(_, name)
	return { __loader = function() return load(__SRC.core)() end }
end }
_G.require = function(m) return m.__loader() end

-- ============ SAHNE ============
local function find(name)
	for _, d in ipairs(WIDGET:GetDescendants()) do if d.Name == name then return d end end
	error("bulunamadı: " .. name)
end
local function click(name) fire(find(name).MouseButton1Click) end
local function setText(name, text) find(name).Text = text end
local function blur(name, enter) fire(find(name).FocusLost, enter) end
local function statusText() return find("UT_Status").Text end

-- Oyun ağacı
local game_ = newInst("ScreenGui"); game_.Name = "Game"
local P = newInst("Frame"); P.Name = "P"; P.Parent = game_
P.AbsoluteSize = V2(200, 200)
P.Size = UDim2n(0, 200, 0, 200)
local A = newInst("Frame"); A.Name = "A"; A.Parent = P
A.Position = UDim2n(0, 10, 0, 10); A.Size = UDim2n(0, 50, 0, 20)
local B = newInst("Frame"); B.Name = "B"; B.Parent = P
B.Position = UDim2n(0, 100, 0, 40); B.Size = UDim2n(0, 30, 0, 30)
local T = newInst("TextLabel"); T.Name = "Etiket"; T.Parent = A; T.Text = "Merhaba"
local Q_root = newInst("Frame"); Q_root.Name = "R"; Q_root.Parent = game_; Q_root.AbsoluteSize = V2(100, 100)
local Q = newInst("Frame"); Q.Name = "Q"; Q.Parent = Q_root; Q.Position = UDim2n(0, 5, 0, 5); Q.Size = UDim2n(0, 10, 0, 10)

-- Eklentiyi yükle (kendi widget'ını oluşturur, WIDGET global'ine yazılır)
local okP, errP = xpcall(function() assert(load(__SRC.plugin, '=UIToolsPlugin'))() end, debug.traceback)
if not okP then return 'PLUGIN YÜKLEME HATASI:\n' .. tostring(errP) end

-- ============ SENARYOLAR ============
local results, fails = {}, {}
local function check(cond, msg) results[#results+1]=1; if not cond then fails[#fails+1]=msg end end
local Selection = Services.Selection
local function sel(list) Selection:Set(list) end
local function ok(name, fn)
	local good, err = pcall(fn)
	if not good then fails[#fails+1] = name .. " -> HATA: " .. tostring(err) end
end

ok("hizala sol: varsayılan hedef = üst öğe (x=0)", function()
	HISTORY = {}
	sel({ A, B }); click("UT_Align_left")
	check(A.Position.X.Offset == 0 and B.Position.X.Offset == 0, "üst öğenin soluna: " .. A.Position.X.Offset .. "," .. B.Position.X.Offset)
	check(HISTORY[1] == "UI Tools: önce hizala left" and HISTORY[2] == "UI Tools: hizala left", "undo waypoint: " .. table.concat(HISTORY, "|"))
end)

ok("hizala sol: hedef = seçim sınırı (x=10)", function()
	A.Position = UDim2n(0, 10, 0, 10); B.Position = UDim2n(0, 100, 0, 40)
	click("UT_Target")
	sel({ A, B }); click("UT_Align_left")
	check(A.Position.X.Offset == 10 and B.Position.X.Offset == 10, "seçim sınırının soluna: " .. A.Position.X.Offset .. "," .. B.Position.X.Offset)
	click("UT_Target")
end)

ok("tek öğe -> üst öğeye göre sağ", function()
	sel({ A }); click("UT_Align_right")
	check(A.Position.X.Offset == 150, "A sağ (200-50): " .. A.Position.X.Offset)
end)

ok("hedef seçim sınırı + alt", function()
	click("UT_Target")  -- parent -> selection
	check(SETTINGS.UT_target == "selection", "hedef ayarı kaydedildi")
	sel({ A, B }); click("UT_Align_bottom")
	-- A: y 10..30, B: y 40..70 -> sınır 10..70 -> alt: A.y=50, B.y=40
	check(A.Position.Y.Offset == 50, "A alt: " .. A.Position.Y.Offset)
	check(B.Position.Y.Offset == 40, "B alt: " .. B.Position.Y.Offset)
	click("UT_Target")  -- geri: parent
end)

ok("farklı üst öğeler (seçim hedefi) uyarı", function()
	click("UT_Target")
	sel({ A, Q }); click("UT_Align_top")
	check(statusText():find("farklı") ~= nil, "farklı üst uyarısı: " .. statusText())
	click("UT_Target")
end)

ok("taşı: adım 5, ızgara kapalı", function()
	-- grid 1 (varsayılan) -> önce kapat
	click("UT_Grid"); click("UT_Grid")  -- 1 -> 4 -> 8
	click("UT_Grid")                   -- 8 -> 0 (kapalı)
	check(SETTINGS.UT_grid == 0, "ızgara kapalı kaydı: " .. tostring(SETTINGS.UT_grid))
	setText("UT_Step", "5")
	sel({ A }); local x0 = A.Position.X.Offset
	click("UT_Shift_right")
	check(A.Position.X.Offset == x0 + 5, "sağa 5: " .. A.Position.X.Offset .. " (önce " .. x0 .. ")")
	click("UT_Shift_up")
	check(A.Position.Y.Offset == 45, "yukarı 5 (önce 50): " .. A.Position.Y.Offset)
end)

ok("taşı: ızgara 4 px yuvarlar", function()
	click("UT_Grid")                   -- 0 -> 1
	click("UT_Grid")                   -- 1 -> 4
	check(SETTINGS.UT_grid == 4, "ızgara 4")
	setText("UT_Step", "1")
	sel({ A }); A.Position = UDim2n(0, 13, 0, 13)
	click("UT_Shift_right")            -- 14 -> snap 4 -> 16 (14/4=3.5 yukarı)
	check(A.Position.X.Offset == 16, "ızgara 4 snap: " .. A.Position.X.Offset)
end)

ok("konum/boyut alanı", function()
	sel({ A }); setText("UT_Field_X", "33"); blur("UT_Field_X", true)
	check(A.Position.X.Offset == 33, "X=33: " .. A.Position.X.Offset)
	setText("UT_Field_W", "77"); blur("UT_Field_W", true)
	check(A.Size.X.Offset == 77, "W=77: " .. A.Size.X.Offset)
	sel({}); sel({ A }); check(find("UT_Field_X").Text == "33", "alan seçimle senkron: " .. find("UT_Field_X").Text)
	setText("UT_Field_Y", "abc"); blur("UT_Field_Y", true)
	check(statusText():find("Sayı") ~= nil, "geçersiz sayı uyarısı")
end)

ok("sınıf değiştir: Frame -> TextButton (çocuk ve ad korunur)", function()
	sel({ A })
	A:SetAttribute("EI_Id", 7)
	local oldA = A
	click("UT_Class_TextButton")
	local newA = SELECTION[1]
	check(newA ~= nil and newA.ClassName == "TextButton", "yeni sınıf TextButton")
	check(newA.Name == "A", "ad korunur: " .. tostring(newA and newA.Name))
	check(newA.Parent == P, "üst öğe korunur")
	check(oldA._destroyed == true, "eski öğe silindi")
	check(T.Parent == newA, "çocuk yeni öğeye taşındı")
	check(newA.Position.X.Offset == 33, "konum kopyalandı: " .. tostring(newA.Position.X.Offset))
	check(newA:GetAttribute("EI_Id") == 7, "öznitelik kopyalandı")
	check(T.Text == "Merhaba", "çocuk metni korundu")
	check(HISTORY[#HISTORY] == "UI Tools: sınıf TextButton", "sınıf değişimi geri alınabilir: " .. tostring(HISTORY[#HISTORY]))
	check(statusText():find("oldu") ~= nil, "durum: " .. statusText())
	A = newA
end)

ok("aynı sınıfa dönüşüm reddedilir", function()
	sel({ A }); click("UT_Class_TextButton")
	check(statusText():find("zaten") ~= nil, "zaten uyarısı: " .. statusText())
end)

ok("metin kaybı uyarısı (TextButton -> Frame)", function()
	sel({ A }); click("UT_Class_Frame")
	check(statusText():find("metin silinecek") ~= nil, "metin uyarısı: " .. statusText())
	A = SELECTION[1]
end)

ok("Scale'e çevir ve geri Offset'e", function()
	sel({ B })
	local bx = B.Position.X.Offset  -- 100 (ya da önceki işlemlerden değişmiş olabilir)
	local bw = B.Size.X.Offset
	click("UT_Scale_toScale")
	check(math.abs(B.Position.X.Scale - bx / 200) < 1e-9 and B.Position.X.Offset == 0, "konum scale: " .. B.Position.X.Scale)
	check(math.abs(B.Size.X.Scale - bw / 200) < 1e-9 and B.Size.X.Offset == 0, "boyut scale")
	-- Y ekseni: B.Y = 40, B.H = 30 (üst öğe 200x200)
	check(math.abs(B.Position.Y.Scale - 40 / 200) < 1e-9 and B.Position.Y.Offset == 0, "konum Y scale: " .. B.Position.Y.Scale)
	check(math.abs(B.Size.Y.Scale - 30 / 200) < 1e-9 and B.Size.Y.Offset == 0, "boyut Y scale")
	click("UT_Scale_toOffset")
	check(math.abs(B.Position.X.Offset - bx) < 1e-9 and B.Position.X.Scale == 0, "offset'e geri: " .. B.Position.X.Offset)
	check(math.abs(B.Size.X.Offset - bw) < 1e-9, "boyut offset'e geri")
	check(math.abs(B.Position.Y.Offset - 40) < 1e-9 and B.Position.Y.Scale == 0, "Y offset'e geri: " .. B.Position.Y.Offset)
	check(math.abs(B.Size.Y.Offset - 30) < 1e-9 and B.Size.Y.Scale == 0, "boyut Y offset'e geri")
end)

ok("layout kontrollü üst öğe atlanır", function()
	local L = newInst("Frame"); L.Name = "LayoutBox"; L.Parent = game_; L.AbsoluteSize = V2(300, 300)
	local lay = newInst("UIListLayout"); lay.Parent = L
	local item = newInst("Frame"); item.Name = "Item"; item.Parent = L; item.Size = UDim2n(0, 40, 0, 40)
	sel({ item }); click("UT_Align_left")
	check(statusText():find("atlandı") ~= nil, "layout atlama uyarısı: " .. statusText())
end)

ok("kaydırıcı: pencereye göre fare konumu adım değerini ayarlar (Heartbeat ile sürüklenir)", function()
	local rl = find("UT_StepRail")
	rl.AbsolutePosition = V2(100, 0); rl.AbsoluteSize = V2(100, 6)
	local tr = find("UT_StepTrack")
	-- Ana pencere koordinatı bilerek farklı: eski hata bunu okuyordu
	Services.UserInputService.GetMouseLocation = function() return V2(9999, 9999) end
	local input = { UserInputType = Enum.UserInputType.MouseButton1, UserInputState = Enum.UserInputState.Begin, Changed = newEvent() }
	MOUSE = V2(100, 3)   -- rail başı -> min (1)
	fire(tr.InputBegan, input)
	check(find("UT_Step").Text == "1", "kaydırıcı başı = 1: " .. find("UT_Step").Text)
	check(#HEARTBEAT.handlers >= 1, "sürükleme Heartbeat bağladı")
	MOUSE = V2(150, 3)   -- orta
	fire(HEARTBEAT)
	check(find("UT_Step").Text == "26" or find("UT_Step").Text == "25", "kaydırıcı ortası ~25: " .. find("UT_Step").Text)
	check(math.abs(find("UT_StepKnob").Position.X.Scale - find("UT_StepFill").Size.X.Scale) < 1e-9, "tutamaç dolguyla aynı yerde")
	MOUSE = V2(5000, 3)  -- fare pencerenin ÇOK dışında: değer sona kenetlenir, taşmaz
	fire(HEARTBEAT)
	check(find("UT_Step").Text == "50", "pencere dışında kenetlenir = 50: " .. find("UT_Step").Text)
	check(math.abs(find("UT_StepFill").Size.X.Scale - 1) < 1e-9 and find("UT_StepKnob").Position.X.Scale <= 1, "tutamaç 0..1 dışına çıkmaz")
	MOUSE = V2(-300, 3)  -- sola taşma
	fire(HEARTBEAT)
	check(find("UT_Step").Text == "1" and find("UT_StepKnob").Position.X.Scale >= 0, "sola taşınca kenetlenir = 1: " .. find("UT_Step").Text)
	MOUSE = V2(200, 3)
	fire(HEARTBEAT)
	check(find("UT_Step").Text == "50", "tekrar sona")
	check(SETTINGS.UT_step ~= "50", "sürükleme sırasında diske yazılmaz: " .. tostring(SETTINGS.UT_step))
	-- bırakma: girdi nesnesi End olur (pencere dışında bırakılsa da)
	input.UserInputState = Enum.UserInputState.End
	fire(input.Changed)
	check(SETTINGS.UT_step == "50", "bırakınca ayar yazıldı: " .. tostring(SETTINGS.UT_step))
	MOUSE = V2(150, 3)   -- sürükleme bitti: artık değer değişmemeli
	fire(HEARTBEAT)
	check(find("UT_Step").Text == "50", "sürükleme bitince kilitlenir: " .. find("UT_Step").Text)
	-- InputEnded ile de biter
	fire(tr.InputBegan, { UserInputType = Enum.UserInputType.MouseButton1, UserInputState = Enum.UserInputState.Begin, Changed = newEvent() })
	MOUSE = V2(100, 3); fire(HEARTBEAT)
	check(find("UT_Step").Text == "1", "ikinci sürükleme çalışır")
	fire(tr.InputEnded, { UserInputType = Enum.UserInputType.MouseButton1 })
	MOUSE = V2(200, 3); fire(HEARTBEAT)
	check(find("UT_Step").Text == "1", "InputEnded sürüklemeyi bitirir: " .. find("UT_Step").Text)
	-- pencere odağı kaybedilince de biter
	fire(tr.InputBegan, { UserInputType = Enum.UserInputType.MouseButton1, UserInputState = Enum.UserInputState.Begin, Changed = newEvent() })
	fire(WIDGET.WindowFocusReleased)
	MOUSE = V2(100, 3); fire(HEARTBEAT)
	check(find("UT_Step").Text == "50" or find("UT_Step").Text == "1", "odak kaybı sürüklemeyi bitirir")
	local before = find("UT_Step").Text
	MOUSE = V2(150, 3); fire(HEARTBEAT)
	check(find("UT_Step").Text == before, "odak kaybından sonra değişmez: " .. find("UT_Step").Text)
	-- Değer kutusundan 5 yaz -> nudge 5 px
	setText("UT_Step", "5"); blur("UT_Step", true)
	check(math.abs(find("UT_StepFill").Size.X.Scale - (4/49)) < 1e-9, "kutudan yazılınca dolgu güncellenir")
	sel({ A }); local x0 = A.Position.X.Offset
	click("UT_Grid"); click("UT_Grid"); click("UT_Grid")  -- 0 (kapalı)
	click("UT_Shift_right")
	check(A.Position.X.Offset == x0 + 5, "slider adımı nudge'da kullanılır: " .. A.Position.X.Offset)
end)

ok("sınıf kartında 10 UIListLayout var (kart 1 + 9 sınıf hücresi)", function()
	local grid = find("UT_ClassGrid")
	local card = grid.Parent
	local n = 0
	for _, d in ipairs(card:GetDescendants()) do
		if d.ClassName == "UIListLayout" then n = n + 1 end
	end
	if card:FindFirstChildWhichIsA("UIListLayout") then n = n + 0 end
	check(n == 10, "sınıf kartındaki UIListLayout sayısı = 10, bulunan: " .. n)
end)

ok("sınıf kartı: ikon üstte (UIListLayout), düğme sınıf adıyla, açık eflatun", function()
	local classes = { "Frame", "TextLabel", "TextButton", "TextBox", "ImageLabel", "ImageButton", "ScrollingFrame", "CanvasGroup", "ViewportFrame" }
	for _, c in ipairs(classes) do
		local icon = find("UT_ClassIcon_" .. c)
		check(icon.Image == "rbxasset://icons/" .. c, c .. " ikonu atandı: " .. tostring(icon.Image))
		check(icon.ImageRectSize and icon.ImageRectSize.X == 16, c .. " ikon rect boyutu")
		local cell = find("UT_ClassCell_" .. c)
		check(cell:FindFirstChildWhichIsA("UIListLayout") ~= nil, c .. " hücresinde UIListLayout var")
		local ok2, nameLbl = pcall(find, "UT_ClassName_" .. c)
		check(not ok2, c .. " ayrı isim etiketi yok")
		local b = find("UT_Class_" .. c)
		check(b.Text == c, c .. " düğme metni sınıf adı: " .. tostring(b.Text))
		check(b.BackgroundColor3.R == 198 and b.BackgroundColor3.G == 156 and b.BackgroundColor3.B == 255, c .. " düğmesi açık eflatun")
	end
	local Z = newInst("Frame"); Z.Name = "Z"; Z.Parent = P; Z.Size = UDim2n(0, 10, 0, 10)
	sel({ Z }); click("UT_Class_TextButton")
	check(Selection:Get()[1].ClassName == "TextButton", "düğme sınıfı değiştirdi: " .. tostring(Selection:Get()[1] and Selection:Get()[1].ClassName))
end)

ok("öznitelikleri temizle (seçili öğe)", function()
	sel({ A }); A:SetAttribute("EI_Id", 7); A:SetAttribute("Foo", "bar")
	HISTORY = {}
	click("UT_Attr_clear")
	local n = 0 ; for _ in pairs(A:GetAttributes()) do n = n + 1 end
	check(n == 0, "tüm öznitelikler silindi: " .. n)
	check(statusText():find("2 öznitelik silindi") ~= nil, "öznitelik durumu: " .. statusText())
	check(HISTORY[#HISTORY] == "UI Tools: öznitelikleri temizle", "geri alınabilir: " .. tostring(HISTORY[#HISTORY]))
end)

ok("tüm etiketleri temizle (seçili öğe)", function()
	sel({ A })
	Services.CollectionService:AddTag(A, "Button"); Services.CollectionService:AddTag(A, "Hover")
	click("UT_Tag_clear")
	check(#Services.CollectionService:GetTags(A) == 0, "etiketler silindi")
	check(statusText():find("2 etiket silindi") ~= nil, "etiket durumu: " .. statusText())
end)

ok("Offset to Scale / Scale to Offset adları ve gidiş-dönüş", function()
	check(find("UT_Scale_toScale").Text == "Offset to Scale", "düğme adı 1")
	check(find("UT_Scale_toOffset").Text == "Scale to Offset", "düğme adı 2")
end)

ok("seçim bilgisi güncellenir", function()
	sel({ A, B })
	check(find("UT_SelInfo").Text == "2 öğe seçili", "çoklu seçim metni: " .. find("UT_SelInfo").Text)
	sel({})
	check(find("UT_SelInfo").Text == "Seçili değil", "boş seçim metni")
end)


-- ---------------- v22: dağıtma ve ok tuşları ----------------
local function mkFrame(name, x, y, w, h)
	local f = newInst("Frame"); f.Name = name; f.Parent = P
	f.Position = UDim2n(0, x, 0, y); f.Size = UDim2n(0, w, 0, h)
	return f
end

ok("dağıt yatay: 3 öğe eşit aralık, uçlar sabit", function()
	HISTORY = {}
	local D1, D2, D3 = mkFrame("D1", 0, 150, 20, 20), mkFrame("D2", 60, 150, 20, 20), mkFrame("D3", 180, 150, 20, 20)
	sel({ D1, D2, D3 }); click("UT_Dist_h")
	check(D1.Position.X.Offset == 0, "dağıt: sol uç sabit: " .. D1.Position.X.Offset)
	check(D3.Position.X.Offset == 180, "dağıt: sağ uç sabit: " .. D3.Position.X.Offset)
	check(D2.Position.X.Offset == 90, "dağıt: orta öğe 90 (açıklık 200 - 60 = 140, boşluk 70): " .. D2.Position.X.Offset)
	check(HISTORY[#HISTORY] == "UI Tools: dağıt h", "dağıt geri alınabilir: " .. tostring(HISTORY[#HISTORY]))
	D1.Parent = nil; D2.Parent = nil; D3.Parent = nil
end)

ok("dağıt dikey: eksen y", function()
	local E1, E2, E3 = mkFrame("E1", 150, 0, 20, 20), mkFrame("E2", 150, 60, 20, 20), mkFrame("E3", 150, 180, 20, 20)
	sel({ E1, E2, E3 }); click("UT_Dist_v")
	check(E2.Position.Y.Offset == 90, "dikey dağıt: orta y 90: " .. E2.Position.Y.Offset)
	check(E1.Position.X.Offset == 150 and E2.Position.X.Offset == 150, "dikey dağıt x'e dokunmaz")
	E1.Parent = nil; E2.Parent = nil; E3.Parent = nil
end)

ok("dağıt: 2 öğe uyarı verir", function()
	sel({ A, B }); click("UT_Dist_h")
	check(statusText():find("en az 3") ~= nil, "2 öğe uyarısı: " .. statusText())
end)

ok("dağıt: farklı üst öğeler uyarı verir", function()
	local G1, G2 = mkFrame("G1", 0, 0, 10, 10), mkFrame("G2", 50, 0, 10, 10)
	local G3 = newInst("Frame"); G3.Name = "G3"; G3.Parent = Q_root; G3.Position = UDim2n(0, 5, 0, 5); G3.Size = UDim2n(0, 10, 0, 10)
	sel({ G1, G2, G3 }); click("UT_Dist_h")
	check(statusText():find("aynı üst öğede") ~= nil, "farklı üst uyarısı: " .. statusText())
	G1.Parent = nil; G2.Parent = nil; G3.Parent = nil
end)

-- Ok tuşları: önce ızgarayı kapat (adım tam değerle ölçülsün)
for _ = 1, 4 do if SETTINGS.UT_grid == 0 then break end; click("UT_Grid") end
setText("UT_Step", "5")

ok("ok tuşu: pencere odakta, sağ ok öğeyi adım kadar taşır", function()
	WIDGET.Enabled = true; fire(WIDGET.WindowFocused)
	sel({ A }); local x0 = A.Position.X.Offset
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Right }, false)
	check(A.Position.X.Offset == x0 + 5, "sağ ok: " .. A.Position.X.Offset .. " (önce " .. x0 .. ")")
end)

ok("ok tuşu: sol/yukarı/aşağı yönleri", function()
	sel({ A }); local x0, y0 = A.Position.X.Offset, A.Position.Y.Offset
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Left }, false)
	check(A.Position.X.Offset == x0 - 5, "sol ok: " .. A.Position.X.Offset)
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Up }, false)
	check(A.Position.Y.Offset == y0 - 5, "yukarı ok: " .. A.Position.Y.Offset)
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Down }, false)
	check(A.Position.Y.Offset == y0, "aşağı ok geri alır: " .. A.Position.Y.Offset)
end)

ok("ok tuşu: pencere odaktan çıkınca taşımaz", function()
	fire(WIDGET.WindowFocusReleased)
	sel({ A }); local x0 = A.Position.X.Offset
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Right }, false)
	check(A.Position.X.Offset == x0, "odak yokken ok taşımaz: " .. A.Position.X.Offset)
	fire(WIDGET.WindowFocused)
end)

ok("ok tuşu: metin kutusu odaktayken (kod yazarken) taşımaz", function()
	sel({ A }); local x0 = A.Position.X.Offset
	FOCUSED_TB = find("UT_Step")
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Right }, false)
	FOCUSED_TB = nil
	check(A.Position.X.Offset == x0, "metin kutusunda ok taşımaz: " .. A.Position.X.Offset)
end)

ok("ok tuşu: gameProcessed true ise (Studio kullandıysa) taşımaz", function()
	sel({ A }); local x0 = A.Position.X.Offset
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Right }, true)
	check(A.Position.X.Offset == x0, "gameProcessed'da taşımaz: " .. A.Position.X.Offset)
end)

ok("ok tuşu: klavye olmayan girdi ve widget kapalıyken taşımaz", function()
	sel({ A }); local x0 = A.Position.X.Offset
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.MouseButton1, KeyCode = Enum.KeyCode.Right }, false)
	check(A.Position.X.Offset == x0, "fare girdisi taşımaz")
	WIDGET.Enabled = false
	fire(INPUT_BEGAN, { UserInputType = Enum.UserInputType.Keyboard, KeyCode = Enum.KeyCode.Right }, false)
	check(A.Position.X.Offset == x0, "widget kapalıyken taşımaz")
	WIDGET.Enabled = true
end)


-- ---------------- v27: UILayout kartı ----------------
ok("yerleşim: dikey liste eklenir, tekrar tıklayınca ikinci eklenmez", function()
	local L1 = newInst("Frame"); L1.Name = "YL1"; L1.Parent = P
	sel({ L1 }); click("UT_Layout_list_v"); click("UT_Layout_list_v")
	local n, lay = 0, nil
	for _, c in ipairs(L1:GetChildren()) do if c.ClassName == "UIListLayout" then n = n + 1; lay = c end end
	check(n == 1, "UIListLayout tek kopya: " .. n)
	check(lay and lay.FillDirection == "FillDirection.Vertical", "dikey yön: " .. tostring(lay and lay.FillDirection))
	check(HISTORY[#HISTORY] == "UI Tools: yerleşim list_v", "geri alınabilir: " .. tostring(HISTORY[#HISTORY]))
	L1.Parent = nil
end)

ok("yerleşim: dolgu kutucuktan okunur (10 px)", function()
	local L2 = newInst("Frame"); L2.Name = "YL2"; L2.Parent = P
	sel({ L2 }); setText("UT_Layout_pad_v", "10"); click("UT_Layout_pad")
	local pad = L2:FindFirstChildOfClass("UIPadding")
	check(pad ~= nil, "UIPadding eklendi")
	check(pad and pad.PaddingLeft.Offset == 10 and pad.PaddingBottom.Offset == 10, "dolgu 10 px")
	L2.Parent = nil
end)

ok("yerleşim: köşe ve çerçeve değerleri uygulanır", function()
	local L3 = newInst("Frame"); L3.Name = "YL3"; L3.Parent = P
	sel({ L3 }); setText("UT_Layout_radius_v", "12"); click("UT_Layout_corner")
	setText("UT_Layout_stroke_v", "3"); click("UT_Layout_stroke")
	local c = L3:FindFirstChildOfClass("UICorner"); local st = L3:FindFirstChildOfClass("UIStroke")
	check(c and c.CornerRadius.Offset == 12, "köşe 12 px")
	check(st and st.Thickness == 3, "çerçeve 3 px")
	L3.Parent = nil
end)

ok("yerleşim: ızgara ve oran eklenir", function()
	local L4 = newInst("Frame"); L4.Name = "YL4"; L4.Parent = P
	sel({ L4 }); click("UT_Layout_grid"); click("UT_Layout_aspect")
	check(L4:FindFirstChildOfClass("UIGridLayout") ~= nil, "UIGridLayout eklendi")
	check(L4:FindFirstChildOfClass("UIAspectRatioConstraint") ~= nil, "UIAspectRatioConstraint eklendi")
	L4.Parent = nil
end)

ok("yerleşim kaldır: yerleşim/dolgu gider, köşe korunur", function()
	local L5 = newInst("Frame"); L5.Name = "YL5"; L5.Parent = P
	sel({ L5 }); click("UT_Layout_list_v"); click("UT_Layout_pad"); click("UT_Layout_corner")
	click("UT_Layout_clear")
	check(L5:FindFirstChildOfClass("UIListLayout") == nil and L5:FindFirstChildOfClass("UIPadding") == nil, "yerleşim ve dolgu kaldırıldı")
	check(L5:FindFirstChildOfClass("UICorner") ~= nil, "köşe tasarımda kalır")
	L5.Parent = nil
end)

ok("yerleşim: seçim yoksa uyarır", function()
	sel({})
	click("UT_Layout_list_h")
	check(statusText():find("UI öğesi seç") ~= nil, "uyarı: " .. statusText())
end)
if #fails == 0 then return "PLUGIN TESTLERİ GEÇTİ: " .. #results .. " kontrol" end
return "PLUGIN BAŞARISIZ (" .. #fails .. "):\n" .. table.concat(fails, "\n")
