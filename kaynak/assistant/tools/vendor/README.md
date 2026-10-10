# Gömülü (vendored) üçüncü taraf kod

Bu klasör **yalnızca geliştirici testleri** içindir. Figma plugin'ine veya
Roblox Studio plugin'ine GİRMEZ, kullanıcıya gönderilen hiçbir yapıta dahil
edilmez.

## Neden burada?

`tools/verify_runtime.py`, Python / JavaScript / Lua değerlendiricilerinin
birebir aynı özellik vektörünü ürettiğini kanıtlamak zorundadır (bkz. `A1`).
Lua tarafını çalıştırmak için bir Lua yorumlayıcısı gerekir, ama:

- depoya bir ikili dosya (binary) koyamayız,
- CI'da `apt-get install lua5.3` her zaman mümkün değil,
- `node_modules/` kalıcı değil (snapshot dışı).

Çözüm: **fengari** — JavaScript ile yazılmış gerçek bir Lua 5.3 sanal makinesi.
Node içinde koşar, hiçbir yerel bağımlılığı yoktur, tamamen çevrimdışıdır.

## İçindekiler

| Klasör | Sürüm | Lisans | Kaynak |
|---|---|---|---|
| `fengari/` | 0.1.5 | MIT | https://github.com/fengari-lua/fengari |
| `sprintf-js/` | 1.1.3 | BSD-3-Clause | https://github.com/alexei/sprintf.js |

`sprintf-js`, fengari'nin `string.format` uygulamasının gerektirdiği tek
çalışma zamanı bağımlılığıdır.

## Yerel yamalar (VENDOR-PATCH)

fengari'nin iki dosyasına küçük, yalnızca tembellik (laziness) amaçlı yama
yapılmıştır; amaç, hiç kullanmadığımız geliştirme bağımlılıklarının (`tmp`,
`readline-sync`) VM yüklenirken zorunlu olmasını kaldırmaktır:

- `fengari/loslib.js` — `require('tmp')` artık `os.tmpname()` içinde tembel.
- `fengari/ldblib.js` — `require('readline-sync')` artık `debug>` REPL'i
  içinde tembel.

Bunların dışında kaynak **değiştirilmemiştir**. Yükseltme yapılacaksa:
`npm i fengari@<sürüm> && cp node_modules/fengari/src/*.js tools/vendor/fengari/`
ardından iki yamayı yeniden uygula (arama: `VENDOR-PATCH`).

## Kullanım

```bash
python3 tools/verify_runtime.py                    # gömülü fengari ile
EASYIMPORT_LUA_BIN=lua5.3 python3 tools/verify_runtime.py   # gerçek PUC Lua ile
EASYIMPORT_LUA_BIN=luau   python3 tools/verify_runtime.py   # Luau ile
```

`NODE_PATH` bu klasöre işaret edilerek çalıştırılır; Node buradan `fengari` ve
`sprintf-js` paketlerini çözer.
