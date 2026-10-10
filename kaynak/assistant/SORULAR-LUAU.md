# Roblox Luau UI Animasyon — Sorular

Araştırma yaptım, kütüphane hazır (108 animasyon). Şimdi **plugine nasıl gireceğini** netleştirelim.
Format yine: `L3-a`, `L5-D`, … Boş bırakırsan iddiamı doğru kabul ederim.

---

## Araştırmada bulduklarım (kısa)

- **`TweenService`** yerleşik ve standart. UI için doğru seçim. ⚠️ **Server'da değil,
  LocalScript'te** çalıştırılmalı (server'da daha az akıcı). [1](https://devforum.roblox.com/t/how-do-i-decide-between-loops-runservice-tweenservice-and-animations-for-movingrotating-objects/1638186)
- **Spring alternatifi var:** `SpringService` (SmoothDamp tabanlı, TweenService'in yerine geçen
  drop-in) ve topluluk standardı **`spr`** modülü. `UDim2`, `ColorSequence`, `NumberSequence`
  (yani `UIGradient`), `number`, `Vector2`, `Rect` destekliyor. [2](https://devforum.roblox.com/t/springservice-drop-in-replacement-for-tweenservice-using-smoothdamp/3621210)
  → **Artısı:** hover/press daha "canlı", fiziğe yakın. **Eksisi:** fazladan dosya gerekir.
- **ModuleScript tuzağı:** tween'i ModuleScript içinde tanımlayıp nesneyi orada sabitleme;
  nesneyi **LocalScript'ten parametre olarak geç**. [3](https://devforum.roblox.com/t/tweenservice-animation-not-playing-from-modulescript/3050781)
- **Performans:** aşırı `WaitForChild` kullanımı yavaşlatır; `while wait()` döngülerinden kaçın.
- ⚠️ TweenService, karakter animasyonlarına göre daha az performanslı — ama **UI için standart bu**.

---

## Sorular

**L1.** ⭐ Animasyon motoru hangisi?
- **(a) TweenService** — yerleşik, ek dosya yok, 108 animasyonun hepsi çalışır
- (b) **Spring (`spr` benzeri)** — daha doğal/canlı, ama plugin'e fazladan modül gömmek gerekir
- (c) **İkisi:** TweenService varsayılan + ayarda "Spring modu" açılınca spring
→ a / b / c

**L2.** Spring kullanırsak: hazır topluluk modülünü (`spr`) mü gömelim, yoksa **kendimiz
yazalım** mı? (Kendi yazarsak ~120 satır SmoothDamp; lisans/versiyon derdi olmaz.)
→ hazır modül / kendimiz yazalım

**L3.** ⭐ Animasyon dosyaları nasıl dursun?
- **(a)** 2 dosya: `EI_AnimData` (ModuleScript, veri) + `EI_AnimController` (LocalScript, motor)
- (b) Her öğeye kendi LocalScript'i (çok dosya, yavaş açılır)
- (c) Tek ModuleScript + hangi öğenin hangi animasyonu alacağı **Attribute** olarak
→ a / b / c

**Karar (KARARLAR.md madde 5): tek üretilmiş LocalScript** — `EI_AnimData`/`EI_AnimController`
modül çifti yapılmayacak; düz Luau tween kodu, hover/basma bağlamaları da aynı scriptte.

**L4.** Giriş animasyonları **otomatik çalışsın** mı (ScreenGui görünür olunca tüm "giriş"
animasyonları sırayla çalsın), yoksa **sen kodla çağır** mısın (`A:PlayAll("giris")`)?
→ otomatik / kodla çağrılsın / ikisi (ayar ile)

**L5.** ⭐ Hover ve basma animasyonları **otomatik bağlansın** mı? Yani tüm
`ImageButton`/`TextButton`'lara otomatik `MouseEnter`/`MouseLeave`/`MouseButton1Down` bağlanıp
atanan hover/basma animasyonu çalışsın mı?
→ Evet otomatik bağla / Hayır, sadece ben seçersem / Ayar ile aç-kapa

**L6.** Sonsuz döngü animasyonları (`dongu`, `fx`) performans için ne zaman dursun?
→ GUI kapalıyken duraklat / ekran dışındayken de dur / hiç durmasın

**L7.** ⭐ Animasyon **şiddeti** sabit mi, stil göre mi ayarlansın?
Önerim: **stil göre** — cartoon ×1.3 (daha abartılı, overshoot büyük), anime ×0.85 (daha zarif),
stud ×1.0. Süreler de buna göre ölçeklenir.
→ D / Y? Değerler: ………

**L8.** Ses efekti de ekleyelim mi? (hover/click sesi, `SoundService`)
→ Evet, ses ID'si ayarlanabilir olsun / Hayır, sadece görsel

**L9.** ⭐ Plugin'de **hazır paketler** olsun mu? Yani kullanıcı tek tek animasyon seçmeden
tek tıkla uygulasın:
- "🎮 Oyun Paketi" (pop + shrink-bounce + pulse)
- "✨ Premium Paket" (shine + glow + shimmer)
- "🧱 Klasik Paket" (stud: sade shrink-bounce + shine frame)
- "🎌 Anime Paketi" (glow + rays + sparkle)
→ Evet, 4 paket / farklı paketler öner / gerek yok

**L10.** ⭐ `UIShadow` glow animasyonlarını kullanalım mı? (2026'da tam sürüme çıktı, çok güzel
glow veriyor ama **eski Studio sürümlerinde yok** — yoksa Roblox onu görmezden gelir, hata vermez.)
→ Evet kullan / Hayır, uyumluluk için kullanma / Ayar ile

**L11.** Animasyon verisi nerede dursun?
- (a) `EI_AnimData` ModuleScript (saf Lua table — en hızlı, okunabilir)
- (b) Instance **Attribute**'ları (Studio'da elle düzenlenebilir)
- (c) JSON string + çalışma anında parse
→ a / b / c

**L12.** Erişilebilirlik: `StyleQuery.ReduceMotionEnabled` desteği ekleyelim mi?
(Hareket azaltma açıksa animasyonları kapat/hafiflet)
→ Evet / Hayır

**L13.** Bir öğeye **birden fazla** animasyon atanabilsin mi? (Örn. hem `giris` hem `dongu`
hem `basma` — zaten kategoriler ayrı, hepsi birlikte çalışır mı?)
→ Evet, kategori başına bir tane / tek animasyon yeter

**L14.** ⭐ Üretilen Luau kodu **ne kadar sade** olsun?
- (a) **Okunabilir + yorumlu** (kullanıcı düzenleyebilsin)
- (b) **Kompakt** (küçük dosya)
- (c) İkisi: `EI_AnimData` okunabilir, `EI_AnimController` kompakt
→ a / b / c

**L15.** Animasyonlar **Studio'da önizlenebilsin** mi? (Plugin panelinde "Önizle" butonu →
Studio içinde gerçekten oynat)
→ Evet, çok iyi olur / Gerek yok

