# Asistan Modeli — Doğru / Yanlış Soruları

**Nasıl cevaplayacaksın:** Her soruda benim iddiam var. Sadece `12-D`, `13-Y: doğrusu şu...` yazman yeterli.
Cevap vermezsen **iddiamı doğru kabul edip** öyle kodlayacağım.
⭐ = en kritik 10 soru (bunlar mimariyi değiştirir).

---

## A. Sınıflandırma mantığı — senin tecrüben

**A1.** ⭐ Kapama / Close (X) butonu profili: **kareye yakın (aspect 0.8–1.25), küçük (32–96 px),
sağ üst köşede, genelde ImageButton, içinde metin yok veya tek "X" karakteri.**
→ D / Y?

**A2.** ⭐ Uzun + alçak (aspect ≥ 2.5) + **içinde metin var** + kalın kontur → bu bir **butondur**
(ImageButton veya TextButton), TextLabel değil. → D / Y?

**A3.** İçinde metin olan ve hiç görsel öğesi / dolgusu olmayan öğe → **TextLabel** (buton değil).
→ D / Y?

**A4.** Görsel dolgusu (`IMAGE` paint) olan her öğe `ImageLabel`/`ImageButton` olmalı;
Roblox'ta `Frame`'e görsel doğrudan verilemez. → D / Y?

**A5.** ⭐ Buton mu değil mi kararını **isimden** (`_button`, `btn`) çok **konum + boyut + kontur +
çevresindeki öğeler** belirler. Yani isimsiz bir katmanda bile "sağ üstte, 64×64, kalın konturlu"
→ buton diyebilmeliyiz. → D / Y?

**A6.** Bir öğenin **ebeveyni** ScrollingFrame ise çocukları büyük olasılıkla **buton / slot /
kart** olur (liste elemanı). Bu hiyerarşi sinyalini kullanalım mı? → D / Y?

**A7.** Tam ekranı kaplayan (canvas'ın %90'ından fazlası) ve altında başka her şey bulunan öğe
→ **`Frame` (arka plan)**, asla buton değil. → D / Y?

**A8.** İnce uzun (aspect ≥ 10, kalınlık 1–3 px) öğe → **ayırıcı (divider) Frame**, başka bir şey değil.
→ D / Y?

**A9.** Bir öğenin içinde **hem metin hem görsel** varsa ve tıklanabilir görünüyorsa →
`ImageButton` (arka plan görseli) + üstünde `TextLabel`, ikisi ayrı katman. → D / Y?

**A10.** Çok sayıda (≥4) **aynı boyutta** yan yana duran öğe → bunlar bir **liste/ızgara elemanı**
(slot, kart, envanter gözü) ve hepsi **aynı sınıf** olmalı. → D / Y?

---

## B. Roblox teknik kısıtları — araştırma bulgularım (senin deneyiminle çelişebilir)

**B1.** ⭐ Roblox'ta **öğe bazlı blur YOK**. `BlurEffect` tüm ekranı etkiler ve UI'yı etkilemez.
Figma'daki **Background Blur**'u şöyle çevirelim: **yarı saydam koyu renk** (blur taklidi)
+ isteğe bağlı uyarı. → D / Y? (Y ise: blur'lu PNG export mu istersin?)

**B2.** ⭐ Figma'daki **Layer Blur** (katmanın kendisi bulanık) → Roblox'ta tek çözüm **bulanık PNG
export**. Bunu otomatik yapalım mı? → D / Y?

**B3.** ⭐ **Inner Shadow**'nun Roblox'ta karşılığı yok (yeni `UIShadow` inset desteklemiyor).
Seçeneklerim: **(a)** yok say, **(b)** içe yakın koyu `UIStroke` ile taklit et, **(c)** PNG.
Hangisi? → a / b / c

**B4.** ⭐ **Metin gölgesi** Roblox'ta yok (UIShadow metne eklersen **dikdörtgen kutunun** gölgesini
verir). Figma text-shadow → **(a)** `TextStrokeColor3` konturuna çevir, **(b)** metni PNG'ye çiz,
**(c)** yok say. Hangisi? → a / b / c

