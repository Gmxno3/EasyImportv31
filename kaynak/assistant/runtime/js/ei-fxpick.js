// EIFxPick — efekt simgesi seçimi için öğrenen sıralayıcı (v22). Lua'ya gitmez; Figma paneli kullanır.
// Puan = öğrenilmiş skor (EILearn, kullanıcının seçimleri) + 0,25 × tohum (kategori + ad öncülü).
// Tohum bir "ön eğitim"dir: kullanıcı seçimi arttıkça öğrenilmiş skor onu geçersiz kılar.
var EIFxPick = (function () {
  // Efekt türü → kategori öncülü (0..1). Kategoriler: ekstra kütüphanenin "cat" alanı.
  var SEED_CAT = {
    fall:     { Currency: 1, Nature: 0.7, Food: 0.7 },
    confetti: { Currency: 0.8, Exclusive: 0.8, Food: 0.5 },
    burst:    { Exclusive: 1, Item: 0.5 },
    orbit:    { Social: 0.8, Player: 0.8, Animal: 0.5 },
    twinkle:  { UI: 0.8, Exclusive: 0.8 },
    orb:      { Exclusive: 1, Main: 0.5 },
    sweep:    {}
  };
  // Efekt türü → ad anahtar sözcükleri (ikon adında geçerse +0,3).
  var SEED_NAME = {
    fall:     ['coin', 'cash', 'robux', 'diamond', 'crystal', 'ticket', 'ingot', 'premium'],
    confetti: ['coin', 'cash', 'star'],
    burst:    ['aura', 'vip'],
    orbit:    [],
    twinkle:  ['star', 'sparkle'],
    orb:      ['aura', 'angel'],
    sweep:    []
  };

  function seedNorm(kind, icon) {
    var w = (SEED_CAT[kind] || {})[icon.cat] || 0;
    var n = String(icon.name || '').toLowerCase();
    var kws = SEED_NAME[kind] || [];
    var hit = 0;
    for (var i = 0; i < kws.length; i++) {
      if (n.indexOf(kws[i]) !== -1 || String(icon.label || '').toLowerCase().indexOf(kws[i]) !== -1) { hit = 1; break; }
    }
    return Math.min(1, w * 0.7 + hit * 0.3);
  }

  // Bağlam: efekt türü başına ayrı öğrenme (fx | simge). Stil de bağlama girer.
  function ctxFor(style, kind) {
    return EILearn.ctxKey(style || 'belirsiz', 'fx', kind, 'icon');
  }

  // Eğitilmiş Naive Bayes (ei-fxmodel.js, tools/train_fx.py) ile aynı token kuralı: yalnız ad + etiket,
  // NFKD ile ASCII'ye indirgenir, küçük harf, [a-z0-9_] dışı ayırıcı, uzunluğu ≥ 2, tekil.
  function tokensOf(icon) {
    var raw = [icon.name || '', icon.label || ''].join(' ');
    var s = raw.normalize ? raw.normalize('NFKD') : raw;
    s = s.replace(/[^\x00-\x7F]/g, '').toLowerCase();
    var seen = {}, out = [];
    s.split(/[^a-z0-9_]+/).forEach(function (t) {
      if (t.length >= 2 && !seen[t]) { seen[t] = true; out.push(t); }
    });
    return out;
  }

  // Model posterior'u: P(kind | simge). Model yoksa 0.
  function modelProb(kind, icon) {
    if (typeof EIFxModel === 'undefined' || !EIFxModel.classes || EIFxModel.classes.indexOf(kind) === -1) return 0;
    var toks = tokensOf(icon), score = {}, m = -Infinity, i, c;
    EIFxModel.classes.forEach(function (cl) {
      var sc = EIFxModel.prior[cl];
      for (i = 0; i < toks.length; i++) {
        var lp = EIFxModel.logp[toks[i]];
        sc += lp ? lp[cl] : EIFxModel.unk[cl];
      }
      score[cl] = sc;
      if (sc > m) m = sc;
    });
    var z = 0;
    EIFxModel.classes.forEach(function (cl) { score[cl] = Math.exp(score[cl] - m); z += score[cl]; });
    return score[kind] / z;
  }

  // Puan = öğrenilmiş skor + 0,25 × (tohum ve model ortalaması). Öğrenme baskındır.
  function scoreOf(learn, style, kind, icon) {
    var learned = learn ? EILearn.scoreAnim(learn, ctxFor(style, kind), icon.id) : 0.5;
    return learned + 0.25 * (0.5 * seedNorm(kind, icon) + 0.5 * modelProb(kind, icon));
  }

  // icons: [{id, cat, name, label, ...}] → sıralı kopya. Eşitlikte gözlem sayısı, sonra kimlik.
  function rank(kind, icons, learn, style) {
    var list = (icons || []).slice();
    var ctx = ctxFor(style, kind);
    var sc = {}, ob = {};
    list.forEach(function (ic) {
      sc[ic.id] = scoreOf(learn, style, kind, ic);
      ob[ic.id] = learn ? EILearn.obsOf(learn, ctx, ic.id) : 0;
    });
    list.sort(function (a, b) {
      if (sc[a.id] !== sc[b.id]) return sc[b.id] - sc[a.id];
      if (ob[a.id] !== ob[b.id]) return ob[b.id] - ob[a.id];
      return a.id < b.id ? -1 : (a.id > b.id ? 1 : 0);
    });
    return list;
  }

  // Kullanıcı seçimi: kabul (true) ya da red (false).
  function record(learn, style, kind, iconId, accepted) {
    EILearn.recordAnim(learn, ctxFor(style, kind), iconId, accepted);
  }

  return { SEED_CAT: SEED_CAT, seedNorm: seedNorm, ctxFor: ctxFor, tokensOf: tokensOf, modelProb: modelProb,
           scoreOf: scoreOf, rank: rank, record: record };
})();
