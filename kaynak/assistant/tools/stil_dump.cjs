#!/usr/bin/env node
// stil_dump.cjs — gerçek export'larda EIStyle sinyal dökümü + eşik taraması (A12 aracı)
// (.cjs uzantısı zorunlu: Node'un ESM tespiti yorumlardaki "export'" gibi sözcüklerle
//  .js dosyasını ESM sanıyor; .cjs her zaman CommonJS'tir.)
//
//   node tools/stil_dump.cjs <exportsDir>
//       → her export için tam sinyal nesnesi + güncel karar (JSON, stdout)
//
//   node tools/stil_dump.cjs <exportsDir> --grid <grid.json>
//       → ek olarak her override seti için tüm export kararları
//         grid.json: [{"animeLightMin": 0.4, "marginMin": 0.05}, ...]
//         (EIStyle.WEIGHTS üzerine patch; orijinal değerler geri alınır)
//
// Not: tarama YALNIZCA anime/cartoon/margin eşiklerini kapsar. Stud kanalı
// ölçüm-only'dir — stud kuralı gevşetilmez (karar günlüğündeki kısıt: weak keyword
// tek başına stud saymaz, nStudTileGeo tek başına sinyal değildir, hücre tekdüzeliği
// ve kare koşulu gevşetilmez).
'use strict';
const fs = require('fs');
const path = require('path');
const EIRaw = require('../runtime/js/ei-raw.js');
const EIStyle = require('../runtime/js/ei-style.js');

const dir = process.argv[2];
if (!dir) {
  process.stderr.write('kullanım: node stil_dump.js <exportsDir> [--grid grid.json]\n');
  process.exit(2);
}
const gridIdx = process.argv.indexOf('--grid');
const grid = gridIdx >= 0 ? JSON.parse(fs.readFileSync(process.argv[gridIdx + 1], 'utf8')) : null;

const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
const kalemler = [];
for (const f of files) {
  const doc = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  const ex = EIRaw.extract(doc);
  const s = EIStyle.signals(ex.gui, ex.nodes);
  const d = EIStyle.decide(s);
  kalemler.push({
    export: doc.name,
    signals: JSON.parse(JSON.stringify(s)),
    scores: d.scores,
    style: d.style,
    conf: d.conf
  });
}

const out = { n: kalemler.length, exports: kalemler };
if (grid) {
  out.grid = grid.map(ov => {
    const geri = {};
    for (const k of Object.keys(ov)) geri[k] = EIStyle.WEIGHTS[k];
    Object.assign(EIStyle.WEIGHTS, ov);
    const decisions = kalemler.map(e => EIStyle.decide(e.signals).style);
    Object.assign(EIStyle.WEIGHTS, geri); // orijinale dön
    return { overrides: ov, decisions: decisions };
  });
}
process.stdout.write(JSON.stringify(out));
