#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3 — SINIF MODELİ DEĞERLENDİRİCİ (eval)

    model/model.json + datasets/labels/*.jsonl ──▶ top-1 / top-3 raporu

Model matematiği `train_class.py`'de TEK kanon olarak durur (predict/accuracy); bu betik
yalnızca raporlar. Böylece eğitim, değerlendirme ve (gelecekte) Lua/JS çalışma zamanı
aynı formülü paylaşır:  z = W·(x-mean)/std + b + ln(styleBias)  →  softmax.

Raporlar:
  · genel top-1 / top-3, sınıf bazlı, karışıklık matrisi
  · STİL bazlı (stud / anime / cartoon / belirsiz) — stil öncülü işe yarıyor mu?
  · export bazlı — gerçek genelleme (aynı export'un katmanları birbirine benzer)

Kullanım:
    python3 tools/eval.py                                   # model + tüm jsonl
    python3 tools/eval.py model/model.json datasets/labels/bootstrap.jsonl
    python3 tools/eval.py --strict                          # eşik altıysa çıkış 2
    python3 tools/eval.py --json rapor.json                 # makine okunur çıktı
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import train_class as T  # noqa: E402  (paylaşılan kanon: predict/accuracy)

TOP1_MIN = 0.85
TOP3_MIN = 0.95


def load_model(path):
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    if obj.get("format") != "ei-model":
        raise SystemExit("%s: `format` ei-model değil" % path)
    doc = (obj.get("models") or {}).get("class")
    if not doc or doc.get("type") != "softmax":
        raise SystemExit("%s: models.class (softmax) yok" % path)
    cls = doc["classes"]
    if len(doc["W"]) != len(cls) or len(doc["b"]) != len(cls):
        raise SystemExit("%s: W/b satır sayısı sınıf sayısına uymuyor" % path)
    dim = len(doc["W"][0])
    if len(doc["norm"]["mean"]) != dim or len(doc["norm"]["std"]) != dim:
        raise SystemExit("%s: norm boyu W ile uyuşmuyor" % path)
    if obj.get("dim") not in (None, dim):
        raise SystemExit("%s: dim=%s ama W boyu %d" % (path, obj.get("dim"), dim))
    return obj, doc


def by_style(rows, doc):
    out = {}
    for r in rows:
        s = T.style_of(r) or "belirsiz"
        out.setdefault(s, []).append(r)
    return {s: T.accuracy(rs, doc) for s, rs in sorted(out.items())}


def by_export(rows, doc):
    out = {}
    for r in rows:
        out.setdefault(r.get("export") or "?", []).append(r)
    return {e: T.accuracy(rs, doc) for e, rs in sorted(out.items())}


def main():
    ap = argparse.ArgumentParser(description="Sınıf modeli değerlendirici")
    ap.add_argument("model", nargs="?", default=os.path.join(ROOT, "model", "model.json"))
    ap.add_argument("data", nargs="*", default=[])
    ap.add_argument("--strict", action="store_true", help="eşik altıysa çıkış kodu 2")
    ap.add_argument("--json", dest="json_out", default=None)
    a = ap.parse_args()

    if not os.path.exists(a.model):
        print("model yok: %s\n  önce: python3 tools/train_class.py --eval" % a.model)
        return 1
    obj, doc = load_model(a.model)

    paths = a.data
    if not paths:
        base = os.path.join(ROOT, "datasets", "labels")
        paths = sorted(os.path.join(base, f) for f in os.listdir(base) if f.endswith(".jsonl"))
    rows = T.load_rows(paths, len(doc["W"][0]))

    print("=" * 74)
    print("SINIF MODELİ — DEĞERLENDİRME")
    print("=" * 74)
    print("  model      : %s" % os.path.relpath(a.model, ROOT))
    print("  sürüm/özet : %s · %s" % (obj.get("version"), (obj.get("meta") or {}).get("checksum", "—")))
    print("  eğitim meta: %s" % json.dumps(
        {k: v for k, v in (obj.get("meta") or {}).items() if k in ("samples", "trainAcc", "valAcc")},
        ensure_ascii=False))
    print("  veri       : %s (%d satır)" % (", ".join(os.path.basename(p) for p in paths), len(rows)))

    rep = T.fmt_report(T.accuracy(rows, doc), "GENEL")

    print("-" * 74)
    print("  STİL BAZLI")
    st = by_style(rows, doc)
    for s, r in st.items():
        print("      %-9s %3d örnek · top-1 %6.2f%% · top-3 %6.2f%%"
              % (s, r["n"], 100 * r["top1"], 100 * r["top3"]))

    print("-" * 74)
    print("  EXPORT BAZLI (aynı export içinde — iyimser)")
    ex = by_export(rows, doc)
    for e, r in ex.items():
        print("      %-14s %3d katman · top-1 %6.2f%% · top-3 %6.2f%%"
              % (e, r["n"], 100 * r["top1"], 100 * r["top3"]))

    ok = rep["top1"] >= TOP1_MIN and rep["top3"] >= TOP3_MIN
    print("=" * 74)
    print("SONUÇ: %s — top-1 %.2f%% (≥ %.0f%%) · top-3 %.2f%% (≥ %.0f%%)"
          % ("GEÇTİ" if ok else "BAŞARISIZ", 100 * rep["top1"], 100 * TOP1_MIN,
             100 * rep["top3"], 100 * TOP3_MIN))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump({"model": a.model, "rows": len(rows), "overall": rep,
                       "byStyle": {k: v["top1"] for k, v in st.items()},
                       "byExport": {k: v["top1"] for k, v in ex.items()},
                       "pass": ok}, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        print("  [i] rapor: %s" % a.json_out)
    return 0 if (ok or not a.strict) else 2


if __name__ == "__main__":
    sys.exit(main())
