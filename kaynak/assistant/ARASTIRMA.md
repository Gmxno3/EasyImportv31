# EasyImport Asistan — Derin Araştırma Notları (Figma ↔ Roblox UI)

> Amaç: "Sistemi kurmadan önce iki tarafı da tam bilmek." Bu belge, modelin **ne öğreneceğini**
> belirleyen veri haritasıdır. Kaynaklar cümle sonlarında `[id](url)` olarak verilmiştir.
> Tarih: 2026-10-05.
>
> ⚠️ **Not:** Bu dosya bir betik hatasıyla bozuldu ve 2026-10-05'te yeniden kuruldu.
> İçerik aynı; bölüm sırası A→G, H (Luau teknik), I (Luau ek), J (öğrenme motoru).

---

## BÖLÜM A — FIGMA TARAFI: Okunabilir veri haritası

### A1. Düğüm tipleri (`node.type`) — sınıf kararıyla ilgili olanlar

| Tip | Anlamı | Roblox'ta karşılığı |
|---|---|---|
| `FRAME`, `COMPONENT`, `INSTANCE`, `COMPONENT_SET`, `SECTION` | Kap / kutu | `Frame`, `ScrollingFrame`, `CanvasGroup` |
| `RECTANGLE`, `ELLIPSE` | Şekil | `Frame` (+ `UICorner`), bazen `ImageLabel` |
| `TEXT` | Metin | `TextLabel` / `TextButton` / `TextBox` |
| `VECTOR`, `BOOLEAN_OPERATION`, `STAR`, `POLYGON`, `LINE` | Vektör çizim | **PNG'ye çizilir** → `ImageLabel` |
| `GROUP` | Eski tip grup | Genelde `Frame` veya şeffaflanır |

### A2. Boya (Paint) tipleri — `fills`, `strokes`

