# Animasyon Kütüphanesi — `anim-library.json`

**108 animasyon**, 10 kategori, 174 tween track'i. Asistan'ın ikinci (ve son) işi: **animasyon ataması**.

---

## 1. Dağılım

| Kategori | Adet | Tetikleyici | Ne zaman |
|---|---|---|---|
| `giris` | 18 | `show` | Öğe/GUI ekrana girerken |
| `cikis` | 10 | `hide` | Ekrandan çıkarken (girişten **hızlı**) |
| `hover` | 10 | `mouseEnter` / `mouseLeave` | Fare üzerine gelince |
| `basma` | 10 | `click` / `mouseDown` | Tıklama geri bildirimi |
| `dongu` | 13 | `always` | Sürekli çalışan ortam animasyonu |
| `dikkat` | 10 | `event` | Uyarı, ödül, claim, hata |
| `gecis` | 8 | `pageChange` | Ekran/sekme değişimi |
| `durum` | 8 | `stateChange` | Toggle, kilit, ilerleme, başarı |
| `fx` | 15 | `always` / `event` | **Figma'da EFEKT olarak kullanılan ImageLabel'lar** |
| `metin` | 6 | `show` / `event` | Metne özel |

---

## 2. Zaman sistemi (araştırmadan)

Araştırma bulgusu: **4–6 temel süre + 3 easing eğrisi**, sonrası oranlama.

```json
"instant": 0.08, "fast": 0.16, "base": 0.24, "medium": 0.36, "slow": 0.52, "glacial": 0.80
```

| Etkileşim | Süre | Easing |
|---|---|---|
| Hover | 0.08–0.15 | `Quint/Out` (snap) |
| Basma | 0.06–0.12 (in) + 0.20–0.25 (out) | `Quad/Out` → `Back/Out` |
| Buton giriş | 0.30–0.40 | `Back/Out` (spring) |
| Panel / modal giriş | 0.36–0.45 | `Quart/Out` (enter) |
| Çıkış | girişin **~2/3'ü** | `Quad/In` (exit) |
| Sayfa geçişi | 0.36–0.44 | `Quart/Out` |
| Döngü (nefes) | 1.6–2.4 | `Sine/InOut`, `rep:-1, rev:true` |
| Döngü (dönüş) | 4–14 | `Linear`, `rep:-1` |

**Kurallar:**
1. **Çıkış, girişten hızlıdır** (~2:3 oranı). Kullanıcı zaten kararını vermiştir, bekletme.
2. **80 ms altı** algılanmaz, **500 ms üstü** hantal hissettirir (döngüler hariç).
3. Girişlerde `Back/Elastic/Bounce` (overshoot), çıkışlarda asla overshoot yapma.

**Roblox easing karşılıkları:**
`Linear, Sine, Back, Quad, Quart, Quint, Bounce, Elastic, Circular, Cubic, Exponential`
× `In, Out, InOut`

---

## 3. Track şeması

```jsonc
{ "t": "UIScale", "p": "Scale", "from": 1, "to": 0.9,
  "d": 0.08, "dl": 0, "e": "Quad", "ed": "Out", "rep": 0, "rev": false }
```

| Alan | Anlamı |
|---|---|
| `t` | Hedef: `self` \| `UIScale` \| `UIStroke` \| `UIShadow` \| `UIGradient` |
| `p` | Özellik: `Scale, Position, Rotation, Size, ImageTransparency, BackgroundTransparency, TextTransparency, GroupTransparency, ImageColor3, TextColor3, Thickness, BlurRadius, Offset, MaxVisibleGraphemes, Text` |
| `from` / `to` | sayı \| `[x,y]` (Vector2/UDim2) \| `"cur"` (mevcut değer) \| `"textLen"` \| `"textNumber"` |
| `d` | Süre (sn) |
| `dl` | Gecikme — sayı **veya** `"stagger:0.05"` (kardeş sırasına göre) **veya** `"random:0:1.2"` (rastgele) |
| `e` / `ed` | EasingStyle / EasingDirection |
| `rep` | `0` = bir kez, `-1` = sonsuz, `n` = n kez |
| `rev` | Geri dönsün mü |

