# Yerel Öğrenme — Sunucusuz Tasarım

> **Sorunun cevabı: EVET, sunucu olmadan olur.** Öğrenme tamamen **plugin'in içinde**, kullanıcının
> kendi cihazında çalışır. Bu belge neyin nasıl çalıştığını, neyin mümkün olmadığını ve verinin
> nasıl birikebileceğini anlatır.
> Durum: **karar verildi (KARARLAR §12 → revize)** · Tarih: 2026-10-06

---

## 1. Ne mümkün, ne değil (dürüst tablo)

| İstek | Sunucusuz mümkün mü? | Nasıl |
|---|---|---|
| Asistan **bu kullanıcının** seçimlerinden öğrensin | ✅ **Evet** | Sayaçlar cihazda tutulur (`figma.clientStorage` / `plugin:SetSetting`). Öğrenme anında etkili olur. |
| Asistan **tüm kullanıcıların** seçimlerinden öğrensin | ❌ Hayır (otomatik) | Kullanıcılar birbirinden habersizdir; aradaki köprü ya sunucu olur **ya da dosya**. |
| Verinin **sana** ulaşması | 🟡 Şartlı | Kullanıcı **"öğrenme paketi" dosyasını indirirse** (tek tık) ve sana gönderirse. Otomatik gönderim sunucu ister. |
| Modelin herkes için iyileşmesi | ✅ Evet | Sen dosyaları toplayıp **offline** birleştirir, yeni modeli **plugin sürümüyle** yayınlarsın. Kullanıcı hiçbir şey yapmaz, güncellemeyle gelir. |

**Özet:** Sunucusuz = "herkes kendi cihazında öğrenir + sen topluca yayınlarsın".
Sunuculu = "seçimler anında herkese yayılır". Birincisi halka açık ücretsiz plugin için **yeterli ve daha güvenli**.

---

## 2. Platform limitleri (araştırıldı)

