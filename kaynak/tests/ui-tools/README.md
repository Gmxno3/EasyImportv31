# UI Tools — test düzeneği

Bu testler **gerçek Roblox Studio'da çalışmaz**. Roblox API'si yerine mock bir ortam kullanır (`test_plugin.lua`).
Amaç: mantığın doğru olduğunu ve paketlenmiş kodun test edilen kod olduğunu kanıtlamak.

- `test_core.lua` — saf hesaplar (hizalama, dağıtma, ızgara, taşıma, Scale dönüşümü, sınıf planı): 135 kontrol.
- `test_plugin.lua` — plugin'i mock Studio'da çalıştırır, düğmeleri tıklar ve ok tuşu olaylarını gönderir: 137 kontrol.
- `mutate.py` — bilerek hata ekleyip testlerin bunları yakaladığını doğrular (20/20).
- `run.sh` — testleri sırayla çalıştırır. Gereksinim: `node` (Node 18+). Lua VM olarak `assistant/tools/vendor/fengari` kullanılır.

Gerçek Studio'da doğrulama henüz yapılmadı; bkz. `kaynak/roblox-studio-plugin/UI-TOOLS.md`.
