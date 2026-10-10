# UI Animasyon Araştırması

Tarih: 9 Ekim 2026 · Kapsam: Figma → Roblox Studio eklentisindeki animasyon paketleri.

## 1. Bu animasyonlar nedir?

Bunlar **UI animasyonudur**, karakter (humanoid) animasyonu değildir. Roblox'ta bir GUI nesnesinin özelliklerini
(`Position`, `Size`, `Rotation`, `ImageTransparency`, `GroupTransparency`, `ImageColor3`, `UIStroke` renk/kalınlık)
`TweenService` ile zaman içinde değiştiren **LocalScript** kodudur. `Animator` ya da `AnimationTrack` kullanılmaz.
Geçiş eğrisi `TweenInfo` ile seçilir; varsayılan easing `Quad`'dır.
Kaynak: Roblox Creator Docs, *UI animation / tweens* (create.roblox.com/docs/ui/animation).

Asistanın yaptığı iş: her öğeye (buton, panel, ikon) bir **giriş**, **hover** ve **basma** animasyonu bağlamak.
Kullanıcı bunu Figma panelinde seçer; seçim JSON'a `_Animasyon N` adıyla yazılır; Studio bu JSON'dan LocalScript üretir.

## 2. Referans katalog: Framewisp 4.4 (27 Eylül 2026)

Framewisp, aynı işi yapan bir Figma → Roblox eklentisidir. Belgesi (framewisp.com/docs) efektleri dört gruba ayırır:

| Grup | Efekt (etiket) | Ne yapar |
|---|---|---|
| Hover / basma | `_button` | Hover ve basma geri bildirimi |
| | `_smooth` | Hover'da büyür, basmada ezilir |
| | `_up` | Hover'da birkaç piksel yukarı kalkar |
| | `_turn` | Hover'da kart döner, çıkınca geri döner |
| | `_lean` | Kart üzerine gelince ikon eğilir (kartı değil, dış kartı izler) |
| | `_squish` | Basmada yassılır, bırakınca yaylanır |
| | `_ripple` | Tıklama noktasından dalga yayılır |
| | `_burst` | Basmada parçacık patlaması (kendi resmini de kullanabilir) |
| | `_color` | Hover'da renk değişimi (ikon yanar) |
| | `_select` | Seçilen kartın etrafında kalıcı çerçeve; diğer seçim kalkar |
| | `_pointer` | Menü içinde kursorun üstündeki butona işaret eden ok |
| Giriş | `_pop` | Pürüzlü yaylanarak girer |
| | `_fadein` | Görünürlük değişince şeffaftan belirir |
| | `_reveal` | Yarım boyuttan, sallanarak açılır (vitrin) |
| | `_swing` | Hızlı girer, 3D'de kapı gibi sallanır (ödül kapısı) |
| | `_drop` | Yerine düşer, ezilip bir kez zıplar; çocuklar sırayla düşebilir |
| | `_cascade` | Çocuklar yukarıdan aşağı sırayla yaylanarak girer |
| Boşta hareket | `_pulse` | Kalp atışı gibi büyüyüp küçülür |
| | `_jelly` | Hafif dönme + nefes gibi ölçek |
| | `_wiggle` | Çan gibi: kısa sallanma, aralıklı tekrar |
| | `_shake` | Aralıklı titreme (ödül alınmadı hatırlatması) |
| | `_glow` | Yanıp sönmeyen, nefes alan parıltı halkası |
| | `_blink` | Görünür/görünmez döngüsü (yanıp sönen lamba) |
| | `_float` | Bir yönde yavaşça gidip gelir |
| | `_drift` | Doku kayar (sonsuz desen) |
| | `_rays` / `_pixels` / `_gleam` | Güneş ışınları, piksel parıltısı, metin üstünden ışık geçişi |
| Dolgu / çizgi | `_stroke` | Mevcut çizginin gradyanı kayar |
| | `_flow` | Başlık veya bar gradyanı kayar |
| | `_shadow` | Gerçek UIShadow (iç gölge dâhil), iki tonlu gölge |
| Sahne | `_focus` | Panel açılınca kamera yaklaşır, dünya bulanıklaşır |
| | `_fall` | Nesnenin içinde resimler yağmur gibi düşer |
| | `_hold` | Prompt tutulurken kenarlık dolar |
| 3D | `_3d` / `_tilt` | Kart imlece göre 3D eğilir / sabit 3D duruş |

Belgenin temel ilkeleri: efektler birbirine eklenebilir (`_magnet + _smooth` gibi); her efektin parametreleri
(süre, gecikme, şiddet, yön) Figma'da kaydedilir ve JSON ile birlikte gider; önizleme Figma'da oynar.

## 3. Bizim kütüphane ile eşleme

Kütüphane: `assistant/anim/anim-library.json` — 108 animasyon (giris 18, hover 10, basma 10, dongu 13, fx 15, cikis 10, dikkat 10, gecis 8, durum 8, metin 6).

