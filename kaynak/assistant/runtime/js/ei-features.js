/* EasyImport Asistan — ÖZELLİK DEĞERLENDİRİCİ (JavaScript / Figma)  [A1]
 *
 * spec/features.json (build_runtime.py tarafından ei-features-spec.js olarak gömülür)
 * dosyasını okur ve bir RAW nesnesini sabit uzunlukta özellik vektörüne çevirir.
 *
 * Python ve Lua sürümleriyle BİREBİR aynı sonucu vermek ZORUNDADIR.
 * tools/verify_runtime.py bunu zorunlu tutar.
 *
 * Figma'da: ei-features-spec.js ve bu dosya sırayla ui.html'e gömülür (require yok).
 * Node'da : require('./ei-features-spec.js')
 */
var EI = (function () {
  var EPS = 1e-6;
  var LN10 = Math.log(10);

  function log10(x) { return Math.log(x) / LN10; }

  function asnum(v) {
    if (v === null || v === undefined) return 0.0;
    if (v === true) return 1.0;
    if (v === false) return 0.0;
    if (typeof v === 'number') {
      if (v !== v) return 0.0;              // NaN
      if (v === Infinity) return 1e12;
      if (v === -Infinity) return -1e12;
      return v;
    }
    return 0.0;
  }

  function clamp(x, lo, hi) { return x < lo ? lo : (x > hi ? hi : x); }

  function divisor(raw, f) {
    var d = f.d;
    if (d === undefined || d === null) return 1.0;
    var dv = (typeof d === 'string') ? asnum(raw[d]) : asnum(d);
    if (dv === 0.0) return 1.0;
    return dv;
  }

  function num(raw, f) {
    var x = asnum(raw[f.src]);
    var norm = f.norm || 'id';

    if (norm === 'id') return x;
    if (norm === 'clamp01') return clamp(x, 0.0, 1.0);
    if (norm === 'log1p') return log10(1.0 + (x > 0.0 ? x : 0.0));
    if (norm === 'log') {
      var lo = (f.lo === undefined) ? -6.0 : f.lo;
      var hi = (f.hi === undefined) ? 6.0 : f.hi;
      return clamp(log10(x > EPS ? x : EPS), lo, hi);
    }

    var dv = divisor(raw, f);
    var adv = dv > 0.0 ? dv : -dv;
    if (adv === 0.0) adv = 1.0;
    if (norm === 'div') return x / adv;
    if (norm === 'divlog') {
      var lo2 = (f.lo === undefined) ? -6.0 : f.lo;
      var hi2 = (f.hi === undefined) ? 6.0 : f.hi;
      return clamp(log10((x > EPS ? x : EPS) / adv), lo2, hi2);
    }
    return x;
  }

  function compute(spec, raw) {
    var out = [];
    var feats = spec.features;
    for (var i = 0; i < feats.length; i++) {
      var f = feats[i];
      var k = f.k;
      if (k === 'num') {
        out.push(num(raw, f));
      } else if (k === 'bool') {
        out.push(raw[f.src] ? 1.0 : 0.0);
      } else if (k === 'token') {
        var toks = raw[f.src];
        out.push((toks && toks[f.t]) ? 1.0 : 0.0);
      } else if (k === 'onehot') {
        var v = raw[f.src];
        for (var j = 0; j < f.values.length; j++) {
          out.push(v === f.values[j] ? 1.0 : 0.0);
        }
      } else if (k === 'bucket') {
        var x = asnum(raw[f.src]);
        var edges = f.edges;
        var idx = edges.length;
        for (var e = 0; e < edges.length; e++) {
          if (x <= edges[e]) { idx = e; break; }
        }
        for (var b = 0; b <= edges.length; b++) {
          out.push(b === idx ? 1.0 : 0.0);
        }
      } else {
        throw new Error('bilinmeyen tur: ' + k);
      }
    }
    return out;
  }

  return { compute: compute, asnum: asnum, log10: log10, clamp: clamp };
})();

if (typeof module !== 'undefined' && module.exports) { module.exports = EI; }
