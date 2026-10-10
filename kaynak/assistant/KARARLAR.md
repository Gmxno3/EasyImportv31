# EasyImport — Karar Kaydı (Decision Log)

> **Amaç:** `PLAN.md` §8, `SORULAR.md` (A–I) ve `SORULAR-LUAU.md` (L1–L15) sorularına verilen
> cevapların **tek doğruluk kaynağı**. Bir çelişki olursa bu belge kazanır; plan belgeleri buna göre güncellenir.
> **Tarih:** 2026-10-06 · **Cevaplayan:** proje sahibi

---

## 1. Verilen cevaplar → uygulanacak kararlar

| # | Soru (ID) | Senin cevabın | Uygulanacak karar |
|---|---|---|---|
| 1 | **I6** — Model doğrusal mı, sinir ağı (MLP) mı? | *"ne dediğini anlamadım, daha iyi açıkla"* | ⏳ **AÇIK** — sade açıklama §2.1'de; cevap bekleniyor |
| 2 | **I2** — Hata düzeltme akışı nerede olsun? (Figma / Studio / CLI / hepsi) | *"Hata düzeltme olmasın… ama asistanın hata düzeltmesi olsun"* | ✅ **Kullanıcıya soran/düzelttiren arayüz YOK.** Figma'da "düzeltme sekmesi", Studio'da "Asistan'a öğret" butonu yapılmayacak. Asistan hataları **kendi içinde** düzeltir: kural çelişkisi avı, etiket sağlığı (confident learning), kullanım istatistikleri. |
| 3 | **I1** — "Neden böyle dedim" açıklaması nerede görünsün? | *"Olmasın; kullanıcı beğenmezse yeniden farklı şeyler yapsın"* | ✅ Panellerde **açıklama gösterilmeyecek**. Katkı/kök-neden hesabı yalnızca **asistanın iç teşhisi + eğitim raporu** için kullanılır (sen görürsün, son kullanıcı görmez). Beğenilmeyen öneri → **yeni/alternatif öneri** üretilir (soru sorulmaz). |
| 4 | **E1/E3** — Eğitim dosyası çıksın mı + hangi alanlar alınmasın? | *"Tam anlamadım ama bütün verilerle eğitilsin, çünkü halka açık bedava plugin"* | ✅ **E1 = EVET:** export iki çıktı verir — (1) Studio'nun okuduğu `EI_Ad.json`, (2) eğitim dosyası `EI_Ad_egitim.json`. <br>✅ **E3 = HİÇBİR ALAN KIRPILMAZ:** katman adları, sayfa adı, dosya adları ve tüm stil alanları eğitim dosyasında kalır. <br>⏳ Verinin **kimden** toplanacağı §3'te açık soru. |
| 5 | **L1/L3** — Animasyon motoru + dosya yapısı | *"Humanoid filan değil, UI animation Luau ile; o kadar da gerek yok animController filan"* | ✅ **TweenService** (yerleşik, ek modül yok). Spring **iptal** (L2 de iptal). `EI_AnimController` / `EI_AnimData` modül çifti **yapılmayacak** → her UI için **tek üretilmiş LocalScript** içinde düz Luau tween kodu (hover/basma bağlamaları da aynı scriptte). |
| 6 | **L5** — Hover/basma otomatik bağlansın mı? | *"Asistan otomatik yapar, kullanıcı seçer"* | ✅ Butonlara hover + basma animasyonu **varsayılan olarak otomatik bağlanır**; kullanıcı isterse değiştirir veya kapatır. |
| 7 | **L9** + kullanımdan öğrenme | *"Tabi hazır paketler olsun; asistan kullanıcıların seçtiklerinden de öğrensin: ne sıklıkla, hangi stilde, nerede, buton mu, çok detay var mı, anime stili mi kullanılıyor"* | ✅ **4 hazır paket:** 🎮 Oyun · ✨ Premium · 🧱 Klasik (stud) · 🎌 Anime. <br>✅ **`anim-usage` kaydı birinci sınıf gereksinim:** her seçim şu bağlamla kaydedilir → animasyon, öğe sınıfı, boyut kümesi, stil (cartoon/stud/anime), GUI türü, kategori, sıklık. Beğenilmeyen öneri **negatif sinyal** olur. Animasyon modeli (`train_anim.py`) bu veriyle eğitilir. |
| 8 | **PLAN §8.1** — İlk veri: senin export'ların mı, sentetik mi? | *"2 side"* → **ikisi de** | ✅ Sentetik veriyle A1–A3 hattı doğrulanır, **ve** gerçek export'ların eklendiğinde model yeniden eğitilir. İki kaynak ayrı `src` etiketiyle tutulur. |
| 9 | **PLAN §8.2** — 14 sınıf yeterli mi? | *"yeterli"* | ✅ Sınıf listesi olduğu gibi kalır. Dekoratif parçalar (`UICorner`, `UIStroke`) sınıf **olmayacak**; `DROP` / `MERGE` yapısal çıktı olarak kalır. |
| 10 | **PLAN §8.4** — `figma-plugin-klasik/` de asistan alsın mı? | *"Almasın, o[nu] kullanmıyorum da"* | ✅ Geliştirme **yalnızca `figma-plugin-all-in-one/`**. Klasik klasöre dokunulmaz (bu oturumda silinmez), asistan entegrasyonu yapılmaz. |

