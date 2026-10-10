#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3 — SINIF MODELİ EĞİTİCİ (train_class)

    datasets/labels/*.jsonl ──▶ L2'li softmax regresyon ──▶ model/model.json
                                    │
                     stil öncülleri (spec/style-rules.json → _stylePriors.classBias)
                                    ▼
                       çalışma zamanı: önce stil, sonra sınıf önerisi

Neden doğrusal: her tahmin `{cls, conf, top3, KATKI:[(özellik, ağırlık)…]}` olarak
açıklanabilir olmalı (KARARLAR I6). Ağırlıklar Lua'da ~20 satırla çalışır.

Kabul kriteri (PLAN §M1): top-1 ≥ %85 · top-3 ≥ %95 → altındaysa çıkış kodu 2.

Bağımlılık yok (stdlib). Tüm matematik TAM SIRALI ve tohumsuzdur: aynı veri → aynı
model.json (çıktı 6 ondalığa yuvarlanır).

Kullanım:
    python3 tools/train_class.py -o model/model.json --eval
    python3 tools/train_class.py datasets/labels/bootstrap.jsonl --cv 5
    python3 tools/eval.py model/model.json datasets/labels/bootstrap.jsonl
"""
import argparse
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# 14 sınıf (PLAN §M1: "12 + 2 yapısal"). Sıra SABİT — model.json'daki W satırları bu sırada.
CLASSES = [
    "Frame", "ImageLabel", "ImageButton", "TextLabel", "TextButton", "TextBox",
    "ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame",
    "UIGridLayout", "Item", "DROP", "MERGE",
]
STYLES = ["stud", "anime", "cartoon"]
# J grubunda stilin hangi bayrakla geldiği (satırın `feat` sözlüğünden okunur)
STYLE_FLAG = {"stud": "sty_stud", "anime": "sty_anime", "cartoon": "sty_cartoon"}

_N2I = {}   # özellik adı → indeks (features.json'dan; `name2index` doldurur)

DEFAULTS = dict(epochs=400, lr=0.4, momentum=0.9, l2=0.08, patience=40, val_frac=0.25, seed=7, round_nd=6)
# lr/l2 neden düşürüldü: 5306 parametreye karşı 152 satır var; lr 1.2 + l2 1e-4 ile model
# doymuş logitlere (|z|>35) gidiyor ve doğrulama kaybı 2.75'e çıkıyordu. Export-LOO
# taraması (7 kat, aşağıdaki LOO_MIN notuna bak) lr 0.4 / l2 0.08'i en iyi yaptı.
CLIP_Z = 8.0          # standardize edilmiş özellik kırpması (aşağıdaki nota bak)
WINSOR_Q = 0.02       # dayanıklı ortalama/std: uçlar %2'lik dilimden kırpılır
LOO_MIN = 0.55        # kabul: export bazlı LOO top-1 tabanı (dürüst genelleme ölçütü)

# NOT — neden LOO kapıda: 5306 parametre / 152 satır oranında eğitim seti doğruluğu
# ezberlemeyle %100'e çıkabiliyordu (129 satırlık sürümde "top-1 100%" böyle çıkmıştı,
# export-LOO ise 73.87% idi). Bu yüzden --eval artık TEK BAŞINA eğitim setine bakmaz:
# eğitim seti ≥ %85/%95 (model veriyi öğrenmeli) + LOO ≥ %55 (öğrendiği genelleşmeli).


# ---------------------------------------------------------------------------
# VERİ
# ---------------------------------------------------------------------------
def name2index(spec=None):
    """features.json → {özellik adı: indeks}. Satırlardaki `feat` anahtarları İSİMDİR
    (ingest seyrek sözlüğü adlarla yazar); bu yüzden indeks dönüşümü tek yerde yapılır."""
    global _N2I
    if _N2I:
        return _N2I
    import feature_index  # noqa: E402
    if spec is None:
        spec = feature_index.load_spec()
    names = feature_index.names(spec)
    if len(names) != spec["dim"]:
        raise SystemExit("features.json tutarsız: %d ad ama dim=%d" % (len(names), spec["dim"]))
    _N2I = {n: i for i, n in enumerate(names)}
    return _N2I


def indexed(row, n2i=None, strict=True):
    """`{"tok_play":1,…}` → `{0:1,…}`. Bilinmeyen ad: strict'te hata, değilse atlanır.

    Idempotenttir: satır `load_rows`'tan geçtiyse anahtarlar zaten tam sayıdır ve
    yeniden dönüştürülmez (aksi halde ikinci geçiş TÜM özellikleri düşürürdü).
    """
    feat = row["feat"]
    if feat and all(isinstance(k, int) for k in feat):
        return row
    n2i = n2i or name2index()
    out = {}
    for name, v in row["feat"].items():
        i = n2i.get(name)
        if i is None:
            if strict:
                raise SystemExit("bilinmeyen özellik adı: %r" % name)
            continue
        out[i] = v
    return dict(row, feat=out)


def load_rows(paths, dim=None):
    """JSONL dosyalarını okur; `v`/`feat` doğrulanır. `dim` verilirse eksik boyut hata verir."""
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError as e:
                    raise SystemExit("%s:%d JSON hatası: %s" % (p, ln, e))
                if not isinstance(r.get("feat"), dict) or not r["feat"]:
                    raise SystemExit("%s:%d `feat` boş" % (p, ln))
                if r.get("cls") not in CLASSES:
                    raise SystemExit("%s:%d bilinmeyen sınıf %r" % (p, ln, r.get("cls")))
                rows.append(indexed(r))
    return rows


def sparse(row):
    """Seyrek satır → (indeksler, değerler) çifti. Sıra deterministiktir (indeks sırası).

    KANON: yalnızca HAM sıfır-olmayan özellikler katkı verir. Sıfır değerli bir boyut
    toplama KATILMAZ — çünkü normalizasyon `(0-mean)/std` yapar ve `mean≠0` olduğunda
    sıfır sanılan özellik logit'e sapma ekler. Eğitim de aynı kuralı kullanır
    (`norm_row`), dolayısıyla çalışma zamanı da böyle olmak zorundadır.
    NaN/±sonsuz değerler 0 sayılır: gömülü JS/Lua modülleri de (`num`) böyle yapar;
    aksi halde Python kanonu ile iki dil ayrışır.
    """
    items = sorted(row["feat"].items(), key=lambda kv: int(kv[0]))
    idx, val = [], []
    for k, v in items:
        f = float(v)
        if f != 0.0 and math.isfinite(f):   # -0.0 da düşer, NaN/sonsuz da
            idx.append(int(k))
            val.append(f)
    return idx, val


def winsor_bounds(rows, dim, q=WINSOR_Q):
    """Her özellik için alt/üst kırpma sınırı (gözlenen değerlerin %2 / %98 yüzdelikleri).

    Neden: tek bir uç satır (ör. 10.000.000 px genişlik) std'yi 8×10^7'ye çıkarıp TÜM
    diğer satırların bilgisini sıfıra indiriyordu — model tam da bu yüzden çöktü.
    Kırpma deterministiktir (sıralı gözlem listesi + sabit indeks), rastgelelik yok.
    Az gözlemi olan özelliklerde (< 8) kırpma uygulanmaz.
    """
    obs = [[] for _ in range(dim)]
    for r in rows:
        idx, val = sparse(r)
        for i, v in zip(idx, val):
            obs[i].append(v)
    lo = [0.0] * dim
    hi = [0.0] * dim
    for i in range(dim):
        xs = sorted(obs[i])
        if len(xs) < 8:
            continue
        a = int(math.floor(q * len(xs)))
        b = int(math.ceil((1.0 - q) * len(xs))) - 1
        if b <= a:
            b = a
        lo[i], hi[i] = xs[a], xs[b]
    return lo, hi


def _clip(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def standardize(rows, dim, bounds=None):
    """Ağırlıklı ortalama/std — uçlar kırpıldıktan sonra. std=0 → 1.

    Ayrıca `clipZ`: standardize edilmiş değer ±CLIP_Z'ye kırpılır. Bu kırpma hem eğitimde
    hem gömülü tahminde AYNI uygulanır (model.json → clipZ), böylece görülmemiş bir uç
    tasarım da logitleri patlatamaz.
    """
    lo, hi = bounds if bounds else ([0.0] * dim, [0.0] * dim)
    n = len(rows)
    sw = sum(float(r.get("w", 1.0)) for r in rows)
    mean = [0.0] * dim
    for r in rows:
        w = float(r.get("w", 1.0))
        idx, val = sparse(r)
        for i, v in zip(idx, val):
            mean[i] += w * _clip(v, lo[i], hi[i])
    mean = [m / sw for m in mean]
    var = [0.0] * dim
    for r in rows:
        w = float(r.get("w", 1.0))
        idx, val = sparse(r)
        for i, v in zip(idx, val):
            c = _clip(v, lo[i], hi[i])
            var[i] += w * (c - mean[i]) * (c - mean[i])
    std = [math.sqrt(v / sw) for v in var]
    std = [s if s > 1e-9 else 1.0 for s in std]
    return mean, std


def norm_row(row, mean, std, bounds=None, clip=CLIP_Z):
    """Seyrek satırı standartlaştırılmış seyrek biçimde döndürür (norm değeri 0 ise atlanır).

    Sıra: ham değer → winsor kırpma (yalnız eğitimde, `bounds` verilirse) → standartlaştırma
    → ±clip. Tahminde `bounds` YOKTUR (ham değer olduğu gibi standartlaştırılır) ama clip
    AYNI'dır; gömülü JS/Lua modülleri de tam olarak bunu yapar.
    """
    idx, val = sparse(row)
    out_i, out_v = [], []
    for i, x in zip(idx, val):
        if bounds is not None:
            x = _clip(x, bounds[0][i], bounds[1][i])
        z = (x - mean[i]) / std[i]
        if z > clip:
            z = clip
        elif z < -clip:
            z = -clip
        if z != 0:
            out_i.append(i)
            out_v.append(z)
    return out_i, out_v


def class_weights(rows):
    """Dengesizlik düzeltmesi — YUMUŞATILMIŞ (karekök + tavan 3.0).

    Neden tam ters-frekans DEĞİL: 1 örnekli bir sınıf 11× ağırlık alıp kaybı domine ediyor,
    diğer sınıflar eziliyordu (ölçüldü: top-1 %0,7). Karekök + tavan, tek örnekli sınıfı
    görünür kılar ama modeli ona teslim etmez (PLAN §M1 "class weights" ruhu korunur).
    """
    from collections import Counter
    cnt = Counter(r["cls"] for r in rows)
    tot = sum(cnt.values())
    out = {}
    for c in CLASSES:
        if cnt.get(c):
            out[c] = min(3.0, math.sqrt(tot / (len(cnt) * cnt[c])))
        else:
            out[c] = 0.0
    return out


def feat_get(row, name):
    """Özelliği ADLA okur; satır indekslenmişse (load_rows sonrası) adı indekse çevirir."""
    feat = row["feat"]
    if name in feat:
        return feat[name]
    i = name2index().get(name)
    return feat.get(i) if i is not None else None


def style_of(row):
    """Satırın stili: J bayraklarından okunur (stud > anime > cartoon); yoksa None."""
    for s in STYLES:
        if feat_get(row, STYLE_FLAG[s]):
            return s
    return None


def style_log_bias(style, priors):
    """Öncülü LOG uzayında logit'e ekler: skor × bias == logit + ln(bias) (çarpım = toplama).

    12 ondalığa yuvarlanır: gömülü modülde (tools/export_model.py) duran değerle BİT AYNI olsun.
    Aksi halde uç uçta (neredeyse eşit) sınıfların sırası iki dilde farklı çıkabilir.
    """
    out = [0.0] * len(CLASSES)
    if not style:
        return out
    bias = (priors.get(style) or {}).get("classBias") or {}
    for c, b in bias.items():
        if c in CLASSES and b > 0:
            out[CLASSES.index(c)] = round(math.log(b), 12)
    return out


# ---------------------------------------------------------------------------
# EĞİTİM — toplu (full-batch) gradyan + momentum, L2, erken durdurma
# ---------------------------------------------------------------------------
def train(rows, dim, epochs, lr, momentum, l2, patience, val_frac, seed, log=True):
    if not rows:
        raise SystemExit("eğitim verisi yok")
    bounds = winsor_bounds(rows, dim)
    mean, std = standardize(rows, dim, bounds)
    cw = class_weights(rows)

    # determinist bölme: sınıf içinde indeks sırasına göre her `k`inci satır doğrulamaya
    step = max(2, int(round(1.0 / val_frac)))
    train_rows, val_rows = [], []
    for c in CLASSES:
        same = [r for r in rows if r["cls"] == c]
        for j, r in enumerate(same):
            (val_rows if (j % step == 0) else train_rows).append(r)
    if not train_rows:
        train_rows, val_rows = rows, rows
    if not val_rows:
        val_rows = train_rows

    def prep(dataset):
        out = []
        for r in dataset:
            i, v = norm_row(r, mean, std, bounds)
            out.append((i, v, CLASSES.index(r["cls"]),
                        float(r.get("w", 1.0)), cw[r["cls"]]))
        return out
    TR, VA = prep(train_rows), prep(val_rows)

    C, D = len(CLASSES), dim
    W = [[0.0] * D for _ in range(C)]
    b = [0.0] * C
    vW = [[0.0] * D for _ in range(C)]
    vb = [0.0] * C

    def logits(i_, v_, lb=None):
        out = []
        for c in range(C):
            s = b[c]
            Wc = W[c]
            for j, x in zip(i_, v_):
                s += Wc[j] * x
            if lb:
                s += lb[c]
            out.append(s)
        return out

    def softmax(z):
        m = max(z)
        e = [math.exp(x - m) for x in z]
        s = sum(e)
        return [x / s for x in e]

    def loss(data):
        tot = 0.0
        for i_, v_, y_, w_, cwt in data:
            p = softmax(logits(i_, v_))
            tot -= w_ * cwt * math.log(max(p[y_], 1e-12))
        return tot / max(1, len(data))

    best = (loss(VA), [[x for x in row] for row in W], list(b), 0)
    for ep in range(1, epochs + 1):
        gW = [[0.0] * D for _ in range(C)]
        gb = [0.0] * C
        sw = 0.0
        for i_, v_, y_, w_, cwt in TR:
            p = softmax(logits(i_, v_))
            sw += w_ * cwt
            k = w_ * cwt
            for c in range(C):
                d = k * (p[c] - (1.0 if c == y_ else 0.0))
                if d == 0.0:
                    continue
                gb[c] += d
                gWc = gW[c]
                for j, x in zip(i_, v_):
                    gWc[j] += d * x
        n = max(1.0, sw)
        for c in range(C):
            vb[c] = momentum * vb[c] - lr * (gb[c] / n)
            b[c] += vb[c]
            gWc, vWc, Wc = gW[c], vW[c], W[c]
            for j in range(D):
                g = gWc[j] / n + l2 * Wc[j]
                if g:
                    vWc[j] = momentum * vWc[j] - lr * g
                    Wc[j] += vWc[j]
        vl = loss(VA)
        if vl < best[0] - 1e-9:
            best = (vl, [[x for x in row] for row in W], list(b), ep)
        elif ep - best[3] >= patience:
            if log:
                print("  [i] erken durdurma: %d. tur (en iyi %d)" % (ep, best[3]))
            break
    if log:
        print("  [i] eğitim: %d örnek · %d doğrulama · en iyi tur %d · val loss %.4f"
              % (len(TR), len(VA), best[3], best[0]))
    return {"W": best[1], "b": best[2], "mean": mean, "std": std, "clipZ": CLIP_Z,
            "trainRows": train_rows, "valRows": val_rows}


# ---------------------------------------------------------------------------
# TAHMİN (çalışma zamanı matematiğinin TEK kanonu — eval.py bunu kullanır)
# ---------------------------------------------------------------------------
def predict(model, row, classes=None):
    """model → {cls, conf, top3, probs}. `model`, model.json'un `models.class` bloğudur."""
    classes = classes or model["classes"]
    idx, val = sparse(indexed(row, strict=False))
    mean, std = model["norm"]["mean"], model["norm"]["std"]
    clip = float(model.get("clipZ", CLIP_Z))
    lb = style_log_bias(style_of(row), model.get("stylePriors") or {})
    # z katkısı: (x-mean)/std, ±clip'e kırpılır — gömülü JS/Lua ile birebir aynı adım
    zc = []
    for i, x in zip(idx, val):
        t = (x - mean[i]) / std[i]
        if t > clip:
            t = clip
        elif t < -clip:
            t = -clip
        zc.append((i, t))
    z = []
    for c in range(len(classes)):
        s = model["b"][c]
        Wc = model["W"][c]
        for i, t in zc:
            s += Wc[i] * t
        z.append(s + lb[c])
    m = max(z)
    e = [math.exp(x - m) for x in z]
    tot = sum(e)
    p = [x / tot for x in e]
    # v15 tahmin kapısı (JS/Lua ile birebir): destek eşiği altındakiler seçilmez; olasılıklar
    # ham en iyi aday kapıya takılırsa güven 0,69'da sınırlanır.
    elig = model.get("elig") or [True] * len(classes)
    raw = min(range(len(classes)), key=lambda c: (-p[c], classes[c]))
    pe = p  # güven HAM olasılıktan (yeniden normalize edilmez → güven şişmez)
    order = sorted([c for c in range(len(classes)) if elig[c]], key=lambda c: (-pe[c], classes[c]))
    if order:
        cls, conf = classes[order[0]], pe[order[0]]
    else:
        cls, conf = classes[raw], 0
    if (not elig[raw]) and conf > 0.69:
        conf = 0.69
    return {
        "cls": cls,
        "conf": conf,
        "top3": [[classes[c], pe[c]] for c in order[:3]],
        "probs": p,
    }


def accuracy(rows, model_cls):
    """top-1 / top-3 / sınıf bazlı rapor + karışıklık matrisi (determinist sıra)."""
    hit1 = hit3 = 0
    per = {c: [0, 0] for c in CLASSES}
    conf = {c: {d: 0 for d in CLASSES} for c in CLASSES}
    lens = []
    for r in rows:
        pr = predict(model_cls, r)
        y = r["cls"]
        lens.append(len(pr["probs"]))
        per[y][1] += 1
        conf[y][pr["cls"]] += 1
        if pr["cls"] == y:
            hit1 += 1
            per[y][0] += 1
        if y in [t[0] for t in pr["top3"]]:
            hit3 += 1
    n = max(1, len(rows))
    return {
        "n": len(rows),
        "top1": hit1 / n,
        "top3": hit3 / n,
        "per": {c: (v[0] / v[1] if v[1] else None) for c, v in per.items()},
        "support": {c: v[1] for c, v in per.items()},
        "confusion": {c: {d: k for d, k in row.items() if k} for c, row in conf.items() if per[c][1]},
    }


def fmt_report(rep, title="SINIF MODELİ — DEĞERLENDİRME"):
    print("=" * 74)
    print(title)
    print("=" * 74)
    print("  örnek      : %d" % rep["n"])
    print("  top-1      : %6.2f%%   (kabul ≥ 85.00%%)" % (100 * rep["top1"]))
    print("  top-3      : %6.2f%%   (kabul ≥ 95.00%%)" % (100 * rep["top3"]))
    print("  sınıf      : " + ", ".join(
        "%s %s" % (c, ("%.0f%%" % (100 * v)) if v is not None else "—")
        for c, v in rep["per"].items() if rep["support"][c]))
    bad = [c for c in CLASSES if rep["support"][c] and (rep["per"][c] or 0) < 1.0]
    if bad:
        print("  karışan    :")
        for c in bad:
            row = rep["confusion"].get(c, {})
            w = ", ".join("%s×%d" % (d, k) for d, k in sorted(row.items()) if d != c)
            print("      %-14s → %s" % (c, w or "(yok)"))
    return rep


def export_model(tr, dim, classes, style_priors, out_path, meta, round_nd=6):
    """Gömülebilir model.json: 6 ondalığa yuvarlanır → bayt- kararlı çıktı, dürüst metrik."""
    r = lambda x: round(float(x), round_nd)  # noqa: E731
    blocks = [{"n": "W", "d": [[r(v) for v in row] for row in tr["W"]]},
              {"n": "b", "d": [r(v) for v in tr["b"]]},
              {"n": "mean", "d": [r(v) for v in tr["mean"]]},
              {"n": "std", "d": [r(v) for v in tr["std"]]}]
    h = hashlib.sha256()
    for blk in blocks:
        h.update(json.dumps(blk, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    obj = {
        "format": "ei-model",
        "version": 1,
        "featureSpec": "ei-feat-1",
        "dim": dim,
        "models": {
            "class": {
                "type": "softmax",
                "classes": classes,
                "W": blocks[0]["d"],
                "b": blocks[1]["d"],
                "norm": {"mean": blocks[2]["d"], "std": blocks[3]["d"]},
                "clipZ": round(float(tr.get("clipZ", CLIP_Z)), 6),
                "stylePriors": style_priors,
            }
        },
        "meta": meta,
    }
    obj["meta"]["checksum"] = "sha256:" + h.hexdigest()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, sort_keys=True, indent=1)
        fh.write("\n")
    return obj


def export_loo(rows, dim, epochs, lr, l2, patience, val_frac, seed, priors, verbose=True):
    """Her fixture'ı dışarıda bırakıp kalanla eğitir; dıştakinin top-1/top-3'ünü ölçer.

    Dosya adları ground truth DEĞİL; yalnızca gruplama anahtarıdır (aynı ekrandan gelen
    satırlar birlikte dışarıda kalır — satır bazlı bölmeden çok daha dürüst).
    """
    exports = sorted({r.get("export") or "?" for r in rows})
    scores, det = [], []
    for e in exports:
        tr_rows = [r for r in rows if (r.get("export") or "?") != e]
        va_rows = [r for r in rows if (r.get("export") or "?") == e]
        if not tr_rows or not va_rows:
            continue
        t = train(tr_rows, dim, epochs, lr, DEFAULTS["momentum"], l2, patience, val_frac, seed, log=False)
        m = {"classes": CLASSES, "W": t["W"], "b": t["b"],
             "norm": {"mean": t["mean"], "std": t["std"]},
             "clipZ": t.get("clipZ", CLIP_Z), "stylePriors": priors}
        sc = accuracy(va_rows, m)
        scores.append(sc["top1"])
        det.append({"export": e, "top1": sc["top1"], "top3": sc["top3"], "n": sc["n"]})
        if verbose:
            print("  [dışta %-14s] top-1 %6.2f%% · top-3 %6.2f%% (%d katman)"
                  % (e, 100 * sc["top1"], 100 * sc["top3"], sc["n"]))
    if not scores:
        return None
    mean = sum(scores) / len(scores)
    if verbose:
        print("  [i] export-LOO: ortalama top-1 %.2f%% (en kötü %.2f%%)" % (100 * mean, 100 * min(scores)))
    return {"mean": mean, "min": min(scores), "folds": len(scores), "det": det}


def main():
    ap = argparse.ArgumentParser(add_help=True, description="Sınıf modeli eğitici (softmax)")
    ap.add_argument("data", nargs="*", default=[],
                    help="JSONL (varsayılan: datasets/labels/*.jsonl)")
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "model", "model.json"))
    ap.add_argument("--dim", type=int, default=None)
    ap.add_argument("--eval", action="store_true", help="eğitimden sonra rapor + kabul kontrolü")
    ap.add_argument("--cv", type=int, default=0, help="k-katlı çapraz doğrulama (ör. 5)")
    ap.add_argument("--loo", action="store_true",
                    help="export bazlı bırak-birini-dışarıda: satır bazlı CV'den DÜRÜST ölçüt "
                         "(aynı export'un katmanları birbirine benzer)")
    ap.add_argument("--epochs", type=int, default=DEFAULTS["epochs"])
    ap.add_argument("--lr", type=float, default=DEFAULTS["lr"], help="öğrenme oranı (etkin-ağırlık normalizasyonundan sonra)")
    ap.add_argument("--l2", type=float, default=DEFAULTS["l2"])
    ap.add_argument("--patience", type=int, default=DEFAULTS["patience"])
    ap.add_argument("--val-frac", type=float, default=DEFAULTS["val_frac"])
    ap.add_argument("--stamp", action="store_true", help="model.json'a tarih yaz (bayt-kararlılığı bozar)")
    a = ap.parse_args()

    import feature_index  # noqa: E402
    spec = feature_index.load_spec()
    dim = a.dim or spec["dim"]
    name2index(spec)

    paths = a.data
    if not paths:
        base = os.path.join(ROOT, "datasets", "labels")
        paths = sorted(os.path.join(base, f) for f in os.listdir(base) if f.endswith(".jsonl"))
    if not paths:
        print(__doc__.strip())
        return 1

    rows = load_rows(paths, dim)
    print("=" * 74)
    print("SINIF MODELİ — EĞİTİM")
    print("=" * 74)
    print("  veri       : %s" % ", ".join(os.path.basename(p) for p in paths))
    print("  örnek      : %d · boyut %d · sınıf %d" % (len(rows), dim, len(CLASSES)))

    priors = {}
    spr = os.path.join(ROOT, "spec", "style-rules.json")
    if os.path.exists(spr):
        with open(spr, encoding="utf-8") as fh:
            priors = (json.load(fh).get("_stylePriors") or {})
        priors.pop("_desc", None)

    # ---- k-kat çapraz doğrulama (rapor) ----
    cv = None
    if a.cv and a.cv >= 2:
        scores = []
        for k in range(a.cv):
            tr_rows, va_rows = [], []
            for c in CLASSES:
                same = [r for r in rows if r["cls"] == c]
                for j, r in enumerate(same):
                    (va_rows if j % a.cv == k else tr_rows).append(r)
            t = train(tr_rows, dim, a.epochs, a.lr, DEFAULTS["momentum"], a.l2, a.patience,
                      a.val_frac, DEFAULTS["seed"], log=False)
            m = {"classes": CLASSES, "W": t["W"], "b": t["b"],
                 "norm": {"mean": t["mean"], "std": t["std"]}, "stylePriors": priors}
            s = accuracy(va_rows, m)
            scores.append(s["top1"])
            print("  [%d/%d] top-1 %.2f%% · top-3 %.2f%% (%d örnek)"
                  % (k + 1, a.cv, 100 * s["top1"], 100 * s["top3"], s["n"]))
        mean = sum(scores) / len(scores)
        var = sum((x - mean) ** 2 for x in scores) / len(scores)
        cv = {"folds": a.cv, "mean": mean, "std": math.sqrt(var)}
        print("  [i] %d-katlı CV: top-1 %.2f%% ± %.2f%%" % (a.cv, 100 * mean, 100 * math.sqrt(var)))
        if not a.out:
            return 0

    # ---- export bazlı bırak-birini-dışarıda (dürüst genelleme ölçütü) ----
    loo = None
    if a.loo or a.eval:
        print("  [i] export-LOO hesaplanıyor (%d kat)…" % len({r.get("export") or "?" for r in rows}))
        loo = export_loo(rows, dim, a.epochs, a.lr, a.l2, a.patience, a.val_frac,
                         DEFAULTS["seed"], priors, verbose=True)
        if loo and not a.out:
            return 0

    # ---- nihai model: TÜM veri ----
    t = train(rows, dim, a.epochs, a.lr, DEFAULTS["momentum"], a.l2, a.patience, a.val_frac, DEFAULTS["seed"])
    m = {"classes": CLASSES, "W": t["W"], "b": t["b"],
         "norm": {"mean": t["mean"], "std": t["std"]}, "stylePriors": priors}
    if a.eval:
        fmt_report(accuracy(rows, m), "SINIF MODELİ — EĞİTİM SETİ RAPORU (iyimser, bilgi amaçlı)")
        if t["valRows"] and len(t["valRows"]) != len(rows):
            fmt_report(accuracy(t["valRows"], m), "SINIF MODELİ — DOĞRULAMA (ayrılmış) RAPORU")
        no_bias = dict(m)
        no_bias["stylePriors"] = {}
        fmt_report(accuracy(rows, no_bias),
                   "STİL ÖNCÜLÜ OLMADAN (karşılaştırma — öncül farkı görmek için)")

    # ---- dışa aktarım + yuvarlanmış modelle dürüst metrik ----
    meta = {
        "samples": len(rows),
        "classes": len(CLASSES),
        "dim": dim,
        "folds": (cv or {}).get("folds", 0),
        "cvTop1": (cv or {}).get("mean"),
        "looTop1": (loo or {}).get("mean"),
        "looWorst": (loo or {}).get("min"),
        "looFolds": (loo or {}).get("folds"),
        "trainedAt": None,
    }
    if a.stamp:
        import datetime
        meta["trainedAt"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    obj = export_model(t, dim, CLASSES, priors, a.out, meta, DEFAULTS["round_nd"])
    rc = 0
    if a.eval:
        rep = fmt_report(accuracy(rows, obj["models"]["class"]),
                         "DAĞITILAN MODEL (yuvarlanmış, öncüllü) — KABUL KONTROLÜ")
        obj["meta"]["trainAcc"] = round(rep["top1"], 6)
        obj["meta"]["trainTop3"] = round(rep["top3"], 6)
        if t["valRows"] and len(t["valRows"]) != len(rows):
            vrep = accuracy(t["valRows"], obj["models"]["class"])
            obj["meta"]["valAcc"] = round(vrep["top1"], 6)
            obj["meta"]["valTop3"] = round(vrep["top3"], 6)
        else:
            obj["meta"]["valAcc"] = None
            obj["meta"]["valTop3"] = None
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, sort_keys=True, indent=1)
            fh.write("\n")
        doc = obj["models"]["class"]
        acc = accuracy(rows, doc)
        loo_top1 = (loo or {}).get("mean")
        if acc["top1"] < 0.85 or acc["top3"] < 0.95 or (loo_top1 is not None and loo_top1 < LOO_MIN):
            print("=" * 74)
            print("SONUÇ: BAŞARISIZ — eğitim top-1 %.2f%% / top-3 %.2f%% · LOO %s"
                  % (100 * acc["top1"], 100 * acc["top3"],
                     ("%.2f%%" % (100 * loo_top1)) if loo_top1 is not None else "hesaplanmadı"))
            rc = 2
        else:
            print("=" * 74)
            print("SONUÇ: GEÇTİ — eğitim top-1 %.2f%% · top-3 %.2f%% · LOO %.2f%% · %s"
                  % (100 * acc["top1"], 100 * acc["top3"], 100 * loo_top1, a.out))
    else:
        print("  [i] model yazıldı: %s (%s)" % (a.out, obj["meta"]["checksum"]))
    return rc


if __name__ == "__main__":
    sys.exit(main())
