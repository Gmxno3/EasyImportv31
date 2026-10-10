// KAPI: etiket bayrakları dışa aktarımda doğru JSON alanlarına yazılır (v12).
'use strict';
const assert = require('assert');
const path = require('path');
const { runExport, bb, M, base, txt, frame } = require('./figma_mock.js');
const NEW = path.join(__dirname, '..', 'figma', 'code.js');

function flat(node, acc) { acc.push(node); (node.children || []).forEach(c => flat(c, acc)); return acc; }

(async () => {
  const root = frame('1:1', 'Ana', 0, 0, 400, 300, [
    frame('2:1', 'Ac_open:Shop_panel', 10, 10, 80, 30, []),
    frame('2:2', 'Kapat_close', 10, 50, 80, 30, []),
    frame('2:3', 'Shop_panel', 10, 90, 200, 150, [frame('2:12', 'Icerik_close', 10, 100, 40, 20, [])]),
    frame('2:4', 'Sekme_tab:Weapons', 10, 250, 80, 30, []),
    frame('2:5', 'Grup_tabgroup', 100, 250, 200, 30, []),
    frame('2:6', 'Golge_shadow_Frame', 10, 290, 80, 30, []),
    frame('2:7', 'Liste_nolist_Frame', 100, 290, 80, 30, []),
    txt('2:8', 'Baslik_fit_Text', 10, 330, 'Merhaba'),
    frame('2:11', 'Dugme_open', 10, 420, 80, 30, []),
  ]);
  const r = await runExport(NEW, { root });
  const doc = JSON.parse(r.result.json);
  const nodes = flat(doc.root, []);
  const byName = n => nodes.find(x => x.name === n);

  assert.deepStrictEqual(byName('Ac_open:Shop_panel').action, { kind: 'open', target: 'Shop_panel' });
  console.log('[OK] _open:Shop_panel → open, hedef Shop_panel');
  assert.deepStrictEqual(byName('Kapat_close').action, { kind: 'close', target: null });
  console.log('[OK] _close (parametresiz) → close, hedef yok (en yakın panel)');
  assert.deepStrictEqual(byName('Sekme_tab:Weapons').action, { kind: 'tab', target: 'Weapons' });
  console.log('[OK] _tab:Weapons → tab, hedef Weapons');
  assert.strictEqual(byName('Dugme_open').action, undefined);
  console.log('[OK] parametresiz _open etkileşim DEĞİL (güvenlik kuralı)');
  assert.strictEqual(byName('Shop_panel').panel, true, 'hedeflenen öğe panel olmalı');
  assert.strictEqual(byName('Ana').panel, undefined, 'sıradan ad panel olmamalı');
  console.log('[OK] panel: eylem hedefi ya da içindeki _close üzerinden; sıradan ad değil');
  assert.strictEqual(byName('Grup_tabgroup').tabgroup, true);
  console.log('[OK] _panel ve _tabgroup bayrakları');
  assert.strictEqual(byName('Golge_shadow_Frame').shadowTag, true);
  assert.strictEqual(byName('Liste_nolist_Frame').nolist, true);
  console.log('[OK] _shadow ve _nolist bayrakları');
  assert.strictEqual(byName('Baslik_fit_Text').text.fit, true);
  console.log('[OK] _fit metne işlendi (text.fit)');
  console.log('SONUÇ: GEÇTİ — etiket bayrakları JSON\'a doğru yazılıyor');
})().catch(e => { console.error('BAŞARISIZ: ' + e.message); process.exit(1); });
