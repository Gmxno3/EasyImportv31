// KAPI: ekstra kütüphane + öğrenen efekt simgesi sıralayıcı (v22)
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.join(__dirname, '..');
const RT = path.join(ROOT, 'assistant', 'runtime', 'js');

function load(ctx, file) { vm.runInContext(fs.readFileSync(path.join(RT, file), 'utf8'), ctx, { filename: file }); }
const ctx = vm.createContext({});
load(ctx, 'ei-learn.js');
load(ctx, 'ei-ekstra.js');
load(ctx, 'ei-fxpick.js');
const IDX = ctx.EKSTRA_INDEX, THUMBS = ctx.EKSTRA_THUMBS;
const LIB = path.join(ROOT, 'kutuphane', 'EkstraKutuphane');
const json = JSON.parse(fs.readFileSync(path.join(ROOT, 'kutuphane', 'ekstra-kutuphane.json'), 'utf8'));

let pass = 0;
function ok(cond, msg) { assert.ok(cond, msg); pass++; console.log('  [OK] ' + msg); }

// 1) kütüphane bütünlüğü
ok(IDX.length === 1022 && json.count === 1022, 'dizin 1022 simge (' + IDX.length + ')');
const ids = new Set(IDX.map(i => i.id));
ok(ids.size === IDX.length, 'kimlikler benzersiz');
ok(IDX.every(i => /^ikon_[a-z0-9_]+$/.test(i.id)), 'kimlikler ASCII ve Decal adına uygun');
ok(IDX.every(i => THUMBS[i.id] && /^data:image\/(png|webp);base64,/.test(THUMBS[i.id])), 'her simgenin önizleme resmi var (png/webp)');
ok(IDX.every(i => fs.existsSync(path.join(LIB, i.id + '.png'))), 'her simgenin dosyası kütüphane klasöründe (Asset Manager için)');
ok(IDX.filter(i => i.wide).length === 192, 'geniş varyantlar: 192');

// 2) tohum sıralaması (eğitim öncülü, öğrenme yokken)
const fall = ctx.EIFxPick.rank('fall', IDX, null, 'belirsiz');
const top20 = fall.slice(0, 20);
ok(top20.filter(i => i.cat === 'Currency').length >= 10, 'yağmur: ilk 20 içinde para (Currency) ağırlıklı (' + top20.filter(i => i.cat === 'Currency').length + ')');
ok(fall[0].cat === 'Currency', 'yağmur: ilk simge para kategorisinden');
const burst = ctx.EIFxPick.rank('burst', IDX, null, 'belirsiz');
ok(burst.slice(0, 10).some(i => i.cat === 'Exclusive'), 'patlama: ilk 10 içinde özel (Exclusive) simge');
const r1 = ctx.EIFxPick.rank('fall', IDX, null, 'belirsiz').map(i => i.id).join('|');
const r2 = ctx.EIFxPick.rank('fall', IDX, null, 'belirsiz').map(i => i.id).join('|');
ok(r1 === r2, 'sıralama deterministik');

// 3) öğrenme: kabul edilen simge öne çıkar; reddedilen geriye düşer
const learn = ctx.EILearn.newState();
const target = fall.find(i => i.cat === 'Food') || fall[fall.length - 1];  // tohuma göre düşük öncelikli bir simge seç
const topBefore = fall[0].id;
ctx.EIFxPick.record(learn, 'belirsiz', 'fall', target.id, true);
ctx.EIFxPick.record(learn, 'belirsiz', 'fall', target.id, true);
const afterAccept = ctx.EIFxPick.rank('fall', IDX, learn, 'belirsiz');
ok(afterAccept[0].id === target.id, 'iki kez kabul edilen simge (' + target.id + ') tohumu geçip ilk sırada');
ok(afterAccept[0].id !== topBefore, 'öğrenme tohum sırasını değiştirdi (önce ' + topBefore + ')');

// 4) efekt türleri ayrı öğrenir: fall'daki kabul burst sıralamasını değiştirmez
const burstAfter = ctx.EIFxPick.rank('burst', IDX, learn, 'belirsiz');
const burstBase = ctx.EIFxPick.rank('burst', IDX, null, 'belirsiz');
ok(burstAfter[0].id === burstBase[0].id, 'bağlam ayrımı: fall öğrenmesi burst sıralamasını bozmaz');

// 5) red: reddedilen simge düşer
const learn2 = ctx.EILearn.newState();
const first = ctx.EIFxPick.rank('fall', IDX, null, 'belirsiz')[0];
ctx.EIFxPick.record(learn2, 'belirsiz', 'fall', first.id, false);
ctx.EIFxPick.record(learn2, 'belirsiz', 'fall', first.id, false);
const afterReject = ctx.EIFxPick.rank('fall', IDX, learn2, 'belirsiz');
ok(afterReject[0].id !== first.id, 'iki kez reddedilen simge ilk sıradan çıkar');

// 6) öğrenme durumu kalıcılık formatına uyar (encode/decode gidiş-dönüş)
const txt = ctx.EILearn.encode(learn);
const back = ctx.EILearn.decode(txt);
const again = ctx.EIFxPick.rank('fall', IDX, back, 'belirsiz');
ok(again[0].id === target.id, 'kaydet/yükle sonrası öğrenilen sıralama korunur');

console.log('SONUÇ: GEÇTİ — ' + pass + ' kontrol (ekstra kütüphane + öğrenen sıralayıcı)');