| Framewisp | Bizde | Durum |
|---|---|---|
| `_smooth`, `_squish` | `hover_scale_up`, `press_squash` | ✓ |
| `_up` | `hover_lift` | ✓ |
| `_turn`, `_lean`(kısmen) | `hover_rotate_tilt` | ~ (kart değil, öğenin kendisi) |
| `_color` | `hover_brighten` | ~ (renk değil, parlaklık) |
| `_ripple` | `press_ripple` | ✓ |
| `_shake` (basma) | `press_shake` | ✓ (boşta titreme yok) |
| `_pop` | `enter_pop_scale`, `enter_elastic_pop` | ✓ |
| `_fadein` | `enter_fade` | ✓ |
| `_drop` | `enter_bounce_drop` | ✓ |
| `_cascade` | `enter_stagger_list` | ~ (listede sıra var; çocuk bazlı değil) |
| `_pulse` | `loop_pulse_scale` | ✓ |
| `_glow` | `loop_pulse_glow` | ✓ |
| `_float` | `loop_float` | ✓ |
| `_rays` | `fx_rays_rotate` | ✓ |
| `_gleam` | `fx_shine_sweep`, `hover_shine_sweep` | ~ |
| `_drift` | `loop_gradient_sweep` | ~ |
| `_jelly` | `loop_bobble` | ~ |
| `_reveal`, `_swing` | — | ✗ |
| `_wiggle`, `_blink` | — | ✗ |
| `_select` | — | ✗ (önemli: seçim durumu yok) |
| `_burst` | — | ✗ (parçacık gerekir) |
| `_stroke`, `_flow` | — | ✗ (UIGradient + UIStroke tween'i gerekir) |
| `_shadow` | — | ✗ (UIShadow kararımızda yasak: L10) |
| `_3d`, `_tilt` | — | ✗ (kalıcı 3D poz için perspektif yüzeyi gerekir) |
| `_focus`, `_fall`, `_hold` | — | ✗ (Lighting/kamera/parçacık: UI tween'in dışı) |

## 4. Öncelik

- **P1 (UI tween ile yapılabilir, katalogda eksik):** `_select` (seçim çerçevesi), `_wiggle`, `_blink`,
  `_reveal`, `_swing`, `_cascade` (çocuk bazlı sıralı giriş).
- **P2 (UI tween + gradyan/çizgi özellikleri):** `_stroke` ve `_flow` (UIGradient `Offset` ve `Rotation` tween'i),
  `_shake` (boşta), `_jelly` (kendi eğrisi).
- **P3 (UI dışı veya parçacık):** `_burst`, `_fall`, `_focus`, `_hold`, `_3d`. Bunlar Lighting, kamera ya da
  parçacık gerektirir; ayrı bir sistem olarak tasarlanmalı.

## 5. Süreler ve easing

Kütüphane zamanlaması (`_timing`): `instant 0.08 · fast 0.16 · base 0.24 · medium 0.36 · slow 0.52 · glacial 0.80` saniye.
Giriş animasyonları hover'dan yavaştır; basma en hızlısıdır. Yaylanma için `Back` ya da `Elastic`, sürekli
hareketler için `Sine` kullanılır. Bu değerler kütüphanenin `README`'sinde araştırmadan türetilmiştir.

## 6. Asistanın karar kuralları (UYGULANDI — madde 3)

Asistan animasyonu öğe-öğe değil, tasarım bütünü için seçer. Dört kural, sırayla:

1. **Stil:** Stile uygun anahtar sözcük içeren animasyonlara bonus (×1.5). `stud`: fade, scale_up, shrink_only, glow,
   lift, brighten, soft · `anime`: elastic, flip, rotate, bounce, pop, spring, grow · `cartoon`: punch, squash, shake,
   bounce, pop, wiggle, shrink. Skor = güzellik × stil öncülü × stil bonusu.
2. **Konum:** Giriş yalnızca ScreenGui'nin doğrudan çocuklarına (derinlik ≤ 1). Kapat/ikincil butonda (`close-button`)
   basma yok, yalnızca hover.
3. **Tutarlılık:** Aynı sınıftaki (ör. tüm TextButton) öğelerin en az %50'si aynı animasyonu öncelikliyorsa, bu
   animasyon öğrenmesi olmayan diğer öğelere de verilir. Eşitlikte küçük kimlik kazanır.
4. **Öğrenme:** Bağlamda kullanıcı gözlemi varsa her zaman öncelikli; tutarlılık kuralını geçersiz kılar.

Uygulama: `EIAnim.decideRanked` (Lua `runtime/lua/EIAnim.lua`, JS `runtime/js/ei-anim.js`) — iki dilde birebir.
Figma panelinde seçici varsayılanları bu kurallardan gelir; Studio'da LocalScript bu kararlardan üretilir.

Doğrulama: `verify_anim_parity.py` bölüm 6–7. Kapat butonunda basma yok; TextButton'lar tutarlı hover alır;
anime'de ana panel yaylı/dönen, stud'da sade giriş alır; öğrenilmiş seçim önceliklidir.

**Sınır:** Tutarlılık kuralı, sınıfın tüm öğeleri aynı animasyonu seçmiş olsa da görünmez; kuralın ayırt
edici etkisi için farklı önceliklere sahip öğeler gerekir. Bu tasarım için ayrı bir test fixture'ı önerilir.

## 7. Kaynaklar

- Framewisp belgesi, sürüm 4.4 (27 Eylül 2026): https://framewisp.com/docs
- Roblox Creator Docs, UI animasyonu: https://create.roblox.com/docs/ui/animation
- Kütüphane zamanlaması: `assistant/anim/README.md`
