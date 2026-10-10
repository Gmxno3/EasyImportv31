local Core = (function() local f = assert(load(__SRC.core)); return f() end)()
local fails, passes = {}, 0
local function eq(a, b, msg)
	if a == b then passes = passes + 1
	else fails[#fails + 1] = msg .. ": beklenen " .. tostring(b) .. ", bulunan " .. tostring(a) end
end
local function near(a, b, msg) eq(math.abs(a - b) < 1e-9, true, msg .. " (" .. tostring(a) .. " ~ " .. tostring(b) .. ")") end

-- Hizalama: seçim sınırına
local r = { {x=10,y=10,w=50,h=20}, {x=100,y=40,w=30,h=30} }
local p = Core.align(r, "left")
eq(p[1].x, 10, "sol: A") ; eq(p[2].x, 10, "sol: B")
p = Core.align(r, "right") -- sınır: 10..130
eq(p[1].x, 80, "sağ: A (130-50)") ; eq(p[2].x, 100, "sağ: B (130-30)")
p = Core.align(r, "top")
eq(p[1].y, 10, "üst: A") ; eq(p[2].y, 10, "üst: B")
p = Core.align(r, "bottom") -- sınır y: 10..70
eq(p[1].y, 50, "alt: A (70-20)") ; eq(p[2].y, 40, "alt: B (70-30)")
p = Core.align(r, "hcenter") -- sınır x: 10..130, merkez 70
near(p[1].x, 45, "yatay orta: A (10+(120-50)/2)") ; near(p[2].x, 55, "yatay orta: B (10+(120-30)/2)")
p = Core.align(r, "vcenter") -- sınır y: 10..70, merkez 40
near(p[1].y, 30, "dikey orta: A (40-10)") ; near(p[2].y, 25, "dikey orta: B (40-15)")

-- Üst öğe (container) hedefi
local c = {x=0,y=0,w=200,h=200}
p = Core.align({ {x=10,y=10,w=50,h=50} }, "hcenter", c)
eq(p[1].x, 75, "konteynere yatay orta (200-50)/2")
p = Core.align({ {x=10,y=10,w=50,h=50} }, "right", c)
eq(p[1].x, 150, "konteynere sağ")

-- Hatalı mod ve boş giriş
local bad, err = Core.align(r, "diagonal")
eq(bad, nil, "bilinmeyen mod nil döner"); eq(type(err), "string", "bilinmeyen mod hata metni")
eq(#Core.align({}, "left"), 0, "boş seçim")

-- Dağıtma (v22): uçlar sabit, aradakiler eşit boşluk
local dA, dB, dC = {x=0,y=0,w=10,h=10}, {x=50,y=0,w=10,h=10}, {x=200,y=0,w=10,h=10}
local dd = Core.distribute({ dA, dB, dC }, "h")
eq(dd[1].x, 0, "dağıt yatay: sol uç sabit")
eq(dd[3].x, 200, "dağıt yatay: sağ uç sabit")
near(dd[2].x, 100, "dağıt yatay: orta öğe (açıklık 210 - tüm boyutlar 30 = 180, boşluk 90 -> x=100)")
-- Girdi sırası karışık olsa da eşleşme doğru (indeks korunur)
local dd2 = Core.distribute({ dC, dA, dB }, "h")
eq(dd2[1].x, 200, "dağıt sıra karışık: C (ilk girdi) yerinde") ; eq(dd2[2].x, 0, "dağıt sıra karışık: A yerinde")
near(dd2[3].x, 100, "dağıt sıra karışık: B eşit aralıkta")
-- Dikey eksen, farklı boyutlar
local vA, vB, vC = {x=0,y=0,w=10,h=20}, {x=0,y=30,w=10,h=40}, {x=0,y=200,w=10,h=20}
local dv = Core.distribute({ vA, vB, vC }, "v")
near(dv[2].y, 90, "dağıt dikey: açıklık 220 - boyutlar 80 = 140, boşluk 70 -> B y=90")
eq(dv[3].y, 200, "dağıt dikey: alt uç sabit")
-- Hatalı girdi
local dbad, derr = Core.distribute({ dA, dB }, "h")
eq(dbad, nil, "dağıt: 2 öğe reddedilir") ; eq(type(derr), "string", "dağıt: hata metni")
local dbad2 = Core.distribute({ dA, dB, dC }, "x")
eq(dbad2, nil, "dağıt: bilinmeyen eksen reddedilir")

-- Izgara
eq(Core.roundToGrid(13.4, 1), 13, "snap 1px")
eq(Core.roundToGrid(13, 8), 16, "snap 8 (13/8=1.6 -> 2)")
eq(Core.roundToGrid(11, 8), 8, "snap 8 (11/8=1.4 -> 1)")
eq(Core.roundToGrid(-3.2, 1), -3, "snap negatif")
eq(Core.roundToGrid(7.7, 0), 7.7, "snap kapalı (step 0)")

-- Nudge
local n = Core.shiftRects({ {x=13,y=21,w=1,h=1} }, 1, -1, 8)
eq(n[1].x, 16, "nudge snap x (14->16)")
eq(n[1].y, 24, "nudge snap y (20/8=2.5 -> yukarı yuvarlanır -> 24)")
n = Core.shiftRects({ {x=13,y=21,w=1,h=1} }, 1, -1, 0)
eq(n[1].x, 14, "nudge serbest x") ; eq(n[1].y, 20, "nudge serbest y")

-- Scale dönüşümü
near(Core.toScale(50, 200), 0.25, "toScale 50/200")
near(Core.toPixels(0.25, 200), 50, "toPixels 0.25*200")
local px = 73.5
near(Core.toPixels(Core.toScale(px, 300), 300), px, "round-trip scale")
eq(Core.toScale(10, 0), nil, "parent 0 -> nil")

-- Sınıf değiştirme
local plan = Core.classChangePlan("Frame", "TextButton")
eq(type(plan), "table", "Frame->TextButton planı")
local hasBg = false ; for _, k in ipairs(plan.copy) do if k == "BackgroundColor3" then hasBg = true end end
eq(hasBg, true, "arka plan kopyalanır")
eq(#plan.dropped, 0, "Frame->TextButton hiçbir şey kaybetmez")
local hasAuto = false ; for _, k in ipairs(plan.gained) do if k == "AutoButtonColor" then hasAuto = true end end
eq(hasAuto, true, "TextButton yeni özellik kazanır")

plan = Core.classChangePlan("TextLabel", "Frame")
local textLost = false ; for _, w in ipairs(plan.warnings) do if w == "metin silinecek" then textLost = true end end
eq(textLost, true, "TextLabel->Frame metin uyarısı")

plan = Core.classChangePlan("ImageLabel", "ImageButton")
local imgKept = false ; for _, k in ipairs(plan.copy) do if k == "Image" then imgKept = true end end
eq(imgKept, true, "ImageLabel->ImageButton resim korunur")
eq(#plan.warnings, 0, "ImageLabel->ImageButton uyarı yok")

local pl, e1 = Core.classChangePlan("Frame", "Frame") ; eq(pl, nil, "aynı sınıf reddedilir")
pl, e1 = Core.classChangePlan("Frame", "UIListLayout") ; eq(pl, nil, "desteklenmeyen hedef reddedilir")
pl, e1 = Core.classChangePlan("UIListLayout", "Frame") ; eq(pl, nil, "desteklenmeyen kaynak reddedilir")

-- Her desteklenen sınıf çifti için plan üretilebilir ve kopya listesi boş değil
for _, a in ipairs(Core.CLASS_ORDER) do
	for _, b in ipairs(Core.CLASS_ORDER) do
		if a ~= b then
			local q = Core.classChangePlan(a, b)
			eq(q ~= nil and #q.copy > 0, true, "plan " .. a .. "->" .. b)
		end
	end
end

-- Kaydırıcı
eq(Core.sliderToValue(0, 1, 50, 1), 1, "slider başı = min")
eq(Core.sliderToValue(1, 1, 50, 1), 50, "slider sonu = max")
eq(Core.sliderToValue(0.5, 1, 50, 1), 26, "slider ortası adımlı (1+24.5 -> 26)")
eq(Core.sliderToValue(-3, 1, 50, 1), 1, "slider frac alt sınır")
eq(Core.sliderToValue(9, 1, 50, 1), 50, "slider frac üst sınır")
eq(Core.sliderToValue(0.37, 0, 10, 0), 3.7, "adımsız (step 0) ara değer")
near(Core.valueToFrac(1, 1, 50), 0, "valueToFrac min")
near(Core.valueToFrac(50, 1, 50), 1, "valueToFrac max")
near(Core.valueToFrac(25.5, 1, 50), 0.5, "valueToFrac orta")
eq(Core.formatValue(5), "5", "formatValue tam sayı")
eq(Core.formatValue(2.5), "2.5", "formatValue ondalık")
eq(Core.formatValue(2.0), "2", "formatValue sondaki sıfır")

if #fails == 0 then return "CORE TESTLERİ GEÇTİ: " .. passes .. " kontrol" end
return "CORE BAŞARISIZ (" .. #fails .. "):\n" .. table.concat(fails, "\n")
