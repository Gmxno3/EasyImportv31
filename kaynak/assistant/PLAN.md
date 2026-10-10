# EasyImport Asistan Modeli — Sistem Planı (v0.1)

> **Durum:** TASLAK / onay bekliyor. Bu belge "önce sistemi planlayalım, sonra yapalım" kararının çıktısıdır.
> Onay sonrası A1 adımından itibaren kod üretilecek. Bu belge tek doğruluk kaynağıdır (single source of truth).

---

## 0. Ne yapıyoruz, ne yapmıyoruz

**Yapıyoruz — TAM OLARAK İKİ İŞ:**
1. **Sınıf ataması:** her katman → `ImageLabel` / `ImageButton` / `TextLabel` / `TextButton` /
   `TextBox` / `Frame` / `ScrollingFrame` / `CanvasGroup` / `ViewportFrame` / `VideoFrame` / ...
   Kanıt: isim + boyut + **kalınlık (kontur)** + uzunluk/yükseklik + konum + efektler + renk +
   içerik (metin/görsel) + hiyerarşi + **aynı GUI içindeki diğer ölçülerle karşılaştırma**.
2. **Animasyon ataması:** her öğe → `anim-library.json`'dan bir animasyon (+ beğenilmezse 5 alternatif).
   Buna **Figma'daki efekt image'lerinin** (glow / ray / sparkle / shine / vignette / noise / toz)
   tespiti ve bunlara döngü animasyonu atanması da dâhil.

Bunları yapabilmek için: Figma'dan çıkan UI verisinden **öğrenen**, ağırlıkları olan, dosyaya
yazılabilen bir **model**; **hem Roblox Studio (saf Lua/Luau) hem Figma (JS)** tarafında çalışan
bir çalışma zamanı; eğitim **senin kendi JSON'larınla** (sunucu yok, telemetri yok, internet yok).