**Özel `dl` değerleri:**
- `"stagger:0.05"` → aynı kategorideki kardeşler 0.05 sn arayla başlar (liste girişleri)
- `"random:0:1.2"` → her öğeye 0–1.2 sn arası rastgele gecikme (sparkle, toz)

**Özel `from`/`to` değerleri:**
- `"cur"` → çalışma anındaki değer (renk flash'larında geri dönmek için)
- `"textLen"` → metnin karakter sayısı (daktilo)
- `"textNumber"` → metnin sayısal değeri (sayaç)

---

## 4. 🔥 FX tespiti — "Figma'daki şu image'yi efekt olarak kullanır"

Figma'da bazı görseller **içerik değil efekttir**: glow, ışık huzmesi, sparkle, shine, vignette,
noise, toz, halka. Roblox'ta bunlar **ayrı bir `ImageLabel`** olur ve **sürekli animasyon** alır.
Asistan bunu tespit edip `fx` kategorisinden animasyon atar.

### Tespit kuralları (`_fxDetection`)

```
fx = true  EĞER
  (a) katman adında FX token'ı var
      glow, ray, rays, shine, sparkle, star, twinkle, particle, flare, bloom, vignette,
      noise, grain, dust, smoke, fog, ring, pulse, aura, beam, streak, gloss, shimmer,
      glint, halo, neon, energy, magic, fx, effect, efekt, isik, parlama, parlilti, huzme,
      toz, duman, halka, pırıltı ...
  VEYA
  (b) blend mode şunlardan biri:
      SCREEN, LINEAR_DODGE, COLOR_DODGE, LIGHTEN, ADD, PLUS_LIGHTER
  VEYA
  (c) görsel ebeveyninden BÜYÜK (spill) VE çok saydam (opacity < 0.35)
      → glow / halo / aura
```

### FX türü → animasyon eşlemesi

| FX türü | Önerilen animasyonlar |
|---|---|
| `glow` / `halo` / `bloom` / `flare` | `fx_glow_pulse`, `press_ripple` |
| `rays` / `beam` / `sunburst` | `fx_rays_rotate`, `fx_rays_rotate_reverse`, `fx_aura_rotate_pulse` |
| `sparkle` / `star` / `twinkle` / `glint` | `fx_sparkle_twinkle`, `fx_star_burst` |
| `shine` / `gloss` / `shimmer` | `fx_shine_sweep`, `fx_gloss_sweep`, `hover_shine_sweep` |
| `ring` / `pulse` / `radar` / `wave` | `fx_ring_ping`, `loop_expand_ring`, `attention_ping` |
| `vignette` / `overlay` | `fx_vignette_breathe` |
| `noise` / `grain` / `texture` | `fx_noise_drift` |
| `dust` / `particle` / `bubble` | `fx_dust_float`, `fx_bubble_rise` |
| `aura` / `energy` / `magic` | `fx_aura_rotate_pulse` |
| `smoke` / `fog` / `cloud` | `fx_smoke_drift` |
| `streak` / `scan` | `fx_beam_sweep` |

---

## 5. Sınıf / rol → animasyon eşlemesi (varsayılan öneri)

| Rol | Giriş | Hover | Basma | Döngü | Dikkat |
|---|---|---|---|---|---|
| `primary-button` | `enter_pop_scale` | `hover_glow` / `hover_scale_up` | `press_shrink_bounce` | `loop_pulse_scale` | `attention_pulse_scale_big` |
| `button` | `enter_pop_scale` | `hover_scale_up` | `press_shrink_bounce` | — | `attention_bounce_big` |
| `icon-button` | `enter_rotate_in` | `hover_rotate_tilt` | `press_rotate_spin` | — | `attention_bell_ring` |
| `close-button` | `enter_pop_scale` | `hover_scale_down` | `press_shake` | — | — |
| `panel` / `modal` | `enter_slide_up` / `enter_zoom_out` | — | — | — | `state_error_shake` |
| `card` / `slot` | `enter_scale_rotate` | `hover_lift` | `press_squash` | — | `state_unlock_pop` |
| `title` | `enter_punch` | — | — | `loop_shimmer` | `attention_zoom_punch` |
| `value` / `currency` | `text_pop_in` | — | — | — | `attention_zoom_punch` |
| `bar` / `progress` | `enter_mask_reveal` | — | — | — | `attention_flash_red` |
| `badge` / `notification` | `enter_rotate_in` | — | — | `loop_pulse_glow` | `attention_ping` |
| `reward` | `enter_zoom_out` | `hover_bounce_small` | `press_pop_scale` | `loop_pulse_glow` | `attention_glow_burst` |
| `icon` | `enter_pop_scale` | `hover_glow` | — | `loop_float` | `attention_wiggle` |
| `toggle` / `tab` | `enter_fade` | `hover_brighten` | `state_toggle_on` | — | — |
| `background` | `enter_fade` | — | — | — | — |
| `list` (≥3 kardeş) | `enter_stagger_list` | `hover_shift_right` | — | — | — |

---

## 6. "Beğenmedim" → 5 alternatif (MMR)

Kullanıcı öneriyi beğenmezse asistan **5 alternatif** verir:
1. **Zorunlu çeşitlilik:** en az **3 farklı kategori**.
2. **Aynı kategoriden farklı parametre:** süre ×0.6 (hızlı) ve ×1.5 (yavaş), farklı easing
   (`Back` ↔ `Elastic`, `Quart` ↔ `Exponential`).
3. **Benzerlik cezası:** bir önceki öneriye yakın olanların skoru düşürülür.
4. **Stil uyumu:** cartoon ise overshoot'lu (`Back`, `Elastic`), anime ise yumuşak
   (`Quart`, `Exponential`), minimal ise `Sine`.

Her seçim kaydedilir → `usageCount++`, reddedilen önerinin skoru düşer (**negatif sinyal**).

---

## 7. Roblox'a çıktı

Studio tarafı iki dosya üretir:

- **`EI_AnimData` (ModuleScript)** — kütüphaneden seçilen animasyonların Luau table'ı
- **`EI_AnimController` (LocalScript)** — `TweenService` ile çalıştırır

```lua
local A = require(script.Parent:WaitForChild("EI_AnimData"))
A:Play("Play_Button", "giris")     -- tek öğe, tek kategori
A:PlayAll("giris", 0.05)           -- tüm girişleri 0.05 sn stagger ile
A:Stop("Play_Button")
A:SetEnabled(false)                -- StyleQuery.ReduceMotionEnabled için
```

**Kurallar:**
- UIScale yoksa otomatik eklenir, `AnchorPoint = 0.5,0.5` yapılır (merkezden ölçekleme)
- `UIShadow` tween için `BlurRadius` UDim, `Transparency` float
- `GroupTransparency` yalnızca `CanvasGroup` üzerinde (küçük alanlarda!)
- Çakışan tween'ler önce iptal edilir (`tween:Cancel()`)
- Sonsuz döngüler `Visible = false` iken duraklatılır (performans)

---

## 8. Kütüphaneye animasyon eklemek

Yeni kayıt ekle, `_fxDetection.nameTokens`'a gerekirse token ekle, sonra:

```bash
python tools/validate_anim.py     # şema + easing + süre kontrolü
python tools/export_model.py      # Lua/JS çıktısını yenile
```

Zorunlu alanlar: `id, name, cat, trig, cls, roles, fx, fit, q, dur, tracks`
`q` = `{detail, variety, beauty, snap}` (1–5) — çeşitlilik/beğenmeme motoru bunu kullanır.
