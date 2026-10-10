#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A4a — MODEL DIŞA AKTARICI (export_model)

    model/model.json ──▶ runtime/js/ei-model.js   (kanon: veri + tahmin)
                     └─▶ runtime/lua/EIModel.lua  (Studio ikizi: aynı veri + aynı tahmin)

Neden üretici: model dosyası elle kopyalanırsa iki dil arasında sessiz fark doğar. Tek kaynaktan
(model.json) iki dosya üretilir ve `tools/verify_predict.py` kapısı JS ≡ Lua olduğunu KANITLAR.

Tahmin matematiği (train_class.py ile aynı kanon):
    z_c = Σ_i W[c][i]·(x_i − mean_i)/std_i + b_c + ln(styleBias)   →   softmax
Eşitlik bozulmasın diye:
  · `ln(bias)` burada BİR KEZ hesaplanıp gömülür (iki dilde math.log farkı sıfırlanır),
  · stil bayraklarının vektör indeksleri gömülür → `predict(vec)` stili kendi okur,
  · sıralama tam bağlı: skor ↓, sonra sınıf adı ↑ (Lua `<` ile JS `<` ASCII'de aynı).

Kullanım:
    python3 tools/export_model.py [model/model.json]
Çıkış: 0 = başarılı, 1 = model eksik/bozuk
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import feature_index  # noqa: E402
import verify_model as VM  # noqa: E402  (checksum doğrulaması tek yerde)

JS_OUT = os.path.join(ROOT, "runtime", "js", "ei-model.js")
LUA_OUT = os.path.join(ROOT, "runtime", "lua", "EIModel.lua")
STYLE_FLAG = {"stud": "sty_stud", "anime": "sty_anime", "cartoon": "sty_cartoon"}


def num(v):
    """JS/Lua değişmez yazımı: tam sayılar kısa, ondalıklar repr ile (çift duyarlık korunur)."""
    v = float(v)
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return repr(v)


def num_list(vals, indent, per_line=12):
    parts = [num(v) for v in vals]
    lines = []
    for i in range(0, len(parts), per_line):
        lines.append(" " * indent + ", ".join(parts[i:i + per_line]))
    return (",\n").join(lines)


def main():
    args = [a for a in sys.argv[1:]]
    out_dir = None
    if "--out-dir" in args:
        i = args.index("--out-dir")
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    if out_dir:
        global JS_OUT, LUA_OUT
        JS_OUT = os.path.join(out_dir, "ei-model.js")
        LUA_OUT = os.path.join(out_dir, "EIModel.lua")
        os.makedirs(out_dir, exist_ok=True)
    src = args[0] if args else os.path.join(ROOT, "model", "model.json")
    if not os.path.exists(src):
        print("model yok: %s\n  önce: python3 tools/train_class.py --eval" % src)
        return 1
    with open(src, encoding="utf-8") as fh:
        obj = json.load(fh)
    doc = obj["models"]["class"]
    classes, W, b = doc["classes"], doc["W"], doc["b"]
    mean, std = doc["norm"]["mean"], doc["norm"]["std"]
    dim = len(mean)

    # --- güvenlik kontrolleri: bozuk model gömülmesin -----------------------
    if [len(r) for r in W] != [dim] * len(classes):
        raise SystemExit("W boyutu tutarsız")
    if any(s <= 0 or not math.isfinite(s) for s in std):
        raise SystemExit("std içinde 0/sonsuz var")
    recomputed = VM.recompute_checksum(doc)
    if recomputed != (obj.get("meta") or {}).get("checksum"):
        raise SystemExit("model checksum tutmuyor — önce tools/train_class.py --eval ile yeniden üret")
    print("  [OK] model: %s · %d sınıf · %d boyut · %s" % (os.path.relpath(src, ROOT), len(classes), dim, recomputed))

    # --- stil öncülleri: ln(bias) tek seferde burada hesaplanır -------------
    n2i = {n: i for i, n in enumerate(feature_index.names(feature_index.load_spec()))}
    flag_idx = {s: n2i[name] for s, name in STYLE_FLAG.items()}
    priors = doc.get("stylePriors") or {}
    logbias = {}
    for s in sorted(STYLE_FLAG):
        bias = (priors.get(s) or {}).get("classBias") or {}
        arr = [0.0] * len(classes)
        for c, v in bias.items():
            if c in classes and v > 0:
                arr[classes.index(c)] = round(math.log(v), 12)
        logbias[s] = arr
        print("  [i] %-8s öncül: %s" % (s, {c: round(v, 4) for c, v in zip(classes, arr) if v}))

    clipz = float(doc.get("clipZ", 8.0))
    if clipz <= 0:
        clipz = 8.0

    chk = recomputed.split(":", 1)[1][:12]
    header = ("-- OTOMATİK ÜRETİLDİ — ELLE DÜZENLEMEYİN.\n"
              "-- Kaynak: model/model.json (tools/train_class.py) · checksum %s\n"
              "-- Yeniden üret: python3 tools/export_model.py && python3 tools/verify_predict.py\n" % chk)
    js_header = header.replace("--", "//")
    ver = "%s-%d" % (obj["format"], obj["version"])

    # ---- v15: SINIF DESTEĞİ KAPISI — tek kaynak: models.class.elig (tools/class_support.py yazar) ----
    if doc.get("elig") is None or len(doc["elig"]) != len(classes):
        raise SystemExit("models.class.elig yok/uyumsuz: önce python3 tools/class_support.py")
    ELIG = [bool(e) for e in doc["elig"]]

    # ---------------- JS ----------------
    js = [js_header,
          "var EIModel = (function () {",
          "  var VERSION = '%s';" % ver,
          "  var DIM = %d;" % dim,
          "  var CLASSES = [%s];" % ", ".join("'%s'" % c for c in classes),
          "  var ELIG = [%s]; // destek kapısı: true = tahmin edilebilir" % ", ".join("true" if e else "false" for e in ELIG),
          "  var W = [",
          ",\n".join("    [" + num_list(row, 6) + "]" for row in W),
          "  ];",
          "  var B = [" + num_list(b, 4) + "];",
          "  var MEAN = [" + num_list(mean, 4) + "];",
          "  var STD = [" + num_list(std, 4) + "];",
          "  var CLIPZ = %s;" % num(clipz),
          "  var STYLE_FLAG = { stud: %d, anime: %d, cartoon: %d };" % (
              flag_idx["stud"], flag_idx["anime"], flag_idx["cartoon"]),
          "  var STYLE_LOG_BIAS = {"]
    for s in sorted(STYLE_FLAG):
        js.append("    %s: [%s]," % (s, ", ".join(num(v) for v in logbias[s])))
    js += [
        "  };",
        "",
        "  function num(x) {",
        "    if (typeof x !== 'number' || x !== x || x === Infinity || x === -Infinity) return 0;",
        "    return x;",
        "  }",
        "",
        "  function styleOf(vec) {",
        "    if (num(vec[STYLE_FLAG.stud])) return 'stud';",
        "    if (num(vec[STYLE_FLAG.anime])) return 'anime';",
        "    if (num(vec[STYLE_FLAG.cartoon])) return 'cartoon';",
        "    return null;",
        "  }",
        "",
        "  // vec: 379 boyutlu özellik vektörü (features.json sırası) → {cls, conf, top3, probs}",
        "  function predict(vec) {",
        "    var style = styleOf(vec);",
        "    var z = new Array(CLASSES.length);",
        "    for (var c = 0; c < CLASSES.length; c++) {",
        "      var s = B[c], Wc = W[c];",
        "      for (var i = 0; i < DIM; i++) {",
        "        var x = num(vec[i]);",
        "        if (x !== 0) {",
        "          var t = (x - MEAN[i]) / STD[i];",
        "          if (t > CLIPZ) t = CLIPZ; else if (t < -CLIPZ) t = -CLIPZ;",
        "          s += Wc[i] * t;",
        "        }",
        "      }",
        "      if (style) s += STYLE_LOG_BIAS[style][c];",
        "      z[c] = s;",
        "    }",
        "    var m = z[0];",
        "    for (var j = 1; j < z.length; j++) if (z[j] > m) m = z[j];",
        "    var sum = 0, p = new Array(z.length);",
        "    for (var k = 0; k < z.length; k++) { p[k] = Math.exp(z[k] - m); sum += p[k]; }",
        "    for (var q = 0; q < p.length; q++) p[q] /= sum;",
        "    var rawTop = 0;",
        "    for (var r = 1; r < p.length; r++) if (p[r] > p[rawTop] || (p[r] === p[rawTop] && CLASSES[r] < CLASSES[rawTop])) rawTop = r;",
        "    var pe = p; // güven HAM olasılıktan (yeniden normalize edilmez → güven şişmez)",
        "    var order = [];",
        "    for (var t = 0; t < p.length; t++) if (ELIG[t]) order.push(t);",
        "    order.sort(function (a, b2) {",
        "      if (pe[a] !== pe[b2]) return pe[a] > pe[b2] ? -1 : 1;",
        "      return CLASSES[a] < CLASSES[b2] ? -1 : (CLASSES[a] > CLASSES[b2] ? 1 : 0);",
        "    });",
        "    var top3 = [];",
        "    for (var u = 0; u < order.length && u < 3; u++) top3.push([CLASSES[order[u]], pe[order[u]]]);",
        "    var conf = order.length ? pe[order[0]] : 0;",
        "    if (!ELIG[rawTop] && conf > 0.69) conf = 0.69; // ham en iyi aday kapıya takıldı: güven sınırlanır",
        "    return { cls: order.length ? CLASSES[order[0]] : CLASSES[rawTop], conf: conf, top3: top3, probs: p, style: style };",
        "  }",
        "",
        "  // DATA: yalnızca kapı (verify_predict) ve iç teşhis için açıktır; kullanıcıya gösterilmez",
        "  var DATA = { W: W, B: B, MEAN: MEAN, STD: STD, CLIPZ: CLIPZ,",
        "               STYLE_LOG_BIAS: STYLE_LOG_BIAS, STYLE_FLAG: STYLE_FLAG };",
        "  return { VERSION: VERSION, DIM: DIM, CLASSES: CLASSES, predict: predict, DATA: DATA };",
        "})();",
        "if (typeof module !== 'undefined' && module.exports) module.exports = EIModel;",
        ""]

    # ---------------- Lua ----------------
    lu = [header,
          "local EIModel = {}",
          "EIModel.VERSION = '%s'" % ver,
          "EIModel.DIM = %d" % dim,
          "EIModel.CLASSES = { %s }" % ", ".join("'%s'" % c for c in classes),
          "EIModel.ELIG = { %s } -- destek kapısı" % ", ".join("true" if e else "false" for e in ELIG),
          "local W = {",
          ",\n".join("  { " + num_list(row, 4) + " }" for row in W),
          "}",
          "local B = { " + num_list(b, 2) + " }",
          "local MEAN = { " + num_list(mean, 2) + " }",
          "local STD = { " + num_list(std, 2) + " }",
          "local CLIPZ = %s" % num(clipz),
          "local STYLE_FLAG = { stud = %d, anime = %d, cartoon = %d }" % (
              flag_idx["stud"], flag_idx["anime"], flag_idx["cartoon"]),
          "local STYLE_LOG_BIAS = {"]
    for s in sorted(STYLE_FLAG):
        lu.append("  %s = { %s }," % (s, ", ".join(num(v) for v in logbias[s])))
    lu += [
        "}",
        "",
        "-- NaN/sonsuz → 0 (Luau'da NaN karşılaştırmaları sessizce yanlış sonuç verir)",
        "local function num(x)",
        "  if type(x) ~= 'number' then return 0 end",
        "  if not (x == x) then return 0 end",
        "  if x == math.huge or x == -math.huge then return 0 end",
        "  return x",
        "end",
        "",
        "-- DİKKAT: STYLE_FLAG indeksleri features.json'dan (0-tabanlı) gelir; Lua tabloları",
        "-- 1-tabanlıdır → kullanırken +1. Bu tek satır atlanırsa stil sessizce yanlış okunur.",
        "local function styleOf(vec)",
        "  if num(vec[STYLE_FLAG.stud + 1]) ~= 0 then return 'stud' end",
        "  if num(vec[STYLE_FLAG.anime + 1]) ~= 0 then return 'anime' end",
        "  if num(vec[STYLE_FLAG.cartoon + 1]) ~= 0 then return 'cartoon' end",
        "  return nil",
        "end",
        "",
        "-- vec: 379 boyutlu özellik vektörü (features.json sırası) → {cls, conf, top3, probs}",
        "function EIModel.predict(vec)",
        "  local style = styleOf(vec)",
        "  local n = #EIModel.CLASSES",
        "  local z = {}",
        "  for c = 1, n do",
        "    local s = B[c]",
        "    local Wc = W[c]",
        "    for i = 1, EIModel.DIM do",
        "      local x = num(vec[i])",
        "      if x ~= 0 then",
        "        local t = (x - MEAN[i]) / STD[i]",
        "        if t > CLIPZ then t = CLIPZ elseif t < -CLIPZ then t = -CLIPZ end",
        "        s = s + Wc[i] * t",
        "      end",
        "    end",
        "    if style then s = s + STYLE_LOG_BIAS[style][c] end",
        "    z[c] = s",
        "  end",
        "  local m = z[1]",
        "  for j = 2, n do if z[j] > m then m = z[j] end end",
        "  local sum = 0",
        "  local p = {}",
        "  for k = 1, n do p[k] = math.exp(z[k] - m); sum = sum + p[k] end",
        "  for q = 1, n do p[q] = p[q] / sum end",
        "  local rawTop = 1",
        "  for r = 2, n do if p[r] > p[rawTop] or (p[r] == p[rawTop] and EIModel.CLASSES[r] < EIModel.CLASSES[rawTop]) then rawTop = r end end",
        "  local pe = p -- güven HAM olasılıktan (yeniden normalize edilmez → güven şişmez)",
        "  local order = {}",
        "  for t = 1, n do if EIModel.ELIG[t] then order[#order + 1] = t end end",
        "  table.sort(order, function(a, b)",
        "    if pe[a] ~= pe[b] then return pe[a] > pe[b] end",
        "    return EIModel.CLASSES[a] < EIModel.CLASSES[b]",
        "  end)",
        "  local top3 = {}",
        "  for u = 1, #order do",
        "    if u > 3 then break end",
        "    top3[u] = { EIModel.CLASSES[order[u]], pe[order[u]] }",
        "  end",
        "  local conf = (#order > 0) and pe[order[1]] or 0",
        "  if (not EIModel.ELIG[rawTop]) and conf > 0.69 then conf = 0.69 end -- ham en iyi aday kapıya takıldı",
        "  local cls = (#order > 0) and EIModel.CLASSES[order[1]] or EIModel.CLASSES[rawTop]",
        "  return { cls = cls, conf = conf, top3 = top3, probs = p, style = style }",
        "end",
        "",
        "EIModel.DATA = { W = W, B = B, MEAN = MEAN, STD = STD, CLIPZ = CLIPZ,",
        "                STYLE_LOG_BIAS = STYLE_LOG_BIAS, STYLE_FLAG = STYLE_FLAG }",
        "",
        "return EIModel",
        ""]

    with open(JS_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(js))
    with open(LUA_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lu))
    for out in (JS_OUT, LUA_OUT):
        print("  [OK] %s (%.1f KB)" % (os.path.relpath(out, ROOT), os.path.getsize(out) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
