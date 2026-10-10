# EasyImport — DURUM RAPORU (yapılmayanlar)

> Tarih: 2026-10-06 · Dal: `arena/f1723caf-easyimport` · Son commit: `964db25`
> Bu rapor **kalan işleri** listeler. Tamamlananlar için: `ANALIZ.md §9` (uygulama günlüğü) ve
> kapı tablosu. Yöntem: her satır ya dosya envanteriyle ya da kapı çıktısıyla doğrulandı.

---

## 0. Tek bakışta durum

| Alan | Durum | Kanıt |
|---|---|---|
| RAW çıkarıcı (JS ≡ Lua) | ✅ | `verify_extract.py` (7 export × 179 alan) |
| Özellik vektörü 379 (Py ≡ JS ≡ Lua) | ✅ | `verify_runtime.py` |
| Kural öğretmeni (Lua ≡ Python) | ✅ | `verify_teacher.py` (193 katman) |
| Stil tespiti + kalibrasyon 7/7 | ✅ | `verify_style.py` |
| Yerel öğrenme kodlaması (JS ≡ Lua) | ✅ | `verify_learn.py` |
| Sınıf modeli (softmax, stil öncüllü) | ✅ | `verify_model.py` · `model/model.json` · export-LOO **%95.67** · dosya-LOO **%98.17** · jenerik katman **%99.86** |
| Model gömme + tahmin paritesi | ✅ | `verify_predict.py` (JS ≡ Lua ≡ Python) |
| **Modelin eklentide KULLANILMASI** | ✅ | `verify_plugin_v9.py` · 6 modül `.rbxmx`'e gömülü · 42/94 katmanda model kararı |
| **Figma panelinde öğrenme** | ❌ | `ui.html`/`code.js`'de `clientStorage` 0 |
| **Eğitim dosyası çıktısı (E1 kararı)** | ✅ (Figma tarafı) | `code.js` `buildTrainDump` → `train` alanı · `ui.html` “_egitim.json indir” · kapı: `tools/verify_train_dump.js` |
| **Animasyon üretici (TweenService)** | ✅ (giriş/hover/basma · fx ve döngü YOK) | `runtime/lua/EIAnim.lua` · `tools/build_anim_lua.py` · kapı: `tools/verify_anim.py` · Studio: `EI_Animator` LocalScript (yalnız asistan modu) |
| **FX tespiti** | ❌ | `ei-fxdetect.js` yok |
| **Öğrenme paketi birleştirme** | ✅ | `tools/merge_learn.py` + `verify_merge.py` (JS ≡ Python ≡ Lua) |
| Boyut/kalınlık modeli (M2) | ⬜ opsiyonel | `tools/train_size.py` yok |
| **v9 dondurma (altın dosya)** | ✅ | `datasets/golden/v9_decisions.json` · 7 fixture × 135 katman |
| Belgelerin güncellenmesi | ⚠️ kısmi | PLAN §212 hâlâ "≈165 özellik" diyor |

---

## 1. Eklenti entegrasyonu — **A4b** ✅ **YAPILDI** (gerçek Studio testi sende)

**Durum:** asistan artık eklentinin İÇİNDE. `EIRaw · EIStyle · EIFeatures_Spec · EIFeatures ·
EIModel · EILearn` modülleri `.rbxmx`'e gömülü (6 modül, paket 239 KB) ve karar akışına bağlı.

