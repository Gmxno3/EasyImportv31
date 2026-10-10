# Eksik Raporu (güncel): EasyImport ↔ Framewisp

Kapsam kararları: canlı senkron yok (JSON ile devam). Sunucu/yükleme mimarisi ve iş modeli plugin bitince karar verilecek.

## Yapılanlar
- Etkileşim: `_open`, `_close`, `_toggle`, `_tab`, `_tabgroup`, `_panel`. Paneller başlangıçta kapalı; açılınca giriş animasyonları yeniden oynar.
- `_shadow`: UIShadow artık yalnızca etiketle (otomatik gölge kaldırıldı).
- `_fit` (TextScaled), `_nolist` (otomatik liste kapalı), `_turn` (hover kart dönüşü).
- Doğrulandı: `_ignore` ve `_image` zaten vardı.

## Hâlâ eksik
- Konum/yapı: `_pointer`, `_nopointer`, `_card`, `_lean`, `_color`, `_frame`, `_txt`, `_keep`, `_nodim`.
- Dünya UI'ı: `_3d`, `_tilt`, `_billboard`, `_surface`, `_prompt`, `_hold`.
- Efekt/kamera: `_focus`, `_flow`, `_rays`, `_pixels`, `_drift`, tam `_stroke` (Rotation/Offset modları), `_float` kadranı.
- Araçlar: UI düzenleyici (Studio), Assets/My Images kütüphanesi, tek script'e birleştirme (şu an ayrı betikler).
- Kullanıcı kararıyla kapsam dışı: canlı senkron, Code kodu, Open Cloud/sunucu, iş modeli (plugin bitince).

## Risk
- Gerçek Roblox Studio ve Figma'da hiç çalıştırılmadı; tüm doğrulama sahte ortam ve tarayıcı testleriyle.


Not: Canlı veri (`{Coins}`, `_bind`) kullanıcı isteğiyle kaldırıldı.
