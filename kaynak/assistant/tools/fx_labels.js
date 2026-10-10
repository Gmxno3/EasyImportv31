// Efekt simgesi etiketleri (zayıf denetim): ei-fxpick.js tohum puanlarından üretilir.
// Çıktı (stdout): her simge için {id, cat, name, label, margin}. Güvenilir değilse label null.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const RT = path.join(__dirname, '..', 'runtime', 'js');
const ctx = vm.createContext({});
for (const f of ['ei-learn.js', 'ei-fxpick.js']) vm.runInContext(fs.readFileSync(path.join(RT, f), 'utf8'), ctx);
const KINDS = ['fall', 'confetti', 'burst', 'orbit', 'twinkle', 'orb'];
const MIN_SEED = 0.5;   // yalnız açık tohumu olan simgeler etiketlenir
const idx = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'kutuphane', 'ekstra-kutuphane.json'), 'utf8')).items;
const out = [];
for (const ic of idx) {
  let best = null, bestV = -1, second = -1;
  for (const k of KINDS) {
    const v = ctx.EIFxPick.seedNorm(k, ic);
    if (v > bestV) { second = bestV; bestV = v; best = k; } else if (v > second) second = v;
  }
  const label = bestV >= MIN_SEED && bestV > second ? best : null;
  out.push({ id: ic.id, cat: ic.cat, name: ic.name, label, seed: +bestV.toFixed(3) });
}
process.stdout.write(out.map(o => JSON.stringify(o)).join('\n') + '\n');