Figma'nın **dört** boya tipi var: `SOLID`, `GRADIENT_LINEAR`, `GRADIENT_RADIAL`,
`GRADIENT_ANGULAR`, `GRADIENT_DIAMOND`, `IMAGE` ve **yeni: `VIDEO`** [1](https://www.figma.com/widget-docs/api/type-Paint/) [2](https://staging.figma.com/plugin-docs/api/Paint/)

Her boya için okunacak alanlar:
- ortak: `type`, `visible`, `opacity`, `blendMode`
- `SOLID`: `color {r,g,b}` (0–1) — **not:** alpha paint'in `opacity`'sinde, `color.a` değil
- `GRADIENT_*`: `gradientStops[] {position, color}`, `gradientTransform` (2×3 matris)
- `IMAGE`: `imageHash`, `scaleMode` (`FILL`/`FIT`/`CROP`/`TILE`), `imageTransform`, `scalingFactor`,
  `rotation`, **yeni: `filters`** (exposure/contrast/saturation/temperature/tint/hue)
- `VIDEO`: video dolgusu — **Roblox'ta karşılığı `VideoFrame`**

> ⚠️ Mevcut `code.js` `convertPaints()` yalnızca `type/color/opacity/angle/stops/scaleMode`
> alıyor. `blendMode`, `imageHash`, `filters`, 4 gradient tipinin ayrımı, `VIDEO` **kayboluyor**.

### A3. Efektler (`node.effects`)

Figma efekt tipleri [3](https://developers.figma.com/docs/plugins/api/Effect/):

| Tip | Alanlar | Not |
|---|---|---|
| `DROP_SHADOW` | `color(RGBA)`, `offset{x,y}`, `radius`, `spread`, `visible`, `blendMode`, `showShadowBehindNode` | Roblox `UIShadow` ile **birebir** eşleşiyor |
| `INNER_SHADOW` | aynı | Roblox'ta **karşılığı yok** |
| `LAYER_BLUR` (Layer Blur) | `radius`, `visible`, `blurType: 'NORMAL' \| 'PROGRESSIVE'` | Katmanın kendisini bulanıklaştırır |
| `BACKGROUND_BLUR` | `radius`, `visible` | **Altındakileri** bulanıklaştırır (glass/acrylic) |
| `NOISE` | `color`, `noiseSize`, `blendMode`, (monotone/duotone/multitone) | Beta — Roblox'ta karşılığı yok |
| `TEXTURE` | doku | Beta — karşılığı yok |
| `GLASS` | cam | Beta — karşılığı yok |
| `SHADER` | özel shader | Beta — karşılığı yok |

`PROGRESSIVE` blur için ek: `startRadius`, `startOffset`, `endOffset`.

> ⚠️ Mevcut `code.js` **yalnızca `DROP_SHADOW`** okuyor.
>
> 🔴 **KULLANICI NOTU (çok önemli):** *"Figma efek tiplerinde Texture ve Effect'i bulamazsın,
> çünkü onları IMAGE olarak alıyoruz, bazen de frame'de biz yapıyoruz."*
> → Bu projede **doku ve efektler Figma `effects[]` dizisinden OKUNMAZ**. Hepsi **image katmanı**
> veya **frame** olarak gelir. Tespit yalnızca katman adı + blend mode + geometri + doku tekrarı
> + frame tabanlı shine ile yapılır. (Bkz. `anim/anim-library.json` → `_fxDetection`.)

### A4. Çizgi (stroke) özellikleri — "kalınlık" isteğinin kaynağı

`strokes[]`, `strokeWeight` (veya `figma.mixed`), `strokeAlign` (`INSIDE`/`CENTER`/`OUTSIDE`),
`strokeJoin` (`MITER`/`BEVEL`/`ROUND`), `strokeCap` (`NONE`/`ROUND`/`SQUARE`/`ARROW_*`),
`dashPattern[]`, `strokeTopWeight`/`Bottom`/`Left`/`Right` (kenar kenar farklı kalınlık!),
`strokeMiterLimit`, `outlineStroke`, `variableWidthStrokeProperties`, `strokesIncludedInLayout`
[4](https://www.figma.com/plugin-docs/api/node-properties/)

> ⚠️ Mevcut kod yalnızca `strokeWeight` + `strokeAlign` alıyor; **kenar kenar kalınlık, dash,
> join/cap** kayboluyor.

### A5. Köşe yarıçapı

`cornerRadius` (veya `figma.mixed`), `topLeftRadius`, `topRightRadius`, `bottomLeftRadius`,
`bottomRightRadius`, `cornerSmoothing` (iOS squircle), `rectangleCornerRadii`
[4](https://www.figma.com/plugin-docs/api/node-properties/)

### A6. Metin özellikleri

Mevcut kodun aldıkları: `characters`, `fontSize`, `fontName{family,style}`, `fills`,
`textAlignHorizontal`, `textAlignVertical`, `textAutoResize`, `textCase`, `textDecoration`,
`lineHeight`, `strokes`, `effects`, `getStyledTextSegments`.

**Alınmayanlar (model için değerli):** `letterSpacing`, `paragraphSpacing`, `paragraphIndent`,
`textTruncation`, `maxLines`, `leadingTrim`, `textStyleId`, `openTypeFeatures`,
`textDecorationColor/Offset/SkipInk/Style/Thickness`, `hyperlink`, `listSpacing`, `textWrapStyle`.

### A7. Auto Layout (Figma) → Roblox düzen

`layoutMode`, `itemSpacing`, `counterAxisSpacing`, `layoutWrap`,
`paddingLeft/Right/Top/Bottom`, `primaryAxisAlignItems` (`MIN`/`MAX`/`CENTER`/`SPACE_BETWEEN`),
`counterAxisAlignItems`, `counterAxisAlignContent`, `layoutGrow`, `layoutAlign`,
`layoutPositioning` (`AUTO`/`ABSOLUTE`), `layoutSizingHorizontal/Vertical` (`FIXED`/`HUG`/`FILL`),
`numberOfFixedChildren`, `itemReverseZIndex`, `inferredAutoLayout`
[4](https://www.figma.com/plugin-docs/api/node-properties/)

> ⚠️ Mevcut kod `layoutGrow`, `layoutSizing*`, `layoutAlign`, `numberOfFixedChildren` almıyor.

### A8. Diğer

`opacity`, `visible`, `blendMode` (NORMAL/MULTIPLY/SCREEN/OVERLAY/DARKEN/LIGHTEN/COLOR_DODGE/
COLOR_BURN/HARD_LIGHT/SOFT_LIGHT/DIFFERENCE/EXCLUSION/HUE/SATURATION/COLOR/LUMINOSITY/
PASS_THROUGH/LINEAR_DODGE/LINEAR_BURN/LINEAR_LIGHT), `clipsContent`, `isMask`, `maskType`,
`constraints`, `rotation`, `absoluteRenderBounds`, `exportSettings`, `boundVariables`
(Figma **değişkenleri** = tasarım token'ları), `componentPropertyReferences`,
`fillGeometry`/`strokeGeometry`, `reactions`.

> 💡 `boundVariables` = Figma değişkenleri. Roblox'un yeni **StyleSheet/StyleAttribute**
> sistemine birebir karşılık gelir. Uzun vadeli hedef: Figma değişkeni → Roblox tasarım token'ı.

---

## BÖLÜM B — ROBLOX TARAFI: Sınıflar, özellikler, **yeni yetenekler**

### B1. Çekirdek UI sınıfları

| Sınıf | Ne zaman | Kritik özellikler |
|---|---|---|
| `Frame` | Kap, arka plan, panel | `BackgroundColor3`, `BackgroundTransparency`, `ClipsDescendants` |
| `TextLabel` | Salt metin | `Text`, `TextSize`, `FontFace`, `TextColor3`, `TextX/YAlignment`, `TextWrapped`, `TextScaled`, `TextTruncate`, `MaxVisibleGraphemes`, `RichText`, `LineHeight`, `TextStrokeColor3/Transparency`, `OpenTypeFeatures`, `AutomaticSize` |
| `TextButton` | Metinli buton | TextLabel + `GuiButton.AutoButtonColor` |
| `TextBox` | Girdi | + `PlaceholderText`, `ClearTextOnFocus`, `MultiLine`, `TextEditable`, `ShowNativeInput` |
| `ImageLabel` | Görsel | `Image`(Content), `ImageColor3`, `ImageTransparency`, `ScaleType` (Stretch/Tile/Slice/Fit/Crop), `SliceCenter`, `SliceScale`, `TileSize`, `ImageRectOffset/Size`, `ResampleMode` |
| `ImageButton` | Görsel buton | ImageLabel + `HoverImage`, `PressedImage` |
| `ScrollingFrame` | Kaydırma | `CanvasSize`, `AutomaticCanvasSize`, `ScrollingDirection`, `ScrollBarThickness`, `ScrollBarImageColor3`, `ElasticBehavior`, `ScrollBarInset`, `TopImage/MidImage/BottomImage` |
| `CanvasGroup` | Grup şeffaflığı | `GroupColor3`, `GroupTransparency` — **riskli, B4'e bak** |
| `ViewportFrame` | 3D önizleme | `Ambient`, `LightColor`, `LightDirection`, `ImageColor3`, `ImageTransparency` |
| `VideoFrame` | Video | Figma `VIDEO` dolgusunun karşılığı |
| `Path2D` | 2D yol çizimi | `Closed`, `Color3`, `Thickness`, `ZIndex` |
| `InputActionLabel` | Tuş/ipuç göstergesi | metin + görsel |

Kaynak: [5](https://create.roblox.com/docs/ui/styling/compatibility)

### B2. Görünüm değiştiriciler (appearance modifiers)

**`UICorner`** — `CornerRadius: UDim` + **YENİ:** `TopLeftRadius`, `TopRightRadius`,
`BottomLeftRadius`, `BottomRightRadius` (her köşe ayrı!) [5](https://create.roblox.com/docs/ui/styling/compatibility)
- `Scale ≥ 0.5` → **pill** şekli · `Offset` → piksel

**`UIStroke`** — `Color`, `Thickness`, `Transparency`, `ApplyStrokeMode` (`BORDER`/`TEXT`/`CONTEXTUAL`),
`LineJoinMode` (`ROUND`/`BEVEL`/`MITER`), `Enabled` [6](https://create.roblox.com/docs/ui/appearance-modifiers)
- Metin objesine eklenirse **metin konturu**, diğerlerine **kenarlık** olur
- Altına `UIGradient` koyarak **gradient kenarlık** yapılabilir

**`UIGradient`** — `Color: ColorSequence`, `Transparency: NumberSequence`, `Rotation` (derece,
**saat yönü**, soldan sağa 0°), `Offset: Vector2`, `Scale`, `Type` (Linear/Radial), `TileMode`, `Enabled`
[7](https://robloxapi.github.io/ref/class/UIGradient.html)
- ⚠️ **Desteklenen:** Frame, TextLabel, TextButton, ImageLabel, ImageButton, Path2D, ViewportFrame
- ❌ **Desteklenmeyen:** `ScrollingFrame` ve `TextBox`
- ⚠️ 6'dan fazla renk durağı önerilmez · ⚠️ `TextStrokeColor3` ile birlikte kullanmayın

**`UIShadow` — 2026'da tam sürüme çıktı, ÇOK ÖNEMLİ** [8](https://devforum.roblox.com/t/full-release-new-ui-capabilities-shadows-individual-corners/4636263) [9](https://robloxapi.github.io/ref/class/UIShadow.html)
- `BlurRadius: UDim` (scale = **kısa kenara** göre), `Color`, `Transparency`, `Offset: UDim2`,
  `Spread: UDim2`, `Enabled`, `ZIndex` (**negatif olmalı**)
- Ebeveyn dönerse gölge de döner; `UICorner` varsa gölge de yuvarlak olur
- Bir objede **birden fazla** UIShadow olabilir (katmanlı gölge / glow)
- ❌ **Metni desteklemez** — TextLabel'a eklersen **dikdörtgen kutunun** gölgesini verir
- ❌ **İç gölge (inset) yok** · ❌ `Path2D` desteklemiyor
- 💡 `Transparency` düşük + `BlurRadius` yüksek + `Spread` negatif → **glow / parlama**

**`UIPadding`** — `PaddingTop/Bottom/Left/Right: UDim` ← Figma `padding*`
**`UIScale`** — `Scale` (animasyonların ana hedefi)
**`UIAspectRatioConstraint`**, **`UISizeConstraint`**, **`UITextSizeConstraint`**
**`UIListLayout`** — `Padding`, `HorizontalPadding`, `VerticalPadding`, `Wraps`, `ItemLineAlignment`,
`HorizontalFlex`/`VerticalFlex` (`NONE`/`FILL`/`SPACE_AROUND`/`SPACE_BETWEEN`/`SPACE_EVENLY`)
**`UIGridLayout`** — `CellSize`, `CellPadding`, `FillDirectionMaxCells`, `StartCorner`
**`UITableLayout`**, **`UIPageLayout`** (animasyonlu geçişler)
**`UIFlexItem`** — `FlexMode`, `GrowRatio`, `ShrinkRatio`, `ItemLineAlignment` ← Figma `layoutGrow`
**`StyleQuery`** — koşullu kırılma noktaları: `MinSize`, `MaxSize`, `AspectRatioRange`,
`PreferredInputType`, `ViewportDisplaySize`, `ReduceMotionEnabled` ← **responsive tasarım**

### B3. 🔴 Kritik boşluklar — Figma'da var, Roblox'ta YOK

| Figma | Roblox durumu | Önerilen davranış |
|---|---|---|
| **Background Blur** (glass/acrylic) | **YOK.** `BlurEffect` tüm ekranı etkiler ve **UI'yı etkilemez** [10](https://devforum.roblox.com/t/ui-acrylic-glasspostprocessing-blur-on-canvasgroups-images/1778436) | ⛔ **Çözüm üretmiyoruz** — kullanıcı kararı: desteklenmeyen efektler için Roblox tarafı taklidi yok, import tarafı zaten PNG ile çözüyor |
| **Layer Blur** | **YOK** | ⛔ aynı |
| **Inner Shadow** | **YOK** (UIShadow inset desteklemiyor) | ⛔ aynı |
| **Metin gölgesi** | **YOK** — UIShadow metinde dikdörtgen kutu verir [9](https://robloxapi.github.io/ref/class/UIShadow.html) | ⛔ aynı |
| **Blend Mode** (Multiply, Screen, Overlay…) | **YOK** | ⛔ aynı |
| **Dash pattern** | **YOK** | ⛔ aynı |
| **Noise / Texture / Glass / Shader** | **YOK** (ayrıca bu UI'larda Figma efekti olarak da yok — PNG geliyor) | ⛔ aynı |
| **Gradient** → `ScrollingFrame`/`TextBox` | **ÇALIŞMIYOR** [7](https://robloxapi.github.io/ref/class/UIGradient.html) | ⚠️ Düz renge düşür + uyarı (import kararı değil, model özelliği) |
| **Maske** (`isMask`) | Kısmen | Mevcut `_mask` mantığı korunur |
| **Değişken genişlikli çizgi** | **YOK** | ⛔ aynı |
| **Figma fontları** | Roblox'ta sınırlı font var | Font eşleme tablosu (model öğrenir) |

### B4. ⚠️ CanvasGroup tuzağı

- Tam ekran (`Size = {1,0,1,0}`) `CanvasGroup` **bulanık görünür** [11](https://devforum.roblox.com/t/canvasgroups-are-blurry-when-set-to-1010/2136621/7)
- Bellek baskısında **çözünürlük düşürme (down-res) fallback** → cihazdan cihaza farklı görünür
- `ZIndexBehavior = Global` sorunu azaltıyor ama `GroupTransparency`/`GroupColor3` kilitlenebiliyor
- **Sonuç:** CanvasGroup'u **yalnızca** grup şeffaflığı gerektiğinde ve **küçük alanlarda** kullan.

### B5. Font eşlemesi

Roblox font varlıkları: `rbxasset://fonts/families/GothamSSm.json`, `BuilderSans`,
`SourceSansPro`, `Roboto`, `RobotoMono`, `Montserrat`, `Merriweather` + Creator Store'dan
eklenenler (Inter, Open Sans, Nunito, Fira Sans, DotGothic16, Noto Sans, Lobster, Pacifico vb.)
[12](https://www.mintlify.com/AlroviOfficial/rbx-css/mapping/fonts) [13](https://github.com/Shuiux/Roblox-Builder-Fonts)
- `FontFace = Font.new(family, Enum.FontWeight.Regular, Enum.FontStyle.Normal)`
- Ağırlıklar: Thin100 … Regular400 … SemiBold600 … Bold700 … ExtraBold800
- ⚠️ **Gotham ve Arial 28 Mayıs 2024'te kaldırıldı** → Montserrat / Arimo'ya düştü
[14](https://www.designyourway.net/blog/what-font-does-roblox-use/)
- 💡 Mevcut `FONT_FAMILY_MAP` Lua'da var — model bunu da öğrenebilir.

---

## BÖLÜM C — "Stil" kavramı: model ne öğrenecek?

### C1. ⭐ STİL TARİFLERİ — SENİN TANIMIN

> Kaynak: kullanıcı tarifi, 2026-10-05. Ölçülebilir sinyaller `spec/style-rules.json` içinde.

#### 🥇 STUD — **kesin kural, en yüksek öncelik**
> *"Stud olan her GUI Stud stildir. Stud kullanılmışsa Stud'a girer."*

Bu bir **sınıflandırma değil, tespit**tir: **stud varsa → Stud.** Override edilemez, güven 1.0.

#### 🥈 ANIME — **en iyi ışıklandırma, en yüksek detay, koyu + çok renk**
> *"Görünüşü çok iyi olması için çok fazla detay verilmiş. En iyi ışıklandırma stilidir.
> Genellikle efektler çoktur, texturelar ortadır."*
> *"Genellikle koyu renk ve birden fazla renkli olur. Çoğu renk kapalı olur, çünkü ışıklandırma
> yaptığında en verimli en güzel gözükür. Efektler tam ideal olur."*

#### 🥉 CARTOON — **doku ağırlıklı, efekti az**
> *"Texture'den olan, pek fazla efekti olmayan GUI'dir."*
> *"Birden fazla texture olabilir, efekt de olabilir ama genellikle azdır."*

#### 🔑 Ayırt etme sırası
```
1. hasStud ?                      -> STUD     (kesin, güven 1.0, override yok)
2. ışık + detay + koyuluk yüksek   -> ANIME
3. doku yüksek & efekt/detay az    -> CARTOON
4. ikisi de zayıf                  -> "belirsiz" (stil önceliği uygulanmaz, model nötr kalır)
```

#### ⚠️ İlk hipotezimde NELER YANLIŞTI
| İlk tahminim | Gerçek |
|---|---|
| Cartoon = kalın kontur (3–8 px) | ❌ Cartoon'un ayırt edicisi **doku**, kontur değil (C6: "çok fazla yok") |
| Anime = keskin köşe, ince font | ❌ Anime'nin ayırt edicisi **ışıklandırma + detay + koyuluk** |
| Stud = "çok kalın koyu kontur, primer renkler" | ❌ Stud bir **tespit**tir, görünüm kalıbı değil |
| Üçü aynı özellik uzayında yarışır | ❌ Stud önce ayrılır; Anime/Cartoon **farklı eksenlerde** (ışık ↔ doku) |

### C1b. TUR 2 — Ek açıklamalar (ölçülebilir sinyallere çevrildi)

#### 🎨 ANIME — renk davranışı
Anime'nin mantığı: **koyu + kapalı (düşük doygunluk/parlaklık) taban → üzerinde ışık/efekt patlar.**

| Sinyal | Formül | Anime'de |
|---|---|---|
| `darknessIndex` | `1 − ortalama(dolgu VALUE)` | **yüksek (> 0.55)** |
| `mutedBaseRate` | kapalı dolgu / toplam — kapalı = `sat < 0.35 && val < 0.50` | **yüksek (> 0.50)** |
| `hueDiversity` | %2'den fazla pay alan hue kovası / 12 | **yüksek (> 0.35)** |
| `accentPopRate` | küçük + yüksek doygunluklu öğe / toplam öğe | orta-yüksek |

#### 🧱 STUD — tespit detayları
> *"UI için stud, header için stud, menüler için stud — birden fazla aynı şeyi kullanmışsa.
> Size ve boyutundan da anlaşılıyor."* · *"Image kullanarak yapılmış UI stud olma ihtimali
> yüksektir. Çoğu zaman efek yoktur. Texture'si stud olduğundan başka texture kullanılmaz.
> Efekt kullanabilir — en sık **shine**. Shine'ı **Frame ile** yaparlar. Button ve header'da
> stud texture **olmazsa olmazıdır**. Genellikle **3D yapmaya çalışırlar: aynı rengin
> kapalısını altta geçirerek**."*

| Sinyal | Açıklama | Stud'da |
|---|---|---|
| `reuseRate` | Aynı image dosyasının kaç yerde kullanıldığı (**plugin'in dedupe hash'i bedava veriyor**) | **yüksek (> 0.5)** |
| `imageDrivenRate` | UI'nin ne kadarı image'dan yapılmış | **yüksek (> 0.5)** |
| `onButtonOrHeader` | Stud texture button **veya** header üzerinde | **ZORUNLU** ("olmazsa olmazı") |
| `tileCellSize` | Döşeme hücresi küçük + tutarlı | karakteristik |
| `noOtherTexture` | Stud dışında doku yok | ≈ 0 çeşit |
| `darkerUnderlayRate` | **3D: alttaki katman üsttekiyle aynı hue, daha düşük value** | var |
| `shineFrameRate` | **Shine bir FRAME ile** yapılır (yarı saydam/gradyanlı, üstte binen) | var |
| `effectDensity` | Efekt yoğunluğu | **çok az (≤ 0.25)** |

#### 📐 DETAY SEVİYELERİ
> *"Cartoonda çok fazla yok, Anime'de detay fazladır, Stud orta-düşük derece, efekti olan basit
> bir stildir."*

| Stil | Detay | Efekt | Doku |
|---|---|---|---|
| **Anime** | **YÜKSEK** (≥ 0.55) | **ÇOK** (≥ 0.60) | Orta (0.20–0.70) |
| **Stud** | **ORTA / DÜŞÜK** (0.25–0.50) | **ÇOK AZ** (≤ 0.25, genelde sadece shine) | Tek doku = stud |
| **Cartoon** | **DÜŞÜK** (≤ 0.35) | Az (≤ 0.40) | **Yüksek, birden fazla olabilir** |

#### ⚡ İKİ YENİ **SINIF ATAMA** SİNYALİ (stil değil — asistanın 1. işi)

1. **3D underlay:** aynı hue'nun daha koyusu altta → alt katman **ayrı bir sınıf değil**, `Frame`
   olarak kalmalı (süs). Üstteki asıl eleman (`ImageButton`/`ImageLabel`).
   Tespit: `|Δhue| < 12° AND V_alt < V_üst × 0.8 AND kutular biniyor`.
2. **Shine Frame:** buton/panel üstüne bindirilmiş yarı saydam/gradyanlı ince FRAME → bir kap
   değil, **FX katmanı**. `Frame` olarak sınıflandırılmamalı; `fx_shine_sweep` animasyonu almalı.

### C1c. TUR 3 — **STUD TESPİTİ ARAŞTIRMASI** (2026-10-06)

> Soru: "Asistan stud'u nasıl anlayacak?" Tek doğru cevap **isim değil**: tasarımcı katmana
> "stud" yazmayabilir. Araştırma üç kanal buldu — **geometri**, **tekrar** ve **stüdyo gelenekleri**.

#### 1) Stud dokusu nedir, nasıl görünür (kaynak: Roblox tarihi + topluluk)
- Stud'lar **kare** bir döşeme hücresinin içinde **yuvarlak kabartma** olarak çizilir.
  Tarih: 2006–2009 **yuvarlak** stud ("LEGO benzeri", ortada R), 2009–Ekim 2013 **kare + R**,
  Ekim 2013–Ocak 2017 normal map'li kare, 2017+ **markasız kare**. *(roblox.fandom "Studs (surface)",
  classic-roblox.fandom "Textures")*
- Klasik baseplate dokusu **4×4 stud**'luk tek bir resimdir; `StudsPerTileU/V = 4` ile döşenir.
  Topluluk 5×5 varyantı da üretir (`StudsPerTileU/V = 10`, ayrı doku kimliği).
  Güncel doku kimlikleri: `rbxassetid://18878365966` (stud), `rbxassetid://6372755229` (ızgara).
  *(DevForum: "Where can I get TEXTURES of the studs…", "Baseplate texture grid 5x5 studs")*
- Yani: **stud dokusu = küçük + kare + kesintisiz (seamless) + tekrar eden**. Uygulama tarafında
  Roblox'ta `Texture.StudsPerTileU/V`, UI'da ise **`ImageLabel.ScaleType = Tile` + `TileSize`**
  (genelde offset = dokunun doğal boyutu, tipik 64–256 px) karşılığıdır.
  *(Roblox API: ImageLabel.TileSize; DevForum "Texture Mapping On ImageLabels")*
- ⚠️ Topluluk uyarısı: döşeme hücresi çok küçükse (ör. 2 px) Roblox binlerce karo çizer →
  gerçek tasarımlarda hücre **8–96 px** bandındadır. Bu bant, bizim "stud ölçüsü" testimizin temeli.

#### 2) Klasiğin ayırt edici gelenekleri (kullanıcı tarifiyle örtüşüyor)
| Gelenek | Ölçülebilir karşılığı |
|---|---|
| Buton + header + menü **aynı** stud dokusunu kullanır | `reuseRate` yüksek, **benzersiz doku sayısı 1–2** |
| "Başka texture kullanılmaz" | `nUniqueImages` küçük; karışık doku → **veto** |
| 3D görünüm: aynı rengin koyusu **altta** | `darkerUnderlayRate` (var/yok) |
| Efekt "çok az", en sık **shine** — shine bir **FRAME** ile yapılır | `shineFrameRate`, `effectDensity ≤ 0.25` |
| Butonda **~3×3 stud** görünür ("size ve boyutundan anlaşılıyor") | hücre px → `round(w/hücre) ∈ 2..8` |
| Modern "studded UI" paketleri stud'u **ikon/rozet** olarak da kullanır | tek ikon **stud değildir** (aşağıdaki tuzak) |

Modern kullanım kanıtı: BuiltByBit'te satılan "Studded UI / Studs UI Pack"lerin çoğu, stud
katmanını bir **BoolValue "Studs"** ile açıp kapatır; ayrıca "Studs Icon Pack" gibi yalnızca
**ikon** satan paketler var. Figma tarafında "How to make a Studs HUD on FIGMA" gibi eğitimler
hazır bir **stud PNG**'sini döşemeyle kullanmayı öğretir. *(builtbybit studs etiketi; YouTube)*

#### 3) Figma'dan ölçüm: döşeme hücresi **hesaplanabilir**
- `ImagePaint.scaleMode ∈ FILL | FIT | CROP | TILE`; **`scalingFactor` yalnızca TILE'da anlamlıdır**
  ("determines the scaling (thus, repetition) of the image within the layer"). Figma arayüzü bunu
  "orijinal boyutun yüzdesi" olarak gösterir. *(Figma Plugin API: ImagePaint; Figma Help: Tile)*
- `figma.getImageByHash(hash)` → `Image.getSizeAsync()` (px) ve `getBytesAsync()` (ham bayt).
  Görseller en çok **4096 px**; `getSizeAsync` bazen reddeder ("Image dimensions not available",
  dev VM'de "This VM has been destroyed") → **her çağrı try/catch + önbellek** olmalı.
  *(Figma Plugin API: Image; Working with Images; forum başlıkları)*
- **Sonuç formülü:** `hücre_px = görsel_px × scalingFactor` (TILE'da) → stud ölçüsü **ölçülmüş** olur,
  isim tahminine gerek kalmaz. Aynı sayı Studio'ya birebir taşınır: `TileSize = UDim2.fromOffset(hücre)`.
- Uygulama: `figma-plugin-all-in-one/code.js` artık `item.ei` yan kanalına şunları yazar:
  `imageW/imageH`, TILE'da `sf` + `tileW/tileH` (+ `repX/repY`), ve blend modu (`SCREEN/ADD…`).
  Ölçüm yoksa alan **hiç eklenmez** → `ei` yokken v9 davranışı aynen korunur.

#### 4) İsim kanıtı: güçlü / zayıf ayrımı (öğrenilen ders)
- **Güçlü** (doğrudan stud): `stud, studs, studded, studtexture, studpattern, studtile, studbg,
  studsui, studs3x3` + Türkçe `civi, civili`.
- **Zayıf** (tek başına YETMEZ): `brick, tugla, texture, pattern, desen` — bunlar duvar/ahşap
  dokusunda da geçer. Eski kuralda `texture` ve `pattern` güçlü sayılıyordu; bu, düz dokulu
  her tasarımı stud yapma riski taşıyordu.
- **Tek düğümde "stud" adı da yetmez**: modern paketlerde tek bir **stud ikonu** olabilir.
  Kural: ad kanıtı ≥ 2 düğümde **veya** ad + ölçülmüş döşeme geometrisi birlikte.

#### 5) NEGATİF örnekler (yanlış pozitifi kilitleyen testler)
| Durum | Neden stud DEĞİL | Test |
|---|---|---|
| Tek **stud ikonu** (döşenmiyor) | Doku değil, rozet; stud stili değil | `stud-icon.json` → **belirsiz** (sert kural) |
| Ahşap/doku **karışık** cartoon menü | `nUniqueImages > 3` → "başka texture kullanılmaz" ihlali | `cartoon-menu.json` → **cartoon** |
| Anime HUD (yoğun efekt) | `effectDensity > 0.60` → veto | `anime-hud.json` → **anime** |
| Aynı görseli 2 kez kullanan sade menü | Ölçülmüş döşeme yok, ad kanıtı yok | kanıt < 4 → **belirsiz** |

#### 6) Uygulanan tespit merdiveni (kanıt + veto) — `detect.stud.v3`
```
GÜÇLÜ  +3 : ad kanıtı (≥2 düğüm VEYA ad + ölçülmüş döşeme)
GÜÇLÜ  +3 : buton/header üzerinde KÜÇÜK KARE ölçülmüş döşeme hücresi
DESTEK +1 : doku tekrarı · tek doku (≤2) · image ağırlıklı · döşemenin yaygınlığı · tek hücre ölçüsü · 2..8 stud sığması
DESTEK +0.5: shine katmanı · 3D alt katman · az efekt · orta-düşük detay
VETO      : >3 benzersiz doku VEYA efekt > 0.60 VEYA detay > 0.62
KARAR     : güçlü ad  VEYA  (kanıt ≥ 4  VE  veto yok  VE  geometri/zayıf ad/döşeme yaygınlığı var)
```
Sonuç: `stud-market` **kanıt 18/20** · `stud-unnamed` (adında hiç "stud" yok) **20/20** ·
`stud-icon` **veto** · cartoon/anime/edge etkilenmedi. Kalibrasyon **6/6**.

#### 7) Bir sonraki adım (henüz yapılmadı — gerekçesiyle)
İsim ve geometri de yoksa **piksel kanıtı** kullanılabilir: `getBytesAsync()` → UI iframe'inde
canvas → (a) **kenar sürekliliği** (sol/sağ, üst/alt sütun farkı: dokunun kesintisiz olduğunun kanıtı),
(b) **özilinti (autocorrelation)** ile baskın periyot = stud adımı. Literatür, az sayıda tekrar
içeren desenlerde özilintinin Fourier'den daha uygun olduğunu söyler (Liu vd., *A Computational
Model for Periodic Pattern Perception*; Stack Overflow özilinti örnekleri). Bu kanal şimdilik
**kapalı**: Figma'da `getBytesAsync` asenkron + dev VM'de kırılgan, ayrıca her görseli indirmek
büyük dosyalarda yavaş. Ölçülmüş hücre + tekrar çoğu gerçek dosyada yeterli; gerekirse açılır.

### C2. Model mimarisi önerisi (stil için)
1. **GUI düzeyi özet vektörü** (~40 özellik): kontur kalınlığı dağılımı, köşe yarıçapı dağılımı,
   renk paleti (HCL histogramı — 12 kova), doygunluk/parlaklık dağılımı, gölge ofset/blur oranı,
   font ağırlığı dağılımı, gradient kullanım oranı, öğe boyutu dağılımı.
2. **Stil sınıflandırıcısı** → `style ∈ {stud, anime, cartoon, belirsiz}`
3. **Stil → öneri profili:** stil tahmini, sınıf/animasyon önceliklerini **değiştirir**.
4. **Stil bilgisi tek cümlede:** *"%86 Anime: koyu taban (0.63) + kapalı renkler (0.58) + 8 ayrı
   renk + güçlü ışıklandırma (0.74) + yüksek detay (0.68)."*

---

## BÖLÜM D — Genişletilmiş özellik listesi

Plan'da ~165 özellik vardı. Araştırma sonrası eklenen gruplar:

| Grup | Sayı | İçerik |
|---|---|---|
| **I. Efektler** | ~18 | `nDropShadow`, `shadowOffsetX/Y`, `shadowBlur/minDim`, `shadowSpread`, `shadowAlpha`, `shadowIsMulti`, `hasInnerShadow`, `hasLayerBlur`, `hasBackgroundBlur`, `hasNoise/Texture/Glass/Shader`, `hasGlowPattern` |
| **J. Renk istatistikleri** | ~16 | `fillHue/Sat/Val`, `fillIsDark`, `fillIsNeon`, `strokeHue/Sat/Val`, **`strokeIsDarkerThanFill`** (çizgi film göstergesi!), `contrast(fill,stroke)`, `paletteBucket` (12 kova), `nDistinctColors`, `hasGradient`, `gradientStopCount`, `gradientAngleBucket` |
| **K. Kalınlık / kontur** | ~10 | `strokeWeight/minDim` (log), `strokeWeightBucket` (0, 1-2, 3-5, 6-10, 10+), `strokeIsPerSideDifferent`, `strokeDash`, `strokeJoinRound/Bevel/Miter`, `borderRatio`, `hasStrokeAndRadius`, `strokeAlign_*` |
| **L. Kompozisyon / konum** | ~8 | `cornerRegion` (9 bölge one-hot), `isTopRightCorner`, `isBottomCenter`, `distanceToCorner`, `isFullWidth/Height`, `isCenteredX/Y` |
| **M. İçerik** | ~6 | `hasTextChild`, `hasImageChild`, `textCharCount/boxArea` (metin yoğunluğu), `textIsOnlyChild`, `imageIsOnlyChild`, `hasTextAndImage` |
| **N. Stil önceliği** (GUI düzeyi) | ~6 | `styleStud`, `styleAnime`, `styleCartoon`, `styleBelirsiz`, `styleConfidence` |
| **O. Stil sinyalleri** (v2'den) | ~8 | `reuseRate`, `imageDrivenRate`, `darkerUnderlayRate`, `shineFrameRate`, `darknessIndex`, `mutedBaseRate`, `hueDiversity`, `accentPopRate` |

**Yeni toplam: ~240 özellik.** Lua'da öğe başına ~240×14 = 3.360 çarpım → ~0.2 ms. Sorun değil.

---

## BÖLÜM E — Eğitim verisi çıktısı: `EI_<Ad>_egitim.json`

İstendiği gibi: kullanıcı JSON alırken **ayrı bir eğitim dosyası** da alsın.

> **Güncel karar (2026-10-08, KARARLAR.md §2.2): eğitim dosyasında KIRPMA YOK.**
> Aşağıdaki örnekte `figmaFileKey`/`figmaFileName`/`pageName` alanları `null` görünüyor —
> bu ilk taslağın gizlilik varsayımıydı, karar ile çelişir. Gerçek kural: üretilen veride
> **hiçbir alan kırpılmaz** — katman adları, geometri, renk, stil, tasarım/export adları hepsi
> kalır (gerçek veri: `datasets/labels/real-exports.jsonl`, export adlarıyla birlikte).
> Figma dosya anahtarı gibi kimlik alanları kaynakta hiç üretilmez — bu kırpma değil,
> hiç toplanmamadır. Cihazdan çıkış kullanıcının isteğine bağlıdır (karar 12: sunucu yok).

```jsonc
{
  "format": "ei-training", "version": 1,
  "exportedAt": "2026-10-05T12:00:00Z",
  "pluginVersion": "6.0.0",
  "figmaFileKey": null,          // GİZLİLİK: dosya anahtarı ALINMAZ
  "figmaFileName": null,         // GİZLİLİK: dosya adı ALINMAZ
  "pageName": null,              // GİZLİLİK: sayfa adı ALINMAZ
  "canvas": { "w": 1920, "h": 1080, "scaleClass": "auto" },
  "nodes": [
    {
      "path": "0.2.5",                    // deterministik yol (id değil)
      "type": "FRAME",
      "name": "Play_Button",
      "box": { "x":820, "y":640, "w":420, "h":96, "rot":0 },
      "opacity": 1, "visible": true, "blendMode": "PASS_THROUGH",
      "clipsContent": true, "isMask": false,
      "corner": { "r": 24, "tl":24, "tr":24, "bl":24, "br":24, "smoothing": 0 },
      "fills":  [ { "type":"SOLID", "color":{"r":0.1,"g":0.5,"b":0.9}, "opacity":1, "blendMode":"NORMAL" } ],
      "strokes":[ { "type":"SOLID", "color":{"r":0,"g":0,"b":0}, "opacity":1 } ],
      "stroke": { "weight":4, "align":"INSIDE", "join":"ROUND", "cap":"NONE",
                  "dash":[], "perSide":{ "t":4,"r":4,"b":4,"l":4 } },
      "effects":[
        { "type":"DROP_SHADOW", "color":{"r":0,"g":0,"b":0,"a":0.35}, "offset":{"x":0,"y":6}, "radius":12, "spread":0, "blendMode":"NORMAL" },
        { "type":"BACKGROUND_BLUR", "radius":16, "visible":true, "blurType":"NORMAL" }
      ],
      "image": { "ref":"Play_Button_12-34.png", "hash":"a1b2c3", "scaleMode":"FILL", "tile":null, "reuseCount":1 },
      "text": { "characters":"PLAY", "fontSize":32, "font":{"family":"Builder Sans","style":"ExtraBold"},
                "weight":800, "italic":false, "alignH":"CENTER", "alignV":"CENTER",
                "letterSpacing":0.5, "lineHeight":{"unit":"PIXELS","value":38},
                "autoResize":"NONE", "textCase":"UPPER", "decoration":"NONE",
                "truncation":"DISABLED", "maxLines":null, "nLines":1 },
      "layout": { "mode":"HORIZONTAL", "gap":12, "wrap":false, "padding":{ "l":16,"r":16,"t":8,"b":8 },
                  "primary":"CENTER", "counter":"CENTER", "grow":0, "sizingH":"FIXED", "sizingV":"FIXED" },
      "parentPath": "0.2", "siblingIndex": 1, "nSiblings": 3, "depth": 2,
      "label": { "cls": null, "thickness": null, "radius": null, "style": null, "anim": null, "src": null }
      // ↑ sen dolduracaksın: label_tool.py ile
    }
  ],
  "guiSummary": {
    "nNodes": 148,
    "strokeThickness": { "median":4, "iqr":[3,6], "max":10 },
    "cornerRadius":    { "median":16, "iqr":[8,32], "pillRatio":0.22 },
    "shadow":          { "usageRate":0.41, "medianOffset":[0,6], "medianBlur":12 },
    "colorHistogram":  [ /* 12 kova */ ],
    "fontWeight":      { "median":700 },
    "gradientUsage":   0.18,
    // ↓ v2 stil sinyalleri
    "reuseRate":       0.62,
    "imageDrivenRate": 0.71,
    "darkerUnderlayRate": 0.08,
    "shineFrameRate":  0.04,
    "darknessIndex":   0.34,
    "mutedBaseRate":   0.29,
    "hueDiversity":    0.33,
    "effectDensity":   0.55,
    "styleHint": null                      // ← sen etiketleyeceksin
  }
}
```

**Gizlilik:** dosya adı, sayfa adı, dosya anahtarı, kullanıcı adı **alınmaz**. Sadece katman
adları (kapatılabilir: `includeNames: false`).

---

## BÖLÜM F — Bu araştırmanın Plan'a etkisi

| Plan'daki madde | Değişiklik |
|---|---|
| Özellik sayısı ~165 | **~240** (I/J/K/L/M/N/O grupları eklendi) |
| M1 sınıf listesi 14 | Aynı + `Path2D`, `VideoFrame` kesinleşti |
| M2 boyut modeli | **Kontur kalınlığı ve köşe yarıçapı** ayrı ve birinci sınıf hedef oldu |
| M3 animasyon | `UIScale`, `UIStroke.Thickness`, `UIShadow.BlurRadius`, `UIGradient.Offset/Rotation` hedefler |
| YOKTU | **M0 Stil Modeli** eklendi (stud/anime/cartoon) |
| Veri toplama | `EI_*_egitim.json` ayrı çıktı olarak eklendi |
| Bilinmeyen | **Roblox kısıtları** netleşti (blur yok, inner shadow yok, text shadow yok, UIGradient sınırları, CanvasGroup tuzağı) |
| YOKTU | **Gelişmiş öğrenme motoru** eklendi (Bölüm J + `OGRENME-MOTORU.md`) |

---

## BÖLÜM G — ANİMASYON ARAŞTIRMASI

### G1. Evrensel hareket (motion) kuralları

Kaynaklar: [15](https://socialanimal.dev/blog/micro-interactions-web-design/),
[16](https://gist.github.com/uxderrick/07b81ca63932865ef1a7dc94fbe07838),
[17](https://www.appypie.com/blog/mobile-app-animation-guide),
[18](https://www.72technologies.com/blog/motion-ratios-ui-feel-cheap)

**Süre ölçeği:** `instant 80ms` · `fast 160ms` · `base 240ms` · `medium 360ms` · `slow 520ms` · `glacial 800ms`

**Üç easing:**
- **enter** (yavaşlayan) → Roblox `Quart/Out`, `Quint/Out`, `Expo/Out`
- **exit** (hızlanan) → Roblox `Quad/In`, `Cubic/In`, `Expo/In`
- **move** (simetrik) → Roblox `Sine/InOut`, `Cubic/InOut`
- **spring** (yay) → Roblox `Back/Out`, `Elastic/Out`, `Bounce/Out`

**Kurallar:**
1. **Çıkış, girişten hızlıdır** (~2:3). 2. **<80 ms algılanmaz, >500 ms hantal.**
3. **80–150 ms** buton basma/toggle · **200–300 ms** modal/dropdown.
4. **Stagger** ~40 ms (`base/6`). 5. `prefers-reduced-motion` → `StyleQuery.ReduceMotionEnabled`.

### G2. Roblox'ta UI animasyonu — pratik gerçekler

Kaynaklar: [19](https://create.roblox.com/docs/education/build-it-play-it-island-of-move/animating-parts),
[20](https://devforum.roblox.com/t/ui-size-animation/2395076),
[21](https://devforum.roblox.com/t/choppy-ui-tween/2170828),
[22](https://devforum.roblox.com/t/tween-module-for-hovering-over-gui-objects/3548091),
[23](https://devforum.roblox.com/t/uianimcontroller-lightweight-client-ui-animations-frame-toggles-hover-click-effects-slide-in-frames/4315843)

- **Standart:** nesneye `UIScale` ekle, `MouseEnter/MouseLeave` ile `Scale` tween et
  (`1 → 1.05` hover, `1 → 0.95` press).
- ⚠️ **`TweenSize`/`TweenPosition` önerilmiyor** — "choppy", layout'u yeniden hesaplatıyor.
- ⚠️ **AnchorPoint = 0.5, 0.5 şart.** ⚠️ **TextSize tween edilmez** (alt piksel yuvarlar).
- `TweenInfo.new(süre, EasingStyle, EasingDirection, repeatCount, reverses, delayTime)`
- Çakışan tween'ler `Cancel()` edilmeli; sonsuz döngüler görünmezken duraklatılmalı.

### G3. 🔥 Figma'daki "efekt image'i" → Roblox gerçeği

Kaynaklar: [24](https://devforum.roblox.com/t/gui-neonglow-effect/607011),
[25](https://devforum.roblox.com/t/visual-tweens-effect-for-ui/3295455),
[26](https://devforum.roblox.com/t/plugin-ui-shine-effect-add-animated-gloss-streaks-to-buttons-images-text-in-one-click/4686373),
[27](https://mozert.itch.io/roblox-ui-effects)

**Roblox'ta efekt ayrı bir sistem değil → EFEKT = ImageLabel/Frame + animasyon.**
Glow için tek pratik yol: beyaz glow PNG'sini `ImageLabel` olarak elemanın **altına** koymak.
Shine/gloss → üzerinden geçen parlaklık şeridi. Sparkle → yıldızlar belirip söner.
Ringing → halka yayılma. Bubble gloss → cam parlaması.

**→ Çıkarım:** Figma'da `glow`, `ray`, `sparkle`, `shine`, `vignette`, `noise`, `dust`, `ring`
adlı veya **SCREEN/ADD blend modlu** katmanlar içerik değil **efekttir**. Tespit kuralları ve
tür→animasyon eşlemesi: `anim/anim-library.json` → `_fxDetection` ve `anim/README.md` §4.

### G4. UIShadow = yeni animasyon hedefi

`UIShadow.BlurRadius` (UDim), `Transparency`, `Offset`, `Spread` **tween edilebilir**:
- **Glow nefesi:** `BlurRadius` 10→30 + `Transparency` 0.6→0.15, `rep:-1, rev:true`
- **Parlama patlaması:** `BlurRadius` 4→60→8, `Transparency` 1→0.05→0.7
- ⚠️ Metin üzerinde çalışmaz → metin glow'u için `TextStrokeTransparency` tween edilmeli.

### G5. Teslim edilenler

| Dosya | İçerik |
|---|---|
| `anim/anim-library.json` | **108 animasyon**, 10 kategori, 174 track, FX tespit sözlüğü |
| `anim/README.md` | Zaman sistemi, easing karşılıkları, track şeması, FX eşlemesi, rol→animasyon tablosu |

---

## BÖLÜM H — ROBLOX LUAU UI ANİMASYON: teknik gerçekler

Kaynaklar: [28](https://devforum.roblox.com/t/ui-size-animation/2395076),
[29](https://devforum.roblox.com/t/choppy-ui-tween/2170828),
[30](https://www.reddit.com/r/robloxgamedev/comments/1exmmxk/what_is_the_difference_between_lerping_and/),
[31](https://devforum.roblox.com/t/what-is-smoother-bindtorenderstep-or-tween/1331705/7),
[32](https://devforum.roblox.com/t/more-efficient-way-to-tween-lerp-towards-constant-moving-goal/2713772)

### H1. TweenService ne yapar, ne yapmaz

| Özellik | Tween edilebilir mi? | Not |
|---|---|---|
| `UIScale.Scale` | ✔ | **En iyi yöntem** |
| `Position` (UDim2) | ✔ | Konum için tercih edilen |
| `Rotation` | ✔ | |
| `Size` (UDim2) | △ | Tween edilir ama **layout yeniden hesaplar** → yavaş/takılmalı |
| `Background/Image/Text/GroupTransparency` | ✔ | |
| `*Color3` | ✔ | |
| `UIStroke.Thickness` / `.Color` | ✔ | |
| `UIShadow.BlurRadius` (UDim) / `Offset`/`Spread` (UDim2) / `Transparency` / `Color` | ✔ | 2026 yeni |
| `UIGradient.Offset` (Vector2) / `Rotation` | ✔ | **Roblox'un resmi önerisi** |
| `MaxVisibleGraphemes` (int) | ✔ | Daktilo efekti çalışır |
| **`Text` (string)** | ❌ | **TweenService string tween EDEMEZ** → sayaç için elle döngü şart |
| `FontFace` | ❌ | |
| `UIGradient.Color` / `.Transparency` | ❌ | Sequence; yeniden kurmak pahalı → `Offset`/`Rotation` kullan |
| `TextSize` | △ | Alt piksel yuvarlar → **takılmalı**. UIScale kullan |

> ⚠️ **Kütüphaneye yansıması:** `text_count_up` animasyonu `Text` özelliğini tween ediyor.
> Gerçek üretimde bu **elle sayım döngüsü** olarak üretilmeli (TweenService string tween edemez).

### H2. Performans kuralları

1. **`TweenSize` / `TweenPosition` kullanma** → layout recalc. `UIScale` kullan. [29]
2. **`TextSize`'ı tween etme** → alt piksel yuvarlama. `UIScale` kullan. [29]
3. **AnchorPoint = 0.5, 0.5** → yoksa köşeden ölçeklenir. [28]
4. **TweenInfo referanslarını döngü dışında tut.**
5. **Yeni tween başlatmadan önce `Cancel()`** — çakışan tween'ler titreme yapar.
6. **Sonsuz döngüleri `Visible=false` iken duraklat.**
7. **TweenService `Stepped`'de çalışır** (RenderStepped değil) — UI için yeterli. [31]
8. Elle lerp gerekirse **kare hızından bağımsız** yap: `alpha = 1 - math.exp(-rate * dt)`
   (basit `Lerp(a, b, 0.1)` FPS'e bağımlıdır). [32]
9. Çok akıcı takip (sürükleme, takip eden bar) için **spring** modülü tercih edilir. [29]

---

## BÖLÜM I — LUAU ANİMASYON: ek bulgular (BÖLÜM H'nin üstüne)

### I1. Motor seçenekleri
- **`TweenService`** (yerleşik) — UI için standart. ⚠️ **LocalScript** ile çalıştırılmalı;
  server'da daha az akıcı. [33](https://devforum.roblox.com/t/how-do-i-decide-between-loops-runservice-tweenservice-and-animations-for-movingrotating-objects/1638186)
- **Spring:** `SpringService` (SmoothDamp, TweenService drop-in) ve topluluk standardı **`spr`**.
  Desteklediği tipler: `number, Vector2, Vector3, CFrame, Color3, UDim, UDim2, Rect,
  NumberSequence, ColorSequence` → **`UIGradient` de spring edilebilir**.
  [34](https://devforum.roblox.com/t/springservice-drop-in-replacement-for-tweenservice-using-smoothdamp/3621210)

### I2. Uygulama tuzakları
- **ModuleScript tuzağı:** tween'i modül içinde tanımlayıp nesneyi orada sabitleme → nesneyi
  **LocalScript'ten parametre olarak geç**. [35](https://devforum.roblox.com/t/tweenservice-animation-not-playing-from-modulescript/3050781)
- **Performans:** aşırı `WaitForChild`, `while wait()` döngüleri yavaşlatır.
- TweenService karakter animasyonlarından daha az performanslı — ama **UI için doğru araç**.

### I3. Çıktı
| Dosya | İçerik |
|---|---|
| `SORULAR-LUAU.md` | 15 soru: motor seçimi, dosya yapısı, otomatik bağlama, hazır paketler |

---

## BÖLÜM J — GELİŞMİŞ ÖĞRENME MOTORU (araştırma)

> İstek: *"Asistana gelişmiş öğrenme motoru ekle. Yanlış yaptığında neden yanlış yaptığını bilen
> akıllı bir sistem yap."* → Tam tasarım: `assistant/OGRENME-MOTORU.md`

### J1. Kritik bulgu: lineer model = **kesin** açıklanabilirlik

Modelimiz **softmax regresyon**. Sinir ağı seçseydik her şey yaklaşık olurdu:

| Yöntem | Sinir ağı | **Lineer model (bizim)** |
|---|---|---|
| SHAP | KernelSHAP ≈ örnekleme, yavaş | **LinearSHAP: O(F) kesin** [40](https://letsdatascience.com/blog/shap-and-lime-making-ai-models-explainable) [41](https://christophm.github.io/interpretable-ml-book/shap.html) |
| Karşıt-olgusal | optimizasyon | **kapalı form** |
| Artımlı güncelleme | felaket unutma | **RLS: kapalı form, unutma yok** |

**Gruplanmış atıf:** `φ_g(c) = Σ_{i∈g} W[c][i]·(x_i − μ_i)` — grup bazında (özellikler birbiriyle
ilişkili olduğu için SHAP'in bağımsızlık varsayımına takılmamak adına).
**Karşıt-olgusal:** `Δᵢ = (z_wrong − z_correct) / (W[correct][i] − W[wrong][i])`.

⚠️ **İki araç, iki farklı soru** [42](https://uplatz.com/blog/a-technical-analysis-of-post-hoc-explainability-lime-shap-and-counterfactual-methods/):
*atıf* = "neden böyle dedi" (geçmiş), *karşıt-olgusal* = "ne değişseydi doğru olurdu" (eylem).
En yüksek atıflı özellik karşıt-olgusal için en iyisi **olmayabilir** → **ikisini birlikte kullan.**

### J2. Kalibrasyon — güven eşiğinin ön koşulu
- **Temperature scaling:** logitleri skaler `T`'ye böl. **Doğruluğu/sıralamayı değiştirmez**,
  güveni dürüstleştirir. [43](https://arxiv.org/pdf/1706.04599)
- Ölçüm: **ECE**, **MCE**, **Brier**, **reliability diagram**. [44](https://mbrenndoerfer.com/writing/calibration-machine-learning-confidence-accuracy-ece)
- Sınıf bazlı yanlılık için **Dirichlet calibration** [45](https://papers.neurips.cc/paper/9397-beyond-temperature-scaling-obtaining-well-calibrated-multi-class-probabilities-with-dirichlet-calibration.pdf)
- ⚠️ **Kalibre edilmemiş modelde belirsizlik örneklemesi işe yaramaz** [46](https://younsess-elbrag.medium.com/active-learning-approaches-strategies-deep-learning-integration-and-essential-tools-6ff2bdfe5cb)
  → **sıra: önce kalibre et, sonra aktif öğrenme.**

### J3. Aktif öğrenme
- **Margin sampling** (`p₁−p₂` en düşük) → SGD ile kanıtlanmış yakınsama [47](https://proceedings.mlr.press/v162/raj22a/raj22a.pdf)
- **Max-entropy**, **least-confidence**
- **Çeşitlilik şart:** havuzu kümele, farklı kümelerden seç — yoksa tek bölgeye yığılır [46]

### J4. Sürekli öğrenme
- **Felaket unutma** → **replay buffer** fiilî standart; sınıf başına az sayıda örnek bile
  unutmayı büyük ölçüde azaltır. [48](https://cameronrwolfe.substack.com/p/a-broad-and-practical-exposition-of-online-learning-techniques-a4cbc300dcd4)
- Alternatifler: **EWC**, **BiC**, distillation.
- ⭐ **Bizim avantajımız:** `W = (XᵀX + λI)⁻¹XᵀY` — Sherman-Morrison ile **artımlı, replay'sız,
  kesin** güncelleme (RLS). Bellek: 230×230 ≈ 420 KB. **Unutma yok.**

### J5. Confident learning — "etiket mi yanlış, model mi?"
Etiket gürültüsünü tespit eden ayrı bir katman (`label_health.py`). Özellikle **öğretmen kural
etiketleri** gürültülü olabilir — model ısrarla farklı diyorsa etiket şüphelidir.

### J6. Hata taksonomisi (7 kova)
`EKSİK_ÖZELLİK` · `YETERSİZ_VERİ` · `ETİKET_HATASI` · `STİL_UYUŞMAZLIĞI` · `KURAL_MÜDAHALESİ` ·
`BAĞLAM_EKSİK` · `SINIR_DURUM` — her birinin **otomatik aksiyonu** var
(özellik öner / kuyruğa at / etiketi düzelt / eşiği kalibre et / kuralı gözden geçir).

### J7. Çıktı
| Dosya | İçerik |
|---|---|
| `OGRENME-MOTORU.md` | Araştırma + 6 katmanlı mimari + dosya yapısı + yol haritası + sorular |
| `SORULAR.md` → Bölüm I | Öğrenme motoru soruları (atıf nerede gösterilsin, kaç soru, model doğrusal kalsın mı) |

---

*Tamamlanan: `anim/*` — 108 animasyon (A5) · `spec/style-rules.json` — stil v2 ·
`OGRENME-MOTORU.md` — gelişmiş öğrenme motoru.*
*Açık: `SORULAR.md` (stil D/Y + öğrenme motoru) · `SORULAR-LUAU.md` (Luau animasyon).*