**Karar akışı (v9'u bozmaz):**
1. `ei` yan kanalı **yoksa** (v9 export'ları) asistan hiç hesaplamaz → çıktı birebir eski davranış.
2. `ei` **varsa**: RAW + stil çıkarılır (`Assist.prepare`), her katman için karar:
   - ad/etiket sinyali varsa (`forceClass`, `_button`, `_scroll`, `isNameButton`…) → **kural motoru**
     (v9) kazanır; asistan dokunmaz,
   - sinyalsiz katmanda model konuşur — ama yalnızca güven ≥ **0.70** ve sınıf tür-uyumluysa,
   - kullanıcının kendi düzeltmeleri (aynı bağlamda ≥2 gözlem) modelin önüne geçer (`ogrenme`).
3. Öğrenme cihazda saklanır: `plugin:SetSetting("EasyImportLearn")` (nokta/ters bölü içermez).
   Açık sınıf etiketi modelin dediğinden farklıysa bu bir düzeltme sayılır — soru sorulmaz.
4. Durum satırı import sonrası özeti yazar: `🤖 asistan: stil stud (100%) · model 10 · kural 8 ·
   düzeltme 2` + kaç katmanda model kararı verdiği.

**Kapı — `assistant/tools/verify_plugin_v9.py` (yeni, 13 kontrol):**
- **v9 dondurma:** modüller kapalıyken eklentinin karar yolu 7 fixture × 135 katmanda
  `datasets/golden/v9_decisions.json` altın dosyasıyla **birebir** (ad/etiket sinyalleri dâhil).
- **`ei` yokken:** modüller yüklü olsa bile kararlar aynı ve `predicts=0` (asistan hiç çalışmadı).
- **`ei` varken:** stil EXPECTED ile aynı · sinyalli katmana dokunulmadı · asistanın verdiği her sınıf
  üç dilli hattın doğrudan sonucuyla aynı · güven ≥ 0.70 · düğüm↔RAW eşlemesi tam ·
  öğrenilmiş düzeltme kararı değiştiriyor (kaynak `ogrenme`).
- **Paket:** modüller gömülü, fengari'de derleniyor, luau-lint temiz, gömme deterministik,
  `.rbxmx` XML'i geçerli ve içindeki kaynak üretilenle birebir, `build_rbxmx --check` senkron.

**Bu adımda bulunan GERÇEK v9 hatası (düzeltildi ama kapılı):** `simplifyTree`, **yalnızca görsel
(IMAGE) dolgusu olan frame'leri "boş sarmalayıcı" sayıp siliyordu** → stud başlık (`Bar_Top`),
buton yüzleri (`Btn_*_Yuz`), liste zemini (`Liste`) Studio'da hiç oluşmuyordu; yani stud dokusu
kayboluyordu. Düzeltme **yalnızca asistan modunda** devrede (`Assist.activeFor(doc)`), çünkü senin
"v9 JSON davranışı değişmeyecek" sözleşmen bayt bayt korunmalı. Kapı bunu kanıtlıyor: asistan
modunda 6 görsel dolgulu frame korunuyor, v9 yolunda katman sayısı aynı kalıyor. **Karar senin:**
gerçek kullanıcı testinden sonra bu düzeltmeyi herkese açalım mı? (Tek satır: bayrağı `true` yap.)

**Kalan:** (a) **gerçek Studio smoke testi** — aşağıdaki adımlar; (b) Figma panelinde model tahmini
+ seçim kaydı (§2 ile birlikte); (c) UIGridLayout/Item/DROP/MERGE karar yolları (§6'da not: bu
kapının arkasına girecekler).

**Smoke test (senin Studio'nda, 2 dakika):**
1. `roblox-studio-plugin/EasyImportStudioPlugin.rbxmx` dosyasını Studio'ya sürükle (eski sürümü
   değiştir) → eklenti araç çubuğunda görünür.
2. Figma'da v10 eklentisiyle bir tasarım export et (içinde `ei` alanları olan) → JSON'u paneldeki
   kutuya yapıştır → **Oluştur**.
3. Bak: durum satırının sonunda `🤖 asistan: stil …` olmalı; stud bir tasarımda stud başlık/buton
   yüzeyleri **dokulu** gelmeli (eski sürümde bunlar kayboluyordu).
4. Bir katmanın adını `Ad_ImageButton` yapıp yeniden içe aktar → aynı bağlamda ikinci kez
   tekrarlarsan asistanın o katmanı `ImageButton` yaptığını görmelisin (yerel öğrenme).

---

## 2. Figma paneli — öğrenme uçtan uca

**Durum:** `ui.html` 603 satır, `code.js` 955 satır; ikisinde de `clientStorage` **0**.
Yerel öğrenme motoru (`ei-learn.js` ≡ `EILearn.lua`) ve depolama kararı (Figma `clientStorage`
5 MB · Studio `SetSetting` anahtarı `EasyImportLearn`) hazır ama **bağlı değil**.

**Yapılacak:**
1. Seçim kaydı: kullanıcı bir animasyon/sınıf seçtiğinde `EILearn.observe(ctx, id, seçim)` →
   `figma.clientStorage.setAsync('EasyImportLearn', …)` (yazma sıklığı sınırlı, toplu yazma).
2. "Beğenmedim" → negatif sinyal (A8 döngüsü) + **MMR çeşitliliği**: 5 alternatif en az 3 farklı
   kategoriden (PLAN §A8).
3. **"Öğrenme paketi indir"** düğmesi: `ei-learn v1` metnini dosya olarak indirir; kullanıcı
   isterse geliştiriciye gönderir. Arka planda gönderim **yok** (KARARLAR §12).
4. Studio tarafı eşleniği: `plugin:SetSetting("EasyImportLearn", …)` + aynı paketi indirme.

**Bağımlılık:** §1 (panel ve plugin aynı sinyalleri üretmeli).

---

## 3. Eğitim dosyası (iki export) — **karar E1 · Figma tarafı ✅ (bu tur)**

**Bu tur yapıldı:** Figma `code.js` artık ikinci çıktıyı üretir: `train` alanı (`format: ei-train v1`,
`src: figma`), seçilen ağacın KIRPILMAMIŞ dökümü (katman adları, yollar, metin, stil alanları).
`ui.html`'de “_egitim.json indir” düğmesi var. v9 `json` çıktısı değişmedi (altın dosya bayt birebir;
`tools/verify_train_dump.js`). Kalan: Studio'nun `EI_Ad.json` dosya adıyla hizası ve §1/§2 çıktılarının
(model/stil/öğrenme olayları) eğitim dosyasına eklenmesi.


**Durum:** `code.js` hâlâ **tek** dosya üretiyor (`ui.html` → `.easyimport.json`).
Kararın (KARARLAR satır 4): (1) Studio'nun okuduğu `EI_Ad.json`, (2) `EI_Ad_egitim.json`
(eğitim dosyası, **hiçbir alan kırpılmadan**, katman adları dâhil).

**Yapılacak:** `ui.html` indirme akışına ikinci çıktı; içine §1'in model/stil çıktıları +
KARARLAR §12 öğrenme olayları; sürüm/format alanı (`ei-train v1`) ve `src` etiketi.

---

## 4. Animasyon hattı — **A6/A7/A8** · üretici ✅ (bu tur) · seçici UI ve FX ⏳

**Bu tur yapıldı:** `EIAnim.lua` (Studio, yalnız `ei` varken): giriş (üst düzey öğeler), hover
(butonlar) ve basma (butonlar) animasyonunu stil öncülüyle seçer ve UI başına TEK `EI_Animator`
LocalScript üretir (TweenService, L1/L3). Hover çıkışı, hover'a girmeden önceki değere döner.
Pivot (AnchorPoint 0.5,0.5) düzeltmesi sol-üst köşeyi korur; layout kabında yapılmaz.
UIShadow glow yok (L10). Kapı `tools/verify_anim.py`: Lua ≡ Python seçimi (4 stil), LocalScript
derlenir, sahte Roblox ortamında davranış ve pivot doğrulanır.

**Sınırlar (dürüst):** (a) fx ve döngü (`dongu`) kategorileri üretilmiyor — FX tespiti (A6) yok;
(b) `stagger:` gecikmeleri tek öğe için 0 sayılıyor; (c) `cartoon` öncülü (basma 1.3) mevcut kütüphanede
seçimi değiştirmiyor; (d) gerçek Studio'da görsel test yapılmadı; (e) Figma'da seçici/önizleme UI yok,
dolayısıyla kullanıcı seçimi (öğrenme sinyali) henüz toplanmıyor.

**Kalan:** seçici UI (Figma/Studio), FX tespiti (`ei-fxdetect.js`), `train_anim.py`, `dongu` üretimi.

**Durum:** `anim/anim-library.json` **108 animasyon** (10 kategori, 25 rol, 16 FX türü) ✅
Ama: `TweenService` pluginde **0**; `ei-anim.js`/`EIAnim.lua` yok; animasyon seçici UI yok;
`anim-usage` sinyalleri toplanmıyor; `train_anim.py` yok.

**Yapılacak (senin kararların çerçevesinde):**
1. Seçici: stil öncülü ağırlıkları (`animBias`: anime `fx 1.7 · döngü 1.45`, cartoon `basma 1.3`,
   stud shine sweep'leri) + kullanıcı seçimi; hover/press **otomatik bağlanır**, kullanıcı seçer.
2. Luau üretici: **TweenService**, spring yok, **UI başına tek LocalScript**, `UIShadow` glow
   için **kullanılmaz** (KARARLAR L1/L2/L3/L10).
3. FX tespiti (A6): `ei-fxdetect.js` — Figma'daki glow/ray/sparkle/shine/vignette katmanları
   (şu an yalnız `isShineFrame`/`isFx` RAW alanları var; eşleştirme kuralları yok).
4. `anim-usage` → `train_anim.py` (frekans, stil, konum, buton mu, detay seviyesi, anime kullanımı).

**Bağımlılık:** §1 (kullanıcı seçimi kaydı aynı altyapıyı kullanır).

---

## 5. Öğrenme paketi birleştirme — `tools/merge_learn.py` ✅ **YAPILDI**

**Durum:** araç yazıldı + kapısı yeşil. Sunucusuz akışın son halkası kapandı:
kullanıcı "öğrenme paketini indir" der → `ei-learn v1` metni (veya `{"text": …}` JSON sarmalayıcısı)
→ sen dosyaları toplar → `merge_learn.py` **offline** birleştirir → yeni model/önsel tablo → sürüm.

```
python3 tools/merge_learn.py paketler/*.txt -o datasets/learn/merged.txt --priors datasets/learn/priors.json
python3 tools/verify_merge.py          # kapı: JS ≡ Python ≡ Lua (fengari), sınırlar, düşmanca girdi
```

**Ne yapıyor:** sürüm/şema doğrulaması · sayaç toplama (aynı bağlam+id) · `--dedupe` (aynı kullanıcı
iki kez gönderdiyse) · `--min-observations` (gürültü süzgeci) · 400 bağlam / 64 KB sınırına
deterministik budama (kanon `prune` + `fit` portu) · rapor (en güçlü öneriler, **tutmayan öneriler**,
sınıf düzeltmeleri, kütüphane dışı id/sınıf/rol/fx uyarıları, `__proto__` benzeri token uyarısı) ·
`--priors` ile A7/A8'in tüketeceği önsel tablo (skor formülü `_meta`da yazılı) · `--report` JSON.

**Kapının kanıtladıkları (16 kontrol):** bayt paritesi (JS çöz+birleştir+kodla ≡ Python, 501 bayt) ·
birleşik dosyayı `EILearn.lua` de fengari'de çözüp aynı baytları üretiyor · skor formülü iki dilde
aynı · determinizm (aynı girdi ve **ters paket sırası** → aynı bayt) · sayaç korunumu · 600 bağlam →
400 · 4096 bayt/40 bağlam sınırı tutuyor (1660 bayt) · düşmanca girdi (satır sonu/boşluk enjeksiyonu,
negatif/ondalık sayaç, fazla alan, yinelenen satır) biçimi bozmuyor ve **kanon semantiği** korunuyor
(sonraki satır kazanır) · JSON sarmalayıcı ≡ düz metin · süzgeç · önsel tablo.

**Kalan (A4 entegrasyonuna bağlı, §2/§1):** panelde "öğrenme paketini indir" düğmesi ve paketin
gerçek cihaz durumundan üretilmesi. Araç tarafı hazır; biçim birebir kanon olduğu için panel
`EILearn.encode(state)` metnini olduğu gibi dosyaya yazacak (`.txt` veya `{"text": …}`).

**Not (karar E1/§3 ile ayrım):** bu paket **animasyon/sınıf tercihi sayaçlarıdır**, eğitim export'u
(`EI_Ad_egitim.json`, ham katman verisi) değildir. İkisi ayrı dosya, ayrı akış.

---

## 6. Model kalitesi — **gerçek veri eklendi, eğitim geçti** (dürüst ölçüm)

**Durum (2026-10-07 güncel):** 10 gerçek `.fig` tasarımı öğretildi → veri **4.642 örnek**
(4.490'ı gerçek export'lardan) · 14 sınıfın 10'unda örnek var. Yeni metrikler (§`GERCEK-VERI-RAPORU.md`):

```
eğitim seti : top-1 99.70% · top-3 99.89%      (örneklerin %71.9'u Frame → iyimser)
doğrulama   : top-1 99.49%
export-LOO  : ortalama %95.67 · en kötü %52.17 (35 kat; katlar export düzeyinde → iyimser)
dosya-LOO   : %98.17                            (10 kat; kardeş frame sızıntısı YOK — dürüst)
  └ jenerik katmanlar (modelin üretimde konuştuğu altküme): %99.86
    çoğunluk-sınıfı tabanı %78.33 → model +21.5 puan · 2.903 katmanda 3 hata
```

Zayıflık yalnızca **Studio'ya özel 5 sınıfta** (`ViewportFrame`, `VideoFrame`, `CanvasGroup`,
`ScrollingFrame`, `TextBox`; tüm veride 8 örnek): model bunları Frame/TextLabel'e çökertebiliyor.
Üretimde etkisi yok — bu katmanlar isimli (`Avatar_Viewport`, `Liste_ScrollY`…) ve `Assist.decide`
isim sinyali olan katmana dokunmuyor.

**Yeni kapı:** `tools/verify_generalization.py` — katları **tasarım dosyası** düzeyinde ayırır
(kardeş sızıntısı yok), jenerik katmanda PLAN §A3 kabulünü (≥ %85) arar. `--folds 3` hızlı,
tam koşu ~6 dk.

**Uçtan uca gerçek-tasarım kapısı (`tools/verify_real_run.py`):** eklentinin karar yolunu 28 gerçek
export'ta koşturur. Sonuç: 4.057 katmanda kural/model **%100** etiketle uyumlu, sinyalli katmana
dokunma 0, hizalama hatası 0, anime yanlış pozitifi 0; `ei` olmayan 5 tasarımda asistan kapalı ve
çıktı v9 ile birebir. Ayrıntı: `GERCEK-VERI-RAPORU.md` §5.1.

**Test düzeneği dersi:** `run_fengari` artık çıktıyı **dosyaya** yazar (boru, fengari'nin senkron
`writeSync`'ini non-blocking fd'de sessizce kısaltıyordu: 1.044 satırın 615'i geliyordu) ve
`run_lua` sürücünün bildirdiği satır sayısını doğrular — eksik çıktı artık gürültü çıkarır.

**Paket kuralı (2026-10-07 dersi):** model/stil değişince zincir şart —
`export_model.py` → `verify_predict.py` → `build_rbxmx.py` → `verify_plugin_v9.py`.
Bayat paket yüzünden asistan 61 yerine 42 katmanda konuşuyordu (GERCEK-VERI-RAPORU §3 Hata 4).

**Eski ölçüm (2026-10-06, sentetik veri):** kapsama genişletildi — 7. fixture (`widgets-kit`, 23 katman)
eklendi ve **14 sınıfın 10'u artık veride**: Frame 68 · TextLabel 39 · TextButton 22 ·
ImageLabel 12 · ImageButton 5 · ScrollingFrame 2 · TextBox 1 · CanvasGroup 1 · VideoFrame 1 ·
ViewportFrame 1. Hâlâ **sıfır örnek: UIGridLayout, Item, DROP, MERGE**.

**Eğitim çöküşü bulundu ve düzeltildi (bu bölümün en önemli çıktısı):**
152 satıra çıkınca `train_class.py --eval` **%3.95** verdi. Sebep veri değil, hattın kendisiydi:
`edge` fixture'ındaki kasıtlı uç satır (w=10.000.000 px, minDim=0.001 → oran 1e9) ham
standardizasyonu patlatıyordu: **bir özelliğin std'si 8×10⁷**, 145 özelliğin std'si ~0, model
`best epoch 0`da erken durup **W ve b'yi tamamen sıfır** bırakıyordu → tüm tahminler tek sınıfa
(CanvasGroup) çöküyordu. Düzeltmeler (hepsi `tools/train_class.py`):
- **winsor kırpma** (%2/%98) → uç satır std'yi patlatamıyor; en büyük std artık **1.54**;
- **`clipZ = ±8`** — eğitimde ve gömülü tahminde AYNI adım (`model.json → clipZ`, JS/Lua ikizleri
  de uygular) → görülmemiş uç tasarım logitleri patlatamıyor;
- **yumuşatılmış sınıf ağırlığı** (karekök + tavan 3.0): 1 örnekli sınıf 11× ağırlık alıp kaybı
  domine etmiyordu; artık görünür ama belirleyici değil;
- **lr 1.2→0.4, l2 1e-4→0.08** (export-LOO taramasıyla seçildi: 18 kombinasyon).

**Dürüst metrikler (yeni kapı):** `--eval` artık yalnızca eğitim setine bakmıyor — **eğitim
seti ≥ %85/%95 + export-LOO ≥ %55** arıyor. Sonuç:

```
eğitim seti : top-1 95.39% · top-3 97.37%   (öncülsüz de aynı: ayrışma öncülden gelmiyor)
export-LOO  : ortalama top-1 67.37% · en kötü 42.86%
   AnimeHUD 82.98 · CartoonMenu 100.00 · Edge 44.44 · StudIcon 62.50
   StudMarket 86.67 · StudUnnamed 42.86 · WidgetKit 52.17  (top-3 çoğunda %100)
129 satırlık sürüm: eğitim %100 (ezber) · LOO %73.87 → kapsama büyüdükçe LOO düşüyor:
bu BEKLENEN ve DÜRÜST yön; gerçek kullanıcı verisiyle yükselecek.
```

**Regresyon kapısı:** `verify_model.py` artık çöküş imzasını arıyor — W satırı tamamen sıfır mı,
b hepsi sıfır mı, std > 1e6 mı, `clipZ` var mı (yoksa model kabul edilmez).

**Yapılacak (kalan):** (a) senin **gerçek export'ların** → `ingest.py --append` → yeniden eğitim
(gerçek veri eklendikçe LOO yukarı çıkmalı); (b) **UIGridLayout / Item / DROP / MERGE** örnekleri —
**§1'e bağlı, bilinçli olarak ertelendi:** bu 4 sınıfı öğretmene eklemek Lua ≡ Python paritesini
bozar (`verify_teacher.py` düşer) ve v9 modunda eklenti davranışını değiştirir. Doğru sıra: §1'de
asistan modu (`ei` var) kapısının arkasına `decideClass` yollarını koymak (DROP = süs grubu at,
MERGE = şeffaf sarmalayıcıyı ebeveynle birleştir, UIGridLayout/Item = ızgara kabı + eş boyutlu
slot), sonra bu yolları besleyen fixture'ları eklemek. Model, hiçbir kod yolunun üretemediği
sınıfı öğrenemez;
(c) eşiklerin (`style-rules.json`, hâlâ "proposed") gerçek etiketlerle doğrulanması;
(d) `eval.py --strict` ile kabul kapısının gerçek veride koşulması.

## 7. Belgeler ve küçük tutarsızlıklar (temizlik)

**2026-10-08: KARARLAR.md §4'teki bekleyen düzenlemeler + bu tablo TAMAMLANDI** (aşağıda).

| # | Sorun | Nerede | Durum (2026-10-08) |
|---|---|---|---|
| 1 | "≈165 özellik" yazıyor; gerçek **379** | `PLAN.md` satır 212 | ✅ 379 özellik / 14 sınıf olarak güncellendi |
| 2 | Yol tahmini `doc.ei.assistant.predictions["0.2.5"]` ↔ gerçek item düzeyi `it.ei` | `PLAN.md §2.1` | ✅ §2.1 gerçek şemaya çevrildi: `item.ei` **ölçüm** kanalı; JSON'da tahmin YOK (Studio çalışma zamanında hesaplar) |
| 3 | `it.ei` şema ayrımı (gerçek Figma bilgisi ↔ model çıktısı) ve ~12 ölü alan | `code.js` | 🟡 şema ayrımı PLAN §2.1'de belgelendi; **ölü-alan temizliği bilerek ertelendi** (v9 bayt-birebir kuralına dokunma riski — ayrı iş) |
| 4 | Roadmap etiketleri (A5 tamam, A9/A10 adları) güncel değil | `PLAN.md §10` | ✅ "Durum güncellemesi (2026-10-08)" tablosu eklendi (A0–A5 ✅, A6–A8 ⏳, A10 🟡, yeni A11 ✅ / A12 ⏳ / A13 ⏳) |
| 5 | Aktif öğrenme kuyruğu artık **geliştiriciye** bağlı (kullanıcıya değil) | `OGRENME-MOTORU.md` §7/§9 | ✅ KARARLAR §4 kararı olarak eklendi (ayrıca §4 I1: attribution panellerde gösterilmez) |
| 6 | `RESPONSIVE_SCRIPT` PURE bloğun dışında; Luau→Lua dönüşümü **yalnız test** | plugin | ✅ `.lua` başlığına not eklendi; `.rbxmx` yeniden üretildi → `verify_plugin_v9` + `verify_real_run --limit 2` GEÇTİ |
| 7 | `ui.html` içinde eski Luau/RBXMX üretim yolu duruyor (yeni akış mellett) | `ui.html` | ✅ "(eski yol)" etiketi + `title` uyarısı eklendi (OKU-BENI.md zaten yönlendiriyor) |
| 8 | `SORULAR.md` E3 (gizlilik) "kırpma yok" olarak güncellenmedi | `SORULAR.md` | ✅ E3 cevabı eklendi: **kırpma yok** (KARARLAR §2.2; `ARASTIRMA.md` Bölüm E de güncellendi) |

Aynı temizlik dalgasında KARARLAR.md §4'teki diğer bekleyen düzenlemeler de uygulandı:
`PLAN.md` §6.1/§6.2 (kullanıcıya-düzelt akışı kaldırıldı, tek-LocalScript kararı, gerçek
modül yapısı), `SORULAR-LUAU.md` L1/L2/L3/L5/L9 karar notları (TweenService · spring iptal ·
tek LocalScript · hover otomatik · 4 paket).

**Bu turun özeti (2026-10-08, öğleden sonra):**

- `verify_model` kapısı **güncel modelde yeniden koştu → GEÇTİ**: 4 642 satır, 14 sınıf, 379 boyut;
  yeniden eğitim **84 473 bayt birebir aynı**; kabul top-1 %99.70 / top-3 %99.89.
- Tüm kapılar yeşil: `verify_style/extract/runtime/teacher/learn/merge/predict/plugin_v9/
  real_dataset/generalization/real_run` + `build_rbxmx --check`.
- **Stil kalibrasyon aracı hazır**: `tools/stil_rapor.py` + `tools/stil_dump.cjs`.
  Ölçüm modu + etiketli mod (uyuşma, karışıklık matrisi, 3 888 kombinasyonluk anime/cartoon/
  margin eşik taraması; stud kuralına dokunmaz). Etiket gelince tek komut:
  `python3 tools/stil_rapor.py --etiketler ../designs-export/_rapor/stil-etiketleri.json`
  → rapor: `designs-export/_rapor/stil-rapor.md` (şu an ölçüm modu tablosu).
- Node tuzağı not: araç `.cjs` uzantılı — Node'un ESM tespiti yorumlardaki `export'`
  gibi sözcüklerle `.js` dosyasını ESM sanabiliyor; `.cjs` her zaman CommonJS.

---

## 8. Önerilen sıra (bağımlılıklara göre)

1. **§1 Eklenti entegrasyonu (A4b)** + `verify_plugin_v9.py` kapısı → ilk uçtan uca çalışan sürüm
2. **§2 Panel öğrenmesi** (seçim kaydı + paket indirme) → senin seçimlerin veriye dönüşmeye başlar
3. **§4 Animasyon** (seçici + TweenService üretici) → ürünün ikinci büyük vaadi
4. **§5 merge_learn.py** + **§6 gerçek veri turu** → model gerçekten öğrenir
5. **§3 eğitim dosyası** + **§7 belge temizliği** → yayın/paylaşım hazırlığı

**Not (bilinçli kapalı):** piksel kanıtı kanalı (`getBytesAsync` → canvas → kenar sürekliliği +
özilinti) gerekçesiyle kapalı (ARASTIRMA §C1c §7); ölçülmüş döşeme hücresi yetmezse açılacak.
Ayrıca `figma-plugin-klasik/` kapsam dışı (karar 10) ve Luau→Lua dönüşümü yalnızca test amaçlı.
