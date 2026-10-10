// EasyImport · Animasyon üretici (JS) — runtime/lua/EIAnim.lua'nın birebir karşılığı.
// Veri ve şablon tools/build_anim_lua.py tarafından üretilir (ELLE DÜZENLEMEYİN).
// Parite: tools/verify_anim_parity.py  (aynı girdi → aynı seçim ve aynı LocalScript baytı).
var EIAnim = (function () {
  var VERSION = 'ei-anim-1';
  // <<EI_ANIM_DATA>>
var ANIM_IDS = ["attention_bell_ring", "attention_blink", "attention_bounce_big", "attention_ping", "attention_pulse_scale_big", "attention_shake_strong", "attention_wiggle", "attention_zoom_punch", "enter_bounce_drop", "enter_elastic_pop", "enter_fade", "enter_flip_in", "enter_grow_from_center", "enter_pop_scale", "enter_punch", "enter_reveal_showcase", "enter_rotate_in", "enter_scale_rotate", "enter_slide_down", "enter_slide_left", "enter_slide_right", "enter_slide_up", "enter_soft_scale", "enter_stagger_list", "enter_swing_door", "enter_zoom_in", "enter_zoom_out", "hover_bounce_small", "hover_brighten", "hover_glow", "hover_lift", "hover_rotate_tilt", "hover_scale_down", "hover_scale_up", "hover_shift_right", "hover_shine_sweep", "hover_stroke_grow", "hover_turn_card", "hover_wiggle_once", "loop_blink_cta", "loop_bobble", "loop_border_spin", "loop_breathe_transparency", "loop_color_cycle", "loop_expand_ring", "loop_float", "loop_gradient_sweep", "loop_pulse_scale", "loop_rotate_medium", "loop_rotate_reverse", "loop_rotate_slow", "loop_shake_slight", "loop_shimmer", "loop_wiggle_icon", "press_depress", "press_flash", "press_pop_scale", "press_punch", "press_ripple", "press_rotate_spin", "press_select_pop", "press_shake", "press_shrink_bounce", "press_shrink_only", "press_squash", "select_outline_pop"];
var ANIM_LIB = {
 "attention_bell_ring": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "icon",
   "notification"
  ],
  "tracks": [
   {
    "d": 0.13,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -18,
    "p": "Rotation",
    "rep": 5,
    "rev": true,
    "t": "self",
    "to": 18
   }
  ],
  "trig": "event"
 },
 "attention_blink": {
  "beauty": 2,
  "cat": "dikkat",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextLabel"
  ],
  "roles": [
   "badge",
   "bar",
   "value"
  ],
  "tracks": [
   {
    "d": 0.15,
    "dl": 0,
    "e": "Linear",
    "ed": "InOut",
    "from": 0,
    "p": "ImageTransparency",
    "rep": 2,
    "rev": true,
    "t": "self",
    "to": 1
   }
  ],
  "trig": "event"
 },
 "attention_bounce_big": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "currency",
   "icon",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.45,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 1,
    "rev": true,
    "t": "UIScale",
    "to": 1.25
   }
  ],
  "trig": "event"
 },
 "attention_ping": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "icon"
  ],
  "tracks": [
   {
    "d": 0.9,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": 0.5,
    "p": "Scale",
    "rep": 2,
    "rev": false,
    "t": "UIScale",
    "to": 2.0
   },
   {
    "d": 0.9,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0,
    "p": "ImageTransparency",
    "rep": 2,
    "rev": false,
    "t": "self",
    "to": 1
   }
  ],
  "trig": "event"
 },
 "attention_pulse_scale_big": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "claim",
   "primary-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.6,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 1,
    "p": "Scale",
    "rep": -1,
    "rev": true,
    "t": "UIScale",
    "to": 1.16
   }
  ],
  "trig": "event"
 },
 "attention_shake_strong": {
  "beauty": 2,
  "cat": "dikkat",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextLabel"
  ],
  "roles": [
   "badge",
   "button",
   "icon",
   "value"
  ],
  "tracks": [
   {
    "d": 0.075,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -9,
    "p": "Rotation",
    "rep": 5,
    "rev": true,
    "t": "self",
    "to": 9
   }
  ],
  "trig": "event"
 },
 "attention_wiggle": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "icon",
   "reward",
   "slot"
  ],
  "tracks": [
   {
    "d": 0.1,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -12,
    "p": "Rotation",
    "rep": 2,
    "rev": true,
    "t": "self",
    "to": 12
   },
   {
    "d": 0.3,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 1,
    "rev": true,
    "t": "UIScale",
    "to": 1.08
   }
  ],
  "trig": "event"
 },
 "attention_zoom_punch": {
  "beauty": 4,
  "cat": "dikkat",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextLabel"
  ],
  "roles": [
   "reward",
   "title",
   "value"
  ],
  "tracks": [
   {
    "d": 0.4,
    "dl": 0,
    "e": "Exponential",
    "ed": "Out",
    "from": 1.35,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "event"
 },
 "enter_bounce_drop": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "card",
   "modal",
   "panel",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.75,
    "dl": 0,
    "e": "Bounce",
    "ed": "Out",
    "from": [
     0,
     -180
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   }
  ],
  "trig": "show"
 },
 "enter_elastic_pop": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "primary-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.7,
    "dl": 0,
    "e": "Elastic",
    "ed": "Out",
    "from": 0.2,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "show"
 },
 "enter_fade": {
  "beauty": 2,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageButton",
   "ImageLabel",
   "ScrollingFrame",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "background",
   "label",
   "modal",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.3,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_flip_in": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "card",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.55,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": 0.05,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "show"
 },
 "enter_grow_from_center": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "modal",
   "panel",
   "tooltip"
  ],
  "tracks": [
   {
    "d": 0.32,
    "dl": 0,
    "e": "Cubic",
    "ed": "Out",
    "from": 0.8,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.24,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_pop_scale": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "button",
   "card",
   "icon",
   "modal",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.35,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.6,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.2,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_punch": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "button",
   "title",
   "value"
  ],
  "tracks": [
   {
    "d": 0.25,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1.3,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "show"
 },
 "enter_reveal_showcase": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "button",
   "card",
   "icon",
   "modal",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.45,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.5,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.45,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": -6,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   },
   {
    "d": 0.25,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_rotate_in": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "card",
   "icon",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.45,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": -28,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   },
   {
    "d": 0.35,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.5,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.2,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_scale_rotate": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "card",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.5,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.4,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.5,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": 180,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_slide_down": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "modal",
   "panel",
   "tooltip"
  ],
  "tracks": [
   {
    "d": 0.4,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": [
     0,
     -40
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   },
   {
    "d": 0.3,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.6,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_slide_left": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "card",
   "panel",
   "sidebar"
  ],
  "tracks": [
   {
    "d": 0.38,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": [
     -60,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   },
   {
    "d": 0.28,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.5,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_slide_right": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "card",
   "panel",
   "sidebar"
  ],
  "tracks": [
   {
    "d": 0.38,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": [
     60,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   },
   {
    "d": 0.28,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.5,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_slide_up": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel",
   "ScrollingFrame",
   "TextButton"
  ],
  "roles": [
   "card",
   "list",
   "modal",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.4,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": [
     0,
     40
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   },
   {
    "d": 0.3,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.6,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_soft_scale": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel",
   "ScrollingFrame",
   "TextLabel"
  ],
  "roles": [
   "background",
   "label",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.28,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 0.94,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.24,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 0.5,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_stagger_list": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "card",
   "list",
   "slot"
  ],
  "tracks": [
   {
    "d": 0.25,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   },
   {
    "d": 0.3,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.85,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "show"
 },
 "enter_swing_door": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "icon",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.4,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0.6,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.6,
    "dl": 0,
    "e": "Elastic",
    "ed": "Out",
    "from": 14,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_zoom_in": {
  "beauty": 3,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "modal",
   "panel"
  ],
  "tracks": [
   {
    "d": 0.36,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 0.35,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.22,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.8,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "enter_zoom_out": {
  "beauty": 4,
  "cat": "giris",
  "cls": [
   "CanvasGroup",
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "modal",
   "panel",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.42,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": 1.35,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   },
   {
    "d": 0.25,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 1,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "show"
 },
 "hover_bounce_small": {
  "beauty": 4,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "currency",
   "icon-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.28,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.1
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_brighten": {
  "beauty": 3,
  "cat": "hover",
  "cls": [
   "Frame",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "slot",
   "tab"
  ],
  "tracks": [
   {
    "d": 0.13,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 0,
    "p": "BackgroundTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0.15
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_glow": {
  "beauty": 4,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "icon",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.14,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 0.15,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_lift": {
  "beauty": 4,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "slot"
  ],
  "tracks": [
   {
    "d": 0.15,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": [
     0,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     -3
    ]
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_rotate_tilt": {
  "beauty": 3,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "card",
   "icon-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.15,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 0,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 4
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_scale_down": {
  "beauty": 2,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "close-button",
   "icon-button"
  ],
  "tracks": [
   {
    "d": 0.12,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 0.95
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_scale_up": {
  "beauty": 3,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "icon-button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.12,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.06
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_shift_right": {
  "beauty": 3,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "button",
   "list",
   "tab"
  ],
  "tracks": [
   {
    "d": 0.14,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": [
     0,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     4,
     0
    ]
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_shine_sweep": {
  "beauty": 5,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "card",
   "primary-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.55,
    "dl": 0,
    "e": "Circular",
    "ed": "InOut",
    "from": [
     -1.2,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     1.2,
     0
    ]
   },
   {
    "d": 0.55,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 0.9
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_stroke_grow": {
  "beauty": 4,
  "cat": "hover",
  "cls": [
   "Frame",
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.14,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 3,
    "p": "Thickness",
    "rep": 0,
    "rev": false,
    "t": "UIStroke",
    "to": 5
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_turn_card": {
  "beauty": 4,
  "cat": "hover",
  "cls": [
   "Frame",
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "icon"
  ],
  "tracks": [
   {
    "d": 0.25,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": -5
   }
  ],
  "trig": "mouseEnter"
 },
 "hover_wiggle_once": {
  "beauty": 3,
  "cat": "hover",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "icon"
  ],
  "tracks": [
   {
    "d": 0.08,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": 1,
    "rev": true,
    "t": "self",
    "to": -4
   }
  ],
  "trig": "mouseEnter"
 },
 "loop_blink_cta": {
  "beauty": 5,
  "cat": "dongu",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.6,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "ImageTransparency",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": 0.7
   },
   {
    "d": 0.6,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "TextTransparency",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": 0.7
   }
  ],
  "trig": "always"
 },
 "loop_bobble": {
  "beauty": 3,
  "cat": "dongu",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "icon",
   "reward"
  ],
  "tracks": [
   {
    "d": 1.0,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -7,
    "p": "Rotation",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": 7
   }
  ],
  "trig": "always"
 },
 "loop_border_spin": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "icon",
   "modal",
   "panel",
   "primary-button",
   "slot",
   "tab"
  ],
  "tracks": [
   {
    "d": 2.5,
    "dl": 0,
    "e": "Linear",
    "ed": "In",
    "from": 0,
    "p": "Rotation",
    "rep": -1,
    "rev": false,
    "t": "UIGradient",
    "to": 360
   }
  ],
  "trig": "always"
 },
 "loop_breathe_transparency": {
  "beauty": 3,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageLabel",
   "TextLabel"
  ],
  "roles": [
   "background",
   "icon",
   "label"
  ],
  "tracks": [
   {
    "d": 1.2,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0.25,
    "p": "ImageTransparency",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": 0.6
   }
  ],
  "trig": "always"
 },
 "loop_color_cycle": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageLabel",
   "TextLabel"
  ],
  "roles": [
   "badge",
   "reward",
   "title",
   "value"
  ],
  "tracks": [
   {
    "d": 3.0,
    "dl": 0,
    "e": "Linear",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": -1,
    "rev": false,
    "t": "UIGradient",
    "to": 360
   }
  ],
  "trig": "always"
 },
 "loop_expand_ring": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "icon"
  ],
  "tracks": [
   {
    "d": 1.8,
    "dl": 0,
    "e": "Sine",
    "ed": "Out",
    "from": 0.7,
    "p": "Scale",
    "rep": -1,
    "rev": false,
    "t": "UIScale",
    "to": 1.4
   },
   {
    "d": 1.8,
    "dl": 0,
    "e": "Sine",
    "ed": "In",
    "from": 0.1,
    "p": "ImageTransparency",
    "rep": -1,
    "rev": false,
    "t": "self",
    "to": 1
   }
  ],
  "trig": "always"
 },
 "loop_float": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "card",
   "icon",
   "reward"
  ],
  "tracks": [
   {
    "d": 1.5,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": [
     0,
     -5
    ],
    "p": "Position",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": [
     0,
     5
    ]
   }
  ],
  "trig": "always"
 },
 "loop_gradient_sweep": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageLabel"
  ],
  "roles": [
   "background",
   "bar",
   "panel"
  ],
  "tracks": [
   {
    "d": 2.0,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": [
     0,
     -0.8
    ],
    "p": "Offset",
    "rep": -1,
    "rev": true,
    "t": "UIGradient",
    "to": [
     0,
     0.8
    ]
   }
  ],
  "trig": "always"
 },
 "loop_pulse_scale": {
  "beauty": 3,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "icon",
   "primary-button",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.8,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 1,
    "p": "Scale",
    "rep": -1,
    "rev": true,
    "t": "UIScale",
    "to": 1.05
   }
  ],
  "trig": "always"
 },
 "loop_rotate_medium": {
  "beauty": 3,
  "cat": "dongu",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "icon",
   "loading"
  ],
  "tracks": [
   {
    "d": 4.0,
    "dl": 0,
    "e": "Linear",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": -1,
    "rev": false,
    "t": "self",
    "to": 360
   }
  ],
  "trig": "always"
 },
 "loop_rotate_reverse": {
  "beauty": 3,
  "cat": "dongu",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "icon"
  ],
  "tracks": [
   {
    "d": 9.0,
    "dl": 0,
    "e": "Linear",
    "ed": "InOut",
    "from": 360,
    "p": "Rotation",
    "rep": -1,
    "rev": false,
    "t": "self",
    "to": 0
   }
  ],
  "trig": "always"
 },
 "loop_rotate_slow": {
  "beauty": 4,
  "cat": "dongu",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "icon",
   "loading"
  ],
  "tracks": [
   {
    "d": 12.0,
    "dl": 0,
    "e": "Linear",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": -1,
    "rev": false,
    "t": "self",
    "to": 360
   }
  ],
  "trig": "always"
 },
 "loop_shake_slight": {
  "beauty": 2,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "badge",
   "icon"
  ],
  "tracks": [
   {
    "d": 0.1,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -2,
    "p": "Rotation",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": 2
   }
  ],
  "trig": "always"
 },
 "loop_shimmer": {
  "beauty": 5,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageLabel",
   "TextButton",
   "TextLabel"
  ],
  "roles": [
   "currency",
   "primary-button",
   "reward",
   "title"
  ],
  "tracks": [
   {
    "d": 2.2,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": [
     -1.2,
     0
    ],
    "p": "Offset",
    "rep": -1,
    "rev": false,
    "t": "UIGradient",
    "to": [
     1.2,
     0
    ]
   }
  ],
  "trig": "always"
 },
 "loop_wiggle_icon": {
  "beauty": 6,
  "cat": "dongu",
  "cls": [
   "Frame",
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "icon"
  ],
  "tracks": [
   {
    "d": 0.25,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": -1,
    "rev": true,
    "t": "self",
    "to": -6
   }
  ],
  "trig": "always"
 },
 "press_depress": {
  "beauty": 3,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.08,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": [
     0,
     0
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     2
    ]
   },
   {
    "d": 0.16,
    "dl": 0.1,
    "e": "Back",
    "ed": "Out",
    "from": [
     0,
     2
    ],
    "p": "Position",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": [
     0,
     0
    ]
   }
  ],
  "trig": "mouseDown"
 },
 "press_flash": {
  "beauty": 4,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.08,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 0.94
   },
   {
    "d": 0.17,
    "dl": 0.08,
    "e": "Back",
    "ed": "Out",
    "from": 0.94,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_pop_scale": {
  "beauty": 4,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "ImageLabel",
   "TextButton"
  ],
  "roles": [
   "button",
   "currency",
   "reward"
  ],
  "tracks": [
   {
    "d": 0.12,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.15
   },
   {
    "d": 0.22,
    "dl": 0.12,
    "e": "Back",
    "ed": "Out",
    "from": 1.15,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_punch": {
  "beauty": 4,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.06,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 0.85
   },
   {
    "d": 0.2,
    "dl": 0.06,
    "e": "Exponential",
    "ed": "Out",
    "from": 0.85,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_ripple": {
  "beauty": 5,
  "cat": "basma",
  "cls": [
   "ImageLabel"
  ],
  "roles": [
   "button",
   "ripple"
  ],
  "tracks": [
   {
    "d": 0.5,
    "dl": 0,
    "e": "Quart",
    "ed": "Out",
    "from": 0.1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.8
   },
   {
    "d": 0.5,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0.4,
    "p": "ImageTransparency",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_rotate_spin": {
  "beauty": 3,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "close-button",
   "icon-button",
   "settings"
  ],
  "tracks": [
   {
    "d": 0.4,
    "dl": 0,
    "e": "Quart",
    "ed": "InOut",
    "from": 0,
    "p": "Rotation",
    "rep": 0,
    "rev": false,
    "t": "self",
    "to": 360
   }
  ],
  "trig": "click"
 },
 "press_select_pop": {
  "beauty": 3,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "icon-button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.12,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.05
   },
   {
    "d": 0.2,
    "dl": 0.12,
    "e": "Quad",
    "ed": "Out",
    "from": 1.05,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_shake": {
  "beauty": 3,
  "cat": "basma",
  "cls": [
   "Frame",
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "close-button",
   "slot"
  ],
  "tracks": [
   {
    "d": 0.08,
    "dl": 0,
    "e": "Sine",
    "ed": "InOut",
    "from": -5,
    "p": "Rotation",
    "rep": 3,
    "rev": true,
    "t": "self",
    "to": 5
   }
  ],
  "trig": "click"
 },
 "press_shrink_bounce": {
  "beauty": 4,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "close-button",
   "icon-button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.08,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 0.9
   },
   {
    "d": 0.22,
    "dl": 0.08,
    "e": "Back",
    "ed": "Out",
    "from": 0.9,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "press_shrink_only": {
  "beauty": 2,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "close-button"
  ],
  "tracks": [
   {
    "d": 0.1,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 0.93
   }
  ],
  "trig": "mouseDown"
 },
 "press_squash": {
  "beauty": 4,
  "cat": "basma",
  "cls": [
   "ImageButton",
   "ImageLabel"
  ],
  "roles": [
   "button",
   "primary-button"
  ],
  "tracks": [
   {
    "d": 0.1,
    "dl": 0,
    "e": "Quint",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.12
   },
   {
    "d": 0.09,
    "dl": 0.1,
    "e": "Sine",
    "ed": "InOut",
    "from": -4,
    "p": "Rotation",
    "rep": 1,
    "rev": true,
    "t": "self",
    "to": 4
   },
   {
    "d": 0.2,
    "dl": 0.18,
    "e": "Back",
    "ed": "Out",
    "from": 1.12,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1
   }
  ],
  "trig": "click"
 },
 "select_outline_pop": {
  "beauty": 4,
  "cat": "secim",
  "cls": [
   "ImageButton",
   "TextButton"
  ],
  "roles": [
   "button",
   "card",
   "slot",
   "tab"
  ],
  "tracks": [
   {
    "d": 0.2,
    "dl": 0,
    "e": "Quad",
    "ed": "Out",
    "from": 0,
    "p": "Thickness",
    "rep": 0,
    "rev": false,
    "t": "UIStroke",
    "to": 3
   },
   {
    "d": 0.2,
    "dl": 0,
    "e": "Back",
    "ed": "Out",
    "from": 1,
    "p": "Scale",
    "rep": 0,
    "rev": false,
    "t": "UIScale",
    "to": 1.03
   }
  ],
  "trig": "stateChange"
 }
};
// <<END_EI_ANIM_DATA>>

  var STYLE_BIAS = { cartoon: { basma: 1.3 } };

  // LocalScript şablonu (Lua'daki TEMPLATE ile aynı metin)
  var TEMPLATE = "-- EasyImport animasyon (otomatik üretildi — istersen düzenle).\n-- UI başına tek LocalScript (KARARLAR L3). Motor: TweenService (L1). UIShadow glow yok (L10).\nlocal TweenService = game:GetService(\"TweenService\")\nlocal root = script.Parent\nlocal ANIMS = __ANIMS__\nlocal BINDINGS = __BINDINGS__\nlocal ACTIONS = __ACTIONS__\nlocal PANEL_IDS = __PANELS__\nlocal GROUP_IDS = __GROUPS__\n\n-- BASE: hover/seçim öncesi değer. Çıkış (leave) animasyonu buraya döner.\nlocal BASE = {}\nlocal function baseOf(o, p)\n\tBASE[o] = BASE[o] or {}\n\tif BASE[o][p] == nil then\n\t\tlocal ok, v = pcall(function() return o[p] end)\n\t\tif ok then BASE[o][p] = v end\n\tend\n\treturn BASE[o][p]\nend\n\nlocal function holder(inst, t)\n\tif t == \"self\" then return inst end\n\tif t == \"parent\" then return inst.Parent end\n\tlocal found = inst:FindFirstChildOfClass(t)\n\tif found then return found end\n\tif t == \"UIScale\" then\n\t\tlocal s = Instance.new(\"UIScale\")\n\t\ts.Parent = inst\n\t\treturn s\n\tend\n\tif t == \"UIStroke\" then\n\t\tlocal s = Instance.new(\"UIStroke\")\n\t\ts.Thickness = 0\n\t\ts.Color = Color3.new(1, 1, 1)\n\t\ts.Parent = inst\n\t\treturn s\n\tend\n\tif t == \"UIGradient\" then\n\t\t-- Kenarlık gradyanı: önce kenarlığın (UIStroke) içindeki gradyan; yoksa kenarlık ve beyaz gradyan oluşturulur.\n\t\tlocal st = inst:FindFirstChildOfClass(\"UIStroke\")\n\t\tif not st then\n\t\t\tst = Instance.new(\"UIStroke\")\n\t\t\tst.Thickness = 2\n\t\t\tst.Color = Color3.new(1, 1, 1)\n\t\t\tst.Parent = inst\n\t\tend\n\t\tlocal g = st:FindFirstChildOfClass(\"UIGradient\")\n\t\tif not g then\n\t\t\tg = Instance.new(\"UIGradient\")\n\t\t\tg.Parent = st\n\t\tend\n\t\treturn g\n\tend\n\treturn nil\nend\n\nlocal function delayOf(dl, extra)\n\tlocal base\n\tif type(dl) == \"table\" then\n\t\tbase = dl.a + math.random() * (dl.b - dl.a)\n\telse\n\t\tbase = dl or 0\n\tend\n\treturn base + (extra or 0)\nend\n\n-- İki elemanlı değerler: Position/Size → UDim2 (piksel ofseti), diğerleri (UIGradient.Offset) → Vector2.\nlocal function toValue(p, v)\n\tif type(v) == \"table\" then\n\t\tif p == \"Position\" or p == \"Size\" then\n\t\t\treturn UDim2.fromOffset(v[1], v[2])\n\t\tend\n\t\treturn Vector2.new(v[1], v[2])\n\tend\n\treturn v\nend\n\n-- mode: \"show\" (from'a set, to'ya tween) · \"loop\" (aynı, sürekli) · \"hover\"/\"press\" (mevcut → to)\n--       · \"leave\" (BASE'e tween)\nlocal function play(inst, animId, mode, extra)\n\tlocal anim = ANIMS[animId]\n\tif not anim or not inst then return end\n\tfor _, tr in ipairs(anim.tracks) do\n\t\tpcall(function()\n\t\t\tlocal o = holder(inst, tr.t)\n\t\t\tif not o then return end\n\t\t\tlocal base = baseOf(o, tr.p)\n\t\t\tlocal goal\n\t\t\tif mode == \"leave\" then\n\t\t\t\tgoal = base\n\t\t\telse\n\t\t\t\tgoal = tr.to\n\t\t\t\tif goal == \"cur\" or goal == nil then goal = base end\n\t\t\tend\n\t\t\tif goal == nil then return end\n\t\t\tgoal = toValue(tr.p, goal)\n\t\t\tif (mode == \"show\" or mode == \"loop\") and tr.from ~= nil and tr.from ~= \"cur\" then\n\t\t\t\to[tr.p] = toValue(tr.p, tr.from)\n\t\t\tend\n\t\t\tlocal info = TweenInfo.new(tr.d, Enum.EasingStyle[tr.e], Enum.EasingDirection[tr.ed], tr.rep, tr.rev, delayOf(tr.dl, extra))\n\t\t\tTweenService:Create(o, info, { [tr.p] = goal }):Play()\n\t\tend)\n\tend\nend\n\n-- Pivot: AnchorPoint (0,0) → (0.5,0.5); konum, sol-üst köşe aynı kalacak şekilde düzeltilir.\n-- Layout (UIListLayout/UIGridLayout) yöneten kapta konum değiştirilmez.\nlocal function centerPivot(inst)\n\tif not inst:IsA(\"GuiObject\") then return end\n\tif inst.AnchorPoint ~= Vector2.new(0, 0) then return end\n\tlocal p = inst.Parent\n\tif p and (p:FindFirstChildWhichIsA(\"UIListLayout\") or p:FindFirstChildWhichIsA(\"UIGridLayout\")) then return end\n\tlocal s, pos = inst.Size, inst.Position\n\tinst.Position = UDim2.new(pos.X.Scale + s.X.Scale * 0.5, pos.X.Offset + s.X.Offset * 0.5,\n\t\tpos.Y.Scale + s.Y.Scale * 0.5, pos.Y.Offset + s.Y.Offset * 0.5)\n\tinst.AnchorPoint = Vector2.new(0.5, 0.5)\nend\n\nlocal function findById(id)\n\tfor _, d in ipairs(root:GetDescendants()) do\n\t\tif d:GetAttribute(\"EI_Id\") == id then return d end\n\tend\n\treturn nil\nend\n\n-- Seçim grupları (kalıcı _select): grup anahtarı → üyeler {inst, a}; seçili üye grup başına tek.\nlocal SELREG = {}\nlocal SELSTATE = {}\n\nlocal function selectClick(key, entry)\n\tlocal cur = SELSTATE[key]\n\tif cur == entry then\n\t\tplay(entry.inst, entry.a, \"leave\")\n\t\tSELSTATE[key] = nil\n\t\treturn\n\tend\n\tif cur then play(cur.inst, cur.a, \"leave\") end\n\tplay(entry.inst, entry.a, \"hover\")\n\tSELSTATE[key] = entry\nend\n\n-- ================================================================ EFEKTLER (kendi öğeleriyle, arka planda, parametreli)\n-- Framewisp \"Effect Playground\" benzeri: her efektin ayarları (kaydırıcılar) katmanda saklanır ve JSON ile gelir.\n-- Varsayılanlar aşağıda; JSON'da params tablosu varsa o değerler kullanılır.\nlocal FX_DEFAULTS = {\n\tfall = { count = 12, seconds = 6, fade = 0.75, smallest = 0.6, largest = 1.0 },\n\tburst = { count = 10, fade = 0.7, distance = 0.8 },\n\torbit = { count = 3, seconds = 4 },\n\ttwinkle = { count = 6, seconds = 0.6, smallest = 0.6, largest = 1.0 },\n\torb = { scale = 1.7, pulse = 1.12 },\n\tsmooth = { hover = 1.08, press = 0.9 },\n\tgleam = { sweep = 3, pause = 1, width = 0.22 },\n}\nlocal function fxParam(params, kind, key)\n\tlocal v = params and params[key]\n\tif type(v) == \"number\" then return v end\n\treturn FX_DEFAULTS[kind][key]\nend\n\nlocal FX_GOLD = { Color3.fromRGB(255, 205, 70), Color3.fromRGB(255, 225, 120), Color3.fromRGB(230, 170, 40) }\nlocal FX_CONFETTI = { Color3.fromRGB(255, 90, 90), Color3.fromRGB(90, 200, 255), Color3.fromRGB(120, 255, 140),\n\tColor3.fromRGB(255, 220, 80), Color3.fromRGB(190, 120, 255) }\n\n-- Kopyalanacak şablonların listesi (tasarım öğeleri + Figma panelinden yüklenen resimler). Yoksa nil.\nlocal function fxTemplate(inst)\n\tlocal list = {}\n\tfor _, c in ipairs(inst:GetChildren()) do\n\t\tif c:GetAttribute(\"EI_FxTpl\") then list[#list + 1] = c end\n\tend\n\tif #list == 0 then return nil end\n\treturn list\nend\n\nlocal function fxLayer(inst)\n\tlocal w, h = 200, 120\n\tlocal ok, sz = pcall(function() return inst.AbsoluteSize end)\n\tif ok and sz and sz.X > 0 and sz.Y > 0 then w, h = sz.X, sz.Y end\n\tlocal layer = inst:FindFirstChild(\"EI_FX\")\n\tif not layer then\n\t\tlayer = Instance.new(\"Frame\")\n\t\tlayer.Name = \"EI_FX\"\n\t\tlayer.BackgroundTransparency = 1\n\t\tlayer.BorderSizePixel = 0\n\t\tlayer.Size = UDim2.new(1, 0, 1, 0)\n\t\tlayer.ClipsDescendants = true\n\t\tlayer.ZIndex = 0\n\t\tlayer.Parent = inst\n\tend\n\treturn layer, w, h\nend\n\n-- Tek parça: şablonun kopyası (tasarım öğesi) ya da yedek renkli kare. Her parçada UIScale vardır.\nlocal function fxSpawn(tpl, layer, w, h, color, smin, smax)\n\tlocal p\n\tif type(tpl) == \"table\" then tpl = tpl[math.random(#tpl)] end -- birden çok şablon: her parça rastgele birini kopyalar\n\tif tpl then\n\t\tlocal ok, c = pcall(function() return tpl:Clone() end)\n\t\tif ok and c then p = c end\n\tend\n\tif not p then\n\t\tp = Instance.new(\"Frame\")\n\t\tp.BorderSizePixel = 0\n\t\tp.BackgroundColor3 = color\n\t\tp.Size = UDim2.fromOffset(math.max(4, math.floor(w * 0.06)), math.max(4, math.floor(w * 0.06)))\n\t\tlocal c = Instance.new(\"UICorner\")\n\t\tc.CornerRadius = UDim.new(1, 0)\n\t\tc.Parent = p\n\tend\n\tp.Visible = true\n\tp.AnchorPoint = Vector2.new(0.5, 0.5)\n\tp.ZIndex = 0\n\tlocal sc = Instance.new(\"UIScale\")\n\tsc.Scale = smin + math.random() * (smax - smin)\n\tsc.Parent = p\n\tp.Parent = layer\n\treturn p\nend\n\nlocal function fxTween(o, d, style, dir, rep, rev, goal)\n\tlocal info = TweenInfo.new(d, Enum.EasingStyle[style], Enum.EasingDirection[dir], rep, rev, 0)\n\tlocal t = TweenService:Create(o, info, goal)\n\tt:Play()\n\treturn t\nend\n\nlocal function fxDone(t, f)\n\tpcall(function() t.Completed:Connect(f) end)\nend\n\n-- Yağmur (fall): count parça, seconds süreyle üstten düşer. Parça aralığı = seconds / count. Sürekli.\nlocal function startFall(inst, params, confetti)\n\tlocal layer, w, h = fxLayer(inst)\n\tlocal tpl = fxTemplate(inst)\n\tlocal count = math.max(1, fxParam(params, \"fall\", \"count\"))\n\tlocal seconds = math.max(0.2, fxParam(params, \"fall\", \"seconds\"))\n\tlocal fade = fxParam(params, \"fall\", \"fade\")\n\tlocal smin, smax = fxParam(params, \"fall\", \"smallest\"), fxParam(params, \"fall\", \"largest\")\n\ttask.spawn(function()\n\t\twhile layer.Parent do\n\t\t\tlocal color = confetti and FX_CONFETTI[math.random(#FX_CONFETTI)] or FX_GOLD[math.random(#FX_GOLD)]\n\t\t\tlocal p = fxSpawn(tpl, layer, w, h, color, smin, smax)\n\t\t\tpcall(function() p.ImageTransparency = 1 - fade end)\n\t\t\tpcall(function() p.BackgroundTransparency = 1 - fade end)\n\t\t\tlocal x = math.random() * w\n\t\t\tp.Position = UDim2.fromOffset(x, -20)\n\t\t\tlocal t = fxTween(p, seconds, \"Linear\", \"In\", 0, false,\n\t\t\t\t{ Position = UDim2.fromOffset(x, h + 20), Rotation = math.random(-360, 360) })\n\t\t\tfxDone(t, function() p:Destroy() end)\n\t\t\ttask.wait(seconds / count)\n\t\tend\n\tend)\nend\n\n-- Patlama (burst): count parça merkezden distance kadar dağılır; fade başlangıç opaklığı.\nlocal function startBurst(inst, params)\n\tlocal layer, w, h = fxLayer(inst)\n\tlocal tpl = fxTemplate(inst)\n\tlocal n = math.max(1, math.floor(fxParam(params, \"burst\", \"count\")))\n\tlocal fade = fxParam(params, \"burst\", \"fade\")\n\tlocal dist = fxParam(params, \"burst\", \"distance\")\n\tfor i = 1, n do\n\t\tlocal p = fxSpawn(tpl, layer, w, h, FX_CONFETTI[(i % #FX_CONFETTI) + 1], 0.6, 0.9)\n\t\tpcall(function() p.ImageTransparency = 1 - fade end)\n\t\tpcall(function() p.BackgroundTransparency = 1 - fade end)\n\t\tp.Position = UDim2.fromOffset(w / 2, h / 2)\n\t\tlocal ang = (i / n) * math.pi * 2\n\t\tlocal r = math.min(w, h) * dist * (0.7 + math.random() * 0.3)\n\t\tlocal t = fxTween(p, 0.7, \"Quad\", \"Out\", 0, false,\n\t\t\t{ Position = UDim2.fromOffset(w / 2 + math.cos(ang) * r, h / 2 + math.sin(ang) * r),\n\t\t\t  Rotation = math.random(-180, 180) })\n\t\tpcall(fxTween, p, 0.7, \"Quad\", \"Out\", 0, false, { ImageTransparency = 1 })\n\t\tpcall(fxTween, p, 0.7, \"Quad\", \"Out\", 0, false, { BackgroundTransparency = 1 })\n\t\tfxDone(t, function() p:Destroy() end)\n\tend\nend\n\n-- Yörünge (orbit): count parça merkez etrafında döner; seconds = bir tam tur süresi.\nlocal function startOrbit(inst, params)\n\tlocal layer, w, h = fxLayer(inst)\n\tlocal tpl = fxTemplate(inst)\n\tlocal n = math.max(1, math.floor(fxParam(params, \"orbit\", \"count\")))\n\tlocal seconds = math.max(0.5, fxParam(params, \"orbit\", \"seconds\"))\n\tlocal r = math.min(w, h) * 0.42\n\tlocal step = seconds / 12\n\tfor k = 1, n do\n\t\ttask.spawn(function()\n\t\t\tlocal p = fxSpawn(tpl, layer, w, h, FX_GOLD[(k % #FX_GOLD) + 1], 0.5, 0.7)\n\t\t\tlocal a = (k / n) * math.pi * 2\n\t\t\twhile layer.Parent do\n\t\t\t\tfxTween(p, step, \"Linear\", \"Out\", 0, false,\n\t\t\t\t\t{ Position = UDim2.fromOffset(w / 2 + math.cos(a) * r, h / 2 + math.sin(a) * r) })\n\t\t\t\ta = a + math.pi / 6\n\t\t\t\ttask.wait(step)\n\t\t\tend\n\t\tend)\n\tend\nend\n\n-- Parıltı (twinkle): count / seconds sıklıkta rastgele noktalarda kopya büyüyüp söner. Sürekli.\nlocal function startTwinkle(inst, params)\n\tlocal layer, w, h = fxLayer(inst)\n\tlocal tpl = fxTemplate(inst)\n\tlocal count = math.max(1, fxParam(params, \"twinkle\", \"count\"))\n\tlocal seconds = math.max(0.2, fxParam(params, \"twinkle\", \"seconds\"))\n\tlocal smin, smax = fxParam(params, \"twinkle\", \"smallest\"), fxParam(params, \"twinkle\", \"largest\")\n\ttask.spawn(function()\n\t\twhile layer.Parent do\n\t\t\tlocal p = fxSpawn(tpl, layer, w, h, Color3.fromRGB(255, 250, 200), smin, smax)\n\t\t\tp.Position = UDim2.fromOffset(math.random() * w, math.random() * h)\n\t\t\tlocal sc = p:FindFirstChildOfClass(\"UIScale\")\n\t\t\tif sc then sc.Scale = 0 end\n\t\t\tlocal t = fxTween(sc or p, seconds, \"Sine\", \"InOut\", 1, true, sc and { Scale = 1 } or { Size = UDim2.fromOffset(12, 12) })\n\t\t\tfxDone(t, function() p:Destroy() end)\n\t\t\ttask.wait(seconds / count)\n\t\tend\n\tend)\nend\n\n-- Işık süpürme (sweep): eğik yarı saydam bir çubuk öğenin üzerinden geçer. Sürekli. (Şablon gerektirmez.)\nlocal function startSweep(inst)\n\tlocal layer, w, h = fxLayer(inst)\n\ttask.spawn(function()\n\t\twhile layer.Parent do\n\t\t\tlocal bar = Instance.new(\"Frame\")\n\t\t\tbar.BorderSizePixel = 0\n\t\t\tbar.BackgroundColor3 = Color3.fromRGB(255, 255, 255)\n\t\t\tbar.BackgroundTransparency = 0.82\n\t\t\tbar.AnchorPoint = Vector2.new(0.5, 0.5)\n\t\t\tbar.Size = UDim2.fromOffset(math.floor(w * 0.35), math.floor(h * 2.2))\n\t\t\tbar.Rotation = 20\n\t\t\tbar.Position = UDim2.fromOffset(-w * 0.4, h / 2)\n\t\t\tbar.Parent = layer\n\t\t\tlocal t = fxTween(bar, 1.6, \"Quad\", \"InOut\", 0, false, { Position = UDim2.fromOffset(w * 1.4, h / 2) })\n\t\t\tfxDone(t, function() bar:Destroy() end)\n\t\t\ttask.wait(1.9)\n\t\tend\n\tend)\nend\n\n-- Dev hale (orb): öğenin arkasında büyük yumuşak daire; scale = çap, pulse = nefes büyüklüğü. Sürekli.\nlocal function startOrb(inst, params)\n\tlocal _, w, h = fxLayer(inst)\n\tlocal d = math.max(w, h) * fxParam(params, \"orb\", \"scale\")\n\tlocal orb = Instance.new(\"Frame\")\n\torb.BorderSizePixel = 0\n\torb.BackgroundColor3 = Color3.fromRGB(255, 220, 120)\n\torb.BackgroundTransparency = 0.88\n\torb.Size = UDim2.fromOffset(d, d)\n\torb.AnchorPoint = Vector2.new(0.5, 0.5)\n\torb.Position = UDim2.fromOffset(w / 2, h / 2)\n\torb.ZIndex = 0\n\tlocal c = Instance.new(\"UICorner\")\n\tc.CornerRadius = UDim.new(1, 0)\n\tc.Parent = orb\n\torb.Parent = inst\n\tlocal pulse = fxParam(params, \"orb\", \"pulse\")\n\tfxTween(orb, 1.6, \"Sine\", \"InOut\", -1, true, { Size = UDim2.fromOffset(d * pulse, d * pulse), BackgroundTransparency = 0.75 })\nend\n\n-- Büyüme (smooth): buton üzerine gelince hover ölçeği, basınca press ölçeği. Yalnız GuiButton.\nlocal function startSmooth(inst, params)\n\tif not inst:IsA(\"GuiButton\") then return end\n\tcenterPivot(inst)\n\tlocal hover = fxParam(params, \"smooth\", \"hover\")\n\tlocal press = fxParam(params, \"smooth\", \"press\")\n\tlocal sc = holder(inst, \"UIScale\")\n\tlocal hov = false\n\tlocal function go(v)\n\t\tfxTween(sc, 0.12, \"Quad\", \"Out\", 0, false, { Scale = v })\n\tend\n\tinst.MouseEnter:Connect(function() hov = true; go(hover) end)\n\tinst.MouseLeave:Connect(function() hov = false; go(1) end)\n\tinst.MouseButton1Down:Connect(function() go(press) end)\n\tinst.MouseButton1Up:Connect(function() go(hov and hover or 1) end)\nend\n\n-- Işık süpürme metinde (gleam): yazının üzerinden parlak bir bant sürekli geçer. sweep: geçiş süresi,\n-- pause: geçişler arası bekleme, width: bandın genişliği (0–1). Yalnız metin öğeleri.\nlocal function startGleam(inst, params)\n\tif not (inst:IsA(\"TextLabel\") or inst:IsA(\"TextButton\")) then return end\n\tlocal sweep = math.max(0.2, fxParam(params, \"gleam\", \"sweep\"))\n\tlocal pause = math.max(0, fxParam(params, \"gleam\", \"pause\"))\n\tlocal width = fxParam(params, \"gleam\", \"width\")\n\tlocal half = math.min(0.45, math.max(0.02, width / 2))\n\tlocal g = Instance.new(\"UIGradient\")\n\tg.Color = ColorSequence.new(Color3.fromRGB(255, 255, 255))\n\tg.Transparency = NumberSequence.new({\n\t\tNumberSequenceKeypoint.new(0, 1),\n\t\tNumberSequenceKeypoint.new(0.5 - half, 1),\n\t\tNumberSequenceKeypoint.new(0.5, 0),\n\t\tNumberSequenceKeypoint.new(0.5 + half, 1),\n\t\tNumberSequenceKeypoint.new(1, 1),\n\t})\n\tg.Parent = inst\n\ttask.spawn(function()\n\t\twhile inst.Parent do\n\t\t\tg.Offset = Vector2.new(-1, 0)\n\t\t\tfxTween(g, sweep, \"Linear\", \"InOut\", 0, false, { Offset = Vector2.new(1, 0) })\n\t\t\ttask.wait(sweep + pause)\n\t\tend\n\tend)\nend\n\nlocal function startFx(inst, kind, params)\n\tif kind == \"tpl\" then return end -- şablon: pre-pass'te gizlendi, kopyalanır\n\tif kind == \"fall\" then return startFall(inst, params, false) end\n\tif kind == \"confetti\" then return startFall(inst, params, true) end\n\tif kind == \"burst\" then\n\t\tlocal function go() pcall(startBurst, inst, params) end\n\t\tif inst:IsA(\"GuiButton\") then\n\t\t\tinst.MouseButton1Down:Connect(go)\n\t\telse\n\t\t\tgo()\n\t\tend\n\t\treturn\n\tend\n\tlocal runners = {\n\t\torbit = startOrbit, twinkle = startTwinkle, sweep = function(i) return startSweep(i) end,\n\t\torb = startOrb, smooth = startSmooth, gleam = startGleam,\n\t}\n\tlocal f = runners[kind]\n\tif f then pcall(f, inst, params) end\nend\n\n-- Şablonları önce gizle ve işaretle (kapsayıcılar bunları aramadan önce).\nfor _, b in ipairs(BINDINGS) do\n\tif b.fx == \"tpl\" then\n\t\tlocal inst = findById(b.id)\n\t\tif inst then\n\t\t\tinst:SetAttribute(\"EI_FxTpl\", true)\n\t\t\tpcall(function() inst.Visible = false end)\n\t\tend\n\tend\nend\n\nfor _, b in ipairs(BINDINGS) do\n\tlocal inst = findById(b.id)\n\tif inst then\n\t\tpcall(function()\n\t\t\tif b.hover or b.press or b.selA then centerPivot(inst) end\n\t\t\tif b.show then play(inst, b.show, \"show\", b.delay) end\n\t\t\tif b.loop then play(inst, b.loop, \"loop\", 0) end\n\t\t\tif b.fx then startFx(inst, b.fx, b.params) end\n\t\t\tif inst:IsA(\"GuiButton\") then\n\t\t\t\tif b.hover then\n\t\t\t\t\tinst.MouseEnter:Connect(function() play(inst, b.hover, \"hover\") end)\n\t\t\t\t\tinst.MouseLeave:Connect(function() play(inst, b.hover, \"leave\") end)\n\t\t\t\tend\n\t\t\t\tif b.press then\n\t\t\t\t\tinst.MouseButton1Down:Connect(function() play(inst, b.press, \"press\") end)\n\t\t\t\tend\n\t\t\tend\n\t\t\tif b.selA and b.sel ~= nil then\n\t\t\t\tSELREG[b.sel] = SELREG[b.sel] or {}\n\t\t\t\ttable.insert(SELREG[b.sel], { inst = inst, a = b.selA })\n\t\t\tend\n\t\tend)\n\tend\nend\n\nfor key, members in pairs(SELREG) do\n\tfor _, entry in ipairs(members) do\n\t\tif entry.inst:IsA(\"GuiButton\") then\n\t\t\tentry.inst.MouseButton1Click:Connect(function() selectClick(key, entry) end)\n\t\tend\n\tend\nend\n\n-- ================================================================ ETKİLEŞİM (paneller, sekmeler) + CANLI VERİ\n-- Paneller: _panel etiketli (başlangıçta gizli). _open:Ad / _toggle:Ad / _close / _tab:Ad (gruplu sekme).\n-- Açılan panelde, içindeki öğelerin giriş animasyonları yeniden oynar (_pop/_fadein/_reveal… her açılışta).\nlocal MAP = {}\nfor _, d in ipairs(root:GetDescendants()) do\n\tlocal mid = d:GetAttribute(\"EI_Id\")\n\tif mid then MAP[mid] = d end\nend\nlocal PANEL_SET = {}\nfor _, pid in ipairs(PANEL_IDS) do PANEL_SET[pid] = true end\nlocal GROUP_SET = {}\nfor _, gid in ipairs(GROUP_IDS) do GROUP_SET[gid] = true end\n\nlocal function replayIn(panel)\n\tlocal pid = panel:GetAttribute(\"EI_Id\")\n\tfor _, b in ipairs(BINDINGS) do\n\t\tif b.show then\n\t\t\tlocal d = MAP[b.id]\n\t\t\tif d and d ~= panel and d:IsDescendantOf(panel) then\n\t\t\t\tpcall(play, d, b.show, \"show\", b.delay)\n\t\t\tend\n\t\tend\n\tend\n\tfor _, b in ipairs(BINDINGS) do\n\t\tif b.show and b.id == pid then\n\t\t\tpcall(play, panel, b.show, \"show\", b.delay)\n\t\tend\n\tend\nend\n\nlocal function openPanel(p)\n\tif not p then return end\n\tp.Visible = true\n\treplayIn(p)\nend\n\n-- Buton bir panelin içindeyse en yakın _panel atası (kapatma için).\nlocal function nearestPanel(d)\n\tlocal p = d.Parent\n\twhile p and p ~= root do\n\t\tlocal pid = p:GetAttribute(\"EI_Id\")\n\t\tif pid and PANEL_SET[pid] then return p end\n\t\tp = p.Parent\n\tend\n\treturn nil\nend\n\n-- Panel yoksa: ScreenGui'nin doğrudan çocuğu olan üst kapsayıcı (import kökü).\nlocal function topBelowRoot(d)\n\tlocal p = d\n\twhile p and p.Parent and p.Parent ~= root do p = p.Parent end\n\treturn p\nend\n\nlocal function closeTarget(btn, targetId)\n\tif targetId then return MAP[targetId] end\n\treturn nearestPanel(btn) or topBelowRoot(btn)\nend\n\n-- Sekme grubu: en yakın _tabgroup atası; yoksa \"0\" (kök).\nlocal function groupOf(btn)\n\tlocal p = btn.Parent\n\twhile p and p ~= root do\n\t\tlocal gid = p:GetAttribute(\"EI_Id\")\n\t\tif gid and GROUP_SET[gid] then return gid end\n\t\tp = p.Parent\n\tend\n\treturn 0\nend\n\nlocal TAB_BY_GROUP = {}\nfor _, a in ipairs(ACTIONS) do\n\tlocal btn = MAP[a.id]\n\tif btn and a.kind == \"tab\" then\n\t\tlocal g = groupOf(btn)\n\t\tTAB_BY_GROUP[g] = TAB_BY_GROUP[g] or {}\n\t\ttable.insert(TAB_BY_GROUP[g], a)\n\tend\nend\n\n-- Başlangıç: her sekme grubunda ilk sekmenin paneli açık, diğerleri kapalı.\nfor _, list in pairs(TAB_BY_GROUP) do\n\tfor i, a in ipairs(list) do\n\t\tlocal t = MAP[a.target]\n\t\tif t and i > 1 then t.Visible = false end\n\tend\n\tif list[1] then openPanel(MAP[list[1].target]) end\nend\n\nfor _, a in ipairs(ACTIONS) do\n\tlocal btn = MAP[a.id]\n\tif btn and btn:IsA(\"GuiButton\") then\n\t\tbtn.MouseButton1Click:Connect(function()\n\t\t\tif a.kind == \"open\" then\n\t\t\t\topenPanel(MAP[a.target])\n\t\t\telseif a.kind == \"close\" then\n\t\t\t\tlocal t = closeTarget(btn, a.target)\n\t\t\t\tif t then t.Visible = false end\n\t\t\telseif a.kind == \"toggle\" then\n\t\t\t\tlocal t = MAP[a.target]\n\t\t\t\tif t then\n\t\t\t\t\tif t.Visible then t.Visible = false else openPanel(t) end\n\t\t\t\tend\n\t\t\telseif a.kind == \"tab\" then\n\t\t\t\tlocal target = MAP[a.target]\n\t\t\t\tfor _, o in ipairs(TAB_BY_GROUP[groupOf(btn)] or {}) do\n\t\t\t\t\tlocal ot = MAP[o.target]\n\t\t\t\t\tif ot and ot ~= target then ot.Visible = false end\n\t\t\t\tend\n\t\t\t\topenPanel(target)\n\t\t\tend\n\t\tend)\n\tend\nend\n\n";

  function lowerAscii(s) {
    return String(s == null ? '' : s).replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  }
  function containsAny(s, words) {
    for (var i = 0; i < words.length; i++) if (s.indexOf(words[i]) !== -1) return true;
    return false;
  }
  function listHas(list, v) {
    for (var i = 0; i < list.length; i++) if (list[i] === v) return true;
    return false;
  }

  // Rol çıkarımı — Lua roleOf ile BİREBİR aynı kural sırası.
  function roleOf(el) {
    var n = lowerAscii(el.name);
    var c = el.cls;
    if (c === 'TextButton' || c === 'ImageButton') {
      if (containsAny(n, ['close', 'kapat']) || n.slice(-2) === '_x') return 'close-button';
      if (containsAny(n, ['primary'])) return 'primary-button';
      if (containsAny(n, ['icon'])) return 'icon-button';
      return 'button';
    }
    if (containsAny(n, ['card'])) return 'card';
    if (containsAny(n, ['modal', 'popup'])) return 'modal';
    if (containsAny(n, ['title', 'baslik'])) return 'title';
    if (containsAny(n, ['icon', 'ikon'])) return 'icon';
    if (containsAny(n, ['tab'])) return 'tab';
    if (containsAny(n, ['panel', 'frame'])) return 'panel';
    if (c === 'TextLabel') return 'label';
    if (c === 'ImageLabel') return 'icon';
    return 'panel';
  }

  // Statik aday sırası (skor ↓, eşitlikte id ↑). Önce rol eşleşmesi, yoksa sınıf.
  function staticCandidates(cat, cls, role, style) {
    var bias = (STYLE_BIAS[style] && STYLE_BIAS[style][cat]) || 1;
    for (var pass = 1; pass <= 2; pass++) {
      var list = [];
      for (var i = 0; i < ANIM_IDS.length; i++) {
        var id = ANIM_IDS[i], a = ANIM_LIB[id];
        if (a.cat === cat && listHas(a.cls, cls) && (pass === 2 || listHas(a.roles, role))) list.push(id);
      }
      if (list.length > 0) {
        list.sort(function (x, y) {
          var sx = ANIM_LIB[x].beauty * bias, sy = ANIM_LIB[y].beauty * bias;
          if (sx !== sy) return sy - sx;
          return x < y ? -1 : (x > y ? 1 : 0);
        });
        return list;
      }
    }
    return [];
  }

  function learnedObs(learn, ctx) {
    var m = learn && learn.anim ? learn.anim[ctx] : null;
    if (!m) return 0;
    var t = 0;
    for (var k in m) if (Object.prototype.hasOwnProperty.call(m, k)) t += m[k][0] + m[k][1];
    return t;
  }

  // Seçici için sıralı seçenekler (ilk = varsayılan). Gözlem yoksa statik sıra.
  function options(cls, role, cat, style, learn) {
    var list = staticCandidates(cat, cls, role, style);
    if (learn && list.length > 0) {
      var ctx = EILearn.ctxKey(style, cls, role, cat);
      if (learnedObs(learn, ctx) > 0) list = EILearn.rankAnim(learn, ctx, list);
    }
    return list;
  }

  function pickAnim(cat, cls, role, style, learn) {
    return options(cls, role, cat, style, learn)[0];
  }

  // elements: [{id, name, cls, depth}] · Dönüş: [{id, cls, role, show?, hover?, press?}]
  function plan(elements, style, learn) {
    var out = [];
    for (var i = 0; i < elements.length; i++) {
      var el = elements[i];
      var role = roleOf(el);
      var isBtn = (el.cls === 'TextButton' || el.cls === 'ImageButton');
      var b = { id: el.id, cls: el.cls, role: role };
      if (el.depth <= 1) b.show = pickAnim('giris', el.cls, role, style, learn);
      if (isBtn) {
        b.hover = pickAnim('hover', el.cls, role, style, learn);
        b.press = pickAnim('basma', el.cls, role, style, learn);
      }
      if (b.show || b.hover || b.press) out.push(b);
    }
    return out;
  }

  // ---------------------------------------------------------------- Lua literal yazıcı (lit ile birebir)
  function fmtG(x) {
    if (Number.isInteger(x)) return String(x);
    return String(Number(x.toPrecision(6)));
  }
  var LUA_KW = ['and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'if', 'in', 'local',
    'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while'];
  function lit(v) {
    if (typeof v === 'number') return fmtG(v);
    if (typeof v === 'boolean') return v ? 'true' : 'false';
    if (typeof v === 'string') {
      // Kaçış (Lua lit ile birebir): ters eğik çizgi, tırnak, satır sonu
      return '"' + v.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n') + '"';
    }
    if (Array.isArray(v)) {
      if (v.length > 0) return '{' + v.map(lit).join(', ') + '}';
      return '{}';
    }
    var keys = Object.keys(v).filter(function (k) { return v[k] !== undefined; }).sort();
    return '{' + keys.map(function (k) {
      var kk = (LUA_KW.indexOf(k) !== -1 || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(k)) ? '["' + k + '"]' : k;
      return kk + ' = ' + lit(v[k]);
    }).join(', ') + '}';
  }

  // bindings: plan() çıktısı → LocalScript kaynağı (Lua buildSource ile birebir)
  function buildSource(bindings) {
    var used = {}, usedIds = [], bl = [];
    for (var i = 0; i < bindings.length; i++) {
      var b = bindings[i];
      var item = { id: b.id };
      var keys = ['show', 'hover', 'press', 'loop', 'selA'];
      for (var k = 0; k < keys.length; k++) {
        var key = keys[k];
        if (b[key]) {
          item[key] = b[key];
          if (!used[b[key]]) { used[b[key]] = true; usedIds.push(b[key]); }
        }
      }
      if (b.sel !== undefined) item.sel = b.sel;
      if (b.fx) item.fx = b.fx;
      if (b.delay !== undefined && b.delay > 0) item.delay = b.delay;
      bl.push(item);
    }
    usedIds.sort();
    var animTable = [];
    for (var u = 0; u < usedIds.length; u++) {
      var id = usedIds[u], a = ANIM_LIB[id], tracks = [];
      for (var t = 0; t < a.tracks.length; t++) {
        var tr = a.tracks[t];
        var dl = tr.dl;
        if (dl !== null && typeof dl === 'object') dl = { a: dl.a, b: dl.b, rnd: true };
        tracks.push({ t: tr.t, p: tr.p, from: tr.from, to: tr.to, d: tr.d, dl: dl, e: tr.e, ed: tr.ed, rep: tr.rep, rev: tr.rev });
      }
      animTable.push('["' + id + '"] = { tracks = ' + lit(tracks) + ' }');
    }
    var src = TEMPLATE;
    src = src.replace('__ANIMS__', function () { return '{\n\t' + animTable.join(',\n\t') + '\n}'; });
    src = src.replace('__BINDINGS__', function () { return lit(bl); });
    // Etkileşim yer tutucuları (bu API'de boş; Lua varsayılanı {} ile aynı)
    src = src.replace('__ACTIONS__', '{}').replace('__PANELS__', '{}').replace('__GROUPS__', '{}');
    return src;
  }

  // ================================================================ v11: TASARIM KARARI (madde 3 + P1)
  // Lua'daki decideRanked ile BİREBİR aynı kurallar (parite: verify_anim_parity.py).
  var STYLE_TOKENS = {
    stud: ['fade', 'scale_up', 'shrink_only', 'glow', 'lift', 'brighten', 'soft', 'reveal'],
    anime: ['elastic', 'flip', 'rotate', 'bounce', 'pop', 'spring', 'grow', 'swing'],
    cartoon: ['punch', 'squash', 'shake', 'bounce', 'pop', 'wiggle', 'shrink']
  };
  var TOKEN_BONUS = 1.5;
  var CASCADE_STEP = 0.06;
  var CASCADE_MIN = 3;
  var LOOP_MAX = 3;
  var SELECT_MIN = 2;

  function tokenBonus(id, style) {
    var toks = Object.prototype.hasOwnProperty.call(STYLE_TOKENS, style) ? STYLE_TOKENS[style] : null;
    if (!toks) return 1;
    for (var i = 0; i < toks.length; i++) if (id.indexOf(toks[i]) !== -1) return TOKEN_BONUS;
    return 1;
  }

  function scoredCandidates(cat, cls, role, style) {
    var bias = (STYLE_BIAS[style] && STYLE_BIAS[style][cat]) || 1;
    for (var pass = 1; pass <= 2; pass++) {
      var list = [];
      for (var i = 0; i < ANIM_IDS.length; i++) {
        var id = ANIM_IDS[i], a = ANIM_LIB[id];
        if (a.cat === cat && listHas(a.cls, cls) && (pass === 2 || listHas(a.roles, role))) list.push(id);
      }
      if (list.length > 0) {
        var score = {};
        for (var k = 0; k < list.length; k++) score[list[k]] = ANIM_LIB[list[k]].beauty * bias * tokenBonus(list[k], style);
        list.sort(function (x, y) {
          if (score[x] !== score[y]) return score[y] - score[x];
          return x < y ? -1 : (x > y ? 1 : 0);
        });
        return list;
      }
    }
    return [];
  }

  function rankFor(cat, cls, role, style, learn) {
    var list = scoredCandidates(cat, cls, role, style);
    if (learn && list.length > 0) {
      var ctx = EILearn.ctxKey(style, cls, role, cat);
      if (learnedObs(learn, ctx) > 0) list = EILearn.rankAnim(learn, ctx, list);
    }
    return list;
  }

  function learnedFor(learn, style, pe, cat) {
    if (!learn) return false;
    return learnedObs(learn, EILearn.ctxKey(style, pe.cls, pe.role, cat)) > 0;
  }

  function applyConsensus(per, cat, style, learn) {
    var groups = {};
    for (var i = 0; i < per.length; i++) {
      var pe = per[i], list = pe.rank[cat];
      if (list && list.length > 0 && !learnedFor(learn, style, pe, cat) && !pe.tagged[cat]) {
        if (!Object.prototype.hasOwnProperty.call(groups, pe.cls)) groups[pe.cls] = [];
        groups[pe.cls].push(i);
      }
    }
    var order = Object.keys(groups).sort();
    for (var g = 0; g < order.length; g++) {
      var mem = groups[order[g]];
      if (mem.length < 2) continue;
      var tally = {};
      for (var m = 0; m < mem.length; m++) {
        var top = per[mem[m]].rank[cat][0];
        tally[top] = (tally[top] || 0) + 1;
      }
      var best = null, bestN = 0;
      var keys = Object.keys(tally);
      for (var t = 0; t < keys.length; t++) {
        var id = keys[t], n = tally[id];
        if (best === null || n > bestN || (n === bestN && id < best)) { best = id; bestN = n; }
      }
      if (best !== null && bestN * 2 >= mem.length) {
        for (var q = 0; q < mem.length; q++) {
          var idx = mem[q], list2 = per[idx].rank[cat];
          if (list2.indexOf(best) === -1) continue;
          var nl = [best];
          for (var r = 0; r < list2.length; r++) if (list2[r] !== best) nl.push(list2[r]);
          per[idx].rank[cat] = nl;
        }
      }
    }
  }

  // ETİKETLER (Framewisp benzeri): katman adında "_etiket" geçerse o animasyon seçilir.
  var TAG_ANIM = {
    pop: 'enter_pop_scale', fade: 'enter_fade', slide: 'enter_slide_up', zoom: 'enter_zoom_in',
    rotate: 'enter_rotate_in', elastic: 'enter_elastic_pop', drop: 'enter_bounce_drop', punch: 'enter_punch',
    reveal: 'enter_reveal_showcase', swing: 'enter_swing_door', flip: 'enter_flip_in', stagger: 'enter_stagger_list',
    lift: 'hover_lift', turn: 'hover_turn_card', glow: 'hover_glow', tilt: 'hover_rotate_tilt',
    stroke: 'hover_stroke_grow', brighten: 'hover_brighten', shine: 'hover_shine_sweep', bounce: 'hover_bounce_small',
    squish: 'press_squash', ripple: 'press_ripple',
    pulse: 'loop_pulse_scale', float: 'loop_float', blink: 'loop_blink_cta', wiggle: 'loop_wiggle_icon',
    border: 'loop_border_spin', kenar: 'loop_border_spin', spin: 'loop_rotate_slow',
    breathe: 'loop_breathe_transparency', shimmer: 'loop_shimmer', bobble: 'loop_bobble', ring: 'loop_expand_ring',
    shake: 'attention_shake_strong', ping: 'attention_ping', bell: 'attention_bell_ring',
    select: 'select_outline_pop', secim: 'select_outline_pop'
  };
  var SLOT_OF = { giris: 'giris', hover: 'hover', basma: 'basma', dongu: 'dongu', dikkat: 'dongu', secim: 'secim' };

  function tagIds(name) {
    var out = [];
    var toks = lowerAscii(name).split(/[^a-z0-9]+/);
    for (var i = 0; i < toks.length; i++) {
      if (toks[i] && Object.prototype.hasOwnProperty.call(TAG_ANIM, toks[i])) out.push(TAG_ANIM[toks[i]]);
    }
    return out;
  }

  // Etiketleri uygular. Bir kategoride ilk etiket kazanır; öğrenme varsa öğrenme kazanır (Lua applyTags ile aynı).
  function applyTags(pe, el, learn, style) {
    var ids = tagIds(el.name);
    for (var i = 0; i < ids.length; i++) {
      var id = ids[i], a = ANIM_LIB[id];
      var slot = a ? SLOT_OF[a.cat] : undefined;
      // Buton slotları (hover/basma/secim): buton öğeler, animasyonun cls listesinden bağımsız kabul edilir.
      var btnSlot = (slot === 'hover' || slot === 'basma' || slot === 'secim');
      var clsOk = !!a && (listHas(a.cls, pe.cls) || (pe.isBtn && btnSlot));
      if (slot && !pe.tagged[slot] && clsOk) {
        var slotOk = (slot === 'giris' || slot === 'dongu') || pe.isBtn;
        if (slotOk && !learnedFor(learn, style, pe, slot)) {
          var nl = [id];
          var old = pe.rank[slot] || [];
          for (var k = 0; k < old.length; k++) if (old[k] !== id) nl.push(old[k]);
          pe.rank[slot] = nl;
          pe.tagged[slot] = true;
        }
      }
    }
  }

  // Efekt varsayılan parametreleri (Lua FX_DEFAULTS ile birebir; verify_anim_parity.py denetler).
  var FX_DEFAULTS = {
    fall: { count: 12, seconds: 6, fade: 0.75, smallest: 0.6, largest: 1.0 },
    burst: { count: 10, fade: 0.7, distance: 0.8 },
    orbit: { count: 3, seconds: 4 },
    twinkle: { count: 6, seconds: 0.6, smallest: 0.6, largest: 1.0 },
    orb: { scale: 1.7, pulse: 1.12 },
    smooth: { hover: 1.08, press: 0.9 },
    gleam: { sweep: 3, pause: 1, width: 0.22 }
  };

  // EFEKTLER: ad etiketi → efekt kimliği (Lua TAG_FX ile aynı). Animasyon kütüphanesinde değil, şablonda çalışır.
  var TAG_FX = {
    fall: 'fall', rain: 'fall', coin: 'fall', confetti: 'confetti',
    burst: 'burst', patlama: 'burst', orbit: 'orbit', yorunge: 'orbit',
    twinkle: 'twinkle', sparkle: 'twinkle', parilti: 'twinkle', sweep: 'sweep', orb: 'orb', hale: 'orb',
    smooth: 'smooth', gleam: 'gleam'
  };
  // "fx" etiketi kapsayıcı etiketinden önce gelir (Lua fxTag ile aynı).
  function fxTag(name) {
    var toks = lowerAscii(name).split(/[^a-z0-9]+/);
    var kind = null, tpl = false;
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i];
      if (!t) continue;
      if (!kind && Object.prototype.hasOwnProperty.call(TAG_FX, t)) kind = TAG_FX[t];
      if (t === 'fx') tpl = true;
    }
    if (tpl) return 'tpl'; // "fx" içeren öğe şablondur; kapsayıcı olamaz
    if (kind) return kind;
    return null;
  }

  function isBtnCls(c) { return c === 'TextButton' || c === 'ImageButton'; }

  function selectEligible(el, role) {
    // Seçilebilirlik: rol değil ad belirteci (roleOf buton adlarında "tab"/"slot"u görmez).
    return containsAny(lowerAscii(el.name), ['tab', 'slot', 'select', 'secim', 'option', 'secenek']);
  }

  // elements: [{id, name, cls, depth, parent?}] · Dönüş: [{id, cls, role, parent, sel?, delay?, rank}]
  function decideRanked(elements, style, learn) {
    var per = [];
    for (var i = 0; i < elements.length; i++) {
      var el = elements[i];
      per.push({ id: el.id, cls: el.cls, role: roleOf(el), parent: (el.parent === undefined ? null : el.parent),
                 depth: el.depth, isBtn: isBtnCls(el.cls), rank: {}, tagged: {} });
    }
    var groupCount = {}, cascadeIdx = {}, seen = {};
    for (var a = 0; a < per.length; a++) {
      if (per[a].isBtn && per[a].parent !== null) {
        var k1 = String(per[a].parent);
        groupCount[k1] = (groupCount[k1] || 0) + 1;
      }
    }
    for (var b2 = 0; b2 < per.length; b2++) {
      if (per[b2].isBtn && per[b2].parent !== null && groupCount[String(per[b2].parent)] >= CASCADE_MIN) {
        var k2 = String(per[b2].parent);
        seen[k2] = seen[k2] || 0;
        cascadeIdx[b2] = seen[k2];
        seen[k2] = seen[k2] + 1;
      }
    }
    var loops = 0;
    for (var j = 0; j < per.length; j++) {
      var pe = per[j], cls = pe.cls, role = pe.role;
      if (pe.depth <= 1 || cascadeIdx[j] !== undefined) pe.rank.giris = rankFor('giris', cls, role, style, learn);
      if (cascadeIdx[j] !== undefined) pe.delay = cascadeIdx[j] * CASCADE_STEP;
      if (pe.isBtn) {
        pe.rank.hover = rankFor('hover', cls, role, style, learn);
        if (role !== 'close-button') pe.rank.basma = rankFor('basma', cls, role, style, learn);
        if (selectEligible(elements[j], role)) pe.rank.secim = rankFor('secim', cls, role, style, learn);
      }
      applyTags(pe, elements[j], learn, style);
      pe.fx = fxTag(elements[j].name);
      // Otomatik döngü: yalnız CTA ve ikon; etiketli öğeler sayıma girmez
      if (!pe.tagged.dongu && (role === 'primary-button' || role === 'icon') && loops < LOOP_MAX) {
        var l = rankFor('dongu', cls, role, style, learn);
        if (l.length > 0) { pe.rank.dongu = l; loops += 1; }
      }
    }
    var selCount = {};
    for (var s1 = 0; s1 < per.length; s1++) {
      if (per[s1].rank.secim && per[s1].rank.secim.length > 0) {
        var k3 = String(per[s1].parent === null ? 0 : per[s1].parent);
        selCount[k3] = (selCount[k3] || 0) + 1;
      }
    }
    for (var s2 = 0; s2 < per.length; s2++) {
      if (per[s2].rank.secim) {
        var k4 = String(per[s2].parent === null ? 0 : per[s2].parent);
        if (selCount[k4] < SELECT_MIN) delete per[s2].rank.secim;
        else per[s2].sel = per[s2].parent === null ? 0 : per[s2].parent;
      }
    }
    var cats = ['giris', 'hover', 'basma'];
    for (var c = 0; c < cats.length; c++) applyConsensus(per, cats[c], style, learn);
    return per;
  }

  // Studio'nun ve Figma panelinin kullandığı bağlamalar: seçilen (ilk) öneriler.
  function decideBindings(elements, style, learn) {
    var out = [];
    var per = decideRanked(elements, style, learn);
    for (var i = 0; i < per.length; i++) {
      var pe = per[i];
      var b = { id: pe.id, cls: pe.cls, role: pe.role };
      var any = false;
      if (pe.rank.giris && pe.rank.giris.length) { b.show = pe.rank.giris[0]; any = true; }
      if (pe.rank.hover && pe.rank.hover.length) { b.hover = pe.rank.hover[0]; any = true; }
      if (pe.rank.basma && pe.rank.basma.length) { b.press = pe.rank.basma[0]; any = true; }
      if (pe.rank.dongu && pe.rank.dongu.length) { b.loop = pe.rank.dongu[0]; any = true; }
      if (pe.rank.secim && pe.rank.secim.length) { b.selA = pe.rank.secim[0]; b.sel = pe.sel; any = true; }
      if (pe.delay !== undefined && pe.delay > 0) b.delay = pe.delay;
      if (pe.fx) { b.fx = pe.fx; any = true; }
      if (any) out.push(b);
    }
    return out;
  }

  // Bir animasyon kütüphane kimliğinin tanımı (JSON'a yazılacak tracks dâhil). Yoksa null.
  // Bir kategorideki TÜM kullanılabilir animasyonlar (öğe sınıfına/role bakılmaksızın), güzelliğe göre sıralı.
  function allForCat(cat) {
    return ANIM_IDS.filter(function (id) { return ANIM_LIB[id].cat === cat; })
      .sort(function (a, b) {
        if (ANIM_LIB[a].beauty !== ANIM_LIB[b].beauty) return ANIM_LIB[b].beauty - ANIM_LIB[a].beauty;
        return a < b ? -1 : (a > b ? 1 : 0);
      });
  }
  function getAnim(id) { return Object.prototype.hasOwnProperty.call(ANIM_LIB, id) ? ANIM_LIB[id] : null; }

  return { VERSION: VERSION, roleOf: roleOf, options: options, plan: plan, buildSource: buildSource, lit: lit,
           getAnim: getAnim, decideRanked: decideRanked, decideBindings: decideBindings, FX_DEFAULTS: FX_DEFAULTS, allForCat: allForCat };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = EIAnim;