| Platform | API | Limit | Not |
|---|---|---|---|
| Figma | `figma.clientStorage` | **5 MB / plugin** (resmî) | Öğrenme dosyamız ~3–70 KB. Tarayıcı önbelleği temizlenirse silinebilir → periyodik dışa aktarma önerilir. `setPluginData` (100 KB) **kullanılmaz**, çünkü o dosyaya yazar ve kullanıcılar arası senkron olur. |
| Roblox Studio | `plugin:SetSetting` | Resmî sınır yok; diske yazar | ⚠️ Büyük ayar dosyası **Studio açılışını yavaşlatır** (forumda 800 KB'lık dosya takılmaya yol açmış). ⚠️ Anahtar `.` veya `\` içerirse **sessizce başarısız olur** → anahtarımız: `EasyImportLearn`. Öğrenme dosyamızı **64 KB** ile sınırlıyoruz. |

Kaynaklar: Figma `clientStorage` dokümantasyonu (5 MB, plugin bazlı) · Roblox DevForum
(`SetSetting` davranışı, ayar dosyası boyutu, anahtar karakter kısıtı).

---

## 3. Ne öğrenilir? (tam olarak senin istediğin)

Senin cümleyin: *"Kullanıcıların seçtiği animasyonlardan da öğrensin: ne sıklıkla, hangi stilde,
nerede, buton mu, çok detay var mı, anime stili mi kullanılıyor."*

Bunun veri modeli **sayaçlardır** — ağır eğitim değil:

```
bağlam  = stil | sınıf | rol | fx
örnek   = "anime|ImageButton|primary|glow"
kayıt   = {"shine_sweep": [seçildi=12, reddedildi=1], "glow_pulse": [7, 0], ...}
```

- **stil**: GUI düzeyi stil yuvaları (`cartoon` / `stud` / `anime` / `belirsiz`)
- **sınıf**: öğenin (tahmin edilen veya gerçek) Roblox sınıfı
- **rol**: `anim-library.json` rolleri (`primary-button`, `icon`, `panel`, …)
- **fx**: FX türü varsa (`glow`, `shine`, `rays`…), yoksa `-`

Ayrıca **sınıf tercihi**: kullanıcı asistanın dediğini elle değiştirdiyse
(`ImageLabel` → `ImageButton`) bu da bağlamla sayılır ve bir sonraki tahminde önsel olur.

**Beğenmeme = ret sayacı.** Kullanıcı öneriyi reddedip başka animasyon seçtiğinde eski öneri
`reddedildi` alır; skoru düşer. Soru sorulmaz, panel açılmaz (KARARLAR §2 ile uyumlu).

---

## 4. Skorlama (iki dilde birebir olacak şekilde tamsayı tabanlı)

```
skor(anim) = (2·seçim + 1) / (2·(seçim + ret) + 2)      ← yumuşatılmış kabul oranı
sıralama   = skor ↓, toplam gözlem ↓, id ↑              ← son ölçüt determinizm için ŞART
```

- Yalnızca **tamsayı** sayaçlar ve **IEEE-754** bölme → JS ile Lua aynı sonucu verir (tarayıcı/Luau
  ikisi de aynı double aritmetiği yapar).
- Hiç gözlem yoksa skor = 0.5 (nötr) → asistan kendi varsayılan sırasını korur.

---

## 5. Dosya biçimi (küçük, metin, satır tabanlı)

```
ei-learn v1
events 615
exports 3
anim anime|ImageButton|primary|glow shine_sweep 12 1
anim stud|Frame|panel|- pop_in_scale 9 0
cls  belirsiz|Icon|-|-    ImageButton 4
```

- Satırlar **sıralı** yazılır (`ctx`, sonra `id`) → aynı durum her zaman aynı metni verir.
- Kodlama-çözme **kayıpsız** (kapıda test edilir).
- **Budama:** bağlam sayısı 400'ü ya da metin 64 KB'ı geçerse **en az kullanılan** bağlamlar atılır
  (ölçüt: toplam gözlem ↑, sonra anahtar ↑). Yani depolama asla şişmez.

Ölçülen (kapı çıktısı): 615 olay → **2.866 bayt**; yapay 300 bağlamlık kalabalık → budama sonrası
40 bağlam / **3.676 bayt** (sınır 4.096 bayt).

**Birleştirme kabul kuralları (`merge_learn.py`):** düz metin ya da `{"text": "ei-learn …"}` JSON
sarmalayıcısı · `ei-learn v1` dışındaki sürüm **reddedilir** (sessiz karışım yok) · `--dedupe` bayt
bayt aynı paketi bir kez sayar · `--min-observations N` gürültüyü süzer · çıktı dosyası = kanon
`encode()` + tek satır sonu · uyarılı birleştirme **çıkış kodu 2** (boş sonuç dâhil: boş dosyayı
model güncellemesinde kullanma uyarısı).

---

## 6. Akış — sunucusuz

```
   KULLANICI (Figma)                                  KULLANICI (Studio)
   ┌───────────────────────┐                          ┌───────────────────────┐
   │ animasyon önerisi     │                          │ sınıf/animation önerisi│
   │ kullanıcı seçer/reddeder│                         │ kullanıcı değiştirir   │
   └──────────┬────────────┘                          └──────────┬────────────┘
              ▼                                                    ▼
   ┌────────────────────────┐                          ┌────────────────────────┐
   │ ei-learn.js            │  aynı biçim (kapı testli) │ EILearn.lua            │
   │ figma.clientStorage    │ ◀─────── metin ─────────▶ │ plugin:SetSetting      │
   └──────────┬─────────────┘                          └──────────┬─────────────┘
              │                                                   │
              │        [isteğe bağlı] "Öğrenme paketini indir"     │
              └───────────────┬───────────────────────────────────┘
                              ▼
                    EI_ogrenme_<tarih>.json      ← kullanıcı isterse sana gönderir
                              │
                              ▼   (sunucu YOK: elle toplama)
                   tools/merge_learn.py          ← sen birleştirirsin
                              │
                              ▼
                   model + önsel tablolar  →  yeni plugin sürümü (herkes kazanır)
```

---

## 7. Geliştiriciye düşen iş (senin rahatın için minimum)

| İş | Sıklık | Süre |
|---|---|---|
| Kullanıcıların gönderdiği `EI_ogrenme_*.json` dosyalarını bir klasöre atmak | istediğinde | 1 dakika |
| `python3 tools/merge_learn.py dosyalar/* -o datasets/learn/merged.txt --priors datasets/learn/priors.json` | istediğinde | 1 komut |
| Yeni modeli/önsel tabloları plugin'e gömüp sürüm çıkarmak | istediğinde | 1 komut + yayın |

**Sunucu yok, hesap yok, veri akışı yok.** Öğrenme paketi göndermeyen kullanıcı da kendi
cihazındaki öğrenmeden tam olarak faydalanır.

---

## 8. Uygulama durumu

| Parça | Durum |
|---|---|
| `runtime/js/ei-learn.js` | ✅ yazıldı (kanon) |
| `runtime/lua/EILearn.lua` | ✅ yazıldı (Studio) |
| `tools/verify_learn.py` — determinizm kapısı | ✅ **GEÇTİ** (kodlama, sıralama, budama, round-trip birebir) |
| Figma paneli: seçim/ret kaydı + "öğrenme paketi indir" | ⏳ A4 entegrasyonu |
| Studio eklentisi: sınıf düzeltmesi kaydı + yerel öğrenme | ✅ A4b — `Assist.noteCorrection` → `SetSetting("EasyImportLearn")` |
| `tools/merge_learn.py` — paketleri birleştirme | ✅ yazıldı (deterministik, 400 bağlam/64 KB, rapor + önsel tablo) |
| `tools/verify_merge.py` — birleştirme kapısı | ✅ **GEÇTİ** (16 kontrol: JS ≡ Python ≡ Lua bayt paritesi, sınırlar, düşmanca girdi) |
| Önsel tabloların modele gömülmesi (anim önerisi) | ⏳ A7/A8 ile birlikte (`merge_learn.py --priors` çıktısı hazır) |
| Studio'da "öğrenme paketini indir/yükle" düğmesi | ⏳ §2 (panel) — biçim kanonla birebir olduğu için panel yalnız `EILearn.encode(state)` yazacak |

---

## 9. Gizlilik (net cümleler)

- Varsayılan: **hiçbir şey cihazdan çıkmaz**. Öğrenme paketi **yalnızca kullanıcı indirirse** oluşur.
- Paketin içinde: animasyon id'leri, sınıf adları, stil/rol/fx etiketleri ve **sayılar**.
  Katman adları, dosya adları, PNG'ler, node id'leri **pakete girmez**.
- Panelde açık metin: *"Bu dosya yalnızca seçim istatistiklerini içerir; katman adların ve
  proje bilgilerin paylaşılmaz."*
- Sunucu olmadığı için "arka planda gönderim" **teknik olarak mümkün değil** — bu, gizlilik için
  en güçlü garanti.
