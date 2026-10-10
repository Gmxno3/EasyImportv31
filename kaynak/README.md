# EasyImport — Asistanlı sürüm

Klasörler:
- `figma/` — Figma eklentisi (`code.js`, `ui.html`, `manifest.json`). Yeni: görsel ölçümü (`item.ei`), eğitim dosyası (`_egitim.json`), asistan özeti.
- `roblox-studio-plugin/` — Studio eklentisi. `EasyImportStudioPlugin.rbxmx` (Studio'ya sürüklenecek dosya; `.rbxm` ile aynıdır).
  `.lua` kaynağı tek doğruluk kaynağıdır; `python3 build_rbxmx.py` ile paketlenir.
- `assistant/` — asistan modülleri (`runtime/lua`), animasyon kütüphanesi, eğitim/doğrulama araçları.
- `tests/` — Figma birleştirme kapısı ve Studio köprü kapısı.

Kurulum: Figma'da `figma/manifest.json` ile eklentiyi içe aktar. Studio'da `EasyImportStudioPlugin.rbxmx`'i sürükle.

Asistan yalnızca Figma'dan gelen JSON'da `ei` ölçümü varsa devreye girer; yoksa v9 davranışı birebir korunur.

## Bu sürümde eklenenler

- **Figma paneli asistanı:** Sonuç ekranında her katmanın tahmini sınıfı (model / öğrenme / düşük güven), güven yüzdesi ve sınıf seçici var. Sınıf değiştirmek bir düzeltmedir: öğrenme durumuna yazılır ve Figma'nın kendi depolamasında (`clientStorage`) saklanır. "Öğrenme paketini indir" düğmesi kanonik `ei-learn v1` metnini indirir.
- **Studio öğrenmesi:** Düzeltmeler eklenti ayarında (`SetSetting`, anahtar `EasyImportLearn`) kalıcıdır.
- **Derleme:** `figma/ui.html` `figma/ui.base.html` + `assistant/runtime/js` + `figma/asistan_panel.*` dosyalarından `python3 figma/build_ui.py` ile üretilir. Kaynağı değiştirirsen ui.html'i yeniden üret.

Yapılmayanlar: animasyon seçici arayüzü, FX tespiti, `train_anim.py`, UIGridLayout/Item/DROP/MERGE öğrenmesi.

## Testler

- `tests/verify_figma_merge.js` — code.js birleştirmesi (v9 bayt eşitliği, ei ölçümü, E1)
- `tests/verify_learn_channel.js` — öğrenme kanalı (clientStorage kayıt/okuma)
- `tests/verify_studio_port.py` — Studio asistan köprüsü, gerçek fixture'larda
- `assistant/tools/verify_anim.py`, `verify_learn.py`, `verify_merge.py` — asistan modülleri

## Sürüm 3 (animasyon ve tamamlanan asistan)

- **Animasyon seçicisi (Figma paneli):** Her buton ve üst düzey öğe için giriş, hover ve basma animasyonu seçilebilir. Seçim öğrenmeye kaydedilir (kabul/ret). Gözlem olmadan sıralama v10 ile birebir aynıdır.
- **Studio:** Animasyon planı eklentinin öğrenme durumunu kullanır (`assist.learn`).
- **Lua ≡ JS parite kapısı:** `assistant/tools/verify_anim_parity.py` — plan, 840 seçenek sırası ve 8 LocalScript kaynağı iki dilde bayt birebir.
- **Veri üretimi:** `assistant/tools/build_anim_lua.py` hem `runtime/lua/EIAnim.lua` hem `runtime/js/ei-anim.js` veri bloğunu ve şablonu üretir.

Kalan (bilinçli kapsam dışı): FX tespiti, döngü (`dongu`) animasyonları, `train_anim.py`, UIGridLayout/Item/DROP/MERGE öğrenmesi.