**B5.** `UIGradient` **`ScrollingFrame` ve `TextBox`'ta çalışmıyor** ve **6'dan fazla renk durağı**
önerilmiyor. Bu durumda gradient'i **ilk ve son durağın ortalamasına (düz renge)** düşürelim.
→ D / Y?

**B6.** ⭐ `CanvasGroup`'u **yalnızca** grup şeffaflığı (`GroupTransparency`) gerektiğinde kullanalım;
tam ekran `CanvasGroup` **bulanık görünüyor** ve bellek baskısında çözünürlüğü düşüyor. → D / Y?

**B7.** Artık `UICorner`'da **her köşe ayrı** ayarlanabiliyor (`TopLeft/TopRight/BottomLeft/
BottomRight`). Figma'nın farklı köşe yarıçaplarını **birebir** aktaralım. → D / Y?

**B8.** `UIShadow` ile **glow/parlama** yapılabilir: yüksek `BlurRadius` + düşük `Transparency` +
negatif `Spread`. Figma'da "drop shadow ama blur çok yüksek, ofset 0" görürsek bunu **glow** sayalım.
→ D / Y?

**B9.** Birden fazla `DROP_SHADOW` varsa hepsini ayrı ayrı `UIShadow` olarak üretelim
(Roblox birden fazla UIShadow'u destekliyor). → D / Y?

**B10.** Figma **blend mode**'ları (Multiply, Screen, Overlay…) Roblox'ta yok → **en yakın düz renge
indirgeme** yapalım (Figma'daki katman sırasına göre basit lerp). → D / Y?

**B11.** Kesikli çizgi (`dashPattern`) Roblox'ta yok → **düz çizgiye** düşür. → D / Y?

**B12.** Roblox fontları sınırlı (BuilderSans, GothamSSm, SourceSansPro, Roboto, Montserrat…).
Figma'da Roblox'ta olmayan bir font varsa → **BuilderSans'e düşür + ağırlığı koru**. → D / Y?
(Yoksa varsayılan fontun ne olsun?)

---

## C. Stil — ✅ TANIMLARIN ALINDI, şimdi ölçülebilir karşılıkları

Tarifin `ARASTIRMA.md` §C1 ve `spec/style-rules.json` içine işlendi. İlk hipotezimin **yanlış
olduğu** yerleri de not ettim. Şimdi **ölçülebilir sinyalleri** doğrula:

**C1.** ⭐ **Stud tespiti** nasıl yapılsın? (Birden fazla seç işaretle)
- (a) katman adında `stud / studs / çivi / brick / tugla` token'ı
- (b) `scaleMode = TILE` (döşeme) image fill + küçük döşeme hücresi (<128 px)
- (c) PNG **piksel analizi** (düzenli dairesel nokta ızgarası) — dosya boyutu ve işlem maliyeti artar
- (d) **sen elle** işaretle (Figma panelinde "Bu GUI Stud" kutusu)
- (e) başka: ………
→ ……

**C2.** ⭐ Stud **nerede** aranmalı? Sadece **arka plan / panel** katmanlarında mı, yoksa **herhangi
bir katmanda** (buton, ikon dâhil) stud dokusu bulunsa tüm GUI "Stud" sayılır mı?
→ sadece arka plan-panal / herhangi bir katman yeterli

**C3.** ⭐ **Anime'nin "ışıklandırma"sını** şunlarla ölçüyorum — doğru mu, eksiği var mı?
`gradyan oranı` + `radyal gradyan sayısı` + **glow sayısı** (offset≈0, blur yüksek) +
`3+ duraklı gradyan` + `SCREEN/ADD/LINEAR_DODGE blend modlu katman sayısı`
→ D / Y? Eksik: ………

**C4.** ⭐ **Anime'nin "detay"ını** şunlarla ölçüyorum — doğru mu?
`katman sayısı` + `ağaç derinliği` + `düğüm başına efekt sayısı`
→ D / Y? Eksik: ………

**C5.** ⭐ **Cartoon'un "texture"sini** şunlarla ölçüyorum — doğru mu?
`IMAGE fill oranı` + `TILE (döşeme) kullanımı` + `TEXTURE/NOISE efektli katman` + `vektör/süs katmanı`
→ D / Y? Eksik: ………

**C6.** Cartoon'da ilk tahminim **"kalın kontur (3–8 px)"** demişti ama sen dokudan bahsettin.
Cartoon'da **kontur kalınlığı** ayırt edici mi? → Evet kalın kontur da var / Hayır, alakasız

**C7.** ⭐ Sırayı böyle kurdum — doğru mu?
`1) hasStud → STUD (kesin, override yok)` → `2) ışık+detay yüksek → ANIME` →
`3) doku yüksek + efekt az → CARTOON` → `4) ikisi de zayıfsa → BELİRSİZ (stil önceliği uygulanmaz)`
→ D / Y?

**C8.** Stil **birbirine karışabilir mi**? (Örn. stud arka plan + anime tarzı butonlar?)
→ Hayır, GUI tek etiket / Evet karışabilir (öğe bazında da tahmin et)

**C9.** Üçü dışında **"hiçbiri" (nötr)** seçeneği olsun mu? Yoksa her GUI illa birine mi girsin?
→ "hiçbiri" olsun / illa birine girsin

**C10.** ⭐ Bu eşikler sence makul mü? (sentetik veriyle kalibre edip sonra senin etiketlerinle
doğrulayacağım)
`ışıklandırma ≥ 0.55 ve detay ≥ 0.50 → ANIME` · `doku ≥ 0.45 ve efekt yoğunluğu ≤ 0.40 → CARTOON`
→ D / Y? Önerin: ………

**C11.** ⭐ Stil **animasyon seçimini** etkilesin mi? Önerdiğim öncelikler:
- **Anime** → ağırlıkla **fx + döngü**: glow nefesi, huzme dönüşü, sparkle, shimmer, aura
- **Cartoon** → ağırlıkla **basma + giriş**: pop, elastic, küçül-zıpla, squash, zıplama
- **Stud** → sade, efektsiz: shrink-bounce, pop, kontur kalınlaşması
→ D / Y? Değiştir: ………

**C12.** Stil **sınıf tahminini** de etkilesin mi? (Örn. anime'de glow'lu katman → efekt
`ImageLabel`; cartoon'da dokulu panel → `ImageLabel`) → D / Y?

---

## D. Özellikler — "sadece size değil" isteğin

**D1.** ⭐ İstediğin özellikleri doğru mu çevirdim: **kalın–ince** (kontur kalınlığı), **uzun–kısa**
(aspect ratio + canvas'a göre uzunluk), **yüksek–alçak** (yükseklik), **sağda–solda–ortada**
(konum bölgesi), **UI stroke'lu mu**, **içinde metin var mı**. Başka ne ekleyelim?
→ Eksiklerin: ………

**D2.** ⭐ "Kalınlık" derken sadece **kontur (stroke)** kalınlığı mı, yoksa **öğenin kendisi**
(buton gövdesi) de dâhil mi? (Örn. "kalın uzun buton" = yüksek gövde + uzun genişlik?)
→ sadece kontur / gövde de dâhil / ikisi ayrı özellik

**D3.** Kontur kalınlığını **mutlak px** mi, **öğenin kısa kenarına oranı** mı, yoksa **canvas'a
oranı** mı olarak öğrenelim? (Önerim: **üçü de** ayrı özellik — farklı canvas ölçeklerinde
karşılaştırılabilirlik için.) → D / Y?

**D4.** Renk bilgisini **HSV/HSL bileşenleri** (hue, saturation, value) olarak mı öğrenelim,
yoksa **12 kovalık renk kovası** (kırmızı/turuncu/sarı/yeşil/cyan/mavi/mor/pembe/kahverengi/
gri/beyaz/siyah) olarak mı? (Önerim: **ikisi de**.) → D / Y?

**D5.** ⭐ "Kontur, dolgudan koyu mu?" özelliği benim bulduğum en güçlü **çizgi film / stud**
göstergesi. Bunu birinci sınıf özellik yapalım. → D / Y?

**D6.** Metin için: **metin alanının kutuya oranı** (metin yoğunluğu) ve **harf sayısı** öğrenilsin mi?
(Çok metin = TextLabel, az metin = buton etiketi.) → D / Y?

---

## E. Eğitim verisi & gizlilik

**E1.** ⭐ Export'ta **iki dosya** çıksın: (1) Studio'nun okuduğu mevcut JSON, (2)
`EI_<Ad>_egitim.json` (tam özellikli eğitim verisi). → D / Y?

**E2.** Eğitim dosyasına **katman adları** dâhil edilsin mi? (Önerim: evet, ama "ad" ayrı bir kanal;
isimsiz katmanlarda model adı kullanmasın.) → D / Y?

**E3.** Gizlilik: **dosya adı, sayfa adı, Figma dosya anahtarı, kullanıcı adı alınmasın.**
Sadece katman adları + geometri + renk + stil. → D / Y?

→ **Cevap: Y — kırpma yok** (KARARLAR.md §2.2). Hiçbir alan kırpılmaz; katman adları +
geometri + renk + stil + tasarım/export adları hepsi kalır (gerçek veri: `real-exports.jsonl`
içinde export adları da var). Figma dosya anahtarı gibi kimlik alanları kaynakta hiç üretilmez —
bu kırpma değil, hiç toplanmamadır. Cihazdan çıkış: kullanıcı isterse dosya gönderir (karar 12).

**E4.** Eğitim verisine **PNG küçük resim (thumbnail, 64×64)** de ekleyelim mi? Renk/ışık/gölge
dağılımını **pikselden** de öğrenebiliriz (özellik vektörüne ek). Dosya boyutu büyür.
→ Evet ekle / Hayır, sadece sayısal veri

**E5.** ⭐ Eğitim akışı: `ingest.py` önce **mevcut kural motoruyla otomatik etiketlesin**
("öğretmen"), sonra **sen** `label_tool.py` ile düzelt. Elle etiketlenmiş veri ağırlığı 1.0,
öğretmen etiketi 0.35. → D / Y?

**E6.** İlk veri seti **kaç GUI** olacak? (Tahmin: 20–50 GUI yeterli başlangıç için.)
→ …… GUI

---

## F. Animasyon

**F1.** ⭐ Animasyon kategorileri: **giriş, çıkış, hover, basma (press), döngü (idle), dikkat
(attention), geçiş (page transition)**. Eksik var mı? → ……

**F2.** ⭐ Roblox'ta animasyon = **TweenService** ile **LocalScript**. Tek bir `EI_AnimData`
(ModuleScript) + tek bir `EI_AnimController` (LocalScript) üretelim, her öğe için ayrı script değil.
→ D / Y?

**F3.** Tween edilebilir hedefler: `UIScale.Scale`, `Position`, `Rotation`, `BackgroundTransparency`,
`ImageTransparency`, `TextTransparency`, `UIStroke.Thickness`, `UIShadow.BlurRadius`,
`UIGradient.Offset/Rotation`, `GroupTransparency` (CanvasGroup). Eksik var mı? → ……

**F4.** ⭐ "Beğenmedim" dendiğinde: **farklı kategoriden** bir animasyon mu verelim, yoksa **aynı
kategorinin farklı parametreleri** (daha hızlı/yavaş, farklı easing) mi? (Önerim: **5 alternatif,
en az 3 farklı kategori** + her birinin hızlı/yavaş varyantı.) → D / Y?

**F5.** Animasyon süreleri **GUI ölçeğine göre** otomatik ayarlansın mı? (Büyük GUI'de 0.5 sn,
küçük ikonda 0.2 sn gibi.) → D / Y?

**F6.** Animasyon **sıralaması** (stagger): aynı kategorideki öğeler sırayla (0.05 sn gecikmeyle)
girsin mi? → D / Y?

**F7.** İlk etapta **kaç animasyon** girelim kütüphaneye? (Önerim: **30** — format otursun, sonra
100+'a çıkarız.) → …… adet

**F8.** Animasyon önerisi **sınıf modelinin çıktısına bağlı** olsun mu? (Butona "basma" animasyonu,
panele "giriş", ikona "hover" gibi.) → D / Y?

---

## G. Kapsam & süreç

**G1.** ⭐ Kullanıcılara **hiç açmayacağız**; model yalnızca senin verinle eğitilecek ve
"Asistan" özelliği **varsayılan olarak kapalı** gelecek (AÇILINCA v9 davranışı birebir aynı).
→ D / Y?

**G2.** ⭐ Mevcut JSON'u **v10'a yükseltelim ama eski alanları koruyalım**; v9 okuyan eski Studio
eklentisi yeni JSON'u sorunsuz okusun. → D / Y?

**G3.** `figma-plugin-klasik/`'i de güncelleyelim mi, yoksa sadece `figma-plugin-all-in-one/` mi?
→ ikisi / sadece all-in-one

**G4.** Önerilen kalınlık/radius **otomatik uygulanmasın**, "Öneri" olarak gösterilip kullanıcı
onaylasın. → D / Y?

**G5.** ⭐ Sıra: **A1** özellik spec'i + 3 dil + determinizm testi → **A2** öğretmen + ingest →
**A3** sınıf modeli → **A4** entegrasyon → **A5** boyut/kalınlık → **A6** stil → **A7** animasyon.
Bu sıra doğru mu? → D / Y? (Y ise doğru sırayı yaz)

---

### ⭐ En kritik 10 (bunlar mimariyi belirliyor)
A1, A2, A5, B1, B3, B4, B6, C1, C2, C3 — artı C5, D2, E5, G1.

**Cevap formatın:** `A1-D, A2-Y: aspect 3+ olmalı, B1-D, B3-b, ...`
Boş bıraktığın her şeyi **iddiam doğru** kabul edeceğim.

---

## H. ROBLOX LUAU ANİMASYON — Pluginde hazır animasyonlar

**H1.** ⭐ Animasyonları çalıştırma yöntemi hangisi olsun?
- (a) **Sadece `TweenService`** — basit, hafif, Roblox'un standart yolu (önerim)
- (b) `TweenService` + özel **spring modülü** — hover/takip daha akıcı ama kod artar
- (c) `RenderStepped` + elle lerp — en akıcı ama her öğe için döngü, daha ağır
→ a / b / c

**H2.** ⭐ **Sonsuz döngüler** (glow nefesi, huzme dönüşü, shimmer) performans için:
sadece GUI görünürken çalışsın, gizlenince duraklasın mı? → Evet otomatik duraklat / Hayır sürekli

**H3.** Tween çakışması: yeni animasyon başlarken eskisi **`Cancel()`** edilsin mi (titreme önler),
yoksa üstüne binsin mi? → İptal et / Bin

**H4.** ⭐ Sayaç (count-up) animasyonu: `TweenService` **string tween edemez**, o yüzden elle
sayım döngüsü üretmem gerekir. Bunu ister misin, yoksa sayaç animasyonunu kütüphaneden çıkaralım mı?
→ Elle döngü üret / Çıkar

**H5.** ⭐ Dosya yapısı hangisi?
- (a) **Tek `EI_AnimData` (ModuleScript) + tek `EI_AnimController` (LocalScript)** — önerim, temiz
- (b) Her öğeye kendi LocalScript'i — basit ama 100 öğede 100 script, kalabalık
- (c) **Attribute tabanlı** — kod yok, sadece Attribute; ayrı bir controller okur
→ a / b / c

**H6.** ⭐ Butonlara **otomatik `UIScale` ekleyelim mi**? (hover/basma için şart.)
AnchorPoint'i 0.5,0.5 yapmak pozisyonu kaydırır — otomatik düzeltmemi onaylıyor musun?
→ Evet ekle + düzelt / Ekle ama AnchorPoint'e dokunma / Hayır elle eklerim

**H7.** Hangi tetikleyiciler **otomatik bağlansın**? (Çoklu seç)
- (a) `MouseEnter`/`MouseLeave` → hover animasyonu
- (b) `MouseButton1Down`/`Up` → basma animasyonu
- (c) GUI açılışta → giriş animasyonu
- (d) Sekme/sayfa değişiminde → geçiş animasyonu
- (e) Hiçbiri — kullanıcı kendi kodundan çağırsın
→ ……

**H8.** `ReduceMotion`: `StyleQuery.ReduceMotionEnabled` okunup animasyonlar kapatılsın/kısaltılsın mı?
→ Evet / Gerek yok

**H9.** ⭐ **Hazır "animasyon paketleri"** ister misin? Tek tıkla tüm GUI'ye tutarlı bir set:
- **"Cartoon Oyun Menüsü"** = pop giriş + küçül-zıpla basma + zıplama hover
- **"Anime Lobi"** = zoom giriş + glow nefesi + huzme dönüşü + sparkle
- **"Stud Klasik"** = shrink-bounce basma + shine geçişi + sade giriş
- **"Minimal"** = fade giriş + hafif ölçek hover
→ Evet, 4 paket yap / Sadece tek tek seçim olsun / Şu paketler olsun: ………

**H10.** Animasyonlar plugin içine **gömülü** mü gelsin (kullanıcı listeden seçsin), yoksa export
sırasında mı üretilsin? → Gömülü + seçim / Export'ta üret

---

## I. GELİŞMİŞ ÖĞRENME MOTORU

**I1.** ⭐ "Neden böyle dedim" açıklaması (attribution) **nerelerde** görünsün? (Çoklu seç)
- (a) Figma panelinde (export sırasında, güven skorunun yanında)
- (b) Studio panelinde (import sonrası, öğe seçince)
- (c) Eğitim raporunda (terminal/HTML)
- (d) Hiçbirinde — sadece hata olunca göster
→ ……

**I2.** ⭐ **Hata düzeltme akışı** nasıl olsun?
- (a) Figma'da export sırasında (tahminleri gör, düzelt, JSON'a yaz)
- (b) Studio'da import sonrası (yanlış sınıfı değiştir, "Asistan'a öğret")
- (c) Ayrı bir CLI aracı (`label_tool.py`) — en düzenli ama Figma/Studio dışında
- (d) Hepsi (a+c önerim)
→ a / b / c / d

**I3.** ⭐ Confident Learning **şüpheli etiket** bulunca: sana mı sorsun, otomatik mi düzeltsin?
→ Sana sorsun / Otomatik düzelt (riskli) / Sadece işaretle, dokunma

**I4.** Hata teşhis kovalarım doğru mu? (7 kova: EKSİK_ÖZELLİK, YETERSİZ_VERİ, ETİKET_HATASI,
STİL_UYUŞMAZLIĞI, KURAL_MÜDAHALESİ, BAĞLAM_EKSİK, SINIR_DURUM) → D / Y? Eksik: ……

**I5.** Aktif öğrenme: sana **seans başına kaç soru** sormalı? (Önerim: 20, en az 5 farklı kümeden)
→ …… soru

**I6.** ⭐ Model **doğrusal (lojistik regresyon)** kalsın mı? Kritik: doğrusal modelde açıklama
**matematiksel olarak tam ve bedava**. MLP eklersek doğruluk biraz artar ama açıklama yaklaşık olur.
→ Doğrusal kalsın (açıklanabilirlik) / Doğruluk için MLP'ye geç / Hibrit: eğitimde MLP, açıklamada doğrusal sürrogate

**I7.** Model otomatik güncellensin mi, yoksa her seferinde **senin onayınla** mı yayınlansın?
→ Otomatik (altın seti geçerse) / Onaylı (önerim)

**I8.** Yeni model yayınlanmadan önce **altın set** (elle doğrulanmış sabit örnekler) oluşturalım mı?
Bu set hiç değişmez, her sürüm ona karşı ölçülür. → Evet (önerim) / Gerek yok

**I9.** Unutma (catastrophic forgetting) riskine karşı: her yeniden eğitimde **eski örneklerden
temsili bir havuz (replay)** tutulsun mu? → Evet / Hayır
