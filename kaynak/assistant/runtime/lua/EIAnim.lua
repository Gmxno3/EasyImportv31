-- EasyImport · Animasyon üretici (A6-A8) — `runtime/js/ei-anim.js` YOK; bu modül tek kaynaktır.
--
-- Ne yapar: GUI ağacındaki öğeler için anim-library.json'dan (1) giriş (show), (2) hover,
-- (3) basma (press) animasyonu seçer ve bunları UI başına TEK bir LocalScript olarak üretir
-- (KARARLAR L1/L3: TweenService, ek modül yok). Spring yok (L2), UIShadow glow yok (L10).
--
-- Kapsam bilinçli olarak dar: fx (efekt) ve döngü (dongu) kategorileri ve FX tespiti HENÜZ
-- yok (DURUM §4). Bu yüzden yalnız giris / hover / basma üretilir.
--
-- Veri bloğu (ANIM_LIB, ANIM_IDS) `tools/build_anim_lua.py` tarafından anim-library.json'dan
-- üretilir. ELLE DÜZENLEMEYİN; kütüphane değişince betiği yeniden çalıştırın ve
-- `tools/verify_anim.py` ile senkronluğu doğrulayın.
--
-- Parite: `tools/verify_anim.py` seçimi bağımsız bir Python referansıyla karşılaştırır ve
-- üretilen LocalScript'i fengari'de (Lua 5.3) derleyip sahte Roblox ortamında koşturur.

local EIAnim = {}

local VERSION = "ei-anim-1"

