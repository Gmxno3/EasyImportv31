# Efekt Araştırması: Framewisp "Effect Playground" (ekran görüntüleri)

## Gözlemler (Framewisp arayüzü)

- Her efektin ayarları **kaydırıcı + sayı kutusu** ile yapılır ve etiketin yanında yazar, örnek: "How many · _fall".
- Yağmur (`_fall`) ayarları: öğe seçimi ("What falls": kopyalanacak görsel), kaç tane (12), karşıya geçiş süresi (6 sn),
  görünürlük (0,75), en küçük kopya (0,6), en büyük kopya.
- Büyüme (`_smooth`) ayarları: üzerine gelince büyüme (1,08), basınca küçülme (0,9), hover/tık ses kimliği.
- Metin parıltısı (`_gleam`): süpürme süresi (3 sn), süpürmeler arası bekleme (1 sn), dalga genişliği (0,22).
- Değerler katmanda saklanır ve dönüştürmeyle birlikte oyuna gider ("the game uses exactly what you see").
- Bir katman seçilir, etiket eklenir/kaldırılır ("tap to add, tap again to remove"); etiketler "Clear tags" ile temizlenir.

## Bu sürümde karşılığı

| Framewisp | Bizde (etiket) | Ayarlar (JSON `params`) |
|---|---|---|
| `_fall` (görsel düşer) | `_fall` / `_coin` (kapsayıcı) + `_fx` (şablon öğe) | count, seconds, fade, smallest, largest |
| `_smooth` (buton) | `_smooth` (buton) | hover, press |
| `_gleam` (metin) | `_gleam` (metin) | sweep, pause, width |
| `_burst` | `_burst` (buton) | count, fade, distance |
| (ek) `_orbit`, `_twinkle`, `_sweep`, `_orb` | `_orbit`, `_twinkle`, `_sweep`, `_orb` | count/seconds, scale/pulse |

Figma panelinde "Efekt oynatma" bölümü: efekt katmanlarının listesi, seçili efektin kaydırıcıları. Her değişiklik
anında JSON'a (`anim.params`) yazılır; Studio bu değerlerle LocalScript üretir.

## Sınırlar

- Görsel "ses kimliği" (hover/click sesi) yok; ses Roblox'ta ayrı bir Sound nesnesi gerektirir (bu sürümde yok).
- Kopyalar en fazla birkaç düzine olmalı; performans için efekti gerekli öğelere ver.
- `_focus`, `_3d`, `_hold`, `_rays` ve sayı kutusu için "Smooth/ease" seçimi yok (sabit easing).