---

### ⭐ En kritik 5
**L1** (motor: Tween mi spring mi) · **L3** (dosya yapısı) · **L5** (hover/basma otomatik mi)
· **L9** (hazır paketler) · **L10** (UIShadow kullanılsın mı)

---

## ⚠️ Bir not: Figma efektleri bu işe yaramaz

Senin söylediğin gibi: **Figma'nın `effects[]` dizisinde texture/efekt bulamayız**, çünkü
bunlar **image katmanı** veya **frame** olarak yapılıyor.

`anim-library.json` içindeki `_fxDetection` zaten buna göre kurulu — Figma `effects[]`'e
**bakmıyor**, şunlara bakıyor:
1. **Katman adı** token'ları (`glow`, `ray`, `sparkle`, `shine`, `vignette`, `noise`, `dust`, `ring`…)
2. **Blend mode** (`SCREEN`, `ADD`, `LINEAR_DODGE`, `COLOR_DODGE`, `LIGHTEN`)
3. **Geometri** (ebeveyninden büyük + çok saydam → glow spill)
4. **Frame tabanlı shine** (yarı saydam/gradyanlı, üstte binen ince Frame)
5. **Doku tekrarı** (aynı image birden fazla yerde → `reuseRate`)

Bu listede **eksik veya fazla** var mı? → ………
