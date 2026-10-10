// Sahte Figma ortamı: code.js'i vm içinde çalıştırıp doExport sonuçlarını döndürür.
'use strict';
const fs = require('fs'), vm = require('vm');
const bb = (x, y, w, h) => ({ x, y, width: w, height: h });
const M = (x, y) => [[1, 0, x], [0, 1, y]];
const base = (id, name, type, x, y, w, h) => ({ id, name, type, visible: true, opacity: 1, x, y, width: w, height: h,
  rotation: 0, absoluteBoundingBox: bb(x, y, w, h), absoluteTransform: M(x, y), relativeTransform: M(x, y),
  strokes: [], effects: [], blendMode: 'PASS_THROUGH', locked: false, clipsContent: false,
  constraints: { horizontal: 'MIN', vertical: 'MIN' } });
const txt = (id, name, x, y, chars) => Object.assign(base(id, name, 'TEXT', x, y, 200, 30), {
  fills: [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 }, opacity: 1, visible: true }], characters: chars, fontSize: 18,
  fontName: { family: 'Inter', style: 'Bold' }, textAlignHorizontal: 'LEFT', textAlignVertical: 'TOP',
  textAutoResize: 'WIDTH_AND_HEIGHT', letterSpacing: { value: 0, unit: 'PERCENT' }, lineHeight: { unit: 'AUTO' },
  textCase: 'ORIGINAL', textDecoration: 'NONE', paragraphSpacing: 0 });
const frame = (id, name, x, y, w, h, kids, fills) => Object.assign(base(id, name, 'FRAME', x, y, w, h), {
  fills: fills || [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.2 }, opacity: 1, visible: true }],
  cornerRadius: 12, children: kids, layoutMode: 'NONE' });
const imgFill = (hash) => [{ type: 'IMAGE', imageHash: hash, scaleMode: 'TILE', scalingFactor: 0.5, visible: true, opacity: 1, blendMode: 'NORMAL' }];

function mkTree(withImage) {
  const kids = [
    txt('1:2', 'Baslik_Text', 20, 20, 'Merhaba'),
    frame('1:3', 'Buton_button', 20, 80, 120, 40, [txt('1:4', 'Etiket', 10, 8, 'Tikla')]),
    frame('1:5', 'Ikon_ImageLabel', 200, 80, 40, 40, []),
  ];
  if (withImage) kids.push(frame('1:6', 'Stud_Bar_Top', 20, 160, 360, 40, [], imgFill('hash_stud_1')));
  return frame('1:1', 'Ana_Panel', 0, 0, 400, 300, kids);
}

async function runExport(codePath, opts) {
  const posted = [];
  const sizes = (opts && opts.sizes) || {};
  const root = (opts && opts.root) ? opts.root : mkTree(!!(opts && opts.withImage));
  const figma = {
    mixed: Symbol('mixed'), showUI() {}, root: { name: 'Demo Dosya' },
    currentPage: { name: 'Sayfa 1', children: [root], selection: [root] },
    ui: { postMessage: (m) => posted.push(m), onmessage: null },
    getImageByHash(h) {
      if (!(h in sizes)) return null;
      return { getSizeAsync: async () => sizes[h] };
    },
    getNodeById() { return null; }, on() {}, once() {},
  };
  const ctx = { figma, console, Math, JSON, Object, Array, Number, String, Symbol, Blob: function () {},
    setTimeout, __html__: '', Promise };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(codePath, 'utf8'), ctx, { filename: codePath });
  await ctx.doExport({ images: false, mergeVectors: true, dedupe: true, flatten: true, mergeDecor: true });
  return { result: posted.find((m) => m.type === 'result'), posted };
}
module.exports = { runExport, mkTree, bb, M, base, txt, frame };
