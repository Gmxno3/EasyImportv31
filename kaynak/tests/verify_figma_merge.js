// KAPI: asistan eklemesi code.js'i (1) görselsiz tasarımda yüklenen dosyayla BAYT birebir tutar,
//       (2) görsel ölçümü olan tasarımda yalnız `ei` alanını ekler ve (3) eğitim dökümü (E1) çalışır.
'use strict';
const assert = require('assert');
const path = require('path');
const { runExport } = require('./figma_mock.js');
const ORIG = path.join(__dirname, 'baseline', 'code.js');
const NEW = path.join(__dirname, '..', 'figma', 'code.js');

function strip(json) { // `ei` alanlarını çıkar → v9 yapısının kıyası
  return JSON.stringify(JSON.parse(json), (k, v) => (k === 'ei' ? undefined : v));
}
(async () => {
  // 1) görselsiz: v9 çıktısı birebir
  const a = await runExport(ORIG, {});
  const b = await runExport(NEW, {});
  assert.strictEqual(b.result.json, a.result.json, 'görselsiz json DEĞİŞTİ');
  console.log('[OK] görselsiz tasarım: json bayt birebir aynı (' + b.result.json.length + ' bayt)');
  assert.ok(b.result.train && JSON.parse(b.result.train).format === 'ei-train', 'E1 eğitim dökümü yok');
  console.log('[OK] E1: train alanı ei-train v1 (' + JSON.parse(b.result.train).nodeCount + ' düğüm)');

  // 2) görselli + ölçülmüş: ei eklenir, geri kalan her şey aynı
  const sizes = { hash_stud_1: { width: 64, height: 64 } };
  const a2 = await runExport(ORIG, { withImage: true, sizes });
  const b2 = await runExport(NEW, { withImage: true, sizes });
  assert.strictEqual(strip(b2.result.json), strip(a2.result.json), 'ei dışında alan değişti');
  console.log('[OK] ei dışındaki tüm alanlar aynı');
  const doc = JSON.parse(b2.result.json);
  const eiNodes = [];
  (function rec(it) { if (it.ei) eiNodes.push({ name: it.name, ei: it.ei }); (it.children || []).forEach(rec); })(doc.root);
  assert.ok(eiNodes.length >= 1, 'ei ölçümü yazılmadı');
  const stud = eiNodes.find((n) => n.ei.tileW);
  assert.ok(stud, 'TILE ölçümü (tileW) yok: ' + JSON.stringify(eiNodes));
  assert.strictEqual(stud.ei.imageW, 64); assert.strictEqual(stud.ei.sf, 0.5); assert.strictEqual(stud.ei.tileW, 32);
  console.log('[OK] ei ölçümü: ' + stud.name + ' → görsel 64px, sf 0.5, döşeme 32px (' + JSON.stringify(stud.ei) + ')');
  console.log('[OK] ölçüm yoksa ei alanı hiç yazılmadı (görselsiz: ' + (a.result.json.includes('"ei"') ? 'HATA' : 'yok') + ')');
  assert.ok(!a.result.json.includes('"ei"'), 'görselsiz çıktıda ei var');
  console.log('SONUÇ: GEÇTİ — code.js birleştirmesi (v9 değişmez · ei ölçümü · E1)');
})().catch((e) => { console.error('BAŞARISIZ: ' + e.message); process.exit(1); });