### Yan kararlar (cevaplarından türeyen)

| Soru | Karar |
|---|---|
| **I3** (confident learning şüphelisi) | Kullanıcıya sorulmaz → **otomatik işaretlenir**, sana (geliştiriciye) eğitim raporunda listelenir. |
| **I5** (seans başına kaç soru) | Son kullanıcıya soru sorulmayacağı için **iptal**. "Aktif öğrenme" yalnızca **senin eğitim oturumlarında** çalışır. |
| **I4** (7 kovalı kök neden) | Kalır, ama **iç teşhis**: hata kovaları eğitim raporunda + asistanın kendi düzeltmesinde kullanılır. |
| **I7 / I8** (model onayı / altın set) | Varsayılan: **onaylı yayın** + **altın set var** (aksi söylenmedikçe). |
| **I9** (replay buffer) | **RLS** tercih edildiği için replay buffer'a gerek yok (`OGRENME-MOTORU.md` §7.1). |
| **L2** (spring) | Motor TweenService seçildiği için **iptal**. |
| **L3** (dosya yapısı) | Modül çifti yok → **tek LocalScript** (üretilen kod). |
| **L4, L6, L7, L8, L11–L15** | Cevap verilmedi → `SORULAR-LUAU.md`'deki **önerilen varsayılanlar** geçerli kabul edilir (ör. L7: animasyon şiddeti stile göre; L12: hareket azaltma desteği; L15: Studio içi önizleme). İtiraz edersen değiştirilir. |

---

## 2. Anlaşılmayan iki madde — sade dille

### 2.1 "Doğrusal model mi, MLP mi?" (Soru I6) ne demekti?

Asistana "bu katman nedir?" dedirten şey bir **puanlama** işidir. İki farklı yol var:

**(a) Doğrusal model (lojistik regresyon)** — *şeffaf kutu*
Her özelliğin bir **ağırlığı** vardır ve puanlar toplanır:
```
adında "button" var      → +2.0 puan
kontur kalın (>3 px)     → +1.4 puan
içinde metin var         → -0.9 puan
boyutu bu GUI'de en sık  → +0.6 puan
                          ─────────
ImageButton toplam:        3.1  ← en yüksek → "ImageButton" der
```
- ✅ "Neden ImageButton dedim?" sorusunun cevabı **tam olarak** bu listedir; uydurma yok, olasılık yok,
  her çalıştırmada aynı.
- ✅ Asistanın **kendi hatasını teşhis etmesi** (senin 2. maddede istediğin şey) buna dayanır:
  "doğru sınıfın puanını en çok hangi özellik düşürdü" → o özellik/ağırlık düzeltilir.
- ⚠️ Kusuru: yalnızca **toplama–çıkarma** yapar. "İçinde metin VAR **ve** kontur KALIN" gibi
  *kombinasyonları* kendi başına göremez; biz ona hazır kombinasyon özelliği verirsek görür
  (ör. `metinli_ve_kalin_konturlu = 1`).

