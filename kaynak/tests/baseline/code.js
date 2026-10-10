// EasyImport v4 - Figma -> Roblox Studio (Ücretsiz, Sınırsız, Çoklu Seçim & Akıllı İkon Birleştirme)
// v4: Etiketler artık TAM KELİME eşleşir (örn. 'Top_buttons' veya 'Hero_images' yanlışlıkla etiket sayılmaz).
// v2: Görsel tekilleştirme (dedupe) + gereksiz frame sadeleştirme + süs grubu birleştirme

figma.showUI(__html__, { width: 520, height: 820, title: 'EasyImport Pro · Figma', themeColors: false });

// ---------- 2x3 matris yardımcıları ----------
function mul(a, b) {
  return [
    [
      a[0][0] * b[0][0] + a[0][1] * b[1][0],
      a[0][0] * b[0][1] + a[0][1] * b[1][1],
      a[0][0] * b[0][2] + a[0][1] * b[1][2] + a[0][2],
    ],
    [
      a[1][0] * b[0][0] + a[1][1] * b[1][0],
      a[1][0] * b[0][1] + a[1][1] * b[1][1],
      a[1][0] * b[0][2] + a[1][1] * b[1][2] + a[1][2],
    ],
  ];
}
function inv(m) {
  var a = m[0][0], c = m[0][1], e = m[0][2];
  var b = m[1][0], d = m[1][1], f = m[1][2];
  var det = a * d - b * c || 1;
  return [
    [d / det, -c / det, (c * f - d * e) / det],
    [-b / det, a / det, (b * e - a * f) / det],
  ];
}
function apply(m, x, y) {
  return { x: m[0][0] * x + m[0][1] * y + m[0][2], y: m[1][0] * x + m[1][1] * y + m[1][2] };
}

var r2 = function (n) { return Math.round((Number(n) || 0) * 100) / 100; };
var c255 = function (c) {
  return { r: Math.round((c.r || 0) * 255), g: Math.round((c.g || 0) * 255), b: Math.round((c.b || 0) * 255) };
};

// ---------- Boyalar ----------
function convertPaints(arr, w, h) {
  var out = [];
  if (!Array.isArray(arr)) return out;
  for (var i = 0; i < arr.length; i++) {
    var p = arr[i];
    if (!p || p.visible === false) continue;
    var op = p.opacity == null ? 1 : p.opacity;
    if (p.type === 'SOLID') {
      out.push({ type: 'SOLID', color: c255(p.color), opacity: r2(op) });
    } else if (p.type === 'GRADIENT_LINEAR' || p.type === 'GRADIENT_RADIAL' || p.type === 'GRADIENT_ANGULAR' || p.type === 'GRADIENT_DIAMOND') {
      var gi = inv(p.gradientTransform);
      var s = apply(gi, 0, 0.5);
      var e = apply(gi, 1, 0.5);
      var angle = Math.atan2((e.y - s.y) * h, (e.x - s.x) * w) * 180 / Math.PI;
      out.push({
        type: p.type === 'GRADIENT_LINEAR' ? 'GRADIENT' : 'GRADIENT_OTHER',
        angle: r2(angle),
        opacity: r2(op),
        stops: p.gradientStops.map(function (st) {
          return { pos: r2(st.position), color: c255(st.color), opacity: r2(st.color.a == null ? 1 : st.color.a) };
        }),
      });
    } else if (p.type === 'IMAGE') {
      out.push({ type: 'IMAGE', scaleMode: p.scaleMode, opacity: r2(op) });
    }
  }
  return out;
}

function fontWeightOf(style) {
  var s = String(style || '').toLowerCase();
  if (s.indexOf('thin') > -1) return 100;
  if (s.indexOf('extralight') > -1 || s.indexOf('extra light') > -1) return 200;
  if (s.indexOf('light') > -1) return 300;
  if (s.indexOf('semibold') > -1 || s.indexOf('semi bold') > -1 || s.indexOf('demi') > -1) return 600;
  if (s.indexOf('extrabold') > -1 || s.indexOf('extra bold') > -1) return 800;
  if (s.indexOf('black') > -1 || s.indexOf('heavy') > -1) return 900;
  if (s.indexOf('bold') > -1) return 700;
  if (s.indexOf('medium') > -1) return 500;
  return 400;
}

var VECTOR_TYPES = { VECTOR: 1, BOOLEAN_OPERATION: 1, STAR: 1, POLYGON: 1, LINE: 1 };
var FRAME_TYPES = { FRAME: 1, COMPONENT: 1, INSTANCE: 1, COMPONENT_SET: 1, RECTANGLE: 1, ELLIPSE: 1, SECTION: 1 };