-- <<EI_ANIM_DATA>>
local ANIM_IDS = {"attention_bell_ring", "attention_blink", "attention_bounce_big", "attention_ping", "attention_pulse_scale_big", "attention_shake_strong", "attention_wiggle", "attention_zoom_punch", "enter_bounce_drop", "enter_elastic_pop", "enter_fade", "enter_flip_in", "enter_grow_from_center", "enter_pop_scale", "enter_punch", "enter_reveal_showcase", "enter_rotate_in", "enter_scale_rotate", "enter_slide_down", "enter_slide_left", "enter_slide_right", "enter_slide_up", "enter_soft_scale", "enter_stagger_list", "enter_swing_door", "enter_zoom_in", "enter_zoom_out", "hover_bounce_small", "hover_brighten", "hover_glow", "hover_lift", "hover_rotate_tilt", "hover_scale_down", "hover_scale_up", "hover_shift_right", "hover_shine_sweep", "hover_stroke_grow", "hover_turn_card", "hover_wiggle_once", "loop_blink_cta", "loop_bobble", "loop_border_spin", "loop_breathe_transparency", "loop_color_cycle", "loop_expand_ring", "loop_float", "loop_gradient_sweep", "loop_pulse_scale", "loop_rotate_medium", "loop_rotate_reverse", "loop_rotate_slow", "loop_shake_slight", "loop_shimmer", "loop_wiggle_icon", "press_depress", "press_flash", "press_pop_scale", "press_punch", "press_ripple", "press_rotate_spin", "press_select_pop", "press_shake", "press_shrink_bounce", "press_shrink_only", "press_squash", "select_outline_pop"}
local ANIM_LIB = {
	["attention_bell_ring"] = {
		cat = "dikkat", trig = "event",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"badge", "icon", "notification"},
		beauty = 4,
		tracks = {
			{d = 0.13, dl = 0, e = "Sine", ed = "InOut", from = -18, p = "Rotation", rep = 5, rev = true, t = "self", to = 18},
		},
	},
	["attention_blink"] = {
		cat = "dikkat", trig = "event",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextLabel"},
		roles = {"badge", "bar", "value"},
		beauty = 2,
		tracks = {
			{d = 0.15, dl = 0, e = "Linear", ed = "InOut", from = 0, p = "ImageTransparency", rep = 2, rev = true, t = "self", to = 1},
		},
	},
	["attention_bounce_big"] = {
		cat = "dikkat", trig = "event",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"badge", "currency", "icon", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.45, dl = 0, e = "Back", ed = "Out", from = 1, p = "Scale", rep = 1, rev = true, t = "UIScale", to = 1.25},
		},
	},
	["attention_ping"] = {
		cat = "dikkat", trig = "event",
		cls = {"ImageLabel"},
		roles = {"badge", "icon"},
		beauty = 4,
		tracks = {
			{d = 0.9, dl = 0, e = "Quart", ed = "Out", from = 0.5, p = "Scale", rep = 2, rev = false, t = "UIScale", to = 2},
			{d = 0.9, dl = 0, e = "Quad", ed = "Out", from = 0, p = "ImageTransparency", rep = 2, rev = false, t = "self", to = 1},
		},
	},
	["attention_pulse_scale_big"] = {
		cat = "dikkat", trig = "event",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"claim", "primary-button", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.6, dl = 0, e = "Sine", ed = "InOut", from = 1, p = "Scale", rep = -1, rev = true, t = "UIScale", to = 1.16},
		},
	},
	["attention_shake_strong"] = {
		cat = "dikkat", trig = "event",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextLabel"},
		roles = {"badge", "button", "icon", "value"},
		beauty = 2,
		tracks = {
			{d = 0.075, dl = 0, e = "Sine", ed = "InOut", from = -9, p = "Rotation", rep = 5, rev = true, t = "self", to = 9},
		},
	},
	["attention_wiggle"] = {
		cat = "dikkat", trig = "event",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"icon", "reward", "slot"},
		beauty = 4,
		tracks = {
			{d = 0.1, dl = 0, e = "Sine", ed = "InOut", from = -12, p = "Rotation", rep = 2, rev = true, t = "self", to = 12},
			{d = 0.3, dl = 0, e = "Back", ed = "Out", from = 1, p = "Scale", rep = 1, rev = true, t = "UIScale", to = 1.08},
		},
	},
	["attention_zoom_punch"] = {
		cat = "dikkat", trig = "event",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextLabel"},
		roles = {"reward", "title", "value"},
		beauty = 4,
		tracks = {
			{d = 0.4, dl = 0, e = "Exponential", ed = "Out", from = 1.35, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["enter_bounce_drop"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageButton", "ImageLabel"},
		roles = {"card", "modal", "panel", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.75, dl = 0, e = "Bounce", ed = "Out", from = {0, -180}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
		},
	},
	["enter_elastic_pop"] = {
		cat = "giris", trig = "show",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "primary-button", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.7, dl = 0, e = "Elastic", ed = "Out", from = 0.2, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["enter_fade"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageButton", "ImageLabel", "ScrollingFrame", "TextButton", "TextLabel"},
		roles = {"background", "label", "modal", "panel"},
		beauty = 2,
		tracks = {
			{d = 0.3, dl = 0, e = "Sine", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_flip_in"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"card", "panel"},
		beauty = 4,
		tracks = {
			{d = 0.55, dl = 0, e = "Quart", ed = "Out", from = 0.05, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["enter_grow_from_center"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"modal", "panel", "tooltip"},
		beauty = 3,
		tracks = {
			{d = 0.32, dl = 0, e = "Cubic", ed = "Out", from = 0.8, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.24, dl = 0, e = "Sine", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_pop_scale"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageButton", "ImageLabel", "TextButton", "TextLabel"},
		roles = {"button", "card", "icon", "modal", "panel"},
		beauty = 3,
		tracks = {
			{d = 0.35, dl = 0, e = "Back", ed = "Out", from = 0.6, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.2, dl = 0, e = "Quad", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_punch"] = {
		cat = "giris", trig = "show",
		cls = {"ImageButton", "ImageLabel", "TextButton", "TextLabel"},
		roles = {"button", "title", "value"},
		beauty = 3,
		tracks = {
			{d = 0.25, dl = 0, e = "Quint", ed = "Out", from = 1.3, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["enter_reveal_showcase"] = {
		cat = "giris", trig = "show",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton", "TextLabel"},
		roles = {"button", "card", "icon", "modal", "panel"},
		beauty = 4,
		tracks = {
			{d = 0.45, dl = 0, e = "Back", ed = "Out", from = 0.5, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.45, dl = 0, e = "Quad", ed = "Out", from = -6, p = "Rotation", rep = 0, rev = false, t = "self", to = 0},
			{d = 0.25, dl = 0, e = "Quad", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_rotate_in"] = {
		cat = "giris", trig = "show",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"badge", "card", "icon", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.45, dl = 0, e = "Back", ed = "Out", from = -28, p = "Rotation", rep = 0, rev = false, t = "self", to = 0},
			{d = 0.35, dl = 0, e = "Back", ed = "Out", from = 0.5, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.2, dl = 0, e = "Quad", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_scale_rotate"] = {
		cat = "giris", trig = "show",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"badge", "card", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.5, dl = 0, e = "Back", ed = "Out", from = 0.4, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.5, dl = 0, e = "Quart", ed = "Out", from = 180, p = "Rotation", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_slide_down"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"modal", "panel", "tooltip"},
		beauty = 3,
		tracks = {
			{d = 0.4, dl = 0, e = "Quart", ed = "Out", from = {0, -40}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
			{d = 0.3, dl = 0, e = "Quad", ed = "Out", from = 0.6, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_slide_left"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"card", "panel", "sidebar"},
		beauty = 3,
		tracks = {
			{d = 0.38, dl = 0, e = "Quart", ed = "Out", from = {-60, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
			{d = 0.28, dl = 0, e = "Quad", ed = "Out", from = 0.5, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_slide_right"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"card", "panel", "sidebar"},
		beauty = 3,
		tracks = {
			{d = 0.38, dl = 0, e = "Quart", ed = "Out", from = {60, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
			{d = 0.28, dl = 0, e = "Quad", ed = "Out", from = 0.5, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_slide_up"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel", "ScrollingFrame", "TextButton"},
		roles = {"card", "list", "modal", "panel"},
		beauty = 3,
		tracks = {
			{d = 0.4, dl = 0, e = "Quart", ed = "Out", from = {0, 40}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
			{d = 0.3, dl = 0, e = "Quad", ed = "Out", from = 0.6, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_soft_scale"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel", "ScrollingFrame", "TextLabel"},
		roles = {"background", "label", "panel"},
		beauty = 3,
		tracks = {
			{d = 0.28, dl = 0, e = "Sine", ed = "Out", from = 0.94, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.24, dl = 0, e = "Sine", ed = "Out", from = 0.5, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_stagger_list"] = {
		cat = "giris", trig = "show",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton"},
		roles = {"card", "list", "slot"},
		beauty = 4,
		tracks = {
			{d = 0.25, dl = 0, e = "Quad", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
			{d = 0.3, dl = 0, e = "Back", ed = "Out", from = 0.85, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["enter_swing_door"] = {
		cat = "giris", trig = "show",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "card", "icon", "panel"},
		beauty = 4,
		tracks = {
			{d = 0.4, dl = 0, e = "Back", ed = "Out", from = 0.6, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.6, dl = 0, e = "Elastic", ed = "Out", from = 14, p = "Rotation", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_zoom_in"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageLabel"},
		roles = {"modal", "panel"},
		beauty = 3,
		tracks = {
			{d = 0.36, dl = 0, e = "Quint", ed = "Out", from = 0.35, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.22, dl = 0, e = "Quad", ed = "Out", from = 0.8, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["enter_zoom_out"] = {
		cat = "giris", trig = "show",
		cls = {"CanvasGroup", "Frame", "ImageButton", "ImageLabel"},
		roles = {"modal", "panel", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.42, dl = 0, e = "Quart", ed = "Out", from = 1.35, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
			{d = 0.25, dl = 0, e = "Sine", ed = "Out", from = 1, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["hover_bounce_small"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"currency", "icon-button", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.28, dl = 0, e = "Back", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.1},
		},
	},
	["hover_brighten"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"Frame", "ImageLabel", "TextButton"},
		roles = {"button", "slot", "tab"},
		beauty = 3,
		tracks = {
			{d = 0.13, dl = 0, e = "Sine", ed = "Out", from = 0, p = "BackgroundTransparency", rep = 0, rev = false, t = "self", to = 0.15},
		},
	},
	["hover_glow"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "icon", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.14, dl = 0, e = "Sine", ed = "Out", from = 0.15, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0},
		},
	},
	["hover_lift"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "card", "slot"},
		beauty = 4,
		tracks = {
			{d = 0.15, dl = 0, e = "Quint", ed = "Out", from = {0, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {0, -3}},
		},
	},
	["hover_rotate_tilt"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"card", "icon-button", "reward"},
		beauty = 3,
		tracks = {
			{d = 0.15, dl = 0, e = "Back", ed = "Out", from = 0, p = "Rotation", rep = 0, rev = false, t = "self", to = 4},
		},
	},
	["hover_scale_down"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "close-button", "icon-button"},
		beauty = 2,
		tracks = {
			{d = 0.12, dl = 0, e = "Quint", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 0.95},
		},
	},
	["hover_scale_up"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "card", "icon-button", "primary-button"},
		beauty = 3,
		tracks = {
			{d = 0.12, dl = 0, e = "Quint", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.06},
		},
	},
	["hover_shift_right"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "TextButton", "TextLabel"},
		roles = {"button", "list", "tab"},
		beauty = 3,
		tracks = {
			{d = 0.14, dl = 0, e = "Quint", ed = "Out", from = {0, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {4, 0}},
		},
	},
	["hover_shine_sweep"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"card", "primary-button", "reward"},
		beauty = 5,
		tracks = {
			{d = 0.55, dl = 0, e = "Circular", ed = "InOut", from = {-1.2, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {1.2, 0}},
			{d = 0.55, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 0.9},
		},
	},
	["hover_stroke_grow"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"Frame", "ImageButton", "TextButton"},
		roles = {"button", "card", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.14, dl = 0, e = "Quint", ed = "Out", from = 3, p = "Thickness", rep = 0, rev = false, t = "UIStroke", to = 5},
		},
	},
	["hover_turn_card"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"Frame", "ImageButton", "TextButton"},
		roles = {"button", "card", "icon"},
		beauty = 4,
		tracks = {
			{d = 0.25, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "Rotation", rep = 0, rev = false, t = "self", to = -5},
		},
	},
	["hover_wiggle_once"] = {
		cat = "hover", trig = "mouseEnter",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "card", "icon"},
		beauty = 3,
		tracks = {
			{d = 0.08, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "Rotation", rep = 1, rev = true, t = "self", to = -4},
		},
	},
	["loop_blink_cta"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageButton", "ImageLabel", "TextButton", "TextLabel"},
		roles = {"primary-button"},
		beauty = 5,
		tracks = {
			{d = 0.6, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "ImageTransparency", rep = -1, rev = true, t = "self", to = 0.7},
			{d = 0.6, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "TextTransparency", rep = -1, rev = true, t = "self", to = 0.7},
		},
	},
	["loop_bobble"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"badge", "icon", "reward"},
		beauty = 3,
		tracks = {
			{d = 1, dl = 0, e = "Sine", ed = "InOut", from = -7, p = "Rotation", rep = -1, rev = true, t = "self", to = 7},
		},
	},
	["loop_border_spin"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "card", "icon", "modal", "panel", "primary-button", "slot", "tab"},
		beauty = 4,
		tracks = {
			{d = 2.5, dl = 0, e = "Linear", ed = "In", from = 0, p = "Rotation", rep = -1, rev = false, t = "UIGradient", to = 360},
		},
	},
	["loop_breathe_transparency"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageLabel", "TextLabel"},
		roles = {"background", "icon", "label"},
		beauty = 3,
		tracks = {
			{d = 1.2, dl = 0, e = "Sine", ed = "InOut", from = 0.25, p = "ImageTransparency", rep = -1, rev = true, t = "self", to = 0.6},
		},
	},
	["loop_color_cycle"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageLabel", "TextLabel"},
		roles = {"badge", "reward", "title", "value"},
		beauty = 4,
		tracks = {
			{d = 3, dl = 0, e = "Linear", ed = "InOut", from = 0, p = "Rotation", rep = -1, rev = false, t = "UIGradient", to = 360},
		},
	},
	["loop_expand_ring"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageLabel"},
		roles = {"icon"},
		beauty = 4,
		tracks = {
			{d = 1.8, dl = 0, e = "Sine", ed = "Out", from = 0.7, p = "Scale", rep = -1, rev = false, t = "UIScale", to = 1.4},
			{d = 1.8, dl = 0, e = "Sine", ed = "In", from = 0.1, p = "ImageTransparency", rep = -1, rev = false, t = "self", to = 1},
		},
	},
	["loop_float"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"badge", "card", "icon", "reward"},
		beauty = 4,
		tracks = {
			{d = 1.5, dl = 0, e = "Sine", ed = "InOut", from = {0, -5}, p = "Position", rep = -1, rev = true, t = "self", to = {0, 5}},
		},
	},
	["loop_gradient_sweep"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageLabel"},
		roles = {"background", "bar", "panel"},
		beauty = 4,
		tracks = {
			{d = 2, dl = 0, e = "Sine", ed = "InOut", from = {0, -0.8}, p = "Offset", rep = -1, rev = true, t = "UIGradient", to = {0, 0.8}},
		},
	},
	["loop_pulse_scale"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "icon", "primary-button", "reward"},
		beauty = 3,
		tracks = {
			{d = 0.8, dl = 0, e = "Sine", ed = "InOut", from = 1, p = "Scale", rep = -1, rev = true, t = "UIScale", to = 1.05},
		},
	},
	["loop_rotate_medium"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageLabel"},
		roles = {"icon", "loading"},
		beauty = 3,
		tracks = {
			{d = 4, dl = 0, e = "Linear", ed = "InOut", from = 0, p = "Rotation", rep = -1, rev = false, t = "self", to = 360},
		},
	},
	["loop_rotate_reverse"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageLabel"},
		roles = {"icon"},
		beauty = 3,
		tracks = {
			{d = 9, dl = 0, e = "Linear", ed = "InOut", from = 360, p = "Rotation", rep = -1, rev = false, t = "self", to = 0},
		},
	},
	["loop_rotate_slow"] = {
		cat = "dongu", trig = "always",
		cls = {"ImageLabel"},
		roles = {"icon", "loading"},
		beauty = 4,
		tracks = {
			{d = 12, dl = 0, e = "Linear", ed = "InOut", from = 0, p = "Rotation", rep = -1, rev = false, t = "self", to = 360},
		},
	},
	["loop_shake_slight"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageButton", "ImageLabel"},
		roles = {"badge", "icon"},
		beauty = 2,
		tracks = {
			{d = 0.1, dl = 0, e = "Sine", ed = "InOut", from = -2, p = "Rotation", rep = -1, rev = true, t = "self", to = 2},
		},
	},
	["loop_shimmer"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageLabel", "TextButton", "TextLabel"},
		roles = {"currency", "primary-button", "reward", "title"},
		beauty = 5,
		tracks = {
			{d = 2.2, dl = 0, e = "Sine", ed = "InOut", from = {-1.2, 0}, p = "Offset", rep = -1, rev = false, t = "UIGradient", to = {1.2, 0}},
		},
	},
	["loop_wiggle_icon"] = {
		cat = "dongu", trig = "always",
		cls = {"Frame", "ImageButton", "ImageLabel", "TextButton"},
		roles = {"icon"},
		beauty = 6,
		tracks = {
			{d = 0.25, dl = 0, e = "Sine", ed = "InOut", from = 0, p = "Rotation", rep = -1, rev = true, t = "self", to = -6},
		},
	},
	["press_depress"] = {
		cat = "basma", trig = "mouseDown",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "primary-button"},
		beauty = 3,
		tracks = {
			{d = 0.08, dl = 0, e = "Quad", ed = "Out", from = {0, 0}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 2}},
			{d = 0.16, dl = 0.1, e = "Back", ed = "Out", from = {0, 2}, p = "Position", rep = 0, rev = false, t = "self", to = {0, 0}},
		},
	},
	["press_flash"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.08, dl = 0, e = "Quad", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 0.94},
			{d = 0.17, dl = 0.08, e = "Back", ed = "Out", from = 0.94, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["press_pop_scale"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "ImageLabel", "TextButton"},
		roles = {"button", "currency", "reward"},
		beauty = 4,
		tracks = {
			{d = 0.12, dl = 0, e = "Quint", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.15},
			{d = 0.22, dl = 0.12, e = "Back", ed = "Out", from = 1.15, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["press_punch"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.06, dl = 0, e = "Quad", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 0.85},
			{d = 0.2, dl = 0.06, e = "Exponential", ed = "Out", from = 0.85, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["press_ripple"] = {
		cat = "basma", trig = "click",
		cls = {"ImageLabel"},
		roles = {"button", "ripple"},
		beauty = 5,
		tracks = {
			{d = 0.5, dl = 0, e = "Quart", ed = "Out", from = 0.1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.8},
			{d = 0.5, dl = 0, e = "Quad", ed = "Out", from = 0.4, p = "ImageTransparency", rep = 0, rev = false, t = "self", to = 1},
		},
	},
	["press_rotate_spin"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"close-button", "icon-button", "settings"},
		beauty = 3,
		tracks = {
			{d = 0.4, dl = 0, e = "Quart", ed = "InOut", from = 0, p = "Rotation", rep = 0, rev = false, t = "self", to = 360},
		},
	},
	["press_select_pop"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "icon-button", "primary-button"},
		beauty = 3,
		tracks = {
			{d = 0.12, dl = 0, e = "Back", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.05},
			{d = 0.2, dl = 0.12, e = "Quad", ed = "Out", from = 1.05, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["press_shake"] = {
		cat = "basma", trig = "click",
		cls = {"Frame", "ImageButton", "TextButton"},
		roles = {"button", "close-button", "slot"},
		beauty = 3,
		tracks = {
			{d = 0.08, dl = 0, e = "Sine", ed = "InOut", from = -5, p = "Rotation", rep = 3, rev = true, t = "self", to = 5},
		},
	},
	["press_shrink_bounce"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "close-button", "icon-button", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.08, dl = 0, e = "Quad", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 0.9},
			{d = 0.22, dl = 0.08, e = "Back", ed = "Out", from = 0.9, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["press_shrink_only"] = {
		cat = "basma", trig = "mouseDown",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "close-button"},
		beauty = 2,
		tracks = {
			{d = 0.1, dl = 0, e = "Quint", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 0.93},
		},
	},
	["press_squash"] = {
		cat = "basma", trig = "click",
		cls = {"ImageButton", "ImageLabel"},
		roles = {"button", "primary-button"},
		beauty = 4,
		tracks = {
			{d = 0.1, dl = 0, e = "Quint", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.12},
			{d = 0.09, dl = 0.1, e = "Sine", ed = "InOut", from = -4, p = "Rotation", rep = 1, rev = true, t = "self", to = 4},
			{d = 0.2, dl = 0.18, e = "Back", ed = "Out", from = 1.12, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1},
		},
	},
	["select_outline_pop"] = {
		cat = "secim", trig = "stateChange",
		cls = {"ImageButton", "TextButton"},
		roles = {"button", "card", "slot", "tab"},
		beauty = 4,
		tracks = {
			{d = 0.2, dl = 0, e = "Quad", ed = "Out", from = 0, p = "Thickness", rep = 0, rev = false, t = "UIStroke", to = 3},
			{d = 0.2, dl = 0, e = "Back", ed = "Out", from = 1, p = "Scale", rep = 0, rev = false, t = "UIScale", to = 1.03},
		},
	},
}
-- <<END_EI_ANIM_DATA>>

-- Stil öncülleri (DURUM §4 animBias): yalnız kullanılan kategoriler için. anime'nin fx/döngü
-- öncülleri bu kapsamda kullanılmıyor (fx/döngü üretilmiyor).
local STYLE_BIAS = {
	cartoon = { basma = 1.3 },
}

local function lower(s)
	return string.lower(tostring(s or ""))
end

local function containsAny(s, words)
	for _, w in ipairs(words) do
		if string.find(s, w, 1, true) then return true end
	end
	return false
end

local function listHas(list, value)
	for _, v in ipairs(list) do
		if v == value then return true end
	end
	return false
end

-- Rol çıkarımı (ad sinyali + sınıf). Kural sırası Python referansıyla BİREBİR aynıdır.
function EIAnim.roleOf(el)
	local n = lower(el.name)
	local c = el.cls
	if c == "TextButton" or c == "ImageButton" then
		if containsAny(n, { "close", "kapat" }) or string.sub(n, -2) == "_x" then return "close-button" end
		if containsAny(n, { "primary" }) then return "primary-button" end
		if containsAny(n, { "icon" }) then return "icon-button" end
		return "button"
	end
	if containsAny(n, { "card" }) then return "card" end
	if containsAny(n, { "modal", "popup" }) then return "modal" end
	if containsAny(n, { "title", "baslik" }) then return "title" end
	if containsAny(n, { "icon", "ikon" }) then return "icon" end
	if containsAny(n, { "tab" }) then return "tab" end
	if containsAny(n, { "panel", "frame" }) then return "panel" end
	if c == "TextLabel" then return "label" end
	if c == "ImageLabel" then return "icon" end
	return "panel"
end

-- Statik aday sırası: önce (kategori + sınıf + rol), yoksa (kategori + sınıf). Sıra: skor ↓ (beauty × stil
-- öncülü), eşitlikte id ↑. Öğrenme YOKKEN seçim budur (v10 davranışı, bayt-birebir).
local function staticCandidates(cat, cls, role, style)
	local bias = (STYLE_BIAS[style] and STYLE_BIAS[style][cat]) or 1
	for pass = 1, 2 do
		local list = {}
		for _, id in ipairs(ANIM_IDS) do
			local a = ANIM_LIB[id]
			if a.cat == cat and listHas(a.cls, cls) and (pass == 2 or listHas(a.roles, role)) then
				list[#list + 1] = id
			end
		end
		if #list > 0 then
			table.sort(list, function(x, y)
				local sx, sy = ANIM_LIB[x].beauty * bias, ANIM_LIB[y].beauty * bias
				if sx ~= sy then return sx > sy end
				return x < y
			end)
			return list
		end
	end
	return {}
end

-- Bağlamdaki toplam gözlem (kabul + ret). Gözlem yoksa statik sıra geçerlidir.
local function learnedObs(learn, ctx)
	local m = learn and learn.anim and learn.anim[ctx]
	if not m then return 0 end
	local t = 0
	for _, e in pairs(m) do t = t + e[1] + e[2] end
	return t
end

-- Seçici için sıralı seçenekler (ilk = varsayılan). learn verilmişse ve bağlamda gözlem varsa
-- EILearn.rankAnim sırası kullanılır (kabul görenler öne, reddedilenler sona).
function EIAnim.options(cls, role, cat, style, learn)
	local list = staticCandidates(cat, cls, role, style)
	if learn and #list > 0 then
		local ctx = EILearn.ctxKey(style, cls, role, cat)
		if learnedObs(learn, ctx) > 0 then
			list = EILearn.rankAnim(learn, ctx, list)
		end
	end
	return list
end

local function pickAnim(cat, cls, role, style, learn)
	local list = EIAnim.options(cls, role, cat, style, learn)
	return list[1]
end
EIAnim.pickAnim = pickAnim

-- elements: { {id=<sayı>, name=<metin>, cls=<Roblox sınıfı>, depth=<1 = ScreenGui'nin doğrudan çocuğu>}, ... }
-- Dönüş: bağlama listesi { {id, cls, role, show?, hover?, press?}, ... }
--   show  → yalnız depth <= 1 öğelere (üst düzey panel/kart/buton)
--   hover, press → yalnız buton sınıfları (TextButton / ImageButton)
function EIAnim.plan(elements, style, learn)
	local out = {}
	for _, el in ipairs(elements) do
		local role = EIAnim.roleOf(el)
		local isBtn = (el.cls == "TextButton" or el.cls == "ImageButton")
		local b = { id = el.id, cls = el.cls, role = role }
		if el.depth <= 1 then
			b.show = pickAnim("giris", el.cls, role, style, learn)
		end
		if isBtn then
			b.hover = pickAnim("hover", el.cls, role, style, learn)
			b.press = pickAnim("basma", el.cls, role, style, learn)
		end
		if b.show or b.hover or b.press then
			out[#out + 1] = b
		end
	end
	return out
end

-- ---------------------------------------------------------------- Lua literal yazıcı
local LUA_KW = {}
for _, w in ipairs({ "and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if",
	"in", "local", "nil", "not", "or", "repeat", "return", "then", "true", "until", "while" }) do
	LUA_KW[w] = true
end

local function lit(v)
	local t = type(v)
	if t == "number" then
		return string.format("%.6g", v)
	elseif t == "boolean" then
		return tostring(v)
	elseif t == "string" then
		-- Kaçış: ters eğik çizgi, tırnak, satır sonu
		local e = string.gsub(v, "\\", "\\\\")
		e = string.gsub(e, '"', '\\"')
		e = string.gsub(e, "\n", "\\n")
		return '"' .. e .. '"'
	elseif t == "table" then
		if v[1] ~= nil then
			local parts = {}
			for _, x in ipairs(v) do parts[#parts + 1] = lit(x) end
			return "{" .. table.concat(parts, ", ") .. "}"
		end
		local keys = {}
		for k in pairs(v) do keys[#keys + 1] = k end
		table.sort(keys)
		local parts = {}
		for _, k in ipairs(keys) do
			local kk = (LUA_KW[k] or not string.find(k, "^[%a_][%w_]*$")) and ('["' .. k .. '"]') or k
			parts[#parts + 1] = kk .. " = " .. lit(v[k])
		end
		return "{" .. table.concat(parts, ", ") .. "}"
	end
	error("desteklenmeyen tür: " .. t)
end
EIAnim.lit = lit

-- ---------------------------------------------------------------- LocalScript üretici
local TEMPLATE = [==[
-- EasyImport animasyon (otomatik üretildi — istersen düzenle).
-- UI başına tek LocalScript (KARARLAR L3). Motor: TweenService (L1). UIShadow glow yok (L10).
local TweenService = game:GetService("TweenService")
local root = script.Parent
local ANIMS = __ANIMS__
local BINDINGS = __BINDINGS__
local ACTIONS = __ACTIONS__
local PANEL_IDS = __PANELS__
local GROUP_IDS = __GROUPS__

-- BASE: hover/seçim öncesi değer. Çıkış (leave) animasyonu buraya döner.
local BASE = {}
local function baseOf(o, p)
	BASE[o] = BASE[o] or {}
	if BASE[o][p] == nil then
		local ok, v = pcall(function() return o[p] end)
		if ok then BASE[o][p] = v end
	end
	return BASE[o][p]
end

local function holder(inst, t)
	if t == "self" then return inst end
	if t == "parent" then return inst.Parent end
	local found = inst:FindFirstChildOfClass(t)
	if found then return found end
	if t == "UIScale" then
		local s = Instance.new("UIScale")
		s.Parent = inst
		return s
	end
	if t == "UIStroke" then
		local s = Instance.new("UIStroke")
		s.Thickness = 0
		s.Color = Color3.new(1, 1, 1)
		s.Parent = inst
		return s
	end
	if t == "UIGradient" then
		-- Kenarlık gradyanı: önce kenarlığın (UIStroke) içindeki gradyan; yoksa kenarlık ve beyaz gradyan oluşturulur.
		local st = inst:FindFirstChildOfClass("UIStroke")
		if not st then
			st = Instance.new("UIStroke")
			st.Thickness = 2
			st.Color = Color3.new(1, 1, 1)
			st.Parent = inst
		end
		local g = st:FindFirstChildOfClass("UIGradient")
		if not g then
			g = Instance.new("UIGradient")
			g.Parent = st
		end
		return g
	end
	return nil
end

local function delayOf(dl, extra)
	local base
	if type(dl) == "table" then
		base = dl.a + math.random() * (dl.b - dl.a)
	else
		base = dl or 0
	end
	return base + (extra or 0)
end

-- İki elemanlı değerler: Position/Size → UDim2 (piksel ofseti), diğerleri (UIGradient.Offset) → Vector2.
local function toValue(p, v)
	if type(v) == "table" then
		if p == "Position" or p == "Size" then
			return UDim2.fromOffset(v[1], v[2])
		end
		return Vector2.new(v[1], v[2])
	end
	return v
end

-- mode: "show" (from'a set, to'ya tween) · "loop" (aynı, sürekli) · "hover"/"press" (mevcut → to)
--       · "leave" (BASE'e tween)
local function play(inst, animId, mode, extra)
	local anim = ANIMS[animId]
	if not anim or not inst then return end
	for _, tr in ipairs(anim.tracks) do
		pcall(function()
			local o = holder(inst, tr.t)
			if not o then return end
			local base = baseOf(o, tr.p)
			local goal
			if mode == "leave" then
				goal = base
			else
				goal = tr.to
				if goal == "cur" or goal == nil then goal = base end
			end
			if goal == nil then return end
			goal = toValue(tr.p, goal)
			if (mode == "show" or mode == "loop") and tr.from ~= nil and tr.from ~= "cur" then
				o[tr.p] = toValue(tr.p, tr.from)
			end
			local info = TweenInfo.new(tr.d, Enum.EasingStyle[tr.e], Enum.EasingDirection[tr.ed], tr.rep, tr.rev, delayOf(tr.dl, extra))
			TweenService:Create(o, info, { [tr.p] = goal }):Play()
		end)
	end
end

-- Pivot: AnchorPoint (0,0) → (0.5,0.5); konum, sol-üst köşe aynı kalacak şekilde düzeltilir.
-- Layout (UIListLayout/UIGridLayout) yöneten kapta konum değiştirilmez.
local function centerPivot(inst)
	if not inst:IsA("GuiObject") then return end
	if inst.AnchorPoint ~= Vector2.new(0, 0) then return end
	local p = inst.Parent
	if p and (p:FindFirstChildWhichIsA("UIListLayout") or p:FindFirstChildWhichIsA("UIGridLayout")) then return end
	local s, pos = inst.Size, inst.Position
	inst.Position = UDim2.new(pos.X.Scale + s.X.Scale * 0.5, pos.X.Offset + s.X.Offset * 0.5,
		pos.Y.Scale + s.Y.Scale * 0.5, pos.Y.Offset + s.Y.Offset * 0.5)
	inst.AnchorPoint = Vector2.new(0.5, 0.5)
end

local function findById(id)
	for _, d in ipairs(root:GetDescendants()) do
		if d:GetAttribute("EI_Id") == id then return d end
	end
	return nil
end

-- Seçim grupları (kalıcı _select): grup anahtarı → üyeler {inst, a}; seçili üye grup başına tek.
local SELREG = {}
local SELSTATE = {}

local function selectClick(key, entry)
	local cur = SELSTATE[key]
	if cur == entry then
		play(entry.inst, entry.a, "leave")
		SELSTATE[key] = nil
		return
	end
	if cur then play(cur.inst, cur.a, "leave") end
	play(entry.inst, entry.a, "hover")
	SELSTATE[key] = entry
end

-- ================================================================ EFEKTLER (kendi öğeleriyle, arka planda, parametreli)
-- Framewisp "Effect Playground" benzeri: her efektin ayarları (kaydırıcılar) katmanda saklanır ve JSON ile gelir.
-- Varsayılanlar aşağıda; JSON'da params tablosu varsa o değerler kullanılır.
local FX_DEFAULTS = {
	fall = { count = 12, seconds = 6, fade = 0.75, smallest = 0.6, largest = 1.0 },
	burst = { count = 10, fade = 0.7, distance = 0.8 },
	orbit = { count = 3, seconds = 4 },
	twinkle = { count = 6, seconds = 0.6, smallest = 0.6, largest = 1.0 },
	orb = { scale = 1.7, pulse = 1.12 },
	smooth = { hover = 1.08, press = 0.9 },
	gleam = { sweep = 3, pause = 1, width = 0.22 },
}
local function fxParam(params, kind, key)
	local v = params and params[key]
	if type(v) == "number" then return v end
	return FX_DEFAULTS[kind][key]
end

local FX_GOLD = { Color3.fromRGB(255, 205, 70), Color3.fromRGB(255, 225, 120), Color3.fromRGB(230, 170, 40) }
local FX_CONFETTI = { Color3.fromRGB(255, 90, 90), Color3.fromRGB(90, 200, 255), Color3.fromRGB(120, 255, 140),
	Color3.fromRGB(255, 220, 80), Color3.fromRGB(190, 120, 255) }

-- Kopyalanacak şablonların listesi (tasarım öğeleri + Figma panelinden yüklenen resimler). Yoksa nil.
local function fxTemplate(inst)
	local list = {}
	for _, c in ipairs(inst:GetChildren()) do
		if c:GetAttribute("EI_FxTpl") then list[#list + 1] = c end
	end
	if #list == 0 then return nil end
	return list
end

local function fxLayer(inst)
	local w, h = 200, 120
	local ok, sz = pcall(function() return inst.AbsoluteSize end)
	if ok and sz and sz.X > 0 and sz.Y > 0 then w, h = sz.X, sz.Y end
	local layer = inst:FindFirstChild("EI_FX")
	if not layer then
		layer = Instance.new("Frame")
		layer.Name = "EI_FX"
		layer.BackgroundTransparency = 1
		layer.BorderSizePixel = 0
		layer.Size = UDim2.new(1, 0, 1, 0)
		layer.ClipsDescendants = true
		layer.ZIndex = 0
		layer.Parent = inst
	end
	return layer, w, h
end

-- Tek parça: şablonun kopyası (tasarım öğesi) ya da yedek renkli kare. Her parçada UIScale vardır.
local function fxSpawn(tpl, layer, w, h, color, smin, smax)
	local p
	if type(tpl) == "table" then tpl = tpl[math.random(#tpl)] end -- birden çok şablon: her parça rastgele birini kopyalar
	if tpl then
		local ok, c = pcall(function() return tpl:Clone() end)
		if ok and c then p = c end
	end
	if not p then
		p = Instance.new("Frame")
		p.BorderSizePixel = 0
		p.BackgroundColor3 = color
		p.Size = UDim2.fromOffset(math.max(4, math.floor(w * 0.06)), math.max(4, math.floor(w * 0.06)))
		local c = Instance.new("UICorner")
		c.CornerRadius = UDim.new(1, 0)
		c.Parent = p
	end
	p.Visible = true
	p.AnchorPoint = Vector2.new(0.5, 0.5)
	p.ZIndex = 0
	local sc = Instance.new("UIScale")
	sc.Scale = smin + math.random() * (smax - smin)
	sc.Parent = p
	p.Parent = layer
	return p
end

local function fxTween(o, d, style, dir, rep, rev, goal)
	local info = TweenInfo.new(d, Enum.EasingStyle[style], Enum.EasingDirection[dir], rep, rev, 0)
	local t = TweenService:Create(o, info, goal)
	t:Play()
	return t
end

local function fxDone(t, f)
	pcall(function() t.Completed:Connect(f) end)
end

-- Yağmur (fall): count parça, seconds süreyle üstten düşer. Parça aralığı = seconds / count. Sürekli.
local function startFall(inst, params, confetti)
	local layer, w, h = fxLayer(inst)
	local tpl = fxTemplate(inst)
	local count = math.max(1, fxParam(params, "fall", "count"))
	local seconds = math.max(0.2, fxParam(params, "fall", "seconds"))
	local fade = fxParam(params, "fall", "fade")
	local smin, smax = fxParam(params, "fall", "smallest"), fxParam(params, "fall", "largest")
	task.spawn(function()
		while layer.Parent do
			local color = confetti and FX_CONFETTI[math.random(#FX_CONFETTI)] or FX_GOLD[math.random(#FX_GOLD)]
			local p = fxSpawn(tpl, layer, w, h, color, smin, smax)
			pcall(function() p.ImageTransparency = 1 - fade end)
			pcall(function() p.BackgroundTransparency = 1 - fade end)
			local x = math.random() * w
			p.Position = UDim2.fromOffset(x, -20)
			local t = fxTween(p, seconds, "Linear", "In", 0, false,
				{ Position = UDim2.fromOffset(x, h + 20), Rotation = math.random(-360, 360) })
			fxDone(t, function() p:Destroy() end)
			task.wait(seconds / count)
		end
	end)
end

-- Patlama (burst): count parça merkezden distance kadar dağılır; fade başlangıç opaklığı.
local function startBurst(inst, params)
	local layer, w, h = fxLayer(inst)
	local tpl = fxTemplate(inst)
	local n = math.max(1, math.floor(fxParam(params, "burst", "count")))
	local fade = fxParam(params, "burst", "fade")
	local dist = fxParam(params, "burst", "distance")
	for i = 1, n do
		local p = fxSpawn(tpl, layer, w, h, FX_CONFETTI[(i % #FX_CONFETTI) + 1], 0.6, 0.9)
		pcall(function() p.ImageTransparency = 1 - fade end)
		pcall(function() p.BackgroundTransparency = 1 - fade end)
		p.Position = UDim2.fromOffset(w / 2, h / 2)
		local ang = (i / n) * math.pi * 2
		local r = math.min(w, h) * dist * (0.7 + math.random() * 0.3)
		local t = fxTween(p, 0.7, "Quad", "Out", 0, false,
			{ Position = UDim2.fromOffset(w / 2 + math.cos(ang) * r, h / 2 + math.sin(ang) * r),
			  Rotation = math.random(-180, 180) })
		pcall(fxTween, p, 0.7, "Quad", "Out", 0, false, { ImageTransparency = 1 })
		pcall(fxTween, p, 0.7, "Quad", "Out", 0, false, { BackgroundTransparency = 1 })
		fxDone(t, function() p:Destroy() end)
	end
end

-- Yörünge (orbit): count parça merkez etrafında döner; seconds = bir tam tur süresi.
local function startOrbit(inst, params)
	local layer, w, h = fxLayer(inst)
	local tpl = fxTemplate(inst)
	local n = math.max(1, math.floor(fxParam(params, "orbit", "count")))
	local seconds = math.max(0.5, fxParam(params, "orbit", "seconds"))
	local r = math.min(w, h) * 0.42
	local step = seconds / 12
	for k = 1, n do
		task.spawn(function()
			local p = fxSpawn(tpl, layer, w, h, FX_GOLD[(k % #FX_GOLD) + 1], 0.5, 0.7)
			local a = (k / n) * math.pi * 2
			while layer.Parent do
				fxTween(p, step, "Linear", "Out", 0, false,
					{ Position = UDim2.fromOffset(w / 2 + math.cos(a) * r, h / 2 + math.sin(a) * r) })
				a = a + math.pi / 6
				task.wait(step)
			end
		end)
	end
end

-- Parıltı (twinkle): count / seconds sıklıkta rastgele noktalarda kopya büyüyüp söner. Sürekli.
local function startTwinkle(inst, params)
	local layer, w, h = fxLayer(inst)
	local tpl = fxTemplate(inst)
	local count = math.max(1, fxParam(params, "twinkle", "count"))
	local seconds = math.max(0.2, fxParam(params, "twinkle", "seconds"))
	local smin, smax = fxParam(params, "twinkle", "smallest"), fxParam(params, "twinkle", "largest")
	task.spawn(function()
		while layer.Parent do
			local p = fxSpawn(tpl, layer, w, h, Color3.fromRGB(255, 250, 200), smin, smax)
			p.Position = UDim2.fromOffset(math.random() * w, math.random() * h)
			local sc = p:FindFirstChildOfClass("UIScale")
			if sc then sc.Scale = 0 end
			local t = fxTween(sc or p, seconds, "Sine", "InOut", 1, true, sc and { Scale = 1 } or { Size = UDim2.fromOffset(12, 12) })
			fxDone(t, function() p:Destroy() end)
			task.wait(seconds / count)
		end
	end)
end

-- Işık süpürme (sweep): eğik yarı saydam bir çubuk öğenin üzerinden geçer. Sürekli. (Şablon gerektirmez.)
local function startSweep(inst)
	local layer, w, h = fxLayer(inst)
	task.spawn(function()
		while layer.Parent do
			local bar = Instance.new("Frame")
			bar.BorderSizePixel = 0
			bar.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
			bar.BackgroundTransparency = 0.82
			bar.AnchorPoint = Vector2.new(0.5, 0.5)
			bar.Size = UDim2.fromOffset(math.floor(w * 0.35), math.floor(h * 2.2))
			bar.Rotation = 20
			bar.Position = UDim2.fromOffset(-w * 0.4, h / 2)
			bar.Parent = layer
			local t = fxTween(bar, 1.6, "Quad", "InOut", 0, false, { Position = UDim2.fromOffset(w * 1.4, h / 2) })
			fxDone(t, function() bar:Destroy() end)
			task.wait(1.9)
		end
	end)
end

-- Dev hale (orb): öğenin arkasında büyük yumuşak daire; scale = çap, pulse = nefes büyüklüğü. Sürekli.
local function startOrb(inst, params)
	local _, w, h = fxLayer(inst)
	local d = math.max(w, h) * fxParam(params, "orb", "scale")
	local orb = Instance.new("Frame")
	orb.BorderSizePixel = 0
	orb.BackgroundColor3 = Color3.fromRGB(255, 220, 120)
	orb.BackgroundTransparency = 0.88
	orb.Size = UDim2.fromOffset(d, d)
	orb.AnchorPoint = Vector2.new(0.5, 0.5)
	orb.Position = UDim2.fromOffset(w / 2, h / 2)
	orb.ZIndex = 0
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = orb
	orb.Parent = inst
	local pulse = fxParam(params, "orb", "pulse")
	fxTween(orb, 1.6, "Sine", "InOut", -1, true, { Size = UDim2.fromOffset(d * pulse, d * pulse), BackgroundTransparency = 0.75 })
end

-- Büyüme (smooth): buton üzerine gelince hover ölçeği, basınca press ölçeği. Yalnız GuiButton.
local function startSmooth(inst, params)
	if not inst:IsA("GuiButton") then return end
	centerPivot(inst)
	local hover = fxParam(params, "smooth", "hover")
	local press = fxParam(params, "smooth", "press")
	local sc = holder(inst, "UIScale")
	local hov = false
	local function go(v)
		fxTween(sc, 0.12, "Quad", "Out", 0, false, { Scale = v })
	end
	inst.MouseEnter:Connect(function() hov = true; go(hover) end)
	inst.MouseLeave:Connect(function() hov = false; go(1) end)
	inst.MouseButton1Down:Connect(function() go(press) end)
	inst.MouseButton1Up:Connect(function() go(hov and hover or 1) end)
end

-- Işık süpürme metinde (gleam): yazının üzerinden parlak bir bant sürekli geçer. sweep: geçiş süresi,
-- pause: geçişler arası bekleme, width: bandın genişliği (0–1). Yalnız metin öğeleri.
local function startGleam(inst, params)
	if not (inst:IsA("TextLabel") or inst:IsA("TextButton")) then return end
	local sweep = math.max(0.2, fxParam(params, "gleam", "sweep"))
	local pause = math.max(0, fxParam(params, "gleam", "pause"))
	local width = fxParam(params, "gleam", "width")
	local half = math.min(0.45, math.max(0.02, width / 2))
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new(Color3.fromRGB(255, 255, 255))
	g.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.5 - half, 1),
		NumberSequenceKeypoint.new(0.5, 0),
		NumberSequenceKeypoint.new(0.5 + half, 1),
		NumberSequenceKeypoint.new(1, 1),
	})
	g.Parent = inst
	task.spawn(function()
		while inst.Parent do
			g.Offset = Vector2.new(-1, 0)
			fxTween(g, sweep, "Linear", "InOut", 0, false, { Offset = Vector2.new(1, 0) })
			task.wait(sweep + pause)
		end
	end)
end

local function startFx(inst, kind, params)
	if kind == "tpl" then return end -- şablon: pre-pass'te gizlendi, kopyalanır
	if kind == "fall" then return startFall(inst, params, false) end
	if kind == "confetti" then return startFall(inst, params, true) end
	if kind == "burst" then
		local function go() pcall(startBurst, inst, params) end
		if inst:IsA("GuiButton") then
			inst.MouseButton1Down:Connect(go)
		else
			go()
		end
		return
	end
	local runners = {
		orbit = startOrbit, twinkle = startTwinkle, sweep = function(i) return startSweep(i) end,
		orb = startOrb, smooth = startSmooth, gleam = startGleam,
	}
	local f = runners[kind]
	if f then pcall(f, inst, params) end
end

-- Şablonları önce gizle ve işaretle (kapsayıcılar bunları aramadan önce).
for _, b in ipairs(BINDINGS) do
	if b.fx == "tpl" then
		local inst = findById(b.id)
		if inst then
			inst:SetAttribute("EI_FxTpl", true)
			pcall(function() inst.Visible = false end)
		end
	end
end

for _, b in ipairs(BINDINGS) do
	local inst = findById(b.id)
	if inst then
		pcall(function()
			if b.hover or b.press or b.selA then centerPivot(inst) end
			if b.show then play(inst, b.show, "show", b.delay) end
			if b.loop then play(inst, b.loop, "loop", 0) end
			if b.fx then startFx(inst, b.fx, b.params) end
			if inst:IsA("GuiButton") then
				if b.hover then
					inst.MouseEnter:Connect(function() play(inst, b.hover, "hover") end)
					inst.MouseLeave:Connect(function() play(inst, b.hover, "leave") end)
				end
				if b.press then
					inst.MouseButton1Down:Connect(function() play(inst, b.press, "press") end)
				end
			end
			if b.selA and b.sel ~= nil then
				SELREG[b.sel] = SELREG[b.sel] or {}
				table.insert(SELREG[b.sel], { inst = inst, a = b.selA })
			end
		end)
	end
end

for key, members in pairs(SELREG) do
	for _, entry in ipairs(members) do
		if entry.inst:IsA("GuiButton") then
			entry.inst.MouseButton1Click:Connect(function() selectClick(key, entry) end)
		end
	end
end

-- ================================================================ ETKİLEŞİM (paneller, sekmeler) + CANLI VERİ
-- Paneller: _panel etiketli (başlangıçta gizli). _open:Ad / _toggle:Ad / _close / _tab:Ad (gruplu sekme).
-- Açılan panelde, içindeki öğelerin giriş animasyonları yeniden oynar (_pop/_fadein/_reveal… her açılışta).
local MAP = {}
for _, d in ipairs(root:GetDescendants()) do
	local mid = d:GetAttribute("EI_Id")
	if mid then MAP[mid] = d end
end
local PANEL_SET = {}
for _, pid in ipairs(PANEL_IDS) do PANEL_SET[pid] = true end
local GROUP_SET = {}
for _, gid in ipairs(GROUP_IDS) do GROUP_SET[gid] = true end

local function replayIn(panel)
	local pid = panel:GetAttribute("EI_Id")
	for _, b in ipairs(BINDINGS) do
		if b.show then
			local d = MAP[b.id]
			if d and d ~= panel and d:IsDescendantOf(panel) then
				pcall(play, d, b.show, "show", b.delay)
			end
		end
	end
	for _, b in ipairs(BINDINGS) do
		if b.show and b.id == pid then
			pcall(play, panel, b.show, "show", b.delay)
		end
	end
end

local function openPanel(p)
	if not p then return end
	p.Visible = true
	replayIn(p)
end

-- Buton bir panelin içindeyse en yakın _panel atası (kapatma için).
local function nearestPanel(d)
	local p = d.Parent
	while p and p ~= root do
		local pid = p:GetAttribute("EI_Id")
		if pid and PANEL_SET[pid] then return p end
		p = p.Parent
	end
	return nil
end

-- Panel yoksa: ScreenGui'nin doğrudan çocuğu olan üst kapsayıcı (import kökü).
local function topBelowRoot(d)
	local p = d
	while p and p.Parent and p.Parent ~= root do p = p.Parent end
	return p
end

local function closeTarget(btn, targetId)
	if targetId then return MAP[targetId] end
	return nearestPanel(btn) or topBelowRoot(btn)
end

-- Sekme grubu: en yakın _tabgroup atası; yoksa "0" (kök).
local function groupOf(btn)
	local p = btn.Parent
	while p and p ~= root do
		local gid = p:GetAttribute("EI_Id")
		if gid and GROUP_SET[gid] then return gid end
		p = p.Parent
	end
	return 0
end

local TAB_BY_GROUP = {}
for _, a in ipairs(ACTIONS) do
	local btn = MAP[a.id]
	if btn and a.kind == "tab" then
		local g = groupOf(btn)
		TAB_BY_GROUP[g] = TAB_BY_GROUP[g] or {}
		table.insert(TAB_BY_GROUP[g], a)
	end
end

-- Başlangıç: her sekme grubunda ilk sekmenin paneli açık, diğerleri kapalı.
for _, list in pairs(TAB_BY_GROUP) do
	for i, a in ipairs(list) do
		local t = MAP[a.target]
		if t and i > 1 then t.Visible = false end
	end
	if list[1] then openPanel(MAP[list[1].target]) end
end

for _, a in ipairs(ACTIONS) do
	local btn = MAP[a.id]
	if btn and btn:IsA("GuiButton") then
		btn.MouseButton1Click:Connect(function()
			if a.kind == "open" then
				openPanel(MAP[a.target])
			elseif a.kind == "close" then
				local t = closeTarget(btn, a.target)
				if t then t.Visible = false end
			elseif a.kind == "toggle" then
				local t = MAP[a.target]
				if t then
					if t.Visible then t.Visible = false else openPanel(t) end
				end
			elseif a.kind == "tab" then
				local target = MAP[a.target]
				for _, o in ipairs(TAB_BY_GROUP[groupOf(btn)] or {}) do
					local ot = MAP[o.target]
					if ot and ot ~= target then ot.Visible = false end
				end
				openPanel(target)
			end
		end)
	end
end

]==]

-- Ortak üretici. lib: animasyon tanımları (id → {tracks=...}); keyFn: Lua anahtarı üretir.
-- bindings: [{id, show?, hover?, press?}] — değerler lib anahtarlarıdır.
local function buildSourceWith(bindings, lib, keyFn, extra)
	extra = extra or {}
	local used, usedIds = {}, {}
	local bl = {}
	for _, b in ipairs(bindings) do
		local item = { id = b.id }
		for _, k in ipairs({ "show", "hover", "press", "loop", "selA" }) do
			if b[k] and lib[b[k]] then
				item[k] = keyFn(b[k])
				if not used[b[k]] then
					used[b[k]] = true
					usedIds[#usedIds + 1] = b[k]
				end
			end
		end
		if b.sel ~= nil then item.sel = b.sel end
		if b.fx then item.fx = b.fx end
		if b.params then item.params = b.params end
		if b.delay and b.delay > 0 then item.delay = b.delay end
		bl[#bl + 1] = item
	end
	table.sort(usedIds)
	local animTable = {}
	for _, id in ipairs(usedIds) do
		local a = lib[id]
		local tracks = {}
		for _, tr in ipairs(a.tracks) do
			local dl = tr.dl
			if type(dl) == "table" then dl = { a = dl.a, b = dl.b, rnd = true } end
			tracks[#tracks + 1] = { t = tr.t, p = tr.p, from = tr.from, to = tr.to, d = tr.d,
				dl = dl, e = tr.e, ed = tr.ed, rep = tr.rep, rev = tr.rev }
		end
		animTable[#animTable + 1] = "[\"" .. keyFn(id) .. "\"] = { tracks = " .. lit(tracks) .. " }"
	end
	local src = TEMPLATE
	src = string.gsub(src, "__ANIMS__", function() return "{\n\t" .. table.concat(animTable, ",\n\t") .. "\n}" end)
	src = string.gsub(src, "__BINDINGS__", function() return lit(bl) end)
	src = string.gsub(src, "__ACTIONS__", function() return lit(extra.actions or {}) end)
	src = string.gsub(src, "__PANELS__", function() return lit(extra.panels or {}) end)
	src = string.gsub(src, "__GROUPS__", function() return lit(extra.groups or {}) end)
	return src
end

-- Kütüphane tabanlı üretim (v10 yolu; değişmedi).
function EIAnim.buildSource(bindings)
	return buildSourceWith(bindings, ANIM_LIB, function(s) return s end)
end

-- JSON tabanlı üretim (v11): doc.anims tanımları + düğümlerdeki anim alanları.
-- Ad kuralı: "_Animasyon 2" → Lua anahtarı "_Animasyon_2" (boşluk güvenli değil).
-- Tanımı olmayan referanslar sessizce düşürülür (bozuk JSON bütün betiği bozmasın).
function EIAnim.buildSourceSpec(bindings, specs, extra)
	local function luaName(name)
		return (string.gsub(tostring(name), " ", "_"))
	end
	return buildSourceWith(bindings, specs, luaName, extra)
end

-- ================================================================ v11: TASARIM KARARI (madde 3 + P1)
-- Asistan animasyonu öğe-öğe değil, tasarım bütünü için seçer:
--   1) STİL: stile uygun animasyonlara bonus (anahtar sözcük eşleşmesi)
--   2) KONUM: giriş ScreenGui'nin doğrudan çocuklarına (derinlik ≤ 1); kapat butonunda basma yok
--   3) TUTARLILIK: aynı sınıftaki butonların ≥%50'si aynı animasyonu öncelikliyorsa, öğrenmesi olmayanlara o
--   4) ÖĞRENME: bağlamda kullanıcı gözlemi varsa her zaman öncelikli
--   5) KASKAD (_cascade): aynı üst öğedeki ≥3 buton, sırayla CASCADE_STEP aralıklı girer
--   6) DÖNGÜ (_blink/_wiggle): primary-button (yanıp sönme) ve icon (sallanma); en fazla LOOP_MAX öğe
--   7) SEÇİM (_select): tab/slot/seçenek adlı butonlar, aynı üst öğede ≥2 ise kalıcı seçim grubu
-- Parite: ei-anim.js aynı kuralları birebir uygular (verify_anim_parity.py).

local STYLE_TOKENS = {
	stud = { "fade", "scale_up", "shrink_only", "glow", "lift", "brighten", "soft", "reveal" },
	anime = { "elastic", "flip", "rotate", "bounce", "pop", "spring", "grow", "swing" },
	cartoon = { "punch", "squash", "shake", "bounce", "pop", "wiggle", "shrink" },
}
local TOKEN_BONUS = 1.5
local CASCADE_STEP = 0.06
local CASCADE_MIN = 3
local LOOP_MAX = 3
local SELECT_MIN = 2

local function tokenBonus(id, style)
	local toks = STYLE_TOKENS[style]
	if not toks then return 1 end
	for _, t in ipairs(toks) do
		if string.find(id, t, 1, true) then return TOKEN_BONUS end
	end
	return 1
end

-- Skorlu aday sırası: beauty × stil öncülü × stil bonusu ↓, eşitlikte id ↑ (rol → sınıf geri dönüşü).
local function scoredCandidates(cat, cls, role, style)
	local bias = (STYLE_BIAS[style] and STYLE_BIAS[style][cat]) or 1
	for pass = 1, 2 do
		local list = {}
		for _, id in ipairs(ANIM_IDS) do
			local a = ANIM_LIB[id]
			if a.cat == cat and listHas(a.cls, cls) and (pass == 2 or listHas(a.roles, role)) then
				list[#list + 1] = id
			end
		end
		if #list > 0 then
			local score = {}
			for _, id in ipairs(list) do
				score[id] = ANIM_LIB[id].beauty * bias * tokenBonus(id, style)
			end
			table.sort(list, function(x, y)
				if score[x] ~= score[y] then return score[x] > score[y] end
				return x < y
			end)
			return list
		end
	end
	return {}
end

local function rankFor(cat, cls, role, style, learn)
	local list = scoredCandidates(cat, cls, role, style)
	if learn and #list > 0 then
		local ctx = EILearn.ctxKey(style, cls, role, cat)
		if learnedObs(learn, ctx) > 0 then
			list = EILearn.rankAnim(learn, ctx, list)
		end
	end
	return list
end

local function learnedFor(learn, style, pe, cat)
	if not learn then return false end
	return learnedObs(learn, EILearn.ctxKey(style, pe.cls, pe.role, cat)) > 0
end

-- Tutarlılık: sınıf başına ≥%50 çoğunluk varsa öğrenmesi olmayan üyelere uygula (giris/hover/basma).
local function applyConsensus(per, cat, style, learn)
	local groups, order = {}, {}
	for i, pe in ipairs(per) do
		local list = pe.rank[cat]
		if list and #list > 0 and not learnedFor(learn, style, pe, cat) and not pe.tagged[cat] then
			if not groups[pe.cls] then
				groups[pe.cls] = {}
				order[#order + 1] = pe.cls
			end
			groups[pe.cls][#groups[pe.cls] + 1] = i
		end
	end
	table.sort(order)
	for _, cls in ipairs(order) do
		local mem = groups[cls]
		if #mem >= 2 then
			local tally = {}
			for _, i in ipairs(mem) do
				local top = per[i].rank[cat][1]
				tally[top] = (tally[top] or 0) + 1
			end
			local best, bestN = nil, 0
			for id, n in pairs(tally) do
				-- eşitlikte küçük id kazanır: pairs sırasından bağımsız deterministik
				if best == nil or n > bestN or (n == bestN and id < best) then
					best, bestN = id, n
				end
			end
			if best and bestN * 2 >= #mem then
				for _, i in ipairs(mem) do
					local list = per[i].rank[cat]
					local has = false
					for _, x in ipairs(list) do
						if x == best then has = true end
					end
					if has then
						local nl = { best }
						for _, x in ipairs(list) do
							if x ~= best then nl[#nl + 1] = x end
						end
						per[i].rank[cat] = nl
					end
				end
			end
		end
	end
end

-- ETİKETLER (Framewisp benzeri): katman adında "_etiket" geçerse o animasyon seçilir.
-- Örnek: "Kart_pop_button" → giriş enter_pop_scale; "Buton_lift_button" → hover hover_lift.
local TAG_ANIM = {
	pop = "enter_pop_scale", fade = "enter_fade", slide = "enter_slide_up", zoom = "enter_zoom_in",
	rotate = "enter_rotate_in", elastic = "enter_elastic_pop", drop = "enter_bounce_drop", punch = "enter_punch",
	reveal = "enter_reveal_showcase", swing = "enter_swing_door", flip = "enter_flip_in", stagger = "enter_stagger_list",
	lift = "hover_lift", turn = "hover_turn_card", glow = "hover_glow", tilt = "hover_rotate_tilt",
	stroke = "hover_stroke_grow", brighten = "hover_brighten", shine = "hover_shine_sweep", bounce = "hover_bounce_small",
	squish = "press_squash", ripple = "press_ripple",
	pulse = "loop_pulse_scale", float = "loop_float", blink = "loop_blink_cta", wiggle = "loop_wiggle_icon",
	border = "loop_border_spin", kenar = "loop_border_spin", spin = "loop_rotate_slow",
	breathe = "loop_breathe_transparency", shimmer = "loop_shimmer", bobble = "loop_bobble", ring = "loop_expand_ring",
	shake = "attention_shake_strong", ping = "attention_ping", bell = "attention_bell_ring",
	select = "select_outline_pop", secim = "select_outline_pop",
}
local SLOT_OF = { giris = "giris", hover = "hover", basma = "basma", dongu = "dongu", dikkat = "dongu", secim = "secim" }

-- Ad içindeki etiket kimlikleri, geçiş sırasıyla (ayırıcılar: harf/rakam dışı karakterler)
local function tagIds(name)
	local out = {}
	for tok in string.gmatch(lower(name), "[%w]+") do
		local id = TAG_ANIM[tok]
		if id then out[#out + 1] = id end
	end
	return out
end

-- Etiketleri uygular. Bir kategoride ilk etiket kazanır; öğrenme varsa öğrenme kazanır.
-- hover/basma/secim yalnız buton öğelere uygulanır; animasyonun cls listesi de tutmalı.
local function applyTags(pe, el, learn, style)
	for _, id in ipairs(tagIds(el.name)) do
		local a = ANIM_LIB[id]
		local slot = a and SLOT_OF[a.cat]
		-- Buton slotları (hover/basma/secim): buton öğeler, animasyonun cls listesinden bağımsız kabul edilir.
		local btnSlot = (slot == "hover" or slot == "basma" or slot == "secim")
		local clsOk = a ~= nil and (listHas(a.cls, pe.cls) or (pe.isBtn and btnSlot))
		if slot and not pe.tagged[slot] and clsOk then
			local slotOk = (slot == "giris" or slot == "dongu") or pe.isBtn
			if slotOk and not learnedFor(learn, style, pe, slot) then
				local nl = { id }
				for _, x in ipairs(pe.rank[slot] or {}) do
					if x ~= id then nl[#nl + 1] = x end
				end
				pe.rank[slot] = nl
				pe.tagged[slot] = true
			end
		end
	end
end

-- EFEKTLER (Framewisp _fall/_burst/_rays/_focus/_pixels benzeri). Animasyondan ayrı: UI içi parçacık/şekil.
-- Ad etiketi: "Hazine_coin_Frame" → yağan para; "Buton_burst_button" → basınca patlama.
local TAG_FX = {
	fall = "fall", rain = "fall", coin = "fall", confetti = "confetti",
	burst = "burst", patlama = "burst", orbit = "orbit", yorunge = "orbit",
	twinkle = "twinkle", sparkle = "twinkle", parilti = "twinkle", sweep = "sweep", orb = "orb", hale = "orb",
	smooth = "smooth", gleam = "gleam",
}

-- Ad içindeki efekt: kapsayıcı etiketi (fall/burst/…) ya da şablon etiketi ("fx" → "tpl").
-- "fx" etiketi kapsayıcı etiketinden önce gelir (şablon kapsayıcı olamaz).
local function fxTag(name)
	local kind, tpl = nil, false
	for tok in string.gmatch(lower(name), "[%w]+") do
		if TAG_FX[tok] and not kind then kind = TAG_FX[tok] end
		if tok == "fx" then tpl = true end
	end
	if tpl then return "tpl" end -- "fx" içeren öğe şablondur; kapsayıcı olamaz
	if kind then return kind end
	return nil
end

local function isBtnCls(c)
	return c == "TextButton" or c == "ImageButton"
end

-- Seçilebilirlik: rol değil ad belirteci (roleOf buton adlarında "tab"/"slot"u görmez).
local function selectEligible(el, role)
	if role == "tab" or role == "slot" then return true end
	return containsAny(lower(el.name), { "tab", "slot", "select", "secim", "option", "secenek" })
end

-- elements: [{id, name, cls, depth, parent?}] · Dönüş: [{id, cls, role, parent, sel?, delay?, rank = {...}}]
function EIAnim.decideRanked(elements, style, learn)
	local per = {}
	for _, el in ipairs(elements) do
		per[#per + 1] = { id = el.id, cls = el.cls, role = EIAnim.roleOf(el), parent = el.parent,
			depth = el.depth, isBtn = isBtnCls(el.cls), rank = {}, tagged = {} }
	end
	-- Kaskad: aynı üst öğedeki buton sayısı ≥ CASCADE_MIN ise sıra indeksi (0,1,2...) ver.
	local groupCount, cascadeIdx, seen = {}, {}, {}
	for _, pe in ipairs(per) do
		if pe.isBtn and pe.parent ~= nil then
			local key = tostring(pe.parent)
			groupCount[key] = (groupCount[key] or 0) + 1
		end
	end
	for i, pe in ipairs(per) do
		if pe.isBtn and pe.parent ~= nil and groupCount[tostring(pe.parent)] >= CASCADE_MIN then
			local key = tostring(pe.parent)
			seen[key] = seen[key] or 0
			cascadeIdx[i] = seen[key]
			seen[key] = seen[key] + 1
		end
	end
	local loops = 0
	for i, pe in ipairs(per) do
		local cls, role = pe.cls, pe.role
		if pe.depth <= 1 or cascadeIdx[i] ~= nil then
			pe.rank.giris = rankFor("giris", cls, role, style, learn)
		end
		if cascadeIdx[i] ~= nil then
			pe.delay = cascadeIdx[i] * CASCADE_STEP
		end
		if pe.isBtn then
			pe.rank.hover = rankFor("hover", cls, role, style, learn)
			if role ~= "close-button" then
				pe.rank.basma = rankFor("basma", cls, role, style, learn)
			end
			if selectEligible(elements[i], role) then
				pe.rank.secim = rankFor("secim", cls, role, style, learn)
			end
		end
		applyTags(pe, elements[i], learn, style)
		pe.fx = fxTag(elements[i].name)
		-- Otomatik döngü: yalnız CTA ve ikon; etiketli öğeler sayıma girmez
		if not pe.tagged.dongu and (role == "primary-button" or role == "icon") and loops < LOOP_MAX then
			local l = rankFor("dongu", cls, role, style, learn)
			if #l > 0 then
				pe.rank.dongu = l
				loops = loops + 1
			end
		end
	end
	-- Seçim grupları: aynı üst öğede en az SELECT_MIN seçilebilir öğe.
	local selCount = {}
	for _, pe in ipairs(per) do
		if pe.rank.secim and #pe.rank.secim > 0 then
			local key = tostring(pe.parent or 0)
			selCount[key] = (selCount[key] or 0) + 1
		end
	end
	for _, pe in ipairs(per) do
		if pe.rank.secim then
			if selCount[tostring(pe.parent or 0)] < SELECT_MIN then
				pe.rank.secim = nil
			else
				pe.sel = pe.parent or 0
			end
		end
	end
	for _, cat in ipairs({ "giris", "hover", "basma" }) do
		applyConsensus(per, cat, style, learn)
	end
	return per
end

-- Studio'nun ve Figma panelinin kullandığı bağlamalar: seçilen (ilk) öneriler.
function EIAnim.decideBindings(elements, style, learn)
	local out = {}
	for _, pe in ipairs(EIAnim.decideRanked(elements, style, learn)) do
		local b = { id = pe.id, cls = pe.cls, role = pe.role }
		local any = false
		if pe.rank.giris and #pe.rank.giris > 0 then b.show = pe.rank.giris[1]; any = true end
		if pe.rank.hover and #pe.rank.hover > 0 then b.hover = pe.rank.hover[1]; any = true end
		if pe.rank.basma and #pe.rank.basma > 0 then b.press = pe.rank.basma[1]; any = true end
		if pe.rank.dongu and #pe.rank.dongu > 0 then b.loop = pe.rank.dongu[1]; any = true end
		if pe.rank.secim and #pe.rank.secim > 0 then b.selA = pe.rank.secim[1]; b.sel = pe.sel; any = true end
		if pe.delay and pe.delay > 0 then b.delay = pe.delay end
		if pe.fx then b.fx = pe.fx; any = true end
		if any then out[#out + 1] = b end
	end
	return out
end

-- ================================================================ SESLER (hover + tıklama)
-- Ses ID'leri kodda sabit: kullanıcının hazır Asset ID'leri (ayar yok). Her GuiButton için:
--   üzerine gelince → UzerineGelmeSesi · tıklayınca → KullanSesi.
-- Ayrı bir LocalScript (EI_Sesler) olarak üretilir; animasyon betiğinden bağımsızdır.
local SOUND_SOURCE = [==[
-- EasyImport sesleri (otomatik). Hover ve tıklama sesleri; ID'ler kodda sabit.
local root = script.Parent
local SES_UZERINE = "rbxassetid://139719503904449"
local SES_TIKLAMA = "rbxassetid://87437544236708"
local SES_SEVIYE = 0.7

local function sesCal(id)
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Volume = SES_SEVIYE
	s.Parent = root
	pcall(function() s:Play() end)
	pcall(function() s.Ended:Connect(function() s:Destroy() end) end)
end

for _, d in ipairs(root:GetDescendants()) do
	if d:IsA("GuiButton") then
		pcall(function()
			d.MouseEnter:Connect(function() sesCal(SES_UZERINE) end)
			d.MouseButton1Click:Connect(function() sesCal(SES_TIKLAMA) end)
		end)
	end
end
]==]

function EIAnim.buildSoundSource()
	return SOUND_SOURCE
end

EIAnim.VERSION = VERSION
return EIAnim