**(b) MLP (gizli katmanlı sinir ağı)** — *kara kutu*
Araya gizli katman(lar) koyar, kombinasyonları **kendi bulur**; genelde biraz daha isabetli olur.
- ⚠️ "Neden?" sorusuna **kesin** cevap verilemez. Açıklama yalnızca tahmini olur (SHAP/LIME gibi
  yaklaşık yöntemler), üstelik her çalıştırmada küçük farklar çıkabilir.
- ⚠️ Doğrusal modele göre Lua'da çalıştırması ve hata ayıklaması daha zor, dosya boyutu daha büyük.

**(c) Hibrit** — eğitimde MLP, açıklama için ayrı bir doğrusal "ikiz" (surrogate) model.
İsabet yüksek kalır ama açıklama **yaklaşık** olur (asistanın kendi kendini teşhisi zayıflar).

> **Önerim:** **(a) doğrusal ile başla.** Asistan başlangıçta %85 hedefini doğrusal modelle kovalasın;
> yetmezse **kombinasyon özellikleri ekleyerek** (ör. metin+kontur, boyut kümesi+sınıf) yükseltelim.
> Bu, hem istediğin "asistan kendi hatasını düzeltsin" davranışını hem de tam açıklanabilirliği korur.

### 2.2 "E1/E3: iki dosya + gizlilik" ne demekti?

Bu soru **export edilen dosya sayısı** ve **eğitim verisine hangi alanların gireceği** ile ilgiliydi:

- **E1 — "İki dosya çıksın mı?"**
  Bugün Figma sadece **bir** JSON üretiyor: Studio'nun GUI kurmak için okuduğu `EI_Ad.json`.
  Seçenek: bunun **yanında** bir de *eğitim dosyası* üretmek (`EI_Ad_egitim.json` — özellik vektörü +
  etiket + stil + kullanım bilgisi). Bu dosya Figma'ya değil, doğrudan **modele** gider.
  → **Sen: çıksın** (bütün verilerle eğitim).

