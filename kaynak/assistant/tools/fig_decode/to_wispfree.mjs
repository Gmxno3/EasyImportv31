#!/usr/bin/env node
/**
 * to_wispfree — `.fig` (Figma arşivi) → `wispfree v9/v10` sözleşmesi
 *
 * Neden: `master` dalındaki 10 gerçek tasarım projenin en büyük eksiği olan gerçek eğitim
 * verisini içeriyor (assistant/DURUM.md §6). `decode.mjs` ham kiwi düğümlerini verir; bu araç
 * onları `figma-plugin-all-in-one/code.js`'in `walk()` fonksiyonunun ÜRETTİĞİ sözleşmeye çevirir —
 * yani Figma'yı hiç açmadan, plugin'in çıktısının aynısını üretir.
 *
 * Sadakat notu: alan adları, yuvarlama (r2), renk ölçeği (0..255), `kind` kararı, `radius:'full'`,
 * `image` dosya adı (`safeFile`: <temizAd>_<id>.png) ve relatif konum/rot hesabı code.js ile
 * BİREBİR aynı mantığı izler. Kasıtlı farklar `FARKLAR` bölümünde listelidir.
 *
 * Kullanım:
 *   node to_wispfree.mjs <girdi.fig> -o <cikti-klasoru> [--tek] [--sessiz]
 *
 * Çıktı:
 *   <cikti-klasoru>/<tasarimAdi>.json                  wispfree v9 dökümanı
 *   <cikti-klasoru>/images/<ad>_<id>.png               item.image'ların gerçek PNG'leri
 *   <cikti-klasoru>/rapor.json                         üretim sayıları
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
import { join, basename } from 'node:path';
import { decodeFig } from './decode.mjs';

// ---------------------------------------------------------------- sabitler (code.js ile aynı)
const VECTOR_TYPES = { VECTOR: 1, BOOLEAN_OPERATION: 1, STAR: 1, POLYGON: 1, LINE: 1 };
const FRAME_TYPES = {
  FRAME: 1, COMPONENT: 1, INSTANCE: 1, COMPONENT_SET: 1, RECTANGLE: 1, ELLIPSE: 1, SECTION: 1,
};
const CONTAINER_TYPES = { GROUP: 1, FRAME: 1, COMPONENT: 1, INSTANCE: 1, COMPONENT_SET: 1 };
const CLIP_FIELD = 'frameMaskDisabled'; // kiwi karşılığı: clipsContent = (frameMaskDisabled === false)

// `.fig` dosya biçimi, Plugin API'sinde OLMAYAN düğüm tipleri kullanır. Plugin API'de
// yuvarlatılmış dikdörtgen ayrı bir tip değildir: `RECTANGLE` + `cornerRadius`'dur.
// Bu eşleme olmadan code.js'in `FRAME_TYPES` kontrolü tutmaz ve düğüm sessizce düşer
// (gerçek tasarımlarda 2.537 düğüm — en büyük kütle — bu yüzden kayboluyordu).
const FIG_TO_API = { ROUNDED_RECTANGLE: 'RECTANGLE' };
const apiType = (t) => FIG_TO_API[t] || t;

const r2 = (n) => Math.round((Number(n) || 0) * 100) / 100;
const c255 = (c) => ({
  r: Math.round((c?.r || 0) * 255),
  g: Math.round((c?.g || 0) * 255),
  b: Math.round((c?.b || 0) * 255),
});

/** code.js `safeFile` birebir portu (aynı regex'ler, aynı sonuç). */
export function safeFile(name, id) {
  const base =
    String(name)
      .replace(/^#/, '')
      .replace(/^img:/i, '')
      .replace(
        /_(imagelabel|imagebutton|image|lock|button|btn|scroll|scrolling|aspect|canvas|textbox|videoframe)(?![a-z])/gi,
        '',
      )
      .replace(/[^a-zA-Z0-9_-]+/g, '_')
      .replace(/^_+|_+$/g, '') || 'icon';
  return base + '_' + String(id).replace(/[^0-9a-zA-Z]+/g, '-') + '.png';
}

/** code.js `fontWeightOf` birebir portu. */
function fontWeightOf(style) {
  const s = String(style || '').toLowerCase();
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

// ---------------------------------------------------------------- 2x3 matris (code.js ile aynı)
const mul = (a, b) => [
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
function inv(m) {
  const a = m[0][0], c = m[0][1], e = m[0][2];
  const b = m[1][0], d = m[1][1], f = m[1][2];
  const det = a * d - b * c || 1;
  return [
    [d / det, -c / det, (c * f - d * e) / det],
    [-b / det, a / det, (b * e - a * f) / det],
  ];
}
const apply = (m, x, y) => ({
  x: m[0][0] * x + m[0][1] * y + m[0][2],
  y: m[1][0] * x + m[1][1] * y + m[1][2],
});

const t2m = (t) => (t ? [[t.m00 ?? 1, t.m01 ?? 0, t.m02 ?? 0], [t.m10 ?? 0, t.m11 ?? 1, t.m12 ?? 0]] : [[1, 0, 0], [0, 1, 0]]);

// ---------------------------------------------------------------- boyalar
function convertPaints(arr, w, h) {
  const out = [];
  if (!Array.isArray(arr)) return out;
  for (const p of arr) {
    if (!p || p.visible === false) continue;
    const op = p.opacity == null ? 1 : p.opacity;
    if (p.type === 'SOLID') {
      out.push({ type: 'SOLID', color: c255(p.color), opacity: r2(op) });
    } else if (p.type?.startsWith('GRADIENT_')) {
      const gt = t2m(p.transform);
      const gi = inv(gt);
      const s = apply(gi, 0, 0.5);
      const e = apply(gi, 1, 0.5);
      const angle = (Math.atan2((e.y - s.y) * h, (e.x - s.x) * w) * 180) / Math.PI;
      out.push({
        type: p.type === 'GRADIENT_LINEAR' ? 'GRADIENT' : 'GRADIENT_OTHER',
        angle: r2(angle),
        opacity: r2(op),
        stops: (p.stops || []).map((st) => ({
          pos: r2(st.position),
          color: c255(st.color),
          opacity: r2(st.color?.a == null ? 1 : st.color.a),
        })),
      });
    } else if (p.type === 'IMAGE') {
      out.push({
        type: 'IMAGE',
        scaleMode: p.imageScaleMode || 'FILL',
        opacity: r2(op),
        _hash: hexOf(p.image?.hash),
        _ref: p.image?.name || '',
        _origW: p.originalImageWidth,
        _origH: p.originalImageHeight,
        _scale: p.scale,
        _blend: p.blendMode,
      });
    }
  }
  return out;
}

const hexOf = (u8) => (u8 && u8.length ? Buffer.from(u8).toString('hex') : null);

// ---------------------------------------------------------------- düğüm ağacı
function buildTree(nodes) {
  const byGuid = new Map();
  for (const n of nodes) {
    if (!n?.guid) continue;
    byGuid.set(`${n.guid.sessionID}:${n.guid.localID}`, n);
  }
  const childrenOf = new Map();
  for (const n of nodes) {
    if (!n?.parentIndex?.guid || !n.guid) continue;
    const pg = `${n.parentIndex.guid.sessionID}:${n.parentIndex.guid.localID}`;
    if (!childrenOf.has(pg)) childrenOf.set(pg, []);
    childrenOf.get(pg).push(n);
  }
  // `isMaskNode(node) && !CONTAINER_TYPES[parent.type]` kontrolü için ebeveyn tipi
  for (const [, arr] of childrenOf) {
    const p = byGuid.get(gk(arr[0].parentIndex.guid));
    if (p) for (const c of arr) c.parentType = p.type;
  }
  // Figma `position` alanı ASCII sıralı kesirli indekstir → düz sözlük karşılaştırması doğru sırayı verir
  for (const [, arr] of childrenOf) {
    arr.sort((a, b) => {
      const pa = a.parentIndex?.position ?? '';
      const pb = b.parentIndex?.position ?? '';
      return pa < pb ? -1 : pa > pb ? 1 : 0;
    });
  }
  return { byGuid, childrenOf };
}

const gk = (g) => `${g.sessionID}:${g.localID}`;

// ---------------------------------------------------------------- walk (code.js karşılığı)
function makeWalker(ctx) {
  function walk(node, parentAbs, out, isRoot, ax = 0, ay = 0) {
    if (!node) return;
    if (node.visible === false) return;
    if (node.phase === 'REMOVED') return;
    if (isIgnoredName(node.name)) return;          // `_ignore` / `_exclude`

    const t = apiType(node.type); // .fig -> Plugin API tip eşlemesi (ROUNDED_RECTANGLE -> RECTANGLE)
    const lowerName = String(node.name || '').toLowerCase();
    const tagged = hasTag(node.name);
    let forceImage = hasToken(node.name, ['image', 'imagelabel', 'imagebutton', 'lock']) ||
      lowerName.startsWith('#') || lowerName.startsWith('img:');
    if (isMaskNode(node) && node.parentType && !CONTAINER_TYPES[apiType(node.parentType)]) forceImage = true;

    if (!isRoot && !tagged) {
      const op = node.opacity == null ? 1 : node.opacity;
      if (op <= 0.001) { ctx.stats.ghost++; return; }
      const sz = node.size || {};
      if (!VECTOR_TYPES[t] && t !== 'TEXT' && ((sz.x || 0) < 0.5 || (sz.y || 0) < 0.5)) { ctx.stats.ghost++; return; }
      if ((t === 'RECTANGLE' || t === 'ELLIPSE') && !anyVisiblePaint(node.fillPaints) && !anyVisiblePaint(node.strokePaints) && !anyVisibleEffect(node.effects)) {
        ctx.stats.ghost++;
        return;
      }
    }

    // ---- yapı şekillendirme (code.js v2/v7) ----
    const mergeVectorGroup = isPureVectorGroup(node);
    const mergeDecor = !isRoot && !forceImage && !mergeVectorGroup && isDecorGroup(node);
    let maskTexts = null;
    if (!isRoot && !forceImage && CONTAINER_TYPES[t] && node.children?.length) {
      for (const mc of node.children) {
        if (isMaskNode(mc)) { maskTexts = collectTexts(node, []); ctx.stats.maskMerged++; break; }
      }
    }
    const mergeMask = !!maskTexts;
    const mergeAny = mergeVectorGroup || mergeDecor || mergeMask;
    if (mergeDecor) ctx.stats.decorMerged++;
    if (mergeVectorGroup) ctx.stats.vectorMerged++;

    // GROUP birleştirilmeyecekse: grup KENDİSİ düğüm olmaz, yalnızca içindekiler gezinilir
    if (t === 'GROUP' && !forceImage && !mergeAny) {
      for (const g of childListOf(node)) walk(g, parentAbs, out, false, ax + (g.transform?.m02 || 0), ay + (g.transform?.m12 || 0));
      return;
    }

    // Görsele hiçbir şey katmayan sarmalayıcı frame -> çocukları üst seviyeye taşı
    if (!isRoot && !forceImage && !mergeAny && isPlainWrapper(node, ax, ay)) {
      ctx.stats.flattened++;
      for (const f of childListOf(node)) walk(f, parentAbs, out, false, ax + (f.transform?.m02 || 0), ay + (f.transform?.m12 || 0));
      return;
    }

    const isVector = !!VECTOR_TYPES[t] || forceImage || mergeAny;
    if (!isVector && t !== 'TEXT' && !FRAME_TYPES[t]) {
      for (const c of childListOf(node)) walk(c, parentAbs, out, false);
      return;
    }

    const w = node.size?.x || 1;
    const h = node.size?.y || 1;
    // KRİTİK: `.fig` içinde `transform` ZATEN ebeveyn koordinat uzayına göre relatif.
    // (code.js'te `inv(contAbs) * node.absoluteTransform` hesabı bununla aynı sonucu verir.)
    const nodeTransform = t2m(node.transform);
    // Kök düğümde `.fig` transform'u SAYFA koordinatıdır; code.js kökü daima (0,0)'a koyar
    // (contAbs = kökün kendi absoluteTransform'u → rel = birim matris).
    const rel = isRoot ? [[1, 0, 0], [0, 1, 0]] : nodeTransform;
    const center = apply(rel, w / 2, h / 2);
    const rot = (Math.atan2(rel[1][0], rel[0][0]) * 180) / Math.PI;

    const item = {
      name: node.name || 'Layer',
      kind: t === 'TEXT' && !forceImage ? 'text' : isVector ? 'vector' : t === 'ELLIPSE' ? 'ellipse' : 'frame',
      x: r2(center.x - w / 2),
      y: r2(center.y - h / 2),
      w: r2(w),
      h: r2(h),
      rot: r2(rot),
      opacity: r2(node.opacity == null ? 1 : node.opacity),
    };

    let kids = [];
    if (!isVector) {
      for (const c of ctx.childrenOf.get(gk(node.guid)) || []) {
        if (c.phase === 'REMOVED' || c.visible === false) continue;
        kids.push(c);
      }
    }
    const hasChildren = kids.length > 0;

    if (item.kind === 'text') {
      const fn = node.fontName || {};
      const paints = convertPaints(node.fillPaints, w, h);
      const top = paints[paints.length - 1];
      let color = { r: 255, g: 255, b: 255 };
      let alpha = 1;
      if (top) {
        if (top.type === 'SOLID') { color = top.color; alpha = top.opacity; }
        else if (top.stops?.length) { color = top.stops[0].color; alpha = top.opacity; }
      }
      item.text = {
        characters: node.textData?.characters || '',
        fontSize: r2(node.fontSize ?? 16),
        fontFamily: fn.family || 'Inter',
        fontWeight: fontWeightOf(fn.style),
        italic: String(fn.style || '').toLowerCase().includes('italic'),
        color,
        opacity: r2(alpha),
        align: node.textAlignHorizontal || 'LEFT',
        vAlign: node.textAlignVertical || 'TOP',
        wrap: node.textAutoResize !== 'WIDTH_AND_HEIGHT',
        autoW: node.textAutoResize === 'WIDTH_AND_HEIGHT',
      };
      if (top?.stops?.length >= 2) {
        item.text.gradient = { angle: top.angle, opacity: top.opacity, stops: top.stops };
      }
      const sp = convertPaints(node.strokePaints, w, h).filter((p) => p.type === 'SOLID' || p.type === 'GRADIENT');
      const sw = typeof node.strokeWeight === 'number' ? node.strokeWeight : 0;
      if (sp.length && sw > 0) {
        const st = sp[sp.length - 1];
        const col = st.type === 'SOLID' ? st.color : st.stops?.[0]?.color || { r: 0, g: 0, b: 0 };
        item.text.stroke = { color: col, opacity: st.opacity, weight: r2(sw), align: node.strokeAlign || 'OUTSIDE' };
      }
      const tshs = shadowList(node.effects);
      if (tshs.length) { item.text.shadows = tshs; item.text.shadow = tshs[0]; }
      const lines = node.textData?.lines?.length;
      if (lines > 1) item.text.lines = lines;
      item.opacity = r2(item.opacity * alpha);
    } else {
      let paints = convertPaints(node.fillPaints, w, h);

      if (isVector) {
        if (paints.length) { const _e = eiMetaOf(node, item, paints, w, h); if (_e) item.ei = _e; }
        registerImage(node, item, paints, ctx);
        paints = [];
      } else {
        const hasImage = paints.some((p) => p.type === 'IMAGE');
        if (hasImage && hasChildren) {
          paints = paints.filter((p) => p.type !== 'IMAGE');
        } else if (hasImage) {
          registerImage(node, item, paints, ctx);
        }
      }
      item.fills = paints.map(({ _hash, _ref, ...r }) => r);

      // v10/v9 `ei` yan kanalı: ölçülmüş görsel geometrisi + döşeme hücresi (code.js imageMetaOf)
      const _ei = eiMetaOf(node, item, paints, w, h);
      if (_ei) item.ei = _ei;

      const fshs = shadowList(node.effects);
      if (!isVector && !item.image && fshs.length) { item.shadows = fshs; item.shadow = fshs[0]; }

      if (!isVector && node.overflowDirection && node.overflowDirection !== 'NONE') {
        item.scroll = node.overflowDirection;
      }

      if (!isVector && hasChildren && (node.stackMode === 'HORIZONTAL' || node.stackMode === 'VERTICAL')) {
        const absKid = kids.some((k) => k.stackChildAlignSelf === 'ABSOLUTE' || k.layoutPositioning === 'ABSOLUTE');
        if (!absKid) {
          item.layout = {
            mode: node.stackMode,
            gap: r2(node.stackSpacing || 0),
            wrapGap: r2(node.stackCounterSpacing || 0),
            wrap: node.stackWrap === 'WRAP',
            pl: r2(node.stackPadding ?? 0), pr: r2(node.stackPadding ?? 0),
            pt: r2(node.stackPadding ?? 0), pb: r2(node.stackPadding ?? 0),
            primary: node.stackPrimaryAlignItems || 'MIN',
            counter: node.stackCounterAlignItems || 'MIN',
          };
        }
      }

      const allStrokes = convertPaints(node.strokePaints, w, h);
      const sp = allStrokes.filter((p) => p.type === 'SOLID');
      const sw = typeof node.strokeWeight === 'number' ? node.strokeWeight : 0;
      if (sp.length && sw > 0) {
        const st = sp[sp.length - 1];
        item.stroke = { color: st.color, opacity: st.opacity, weight: r2(sw) };
      }
      const spAll = allStrokes.filter((p) => p.type === 'SOLID' || p.type === 'GRADIENT');
      if (spAll.length && sw > 0) {
        item.strokes = spAll;
        item.strokeWeight = r2(sw);
        item.strokeAlign = node.strokeAlign || 'INSIDE';
      }

      if (t === 'ELLIPSE') item.radius = 'full';
      else if (node.cornerRadius != null) item.radius = r2(node.cornerRadius);
      else if (node.rectangleCornerRadiiIndependent && node.rectangleTopLeftCornerRadius != null) {
        item.radius = r2(node.rectangleTopLeftCornerRadius);
      }

      // kiwi'de `clipsContent` yok: kırpma = frameMaskDisabled === false (code.js `clipsContent`)
      if (node.frameMaskDisabled === false) item.clips = true;

      if (hasChildren) {
        item.children = [];
        for (const c of kids) walk(c, nodeTransform, item.children, false);
      }

      if (!isRoot && !item.image && item.kind === 'frame' && (!item.children || item.children.length === 0) && (!item.fills || item.fills.length === 0) && !item.stroke && !item.strokes) {
        ctx.stats.emptyDropped++;
        return;
      }
    }

    out.push(item);
  }
  return walk;
}

// ---- code.js `nameTokens` / `hasTag` / `isScrollNode` birebir portları ----------
const TAG_TOKENS = new Set(['button', 'btn', 'scroll', 'scrollx', 'scrolly', 'scrollingframe', 'canvas', 'canvasgroup', 'viewport', 'viewportframe',
  'aspect', 'hover', 'clicked', 'input', 'textbox', 'textlabel', 'textbutton', 'imagelabel', 'imagebutton', 'image', 'lock',
  'ignore', 'exclude', 'frame', 'keep', 'nodim', 'gray', 'videoframe', 'video']);
const CLASS_WORDS = ['imagebutton', 'imagelabel', 'textbutton', 'textlabel', 'textbox', 'scrollingframe', 'viewportframe', 'canvasgroup', 'videoframe'];

/** code.js `nameTokens`: `_kelime` parçaları + adın içinde geçen sınıf adları. */
function nameTokens(name) {
  const out = {};
  const n = String(name || '').toLowerCase().replace(/\u0307/g, '').replace(/\u0131/g, 'i');
  const re = /_([a-z]+)/g;
  let m;
  while ((m = re.exec(n)) !== null) out[m[1]] = 1;
  for (const c of CLASS_WORDS) if (n.includes(c)) out[c] = 1;
  return out;
}
const hasToken = (name, list) => { const t = nameTokens(name); return list.some((k) => t[k]); };
const isIgnoredName = (name) => hasToken(name, ['ignore', 'exclude']);
function hasTag(name) {
  const n = String(name || '').toLowerCase();
  const tk = nameTokens(n);
  for (const k of Object.keys(tk)) if (TAG_TOKENS.has(k)) return true;
  return n.startsWith('#') || n.startsWith('img:');
}
const isScrollNode = (node) => !!(node && node.overflowDirection && node.overflowDirection !== 'NONE');

function childListOf(node) {
  return (node.children || []).filter((c) => c && c.visible !== false && c.phase !== 'REMOVED' && !isIgnoredName(c.name));
}

/** code.js `collectTexts`: mask'li grupta yazılar düzenlenebilir kalsın diye toplanır. */
function collectTexts(node, acc) {
  for (const c of node.children || []) {
    if (!c || c.visible === false || c.phase === 'REMOVED') continue;
    if (apiType(c.type) === 'TEXT') acc.push(c);
    else if (c.children) collectTexts(c, acc);
  }
  return acc;
}

const anyVisiblePaint = (arr) => Array.isArray(arr) && arr.some((p) => p && p.visible !== false && (p.opacity == null || p.opacity > 0.001));
const anyVisibleEffect = (arr) => Array.isArray(arr) && arr.some((p) => p && p.visible !== false);

/** code.js `isMaskNode`: `isMask` (kiwi: `mask`) ya da adı `mask…`. */
const isMaskNode = (n) => !!n && (n.mask === true || /^\s*mask([\s_\-]?\d.*)?\s*$/i.test(String(n.name || '')));

// ---- Yapı şekillendirme (code.js: süs grubu birleştirme / sarmalayıcı sadeleştirme) ----
// Bu yüklemler salt mantıktır ve AĞACI değiştirir → etiketleri de değiştirir. Atlanırsa
// gerçek tasarımlarda onlarca ikon 20-30 ayrı düğüm olarak açılır ve sınıf dağılımı bozulur.

/** code.js `scanDecor`: ağaç yalnızca vektör/şekil mi (metin ve etiket yok mu)? */
function scanDecor(node, acc) {
  if (!node || node.visible === false || node.phase === 'REMOVED') return true;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  const t = apiType(node.type);
  if (t === 'TEXT') return false;
  if (VECTOR_TYPES[t]) { acc.vec++; acc.n++; return true; }
  if (t === 'RECTANGLE' || t === 'ELLIPSE') { acc.n++; return true; }
  if (t === 'GROUP' || t === 'FRAME' || t === 'INSTANCE' || t === 'COMPONENT' || t === 'BOOLEAN_OPERATION') {
    acc.n++;
    for (const c of node.children || []) if (!scanDecor(c, acc)) return false;
    return true;
  }
  return false;
}

/** code.js `isDecorGroup`: metinsiz süs/ikon grubunu TEK PNG yapar. */
function isDecorGroup(node) {
  const t = apiType(node.type);
  if (t !== 'GROUP' && t !== 'FRAME' && t !== 'INSTANCE' && t !== 'COMPONENT') return false;
  if (!node.children || node.children.length === 0) return false;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  const w = node.size?.x || 0, h = node.size?.y || 0;
  if (w < 1 || h < 1 || w > 2200 || h > 2200) return false;
  const acc = { vec: 0, n: 0 };
  if (!scanDecor(node, acc)) return false;
  return (acc.vec >= 1 && acc.n >= 2) || acc.n >= 4;
}

/** code.js `isPureVectorGroup`: 20 parçalı vektör ikonu 20 PNG yerine TEK PNG olur. */
function isPureVectorGroup(node) {
  if (!node || !node.children || node.children.length === 0) return false;
  let visCount = 0;
  for (const ch of node.children) {
    if (!ch || ch.visible === false || ch.phase === 'REMOVED') continue;
    visCount++;
    const ct = apiType(ch.type);
    if (VECTOR_TYPES[ct]) continue;
    if ((ct === 'GROUP' || ct === 'FRAME' || ct === 'BOOLEAN_OPERATION') && isPureVectorGroup(ch)) continue;
    return false;
  }
  return visCount > 0;
}

/**
 * code.js `childrenInsideBounds`. Gerçek eklenti `absoluteRenderBounds` kullanır; burada
 * mutlak konum ebeveyn çevrimlerinden biriktirilir (döndürme yok sayılır → döndürmeli
 * düğümde "içeride" varsayılır, yani daha çok sadeleştirme yapılır). Fark küçüktür.
 */
function childrenInsideBounds(node, absX, absY) {
  const w = node.size?.x || 0, h = node.size?.y || 0;
  for (const ch of node.children || []) {
    if (!ch || ch.visible === false || ch.phase === 'REMOVED') continue;
    const cx = absX + (ch.transform?.m02 || 0), cy = absY + (ch.transform?.m12 || 0);
    const cw = ch.size?.x || 0, chh = ch.size?.y || 0;
    if (cx < absX - 1 || cy < absY - 1 || cx + cw > absX + w + 1 || cy + chh > absY + h + 1) return false;
  }
  return true;
}

/** code.js `isPlainWrapper`: görsel olarak hiçbir şey katmayan sarmalayıcı frame. */
function isPlainWrapper(node, absX, absY) {
  const t = apiType(node.type);
  if (t !== 'FRAME' && t !== 'INSTANCE' && t !== 'COMPONENT') return false;
  if (hasTag(node.name) || isScrollNode(node)) return false;
  if (!node.children || node.children.length === 0) return false;
  if ((node.opacity == null ? 1 : node.opacity) < 0.999) return false;
  if (node.mask) return false;
  if (node.blendMode && node.blendMode !== 'PASS_THROUGH' && node.blendMode !== 'NORMAL') return false;
  if (anyVisiblePaint(node.fillPaints)) return false;
  if (anyVisiblePaint(node.strokePaints)) return false;
  if (anyVisibleEffect(node.effects)) return false;
  if (node.cornerRadius != null && node.cornerRadius > 0) return false;
  for (const ch of node.children) if (ch?.mask) return false;
  // kiwi: `clipsContent` = !frameMaskDisabled
  if (node.frameMaskDisabled === false && !childrenInsideBounds(node, absX, absY)) return false;
  return true;
}

function shadowList(effects) {
  const out = [];
  for (const e of effects || []) {
    if (e.type === 'DROP_SHADOW' && e.visible !== false) {
      out.push({
        x: r2(e.offset?.x), y: r2(e.offset?.y), blur: r2(e.radius || 0), spread: r2(e.spread || 0),
        color: c255(e.color), opacity: r2(e.color?.a == null ? 1 : e.color.a),
      });
    }
  }
  return out;
}

/**
 * code.js `registerImage` karşılığı — ÖNEMLİ: plugin `item.image`'ı DAİMA yazar.
 *
 * Vektör düğümlerinin IMAGE dolgusu olmaz; Figma onları düğüm olarak PNG'ye render eder
 * (`exportAsync`). code.js `registerImage`'ın son satırına düşer ve yine de `image` atar.
 * Dolayısıyla her vektör Studio'da **ImageLabel** olur (öğretmen: `item.image` → ImageLabel).
 *
 * Bu satır eksikse vektörler `kind:'vector'` + imagesiz kalır ve öğretmen onlara **Frame** der —
 * gerçek tasarımlarda 809 vektör yanlış etiketlenir.
 */
function registerImage(node, item, paints, ctx) {
  const img = paints.find((p) => p.type === 'IMAGE');
  if (img?._hash) {
    // gerçek raster: PNG .fig ZIP'inden çıkarılabilir, dedupe anlamlı
    item.image = safeFile(node.name, img._hash);
    ctx.images.push({ file: item.image, hash: img._hash, node: node.name });
    ctx.stats.imageRefs++;
    return;
  }
  // vektör/şekil: Figma düğümü PNG'ye render eder; dosya adı node id'den türetilir
  const g = node.guid ? `${node.guid.sessionID}:${node.guid.localID}` : 'x';
  item.image = safeFile(node.name, g);
  ctx.stats.vectorRefs = (ctx.stats.vectorRefs || 0) + 1;
}

/**
 * `ei` yan kanalı — code.js `imageMetaOf` karşılığı.
 *
 * code.js bunu `figma.getImageByHash().getSizeAsync()` ile ASENKRON ölçer ve ölçüm başarısızsa
 * alanı hiç yazmaz. `.fig` dosyası ise ölçümü zaten içerir (`originalImageWidth/Height`, `scale`),
 * bu yüzden burada DAİMA yazılabilir — yani `ei`, plugin'in ölçebildiği durumdan daha eksiksiz.
 *
 * Bu kanal olmadan stud/doku tespiti ölür: `style-rules.json` stud kanalları
 * "ölçülmüş döşeme geometrisi" (tileW/tileH/repX/repY) ister ve bu alanlar boş kalır.
 */
function eiMetaOf(node, item, paints, w, h) {
  const ei = {};
  const img = paints.find((p) => p.type === 'IMAGE');
  if (img) {
    const iw = Math.round(img._origW || 0);
    const ih = Math.round(img._origH || 0);
    if (iw > 0 && ih > 0) { ei.imageW = iw; ei.imageH = ih; }
    if ((img.scaleMode || '').toUpperCase() === 'TILE') {
      const sf = img._scale > 0 ? img._scale : 1;
      const tw = iw * sf, th = ih * sf;
      if (tw > 0 && th > 0) {
        ei.sf = sf;
        ei.tileW = Math.round(tw);
        ei.tileH = Math.round(th);
        if (w > 0 && h > 0) { ei.repX = Math.round(w / tw); ei.repY = Math.round(h / th); }
      }
    }
    if (img._blend && img._blend !== 'NORMAL' && img._blend !== 'PASS_THROUGH') ei.blendMode = img._blend;
  }
  if (!ei.blendMode && node.blendMode && node.blendMode !== 'NORMAL' && node.blendMode !== 'PASS_THROUGH') {
    ei.blendMode = node.blendMode;
  }
  return Object.keys(ei).length ? ei : null;
}

// ---------------------------------------------------------------- CLI
function main() {
  const argv = process.argv.slice(2);
  if (!argv.length) {
    console.log('kullanım: node to_wispfree.mjs <girdi.fig> -o <cikti-klasoru> [--tek] [--sessiz]');
    process.exit(1);
  }
  const figPath = argv[0];
  const oi = argv.indexOf('-o');
  const outDir = oi > -1 ? argv[oi + 1] : 'wispfree-out';
  const onlyFirst = argv.includes('--tek');
  const quiet = argv.includes('--sessiz');

  mkdirSync(join(outDir, 'images'), { recursive: true });

  const { message } = decodeFig(figPath);
  const nodes = message.nodeChanges || [];
  const { byGuid, childrenOf } = buildTree(nodes);

  const docNode = nodes.find((n) => n.type === 'DOCUMENT');
  const canvases = (childrenOf.get(gk(docNode.guid)) || []).filter(
    (c) => c.type === 'CANVAS' && c.name !== 'Internal Only Canvas' && c.phase !== 'REMOVED',
  );

  const report = { fig: basename(figPath), tasarimlar: [], gorseller: [], atlananKutu: [] };
  let sira = 0;

  for (const canvas of canvases) {
    const roots = (childrenOf.get(gk(canvas.guid)) || []).filter(
      (c) => c.phase !== 'REMOVED' && c.visible !== false && FRAME_TYPES[apiType(c.type)] && c.type !== 'RECTANGLE' && c.type !== 'ROUNDED_RECTANGLE' && c.type !== 'ELLIPSE',
    );
    for (const root of roots) {
      sira++;
      const ctx = { childrenOf, images: [], stats: { ghost: 0, emptyDropped: 0, imageRefs: 0, vectorRefs: 0, flattened: 0, decorMerged: 0, vectorMerged: 0, maskMerged: 0 } };
      const walk = makeWalker(ctx);
      const list = [];
      walk(root, t2m(root.transform), list, true);

      const rawName = canvas.name && canvas.name !== 'Page 1' ? `${canvas.name}` : '';
      const ad = roots.length > 1 ? `${root.name}${rawName ? ` (${rawName})` : ''}` : root.name || 'Tasarim';
      const guvenli = String(ad).replace(/[^a-zA-Z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || `tasarim${sira}`;
      const docName = `${basename(figPath).replace(/\.fig$/i, '')}__${guvenli}`;

      const doc = {
        format: 'wispfree',
        version: 9,
        name: docName,
        width: r2(root.size?.x || 0),
        height: r2(root.size?.y || 0),
        root: list[0],
      };
      if (!doc.root) { ctx.stats.emptyDropped++; }

      writeFileSync(join(outDir, `${docName}.json`), JSON.stringify(doc, null, 1));

      // görselleri gerçek PNG olarak çıkar (galeri/eşleştirme hattını test edebilmek için)
      for (const im of ctx.images) {
        const p = extractImage(figPath, im.hash);
        if (p) {
          writeFileSync(join(outDir, 'images', im.file), p);
          report.gorseller.push(im.file);
        } else {
          report.gorseller.push(`EKSIK:${im.hash}`);
        }
      }

      report.tasarimlar.push({
        ad: docName, kok: root.name, dugum: countItems(doc.root), boyut: `${Math.round(doc.width)}x${Math.round(doc.height)}`,
        ...ctx.stats,
      });
      if (onlyFirst) break;
    }
    if (onlyFirst && report.tasarimlar.length) break;
  }

  mkdirSync(join(outDir, '_rapor'), { recursive: true });
  writeFileSync(join(outDir, '_rapor', 'rapor.json'), JSON.stringify(report, null, 1));
  if (!quiet) {
    console.log(`  dosya      : ${basename(figPath)}`);
    console.log(`  tasarım    : ${report.tasarimlar.length}`);
    console.log(`  düğüm      : ${report.tasarimlar.reduce((a, t) => a + t.dugum, 0)}`);
    console.log(`  görsel     : ${report.gorseller.filter((g) => !g.startsWith('EKSIK')).length}/${report.gorseller.length}`);
    console.log(`  hayalet    : ${report.tasarimlar.reduce((a, t) => a + t.ghost, 0)} · boş atılan: ${report.tasarimlar.reduce((a, t) => a + t.emptyDropped, 0)}`);
  }
}

const dogrudanCalisti = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (dogrudanCalisti) main();

function countItems(it) {
  if (!it) return 0;
  let n = 1;
  for (const c of it.children || []) n += countItems(c);
  return n;
}

/** .fig ZIP'inden `images/<hex>` dosyasını okur. */
function extractImage(figPath, hashHex) {
  // python yalnızca bir kez listelenir; içerik talep üzerine alınır
  try {
    const buf = execFileSync('python3', [
      '-c',
      `import zipfile,sys
z=zipfile.ZipFile(sys.argv[1])
want='images/'+sys.argv[2]
for n in z.namelist():
    if n==want:
        sys.stdout.buffer.write(z.read(n)); break`,
      figPath, hashHex,
    ], { maxBuffer: 64 * 1024 * 1024 });
    return buf.length ? buf : null;
  } catch {
    return null;
  }
}


