# UI Tools — ikinci eklenti (v1)

`EasyImportStudioPlugin.rbxmx` içinde iki eklenti birden gelir: **EasyImport** (içe aktarma) ve **UI Tools** (düzenleme).
Dosyayı Plugins klasörüne koyunca ikisi de yüklenir. Araç çubuğunda ayrı "UI Tools" düğmesi çıkar.

## Ne yapar
Görsel dil EasyImport Studio paneliyle aynıdır (aynı palet, bölüm kartları, `01 / …` chip'leri, mor ana düğme). İki eklenti yan yana uyumlu görünür.

- **01 · Hizala:** Sol, Yatay Orta, Sağ, Üst, Dikey Orta, Alt. Sağ üstteki `HEDEF` çipi ile iki mod arasında geçilir:
  - *Üst öğe*: her öğe kendi üst öğesine göre hizalanır (varsayılan).
  - *Seçim*: seçilen öğeler birbirine göre hizalanır (aynı üst öğede olmalı).
- **02 · Taşı:** Adım kaydırıcısı ve değer kutusu (1–50 px). Kaydırıcı tutulup fareyle sürüklenir (fare panelin dışına çıksa da çubuğa kenetlenir, taşmaz); sürüklenince değer kutusu güncellenir, kutuya yazılan değer kaydırıcıya yansır. ←↑↓→ düğmeleri öğeyi adım kadar taşır. Izgara: 1 / 4 / 8 px ya da kapalı.
- **03 · Konum & Boyut:** X/Y ve W/H alanları, etiket solda, kutu sağda. Enter veya odak kaybı ile uygulanır; seçim değişince güncellenir.
- **04 · Sınıf:** Frame, TextLabel, TextButton, TextBox, ImageLabel, ImageButton, ScrollingFrame, CanvasGroup, ViewportFrame. Her sınıfın üstünde ortalanmış Studio Explorer ikonu (`StudioService:GetClassIcon`), altında açık eflatun düğme vardır; düğmenin yazısı sınıf adıdır (ör. `Frame`). Çocuklar, ad, konum, boyut ve öznitelikler korunur. Kaybolacak metin/resim/kaydırma özellikleri için uyarı verir.
- **05 · Scale:** `Offset to Scale` ve `Scale to Offset`. Konum ve boyut, piksel değeri korunarak dönüştürülür.
- **06 · Temizle:** `Remove all Attributes` (seçili öğelerin tüm öznitelikleri) ve `Remove All Tags` (seçili öğelerin tüm etiketleri). Yalnızca seçili öğelere uygulanır, alt öğelere değil.
- **Geri alma:** Her işlem `ChangeHistoryService` ile sarılır; Ctrl+Z çalışır.

## Kurallar
- Layout (UIListLayout/UIGridLayout/UITableLayout/UIPageLayout) yöneten üst öğedeki öğelerin konumu/boyutu değiştirilmez; atlanır ve durum satırında sayılır.
- Boyutu okunamayan öğeler (üst öğe Studio'da görünür değilse) atlanır.
- Ayarlar (hedef modu, ızgara, adım) Studio'da kalıcıdır.

## Bilinen sınırlar (v1)
- Zoom ve kısayol özelleştirme yok. Ok tuşları yalnız UI Tools penceresi odaktayken çalışır.
- Kopyalama/yapıştırma yok.
- Temizleme işlemleri alt öğelere (descendant) uygulanmaz.
- AnchorPoint ≠ (0,0) öğelerde hizalama, sol-üst köşe üzerinden yapılır (Roblox'un kendi konum mantığına uygun).

## Doğrulama durumu (v22)
- Mantık (çekirdek): 135 kontrol geçti.
- Mock Studio senaryoları: 137 kontrol geçti (kaydırıcı, sınıf ikonları, temizleme, Offset/Scale, dağıtma, ok tuşları dahil).
- Mutasyon testi: 20/20 bilinçli hata yakalandı.
- Görsel uyum (renk, kart, chip düzeni) EasyImport panelinden birebir kopyalanarak yapıldı; pikselyönünden Studio'da karşılaştırılmadı.
- **Gerçek Roblox Studio'da henüz çalıştırılmadı.** İlk testte şunlara bakın: hizalama değerleri, sınıf değişiminde kaybolan özellikler, Ctrl+Z davranışı.

## Kaynak dosyalar
- `UIToolsCore.lua` — saf hesaplar (Roblox'a bağımlı değil).
- `UIToolsPlugin.lua` — Studio bağlantısı ve arayüz.
- `build_rbxmx.py` — ikisini `EasyImportStudioPlugin.rbxmx` içine paketler. Önce `.lua` dosyalarını değiştirip sonra `python3 build_rbxmx.py` çalıştırın.
- Testler: `kaynak/tests/ui-tools/`.

## v22 değişiklikleri
- **Dağıt (yatay / dikey):** En az 3 öğe seçilir; uç öğeler yerinde kalır, aradakiler eşit boşlukla yerleşir. Aynı üst öğedeki öğeler için çalışır; layout yöneten üst öğedeki öğeler atlanır. Hizala kartının altındaki düğmeler. Ctrl+Z ile geri alınır.
- **Ok tuşları:** ←↑↓→ öğeyi adım kadar taşır (düğmelerle aynı davranış, aynı geri alma). Yalnız UI Tools penceresi odaktayken; metin kutusuna yazarken ya da Studio bir tuşu kullandığında (gameProcessed) çalışmaz.
- **Kaynak düzeltmesi:** Dağıtma boşluk formülü ilk denemede yanlıştı (uç öğelerin boyutu düşülmüyordu); testler yakaladı, düzeltildi.

## v21 değişiklikleri
- **Kaydırıcı düzeltmesi:** Eski sürüm `UserInputService:GetMouseLocation()` kullanıyordu (Studio ana penceresine göre konum). Plugin penceresindeki `AbsolutePosition` ise pencereye göredir; koordinatlar uyuşmadığı için tutamaç panelin dışında/yanlış yerde ilerliyordu. Artık `widget:GetRelativeMousePosition()` + `RunService.Heartbeat` kullanılır; bırakma `input.Changed` ile yakalanır.
- **Eflatun düğmeler:** Sınıf düğmeleri ve `Offset/Scale to ...` düğmeleri açık eflatun. Tüm düğmeleri boyamak için `UIToolsPlugin.lua` başındaki `ALL_BUTTONS_LILAC = true` yap, sonra `python3 build_rbxmx.py`.
- **Sınıf kartı:** 2 sütun; her hücre UIListLayout ile dikey: üstte ikon (ortalı), altta sınıf adlı düğme.