- **E3 — "Eğitim dosyasında ne olmasın?"**
  Burada endişe şuydu: katman adları (`Player_Health_Bar`), sayfa adı, dosya adı gibi bilgiler
  eğitim verisine girerse **gizlilik** sorunu olur mu? (Tasarımcının projesinden isimler dışarı çıkar.)
  → **Sen: hiçbir alan kırpılmasın, hepsi kalsın.** Adlar zaten modelin en güçlü sinyallerinden biri
  (`button`, `hp`, `icon` token'ları); kırpmak isabeti düşürürdü.

- **Açık kalan kısım:** Eğitim dosyası **senin cihazında mı üretilip duracak**, yoksa plugin
  kullanıcılarının seçimleri **sana mı gönderilecek**? (Halka açık ücretsiz plugin olması nedeniyle
  bunu netleştirmemiz gerekiyor — §3'teki sorulardan biri.)

---

## 3. İkinci tur cevaplar (2026-10-06, aynı gün)

| # | Soru | Cevap | Uygulanacak karar |
|---|---|---|---|
| 11 | **I6** — Model hangisi olsun? | **"Doğrusal model"** | ✅ **Softmax (lojistik) regresyon.** Attribution tam ve bedava → asistanın iç teşhisi güçlü. İsabet yetmezse **kombinasyon (çapraz) özellik ekleyerek** yükseltilir; MLP'ye geçilmez. |
| 12 | **E3b** — Kullanıcı verisi nasıl toplanacak? | **"Sunucu olmadan olmaz mı? Plugin'in içinde olsa"** | ✅ **REVİZE — SUNUCU YOK.** Öğrenme tamamen plugin'in içinde, kullanıcının cihazında: `figma.clientStorage` (5 MB) + `plugin:SetSetting` (anahtar `EasyImportLearn`, 64 KB üst sınır). <br>• Her kullanıcı **kendi** seçimlerinden anında öğrenir (animasyon + sınıf tercihi). <br>• Toplu iyileşme **dosya ile**: panelde "öğrenme paketini indir" → kullanıcı isterse sana gönderir → sen `tools/merge_learn.py` ile birleştirip **yeni plugin sürümünde** yayınlarsın. <br>• Arka planda otomatik gönderim **teknik olarak yok** (sunucu olmadığı için) — gizlilik garantisi. <br>Detay: `assistant/YEREL-OGRENME.md`. |
| 13 | **L10** — Glow için `UIShadow` kullanılsın mı? | **"Kullanma"** | ✅ `UIShadow` glow **üretilmeyecek**. Parlama/glow efektleri **UIGradient + yarı saydam katman + Tween** ile yapılır (en geniş Studio uyumluluğu). Mevcut JSON'daki `shadows[]` alanları ise **olduğu gibi** UIShadow'a çevrilmeye devam eder (gölge ≠ glow; bu karar yalnızca animasyon/glow üretimini bağlar). |

### 12. maddenin sonucu: sunucu yok, dosya var
Öğrenme plugin'in içinde çalışıyor; **hiçbir uç nokta gerekmiyor.** Toplu iyileşme istenirse
kullanıcı "öğrenme paketi" dosyasını indirip sana gönderir (tek tık, isteğe bağlı).
Kurulum/hesap/sunucu işi **sıfır**. Detaylar: `assistant/YEREL-OGRENME.md`.

## 4. Kapalı maddeler (özet)

| ID | Karar |
|---|---|
| **I6** | Doğrusal model (softmax regresyon) — tam açıklanabilirlik |
| **I1/I2/I3/I5** | Kullanıcıya soran/düzelttiren akış yok; her şey asistanın içinde |
| **E1/E3/E3b** | İki dosya (Studio + eğitim), alan kırpma yok, öğrenme **cihazda** (sunucu yok) |
| **L1/L2/L3** | TweenService · spring yok · modül çifti yok (tek üretilmiş LocalScript) |
| **L5** | Hover/basma otomatik bağlanır, kullanıcı seçer |
| **L9** | 4 hazır paket + kullanımdan öğrenme (`anim-usage`) |
| **L10** | UIShadow glow **yok** |
| **PLAN §8.1/8.2/8.4** | Sentetik + gerçek veri · 14 sınıf yeterli · klasik plugin'e asistan yok |

---

## 4. Bu kararların plan belgelerine etkisi (uygulanacak düzenlemeler)

| Belge | Değişiklik |
|---|---|
| `PLAN.md` §6.1/§6.2 | Kullanıcıya düzelttiren akışlar ("Güven skoru düşük katmanlar → hızlı düzeltme", "Asistan'a öğret") **kaldırılır**; yerine otomatik öneri + alternatif üretimi gelir. |
| `PLAN.md` §6.2 | `EI_AnimData` + `EI_AnimController` yerine **tek üretilmiş LocalScript**. |
| `OGRENME-MOTORU.md` §7/§9 | Aktif öğrenme kuyruğu son kullanıcıya değil, **geliştiricinin eğitim oturumuna** bağlanır. |
| `OGRENME-MOTORU.md` §4 (I1) | Attribution yalnızca iç teşhis + eğitim raporu; panellerde gösterilmez. |
| `SORULAR-LUAU.md` L1/L2/L3/L5/L9 | TweenService · spring iptal · tek script · hover otomatik · 4 paket. |
| `ARASTIRMA.md` Bölüm E | Eğitim dosyası alanları: **kırpma yok**. |
| `SORULAR.md` E3 | Gizlilik maddesi "kırpma yok" olarak güncellenir. |

---

*Yeni karar geldikçe bu belgeye satır eklenir; eski kararlar silinmez, "geçersiz" olarak işaretlenir.*

---

## 13. Stud tespiti v3 — kullanıcı araştırma talebiyle (2026-10-06)

Senin "Asistanın studları nasıl anlayacağını yazdır + araştır" talimatın üzerine stud tespiti
isim tahmininden **ölçüme** taşındı (ayrıntı: `ARASTIRMA.md` §C1c, `ANALIZ.md` §9.11):

| Karar | Gerekçe |
|---|---|
| **Döşeme hücresi ölçülür** (`code.js` → `item.ei` → RAW) | Figma `scalingFactor` × `Image.getSizeAsync()` = hücre px; Studio'ya `TileSize` olarak birebir geçer |
| **Tek düğümdeki "stud" adı yetmez** | Modern paketlerde tek stud **ikonu** var; stud stili değil. Ad kanıtı ≥2 düğüm VEYA ad + ölçülmüş döşeme |
| **`texture/pattern/brick` zayıf kanıt** | Duvar/ahşap dokusunda da geçer; tek başına stud demek değil |
| **Veto kuralları** (>3 benzersiz doku · efekt >0.60 · detay >0.62) | "Başka texture kullanılmaz" + stud'un efekti az, detayı orta-düşük |
| **Negatif fixture'lar kalıcı** | `stud-icon.json` sert kuralla kilitli; cartoon/anime/edge de stud çıkmamalı |
| **Piksel kanalı kapalı** | `getBytesAsync` asenkron + kırılgan; ölçülmüş hücre + tekrar yeterli, gerekirse açılır |

Sonuç: kalibrasyon **6/6** (ikisi adında "stud" geçmeyen dosya), tüm kapılar yeşil.

## 14. Eğitim kapısı artık "dürüst genelleme" arıyor

152 satıra çıkınca modelin çöktüğü görülünce (bkz. `ANALIZ.md` §9.12) iki karar alındı:

| Karar | Gerekçe |
|---|---|
| **Kabul kapısı = eğitim seti ≥ %85/%95 + export-LOO ≥ %55** | 5306 parametre / 152 satırda eğitim seti doğruluğu ezberlemeyle %100'e çıkabiliyor; asıl soru "hiç görülmemiş bir ekranda ne yapıyor" |
| **Uç girdiye karşı iki kat koruma: winsor (eğitim) + `clipZ` (tahmin)** | Tek uç satır standardizasyonu bozup modeli sıfırlayabildi (kanıtlandı); ikinci koruma gömülü JS/Lua'da da var |
| **Sınıf ağırlığı yumuşatıldı (√ + tavan 3.0)** | Tam ters-frekans ağırlığı tek örnekli sınıfı 11× yapıp modeli ona teslim ediyordu |
| **Çöküş imzası kalıcı kapıda** (`verify_model.py`) | Aynı hatanın sessizce geri dönmesini engeller: W/b sıfır, std > 1e6, `clipZ` yok → model kabul edilmez |

Not: `clipZ` eğitimde ve gömülü tahminde **aynı** adımdır; `verify_predict.py` 110 vektörde
(1e9/NaN/sonsuz kenar durumları dâhil) JS ≡ Lua ≡ Python paritesini doğrular.

## 15. A4b — asistanın devreye girme koşulları (`ei` kapısı)

| Karar | Gerekçe |
|---|---|
| **`ei` yoksa asistan hiç çalışmaz** | Eski export'larda çıktı bayt bayt v9 olmalı; kanıt `datasets/golden/v9_decisions.json` + `verify_plugin_v9.py` |
| **Ad/etiket sinyali olan katmana model dokunmaz** | "Açık etiket her zaman kazanır" (PLAN §M1); kullanıcının `_ImageButton` yazdığı yeri model ezmemeli |
| **Güven eşiği 0.70, altındaysa kural motoru** | PLAN §M1'in eşiği; düşük güvende modelin dik başarısızlığını önler |
| **Tür-uyumsuz model tahmini atılır** | Kural motorunun `forceClass` kapısıyla aynı mantık (text/resim/frame uyumu) |
| **Kullanıcının düzeltmesi modelin önüne geçer (≥2 gözlem)** | Kendi geçmişi, genel modelden daha güçlü sinyaldir; soru sorulmaz (KARARLAR §2) |
| **Açık etiket ≠ model tahmini → düzeltme sayılır** | Kullanıcı etiketi elle yazdıysa bu bir tercih beyanıdır; ekstra UI gerekmez |
| **Öğrenme `plugin:SetSetting("EasyImportLearn")`** | Sunucu yok; anahtar nokta/ters bölü içermez (sessiz başarısızlık riski) |
| **Modüller `.rbxmx`'e gömülü, `.lua` kaynağında yok** | Tek doğruluk kaynağı `.lua` kalır; kaynak üzerinde çalıştırılırsa asistan sessizce kapalı (v9 davranışı) |
| **v9 hatası düzeltmesi (IMAGE dolgulu frame siliniyordu) YALNIZCA asistan modunda** | Bu bir davranış değişikliğidir; v9 sözleşmesini bozmamak için kapılı tutuldu — gerçek kullanıcı testinden sonra herkese açılabilir (karar senin) |
