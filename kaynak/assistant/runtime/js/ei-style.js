// EasyImport — STİL TESPİTİ (A10) — kanon uygulama
//
// Kullanıcının tanımladığı üç stil + belirsiz:
//   🥇 STUD    — "Stud olan her GUI Stud stildir."  → SINIFLANDIRMA DEĞİL, TESPİT.
//                Kural: (ad tokenı VEYA doku tekrarı VEYA döşeme hücresi) VE dokunun
//                buton/header üzerinde olması. Güven 1.0, override edilemez.
//   🥈 ANIME   — en iyi ışıklandırma + yüksek detay + koyu taban + çok renk, doku orta.
//   🥉 CARTOON — doku ağırlıklı, efekti az, detay düşük.
//   4️⃣ BELİRSİZ — ikisi de zayıfsa VEYA skorlar birbirine çok yakınsa (marj < 0.12).
//
// Kaynak: spec/style-rules.json v2 + ARASTIRMA.md Bölüm C1/C1b (kullanıcı tarifi).
//
// Tasarım kuralları:
//   • Saf fonksiyon: Roblox/Figma API'si yok, I/O yok, rastgelelik yok.
//   • Yalnızca +,-,*,/ ve karşılaştırma → JS ile Lua bit bit aynı sonucu verir
//     (tools/verify_style.py kapısı). log10 iki tarafta da ln(x)/ln(10) ile hesaplanır.
//   • Sözlük (nameTokens) yalnızca DOĞRUDAN bakar; for-in/pairs ile gezinilmez.
//
// EIRaw'a `opts.styleFn` olarak verilir:  EIRaw.extract(doc, { styleFn: EIStyle.detect })