**Yapmıyoruz:**
- Sohbet / doğal dil / LLM benzeri üretken yapay zekâ. Asistan **konuşmaz**, **karar verir**.
- Bulut, hesap, OAuth, Vercel/Supabase. (README'deki "cloud yok" ilkesi korunur.)
- Kullanıcılardan veri toplama. Kötü niyetli/bozuk etiket riski bu şekilde sıfırlanır.
- Mevcut kural motorunu silmek. Kurallar **öğretmen + güvenlik ağı** olarak kalır.
- ⛔ **Desteklenmeyen Figma efektlerini Roblox'ta taklit etmek.** (blur, inner shadow, metin
  gölgesi, blend mode, dash, noise/texture/glass/shader.) Bunların import tarafı zaten çözülmüş
  (PNG'ye render). Asistan bunları **yalnızca sınıf/animasyon kararı için özellik olarak okur**;
  Roblox tarafında karşılık üretmeye çalışmaz. Bkz. `ARASTIRMA.md` Bölüm B3 → "bilgi amaçlı, çözüm değil".

**Neden "AI'den daha zeki":** LLM bir metni tahmin eder; bu model **senin tasarım dilinin istatistiğini**
bilir. 300 katmanlı bir UI'da tutarlı, ölçülebilir, deterministik ve **açıklanabilir** ("bu katman
`ImageButton` çünkü 96×96 boyut kümesinde, %82 örnekte buton, adında icon benzeri token var") karar verir.

---

## 1. Büyük resim

```
   SENİN VERİN                    EĞİTİM (Python, offline)              ÇALIŞMA ZAMANI
┌──────────────────┐        ┌───────────────────────────────┐     ┌──────────────────────────┐
│ Figma export     │        │ tools/ingest.py               │     │  figma-plugin-*/         │
│   EI_*.json      │───────▶│   JSON → özellik vektörü      │     │    ei-assistant.js  ─┐   │
│ (format v10)     │        │   + öğretmen etiketi (kurallar)│    │                      │   │
├──────────────────┤        ├───────────────────────────────┤     │  roblox-studio-plugin/  │  │
│ Etiket düzeltme  │───────▶│ tools/label_tool.py           │     │    EI_ModelData.lua  ─┤  │
│   labels/*.jsonl │        │   senin elle düzeltmelerin    │     │    EIAssistant.lua   ─┤  │
├──────────────────┤        ├───────────────────────────────┤     └──────────────────────┼───┘
│ Animasyon        │───────▶│ tools/train_{class,size,anim} │                            │
│   kullanımları   │        │   SGD / k-means / MF          │         model.json         │
└──────────────────┘        ├───────────────────────────────┤◀───────────────┐           │
                            │ tools/export_model.py         │                │           │
                            │   → model.json                │        tools/verify_runtime.py
                            ├───────────────────────────────┤        (3 dil aynı sonucu mu?)
                            │ tools/eval.py                 │                │           │
                            │   doğruluk / confusion / güven│                ▼           ▼
                            └───────────────────────────────┘        EI_ModelData.lua
                                                                     ei-model.js
                                        (build adımı, elle çalıştırılır — Studio'ya gömülür)
```

**Kritik kural:** Model eğitildikten sonra `export_model.py` üç çıktı üretir:
`model.json` (ana), `EI_ModelData.lua` (Luau table literal, plugin içine gömülür), `ei-model.js`.
Böylece Studio tarafında `HttpService` / `HttpEnabled` / internet **gerekmez**.

---

## 2. Veri sözleşmesi

### 2.1 `EILExport` — Figma çıktısı (mevcut `wispfree` v9 → **v10**)

Mevcut alanlar korunur. Yeni alanlar **opsiyoneldir**; eski Studio sürümü v9 JSON'u okumaya devam eder.

```jsonc
{
  "format": "wispfree",
  "version": 10,                     // 9 → 10
  "name": "MainMenu",
  "width": 1920, "height": 1080,     // tasarım tuvali (ölçek normalizasyonu için ŞART)
  "root": { /* ... */ },

  // YENİ v10 — ÖLÇÜM kanalı. Bu dosyada TAHMİN YOKTUR (güncellendi 2026-10-08; ilk taslakta
  // ei.assistant.predictions[path] + ei.corrections vardı — gerçek şema bu, bkz. code.js imageMetaOf):
  // Her öğe (item) için, yalnizca görsel geometrisi ÖLÇÜLDÜYSE yazilir; ölçüm yoksa alan hiç oluşmaz.
  "ei": { "imageW": 420, "imageH": 420, "sf": 0.126, "tileW": 53, "tileH": 53,
          "repX": 14, "repY": 1, "blendMode": "OVERLAY" }
  // Sözleşme: kökte/toplamda "ei" YOKSA bu bir v9 export'tur → asistan kapalıdır,
  // çiktü v9 ile BİREBİR aynıdir (kapı: assistant/tools/verify_plugin_v9.py).
  // Tahminler (cls/conf/top3) Figma'da üretilmez — Studio eklentisi çalışma zamaninda
  // gömülü EIModel ile hesaplar (ei-model.js ≡ EIModel.lua; kapı: verify_predict.py).
}
```

### 2.2 `EILSample` — eğitim örneği (JSONL, satır = 1 katman)

```jsonc
{"path":"0.2.5","export":"MainMenu","feat":{ ...adlandırılmış özellikler... },
 "label":{"cls":"ImageButton","thickness":2,"radius":12,"anim":"pop_in_scale"},
 "src":"manual"}   // "manual" | "rule-teacher" | "user-correction"
```

`feat` **adlandırılmış** sözlük tutulur (okunabilirlik için); eğitim sırasında spec'teki sabit
sıraya göre vektöre çevrilir. Böylece özellik eklendiğinde eski veri bozulmaz.

### 2.3 `EILModel` — model dosyası

```jsonc
{
  "format": "ei-model", "version": 1,
  "featureSpec": "ei-feat-1",
  "models": {
    "class":  { "type":"softmax", "classes":[...], "W":[[...]], "b":[...], "norm":{...} },
    "size":   { "type":"cluster-profile", "clusters":[...], "thickness":{...}, "radius":{...} },
    "anim":   { "type":"mf+lr", "anims":[...], "V":[[...]], "W":[[...]], "b":[...] }
  },
  "meta": { "trainedAt":"...", "trainAcc":0.91, "valAcc":0.88, "samples":12480, "checksum":"sha256:..." }
}
```

---

## 3. Özellik Çıkarıcı (Feature Spec) — `assistant/spec/features.json`

**Tek spec, üç implementasyon:** `js/ei-features.js`, `lua/EIFeatures.lua`, `python/features.py`.
Aynı girdi → üç dilde de **aynı vektör** (tolerans 1e-6). Bunu `tools/verify_runtime.py` zorunlu tutar.
Bu test geçmeden hiçbir model yayınlanmaz.

Her özellik: `{ name, group, kind, norm }` — `kind`: `num` | `bool` | `onehot` | `bucket`.

### A. Ad özellikleri (bag-of-tokens, ~60)
- Token sözlüğü (spec'te sabit liste, sıralı): `button, btn, buton, icon, close, exit, play, start,
  settings, option, menu, back, next, prev, bar, hp, health, mana, energy, xp, level, coin, gem,
  gold, shop, inventory, bag, slot, item, card, panel, bg, background, overlay, modal, popup,
  dialog, title, header, label, text, desc, value, count, timer, progress, fill, loader, slider,
  toggle, check, tab, nav, footer, top, bottom, left, right, center, avatar, profile, badge,
  notif, tooltip, divider, shadow, glow, frame, container, wrapper, content, list, grid, scroll`
- Ek bayraklar: `name_hasUnderscoreTag`, `name_wordCount`, `name_charLen/32`, `name_hasDigit`,
  `name_isCamelCase`, `name_allUpper`, `name_allLower`, `name_hasNonAscii`,
  `name_startsWithHash` (`#` = görsel), `name_startsWithImg` (`img:`).

### B. Geometri — **mutlak** (~14)
- `w`, `h` (tasarım tuvaline göre normalize: `w/docW`), `area = w*h/(docW*docH)`,
  `logArea = clamp(log10(area+1e-6), -6, 0)`, `aspect = w/h` (clamp 0.05–20, log),
  `minDim/docMin`, `maxDim/docMax`, `cx = (x + w/2)/docW`, `cy = (y + h/2)/docH`,
  `distToCenter`, `edgeTop/edgeBottom/edgeLeft/edgeRight` (0–1 yakınlık).

### C. Geometri — **bağlamsal / karşılaştırmalı** ← *senin "bütün sizeleri al, farkları bul" isteğin* (~22)
Bu grup, **aynı GUI içindeki tüm öğeler toplandıktan sonra** iki geçişte hesaplanır
(1. geçiş: tüm öğelerin w/h'si toplanır → kümeler; 2. geçiş: her öğe kendi kümesine göre özellik alır).
- Boyut kümesi (log-log uzayda 1B kümeleme, tolerans %6):
  `cluster_id_rank` (en sık küme = 0), `cluster_count/n`, `cluster_isSingleton`,
  `cluster_w`, `cluster_h`, `cluster_aspect`.
- Göreli: `w / parentW`, `h / parentH`, `area / parentArea`, `w / siblingMeanW`, `h / siblingMeanH`,
  `w / maxW_in_doc`, `h / maxH_in_doc`, `sizeRank_in_doc` (0–1), `sizePercentile_in_doc`.
- Komşuluk: `nSiblingsSameSize`, `siblingSizeVariance`, `isAlignedWithSiblingX`,
  `isAlignedWithSiblingY`, `depth`, `depth/docMaxDepth`.

### D. Görsel / dolgu (~16)
- `hasImageFill`, `imageAspectMatchesBox`, `isVectorKind`, `nFills`, `hasSolidFill`, `hasGradient`,
  `hasImagePaint`, `fillOpacity`, `fillBrightness` (0–1), `fillSaturation`, `isTransparentFill`,
  `hasStroke`, `strokeWeight/docMin` (log), `strokeAlign_*` (one-hot 3), `strokeIsGradient`,
  `nShadows`, `shadowBlur/docMin`.

### E. Köşe / kalınlık (~8) ← *"kalınlık" isteğin*
- `cornerRadius/docMin` (log), `radius_isFull` (aspect≈1 ve r ≥ minDim/2), `radius_isZero`,
  `radius/topLeft` vb. karışık köşe bayrağı, `hasStrokeAndRadius`, `borderRatio = 2*strokeW/minDim`,
  `isPill` (pill şekil: h küçük, r = h/2), `isCircle`.

### F. Metin (~15) — sadece `kind == "text"` ise anlamlı, değilse 0
- `isText`, `textLen/64`, `textWordCount`, `textHasDigit`, `textIsNumeric`, `textAllUpper`,
  `textHasPunctuation`, `fontSize/docH * 100` (log), `fontWeight/900`, `isItalic`,
  `textAlign_*` (one-hot 3), `vAlign_*` (one-hot 3), `wrapEnabled`, `nLines`, `textFillBrightness`.

### G. Ağaç / düzen (~14)
- `nChildren`, `hasChildren`, `nTextChildren`, `nImageChildren`, `nFrameChildren`,
  `childSizeVariance`, `isLeaf`, `isRoot`, `siblingIndex/nSiblings`, `isFirstChild`, `isLastChild`,
  `clipsContent`, `layoutMode_*` (one-hot: none/horizontal/vertical/grid), `layoutGap/docMin`,
  `layoutPaddingAvg/docMin`, `hasScroll`.

### H. Üst/alt bağlam (ebeveyn sınıfı tahmini, 2 geçiş) (~12)
Ebeveynin (tahmin edilen) sınıfı one-hot + ebeveynin boyut kümesi rank'ı:
ebeveyn `Frame` ise içindeki şey `TextLabel` olmaya yatkındır; ebeveyn `ScrollingFrame` ise
çocuklar genelde `ImageButton`/`TextButton`dır. Bu, modelin "hiyerarşi okumasını" sağlar.

**Toplam ≈ 165 özellik.** 12 sınıf × 165 = 1980 çarpım → Lua'da bir katman için ~0.1 ms.
300 katmanlı bir UI = ~30 ms. Sorun değil.

---

## 4. Modeller

### M1 — Sınıf Sınıflandırıcısı (`class`)

**Tip:** Multiclass **softmax regresyon** (lojistik regresyon) + opsiyonel 1 gizli katmanlı MLP
(64 ReLU). Önce softmax ile başlanır; doğruluk plato yaparsa MLP açılır. Neden: ağırlıklar
şeffaf, Lua'da çalıştırması 20 satır, hata ayıklaması kolay.

- **Sınıflar (12 + 2 yapısal):**
  `Frame, ImageLabel, ImageButton, TextLabel, TextButton, TextBox, ScrollingFrame, CanvasGroup,
  ViewportFrame, VideoFrame, UIGridLayout-Item(struct?), DROP, MERGE`
  (`DROP` = süs/atılabilir, `MERGE` = ebeveynle birleştir — mevcut `isDecorGroup` / `isPlainWrapper`
  mantığının öğrenilmiş hâli.)
- **Eğitim:** Adam, lr 0.05, L2 1e-4, class weights (dengesizlik: `ImageButton` az, `Frame` çok),
  early stopping (val loss), 5-fold CV.
- **Kalibrasyon:** güven skoru güvenilir olmalı → Platt scaling / temperature scaling.
  `conf` eşiği: **≥ 0.70 model**, **< 0.70 kural motoru** (güvenli fallback).
- **Açık etiket her zaman kazanır:** `_ImageButton`, `_TextLabel`, `#`/`img:` gibi **açık kullanıcı
  etiketleri modelin üstünde** yer alır. Model sadece **etiketsiz / isimsiz** katmanlarda konuşur.
  *(Senin "isimleri girilmemiş imagelabel filan" senaryosu tam olarak bu.)*
- **Çıktı:** `{ cls, conf, top3, source }`.

**Kabul kriteri:** Senin örnek JSON'larında (etiketsiz katmanlar üzerinde) **≥ %85 top-1 doğruluk**
ve **≥ %95 top-3**, mevcut kural motorunun doğruluğunu geçmek.

### M2 — Boyut / Kalınlık Modeli (`size`) ← *senin asıl vurgun*

Üç alt parça:

**(a) Ölçek sınıfı çıkarımı.** Tasarım tuvali `docW × docH` → öğrenilmiş ölçek sınıfı
(`desktop-1080`, `desktop-720`, `mobile-750x1334`, `square-1080`, ...). Tüm göreli özellikler
bu sınıfa göre normalize edilir; böylece 1920×1080'de eğitilmiş model 750×1334 tasarımda da çalışır.

**(b) Boyut kümesi → rol profili.** Her export'ta log-log uzayında boyut kümeleri çıkarılır
(Aşama C). Eğitim verisinde her küme için **"bu küme hangi sınıflardan oluşuyor"** histogramı
tutulur:
```
cluster_profile[scaleClass][round(aspect,1)][sizeBucket] → { Frame: 12, ImageButton: 88, ... }
```
Yeni bir GUI geldiğinde: öğenin boyut kümesi + aspect + göreli sırası → **küme düzeyinde önsel (prior)**
dağılım. Bu, "aynı boyuttaki 8 öğe varsa ve bunlar eğitimde %90 buton çıktıysa, hepsi butondur"
demektir. **Tek tek bakmak yerine bütünün içindeki yerine bakmak** — istediğin davranış.

**(c) Kalınlık & köşe tamamlayıcı.**
`thickness[cls][sizeBucket]` ve `radius[cls][sizeBucket]` dağılımları öğrenilir (medyan + IQR).
Kullanım:
- JSON'da değer yoksa / 0 ise → **öner** (ve UI'da "öneri" olarak göster, otomatik zorlama yok).
- Değer varsa ama sınıf profilinden **>3 IQR sapıyorsa** → "şüpheli" işareti (ör. 2 px kalınlık
  1080p'de 400 px butonda görülmemiş) → kullanıcıya sor.
- **Kalınlık tutarlılığı:** aynı boyut kümesindeki öğelerin kalınlıkları eğitimde genelde eşit
  çıkıyorsa, küme içinde **tek bir kalınlığa** normalize etmeyi önerir (tasarım tutarlılığı).

### M3 — Animasyon Modeli (`anim`) ← *2. özellik*

**Kütüphane:** `assistant/anim/anim-library.json` — senin ekleyeceğin 100'lerce animasyon.
Her kayıt:
```jsonc
{
  "id": "pop_in_scale",
  "name": "Zıplayarak Giriş",
  "category": "giris",                 // giris | cikis | hover | basma | dongu | dikkat | gecis
  "tracks": [
    { "target":"UIScale", "prop":"Scale", "from":[0.6,0.6], "to":[1,1],
      "dur":0.35, "delay":0, "ease":"Back", "dir":"Out", "repeat":0, "reverses":false },
    { "target":"self", "prop":"GroupTransparency", "from":1, "to":0, "dur":0.25, "ease":"Quad", "dir":"Out" }
  ],
  "fit": { "classes":["ImageButton","TextButton","Frame"], "roles":["primary","close"],
           "minArea":0.0005, "maxArea":0.9, "categories":["ui"] },
  "quality": { "detail":3, "variety":2, "beauty":4 },   // senin 1-5 notların
  "usageCount": 0
}
```

**Öneri motoru (3 katman, sırayla uygulanır):**
1. **Uygunluk filtresi (`fit`):** sınıf, rol, alan aralığı, kategori. Uymayanlar elenir.
2. **Öğrenilmiş skor:** öğe özellik vektörü (M1 ile aynı spec) × animasyon embedding → skor.
   Önce **matris çarpanlarına ayırma (MF)** hafif versiyonu: `score(item, anim) = <W·feat, V_anim> + b_anim`.
   Eğitim verisi = **senin örnek kullanımların** (hangi GUI'de hangi öğeye hangi animasyon)
   + sonradan son kullanıcının seçimleri (yerel, cihazında kalır).
3. **Bağlamsal tutarlılık + çeşitlilik (MMR):** aynı GUI içinde
   - çok sayıda öğe aynı animasyonu almasın (çeşitlilik cezası),
   - aynı boyut kümesindeki öğeler **aynı** animasyonu alsın (tutarlılık ödülü),
   - kategori dağılımı dengeli olsun (ör. 5 giriş + 2 döngü + 1 dikkat).

**"Beğenmedim" döngüsü:** Kullanıcı öneriyi beğenmezse → buton → `top-K` listesi
K=5, MMR ile **kategori çeşitliliği zorunlu** (en az 3 farklı kategori). Seçilen her alternatif
`usageCount++` ve **negatif sinyal** olarak kaydedilir (eski önerinin skoru düşer).

**Çıktı:** her öğe için `{ anim, conf, alts:[4] }` — A7 (animasyon seçici + üretici) henüz
üretilmiyor; üretildiğinde panel/Studio tarafında oluşacak. *(güncellendi 2026-10-08: tahminler
JSON'a yazılmaz — Figma tarafı yalnizca `ei` ölçümü yazar, bkz. §2.1)*

**Roblox üretimi (karar — KARARLAR.md madde 5):** `EI_AnimController` + `EI_AnimData` çifti
**yapılmayacak**. Her UI için **tek üretilmiş LocalScript** içinde düz Luau tween kodu;
hover/basma bağlamaları da aynı scripttedir:
```lua
-- tek üretilmiş LocalScript (modül çifti YOK)
local function Play(inst, animId)        -- TweenService tabanlı, iptal edilebilir
  local tw = TweenService:Create(inst, TweenInfo.new(0.25, Enum.EasingStyle.Back), {Size = ...})
  tw:Play()
end
```
Tween'ler `TweenService:Create(..., TweenInfo.new(dur, Enum.EasingStyle.Back, Enum.EasingDirection.Out))`
ile kurulur; `UIScale` yoksa otomatik eklenir. **Sunucu tarafı kod üretilmez** (LocalScript only).

---

## 5. Eğitim hattı (Python, offline)

```
assistant/
├── PLAN.md                     ← bu belge
├── spec/
│   └── features.json           ← TEK özellik spec'i (sürümlü: ei-feat-1)
├── runtime/
│   ├── js/ei-features.js       ← Figma tarafı özellik çıkarıcı
│   ├── js/ei-assistant.js      ← Figma tarafı çalışma zamanı (predict / suggestAnim)
│   ├── lua/EIFeatures.lua      ← Studio tarafı özellik çıkarıcı
│   ├── lua/EIAssistant.lua     ← Studio tarafı çalışma zamanı
│   └── lua/EIAnim.lua          ← anim → Luau kodu üretici
├── model/
│   ├── model.json              ← ana model (eğitim çıktısı)
│   ├── EI_ModelData.lua        ← üretilmiş Luau table (plugin'e gömülür)
│   └── ei-model.js             ← üretilmiş JS
├── anim/
│   └── anim-library.json
├── datasets/
│   ├── raw/                    ← senin Figma export JSON'ların (EI_*.json)   [gitignore: isteğe bağlı]
│   ├── labels/                 ← *.jsonl düzeltmeler
│   └── anim-usage/             ← *.jsonl animasyon kullanım örnekleri
└── tools/
    ├── ingest.py               ← raw JSON → samples.jsonl (öğretmen etiketli)
    ├── label_tool.py           ← CLI: "bu katman ne olmalı?" → etiketle
    ├── train_class.py
    ├── train_size.py
    ├── train_anim.py
    ├── export_model.py         ← model.json + EI_ModelData.lua + ei-model.js
    ├── eval.py                 ← doğruluk, confusion matrix, güven eğrisi
    └── verify_runtime.py       ← Python/JS/Lua aynı sonucu veriyor mu? (ZORUNLU)
```

**Komutlar (hedef akış):**
```bash
python tools/ingest.py    datasets/raw/*.json        -o datasets/labels/bootstrap.jsonl
python tools/label_tool.py datasets/labels/bootstrap.jsonl      # sen düzeltirsin
python tools/train_class.py  -o model/model.json --eval
python tools/train_size.py   -o model/model.json --append
python tools/train_anim.py   -o model/model.json --append
python tools/export_model.py model/model.json                   # .lua + .js üretir
python tools/verify_runtime.py                                  # geçmezse YAYIN YOK
```

**Bootstrap stratejisi (veri yokken nasıl başlıyoruz):**
1. Mevcut **kural motoru** (Figma `code.js` + Studio `parseLayerTags`) Python'a taşınır
   (`tools/rules_teacher.py`) → senin ham JSON'ların otomatik etiketlenir.
2. Bu etiketler **`src: "rule-teacher"`** işaretli başlangıç verisi olur.
3. `label_tool.py` ile **sen** düzeltirsin → `src: "manual"`.
4. Elle etiketlenmiş veri çoğaldıkça öğretmen ağırlığı azalır (`sample_weight`: manual 1.0,
   rule-teacher 0.35, user-correction 0.8).
5. Model, kuralların **yetişemediği** yerlerde (etiketsiz katmanlar) kuralları geçer.

---

## 6. Çalışma zamanı ve entegrasyon

### 6.1 Figma (`figma-plugin-all-in-one/`, sonra `figma-plugin-klasik/`)

*(güncellendi 2026-10-08 — KARARLAR.md §4 kararları uygulandı)*

- `code.js` içinde export sirasinda: yalnizca **`item.ei` ölçümü** yazilir (`imageMetaOf` —
  görsel geometrisi; ölçüm yoksa alan hiç oluşmaz). **Tahmin üretilmez** — tahminler Studio
  eklentisinde çalışma zamaninda gömülü EIModel ile hesaplanir (bkz. §2.1).
- `ui.html` → **"Asistan"** sekmesi (planlandi, A7/A8 ile):
  - ~~Güven skoru düşük (<0.70) katmanlar listesi → hızlı düzeltme → `ei.corrections`~~
    **KALDIRILDI** (karar): kullanıcıya düzelttiren akış yok; yerine **otomatik öneri +
    alternatif üretimi** (A8).
  - **Animasyon seçici:** önerilen animasyon + 4 alternatif, kategori rozetleri, önizleme metni.
  - "Eğitim verisi olarak indir" butonu → **kırpma yok** (karar §2.2: hiçbir alan kırpılmaz);
    yerel öğrenme cihazda (`figma.clientStorage`), toplu paket indirme **isteğe bağlı**
    (karar 12: sunucu yok, otomatik gönderim yok).
- **Ayar:** Asistan AÇIK/KAPALI (kapalıysa davranış v9 ile birebir aynı).

### 6.2 Roblox Studio (`roblox-studio-plugin/EasyImportStudioPlugin.lua`)
- `EI_ModelData.lua` ve `EIAssistant.lua`, `.rbxmx` paketine **ayrı ModuleScript'ler** olarak eklenir
  (mevcut tek dosya yapısı korunur, sadece paket genişler).
- `buildEasyImportHierarchy` içinde karar sırası **değişmez, genişler**:
  1. **Açık kullanıcı etiketi** (`_ImageButton`, `#`, `img:`) → kazanır (model devre dışı).
  2. JSON'da `ei.predictions[path].cls` ve `conf ≥ 0.70` → **model** uygulanır.
  3. Aksi hâlde → **mevcut kural motoru** (v5 davranışı korunur).
- **Boyut/kalınlık paneli:** Eksik kalınlık/radius önerileri "Öneri" olarak gösterilir, tek tıkla uygula.
- **Animasyon:** JSON'daki `anim` alanı → `EI_AnimData` + `EI_AnimController` üretimi.
- **Geri bildirim (lokal):** Panelde "Asistan'a öğret" → seçili Instance'ın doğru sınıfı kaydedilir.
  Dosyaya yazma yetkisi olmadığı için çıktı: **Attributes** + **Copy to clipboard** butonu
  (`SetClipboard` plugin API yoksa metin kutusu). Son kullanıcı dilerse sana gönderir;
  **otomatik gönderim yok**.

### 6.3 Güvenlik / kötüye kullanım (senin endişen)
| Risk | Önlem |
|---|---|
| Kullanıcı bozuk/yanlış etiket gönderir | Telemetri yok; eğitim verisi **yalnızca senin JSON'ların**. Gelen dosyalar `ingest.py`'de şema doğrulamasından geçer. |
| Model bozuk / eksik / sürüm uyuşmazlığı | `featureSpec` sürüm kontrolü; uyuşmazsa model devre dışı, kurallar çalışır. `checksum` doğrulaması. |
| Aşırı güvenli yanlış tahmin | Eşik 0.70 + temperature calibration + düştüğünde kurala fallback + UI'da gösterim. |
| Sonsuz döngü / performans | Özellik çıkarımı 2 geçişle sınırlı, kümeleme O(n log n), toplam bütçe 50 ms (aşarsa model atlanır). |
| Gizlilik | Hiçbir veri cihazdan çıkmaz (eğitim hariç: sen kendi dosyanı kopyalarsın). |

---

## 7. Yol haritası

| Aşama | İş | Çıktı | Kabul kriteri |
|---|---|---|---|
| **A0** | Bu plan + derin araştırma + D/Y soruları | `PLAN.md`, `ARASTIRMA.md`, `SORULAR.md` | ✅ senin onayın |
| **A1** | Özellik spec + 3 dil implementasyonu + determinizm testi | `spec/features.json`, `runtime/**`, `tools/verify_runtime.py` | Aynı 10 örnek düğümde Python/JS/Lua vektörleri 1e-6 içinde aynı |
| **A2** | Kural motorunu öğretmene çevir + ingest | `tools/rules_teacher.py`, `tools/ingest.py` | Ham JSON → JSONL, öğretmen etiketleri mevcut Studio kararlarıyla %100 uyumlu |
| **A3** | M1 sınıf modeli | `train_class.py`, `eval.py`, `model.json` | Etiketsiz katmanlarda ≥ %85 top-1, kural motorunu geçer |
| **A4** | Studio + Figma entegrasyonu (**sınıf tahmini**) | güncel `code.js` / `ui.html` / `*.lua` / `*.rbxmx` | v9 JSON ile davranış **değişmez**; v10'da model çalışır |
| **A5** | **Animasyon kütüphanesi — 108 animasyon** ✅ TAMAM | `anim/anim-library.json`, `anim/README.md` | 108 animasyon, şema doğrulaması temiz |
| **A6** | FX tespiti (Figma efekt image'i) + eşleştirme kuralları | `runtime/**/fxdetect.*` | glow/ray/sparkle/shine katmanları doğru tespit edilir |
| **A7** | Animasyon seçici UI (Figma paneli) + Luau üretici | `ui.html` sekmesi, `EIAnim.lua` | Önerilen animasyon senin seçiminle %60+ örtüşür; Luau Studio'da hatasız |
| **A8** | "Beğenmedim" döngüsü, top-K + çeşitlilik (MMR) | UI + skor güncellemesi | 5 alternatif en az 3 farklı kategoriden |
| **A9** | M2 boyut/kalınlık modeli + küme profilleri | `train_size.py` | (opsiyonel — sınıf modeli yeterli gelirse atlanır) |
| **A10** | M0 stil modeli (cartoon/stud/anime) | `train_style.py` | Stil tahmini senin etiketlerinle %80+ uyumlu |

**Sıra değişikliği notu:** Animasyon (A5–A8), boyut modelinden (A9) **önce** geliyor — çünkü
Asistan'ın ikinci ve son işi animasyon; boyut/kalınlık modeli sadece sınıf tahminini besleyen bir
alt bileşen. Her aşama kendi başına kullanılabilir ve geriye dönük uyumludur.

**Durum güncellemesi (2026-10-08):**

| Aşama | Durum |
|---|---|
| A0–A3 | ✅ tamam (plan + araştırma · özellik spec + 3 dil + determinizm · öğretmen + ingest · M1 sınıf modeli) |
| A4 | ✅ tamam — **A4b** asistan eklentiye bağlandı (6 modül gömülü, v9 dondurma kapısı) + **A4c** gerçek-veri kapısı (`verify_real_run.py`: 28 tasarım, kural kararı etiketle %100 uyumlu) |
| A5 | ✅ TAMAM (108 animasyon) |
| A6–A8 | ⏳ bekliyor (FX tespiti · animasyon seçici + üretici · beğenmedim döngüsü) |
| A9 | ⏳ opsiyonel |
| A10 | 🟡 kısmi — kural tabanlı `EIStyle` + sınıf modelinde stil öncülleri var; ayrı `train_style.py` yok; eşikler sentetik veriye kalibre, **gerçek etiketle kalibrasyon bekliyor** (`STIL-SORULARI.md`) |
| **A11** (yeni) | ✅ gerçek veri hattı — `fig_decode` (.fig→JSON) + `build_real_dataset.py` + `verify_real_run.py`; 10 `.fig` → 28 export → 4 490 etiket; model 4 642 örnekle eğitildi |
| **A12** (yeni) | ⏳ stil kalibrasyonu — kullanıcı etiketleri (`STIL-SORULARI.md`) |
| **A13** (yeni) | ⏳ Studio smoke testi — kullanıcı (`STUDIO-TESTI.md`) |

---

## 8. Açık sorular (onayda netleştirilecek)

1. **Örnek veri:** `datasets/raw/`'a koyacağın ilk Figma export'ları var mı, yoksa **sentetik**
   (rastgele üretilmiş ama gerçekçi UI ağaçları) veriyle A1–A3'ü doğrulayıp senin verini sonra mı ekleriz?
2. **Sınıf listesi:** 14 sınıf (yukarıdaki liste) yeterli mi, `UICorner`/`UIStroke` gibi **dekoratif
   süslemeler** de sınıf olarak tahmin edilsin mi?
3. **Animasyon iskeleti:** İlk etapta kaç animasyon girmeli? (Öneri: 30 ile başla, format otursun;
   sonra 100+'a çıkar.)
4. **Klasik plugin:** `figma-plugin-klasik/` de asistan alsın mı, yoksa sadece `all-in-one` mu?
5. **Boyut önerisi otomatik uygulanmalı mı?** (Öneri: hayır — "Öneri" olarak göster, kullanıcı onaylar.)

---

*Bu belge onaylandıktan sonra A1 ile başlanacak ve her aşamada `verify_runtime.py` kapısı uygulanacak.*
