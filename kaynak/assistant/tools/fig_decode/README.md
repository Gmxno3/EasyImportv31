# fig_decode — `.fig` arşivini Figma açmadan okuma

`designs/` klasöründeki 10 gerçek tasarım (`.fig`), `assistant/DURUM.md` §6'nın "gerçek veri
eksikliği" dediği boşluğu kapatıyor. Bu araç üç adımda o veriyi eğitim hattına sokar —
**Figma'ya hiç girmeden, tamamen offline ve deterministik.**

## Durum: ✅ ÇALIŞIYOR (10/10 dosya · 4.490 düğüm · 28 tasarım)

## Kurulum

```bash
cd assistant/tools/fig_decode
npm install          # fig-kiwi, kiwi-schema@0.5.0, pako
```

Gereksinim: **Node ≥ 22.15** (yerleşik `zlib.zstdDecompressSync`) ve `python3` (ZIP ayıklama).
`to_preview.py` **sıfır bağımlılıktır** (saf stdlib PNG yazıcı).

## Üç araç

| Araç | Ne yapar |
|---|---|
| `decode.mjs` | `.fig` → **ham kiwi düğümleri** (Figma'nın kendi alanları: `textData`, `fillPaints`, `transform`…) |
| `to_wispfree.mjs` | ham düğümler → **`wispfree v9` sözleşmesi** (eklentinin `walk()` çıktısı) + gerçek PNG'ler |
| `to_preview.py` | `wispfree` JSON → **PNG önizleme** (geometrik doğrulama; Figma thumbnail'ıyla karşılaştırılır) |

```bash
node decode.mjs ../../../designs/OS1File.fig --ozet              # özet
node decode.mjs ../../../designs/OS1File.fig -o /tmp/OS1.json   # ham mesaj
node to_wispfree.mjs ../../../designs/OS1File.fig -o /tmp/out    # sözleşme + PNG
python3 to_preview.py /tmp/out/*.json -o /tmp/onizleme           # görsel doğrulama
```

Hepsi birden (depo kökünden):

```bash
python3 assistant/tools/build_real_dataset.py    # designs/ → designs-export/ → real-exports.jsonl
```

## Format (tersine mühendislikle bulundu — bunlar olmadan çalışmaz)

```
.fig (ZIP)
├── canvas.fig      ← tasarım ağacı
├── thumbnail.png
├── meta.json       ← file_name, render_coordinates
└── images/<hash>   ← gömülü raster görseller (uzantısız)

canvas.fig = "fig-kiwi" + uint32(şema sürümü = 106)
             + deflateRaw( kiwi şeması, 619 tanım )
             + ZSTD( kiwi mesajı )          ← zstd! deflate değil
```

| Tuzak | Belirti | Çözüm |
|---|---|---|
| `kiwi-schema@0.4.7` | `Error: Invalid type -8` | **0.5.0** kullan — binary şema biçimi değişmiş |
| Mesaj gövdesi | `incorrect header check` | Gövde **zstd**: `28 b5 2f fd` → `zlib.zstdDecompressSync` |
| `ROUNDED_RECTANGLE` | Düğümler sessizce düşer | `.fig` bu tipi kullanır ama **Plugin API kullanmaz** → `RECTANGLE`'a eşle |
| Kök `transform` | Tüm kökler sayfa koordinatında kalır | `.fig` kökünün transform'u **sayfa** koordinatıdır; eklenti kökü (0,0)'a koyar |

Son iki madde **bulunması zor, etkisi büyük** hatalardı: ilki 2.537 düğümü (en büyük kütle)
tamamen düşürüyordu, ikincisi tüm tasarımları yanlış konuma koyuyordu.

## Eşleme doğruluğu — eklentiyle aynı mantık

`to_wispfree.mjs`, `figma-plugin-all-in-one/code.js`'in `walk()` fonksiyonunun **birebir
mantığını** izler: `kind` kararı, `safeFile` adlandırma, `radius:'full'`, yuvarlama `r2`,
renk ölçeği 0..255, relatif konum/rot, hayalet eleme, `_ignore`/`_exclude`, `clips`
(`frameMaskDisabled === false`), auto-layout (`stackMode` → `layout`), gölge listesi,
süs-grubu birleştirme (`isDecorGroup`), saf vektör grubu (`isPureVectorGroup`),
sarmalayıcı sadeleştirme (`isPlainWrapper`), maske (`isMaskNode`).

**`ei` yan kanalı** da üretilir: `.fig`, `originalImageWidth/Height` ve `scale` alanlarını
doğrudan verdiği için döşeme hücresi (`tileW/tileH/repX/repY`) ve `blendMode` **ölçümsüz**
hesaplanır. Bu kanal olmadan `style-rules.json`'un stud tespiti ölür (kanalları "ölçülmüş
döşeme geometrisi" ister).

### Bilinen farklar

| # | Eksik | Etkisi |
|---|---|---|
| 1 | `applyRenderBounds` | Efekt/gölge taşması olan düğümde konum birkaç px kayabilir |
| 2 | Figma düğüm export'u | Vektör PNG'leri üretilmez; `item.image` adı yazılır, dosya yoktur (raster görseller vardır) |
| 3 | `overflowDirection` | `.fig`'te alan **yok** → `scroll` üretilemez → ScrollingFrame örneği çıkmaz |
| 4 | node-id dedupe | Raster görseller içerik hash'i ile tekilleşir (eklenti `nodeSig` kullanır) |

## Çıkarılan veri

10 dosya → **28 tasarım** → **4.490 düğüm**. Karşılaştırma: eski eğitim verisi **152 satır**.

```console
$ python3 assistant/tools/build_real_dataset.py
  [i] 28 tasarım JSON'u · 71 görsel
  [i] 4490 örnek datasets/labels/real-exports.jsonl'e yazıldı
  [i] sınıf dağılımı: Frame=3268, ImageLabel=925, TextLabel=291, TextButton=4, ImageButton=2
```

Önizlemeler: `designs-export/onizleme/` — her tasarımın JSON'dan çizilmiş hâli. Figma
thumbnail'larıyla yan yana koyulduğunda geometri doğrulaması gözle yapılabilir.
