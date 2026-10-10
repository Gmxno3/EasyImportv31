// KAPI: Figma öğrenme kanalı — learn-save / learn-load clientStorage'a doğru yazar ve okur;
//       dışa aktarma sonucu (json) bu kanaldan etkilenmez.
'use strict';
const assert = require('assert'), fs = require('fs'), vm = require('vm'), path = require('path');
const CODE = path.join(__dirname, '..', 'figma', 'code.js');
(async () => {
  const store = {};
  const posted = [];
  const figma = {
    mixed: Symbol('m'), showUI() {}, root: { name: 'D' }, currentPage: { name: 'P', children: [], selection: [] },
    ui: { postMessage: (m) => posted.push(m), onmessage: null },
    clientStorage: {
      getAsync: async (k) => (k in store ? store[k] : undefined),
      setAsync: async (k, v) => { store[k] = v; },
    },
    getImageByHash() { return null; }, getNodeById() { return null; }, on() {}, once() {},
  };
  const ctx = { figma, console, Math, JSON, Object, Array, Number, String, Symbol, Promise, setTimeout, Blob: function () {}, __html__: '' };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(CODE, 'utf8'), ctx, { filename: CODE });
  const text = 'ei-learn v1\nevents 3\ncls ctx|a|b|c TextLabel 2\n';
  ctx.figma.ui.onmessage({ type: 'learn-save', text });
  await new Promise((r) => setTimeout(r, 10));
  assert.strictEqual(store['EasyImportLearn'], text, 'kayıt yazılmadı');
  console.log('[OK] learn-save clientStorage\'a yazıyor');
  ctx.figma.ui.onmessage({ type: 'learn-load' });
  await new Promise((r) => setTimeout(r, 10));
  const st = posted.find((m) => m.type === 'learn-state');
  assert.ok(st && st.text === text, 'learn-state yanlış');
  console.log('[OK] learn-load kayıtlı durumu geri gönderiyor');
  const empty = { figma: null };
  store['EasyImportLearn'] = undefined; delete store['EasyImportLearn'];
  ctx.figma.ui.onmessage({ type: 'learn-load' });
  await new Promise((r) => setTimeout(r, 10));
  assert.strictEqual(posted.filter((m) => m.type === 'learn-state').pop().text, '', 'boş durum boş metin olmalı');
  console.log('[OK] kayıt yokken boş metin dönüyor');
  console.log('SONUÇ: GEÇTİ — öğrenme kanalı (Figma clientStorage)');
})().catch((e) => { console.error('BAŞARISIZ: ' + e.message); process.exit(1); });
