# EasyImport — Eksik Raporu (v25)

Durum etiketleri: ✅ var · 🟡 kısmen · ❌ yok · ⚠️ doğrulanmadı.

## Kararlar (kesinleşen)
- **Görsel yükleme: manuel.** ZIP'i indirirsin, görselleri Asset Manager'a elle yüklersin, Studio'da "İsimden eşleştir" çalışır.
  Otomatik yükleme, sunucu ve Open Cloud kapsam dışı. Canlı senkron da kapsam dışı.
- **UIShadow:** yalnızca `_shadow` etiketiyle uygulanır (otomatik gölge yok). ✅
- **Reference (UI-Plus):** iç referans; paketlenmez, dağıtılmaz. ✅

## Açık karar
- **İş modeli:** plugin bittiğinde karar verilecek (aşağıda ne olduğu açıklandı).

## 1. Çekirdek (Figma → Studio)
- JSON, Luau, RBXMX üretimi ✅ (parite ve sözleşme testleri var)
- JSON kopyala/yapıştır ✅
- Görsel yükleme (manuel ZIP + Asset Manager + İsimden eşleştir) 🟡 ⚠️ — Bulk Import'un dosya adını Decal adı yapması gerçek ortamda doğrulanmadı.
- Tek script'te birleştirme 🟡 — animasyon, etkileşim, efekt tek betikte; ses ve duyarlı betik ayrı.

## 2. Etiketler (katman adı etiketleri)
Etiket = Figma katman adına yazılan kısa ek (ör. `_button`, `_pop`, `_fall`). İkonlar bunun dışında, ayrı bir kütüphanedir.
- Var ✅: `_button`, `_textbox`, `_canvas`, `_aspect`, `_hover`, `_clicked`, `_ignore`, `_image`, `_scroll`, `_grid`/`_list`, `_nolist`, `_fit`, `_shadow`, `_select`, `_open`, `_close`, `_toggle`, `_tab`, `_tabgroup`, `_panel`.
- Animasyon etiketleri (38) ✅: pop, fade, reveal, swing, drop, lift, turn, glow, squish, ripple, pulse, float, blink, wiggle, border, spin, breathe, shimmer, bobble, ring, shake, ping, bell, select, …
- Efekt etiketleri (16) ✅: fall/rain/coin, confetti, burst, orbit, twinkle/sparkle, sweep, orb/hale, smooth, gleam, fx (şablon).
- Eksik ❌: `_pointer`, `_nopointer`, `_card`, `_lean`, `_color`, `_frame`, `_txt`, `_keep`, `_nodim`, `_3d`, `_tilt`, `_billboard`, `_surface`, `_prompt`, `_hold`, `_focus`, `_flow`, `_rays`, `_pixels`, `_drift`, tam `_stroke`, `_float` kadranı.

## 3. Animasyonlar
- Kütüphane 117 giriş; Studio'da bağlanabilen 66.
- Kullanılmayan kategoriler: `cikis` (10), `gecis` (8), `durum` (8), `metin` (6).
- Döngüler: en fazla 3 otomatik öğe; etiketle eklenenler sınırsız.

## 4. Efektler
- Çalışıyor ✅ (sahte ortamda test edildi): yağmur, konfeti, patlama, yörünge, parıltı, süpürme, dev hale, büyüme, metin parıltısı.
- Kendi resmi: şablon öğe (`fx`) ve panelden 4'e kadar resim (2 MB); 1022 simgelik Ekstra Kütüphane (ızgara, öğrenen sıralama).
- Eksik ❌: dönmeden düşürme, ayrılık mesafesi, şablona renk verme, patlamada renk/resim ayarı, dışarıdan tetikleme, `_focus`, `_flow`, `_rays`, `_pixels`, `_drift`, `_hold`.
- Performans: kopya havuzu yok; çok efekt yavaşlatabilir.

## 5. Asistan (eğitim ve öğrenme)
- **Öğrenme** ✅: EILearn; efekt simgeleri ve animasyon seçimleri kabul/red ile öğrenilir. Figma tarafı tarayıcıda doğrulandı; Studio tarafı ⚠️.
- **Efekt simge modeli** 🟡:
  - Etiketler: 1022 simge, görsel (AI) yargısıyla etiketlendi. İnsan etiketi değil.
  - Model: ad + etiket tokenları, Naive Bayes, 6 sınıf (orb dışarıda).
  - Çapraz geçerlilik %90,8 (çoğunluk %66). Sınıf bazında: fall 0,91 · none 0,99 · burst 0,80 · twinkle 0,61 · confetti 0,25 · orbit 0,00.
  - **Yeni kategorilerde zayıf:** kategori dışarıda bırakma %33, çoğunluğun (%66) altında. Model yalnızca küçük bir öncül (puanın %12,5'i).
- **Katman sınıfı modeli** 🟡: 14 sınıf, destek kapısı (az örnekli sınıflar seçilmez). Yeniden eğitilmedi; eğitim verisi kural motorunun çıktısı. ScrollingFrame, ImageButton, TextBox, CanvasGroup, ViewportFrame, VideoFrame kapalı.

## 6. UI Tools (Studio ikinci eklenti)
- Var ✅: hizalama (6 mod, üst öğe/seçim hedefi), taşıma (adım, ızgara 1/4/8, ok tuşları — yalnız pencere odaktayken), dağıtma (yatay/dikey), konum ve boyut alanları, sınıf değiştirme (çocuk ve öznitelik korunur), Offset ↔ Scale, öznitelik/etiket temizleme, geri alma.
- Güncellendi (v28): UILayout kartı ✅; renkler ve metin okunur ✅; kütüphane 256 px ✅; Figma'da kütüphane ve önizleme ✅ (CSS önizleme, Roblox birebir değil).
- Eksik ❌: **kopyala/yapıştır** (seçili öğeyi kopyalayıp başka yere yapıştırma; çocuklar ve özellikler dâhil), zoom, kısayol özelleştirme.
- Test: çekirdek 135, plugin 137, mutasyon 20/20. Gerçek Studio'da ⚠️ çalıştırılmadı.

## 7. Risk
- Gerçek Roblox Studio ve Figma'da hiçbir özellik uçtan uca test edilmedi ⚠️. Doğrulama birim testleri, sahte ortam ve tarayıcıyla yapıldı.

---

### İş modeli nedir? (kısa)
Ürünün nasıl para kazanacağını belirler:
- **Tek seferlik satın alma:** bir kez öde, sonsuza kadar kullan.
- **Abonelik:** her ay/yıl ücret.
- **Ücretsiz + ücretli paket:** temel özellikler bedava, gelişmiş özellikler (ör. efekt kütüphanesi, UI Tools) ücretli.
- **Deneme süresi:** belli gün ücretsiz dene, sonra satın al.
Bunu plugin bittiğinde seçeceğiz.