function safeFile(name, id) {
  var base = String(name)
    .replace(/^#/, '')
    .replace(/^img:/i, '')
    .replace(/_(imagelabel|imagebutton|image|lock|button|btn|scroll|scrolling|aspect|canvas|textbox|videoframe)(?![a-z])/gi, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'icon';
  return base + '_' + String(id).replace(/[^0-9a-zA-Z]+/g, '-') + '.png';
}

// Bir Group/Frame'in yalnızca vektör çizimlerden oluşan tek bir ikon olup olmadığını kontrol eder.
// Böylece 20 parçalı bir ikon 20 ayrı PNG yerine TEK BİR PNG olarak dışa aktarılır!
function isPureVectorGroup(node) {
  if (!node || !('children' in node) || !node.children || node.children.length === 0) return false;
  var visCount = 0;
  for (var i = 0; i < node.children.length; i++) {
    var ch = node.children[i];
    if (!ch || ch.visible === false) continue;
    visCount++;
    var ct = ch.type;
    if (VECTOR_TYPES[ct]) continue;
    if ((ct === 'GROUP' || ct === 'FRAME' || ct === 'BOOLEAN_OPERATION') && isPureVectorGroup(ch)) continue;
    return false;
  }
  return visCount > 0;
}


// ---------- v2: Etiket / boya / imza yardımcıları ----------
// v4: '_kelime' parçalarını TAM kelime olarak ayırır (önek eşleşmesi yok).
var TAG_TOKENS = { button: 1, btn: 1, scroll: 1, scrollx: 1, scrolly: 1, scrollingframe: 1, canvas: 1, canvasgroup: 1, viewport: 1, viewportframe: 1,
  aspect: 1, hover: 1, clicked: 1, input: 1, textbox: 1, textlabel: 1, textbutton: 1, imagelabel: 1, imagebutton: 1, image: 1, lock: 1,
  ignore: 1, exclude: 1, frame: 1, keep: 1, nodim: 1, gray: 1, videoframe: 1, video: 1 };
function nameTokens(name) {
  var out = {};
  var n = String(name || '').toLowerCase().replace(/\u0307/g, '').replace(/\u0131/g, 'i');
  var re = /_([a-z]+)/g, m;
  while ((m = re.exec(n)) !== null) out[m[1]] = 1;
  // Sınıf adı adın İÇİNDE doğrudan geçiyorsa (alt çizgi şart değil): "KQWEAMKFWImageButton"
  var CLS = ['imagebutton', 'imagelabel', 'textbutton', 'textlabel', 'textbox', 'scrollingframe', 'viewportframe', 'canvasgroup', 'videoframe'];
  for (var ci = 0; ci < CLS.length; ci++) if (n.indexOf(CLS[ci]) > -1) out[CLS[ci]] = 1;
  return out;
}
function hasToken(name, list) {
  var t = nameTokens(name);
  for (var i = 0; i < list.length; i++) if (t[list[i]]) return true;
  return false;
}
function isIgnoredName(name) { return hasToken(name, ['ignore', 'exclude']); }
function isScrollNode(node) {
  return !!(node && node.overflowDirection && node.overflowDirection !== 'NONE');
}
function hasTag(name) {
  var n = String(name || '').toLowerCase();
  var tk = nameTokens(n);
  for (var k in tk) if (TAG_TOKENS[k]) return true;
  return n.indexOf('#') === 0 || n.indexOf('img:') === 0;
}

function paintVisible(p) {
  return p && p.visible !== false && (p.opacity == null || p.opacity > 0.001);
}
function anyVisiblePaint(arr) {
  if (arr === figma.mixed) return true;
  if (!Array.isArray(arr)) return false;
  for (var i = 0; i < arr.length; i++) if (paintVisible(arr[i])) return true;
  return false;
}
function anyVisibleEffect(arr) {
  if (!Array.isArray(arr)) return false;
  for (var i = 0; i < arr.length; i++) if (arr[i] && arr[i].visible !== false) return true;
  return false;
}

function hashStr(s) {
  var h1 = 5381, h2 = 0;
  for (var i = 0; i < s.length; i++) {
    var c = s.charCodeAt(i);
    h1 = ((h1 << 5) + h1 + c) | 0;
    h2 = (c + (h2 << 6) + (h2 << 16) - h2) | 0;
  }
  return (h1 >>> 0).toString(36) + (h2 >>> 0).toString(36) + s.length.toString(36);
}

function paintSig(arr) {
  if (arr === figma.mixed) return 'mixed';
  if (!Array.isArray(arr)) return '';
  var s = [];
  for (var i = 0; i < arr.length; i++) {
    var p = arr[i];
    if (!p || p.visible === false) continue;
    var o = r2(p.opacity == null ? 1 : p.opacity);
    if (p.type === 'SOLID') {
      var c = c255(p.color);
      s.push('S' + c.r + ',' + c.g + ',' + c.b + ':' + o);
    } else if (p.type === 'IMAGE') {
      s.push('I' + p.imageHash + ':' + p.scaleMode + ':' + o + ':' + JSON.stringify(p.imageTransform || '') + ':' + (p.scalingFactor || ''));
    } else {
      s.push('G' + p.type + ':' + o + ':' + JSON.stringify(p.gradientTransform || '') + ':' + JSON.stringify(p.gradientStops || ''));
    }
  }
  return s.join('|');
}

function geomSig(node) {
  var s = '';
  try {
    if (node.fillGeometry && node.fillGeometry !== figma.mixed) for (var i = 0; i < node.fillGeometry.length; i++) s += node.fillGeometry[i].data;
    if (node.strokeGeometry && node.strokeGeometry !== figma.mixed) for (var j = 0; j < node.strokeGeometry.length; j++) s += '/' + node.strokeGeometry[j].data;
  } catch (e) { /* bazı düğümlerde yok */ }
  return s;
}

// Düğümün GÖRÜNÜMÜNÜ temsil eden imza. Aynı imza = birebir aynı PNG. (Çoklu kopya ikonlar tek dosya olur.)
function nodeSig(node, isTop) {
  var parts = [node.type, r2(node.width), r2(node.height)];
  if (isTop) {
    var rt = node.relativeTransform;
    if (rt) parts.push(r2(rt[0][0]) + ',' + r2(rt[0][1]) + ',' + r2(rt[1][0]) + ',' + r2(rt[1][1]));
  } else {
    parts.push(JSON.stringify(node.relativeTransform || [node.x, node.y]));
  }
  parts.push(r2(node.opacity == null ? 1 : node.opacity));
  parts.push(node.visible === false ? 'h' : 'v');
  if ('blendMode' in node) parts.push(node.blendMode);
  if ('fills' in node) parts.push(paintSig(node.fills));
  if ('strokes' in node) {
    parts.push(paintSig(node.strokes));
    parts.push(node.strokeWeight === figma.mixed ? 'mw' : r2(node.strokeWeight || 0));
    if ('strokeAlign' in node) parts.push(node.strokeAlign);
  }
  if ('cornerRadius' in node) {
    parts.push(node.cornerRadius === figma.mixed
      ? [node.topLeftRadius, node.topRightRadius, node.bottomLeftRadius, node.bottomRightRadius].join(',')
      : r2(node.cornerRadius || 0));
  }
  if ('effects' in node) parts.push(JSON.stringify(node.effects || []));
  if ('clipsContent' in node) parts.push(node.clipsContent ? 'c' : 'n');
  var g = geomSig(node);
  if (g) parts.push('g' + hashStr(g));
  var out = parts.join('~');
  if ('children' in node && node.children) {
    var cs = [];
    for (var i = 0; i < node.children.length; i++) cs.push(nodeSig(node.children[i], false));
    out += '[' + cs.join(';') + ']';
  }
  return out;
}

function exportScale(node) {
  var m = Math.max(node.width || 1, node.height || 1);
  return Math.max(0.5, Math.min(2, 1024 / m)); // Roblox zaten 1024 px üstünü küçültür
}

function countNodes(node) {
  if (!node || node.visible === false) return 0;
  if (isIgnoredName(node.name)) return 0;
  var n = 1;
  if ('children' in node && node.children) for (var i = 0; i < node.children.length; i++) n += countNodes(node.children[i]);
  return n;
}

// Metin içermeyen, sadece şekil/vektörlerden oluşan "süs" ağacı mı?
function scanDecor(node, acc) {
  if (!node || node.visible === false) return true;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  var t = node.type;
  if (t === 'TEXT') return false;
  if (VECTOR_TYPES[t]) { acc.vec++; acc.n++; return true; }
  if (t === 'RECTANGLE' || t === 'ELLIPSE') { acc.n++; return true; }
  if (t === 'GROUP' || t === 'FRAME' || t === 'INSTANCE' || t === 'COMPONENT' || t === 'BOOLEAN_OPERATION') {
    acc.n++;
    if (node.children) for (var i = 0; i < node.children.length; i++) if (!scanDecor(node.children[i], acc)) return false;
    return true;
  }
  return false;
}
function isDecorGroup(node) {
  var t = node.type;
  if (t !== 'GROUP' && t !== 'FRAME' && t !== 'INSTANCE' && t !== 'COMPONENT') return false;
  if (!node.children || node.children.length === 0) return false;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  var w = node.width || 0, h = node.height || 0;
  if (w < 1 || h < 1 || w > 2200 || h > 2200) return false;
  var acc = { vec: 0, n: 0 };
  if (!scanDecor(node, acc)) return false;
  // Sadece tek renk bir kutu + dolgu değilse: en az 1 vektör ve 2 şekil, ya da 4+ şekil
  return (acc.vec >= 1 && acc.n >= 2) || acc.n >= 4;
}

function childrenInsideBounds(node) {
  var wb = node.absoluteBoundingBox;
  if (!wb) return false;
  for (var i = 0; i < node.children.length; i++) {
    var ch = node.children[i];
    if (!ch || ch.visible === false) continue;
    var cb = ch.absoluteRenderBounds || ch.absoluteBoundingBox;
    if (!cb) return false;
    if (cb.x < wb.x - 1 || cb.y < wb.y - 1 || cb.x + cb.width > wb.x + wb.width + 1 || cb.y + cb.height > wb.y + wb.height + 1) return false;
  }
  return true;
}

// Görsel olarak HİÇBİR şey katmayan sarmalayıcı frame mi? (dolgu yok, çizgi yok, köşe yok, gölge yok, opaklık 1)
function isPlainWrapper(node) {
  var t = node.type;
  if (t !== 'FRAME' && t !== 'INSTANCE' && t !== 'COMPONENT') return false;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  if (!node.children || node.children.length === 0) return false;
  if ((node.opacity == null ? 1 : node.opacity) < 0.999) return false;
  if (node.isMask) return false;
  if (node.blendMode && node.blendMode !== 'PASS_THROUGH' && node.blendMode !== 'NORMAL') return false;
  if ('fills' in node && anyVisiblePaint(node.fills)) return false;
  if ('strokes' in node && anyVisiblePaint(node.strokes)) return false;
  if ('effects' in node && anyVisibleEffect(node.effects)) return false;
  if ('cornerRadius' in node && (node.cornerRadius === figma.mixed || node.cornerRadius > 0)) return false;
  for (var i = 0; i < node.children.length; i++) if (node.children[i].isMask) return false;
  if (node.clipsContent && !childrenInsideBounds(node)) return false;
  return true;
}

// Aynı görünüm = aynı PNG
function registerImage(node, item, images, opts) {
  var ctx = opts.ctx;
  if (opts.dedupe !== false) {
    var key;
    try { key = hashStr(nodeSig(node, true)); } catch (e) { key = null; }
    if (key) {
      if (ctx.byKey[key]) {
        item.image = ctx.byKey[key];
        ctx.stats.dupes++;
        return;
      }
      item.image = safeFile(node.name, node.id);
      ctx.byKey[key] = item.image;
      images.push({ file: item.image, node: node });
      return;
    }
  }
  item.image = safeFile(node.name, node.id);
  images.push({ file: item.image, node: node });
}

// v5: PNG, efektleri (glow/gölge) dahil render sınırlarıyla dışa aktarılır.
// Katman kutusuna sığdırılırsa görsel küçülür -> konumu render sınırlarına göre hesapla.
function applyRenderBounds(node, item, contAbs) {
  try {
    var rb = node.absoluteRenderBounds, bb = node.absoluteBoundingBox;
    if (!rb || !bb) return;
    if (Math.abs(item.rot || 0) > 0.01) return;
    if (Math.abs(rb.width - bb.width) < 0.5 && Math.abs(rb.height - bb.height) < 0.5 &&
        Math.abs(rb.x - bb.x) < 0.5 && Math.abs(rb.y - bb.y) < 0.5) return;
    var p = apply(inv(contAbs), rb.x, rb.y);
    item.x = r2(p.x); item.y = r2(p.y); item.w = r2(rb.width); item.h = r2(rb.height);
  } catch (e) {}
}

// v7: mask kapsayan grup/frame'in içindeki yazılar (yazı düzenlenebilir kalır, görsele gömülmez)
function collectTexts(node, acc) {
  acc = acc || [];
  if (!node || node.visible === false) return acc;
  if (node.type === 'TEXT') { acc.push(node); return acc; }
  if ('children' in node) {
    for (var i = 0; i < node.children.length; i++) collectTexts(node.children[i], acc);
  }
  return acc;
}
function attachHide(node, images, texts) {
  for (var q = images.length - 1; q >= 0; q--) {
    if (images[q].node === node) { images[q].hide = texts; break; }
  }
}
function isMaskNode(n) {
  if (!n) return false;
  if (n.isMask === true) return true;
  return /^\s*mask([\s_\-]?\d.*)?\s*$/i.test(n.name || '');
}
var CONTAINER_TYPES = ['GROUP', 'FRAME', 'COMPONENT', 'INSTANCE', 'COMPONENT_SET'];

// v8: geçici klonlar (yumuşak yazı gölgesi görseli için); dışa aktarım bitince silinir
var TMP_CLONES = [];
function cleanupTmp() {
  for (var i = 0; i < TMP_CLONES.length; i++) { try { TMP_CLONES[i].remove(); } catch (e) {} }
  TMP_CLONES = [];
}

// ---------- Node -> JSON ----------
function walk(node, contAbs, list, images, opts, isRoot) {
  if (!node || node.visible === false) return;
  var ctx = opts.ctx;
  var lowerName = String(node.name || '').toLowerCase();
  if (isIgnoredName(node.name)) return;
  var t = node.type;
  var tagged = hasTag(node.name);

  var forceImage = hasToken(node.name, ['image', 'imagelabel', 'imagebutton', 'lock']) || lowerName.indexOf('#') === 0 || lowerName.indexOf('img:') === 0;

  // v7: bağımsız mask (grup/frame altında değilse) tek parça görsel
  if (isMaskNode(node) && node.parent && CONTAINER_TYPES.indexOf(node.parent.type) < 0) forceImage = true;

  // --- v2: görünmez / boş hayalet katmanları at ---
  if (!isRoot && !tagged) {
    if (node.opacity != null && node.opacity <= 0.001) { ctx.stats.ghost++; return; }
    if (!VECTOR_TYPES[t] && t !== 'TEXT' && ((node.width || 0) < 0.5 || (node.height || 0) < 0.5)) { ctx.stats.ghost++; return; }
    if ((t === 'RECTANGLE' || t === 'ELLIPSE') &&
        !anyVisiblePaint('fills' in node ? node.fills : []) &&
        !anyVisiblePaint('strokes' in node ? node.strokes : []) &&
        !anyVisibleEffect('effects' in node ? node.effects : [])) {
      ctx.stats.ghost++;
      return;
    }
  }

  var mergeVectorGroup = (opts.mergeVectors !== false) && isPureVectorGroup(node);
  // v2: metinsiz süs/ikon grupları (arka plan daire + ikon, dekor katmanları...) TEK PNG
  var mergeDecor = !isRoot && !forceImage && !mergeVectorGroup && (opts.mergeDecor !== false) && isDecorGroup(node);
  if (mergeDecor) ctx.stats.decorMerged++;
  // v7: mask içeren grup/frame -> tek parça görsel (efektler mask'ın içinde); yazılar üstte düzenlenebilir kalır
  var maskTexts = null;
  if (!isRoot && !forceImage && CONTAINER_TYPES.indexOf(t) > -1 && 'children' in node) {
    for (var mc = 0; mc < node.children.length; mc++) {
      if (isMaskNode(node.children[mc])) { maskTexts = collectTexts(node, []); opts.ctx.stats.maskMerged = (opts.ctx.stats.maskMerged || 0) + 1; break; }
    }
  }
  var mergeMask = !!maskTexts;
  var mergeAny = mergeVectorGroup || mergeDecor || mergeMask;

  // GROUP ise ve birleştirilmeyecekse sadece içindekileri gez
  if (t === 'GROUP' && !forceImage && !mergeAny) {
    if ('children' in node) {
      for (var g = 0; g < node.children.length; g++) walk(node.children[g], contAbs, list, images, opts, false);
    }
    return;
  }

  // v2: Görsele hiçbir şey katmayan sarmalayıcı frame -> çocukları bir üst seviyeye taşı (frame sayısını düşürür)
  if (!isRoot && !forceImage && !mergeAny && opts.flatten !== false && isPlainWrapper(node)) {
    ctx.stats.flattened++;
    for (var f = 0; f < node.children.length; f++) walk(node.children[f], contAbs, list, images, opts, false);
    return;
  }

  var isVector = !!VECTOR_TYPES[t] || forceImage || mergeAny;
  if (!isVector && t !== 'TEXT' && !FRAME_TYPES[t]) {
    if ('children' in node && Array.isArray(node.children)) {
      for (var k = 0; k < node.children.length; k++) walk(node.children[k], contAbs, list, images, opts, false);
    }
    return;
  }

  var w = node.width || 1, h = node.height || 1;
  var nodeTransform = node.absoluteTransform || [[1, 0, node.x || 0], [0, 1, node.y || 0]];
  var rel = mul(inv(contAbs), nodeTransform);
  var center = apply(rel, w / 2, h / 2);
  var rot = Math.atan2(rel[1][0], rel[0][0]) * 180 / Math.PI;

  var item = {
    name: node.name || 'Layer',
    kind: (t === 'TEXT' && !forceImage) ? 'text' : isVector ? 'vector' : t === 'ELLIPSE' ? 'ellipse' : 'frame',
    x: r2(center.x - w / 2),
    y: r2(center.y - h / 2),
    w: r2(w),
    h: r2(h),
    rot: r2(rot),
    opacity: r2(node.opacity == null ? 1 : node.opacity),
  };

  var hasChildren = !isVector && ('children' in node) && node.children.length > 0 && t !== 'INSTANCE_NOCHILD';

  if (t === 'TEXT' && !forceImage) {
    var fn = (node.fontName === figma.mixed && node.characters.length > 0) ? node.getRangeFontName(0, 1) : node.fontName;
    var fs = (node.fontSize === figma.mixed && node.characters.length > 0) ? node.getRangeFontSize(0, 1) : node.fontSize;
    var fills = (node.fills === figma.mixed && node.characters.length > 0) ? node.getRangeFills(0, 1) : node.fills;
    var tf = convertPaints(fills, w, h);
    var color = { r: 255, g: 255, b: 255 };
    var top = tf[tf.length - 1];
    var alpha = 1;
    if (top) {
      if (top.type === 'SOLID') { color = top.color; alpha = top.opacity; }
      else if (top.stops && top.stops.length) { color = top.stops[0].color; alpha = top.opacity; }
    }
    item.text = {
      characters: node.characters || '',
      fontSize: r2(typeof fs === 'number' ? fs : 16),
      fontFamily: (fn && fn.family) ? fn.family : 'Inter',
      fontWeight: fontWeightOf(fn && fn.style),
      italic: String((fn && fn.style) || '').toLowerCase().indexOf('italic') > -1,
      color: color,
      opacity: r2(alpha),
      align: node.textAlignHorizontal || 'LEFT',
      vAlign: node.textAlignVertical || 'TOP',
      wrap: node.textAutoResize !== 'WIDTH_AND_HEIGHT',
      autoW: node.textAutoResize === 'WIDTH_AND_HEIGHT',
    };
    // v3: yazı gradient'i
    if (top && top.stops && top.stops.length >= 2) {
      item.text.gradient = { angle: top.angle, opacity: top.opacity, stops: top.stops };
    }
    // v3: yazı stroke'u
    try {
      if (Array.isArray(node.strokes) && node.strokes.length) {
        var tsp = convertPaints(node.strokes, w, h).filter(function (p) { return p.type === 'SOLID' || p.type === 'GRADIENT'; });
        var tsw = (typeof node.strokeWeight === 'number') ? node.strokeWeight : 0;
        if (tsp.length && tsw > 0) {
          var tst = tsp[tsp.length - 1];
          var tstCol = tst.type === 'SOLID' ? tst.color : (tst.stops && tst.stops.length ? tst.stops[0].color : { r: 0, g: 0, b: 0 });
          item.text.stroke = { color: tstCol, opacity: tst.opacity, weight: r2(tsw), align: node.strokeAlign || 'OUTSIDE' };
          if (tst.type === 'GRADIENT') item.text.stroke.gradient = { angle: tst.angle, opacity: tst.opacity, stops: tst.stops };
        }
      }
    } catch (e1) {}
    // v3/v4: karışık stil (renk, boyut, font) -> segmentler
    try {
      var tmixed = (node.fills === figma.mixed || node.fontSize === figma.mixed || node.fontName === figma.mixed);
      if (tmixed && node.characters.length > 0 && node.getStyledTextSegments) {
        var tsegs = node.getStyledTextSegments(['fills', 'fontSize', 'fontName']);
        var tout = [];
        for (var tsi = 0; tsi < tsegs.length; tsi++) {
          var tsg = tsegs[tsi];
          var tpl = convertPaints(tsg.fills, w, h);
          var ttop = tpl[tpl.length - 1];
          var tcol = null;
          if (ttop) {
            if (ttop.type === 'SOLID') tcol = ttop.color;
            else if (ttop.stops && ttop.stops.length) tcol = ttop.stops[0].color;
          }
          tout.push({
            text: tsg.characters,
            color: tcol || color,
            fontSize: r2(tsg.fontSize),
            fontFamily: tsg.fontName && tsg.fontName.family,
            fontWeight: fontWeightOf(tsg.fontName && tsg.fontName.style),
          });
        }
        if (tout.length > 1) item.text.segments = tout;
      }
    } catch (e2) {}
    // v4: büyük/küçük harf ve alt çizgi / üstü çizili
    try {
      if (node.textCase && node.textCase !== figma.mixed && node.textCase !== 'ORIGINAL') item.text.textCase = node.textCase;
      if (node.textDecoration && node.textDecoration !== figma.mixed && node.textDecoration !== 'NONE') item.text.decoration = node.textDecoration;
    } catch (e3) {}
    // v9: tüm drop shadow'lar (Roblox UIShadow Text modu blur'lu gölgeyi de çizebilir)
    try {
      if (Array.isArray(node.effects)) {
        var tshs = [];
        for (var tei = 0; tei < node.effects.length; tei++) {
          var te = node.effects[tei];
          if (te.type === 'DROP_SHADOW' && te.visible !== false) {
            tshs.push({ x: r2(te.offset.x), y: r2(te.offset.y), blur: r2(te.radius || 0), spread: r2(te.spread || 0), color: c255(te.color), opacity: r2(te.color.a == null ? 1 : te.color.a) });
          }
        }
        if (tshs.length) { item.text.shadows = tshs; item.text.shadow = tshs[0]; }
      }
    } catch (e4) {}
    // v7: Figma'daki satır sayısı (kutu dar olduğunda metin taşıp sarılabilir)
    try {
      var rbT = node.absoluteRenderBounds;
      if (rbT && node.textAutoResize !== 'WIDTH_AND_HEIGHT' && node.fontSize !== figma.mixed) {
        var fszT = node.fontSize;
        var lhT = null;
        if (node.lineHeight && node.lineHeight !== figma.mixed) {
          if (node.lineHeight.unit === 'PIXELS') lhT = node.lineHeight.value;
          else if (node.lineHeight.unit === 'PERCENT') lhT = node.lineHeight.value / 100 * fszT;
        }
        if (!lhT) lhT = (node.height < fszT * 1.6) ? node.height : fszT * 1.2;
        var inkH = rbT.height - (item.text.stroke ? item.text.stroke.weight * 2 : 0);
        var nLines = Math.max(1, Math.round((inkH + 0.25 * lhT) / lhT));
        if (nLines > 1) item.text.lines = nLines;
      }
    } catch (e5) {}
    item.opacity = r2(item.opacity * alpha);
  } else {
    var paints = 'fills' in node && node.fills !== figma.mixed ? convertPaints(node.fills, w, h) : [];

    if (isVector) {
      registerImage(node, item, images, opts);
      if (maskTexts) attachHide(node, images, maskTexts);
      applyRenderBounds(node, item, contAbs);
      paints = [];
    } else {
      var hasImage = paints.some(function (p) { return p.type === 'IMAGE'; });
      if (hasImage && hasChildren) {
        paints = paints.filter(function (p) { return p.type !== 'IMAGE'; });
      } else if (hasImage) {
        registerImage(node, item, images, opts);
        applyRenderBounds(node, item, contAbs);
      }
    }
    item.fills = paints;

    // v6/v9: native UIShadow için tüm drop shadow'lar (katmanın kendi dolu kutusu gölge atıyorsa)
    if (!isVector && !item.image && Array.isArray(node.effects)) {
      var fshs = [];
      for (var fi = 0; fi < node.effects.length; fi++) {
        var fe = node.effects[fi];
        if (fe.type === 'DROP_SHADOW' && fe.visible !== false) {
          fshs.push({ x: r2(fe.offset.x), y: r2(fe.offset.y), blur: r2(fe.radius || 0), spread: r2(fe.spread || 0), color: c255(fe.color), opacity: r2(fe.color.a == null ? 1 : fe.color.a) });
        }
      }
      if (fshs.length) { item.shadows = fshs; item.shadow = fshs[0]; }
    }
    // v6: kaydırma (Prototype > Overflow)
    if (!isVector && isScrollNode(node)) item.scroll = node.overflowDirection;
    // v6: Auto Layout -> UIListLayout / UIGridLayout / UIPadding
    if (!isVector && hasChildren && node.layoutMode && node.layoutMode !== 'NONE' && (node.layoutMode === 'HORIZONTAL' || node.layoutMode === 'VERTICAL')) {
      var absKid = false;
      for (var ai = 0; ai < node.children.length; ai++) {
        if (node.children[ai].layoutPositioning === 'ABSOLUTE') { absKid = true; break; }
      }
      if (!absKid) {
        item.layout = {
          mode: node.layoutMode,
          gap: r2(node.itemSpacing || 0),
          wrapGap: r2(node.counterAxisSpacing || 0),
          wrap: node.layoutWrap === 'WRAP',
          pl: r2(node.paddingLeft || 0), pr: r2(node.paddingRight || 0),
          pt: r2(node.paddingTop || 0), pb: r2(node.paddingBottom || 0),
          primary: node.primaryAxisAlignItems || 'MIN',
          counter: node.counterAxisAlignItems || 'MIN'
        };
      }
    }

    if ('strokes' in node && Array.isArray(node.strokes) && node.strokes.length && !isVector) {
      var sp = convertPaints(node.strokes, w, h).filter(function (p) { return p.type === 'SOLID'; });
      var sw = node.strokeWeight === figma.mixed ? (node.strokeTopWeight || 1) : node.strokeWeight;
      if (sp.length && sw > 0) {
        var st = sp[sp.length - 1];
        item.stroke = { color: st.color, opacity: st.opacity, weight: r2(sw) };
      }
      // v5: birden fazla / gradient stroke (Figma sırasıyla)
      var spAll = convertPaints(node.strokes, w, h).filter(function (p) { return p.type === 'SOLID' || p.type === 'GRADIENT'; });
      if (spAll.length && sw > 0) {
        item.strokes = spAll;
        item.strokeWeight = r2(sw);
        item.strokeAlign = node.strokeAlign || 'INSIDE';
      }
    }

    if (t === 'ELLIPSE') {
      item.radius = 'full';
    } else if ('cornerRadius' in node) {
      var cr = node.cornerRadius === figma.mixed ? node.topLeftRadius : node.cornerRadius;
      item.radius = r2(cr || 0);
    }
    if ('clipsContent' in node) item.clips = !!node.clipsContent;

    if (hasChildren) {
      item.children = [];
      for (var i = 0; i < node.children.length; i++) {
        walk(node.children[i], nodeTransform, item.children, images, opts, false);
      }
    }

    // v2: içi boş, görünür hiçbir şeyi olmayan, etiketsiz frame'i hiç ekleme
    if (!isRoot && !tagged && !item.image && item.kind === 'frame' &&
        (!item.children || item.children.length === 0) &&
        (!item.fills || item.fills.length === 0) && !item.stroke && !item.strokes) {
      ctx.stats.emptyDropped++;
      return;
    }
  }

  list.push(item);
  if (maskTexts && item.image) {
    for (var mi = 0; mi < maskTexts.length; mi++) walk(maskTexts[mi], contAbs, list, images, opts, false);
  }
}

function getCombinedBounds(nodes) {
  var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (var i = 0; i < nodes.length; i++) {
    var n = nodes[i];
    if (!n || n.visible === false) continue;
    var b = n.absoluteBoundingBox;
    if (b) {
      if (b.x < minX) minX = b.x;
      if (b.y < minY) minY = b.y;
      if (b.x + b.width > maxX) maxX = b.x + b.width;
      if (b.y + b.height > maxY) maxY = b.y + b.height;
    } else if (n.absoluteTransform) {
      var tx = n.absoluteTransform[0][2] || 0;
      var ty = n.absoluteTransform[1][2] || 0;
      var nw = n.width || 100;
      var nh = n.height || 100;
      if (tx < minX) minX = tx;
      if (ty < minY) minY = ty;
      if (tx + nw > maxX) maxX = tx + nw;
      if (ty + nh > maxY) maxY = ty + nh;
    }
  }
  if (minX === Infinity) return { x: 0, y: 0, width: 800, height: 600 };
  return {
    x: minX,
    y: minY,
    width: Math.max(1, maxX - minX),
    height: Math.max(1, maxY - minY)
  };
}

function countItems(item, acc) {
  if (!item) return;
  acc.items++;
  if (item.kind === 'frame') acc.frames++;
  if (item.image) acc.imageRefs++;
  if (item.children) for (var i = 0; i < item.children.length; i++) countItems(item.children[i], acc);
}

async function doExport(opts) {
  cleanupTmp();
  var sel = figma.currentPage.selection;
  var targetNodes = (sel && sel.length > 0) ? sel : figma.currentPage.children;

  if (!targetNodes || targetNodes.length === 0) {
    if (!opts.analyzeOnly) figma.ui.postMessage({ type: 'error', message: 'Sayfada aktarılacak hiçbir katman bulunamadı.' });
    return;
  }

  if (!opts.analyzeOnly) figma.ui.postMessage({ type: 'progress', message: 'Katmanlar okunuyor (' + targetNodes.length + ' ana öğe)…' });
  opts.ctx = {
    byKey: {},
    stats: { dupes: 0, flattened: 0, decorMerged: 0, emptyDropped: 0, ghost: 0 },
  };
  var nodesBefore = 0;
  for (var nb = 0; nb < targetNodes.length; nb++) nodesBefore += countNodes(targetNodes[nb]);

  var images = [];
  var rootItem = null;
  var docName = 'Tasarim';
  var docW = 800;
  var docH = 600;

  if (
    targetNodes.length === 1 &&
    FRAME_TYPES[targetNodes[0].type] &&
    targetNodes[0].type !== 'RECTANGLE' &&
    targetNodes[0].type !== 'ELLIPSE' &&
    !isPureVectorGroup(targetNodes[0])
  ) {
    var singleRoot = targetNodes[0];
    var list = [];
    walk(singleRoot, singleRoot.absoluteTransform, list, images, opts, true);
    rootItem = list[0];
    docName = singleRoot.name || 'Tasarim';
    docW = r2(singleRoot.width || 800);
    docH = r2(singleRoot.height || 600);
  } else {
    var bounds = getCombinedBounds(targetNodes);
    var contAbs = [
      [1, 0, bounds.x],
      [0, 1, bounds.y]
    ];
    var childrenList = [];
    for (var idx = 0; idx < targetNodes.length; idx++) {
      // Seçilen üst seviye katmanlar "ekran" sayılır: kendileri birleştirilmez/düzleştirilmez
      walk(targetNodes[idx], contAbs, childrenList, images, opts, true);
    }
    docName = targetNodes.length === 1 ? (targetNodes[0].name || 'Tasarim') : (figma.currentPage.name || 'Coklu_Tasarim');
    docW = r2(bounds.width);
    docH = r2(bounds.height);
    rootItem = {
      name: docName,
      kind: 'frame',
      x: 0,
      y: 0,
      w: docW,
      h: docH,
      rot: 0,
      opacity: 1,
      fills: [],
      clips: false,
      children: childrenList
    };
  }

  var doc = {
    format: 'wispfree',
    version: 9,
    maskMerged: (opts.ctx && opts.ctx.stats && opts.ctx.stats.maskMerged) || 0,
    name: docName,
    width: docW,
    height: docH,
    root: rootItem,
  };

  var acc = { items: 0, frames: 0, imageRefs: 0 };
  countItems(rootItem, acc);
  var st = opts.ctx.stats;
  var stats = {
    nodesBefore: nodesBefore,
    itemsAfter: acc.items,
    framesAfter: acc.frames,
    imageRefs: acc.imageRefs,
    imagesUnique: images.length,
    dupes: st.dupes,
    flattened: st.flattened,
    decorMerged: st.decorMerged,
    emptyDropped: st.emptyDropped,
    ghost: st.ghost,
    exportFailed: 0,
  };

  if (opts.analyzeOnly) {
    cleanupTmp();
    figma.ui.postMessage({ type: 'analysis', stats: stats });
    return;
  }

  var files = [];
  if (opts.images) {
    for (var i = 0; i < images.length; i++) {
      figma.ui.postMessage({ type: 'progress', message: 'Görsel dışa aktarılıyor ' + (i + 1) + '/' + images.length });
      try {
        var hidden = [];
        var hideList = images[i].hide || [];
        for (var hi = 0; hi < hideList.length; hi++) {
          try { if (hideList[hi].visible) { hideList[hi].visible = false; hidden.push(hideList[hi]); } } catch (eh) {}
        }
        var bytes;
        try {
          bytes = await images[i].node.exportAsync({ format: 'PNG', constraint: { type: 'SCALE', value: exportScale(images[i].node) } });
        } finally {
          for (var ri = 0; ri < hidden.length; ri++) { try { hidden[ri].visible = true; } catch (er) {} }
        }
        files.push({ file: images[i].file, bytes: bytes });
      } catch (e) {
        stats.exportFailed++;
        files.push({ file: images[i].file, bytes: null });
      }
    }
  } else {
    for (var j = 0; j < images.length; j++) files.push({ file: images[j].file, bytes: null });
  }

  cleanupTmp();
  figma.ui.postMessage({ type: 'result', json: JSON.stringify(doc), name: docName, files: files, stats: stats });
}

function sendSelectionStatus() {
  var sel = figma.currentPage.selection;
  var count = sel ? sel.length : 0;
  var label = '';
  if (count === 0) {
    label = 'Tüm Sayfa (' + figma.currentPage.children.length + ' katman)';
  } else if (count === 1) {
    label = sel[0].name;
  } else {
    label = count + ' katman / frame birden seçili';
  }
  var dims = null;
  try {
    var tn = (sel && sel.length > 0) ? sel : figma.currentPage.children;
    if (tn && tn.length > 0) dims = getCombinedBounds(tn);
  } catch (e) {}
  figma.ui.postMessage({
    type: 'selection',
    name: label,
    count: count,
    pageCount: figma.currentPage.children.length,
    w: dims ? dims.width : null,
    h: dims ? dims.height : null
  });
}

var busy = false;
figma.ui.onmessage = function (msg) {
  if (msg.type === 'export' || msg.type === 'analyze') {
    if (busy) { if (msg.type === 'export') setTimeout(function () { figma.ui.onmessage(msg); }, 300); return; }
    busy = true;
    var o = msg.opts || {};
    o.analyzeOnly = msg.type === 'analyze';
    doExport(o).then(function () { busy = false; }, function (err) {
      busy = false;
      if (!o.analyzeOnly) figma.ui.postMessage({ type: 'error', message: 'Dışa aktarma hatası: ' + (err && err.message ? err.message : err) });
    });
  }
  if (msg.type === 'close') figma.closePlugin();
};

figma.on('selectionchange', sendSelectionStatus);
sendSelectionStatus();
