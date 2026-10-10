// KAPI: efekt simge modeli (v23) — JS çalışma zamanı Python eğitim referansıyla aynı posterior'u üretir.
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.join(__dirname, '..');
const RT = path.join(ROOT, 'assistant', 'runtime', 'js');
const ctx = vm.createContext({});
for (const f of ['ei-learn.js', 'ei-fxmodel.js', 'ei-fxpick.js']) {
  vm.runInContext(fs.readFileSync(path.join(RT, f), 'utf8'), ctx, { filename: f });
}
const FX = ctx.EIFxPick;
const REF = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fxmodel_expected.json'), 'utf8'));
let pass = 0;
function ok(c, m) { assert.ok(c, m); pass++; console.log('  [OK] ' + m); }

// 1) model dosyası referansla aynı sınıflar
ok(JSON.stringify(ctx.EIFxModel.classes) === JSON.stringify(REF.classes), 'model sınıfları referansla aynı: ' + REF.classes.join(', '));

// 2) token + posterior: Python referansıyla birebir (tolerans 1e-9)
let maxDiff = 0;
for (const s of REF.samples) {
  const p = {};
  for (const c of REF.classes) p[c] = FX.modelProb(c, { id: s.id, name: s.name, label: s.label, cat: s.cat });
  for (const c of REF.classes) maxDiff = Math.max(maxDiff, Math.abs(p[c] - s.probs[c]));
}
ok(maxDiff < 1e-9, 'JS posterior = Python referansı (en büyük fark ' + maxDiff.toExponential(2) + ')');

// 3) olasılıklar toplamı 1
const ic = { id: 'x', name: 'Gold Coin', label: 'Gold Coin', cat: 'Item' };
const total = ctx.EIFxModel.classes.reduce((a, c) => a + FX.modelProb(c, ic), 0);
ok(Math.abs(total - 1) < 1e-9, 'posterior toplamı 1');

// 4) eğitilmiş token genellemesi: eğitimde görülen "coin" kalıbı yeni bir adda para (fall) sinyali verir
const pFall = FX.modelProb('fall', ic);
ok(pFall > 0.5, '"Gold Coin" (görülmemiş ad) için fall posterior > 0,5: ' + pFall.toFixed(3));

// 5) model yoksa güvenli: 0 döner (ör. sınıf modelde yok)
ok(ctx.EIFxModel.classes.indexOf('orb') === -1 && FX.modelProb('orb', ic) === 0, 'modelde olmayan sınıf (orb: 8 örnek, destek eşiği altı) → 0');

// 6) metaveri: eğitim raporu dosyada
const head = fs.readFileSync(path.join(RT, 'ei-fxmodel.js'), 'utf8').split('\n').slice(0, 2).join(' ');
ok(/CV doğruluk: [0-9.]+, çoğunluk tabanı/.test(head), 'eğitim raporu başlıkta');

console.log('SONUÇ: GEÇTİ — ' + pass + ' kontrol (efekt simge modeli)');
