#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFEKT SİMGE MODELİ (v23 eğitimi) — çok terimli Naive Bayes, ad + kategori kelimeleri.

Veri : datasets/labels/effect-icons.jsonl  (tools/fx_labels.js; ZAYIF denetim: etiketler tohum kurallarından)
Kural: yeterli örneği olmayan sınıflar (MIN_SUPPORT) modele girmez (sınıf modelindeki destek kapısıyla aynı mantık).
Çıktı: assistant/runtime/js/ei-fxmodel.js  (EIFxModel: sınıflar, önsel, token log-olasılıkları)
Ölçüm: 5 katlı çapraz geçerlilik (deterministik) + çoğunluk tabanı. Raporu stdout'a yazar.

Kullanım: python3 tools/train_fx.py
"""
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LABELS = os.path.join(ROOT, "datasets", "labels", "effect-icons-human.jsonl")  # insan-gözden (görsel) etiketler
NONE = "none"   # efekt için uygun değil: modelin açıkça öğrendiği bir sınıf; destek eşiğinden muaf
OUT = os.path.join(ROOT, "runtime", "js", "ei-fxmodel.js")
MIN_SUPPORT = 10
ALPHA = 1.0
FOLDS = 5


def tokens(icon):
    # Yalnız simge adı ve etiketi. Kategori tokenı (cat_*) KULLANILMAZ: kategoriyi dışarıda bırakma testinde
    # genellemeyi bozuyordu (0,19 → 0,33 kaldırınca). Kimlik ve kategori eğitim verisinde sızdırıcıdır.
    raw = " ".join([icon.get("name", ""), icon.get("label", "")])
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    return sorted(set(t for t in re.split(r"[^a-z0-9_]+", raw) if len(t) >= 2))


def load():
    rows = []
    for ln in open(LABELS, encoding="utf-8"):
        if ln.strip():
            rows.append(json.loads(ln))
    items = json.load(open(os.path.join(ROOT, "..", "kutuphane", "ekstra-kutuphane.json"), encoding="utf-8"))["items"]
    byid = {i["id"]: i for i in items}
    data = []
    for r in rows:
        if r["label"] is None:
            continue
        ic = dict(byid[r["id"]])
        data.append((tokens(ic), r["label"], r["id"]))
    return data


def train(data, classes):
    prior = Counter(l for _, l, _ in data)
    tok_count = defaultdict(Counter)
    total = Counter()
    vocab = set()
    for toks, lab, _ in data:
        for t in toks:
            tok_count[lab][t] += 1
            total[lab] += 1
            vocab.add(t)
    V = max(1, len(vocab))
    n = len(data)
    model = {"classes": classes,
             "prior": {c: math.log(prior[c] / n) for c in classes},
             "logp": {},
             "unk": {}}
    for c in classes:
        model["unk"][c] = math.log(ALPHA / (total[c] + ALPHA * V))
    for t in vocab:
        model["logp"][t] = {c: math.log((tok_count[c][t] + ALPHA) / (total[c] + ALPHA * V)) for c in classes}
    return model


def predict(model, toks):
    classes = model["classes"]
    score = {}
    for c in classes:
        s = model["prior"][c]
        for t in toks:
            s += model["logp"][t][c] if t in model["logp"] else model["unk"][c]
        score[c] = s
    m = max(score.values())
    e = {c: math.exp(score[c] - m) for c in classes}
    z = sum(e.values())
    return {c: e[c] / z for c in classes}


def cross_validate(data, classes):
    ordered = sorted(data, key=lambda d: d[2])          # deterministik katlar
    folds = [ordered[i::FOLDS] for i in range(FOLDS)]
    correct = 0
    base = 0
    for k in range(FOLDS):
        test = folds[k]
        train_set = [d for j in range(FOLDS) if j != k for d in folds[j]]
        model = train(train_set, classes)
        maj = Counter(l for _, l, _ in train_set).most_common(1)[0][0]
        for toks, lab, _ in test:
            p = predict(model, toks)
            guess = max(classes, key=lambda c: (p[c], c))
            correct += int(guess == lab)
            base += int(maj == lab)
    return correct / len(data), base / len(data)


def main():
    data = load()
    counts = Counter(l for _, l, _ in data)
    classes = sorted(c for c, n in counts.items() if n >= MIN_SUPPORT or c == NONE)
    kept = [d for d in data if d[1] in classes]
    print("etiketli simge: %d · sınıflar: %s" % (len(data), ", ".join("%s=%d" % (c, counts[c]) for c in classes)))
    print("modelde kullanılmayan (destek < %d): %s" % (MIN_SUPPORT, ", ".join("%s=%d" % (c, n) for c, n in counts.items() if c not in classes) or "-"))
    acc, base = cross_validate(kept, classes)
    print("5 katlı çapraz geçerlilik doğruluğu: %.3f  (çoğunluk tabanı: %.3f)" % (acc, base))
    model = train(kept, classes)
    body = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("// EFEKT SİMGE MODELİ (otomatik: tools/train_fx.py). Naive Bayes; sınıflar ve log-olasılıklar.\n")
        fh.write("// Eğitim: %d insan-gözden etiketli simge (effect-icons-human.jsonl). 5 katlı CV doğruluk: %.3f, çoğunluk tabanı: %.3f.\n" % (len(kept), acc, base))
        fh.write("var EIFxModel = " + body + ";\n")
    print("[OK] %s (%d bayt, %d token)" % (OUT, os.path.getsize(OUT), len(model["logp"])))


if __name__ == "__main__":
    main()
