# Gelişmiş Öğrenme Motoru — Araştırma + Plan

> İstek: *"Asistanı gelişmiş öğrenme motoru eklemeni istiyorum. Yanlış yaptığında da **neden
> yanlış yaptığını** akıllı bir sistem yap."*
> Tarih: 2026-10-05 · Durum: **TASLAK — onay bekliyor**

---

## BÖLÜM 1 — ARAŞTIRMA ÖZETİ

### 1.1 Model seçimimiz zaten en büyük avantajımız

Sınıf modeli olarak **softmax regresyon (lojistik regresyon)** seçtik. Bu, "neden yanlış yaptım"
sorusunu **neredeyse bedavaya** cevaplamamızı sağlıyor:

```
logit_c = W_c · x + b_c
katkı(i → c) = W[c][i] * x[i]
```

Doğrusal modeller **doğal olarak yorumlanabilir** (intrinsically interpretable). SHAP/LIME gibi
pahalı, kararsız ve yaklaşık (approximate) açıklama katmanlarına **ihtiyaç yok** — katkıları
doğrudan, tam ve deterministik hesaplayabiliyoruz. Araştırma da bunu destekliyor: LIME'in
kararlılığı düşük (std 0.33), KernelSHAP bağımsızlık varsayımı yapıyor, Feature Ablation daha seyrek
ama daha güvenilir [1](https://arxiv.org/html/2605.27618v1). Bizim modelde bu tartışma yok.

> ⚠️ İleride MLP (gizli katman) eklersek bu avantaj kaybolur → o zaman **sürrogate** (modeli taklit
> eden doğrusal model) kullanırız. Öneri: **açıklanabilirlik için modeli olabildiğince doğrusal tut.**

### 1.2 Confident Learning — "etiket mi yanlış, model mi?"

Bizim en kritik problemimiz: **öğretmen etiketleri (kural motoru) gürültülü.** Kural motoru
"`btn` geçiyor → ImageButton" diyor ama o katman aslında ImageLabel olabilir. Bu gürültüyü temizlemeden
model eğitmek, yanlışı öğretmektir.

**Confident Learning (CL)** tam bunu çözer [2](https://arxiv.org/abs/1911.00068)
[3](https://l7.curtisnorthcutt.com/confident-learning):
- Girdi: **out-of-sample tahmin olasılıkları** (cross-validation ile) + **verili (gürültülü) etiketler**
- Çıktı: **confident joint** matrisi → "gerçekte B olan ama A etiketlenmiş N örnek var"
- Üç ilke: **Prune** (gürültülü örnekleri çıkar) · **Count** (gürültü oranını say) · **Rank** (güvenle sırala)
- Model-agnostik, iteratif değil, **gerçek (temiz) etiket gerektirmez**
- %40–70 etiket gürültüsünde bile çalışıyor

Bizde kullanımı:
```
1. 5-fold CV ile her örnek için out-of-sample olasılık üret
2. Confident joint Q[verili_etiket][tahmin_edilen] hesapla
3. Q'nun diğer dışı (off-diagonal) hücrelerindeki örnekleri "etiket şüpheli" olarak işaretle
4. Şüphelileri SANA göster → "bu mu doğru?" → onaylananları dzelt
5. Temizlenmiş veriyle yeniden eğit
```

### 1.3 Counterfactual — "ne olmalıydı ki doğru olsun?"

Araştırma: counterfactual explanation = **tahmini değiştiren en küçük özellik değişikliği**
[4](https://christophm.github.io/interpretable-ml-book/counterfactual.html)
[5](https://link.springer.com/article/10.1007/s10618-022-00831-6).

Doğrusal modelde **analitik ve anında**:
```
yanlış sınıf  ŷ  →  doğru sınıf  y*
yön vektörü   d  = (W[y*] - W[ŷ]) / ||W[y*] - W[ŷ]||
x' = x + ε·d     (ε en küçük adım: logit[y*] > logit[ŷ] olana kadar)
```
Seyrek (sparse) versiyon: sadece en yüksek katkılı **k=3** özelliği değiştir.

Çıktı cümlesi:
> *"ImageButton demem için kontur kalınlığının 0.018 → 0.055 olması yeterliydi.
> Bu GUI'deki diğer 6 butonda kalınlık 0.048–0.062 aralığında."*

### 1.4 Aktif Öğrenme — "sana neyi sormalıyım?"

Senin zamanın değerli. Model **kendi sorması gereken soruları seçsin** [6](https://towardsdatascience.com/reducing-human-annotation-with-ml-active-learning/)
[7](https://medium.com/@nirmalya.ghosh/a-quick-overview-of-active-learning-04ca80064219):

| Strateji | Formül | Ne zaman |
|---|---|---|
| **Entropi** | `H(x) = -Σ p_i log₂ p_i` | genel belirsizlik |
| **Margin** | `M(x) = p_(1) - p_(2)` — küçükse belirsiz | ikili kararsızlık (eşik < 0.10) |
| **Çeşitlilik** | belirsizleri kümele, **her kümeden 1** | aynı soruyu 50 kez sormamak için |
| **Yoğunluk (SUD)** | `skor = belirsizlik × temsiliyet` | outlier seçme tuzağından kaçınmak |

⚠️ Araştırma uyarısı: **saf belirsizlik örneklemesi aykırı değerleri (outlier) seçer** ve özellik
uzayının küçük bir bölgesine kilitlenir → **çeşitlilik kontrolü şart** [7].

Bizde: her oturumda sana **~20 soru**, en az 5 farklı kümeden.

### 1.5 Diğer bileşenler

| Bileşen | Kaynak / gerekçe |
|---|---|
| **Focal loss** — zor örneklere ağırlık | `FL = -(1-p_t)^γ · log(p_t)`, γ=2. Kolay örneklerin katkısını bastırır |
| **Kalibrasyon** — güven skoru dürüst olsun | Temperature scaling + ECE (Expected Calibration Error). Eşik 0.70 ancak kalibre edilmişse anlamlı |
| **Replay buffer** — unutma | Sürekli öğrenmede eski örneklerden küçük bir temsili havuz tut; yoksa **catastrophic forgetting** |
| **Dağılım kayması (drift)** | PSI (Population Stability Index) ile özellik dağılımını eğitim verisiyle karşılaştır; kayma varsa uyar |
| **Sürüm kapısı** | Yeni model, sabit "altın set" (golden set) üzerinde eskisini **geçmeden yayınlanmaz**; sınıf bazlı düşüş varsa otomatik geri alma |

---

## BÖLÜM 2 — MİMARİ

```
                        ┌──────────────────────────────────────┐
  SENİN VERİN ─────────▶│ 1. ingest.py  (ham JSON → örnek)     │
  düzeltmelerin ───────▶│ 2. label_tool.py  (etiketleme)       │
                        └──────────────┬───────────────────────┘
                                       ▼
                        ┌──────────────────────────────────────┐
                        │ 3. ETİKET SAĞLIĞI (confident learn.) │
                        │    → şüpheli etiketleri sana sorar    │
                        └──────────────┬───────────────────────┘
                                       ▼
                        ┌──────────────────────────────────────┐
                        │ 4. train_class.py (+ focal loss,     │
                        │    replay buffer, kalibrasyon)       │
                        └──────────────┬───────────────────────┘
                                       ▼
                        ┌──────────────────────────────────────┐
                        │ 5. SÜRÜM KAPISI (altın set + A/B)    │
                        │    geçemezse → eski model kalır      │
                        └──────────────┬───────────────────────┘
                                       ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ 6. ÇALIŞMA ZAMANI (Lua / JS) — her tahminle birlikte:              │
   │    { cls, conf, top3, KATKI: [(özellik, ağırlık), ...], style }    │
   └───────────────────────────────┬────────────────────────────────────┘
                                   ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ 7. HATA KAYDI (mistake ledger) — sen düzeltince:                   │
   │    → 8. KÖK NEDEN ANALİZİ → 9. AKTİF ÖĞRENME KUYRUĞU              │
   └────────────────────────────────────────────────────────────────────┘
```

### 7. Hata Kaydı (`datasets/mistakes.jsonl`)

```jsonc
{"ts":1760000000, "export":"MainMenu", "path":"0.2.5",
 "pred":{"cls":"TextLabel","conf":0.71,"top3":[["TextLabel",0.71],["ImageButton",0.24],["Frame",0.05]]},
 "true":"ImageButton",
 "who":"user",                       // user | rule-teacher | confident-learning
 "feat":{ ...özellik vektörü... },
 "contrib":[["hasTextChild",1.92],["strokeWeightRatio",-1.34],["nameToken_any",-0.71],["aspect",0.55]],
 "style":"cartoon", "guiCluster":3 }
```

> **Güncel karar (KARARLAR.md §4, 2026-10-08):** hata kaydı ve aktif öğrenme kuyruğu
> **son kullanıcıya gösterilmez** — geliştiricinin eğitim oturumuna (offline veri toplama)
> bağlanır. `who` alanındaki `"user"` dalı bu yüzden şu an devre dışıdır.

### 8. ⭐ Kök Neden Analizi — "NEDEN YANLIŞ YAPTIM?"

Her hata **7 kovadan birine** sınıflandırılır. Kova → otomatik aksiyon:

| Kova | Teşhis | Otomatik aksiyon |
|---|---|---|
| `EKSİK_ÖZELLİK` | Doğru sınıfın ağırlıklarında hiçbir özellik yeterli sinyal vermiyor (max katkı < eşik) | **Yeni özellik öner**: counterfactual yönündeki en yüksek 3 özellik adayı |
| `YETERSİZ_VERİ` | Bu desen (özellik komşuluğu) eğitimde < 5 kez görülmüş | **Aktif öğrenme kuyruğuna** al → sana sor |
| `ETİKET_HATASI` | Confident learning bu örneği şüpheli buluyor + model ısrarla farklı diyor | Etiketi **düzelt / sil** |
| `STİL_UYUŞMAZLIĞI` | Stil tahmini yanlış → stil önceliği (prior) kararı bozmuş | Stil eşiklerini yeniden kalibre et |
| `KURAL_MÜDAHALESİ` | Açık etiket/kural modeli ezmiş ama sonuç yanlış | **Kuralı gözden geçir** (hangi kural, kaç kez yanlış) |
| `BAĞLAM_EKSİK` | Öğe tek başına bakınca belirsiz; GUI bağlamı (boyut kümesi, kardeşler) çözer | Bağlam özelliklerinin ağırlığını artır |
| `SINIR_DURUM` | Gerçekten muğlak, iki sınıf da makul | **Kabul et**, güven eşiğini düşür, insan onayı iste |

**Sınıflandırma mantığı:**
```
1. Confident joint bu örneği şüpheli buluyor mu?            → ETİKET_HATASI
2. Bir kural modeli ezmiş mi?                                → KURAL_MÜDAHALESİ
3. Stil tahmini conf < 0.6 mı VEYA stilsiz tahmin doğru mu?  → STİL_UYUŞMAZLIĞI
4. Doğru sınıfın max|katkı| < 0.3 mü?                        → EKSİK_ÖZELLİK
5. Bu desende eğitim örneği < 5 mi?                          → YETERSİZ_VERİ
6. Bağlam özellikleri (küme/kardeş) eklenince düzeliyor mu?  → BAĞLAM_EKSİK
7. Hiçbiri                                                   → SINIR_DURUM
```

### 8b. Hata Raporu — sana gösterilecek çıktı

```
✗ MainMenu / 0.2.5  —  "Play_Button"
  Dedim: TextLabel (%71)     Doğrusu: ImageButton
  Teşhis: EKSİK_ÖZELLİK
  Neden: 'içinde metin var' özelliğine +1.92 ağırlık vermişim.
         Bu GUI'de 8/8 örnekte "metinli + kalın konturlu" desen var ve hepsi buton.
  Counterfactual: kontur kalınlığı 0.018 → 0.050 olsaydı ImageButton derdim (%83).
  Öneri: YENİ ÖZELLİK — "metinli + kalın kontur" çapraz özelliği (hasTextAndThickStroke)
         Bu özellik eklense 12 benzer hatanın 11'i düzeliyor.
  [Kabul et] [Reddet] [Bu deseni göster]
```

### 9. Aktif Öğrenme Kuyruğu — sana sorulacaklar

```
skor(x) = belirsizlik(x) × temsiliyet(x) × çeşitlilik_bonusu(x)
belirsizlik = 1 - (p₁ - p₂)          (margin)
temsiliyet  = k-NN yoğunluğu (outlier cezası)
çeşitlilik  = aynı kümeden zaten sorulmuşsa skor / 10
```

Her oturum: **20 soru, en az 5 farklı küme, en az 3 farklı sınıf.**
Soru formatı: tek tık — `ImageButton ✓ / ImageLabel / TextLabel / Frame / Atla`

### 10. Öz-İzleme

| Kontrol | Eşik | Aksiyon |
|---|---|---|
| **Kalibrasyon (ECE)** | > 0.08 | Temperature scaling yenile |
| **Dağılım kayması (PSI)** | > 0.25 | Uyar: "bu GUI eğitim verimden farklı, düşük güven bekle" |
| **Sınıf bazlı doğruluk düşüşü** | > 5 puan | Otomatik geri alma (rollback) |
| **Kural/model çakışma oranı** | > %20 | Kuralı gözden geçir |

---

## BÖLÜM 3 — DOSYA YAPISI

```
assistant/
├── OGRENME-MOTORU.md          ← bu belge
├── tools/
│   ├── ingest.py              ← ham JSON → samples.jsonl
│   ├── label_tool.py          ← CLI etiketleme + DÜZELTME (hata kaydına yazar)
│   ├── rules_teacher.py       ← kural motorunun Python karşılığı (öğretmen)
│   ├── train_class.py         ← + focal loss, replay buffer, class weights
│   ├── label_health.py        ← ⭐ confident learning (şüpheli etiket avı)
│   ├── diagnose.py            ← ⭐ kök neden analizi (7 kova + counterfactual)
│   ├── active_queue.py        ← ⭐ aktif öğrenme kuyruğu (sana sorulacaklar)
│   ├── feature_propose.py     ← ⭐ eksik özellik önerisi
│   ├── eval.py                ← altın set, sınıf bazlı, kalibrasyon (ECE), drift (PSI)
│   ├── export_model.py        ← model.json + EI_ModelData.lua + ei-model.js
│   └── verify_runtime.py      ← 3 dil aynı sonucu mu? (ZORUNLU KAPI)
├── datasets/
│   ├── raw/  labels/  anim-usage/
│   ├── golden.jsonl           ← ⭐ sabit altın set (sürüm kapısı için, asla değişmez)
│   ├── mistakes.jsonl         ← ⭐ hata kaydı
│   └── replay.jsonl           ← unutmaya karşı temsili havuz
└── runtime/
    ├── lua/EIExplain.lua      ← ⭐ Lua tarafı katkı (attribution) hesabı
    └── js/ei-explain.js       ← ⭐ JS tarafı katkı hesabı
```

**Neden Lua/JS'te de attribution var?** Studio panelinde anında
*"neden ImageButton dedim?"* gösterebilmek için. Hesap 12 sınıf × 230 özellik = 2.760 çarpım,
~0.2 ms — her öğe için gösterilebilir.

---

## BÖLÜM 4 — YOL HARİTASI

| # | İş | Çıktı | Kabul kriteri |
|---|---|---|---|
| **L1** | Hata kaydı + attribution (Lua/JS/Python) | `EIExplain.*`, `mistakes.jsonl` | Her tahminle birlikte katkı listesi; 3 dil aynı |
| **L2** | Counterfactual motoru | `diagnose.py` | "X → Y olması için şu değişmeli" açıklaması üretilir |
| **L3** | Kök neden sınıflandırma (7 kova) | `diagnose.py` | Hatalar doğru kovaya düşer (senin 20 elle etiketlediğin hatada ≥ %80) |
| **L4** | Confident learning (etiket saflığı) | `label_health.py` | Öğretmen etiketlerindeki gürültüyü bulur, temizleme sonrası doğruluk artar |
| **L5** | Aktif öğrenme kuyruğu | `active_queue.py` | 20 soru ≥ 5 küme; sorulan örneklerle doğruluk artışı rastgele seçime göre belirgin |
| **L6** | Focal loss + replay + kalibrasyon | `train_class.py` | ECE < 0.08 |
| **L7** | Sürüm kapısı + otomatik geri alma | `eval.py` | Altın seti geçmeyen model yayınlanmaz |
| **L8** | Eksik özellik önerisi | `feature_propose.py` | Önerilen özellik gerçekten doğruluğu artırıyor |
| **L9** | Drift + öz-izleme paneli | `eval.py` + Studio paneli | Farklı bir GUI verildiğinde uyarı çıkıyor |

**Bağımlılık:** L1–L3 sınıf modelinden (A3) sonra gelir ama **A1'deki attribution altyapısı**
(Lua/JS katkı hesabı) hemen kurulabilir — sonradan eklemek daha zor.

---

## BÖLÜM 5 — SANA SORULAR

`SORULAR.md` → **Bölüm I** (9 soru). En kritikleri:

- **I1** — Attribution'ı nerelerde gösterelim? (Figma paneli / Studio paneli / eğitim raporu / hepsi)
  → **Karar (KARARLAR.md §4):** yalnızca iç teşhis + eğitim raporu; **panellerde gösterilmez**.
- **I2** — Hata düzeltme akışı nasıl olsun? (Figma'da export sırası mı, Studio'da import sonrası mı, ayrı bir araç mı?)
- **I3** — Confident learning şüpheli etiket bulunca: **sana sorsun mu**, yoksa otomatik düzeltsin mi?
- **I5** — Aktif öğrenme: sana seans başına **kaç soru** sormalı? (Öneri: 20)
- **I7** — Model doğrusal (lojistik regresyon) kalsın mı? (Açıklanabilirlik için kritik — MLP eklersek attribution yaklaşık olur)

---

## BÖLÜM 6 — NEDEN BU "AI'DEN DAHA ZEKİ"?

| LLM / sohbet AI | Bu sistem |
|---|---|
| Yanlış yapınca **nedenini bilemez** | Her hatanın **7 kovalı kök neden teşhisi** |
| Düzeltmeyi **unutur** (bağlam dışı) | Hata kaydı + replay buffer → **kalıcı öğrenir** |
| Eğitilemez (senin verinle) | **Senin JSON'larınla** eğitilir |
| Güven skoru **uydurmadır** | Kalibre edilmiş (ECE < 0.08), ölçülmüş |
| "Emin değilim" diyemez | Belirsizde **sana sorar** (aktif öğrenme) |
| Açıklama **sonradan uydurulmuş** | Doğrusal model → katkılar **matematiksel olarak tam** |
| Veri gürültüsünü ayırt edemez | Confident learning → **etiket hatası vs model hatası** |
| İnternet/sunucu ister | **Tamamen çevrimdışı**, plugin içinde |

---

## BÖLÜM 7 — TAMAMLAYICI ARAŞTIRMA (ikinci tur)

Bu bölüm, ilk turda değinilmeyen ama motorun kalitesini doğrudan belirleyen 6 bulguyu ekler.

### 7.1 ⭐ Artımlı güncelleme: RLS — replay'sız, unutmasız

Replay buffer yerine **kapalı form** tercih edilmeli:

```
W = (XᵀX + λI)⁻¹ XᵀY
```

- **Sherman-Morrison** ile satır satır artımlı güncelleme: `O(F²)` ≈ 53.000 işlem (F≈230).
- **Felaket unutma yok** — geçmiş bilgi matematiksel olarak `XᵀX` içinde durur.
  Replay buffer'a **gerek yok**, bellek maliyeti yok, hiperparametre yok.
- Bellek: `F×F` matris = 230×230 ≈ 53.000 float ≈ **420 KB**.
- ⚠️ Sınırlama: sabit özellik seti gerekir. Spec değişirse matris yeniden kurulur (hızlı, sorun değil).

**Karar:** önce RLS dene. Yetmezse (veya MLP'ye geçilirse) replay buffer'a dön
(sınıf başına 40 örnek yeterli — araştırmaya göre az örnek bile unutmayı büyük ölçüde azaltır).

### 7.2 ⭐ Sıra kritik: kalibrasyon → açıklama → aktif öğrenme

Araştırma bulgusu: **kalibre edilmemiş bir modelde belirsizlik örneklemesi işe yaramaz.**
Güven skoru şişkinse "en belirsiz" sandığımız örnekler aslında en belirsiz değildir.

```
E2 modeli eğit  →  E3 KALİBRASYON (T, ECE, sınıf bazlı eşik)  →  E4 açıklama
                                                               →  E5 hata analizi
                                                               →  E6 aktif öğrenme
```

### 7.3 ⭐ Sınıf bazlı eşik (tekGlobal 0.70 yerine)

Seçici tahmin (abstain) — model bilmiyorsa susar, kural motoru devralır.
Eşik **sınıfa göre** farklı olmalı:

| Sınıf | Önerilen eşik | Gerekçe |
|---|---|---|
| `ImageButton` / `TextButton` | **0.80** | Yanlışsa buton çalışmaz — yüksek risk |
| `ImageLabel` / `TextLabel` | 0.70 | Orta risk |
| `Frame` / `ScrollingFrame` | **0.55** | Düşük risk, kolay düzeltilir |

Risk-coverage eğrisiyle kalibre edilir (hedef doğruluğa göre eşik seçilir).

### 7.4 Gruplanmış atıf — ilişkili özellikler tuzağı

SHAP **özellik bağımsızlığı varsayar.** Bizim özelliklerimiz doğal olarak ilişkili
(`w` ↔ `area`, `depth` ↔ `parentDepth`, `strokeWeight` ↔ `borderRatio`).
Tek tek atıf yanıltıcı olur → **grup bazında atıf**:

```python
φ_g(c) = Σ_{i ∈ g} W[c][i] · (x_i − μ_i)      # g ∈ {geometri, kontur, konum, ad, renk, içerik, ağaç, efekt}
```

Toplamları logit farkına **birebir** eşit olmalı — bu, doğruluk testi olarak kullanılır.

### 7.5 Kalibrasyon yöntemleri — ne zaman hangisi

| Yöntem | Parametre | Ne zaman |
|---|---|---|
| **Temperature scaling** | 1 skaler `T` | İlk tercih. Doğruluğu **değiştirmez**. |
| **Vector scaling** | 2K | Sınıf bazlı hata varsa |
| **Dirichlet calibration** | K² | Sınıf bazlı **yanlılık** varsa (temperature tek parametre olduğu için düzeltemez) |
| **Isotonic regression** | çok | Eğri diyagonali kesiyorsa (non-uniform) |

Metrik: **ECE** (ilk hedef < 0.08, olgunlaşınca < 0.03), **MCE**, **Brier**, reliability diagram.

### 7.6 Model kartı & sürüklenme

Her sürümle üretilen **model kartı**: eğitim verisi istatistikleri, sınıf dağılımı, kaynak
ağırlıkları, sınıf bazlı doğruluk, **bilinen hata kalıpları**, kapsam dışı durumlar, üst sürüm,
eşikler, `T`, ECE.

**Sürüklenme tespiti:** yeni export'ların özellik dağılımı vs eğitim dağılımı → **PSI**
(Population Stability Index) özellik başına. `PSI > 0.25` → *"tasarım dilin değişti, yeniden
eğit"* uyarısı.