var EIStyle = (function () {
  var VERSION = 'ei-style-1';

  // spec/style-rules.json → _signals.hasStud.detect.nameTokens
  // ARAŞTIRMA (Bölüm C1c): topluluk adlandırması — "Stud", "Studs", "Studded", "Studs3x3",
  // "Stud UI/Pack", Türkçe "civili/civi". Bunlar DOĞRUDAN stud kanıtı.
  var STUD_TOKENS = ['stud', 'studs', 'studded', 'studtexture', 'studpattern', 'studtile',
                     'studbg', 'studsui', 'studs3x3', 'civi', 'civili'];
  // ZAYIF kanıt: "brick/texture/pattern/tugla" → duvar dokusu, genel doku; stud olabilir ama
  // tek başına YETMEZ (araştırma: "texture" kelimesi her dokulu tasarımda geçer).
  var STUD_WEAK_TOKENS = ['brick', 'tugla', 'texture', 'pattern', 'desen'];
  // RAKİP STİL NİTELEYİCİLERİ: "AnimeTexture" adlı katman ANIME'in dokusudur, stud'un değil.
  // Bu token'lardan biri varsa `texture/pattern` kelimesi stud kanıtı SAYILMAZ.
  var COMPETING_STYLE_TOKENS = ['anime', 'cartoon', 'kawaii', 'chibi', 'manga', 'toon', 'cizgi'];
  // Dokunun "buton veya header üzerinde" olması ZORUNLU ("olmazsa olmazıdır")
  var BUTTON_HEADER_TOKENS = ['button', 'btn', 'buton', 'header', 'top', 'title', 'nav', 'bar', 'tab'];
  // Yarı saydam ışık katmanları (blend mode). Figma tarafı `ei.blendMode` yazana kadar 0 kalır.
  var LIGHT_BLEND = { SCREEN: 1, ADD: 1, LINEAR_DODGE: 1, COLOR_DODGE: 1, LIGHTEN: 1, OVERLAY: 1, SOFT_LIGHT: 1 };

  var W = {
    // lightingIndex
    glow: 0.30, gradient: 0.24, radial: 0.18, multiStop: 0.12, lightLayer: 0.10, darkness: 0.06,
    // detailIndex
    dNodes: 0.40, dDepth: 0.30, dEffect: 0.30,
    // textureIndex
    tImage: 0.40, tTile: 0.25, tTexture: 0.15, tVector: 0.10, tReuse: 0.10,
    // anime / cartoon skorları
    aLight: 0.40, aDetail: 0.22, aDark: 0.18, aHue: 0.12, aMuted: 0.08,
    cTexture: 0.45, cEffect: 0.25, cGradient: 0.18, cDetail: 0.12,
    // eşikler (spec/style-rules.json → _thresholds, hepsi "proposed")
    animeLightMin: 0.55, animeDetailMin: 0.55, animeDarkMin: 0.50,
    cartoonTextureMin: 0.40, cartoonEffectMax: 0.40, cartoonDetailMax: 0.35,
    studEffectMax: 0.25, studReuseMin: 0.50, studImageMin: 0.50,
    studUniqueTexMax: 2,          // "başka texture kullanılmaz" → benzersiz doku sayısı sınırı
    studUniqueTexHardMax: 3,      // bunun ÜSTÜ çelişki: karışık dokulu tasarım stud olamaz
    studEvidenceMin: 4,           // kanıt merdiveni eşiği (0..10 ölçeğinde)
    studNameScopeMin: 2,          // tek düğüm adındaki "stud" yetmez (stud İKONU tuzağı)
    studEffectVeto: 0.60,         // anime gibi yoğun efekt → stud değil
    studDetailVeto: 0.62,         // yüksek detay → stud değil
    studTileRateMin: 0.15,        // dokunun GUI geneline yayılması
    studGeoSpreadMin: 3,          // kaç düğümde ÖLÇÜLMÜŞ kare döşeme hücresi olursa "yayılmış" sayılır
    studGridMin: 2, studGridMax: 8,   // "size ve boyutundan da anlaşılıyor": 2..8 stud sığar
    marginMin: 0.12
  };

  // NaN güvenliği: NaN karşılaştırmaları her zaman false döndüğü için
  // `x < 0 ? ... : x` tuzağına düşmemek adına ters mantık kullanılır.
  function clamp01(x) { if (!(x > 0)) return 0; return x > 1 ? 1 : x; }
  function num(v, d) { return (typeof v === 'number' && v === v) ? v : d; }
  function max(a, b) { return a > b ? a : b; }
  function log10(x) { return Math.log(x > 0 ? x : 1e-12) / Math.log(10); }
  function iv(x) { if (!(x === x) || x === Infinity || x === -Infinity) return 0; return Math.floor(x + 0.5); }
  // Lua: string.format('%d', iv(x)) — ikisi de tam sayı metni üretir (tostring TUZAĞI: Lua 5.3 "32.0")
  function itos(x) { return String(iv(x)); }

  function hasTok(toks, list) {
    if (!toks) return false;
    for (var i = 0; i < list.length; i++) if (toks[list[i]] === true) return true;
    return false;
  }

  // --------------------------------------------------------------------------
  // Sinyaller — hepsi 0..1 (sayımlar düğüm sayısına bölünür)
  // --------------------------------------------------------------------------
  // Zayıf stud adı kanıtı: düğüm adlarında "brick/texture/pattern/desen/tugla" geçiyor mu?
  function hasTokAll(gui, raws, list) {
    for (var i = 0; i < raws.length; i++) {
      if (hasTok(raws[i].nameTokens, list)) return true;
    }
    return false;
  }

  function signals(gui, raws) {
    var n = raws.length;
    var s = {
      hasStud: false, lightingIndex: 0, detailIndex: 0, darknessIndex: 0, mutedBaseRate: 0,
      hueDiversity: 0, accentPopRate: 0, textureIndex: 0, effectDensity: 0, gradientRate: 0,
      reuseRate: 0, imageDrivenRate: 0, darkerUnderlayRate: 0, shineFrameRate: 0,
      glowRate: 0, tileRate: 0, textureEffectRate: 0, vectorDecorRate: 0,
      radialRate: 0, multiStopRate: 0, lightLayerRate: 0,
      maxDepth: 0, nNodes: 0
    };
    if (n === 0) return s;

    var nGlow = 0, nTile = 0, nTexEff = 0, nVecDec = 0, nGrad = 0, nRadial = 0, nMulti = 0, nLight = 0;
    var maxDepth = 0;
    var nameStud = false, repeatUse = false, tileCell = false, onButtonOrHeader = false, weakOnBH = false;
    // --- STUD v3 kanıt sayaçları (ARAŞTIRMA Bölüm C1c) ---
    var nStudName = 0, nStudTileGeo = 0, nStudGeoBH = 0, studGridOk = false;
    var studCellMin = 0, studCellMax = 0;

    for (var i = 0; i < n; i++) {
      var r = raws[i];
      var toks = r.nameTokens || null;
      var tokStud = hasTok(toks, STUD_TOKENS);
      var reuse = num(r.imageReuse, 0);
      var tile = r.imageTile === true;
      var hasImg = (r.hasImageFill === true) || (reuse > 0);
      var onBH = hasTok(toks, BUTTON_HEADER_TOKENS);

      // Zayıf kanıt: rakip stil niteleyicisi varsa (ör. "AnimeTexture") stud sayılmaz.
      var tokWeak = hasTok(toks, STUD_WEAK_TOKENS) && !hasTok(toks, COMPETING_STYLE_TOKENS);
      if (tokStud) { nameStud = true; nStudName++; }
      // Dokunun BUTON/HEADER üzerinde olması ZORUNLU (kural zaten böyle yazılıydı, kod uygulamıyordu)
      if (tokWeak && onBH && hasImg) weakOnBH = true;
      if (reuse >= 2) repeatUse = true;
      if (tile) tileCell = true;
      if (onBH && hasImg && (tokStud || reuse >= 2 || tile)) onButtonOrHeader = true;

      // GEOMETRİ kanıtı: küçük KARE döşeme hücresi ölçülmüş (Figma `scalingFactor` × görsel px).
      // İsim yazmasa da stud dokusu buradan anlaşılır: "size ve boyutundan da anlaşılıyor".
      var geo = (r.studTileGeo === true);
      if (geo) {
        nStudTileGeo++;
        var cc = num(r.tileCellW, 0);
        if (cc > 0) {
          studCellMin = studCellMin > 0 ? ((cc < studCellMin) ? cc : studCellMin) : cc;
          studCellMax = (cc > studCellMax) ? cc : studCellMax;
        }
        if (onBH) nStudGeoBH++;
        var gn = num(r.tileGridN, 0), gv = num(r.tileGridNv, 0);
        if ((gn >= W.studGridMin && gn <= W.studGridMax) ||
            (gv >= W.studGridMin && gv <= W.studGridMax)) studGridOk = true;
      }

      if (r.hasGlowPattern === true) nGlow++;
      if (tile) nTile++;
      if (r.textureLike === true) nTexEff++;
      if (r.isVectorKind === true && r.isFx !== true && r.isText !== true) nVecDec++;
      if (r.hasGradient === true) {
        nGrad++;
        if (r.gradType === 'RADIAL') nRadial++;
        if (num(r.gradStops, 0) >= 3) nMulti++;
      }
      if (r.blendMode && LIGHT_BLEND[r.blendMode] === 1) nLight++;
      var d = num(r.depth, 0);
      if (d > maxDepth) maxDepth = d;
    }

    s.glowRate = nGlow / n;
    s.tileRate = nTile / n;
    s.textureEffectRate = nTexEff / n;
    s.vectorDecorRate = nVecDec / n;
    s.radialRate = nGrad > 0 ? (nRadial / nGrad) : 0;
    s.multiStopRate = nGrad > 0 ? (nMulti / nGrad) : 0;
    s.lightLayerRate = nLight / n;

    s.darknessIndex = clamp01(num(gui.darknessIndex, 0));
    s.mutedBaseRate = clamp01(num(gui.mutedBaseRate, 0));
    s.hueDiversity = clamp01(num(gui.hueDiversity, 0));
    s.accentPopRate = clamp01(num(gui.accentPopRate, 0));
    s.effectDensity = clamp01(num(gui.effectDensity, 0));
    s.gradientRate = clamp01(num(gui.gradientRate, 0));
    s.reuseRate = clamp01(num(gui.reuseRate, 0));
    s.imageDrivenRate = clamp01(num(gui.imageDrivenRate, 0));
    s.darkerUnderlayRate = clamp01(num(gui.darkerUnderlayRate, 0));
    s.shineFrameRate = clamp01(num(gui.shineFrameRate, 0));
    s.maxDepth = maxDepth;
    s.nNodes = n;

    // --- lightingIndex (ışıklandırma ekseni: Anime'nin ayırt edicisi) --------
    s.lightingIndex = clamp01(
      W.glow * s.glowRate + W.gradient * s.gradientRate + W.radial * s.radialRate +
      W.multiStop * s.multiStopRate + W.lightLayer * s.lightLayerRate + W.darkness * s.darknessIndex);

    // --- detailIndex ---------------------------------------------------------
    var nrm = clamp01(log10(max(1, n)) / 3);
    var drm = clamp01(maxDepth / 8);
    s.detailIndex = clamp01(W.dNodes * nrm + W.dDepth * drm + W.dEffect * s.effectDensity);

    // --- textureIndex (Cartoon'un ayırt edici ekseni) ------------------------
    s.textureIndex = clamp01(
      W.tImage * s.imageDrivenRate + W.tTile * s.tileRate + W.tTexture * s.textureEffectRate +
      W.tVector * s.vectorDecorRate + W.tReuse * s.reuseRate);

    // --- STUD TESPİTİ ---------------------------------------------------------
    // spec/style-rules.json'daki yazılı kural:
    //   (nameTokens OR repeatUse OR tileCellSize) AND onButtonOrHeader
    // ÖLÇÜM: bu hâliyle "aynı görseli 2 kez kullanan her buton" stud sayılıyordu —
    // sentetik cartoon örneği yanlışlıkla stud çıktı. Kullanıcının kendi tarifi
    // bunu desteklemiyor: "Stud dokusu tipik olarak UI + header + menüde tekrar eder"
    // + "Texture'si stud olduğundan BAŞKA TEXTURE KULLANILMAZ" (tek doku karakteri).
    // Bu yüzden kanıt gücü ayrımı yapılır:
    //   GÜÇLÜ  kanıt: stud adı tokenı  VEYA  döşeme (TILE/küçük hücre) dokusu
    //   DESTEK : doku tekrarı  VEYA  "tek doku" (benzersiz doku sayısı <= 2)
    //   hasStud = buton/header üzerinde  VE  (stud adı  VEYA  (döşeme VE tek doku))
    s.fewTextures = (num(gui.nUniqueImages, 0) <= W.studUniqueTexMax) && (num(gui.nImages, 0) > 0);
    s.studTileRate = clamp01(nStudTileGeo / n);
    s.studCellUniform = !!(nStudTileGeo > 0 && studCellMin > 0 && (studCellMax / studCellMin) <= 1.25);
    s.studCellPx = nStudTileGeo > 0 ? studCellMin : 0;
    s.nStudTileGeo = nStudTileGeo; s.nStudName = nStudName;

    // ----------------------------------------------------------------------
    // STUD TESPİTİ v3 — KANIT MERDİVENİ (ARAŞTIRMA Bölüm C1c)
    //
    // Kullanıcı: "Stud olan her GUI Stud stildir" → tespit, güven 1.0, override yok.
    // Ama "stud İKONU ≠ stud STİLİ": modern paketler tek stud rozeti/ikonu kullanır.
    // Bu yüzden karar tek bir sinyale değil, TOPLANAN KANITA dayanır:
    //
    //   GÜÇLÜ  (+3) ad kanıtı   : ≥2 düğümde stud adı VEYA ad + ölçülmüş döşeme
    //   GÜÇLÜ  (+3) geometri    : buton/header üzerinde KÜÇÜK KARE döşeme hücresi
    //   DESTEK (+1) : doku tekrarı · tek doku · image ağırlıklı · döşeme yaygınlığı ·
    //                 tek hücre ölçüsü · 2..8 stud sığması
    //   DESTEK (+0.5): shine katmanı · 3D alt katman · az efekt · orta-düşük detay
    //   VETO        : >3 benzersiz doku ("başka texture kullanılmaz") · yoğun efekt · yüksek detay
    //
    // Eski kural (doku tekrarı + buton/header) tek başına yetmiyordu: aynı görseli 2 kez
    // kullanan her menü stud sayılıyordu. Artık kanıt eşiği + veto var.
    // ----------------------------------------------------------------------
    var strongName = (nStudName >= W.studNameScopeMin) || (nStudName >= 1 && nStudTileGeo >= 1);
    var strongGeo = (nStudGeoBH >= 1);
    // GÜÇLÜ geometri (yayılım): dokunun KENDİSİ ölçülmüş ve birden çok düğümde tekrar ediyor,
    // üstelik başka doku YOK ("tek doku karakteri" + "size ve boyutundan da anlaşılıyor").
    // Gerçek `stud frame templates.fig`: 12 döşemeli düğüm · 53-64 px KARE hücre · 2 benzersiz doku.
    // Buton/header koşulu burada aranmaz: şablon dosyasında katmanlar "Rectangle 8"/"header" adlıdır.
    var strongGeoSpread = (nStudTileGeo >= W.studGeoSpreadMin) && s.fewTextures;
    var weak = hasTokAll(gui, raws, STUD_WEAK_TOKENS);
    var ev = 0;
    if (strongName) ev += 3;
    if (strongGeo) ev += 3;
    if (weak) ev += 1;
    if (studGridOk) ev += 1;
    if (s.reuseRate >= W.studReuseMin) ev += 1;
    if (s.fewTextures) ev += 1;
    if (s.imageDrivenRate >= W.studImageMin) ev += 1;
    if (s.studTileRate >= W.studTileRateMin) ev += 1;
    if (s.studCellUniform) ev += 1;
    if (s.shineFrameRate > 0) ev += 0.5;
    if (s.darkerUnderlayRate > 0) ev += 0.5;
    if (s.effectDensity <= W.studEffectMax) ev += 0.5;
    if (s.detailIndex <= 0.55) ev += 0.5;

    var veto = (num(gui.nUniqueImages, 0) > W.studUniqueTexHardMax) ||
               (s.effectDensity > W.studEffectVeto) || (s.detailIndex > W.studDetailVeto);
    s.studEvidence = ev; s.studStrongName = strongName; s.studStrongGeo = strongGeo;
    s.studWeakName = weak; s.studWeakOnBH = weakOnBH; s.studVeto = veto; s.studGeoSpread = strongGeoSpread;
    // `weak` TEK BAŞINA yetmez: kanıt merdiveninin belgesi "zayıf kanıt yetmez" diyor ve
    // buton/header koşulunu ZORUNLU tutuyor. Aksi hâlde 263 düğümlük bir anime envanterinde
    // tek bir `AnimeTexture` katmanı stud=1.0 üretiyordu (gerçek veriyle yakalandı).
    s.hasStud = strongName ||
      (ev >= W.studEvidenceMin && !veto && (strongGeo || strongGeoSpread || weakOnBH || s.studTileRate >= W.studTileRateMin));
    s._studName = nameStud; s._studRepeat = repeatUse; s._studTile = tileCell; s._studOnBH = onButtonOrHeader;
    return s;
  }

  // --------------------------------------------------------------------------
  // Karar — 4 stil, skorlar ve güven
  // --------------------------------------------------------------------------
  function decide(s) {
    var out = {
      version: VERSION,
      stud: false, anime: false, cartoon: false, belirsiz: true,
      style: 'belirsiz', conf: 0,
      scores: { stud: 0, anime: 0, cartoon: 0 },
      signals: s, oneLiner: ''
    };
    if (s.nNodes === 0) { out.oneLiner = 'Boş GUI: stil belirsiz.'; return out; }

    // 1) STUD — tespit, override yok
    if (s.hasStud) {
      out.stud = true; out.belirsiz = false;
      out.style = 'stud'; out.conf = 1;
      out.scores = { stud: 1, anime: 0, cartoon: 0 };
      out.oneLiner = 'Stud: kanıt ' + itos(s.studEvidence * 2) + '/20 · '
        + (s.studStrongName ? 'ad' : (s.studStrongGeo ? 'döşeme geometrisi' : 'doku'))
        + (s.studStrongGeo ? ' + buton/header' : '')
        + ' · hücre ' + itos(s.studCellPx) + 'px'
        + ' · doku tekrarı ' + pct(s.reuseRate)
        + ' · efekt ' + f2(s.effectDensity);
      return out;
    }

    // 2) ANIME / CARTOON skorları
    var a = W.aLight * s.lightingIndex + W.aDetail * s.detailIndex + W.aDark * s.darknessIndex +
            W.aHue * s.hueDiversity + W.aMuted * s.mutedBaseRate;
    var c = W.cTexture * s.textureIndex + W.cEffect * (1 - s.effectDensity) +
            W.cGradient * (1 - s.gradientRate) + W.cDetail * (1 - s.detailIndex);
    out.scores.anime = a; out.scores.cartoon = c;
    var margin = a > c ? (a - c) : (c - a);
    var sum = a + c;

    var animeRule = (s.lightingIndex >= W.animeLightMin) &&
                    (s.detailIndex >= W.animeDetailMin) &&
                    (s.darknessIndex >= W.animeDarkMin);
    var cartoonRule = (s.textureIndex >= W.cartoonTextureMin) &&
                      (s.effectDensity <= W.cartoonEffectMax) &&
                      (s.detailIndex <= W.cartoonDetailMax);

    var winner = a >= c ? 'anime' : 'cartoon';
    var eligible = (animeRule && cartoonRule) ? null : (animeRule ? 'anime' : (cartoonRule ? 'cartoon' : null));

    if (eligible && margin >= W.marginMin) {
      out[eligible] = true; out.belirsiz = false;
      out.style = eligible;
      out.conf = sum > 0 ? clamp01((eligible === 'anime' ? a : c) / sum) : 0.5;
      out.oneLiner = (eligible === 'anime' ? 'Anime' : 'Cartoon') + ': '
        + 'ışık ' + f2(s.lightingIndex) + ' · detay ' + f2(s.detailIndex) + ' · koyuluk ' + f2(s.darknessIndex)
        + ' · doku ' + f2(s.textureIndex) + ' · efekt ' + f2(s.effectDensity);
      return out;
    }

    // 3) Çok yakın ya da eşiklerin tutmadığı durum → belirsiz (zorlama yok)
    out.conf = eligible ? clamp01(1 - (margin / W.marginMin)) : 0;
    out.oneLiner = eligible
      ? 'Belirsiz: ' + (eligible === 'anime' ? 'anime' : 'cartoon') + ' eşikleri tuttu ama fark küçük ('
        + f2(margin) + ' < ' + f2(W.marginMin) + ').'
      : 'Belirsiz: hiçbir stil eşiği tutmadı (ışık ' + f2(s.lightingIndex) + ' · detay ' + f2(s.detailIndex)
        + ' · doku ' + f2(s.textureIndex) + ' · efekt ' + f2(s.effectDensity) + ').';
    return out;
  }

  // Biçimlendirme TAM SAYI aritmetiğiyle: `toFixed` Lua'da yok, string(format) ise JS'te
  // farklı yuvarlayabilir. Böylece iki dil birebir aynı metni üretir.
  function pct(x) { return iv(clamp01(x) * 100) + '%'; }

  function f2(x) {
    var v = iv(clamp01(x) * 100);          // 0..100 tamsayı
    var s = String(v);
    while (s.length < 3) s = '0' + s;      // 0 -> "000"
    return s.slice(0, s.length - 2) + '.' + s.slice(s.length - 2);
  }

  // EIRaw kancası: (gui, flat, raws) → { stud, anime, cartoon, belirsiz, conf, ... }
  function detect(gui, flat, raws) {
    return decide(signals(gui, raws || []));
  }

  return {
    VERSION: VERSION,
    WEIGHTS: W,
    STUD_TOKENS: STUD_TOKENS,
    BUTTON_HEADER_TOKENS: BUTTON_HEADER_TOKENS,
    signals: signals,
    decide: decide,
    detect: detect
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = EIStyle;
