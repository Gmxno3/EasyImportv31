// EasyImport — YEREL ÖĞRENME (kanon uygulama)
//
// Sunucu YOK. Asistan, kullanıcının kendi seçimlerinden KENDİ CİHAZINDA öğrenir:
//   • hangi animasyon hangi bağlamda seçildi / reddedildi (stil · sınıf · rol · fx)
//   • kullanıcı sınıfı elle değiştirdiyse hangi bağlamda neye çevirdi
//
// Sayaç tabanlıdır (tamsayı) — bu yüzden JS ve Lua tarafları bit bit aynı sonucu üretir
// (tools/verify_learn.py kapısı bunu zorunlu tutar). Öğrenme dosyası küçüktür:
// Figma clientStorage 5 MB, Studio plugin:SetSetting diske yazar; ikisinde de sorun olmaz.
//
// Saklama notu: Studio'da anahtar adı `.` veya `\` İÇERMEMELİ (SetSetting sessizce başarısız olur).
var EILearn = (function () {
  var VERSION = 1;
  var DEFAULT_CAP = 400;          // en fazla bağlam sayısı
  var DEFAULT_SIZE_CAP = 65536;   // kodlanmış metin üst sınırı (bayt)

  // ------------------------------------------------------------------ yardımcı
  function sanitize(tok) {
    var s = String(tok == null ? '-' : tok);
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      // A-Z de geçerli: sınıf adları ("TextLabel") küçültülmemeli.
      var ok = (c >= 97 && c <= 122) || (c >= 65 && c <= 90) || (c >= 48 && c <= 57)
        || c === 95 || c === 45 || c === 124 || c === 35;
      out += String.fromCharCode(ok ? c : 95);
    }
    if (out === '') out = '-';
    return out;
  }

  function lower(s) {
    var t = String(s == null ? '' : s), o = '';
    for (var i = 0; i < t.length; i++) {
      var c = t.charCodeAt(i);
      o += (c >= 65 && c <= 90) ? String.fromCharCode(c + 32) : t[i];
    }
    return o;
  }

  function countKeys(o) { var n = 0; for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) n++; return n; }

  // ---------------------------------------------------------------- yaşam döngü
  function newState() {
    return { v: VERSION, anim: {}, cls: {}, events: 0, exports: 0 };
  }

  // Bağlam anahtarı: stil | sınıf | rol | fx   (boş parça "-" olur)
  function ctxKey(style, cls, role, fx) {
    return [sanitize(lower(style)), sanitize(lower(cls)), sanitize(lower(role)), sanitize(lower(fx))].join('|');
  }

  function ensureAnim(st, ctx) {
    if (!st.anim[ctx]) st.anim[ctx] = {};
    return st.anim[ctx];
  }
  function ensureCls(st, ctx) {
    if (!st.cls[ctx]) st.cls[ctx] = {};
    return st.cls[ctx];
  }

  function recordAnim(st, ctx, animId, accepted) {
    var m = ensureAnim(st, ctx);
    var id = sanitize(animId);
    if (!m[id]) m[id] = [0, 0];
    if (accepted) m[id][0] += 1; else m[id][1] += 1;
    st.events += 1;
    return st;
  }

  function recordClass(st, ctx, clsName, n) {
    var m = ensureCls(st, ctx);
    var id = sanitize(clsName);
    if (!m[id]) m[id] = 0;
    m[id] += (n == null ? 1 : n);
    st.events += 1;
    return st;
  }

  function exportBump(st) { st.exports += 1; return st; }

  // -------------------------------------------------------------------- skor
  // Yumuşatılmış kabul oranı: (2c+1) / (2(c+r)+2). Yalnızca tamsayı girdi → iki dilde birebir.
  function scoreAnim(st, ctx, animId) {
    var m = st.anim[ctx];
    var e = m ? m[sanitize(animId)] : null;
    if (!e) return 0.5;
    var c = e[0], r = e[1];
    return (2 * c + 1) / (2 * (c + r) + 2);
  }

  function totalOf(st, ctx) {
    var t = 0, k;
    var a = st.anim[ctx] || {};
    for (k in a) if (Object.prototype.hasOwnProperty.call(a, k)) t += a[k][0] + a[k][1];
    var c = st.cls[ctx] || {};
    for (k in c) if (Object.prototype.hasOwnProperty.call(c, k)) t += c[k];
    return t;
  }

  // Sıralama: skor ↓ · toplam gözlem ↓ · id ↑  (son ölçüt kararlılık için ŞART)
  function rankAnim(st, ctx, candidates) {
    var list = (candidates || []).slice();
    var self = st;
    list.sort(function (a, b) {
      var sa = scoreAnim(self, ctx, a), sb = scoreAnim(self, ctx, b);
      if (sa !== sb) return sb - sa;
      var ta = obsOf(self, ctx, a), tb = obsOf(self, ctx, b);
      if (ta !== tb) return tb - ta;
      var ia = sanitize(a), ib = sanitize(b);
      return ia < ib ? -1 : (ia > ib ? 1 : 0);
    });
    return list;
  }

  function obsOf(st, ctx, animId) {
    var m = st.anim[ctx];
    var e = m ? m[sanitize(animId)] : null;
    return e ? (e[0] + e[1]) : 0;
  }

  // En çok kullanılan animasyonlar (context → liste)
  function topAnims(st, ctx, k) {
    var m = st.anim[ctx] || {};
    var ids = [];
    for (var id in m) if (Object.prototype.hasOwnProperty.call(m, id)) ids.push(id);
    ids.sort(function (a, b) {
      var ca = m[a][0] - m[a][1], cb = m[b][0] - m[b][1];
      if (ca !== cb) return cb - ca;
      var oa = m[a][0] + m[a][1], ob = m[b][0] + m[b][1];
      if (oa !== ob) return ob - oa;
      return a < b ? -1 : (a > b ? 1 : 0);
    });
    return ids.slice(0, k == null ? 5 : k);
  }

  // Sınıf tercihi: kullanıcının bu bağlamda kaç kez hangi sınıfa çevirdiği
  function preferredClass(st, ctx) {
    var m = st.cls[ctx] || {};
    var best = null, bn = 0;
    for (var k in m) {
      if (!Object.prototype.hasOwnProperty.call(m, k)) continue;
      if (m[k] > bn || (m[k] === bn && best !== null && k < best)) { best = k; bn = m[k]; }
    }
    return best === null ? null : { cls: best, n: bn };
  }

  // -------------------------------------------------------------------- budama
  // Bağlam sayısı ya da metin boyu sınırı aşarsa en az kullanılanlar atılır (deterministik).
  function prune(st, maxCtx) {
    var cap = maxCtx == null ? DEFAULT_CAP : maxCtx;
    var keys = [];
    for (var k in st.anim) if (Object.prototype.hasOwnProperty.call(st.anim, k)) keys.push(k);
    for (var k2 in st.cls) if (Object.prototype.hasOwnProperty.call(st.cls, k2) && keys.indexOf(k2) < 0) keys.push(k2);
    if (keys.length <= cap) return st;
    var self = st;
    keys.sort(function (a, b) {
      var ta = totalOf(self, a), tb = totalOf(self, b);
      if (ta !== tb) return ta - tb;
      return a < b ? -1 : (a > b ? 1 : 0);
    });
    var drop = keys.length - cap;
    for (var i = 0; i < drop; i++) {
      delete st.anim[keys[i]];
      delete st.cls[keys[i]];
    }
    return st;
  }

  // ------------------------------------------------------------------ kodlama
  function encode(st) {
    var lines = ['ei-learn v' + VERSION, 'events ' + st.events, 'exports ' + st.exports];
    var animRows = [];
    for (var ctx in st.anim) {
      if (!Object.prototype.hasOwnProperty.call(st.anim, ctx)) continue;
      for (var id in st.anim[ctx]) {
        if (!Object.prototype.hasOwnProperty.call(st.anim[ctx], id)) continue;
        var e = st.anim[ctx][id];
        animRows.push('anim ' + ctx + ' ' + id + ' ' + e[0] + ' ' + e[1]);
      }
    }
    animRows.sort();
    var clsRows = [];
    for (var c2 in st.cls) {
      if (!Object.prototype.hasOwnProperty.call(st.cls, c2)) continue;
      for (var cn in st.cls[c2]) {
        if (!Object.prototype.hasOwnProperty.call(st.cls[c2], cn)) continue;
        clsRows.push('cls ' + c2 + ' ' + cn + ' ' + st.cls[c2][cn]);
      }
    }
    clsRows.sort();
    return lines.concat(animRows, clsRows).join('\n');
  }

  function decode(text) {
    var st = newState();
    var ls = String(text == null ? '' : text).split('\n');
    for (var i = 0; i < ls.length; i++) {
      var p = ls[i].split(' ');
      if (p[0] === 'events') st.events = toInt(p[1]);
      else if (p[0] === 'exports') st.exports = toInt(p[1]);
      else if (p[0] === 'anim' && p.length >= 5) {
        var m = ensureAnim(st, sanitize(p[1]));
        m[sanitize(p[2])] = [toInt(p[3]), toInt(p[4])];
      } else if (p[0] === 'cls' && p.length >= 4) {
        ensureCls(st, sanitize(p[1]))[sanitize(p[2])] = toInt(p[3]);
      }
    }
    return st;
  }

  function toInt(s) {
    var n = Number(s);
    if (!isFinite(n)) return 0;
    n = Math.floor(n);
    return n < 0 ? 0 : n;
  }

  function byteLen(s) {
    // UTF-8 bayt uzunluğu (kodlamamız ASCII olduğu için karakter sayısına eşit)
    var n = 0;
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      n += c < 128 ? 1 : (c < 2048 ? 2 : 3);
    }
    return n;
  }

  // Boyut sınırını garantiler: önce bağlam sayısını azaltır, yetmezse en az kullanılanları atar.
  function fit(st, maxCtx, maxBytes) {
    var cap = maxCtx == null ? DEFAULT_CAP : maxCtx;
    var maxB = maxBytes == null ? DEFAULT_SIZE_CAP : maxBytes;
    while (countContexts(st) > cap) prune(st, cap);
    var n = cap;
    var guard = 0;
    while (byteLen(encode(st)) > maxB && n > 1 && guard < 64) {
      n = Math.max(1, Math.floor(n * 0.75));
      prune(st, n);
      guard++;
    }
    return st;
  }

  function countContexts(st) {
    var seen = {}, n = 0, k;
    for (k in st.anim) if (Object.prototype.hasOwnProperty.call(st.anim, k) && !seen[k]) { seen[k] = 1; n++; }
    for (k in st.cls) if (Object.prototype.hasOwnProperty.call(st.cls, k) && !seen[k]) { seen[k] = 1; n++; }
    return n;
  }

  function stats(st) {
    var enc = encode(st);
    var lines = enc.split('\n');
    var animRows = 0, clsRows = 0;
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].indexOf('anim ') === 0) animRows++;
      if (lines[i].indexOf('cls ') === 0) clsRows++;
    }
    return {
      version: VERSION,
      contexts: countContexts(st),
      animRows: animRows,
      clsRows: clsRows,
      events: st.events,
      bytes: byteLen(enc)
    };
  }

  return {
    VERSION: VERSION,
    DEFAULT_CAP: DEFAULT_CAP,
    DEFAULT_SIZE_CAP: DEFAULT_SIZE_CAP,
    newState: newState,
    ctxKey: ctxKey,
    recordAnim: recordAnim,
    recordClass: recordClass,
    exportBump: exportBump,
    scoreAnim: scoreAnim,
    obsOf: obsOf,
    rankAnim: rankAnim,
    topAnims: topAnims,
    preferredClass: preferredClass,
    totalOf: totalOf,
    prune: prune,
    fit: fit,
    countContexts: countContexts,
    encode: encode,
    decode: decode,
    byteLen: byteLen,
    stats: stats,
    sanitize: sanitize
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = EILearn;
