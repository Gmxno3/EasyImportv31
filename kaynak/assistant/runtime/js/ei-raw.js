/* EasyImport Asistan — RAW ÇIKARICI (JavaScript — Figma tarafı)  [A2]
 *
 * Girdi : plugin'in ürettiği `wispfree v9` dökümanı ({format,version,name,
 *         width,height,root}).
 * Çıktı : her görünür öğe için bir RAW kaydı + GUI düzeyi özet.
 *
 * spec/features.json 155 farklı kaynak alan okur; bu dosya o alanların TAMAMINI
 * üretmek zorundadır. Eksik alan = sessizce 0 (bkz. EIFeatures.asnum).
 *
 * Python (ei_raw.py) ve Lua (EIRaw.lua) sürümleriyle BİREBİR aynı sonucu
 * vermek ZORUNDADIR; tools/verify_extract.py bunu zorunlu tutar.
 *
 * Figma'da:  var EIRaw = <bu dosya>;
 * Node'da :  var EIRaw = require('./ei-raw.js');
 */
var EIRaw = (function () {
  'use strict';

  var EPS = 1e-9;

  // -------------------------------------------------------------------------
  // 1) AD TOKEN SÖZLÜĞÜ — build_features.py NAME_TOKENS ile AYNI SIRADA.
  //    Sıra sabittir; indeks = ağırlık indeksi. Buradaki liste yalnızca
  //    "ek" eşleştirme kuralları içindir (çoğaltma/kök indirgeme).
  // -------------------------------------------------------------------------
  var NAME_TOKENS = [
    'button','btn','buton','icon','close','exit','play','start','settings',
    'option','menu','back','next','prev','tab','nav','footer','header',
    'panel','bg','background','overlay','modal','popup','dialog','card',
    'slot','item','inventory','bag','shop','list','grid','scroll','content',
    'container','wrapper','divider','frame','label','text','title','desc',
    'value','count','timer','tooltip','badge','avatar','profile',
    'bar','hp','health','mana','energy','xp','level','coin','gem','gold',
    'progress','fill','loader','slider','toggle','check','reward','currency',
    'glow','ray','rays','shine','shining','sparkle','sparkles','star','stars',
    'twinkle','particle','flare','bloom','vignette','noise','grain','dust',
    'smoke','fog','ring','pulse','aura','beam','streak','gloss','shimmer',
    'glint','blur','halo','neon','emission','energy2','magic','fx','effect',
    'stud','studs','brick','civi','civili','texture','pattern',
    'isik','parlama','parilti','huzme','toz','duman','halka','efekt'
  ];

  // FX token -> fxKind (grup I, d_fxKind). 16 türden biri.
  //
  // DİKKAT: bu bir DİZİDİR, sözlük değil. Taranma sırası anlamlıdır ve üç
  // dilde de aynı olmak zorundadır — Lua'da pairs() sırası garantili değildir,
  // bu yüzden sıralı bir liste kullanıyoruz (ilk eşleşme kazanır).
  var FX_TOKENS_ORDERED = [
    ['glow','glow'], ['bloom','glow'], ['halo','glow'], ['neon','glow'],
    ['emission','glow'], ['isik','glow'], ['parlama','glow'], ['efekt','glow'],
    ['fx','glow'], ['effect','glow'],
    ['ray','rays'], ['rays','rays'],
    ['huzme','beam'], ['beam','beam'], ['streak','beam'],
    ['shine','shine'], ['shining','shine'], ['shimmer','shine'], ['parilti','shine'],
    ['sparkle','sparkle'], ['sparkles','sparkle'], ['twinkle','sparkle'],
    ['particle','sparkle'],
    ['star','star'], ['stars','star'],
    ['flare','flare'],
    ['vignette','vignette'],
    ['noise','noise'], ['grain','noise'],
    ['dust','dust'], ['toz','dust'],
    ['smoke','smoke'], ['fog','smoke'], ['duman','smoke'],
    ['ring','ring'], ['pulse','ring'], ['halka','ring'],
    ['aura','aura'], ['magic','aura'],
    ['gloss','gloss'], ['glint','gloss'],
    ['blur','blur']
  ];
  var FX_TOKEN_KIND = {};
  for (var _fi = 0; _fi < FX_TOKENS_ORDERED.length; _fi++) {
    FX_TOKEN_KIND[FX_TOKENS_ORDERED[_fi][0]] = FX_TOKENS_ORDERED[_fi][1];
  }

  // Stud / doku tokenları (kullanıcı: "stud kullanılmışsa Stud'a girer")
  var STUD_TOKENS = { stud:1, studs:1, brick:1, civi:1, civili:1, texture:1, pattern:1 };

  // -------------------------------------------------------------------------
  // 2) küçük yardımcılar
  // -------------------------------------------------------------------------
  function max(a, b) { return a > b ? a : b; }
  function min(a, b) { return a < b ? a : b; }
  function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }

  // Lua ikizindeki `round(x) = math.floor(x + 0.5)` ile AYNI formül (negatifte de birebir)
  function iv(x) { return Math.floor(x + 0.5); }

  function isNum(x) { return typeof x === 'number' && isFinite(x); }
  function num(x, dflt) { return isNum(x) ? x : (dflt === undefined ? 0 : dflt); }

  // --- renk: 0..255 -> HSV -------------------------------------------------
  function rgb2hsv(r, g, b) {
    r = clamp01(num(r) / 255); g = clamp01(num(g) / 255); b = clamp01(num(b) / 255);
    var mx = max(r, max(g, b)), mn = min(r, min(g, b));
    var d = mx - mn;
    var h = 0;
    if (d > EPS) {
      if (mx === r) h = ((g - b) / d) % 6;
      else if (mx === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h *= 60;
      if (h < 0) h += 360;
    }
    var s = (mx <= EPS) ? 0 : d / mx;
    return { h: h, s: s, v: mx };
  }

  function lum(r, g, b) {
    // göreli parlaklık (0..1)
    return (0.2126 * num(r) + 0.7152 * num(g) + 0.0722 * num(b)) / 255;
  }

  function paletteBucket(h, s, v) {
    if (s < 0.12) {
      if (v < 0.16) return 'black';
      if (v > 0.92) return 'white';
      return 'gray';
    }
    if (h < 15) return 'red';
    if (h < 45) return 'orange';
    if (h < 70) return 'yellow';
    if (h < 165) return 'green';
    if (h < 200) return 'cyan';
    if (h < 255) return 'blue';
    if (h < 290) return 'purple';
    if (h < 330) return 'pink';
    if (h < 20) return 'brown';
    return 'red';
  }

  // --- ad tokenizasyonu ---------------------------------------------------
  //
  // KURAL: kelime TAM eşleşmesi + sonek indirgeme (s / es / ing / ed) ve
  // sondaki rakamların atılması. Prefix eşleşmesi YOKTUR — aksi halde
  // "start" -> "star" (FX) gibi yanlış eşleşmeler olur.
  //
  // Üç dilde de BİREBİR aynı olmak zorunda olduğu için yardımcılar elle
  // yazılmıştır: foldLower / utf8len / splitWords / camelSplit.
  // (Yerel ayara bağlı toUpperCase / toLowerCase KULLANILMAZ.)

  // UTF-8 bayt uzunluğu — JS length (UTF-16) ve Lua # (bayt) ayrışmasın.
  function utf8len(s) {
    var n = 0;
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c < 0x80) n += 1;
      else if (c < 0x800) n += 2;
      else if (c >= 0xD800 && c <= 0xDBFF) { n += 4; i++; }
      else n += 3;
    }
    return n;
  }

  // Türkçe'yi de kapsayan, yerel ayardan bağımsız küçültme.
  // 'İ' çağrıdan ÖNCE 'i' yapılır (JS/Python varsayılanı 'i̇' verir, bu
  // üç dilde aynı olmazdı).
  function foldLower(s) {
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 65 && c <= 90) out += String.fromCharCode(c + 32);
      else if (c === 0xC7) out += '\u00E7';       // Ç -> ç
      else if (c === 0x11E) out += '\u011F';      // Ğ -> ğ
      else if (c === 0xD6) out += '\u00F6';       // Ö -> ö
      else if (c === 0x15E) out += '\u015F';      // Ş -> ş
      else if (c === 0xDC) out += '\u00FC';       // Ü -> ü
      else out += s.charAt(i);
    }
    return out;
  }

  // Büyültme — yalnızca "tümü büyük harf mi" testi için.
  function foldUpper(s) {
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 97 && c <= 122) out += String.fromCharCode(c - 32);
      else if (c === 0xE7) out += '\u00C7';       // ç -> Ç
      else if (c === 0x11F) out += '\u011E';      // ğ -> Ğ
      else if (c === 0x131) out += 'I';             // ı -> I
      else if (c === 0xF6) out += '\u00D6';       // ö -> Ö
      else if (c === 0x15F) out += '\u015E';      // ş -> Ş
      else if (c === 0xFC) out += '\u00DC';       // ü -> Ü
      else out += s.charAt(i);
    }
    return out;
  }

  // Büyük harf var mı (A-Z + ÇĞİÖŞÜ)
  function hasUpper(s) {
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 65 && c <= 90) return true;
      if (c === 0xC7 || c === 0x11E || c === 0x130 || c === 0xD6 || c === 0x15E || c === 0xDC) return true;
    }
    return false;
  }

  // [a-z0-9çğıöşü] dışındaki her şey ayırıcıdır.
  // Bayt yerine KARAKTER üzerinden yürürüz ki çok baytlı harfler bozulmasın.
  function isWordChar(code) {
    if (code >= 48 && code <= 57) return true;      // 0-9
    if (code >= 97 && code <= 122) return true;     // a-z
    if (code >= 65 && code <= 90) return true;      // A-Z
    switch (code) {
      case 0xE7: case 0xC7: return true;            // ç Ç
      case 0x11F: case 0x11E: return true;          // ğ Ğ
      case 0x131: case 0x49: return true;           // ı I
      case 0xF6: case 0xD6: return true;            // ö Ö
      case 0x15F: case 0x15E: return true;          // ş Ş
      case 0xFC: case 0xDC: return true;            // ü Ü
      case 0x130: return true;                      // İ
    }
    return false;
  }

  function splitWords(s) {
    var out = [];
    var cur = '';
    for (var i = 0; i < s.length; i++) {
      if (isWordChar(s.charCodeAt(i))) cur += s.charAt(i);
      else { if (cur) { out.push(cur); cur = ''; } }
    }
    if (cur) out.push(cur);
    return out;
  }

  function trimStr(s) { return String(s).replace(/^[ \t\r\n]+/, '').replace(/[ \t\r\n]+$/, ''); }

  function tokenize(name) {
    var out = {};
    var s0 = String(name == null ? '' : name);
    if (!s0) return out;
    s0 = s0.split('\u0130').join('i');                       // İ -> i (yerelden bağımsız)
    s0 = s0.replace(/([a-z0-9çğıöşü])([A-ZÇĞÖŞÜ])/g, '$1 $2'); // camelCase ayır
    var s = foldLower(s0);
    var words = splitWords(s);
    for (var m = 0; m < words.length; m++) {
      var base = words[m].replace(/[0-9]+$/, '');   // "sparkle01" -> "sparkle"
      if (!base) continue;
      var forms = [base];
      if (base.length > 3) {
        if (/s$/.test(base)) forms.push(base.slice(0, -1));
        if (/es$/.test(base)) forms.push(base.slice(0, -2));
        if (/ing$/.test(base)) forms.push(base.slice(0, -3));
        if (/ed$/.test(base)) forms.push(base.slice(0, -2));
      }
      for (var fi = 0; fi < forms.length; fi++) out[forms[fi]] = 1;
    }
    return out;
  }

  function hasAny(tokens, list) {
    for (var k in list) if (tokens[k]) return k;
    return null;
  }

  function countWords(name) {
    var s = String(name == null ? '' : name).trim();
    if (!s) return 0;
    return s.replace(/[^a-zA-Z0-9ığüşöçİĞÜŞÖÇ]+/g, ' ').trim().split(/\s+/).length;
  }

  // -------------------------------------------------------------------------
  // 3) DÜZLEŞTİRME (pass 0)
  // -------------------------------------------------------------------------
  function flatten(root) {
    var flat = [];
    (function rec(item, parent, depth, si, nSib) {
      if (!item) return;
      var rec0 = {
        item: item, parent: parent, depth: depth, si: si, nSib: nSib,
        i: flat.length
      };
      flat.push(rec0);
      var kids = item.children || [];
      for (var i = 0; i < kids.length; i++) rec(kids[i], item, depth + 1, i, kids.length);
    })(root, null, 0, 0, 1);
    return flat;
  }

  function itemW(it) { return num(it && it.w, 0); }
  function itemH(it) { return num(it && it.h, 0); }

  // -------------------------------------------------------------------------
  // 4) BOYUT KÜMELERİ (grup C — "tüm GUI'yi karşılaştır")
  //
  //    Elemanların w/h'si, belgenin kısa kenarının %2'sine yuvarlanır ve
  //    aynı yuvarlanan boyuta düşenler "aynı boyut" sayılır. Kümeler
  //    (üye sayısı AZALAN, sonra alan AZALAN) sıralanır; rank 0 = bu GUI'de
  //    en sık kullanılan boyut. Böylece model mutlak boyuta değil
  //    "bu GUI'nin geri kalanına göre" bakar.
  // -------------------------------------------------------------------------
  function buildClusters(flat, docMin) {
    var q = max(1, docMin * 0.02);
    var map = {};
    var order = [];
    for (var i = 0; i < flat.length; i++) {
      var it = flat[i].item;
      var w = itemW(it), h = itemH(it);
      var key = Math.round(w / q) + ':' + Math.round(h / q);
      var c = map[key];
      if (!c) {
        c = map[key] = { key: key, n: 0, w: 0, h: 0, area: 0, members: [] };
        order.push(key);
      }
      c.n++;
      c.members.push(i);
      if (w * h > c.area) { c.area = w * h; c.w = w; c.h = h; }
    }
    var clusters = [];
    for (var o = 0; o < order.length; o++) clusters.push(map[order[o]]);
    clusters.sort(function (a, b) {
      // Eşitlikte üçüncü bir anahtarla kır: Lua'nın table.sort'u kararlı
      // değildir, bu yüzden üç dilde de aynı sonucu ancak böyle alırız.
      if (b.n !== a.n) return b.n - a.n;
      if (b.area !== a.area) return b.area - a.area;
      return a.key < b.key ? -1 : (a.key > b.key ? 1 : 0);
    });
    for (var ci = 0; ci < clusters.length; ci++) clusters[ci].rank = ci;
    return { byKey: map, list: clusters };
  }

  // -------------------------------------------------------------------------
  // 5) ANA ÇIKARICI
  // -------------------------------------------------------------------------
  function extract(doc, opts) {
    opts = opts || {};
    var root = doc && doc.root;
    if (!root) return { nodes: [], gui: emptyGui() };

    var docW = num(doc.width, itemW(root) || 1920) || 1920;
    var docH = num(doc.height, itemH(root) || 1080) || 1080;
    var docMin = min(docW, docH);
    var docMax = max(docW, docH);
    var docArea = docW * docH;

    var flat = flatten(root);
    var n = flat.length;

    // ---- tüm GUI istatistikleri ------------------------------------------
    var maxW = 0, maxH = 0, maxDepth = 0, maxArea = 0;
    var imageCount = {};  // dosya -> kaç düğümde kullanılmış
    for (var i = 0; i < n; i++) {
      var it0 = flat[i].item;
      var w0 = itemW(it0), h0 = itemH(it0);
      if (w0 > maxW) maxW = w0;
      if (h0 > maxH) maxH = h0;
      if (flat[i].depth > maxDepth) maxDepth = flat[i].depth;
      if (w0 * h0 > maxArea) maxArea = w0 * h0;
      it0.__eiKids = [];
    }
    if (maxW <= 0) maxW = 1;
    if (maxH <= 0) maxH = 1;
    if (maxDepth <= 0) maxDepth = 1;
    if (maxArea <= 0) maxArea = 1;

    // ebeveyn -> çocuk listesi (nesne referansı üzerinden; JS'de güvenli)
    for (var a = 0; a < n; a++) {
      var p = flat[a].parent;
      if (p) p.__eiKids.push(a);
    }

    // image yeniden kullanım sayacı
    for (var b = 0; b < n; b++) {
      var f = imageFileOf(flat[b].item);
      if (f) imageCount[f] = (imageCount[f] || 0) + 1;
    }

    var clusters = buildClusters(flat, docMin);

    // alan sıralaması (sizeRank / sizePercentile için)
    var byArea = [];
    for (var c2 = 0; c2 < n; c2++) byArea.push(c2);
    byArea.sort(function (x, y) {
      var ax = itemW(flat[x].item) * itemH(flat[x].item);
      var ay = itemW(flat[y].item) * itemH(flat[y].item);
      if (ax !== ay) return ax - ay;
      return x - y;                    // eşitlikte deterministik
    });
    var areaRankOf = {};
    for (var c3 = 0; c3 < n; c3++) areaRankOf[byArea[c3]] = c3;

    // ---- PASS 1: düğüm başına yerel özellikler ---------------------------
    var raws = [];
    for (var k = 0; k < n; k++) {
      raws.push(nodeRaw(flat, k, {
        docW: docW, docH: docH, docMin: docMin, docMax: docMax, docArea: docArea,
        maxW: maxW, maxH: maxH, maxDepth: maxDepth, maxArea: maxArea,
        clusters: clusters, areaRankOf: areaRankOf, imageCount: imageCount, n: n
      }));
    }

    // ---- PASS 2: 3D alt katman (kullanıcı: "aynı rengin kapalısını altta")
    markDarkerUnderlays(flat, raws);

    // ---- PASS 3: GUI düzeyi sinyaller (grup J) ---------------------------
    var gui = guiSummary(flat, raws, imageCount);

    // ---- PASS 4: GUI sinyallerini her düğüme kopyala ---------------------
    for (var g = 0; g < raws.length; g++) copyGui(raws[g], gui);

    // ---- PASS 5: isteğe bağlı stil dedektörü (A10) -----------------------
    var style = null;
    if (typeof opts.styleFn === 'function') {
      style = opts.styleFn(gui, flat, raws) || null;
    }
    if (style) {
      for (var s2 = 0; s2 < raws.length; s2++) applyStyle(raws[s2], style);
    }

    // geçici kimlikleri temizle
    for (var t = 0; t < n; t++) {
      try { delete flat[t].item.__eiKids; } catch (e) {}
    }

    return { nodes: raws, gui: gui, style: style, meta: { docW: docW, docH: docH, n: n } };
  }

  function emptyGui() {
    return {
      darknessIndex: 0, mutedBaseRate: 0, hueDiversity: 0, accentPopRate: 0,
      effectDensity: 0, gradientRate: 0, reuseRate: 0, imageDrivenRate: 0,
      darkerUnderlayRate: 0, shineFrameRate: 0,
      nNodes: 0, nImages: 0, nUniqueImages: 0, nEffects: 0, nGradients: 0,
      nSolid: 0, nDarkerUnderlay: 0, nShineFrame: 0,
      nStudTile: 0, studTileRate: 0, studCellW: 0, studCellUniform: false
    };
  }

  // -------------------------------------------------------------------------
  // 6) GÖRSEL DOSYA ADI — plugin dedupe'u aynı görseli aynı adla verir.
  //    Aynı adın birden fazla düğümde geçmesi = DOKU (Stud tespitinin kalbi).
  // -------------------------------------------------------------------------
  function imageFileOf(it) {
    if (!it) return null;
    if (typeof it.image === 'string' && it.image) return it.image;
    var fills = it.fills || [];
    for (var i = 0; i < fills.length; i++) {
      var f = fills[i];
      if (f && f.type === 'IMAGE') {
        if (typeof f.file === 'string' && f.file) return f.file;
        if (typeof f.imageHash === 'string' && f.imageHash) return f.imageHash;
        return '@image:' + i;
      }
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // 7) TEK DÜĞÜM
  // -------------------------------------------------------------------------
  function nodeRaw(flat, k, ctx) {
    var rec = flat[k];
    var it = rec.item;
    var ei = it.ei || {};                       // v10 tam-bağlılık yan kanalı

    var w = itemW(it), h = itemH(it);
    var area = w * h;
    var aspect = (h > EPS) ? (w / h) : 20.0;
    var minDim = min(w, h), maxDim = max(w, h);
    var x = num(it.x, 0), y = num(it.y, 0);

    var parent = rec.parent;
    var parentW = parent ? itemW(parent) : (it === flat[0].item ? w : 0);
    var parentH = parent ? itemH(parent) : (it === flat[0].item ? h : 0);
    if (parent) { parentW = itemW(parent); parentH = itemH(parent); }
    var parentArea = parentW * parentH;
    if (parentArea <= 0) parentArea = 1;

    var raw = {};

    // ---- GRUP B: geometri -------------------------------------------------
    raw.w = w; raw.h = h;
    raw.area = area;
    raw.areaRatio = area / (ctx.docArea > 0 ? ctx.docArea : 1);
    raw.aspect = aspect;
    raw.minDim = minDim; raw.maxDim = maxDim;
    raw.rot = num(it.rot, 0);
    raw.docW = ctx.docW; raw.docH = ctx.docH;
    raw.docMin = ctx.docMin; raw.docMax = ctx.docMax;

    var cx = (x + w / 2) / (ctx.docW > 0 ? ctx.docW : 1);
    var cy = (y + h / 2) / (ctx.docH > 0 ? ctx.docH : 1);
    raw.cx = clamp01(cx);
    raw.cy = clamp01(cy);
    var dx = cx - 0.5, dy = cy - 0.5;
    raw.distCenter = clamp01(Math.sqrt(dx * dx + dy * dy) / 0.7071067811865476);
    raw.edgeTop = clamp01(1 - y / (ctx.docH > 0 ? ctx.docH : 1));
    raw.edgeBottom = clamp01(1 - ((ctx.docH - (y + h)) / (ctx.docH > 0 ? ctx.docH : 1)));
    raw.edgeLeft = clamp01(1 - x / (ctx.docW > 0 ? ctx.docW : 1));
    raw.edgeRight = clamp01(1 - ((ctx.docW - (x + w)) / (ctx.docW > 0 ? ctx.docW : 1)));
    var col = cx < 0.3333333 ? 'l' : (cx > 0.6666667 ? 'r' : 'c');
    var row = cy < 0.3333333 ? 't' : (cy > 0.6666667 ? 'b' : 'm');
    raw.cornerRegion = row + col;

    // ---- GRUP C: bağlam ---------------------------------------------------
    var q = max(1, ctx.docMin * 0.02);
    var ckey = Math.round(w / q) + ':' + Math.round(h / q);
    var clus = ctx.clusters.byKey[ckey] || null;
    raw.clusterRank = clus ? clus.rank : 0;
    raw.clusterCount = clus ? clus.n : 1;
    raw.clusterSingleton = !!clus && clus.n === 1;
    raw.clusterW = clus ? clus.w : w;
    raw.clusterH = clus ? clus.h : h;
    raw.clusterAspect = (clus && clus.h > EPS) ? (clus.w / clus.h) : aspect;
    raw.nSameSize = clus ? clus.n : 1;

    raw.parentW = parentW; raw.parentH = parentH; raw.parentArea = parentArea;

    var kids = (parent && parent.__eiKids) ? parent.__eiKids : [k];
    var sumW = 0, sumH = 0;
    for (var s = 0; s < kids.length; s++) {
      sumW += itemW(flat[kids[s]].item);
      sumH += itemH(flat[kids[s]].item);
    }
    var sibMeanW = sumW / (kids.length > 0 ? kids.length : 1);
    var sibMeanH = sumH / (kids.length > 0 ? kids.length : 1);
    raw.sibMeanW = sibMeanW; raw.sibMeanH = sibMeanH;

    // kardeş boyut değişkenliği (alanın varyasyon katsayısı, 0..1)
    var areas = [];
    for (var s2 = 0; s2 < kids.length; s2++) {
      var ki = flat[kids[s2]].item;
      areas.push(itemW(ki) * itemH(ki));
    }
    raw.sibSizeVar = clamp01(coefVar(areas));

    raw.maxW = ctx.maxW; raw.maxH = ctx.maxH; raw.maxDepth = ctx.maxDepth;

    var ar = ctx.areaRankOf[k];
    raw.sizeRank = (ctx.n > 1) ? (ar / (ctx.n - 1)) : 0;
    raw.sizePercentile = (ctx.n > 1) ? (ar / ctx.n) : 1;

    // hizalama: merkezim bir kardeşin merkeziyle örtüşüyor mu?
    var tol = max(2, ctx.docMin * 0.01);
    var alX = false, alY = false;
    for (var s3 = 0; s3 < kids.length; s3++) {
      if (kids[s3] === k) continue;
      var oj = flat[kids[s3]].item;
      if (Math.abs((num(oj.x, 0) + itemW(oj) / 2) - (x + w / 2)) <= tol) alX = true;
      if (Math.abs((num(oj.y, 0) + itemH(oj) / 2) - (y + h / 2)) <= tol) alY = true;
    }
    raw.alignedX = alX; raw.alignedY = alY;

    raw.depth = rec.depth;
    raw.nSiblings = rec.nSib;

    // ---- GRUP A: ad -------------------------------------------------------
    var nm = String(it.name == null ? '' : it.name);
    var toks = tokenize(nm);
    var tokOut = {};
    for (var ti = 0; ti < NAME_TOKENS.length; ti++) {
      var tk = NAME_TOKENS[ti];
      if (toks[tk]) tokOut[tk] = true;
    }
    raw.nameTokens = tokOut;
    raw.name = nm;
    raw.hasUnderscoreTag = nm.indexOf('_') >= 0;
    raw.nameHasDigit = /[0-9]/.test(nm);
    raw.isCamel = /[a-z0-9][A-Z]/.test(nm);
    raw.nameAllUpper = hasUpper(nm) && (foldUpper(nm) === nm);
    raw.nameLen = utf8len(nm);
    raw.nameEmpty = nm.trim().length === 0;
    raw.nameWords = countWords(nm);

    // ---- GRUP D: dolgu & renk --------------------------------------------
    var fills = it.fills || [];
    var nFills = 0, hasSolid = false, hasGradient = false, hasImageFill = false;
    var fillOpacity = 0, fillAlpha = 0, fillH = 0, fillS = 0, fillV = 0;
    var gradStops = 0, gradType = 'NONE_UNUSED', gradAngle = 0;
    var distinct = {};
    var nDistinct = 0;
    var solidFill = null;

    for (var fi = 0; fi < fills.length; fi++) {
      var f = fills[fi];
      if (!f || f.visible === false) continue;
      nFills++;
      var op = num(f.opacity, 1);
      if (op > fillOpacity) fillOpacity = op;
      if (f.type === 'SOLID') {
        hasSolid = true;
        if (!solidFill) solidFill = f;
        var hsv = rgb2hsv(f.color && f.color.r, f.color && f.color.g, f.color && f.color.b);
        fillH = hsv.h; fillS = hsv.s; fillV = hsv.v;
        fillAlpha = max(fillAlpha, op * num(f.color && f.color.a, 1));
        var dk = quant(f.color);
        if (!distinct[dk]) { distinct[dk] = 1; nDistinct++; }
        raw.paletteBucket = paletteBucket(hsv.h, hsv.s, hsv.v);
      } else if (f.type === 'GRADIENT' || f.type === 'GRADIENT_OTHER') {
        hasGradient = true;
        var stops = f.stops || [];
        if (stops.length > gradStops) {
          gradStops = stops.length;
          gradAngle = num(f.angle, 0);
          gradType = (f.type === 'GRADIENT') ? 'LINEAR' : 'RADIAL';
        }
        // en parlak stop'u "baskın renk" say
        for (var si = 0; si < stops.length; si++) {
          var sc = stops[si].color || {};
          var sh = rgb2hsv(sc.r, sc.g, sc.b);
          if (sh.v > fillV * 0.999 || fillV === 0) {
            fillH = sh.h; fillS = sh.s; fillV = sh.v;
          }
          var dk2 = quant(sc);
          if (!distinct[dk2]) { distinct[dk2] = 1; nDistinct++; }
        }
        fillAlpha = max(fillAlpha, op);
        if (!raw.paletteBucket) raw.paletteBucket = paletteBucket(fillH, fillS, fillV);
      } else if (f.type === 'IMAGE') {
        hasImageFill = true;
        fillAlpha = max(fillAlpha, op);
      }
    }
    raw.nFills = nFills;
    raw.hasSolid = hasSolid;
    raw.hasGradient = hasGradient;
    raw.hasImage = hasImageFill;
    raw.isTransparentFill = (nFills === 0) || (fillAlpha < 0.02);
    raw.fillOpacity = clamp01(fillOpacity > 0 ? fillOpacity : (nFills > 0 ? 1 : 0));
    raw.fillAlpha = clamp01(fillAlpha);
    raw.fillH = fillH; raw.fillS = fillS; raw.fillV = fillV;
    raw.fillIsDark = fillV < 0.45;
    raw.fillIsNeon = (fillS > 0.7) && (fillV > 0.7);
    raw.paletteBucket = raw.paletteBucket || 'gray';
    raw.gradStops = gradStops;
    raw.gradType = gradType === 'NONE_UNUSED' ? 'LINEAR' : gradType;
    raw.gradAngleBucket = ((gradAngle % 360) + 360) % 360 / 45;   // 0..7
    raw.nDistinctColors = nDistinct;
    raw.isMonochrome = true;
    for (var dki in distinct) {
      // 12'lik renk küpü — gri olmayan her kova monokromluğu bozar
      if (!/^g:/.test(dki)) { raw.isMonochrome = false; break; }
    }
    if (nFills === 0) raw.isMonochrome = true;

    // ---- GRUP E: kontur & köşe -------------------------------------------
    var stroke = it.stroke || null;
    var strokeW = 0, strokeS = 0, strokeV = 0, strokeOpacity = 0, strokeH = 0;
    var hasStroke = false;
    if (stroke && num(stroke.weight, 0) > 0) {
      hasStroke = true;
      strokeW = num(stroke.weight, 0);
      var shsv = rgb2hsv(stroke.color && stroke.color.r,
                         stroke.color && stroke.color.g,
                         stroke.color && stroke.color.b);
      strokeS = shsv.s; strokeV = shsv.v; strokeH = shsv.h;
      strokeOpacity = clamp01(num(stroke.opacity, 1));
    } else if (num(it.strokeWeight, 0) > 0 && (it.strokes || []).length) {
      hasStroke = true;
      strokeW = num(it.strokeWeight, 0);
      var st0 = it.strokes[it.strokes.length - 1];
      var shsv2 = rgb2hsv(st0 && st0.color && st0.color.r,
                          st0 && st0.color && st0.color.g,
                          st0 && st0.color && st0.color.b);
      strokeS = shsv2.s; strokeV = shsv2.v; strokeH = shsv2.h;
      strokeOpacity = clamp01(num(st0 && st0.opacity, 1));
    }
    raw.hasStroke = hasStroke;
    raw.strokeW = strokeW;
    raw.strokeAlign = it.strokeAlign || (stroke ? 'INSIDE' : 'CENTER');
    raw.strokeJoin = ei.join || 'MITER';
    raw.hasDash = !!(ei.dash && ei.dash.length);
    raw.strokePerSideDiff = !!ei.strokePerSide;
    raw.strokeS = strokeS; raw.strokeV = strokeV;
    raw.strokeH = strokeH;
    raw.strokeOpacity = strokeOpacity;
    raw.strokeDarkerThanFill = hasStroke && (strokeV < fillV - 0.02);
    raw.contrastFS = clamp01(Math.abs(
      lum(fillRGB(solidFill, raw).r, fillRGB(solidFill, raw).g, fillRGB(solidFill, raw).b) -
      lum(stroke && stroke.color ? stroke.color.r : 0,
          stroke && stroke.color ? stroke.color.g : 0,
          stroke && stroke.color ? stroke.color.b : 0)));
    raw.minDim = minDim;    // bölenler için zorunlu

    var r = 0;
    if (it.radius === 'full') { r = minDim / 2; raw.isFullRadiusFlag = true; }
    else r = num(it.radius, 0);
    raw.r = r;
    raw.rPerSideDiff = !!ei.rPerSide;
    raw.isFullRadius = (it.radius === 'full') || (minDim > 0 && r >= minDim / 2 - 0.01);
    raw.isPill = raw.isFullRadius && (minDim > 0) && ((maxDim / minDim) > 1.6);
    raw.isCircle = raw.isFullRadius && (Math.abs(aspect - 1) < 0.05);
    raw.strokeAndRadius = hasStroke && (r > 0);
    raw.borderRatio = (minDim > 0) ? clamp01(2 * strokeW / minDim) : 0;

    // ---- GRUP F: metin ----------------------------------------------------
    var tx = (it.kind === 'text' && it.text) ? it.text : null;
    raw.isText = !!tx;
    if (tx) {
      var chars = String(tx.characters == null ? '' : tx.characters);
      raw.textLen = utf8len(chars);
      var ws = chars.trim().split(/\s+/);
      raw.textWords = (chars.trim() === '') ? 0 : ws.length;
      raw.textHasDigit = /[0-9]/.test(chars);
      raw.textIsNumeric = /^[0-9\s.,:%+\/-]+$/.test(chars) && chars.trim().length > 0;
      raw.textAllUpper = hasUpper(chars) && (foldUpper(chars) === chars) && trimStr(chars).length > 1;
      raw.fontSize = num(tx.fontSize, 16);
      raw.fontWeight = num(tx.fontWeight, 400);
      raw.italic = !!tx.italic;
      raw.alignH = tx.align || 'LEFT';
      raw.alignV = tx.vAlign || 'TOP';
      raw.wrap = !!tx.wrap;
      raw.nLines = num(tx.lines, 1);
      var thsv = rgb2hsv(tx.color && tx.color.r, tx.color && tx.color.g, tx.color && tx.color.b);
      raw.textV = thsv.v; raw.textS = thsv.s; raw.textH = thsv.h;
      raw.textDensity = (area > 0) ? clamp01(utf8len(chars) / (area / 1000)) : 0;
    } else {
      raw.textLen = 0; raw.textWords = 0;
      raw.textHasDigit = false; raw.textIsNumeric = false; raw.textAllUpper = false;
      raw.fontSize = 0; raw.fontWeight = 0; raw.italic = false;
      raw.alignH = 'LEFT'; raw.alignV = 'TOP'; raw.wrap = false; raw.nLines = 0;
      raw.textV = 0; raw.textS = 0; raw.textH = 0; raw.textDensity = 0;
    }

    // ---- GRUP G: ağaç & düzen --------------------------------------------
    var myKids = it.__eiKids || [];
    var children = it.children || [];
    raw.nChildren = children.length;
    raw.hasChildren = children.length > 0;
    var nT = 0, nI = 0, nF = 0;
    for (var ci = 0; ci < children.length; ci++) {
      var ch = children[ci];
      if (ch.kind === 'text') nT++;
      else if (ch.kind === 'vector' || (ch.image)) nI++;
      else nF++;
    }
    raw.nTextChildren = nT; raw.nImageChildren = nI; raw.nFrameChildren = nF;
    raw.isLeaf = !raw.hasChildren;
    raw.isRoot = (rec.depth === 0);
    raw.siblingIndex = rec.si;
    raw.isFirstChild = (rec.si === 0);
    raw.isLastChild = (rec.si === rec.nSib - 1);
    raw.clips = !!it.clips;
    raw.hasScroll = !!it.scroll;
    var lay = it.layout || null;
    raw.layoutMode = (lay && lay.mode) ? lay.mode : 'NONE';
    raw.gap = lay ? num(lay.gap, 0) : 0;
    raw.padAvg = lay ? (num(lay.pl, 0) + num(lay.pr, 0) + num(lay.pt, 0) + num(lay.pb, 0)) / 4 : 0;
    var cAreas = [];
    for (var ci2 = 0; ci2 < children.length; ci2++) {
      cAreas.push(itemW(children[ci2]) * itemH(children[ci2]));
    }
    raw.childSizeVar = clamp01(coefVar(cAreas));

    // ---- GRUP H: efektler -------------------------------------------------
    var shadows = it.shadows || ((it.shadow) ? [it.shadow] : []);
    var nShadows = 0, sx = 0, sy = 0, sblur = 0, sspread = 0, salpha = 0, nGlow = 0;
    for (var si2 = 0; si2 < shadows.length; si2++) {
      var sh = shadows[si2];
      if (!sh) continue;
      nShadows++;
      sx += num(sh.x, 0); sy += num(sh.y, 0);
      sblur += num(sh.blur, 0); sspread += num(sh.spread, 0);
      salpha = max(salpha, clamp01(num(sh.opacity, 1)));
      // glow deseni: ofset ~0, büyük blur, yüksek opaklık
      if (Math.abs(num(sh.x, 0)) < 1 && Math.abs(num(sh.y, 0)) < 1 &&
          num(sh.blur, 0) >= 8 && clamp01(num(sh.opacity, 1)) >= 0.3) nGlow++;
    }
    raw.nShadows = nShadows;
    raw.shadowOffsetX = sx; raw.shadowOffsetY = sy;
    raw.shadowBlur = sblur; raw.shadowSpread = sspread;
    raw.shadowAlpha = salpha;
    raw.shadowIsMulti = nShadows > 1;
    raw.hasInnerShadow = !!ei.innerShadow;
    raw.hasLayerBlur = !!ei.layerBlur || (num(ei.layerBlur, 0) > 0);
    raw.hasBgBlur = !!ei.bgBlur || (num(ei.bgBlur, 0) > 0);
    raw.blurRadius = max(num(ei.layerBlur, 0), num(ei.bgBlur, 0));
    raw.hasGlowPattern = nGlow > 0;
    raw.nGlow = nGlow;
    raw.hasAnyEffect = (nShadows > 0) || raw.hasInnerShadow || raw.hasLayerBlur || raw.hasBgBlur;
    raw.opacity = clamp01(num(it.opacity, 1));

    // ---- GRUP I: FX & doku ------------------------------------------------
    var imgFile = imageFileOf(it);
    var isVectorKind = (it.kind === 'vector') || !!it.image;
    raw.hasImageFill = !!imgFile;
    raw.isVectorKind = isVectorKind;
    raw.imageReuse = imgFile ? (ctx.imageCount[imgFile] || 1) : 0;
    var tileW = num(ei.tileW, 0), tileH = num(ei.tileH, 0);
    var isTile = false;
    for (var fi2 = 0; fi2 < fills.length; fi2++) {
      if (fills[fi2] && fills[fi2].type === 'IMAGE' && fills[fi2].scaleMode === 'TILE') isTile = true;
    }
    if (tileW > 0 && tileH > 0) isTile = true;
    raw.imageTile = isTile || ((tileW > 0 && tileW < 128) || (tileH > 0 && tileH < 128));

    // ---- DÖŞEME GEOMETRİSİ (stud tespitinin isimden bağımsız kanıtı) ----
    // Kaynak: item.ei (yan kanal) — Figma `ImagePaint.scaleMode/scalingFactor` +
    // `Image.getSizeAsync()`. Hücre px = görsel px × scalingFactor (TILE'da).
    // Tasarımcı katmana "stud" yazmasa da stud dokusu kendini hücre boyutundan belli eder
    // (kullanıcı: "size ve boyutundan da anlaşılıyor" · "başka texture kullanılmaz").
    var sfv = num(ei.sf, 0);
    if ((tileW <= 0 || tileH <= 0) && sfv > 0) {
      var iaWf = num(ei.imageW, 0), iaHf = num(ei.imageH, 0);
      if (iaWf > 0 && iaHf > 0) { tileW = iaWf * sfv; tileH = iaHf * sfv; }
    }
    raw.tileCellW = (tileW > 0 && tileW < 4096) ? tileW : 0;
    raw.tileCellH = (tileH > 0 && tileH < 4096) ? tileH : 0;
    var cw = raw.tileCellW, ch = raw.tileCellH;
    raw.tileCellSquare = (cw > 0 && ch > 0) && (Math.abs(cw - ch) <= 1);
    // stud dokusu tipik olarak KÜÇÜK ve karedir (klasik 32–64 px; dokular 4096'a kadar çıkabilir)
    raw.tileCellSmall = raw.tileCellSquare && cw >= 8 && cw <= 96;
    // "kaç stud sığar" — kullanıcı: "size ve boyutundan da anlaşılıyor"
    raw.tileGridN = (raw.tileCellSmall && w > 0) ? iv(w / cw) : 0;
    raw.tileGridNv = (raw.tileCellSmall && h > 0) ? iv(h / ch) : 0;
    raw.studTileGeo = !!(raw.tileCellSmall && raw.imageTile && num(raw.imageReuse, 0) >= 2);

    var iaW = num(ei.imageW, 0), iaH = num(ei.imageH, 0);
    raw.imageAspectMatch = false;
    if (iaW > 0 && iaH > 0 && w > 0 && h > 0) {
      raw.imageAspectMatch = Math.abs((iaW / iaH) - (w / h)) < 0.1;
    }
    raw.imageLargerParent = parent ? ((w > parentW * 1.05 + 0.5) || (h > parentH * 1.05 + 0.5)) : false;
    raw.blendMode = ei.blendMode || 'NONE';
    raw.hasStudToken = !!hasAny(tokOut, STUD_TOKENS);

    // shine frame: geniş, üstü örten, beyazımsı gradient, düşük opaklık
    var isShineFrame = false;
    if (it.kind !== 'text' && !isVectorKind && hasGradient) {
      var allPale = true, minStopOpacity = 1;
      for (var fi3 = 0; fi3 < fills.length; fi3++) {
        var gf = fills[fi3];
        if (!gf || !(gf.type === 'GRADIENT' || gf.type === 'GRADIENT_OTHER')) continue;
        var sts = gf.stops || [];
        if (sts.length < 2) { allPale = false; break; }
        for (var si3 = 0; si3 < sts.length; si3++) {
          var cc = sts[si3].color || {};
          var hh = rgb2hsv(cc.r, cc.g, cc.b);
          if (hh.s > 0.15) allPale = false;
          minStopOpacity = min(minStopOpacity, num(sts[si3].opacity, 1));
        }
      }
      // Bir shine bir butonu / header'ı kaplar; panelin tamamını değil.
      // Bu yüzden eşik %10 — %25 çok katıydı ve gerçek örnekleri kaçırıyordu.
      var coversParent = parent ? (area >= parentArea * 0.10)
                                : (area >= ctx.docArea * 0.10);
      isShineFrame = allPale && coversParent &&
                     (num(it.opacity, 1) < 0.6 || minStopOpacity < 0.5 || fillAlpha < 0.5);
    }
    raw.isShineFrame = isShineFrame;

    // FX türü
    var fxKind = null;
    for (var fk = 0; fk < FX_TOKENS_ORDERED.length; fk++) {
      if (tokOut[FX_TOKENS_ORDERED[fk][0]]) { fxKind = FX_TOKENS_ORDERED[fk][1]; break; }
    }
    var blendFx = (raw.blendMode !== 'NONE' && raw.blendMode !== 'NORMAL');
    var isFx = false;
    if (fxKind) {
      isFx = true;
    } else if (isShineFrame) {
      isFx = true; fxKind = 'shine';
    } else if (imgFile && (blendFx || raw.imageLargerParent || raw.imageReuse === 1) &&
               (it.kind === 'vector')) {
      isFx = true; fxKind = 'glow';
    } else if (isVectorKind && isVignetteLike(raw, parentW, parentH)) {
      isFx = true; fxKind = 'vignette';
    }
    raw.isFx = isFx;
    raw.fxKind = fxKind || 'glow';   // one-hot, hiçbiri değilse tümü 0 kalır
    raw.fxKindSet = fxKind || false;  // null olmasın: Lua'da anahtar kaybolur

    raw.textureLike = !!(imgFile && (raw.imageReuse >= 2 || isTile ||
                                     (tileW > 0 && tileW < 128) ||
                                     tokOut.texture || tokOut.pattern));

    // ---- GRUP K: ebeveyn bağlamı -----------------------------------------
    raw.parentCls = 'NONE';
    raw.parentIsRoot = !parent;
    raw.parentDepth = parent ? (rec.depth - 1) : 0;
    raw.parentHasScroll = parent ? !!parent.scroll : false;
    if (parent) {
      var pq = max(1, ctx.docMin * 0.02);
      var pkey = Math.round(itemW(parent) / pq) + ':' + Math.round(itemH(parent) / pq);
      var pc = ctx.clusters.byKey[pkey];
      raw.parentClusterRank = pc ? pc.rank : 0;
    } else {
      raw.parentClusterRank = -1;
    }

    raw.darkerUnderlay = false;      // pass 2 doldurur
    raw.__i = k;
    return raw;
  }

  function isVignetteLike(raw, parentW, parentH) {
    return raw.w >= parentW * 0.98 && raw.h >= parentH * 0.98 &&
           raw.opacity < 0.95;
  }

  function fillRGB(solidFill, raw) {
    if (solidFill && solidFill.color) return solidFill.color;
    // HSV'den geri dön (yaklaşık; yalnızca kontrast için)
    return hsv2rgb(raw.fillH, raw.fillS, raw.fillV);
  }

  function hsv2rgb(h, s, v) {
    var c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
    var r = 0, g = 0, b = 0;
    if (h < 60) { r = c; g = x; }
    else if (h < 120) { r = x; g = c; }
    else if (h < 180) { g = c; b = x; }
    else if (h < 240) { g = x; b = c; }
    else if (h < 300) { r = x; b = c; }
    else { r = c; b = x; }
    return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 };
  }

  function quant(color) {
    if (!color) return 'g:0';
    var r = num(color.r, 0), g2 = num(color.g, 0), b2 = num(color.b, 0);
    var hsv = rgb2hsv(r, g2, b2);
    if (hsv.s < 0.12) return 'g:' + Math.round(hsv.v * 7);
    return 'c:' + Math.round(hsv.h / 30) + ':' + Math.round(hsv.s * 3) + ':' + Math.round(hsv.v * 3);
  }

  function coefVar(arr) {
    if (!arr || arr.length < 2) return 0;
    var s = 0, i;
    for (i = 0; i < arr.length; i++) s += arr[i];
    var m = s / arr.length;
    if (Math.abs(m) < EPS) return 0;
    var v = 0;
    for (i = 0; i < arr.length; i++) { var d = arr[i] - m; v += d * d; }
    v /= arr.length;
    return Math.sqrt(v) / Math.abs(m);
  }

  // -------------------------------------------------------------------------
  // 8) PASS 2 — 3D ALT KATMAN
  //    Kullanıcı: "genellikle 3D yapmaya çalışırlar, aynı rengin kapalısını
  //    altta geçirerek 3D görünüm verirler."
  //
  //    Kutuları kabaca çakışan iki katmandan HUE'su aynı (fark < 12°) ve
  //    V'si DÜŞÜK olan -> alt katman. Z-sırasına bakılmaz (Figma'da çocuk
  //    sırası her zaman güvenilir değildir); koyu olan her zaman alttadır.
  // -------------------------------------------------------------------------
  function markDarkerUnderlays(flat, raws) {
    // Kardeş grupları: her ebeveynin __eiKids listesi.
    var groups = [];
    for (var i = 0; i < flat.length; i++) {
      var it = flat[i].item;
      if (it.__eiKids && it.__eiKids.length > 1) groups.push(it.__eiKids);
    }
    // kök de (ebeveyni yok) tek başına bir grup değil; ama aynı ebeveynin
    // çocukları zaten yukarıda toplandı.

    for (var gi = 0; gi < groups.length; gi++) {
      var grp = groups[gi];
      for (var a = 0; a < grp.length; a++) {
        var ia = grp[a], ra = raws[ia];
        if (ra.isText) continue;
        var ia2 = flat[ia].item;
        if (ia2.kind === 'vector' || ia2.image) continue;      // alt katman düz dolgudur
        if (!ra.hasSolid) continue;
        for (var b = 0; b < grp.length; b++) {
          if (a === b) continue;
          var ib = grp[b], rb = raws[ib];
          if (rb.isText) continue;
          var ib2 = flat[ib].item;
          if (!(ia2.children && ia2.children.length) === false) { /* noop */ }
          if (!boxesCoincide(ia2, ib2)) continue;

          // YOL 1 — renk: aynı hue, üstteki (B) daha açık, alttaki (A) daha koyu
          if (ra.hasSolid && rb.hasSolid && ra.fillS >= 0.05 && rb.fillS >= 0.05 &&
              rb.fillV > ra.fillV + 0.05 && hueDist(ra.fillH, rb.fillH) <= 12) {
            ra.darkerUnderlay = true;
            break;
          }
          // YOL 2 — geometri: A, B ile aynı kutu ama 1..%15 aşağı kaymış
          //         ve B görsel/dokulu (stud yüzeyi). Klasik 3D gölge.
          var dy = num(ia2.y, 0) - num(ib2.y, 0);
          if (dy > 0.5 && dy <= 0.15 * max(itemH(ia2), 1) + 8 &&
              (rb.hasImageFill || rb.isVectorKind || rb.hasGradient || rb.hasSolid) &&
              ra.nChildren === 0) {
            ra.darkerUnderlay = true;
            break;
          }
        }
      }
    }
    for (var c = 0; c < raws.length; c++) raws[c].isDarkerUnderlay = !!raws[c].darkerUnderlay;
  }

  function boxesCoincide(a, b) {
    var aw = itemW(a), ah = itemH(a), bw = itemW(b), bh = itemH(b);
    if (aw <= 0 || ah <= 0 || bw <= 0 || bh <= 0) return false;
    var ar = aw / ah, br = bw / bh;
    if (Math.abs(ar - br) > 0.25) return false;               // oran çok farklı
    var sc = (aw / bw + ah / bh) / 2;
    if (sc < 0.8 || sc > 1.25) return false;                   // boyut çok farklı
    var acx = num(a.x, 0) + aw / 2, acy = num(a.y, 0) + ah / 2;
    var bcx = num(b.x, 0) + bw / 2, bcy = num(b.y, 0) + bh / 2;
    var d = Math.sqrt((acx - bcx) * (acx - bcx) + (acy - bcy) * (acy - bcy));
    return d <= 0.25 * max(aw, ah);
  }

  function hueDist(h1, h2) {
    var d = Math.abs(h1 - h2) % 360;
    return d > 180 ? 360 - d : d;
  }

  // -------------------------------------------------------------------------
  // 9) PASS 3 — GUI DÜZEYİ SİNYALLER (grup J)
  // -------------------------------------------------------------------------
  function guiSummary(flat, raws, imageCount) {
    var g = emptyGui();
    var n = raws.length;
    g.nNodes = n;
    if (n === 0) return g;

    var sumV = 0, cntSolid = 0, muted = 0, accent = 0;
    var hues = {};
    var nGrad = 0, nImg = 0, nEff = 0, nShine = 0, nUnder = 0;
    var nStudTile = 0, cellMin = 0, cellMax = 0;
    var imgRefs = 0, uniq = 0;
    for (var k in imageCount) { uniq++; imgRefs += imageCount[k]; }

    for (var i = 0; i < n; i++) {
      var r = raws[i];
      if (r.hasSolid) {
        sumV += r.fillV; cntSolid++;
        if (r.fillS < 0.35) muted++;
        if (r.fillS > 0.6 && r.fillV > 0.6) accent++;
        hues[r.paletteBucket] = 1;
      } else if (r.hasGradient) {
        hues[r.paletteBucket] = 1;
      }
      // Kontur ve yazı renkleri de "birden fazla renkli"nin parçası:
      // kullanıcı "bazı renkler efekt niyetine güzel dursun diye yapılır" diyor.
      if (r.hasStroke && r.strokeS >= 0.12) {
        hues[paletteBucket(r.strokeH, r.strokeS, r.strokeV)] = 1;
      }
      if (r.isText && r.textS >= 0.12) {
        hues[paletteBucket(r.textH, r.textS, r.textV)] = 1;
      }
      if (r.hasGradient) nGrad++;
      if (r.hasImageFill) nImg++;
      if (r.hasAnyEffect) nEff++;
      if (r.isShineFrame) nShine++;
      if (r.isDarkerUnderlay) nUnder++;
      if (r.studTileGeo) {
        nStudTile++;
        var cc = num(r.tileCellW, 0);
        if (cc > 0) {
          cellMin = cellMin > 0 ? Math.min(cellMin, cc) : cc;
          cellMax = Math.max(cellMax, cc);
        }
      }
    }

    var nHue = 0;
    for (var hh in hues) nHue++;

    g.nSolid = cntSolid;
    g.darknessIndex = cntSolid ? clamp01(1 - (sumV / cntSolid)) : 0;
    g.mutedBaseRate = cntSolid ? clamp01(muted / cntSolid) : 0;
    g.accentPopRate = cntSolid ? clamp01(accent / cntSolid) : 0;
    g.hueDiversity = clamp01(nHue / 12);
    g.gradientRate = clamp01(nGrad / n);
    g.imageDrivenRate = clamp01(nImg / n);
    g.effectDensity = clamp01(nEff / n);
    g.reuseRate = (imgRefs > 0) ? clamp01(1 - (uniq / imgRefs)) : 0;
    g.darkerUnderlayRate = cntSolid ? clamp01(nUnder / cntSolid) : clamp01(nUnder / n);
    g.shineFrameRate = clamp01(nShine / n);
    g.nImages = imgRefs;
    g.nUniqueImages = uniq;
    // Stud geometrisi: kaç düğüm stud-benzeri döşeme kullanıyor + tek bir hücre ölçüsünde mi?
    // "tek doku" kuralı: aynı hücre = aynı doku; farklı hücreler = karışık doku → stud değil.
    g.nStudTile = nStudTile;
    g.studTileRate = clamp01(nStudTile / n);
    g.studCellW = nStudTile > 0 ? cellMin : 0;
    g.studCellUniform = !!(nStudTile > 0 && cellMin > 0 && (cellMax / cellMin) <= 1.25);
    g.nGradients = nGrad;
    g.nEffects = nEff;
    g.nDarkerUnderlay = nUnder;
    g.nShineFrame = nShine;
    return g;
  }

  function copyGui(raw, g) {
    raw.darknessIndex = g.darknessIndex;
    raw.mutedBaseRate = g.mutedBaseRate;
    raw.hueDiversity = g.hueDiversity;
    raw.accentPopRate = g.accentPopRate;
    raw.effectDensity = g.effectDensity;
    raw.gradientRate = g.gradientRate;
    raw.reuseRate = g.reuseRate;
    raw.imageDrivenRate = g.imageDrivenRate;
    raw.darkerUnderlayRate = g.darkerUnderlayRate;
    raw.shineFrameRate = g.shineFrameRate;
    // stil yuvaları: A10 dedektörü doldurana kadar "belirsiz"
    raw.styleStud = false; raw.styleAnime = false;
    raw.styleCartoon = false; raw.styleBelirsiz = true;
    raw.styleConf = 0;
  }

  function applyStyle(raw, st) {
    raw.styleStud = !!st.stud;
    raw.styleAnime = !!st.anime;
    raw.styleCartoon = !!st.cartoon;
    raw.styleBelirsiz = !!st.belirsiz;
    raw.styleConf = clamp01(num(st.conf, 0));
  }

  // -------------------------------------------------------------------------
  return {
    extract: extract,
    tokenize: tokenize,
    rgb2hsv: rgb2hsv,
    paletteBucket: paletteBucket,
    buildClusters: buildClusters,
    imageFileOf: imageFileOf,
    utf8len: utf8len,
    foldLower: foldLower,
    foldUpper: foldUpper,
    hasUpper: hasUpper,
    splitWords: splitWords,
    trimStr: trimStr,
    NAME_TOKENS: NAME_TOKENS,
    FX_TOKENS_ORDERED: FX_TOKENS_ORDERED,
    FX_TOKEN_KIND: FX_TOKEN_KIND,
    STUD_TOKENS: STUD_TOKENS
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = EIRaw;
