#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3 — EĞİTİM VERİSİ ÜRETİCİ (ingest)

    Figma export JSON  ──▶  RAW çıkarıcı (JS, canon)  ──▶  379 boyutlu özellik vektörü
                                                                    │
                            öğretmen etiketi (rules_teacher.py) ────┘
                                              ▼
                                  samples.jsonl (satır = 1 katman)

Neden bu hattı: model, "doğru cevabı" Studio'nun mevcut kural motorundan öğreniyor. Öğretmenin
Studio ile birebir aynı olduğu `tools/verify_teacher.py` kapısıyla kanıtlanır; bu betik o
öğretmeni ve A1 özellik vektörünü birleştirip eğitime hazır örnek üretir.

Örnek satır:
    {"v":1,"src":"rule-teacher","export":"stud-market","doc":{"w":720,"h":900},
     "path":"0.2.5","name":"Play_Button","clean":"Play","cls":"TextButton",
     "feat":{"tok_play":1,"aspect":2.5,...},          // yalnızca sıfır olmayanlar (seyrek)
     "obs":{"sw":2,"r":12,"nSh":1}}                    // tasarımda GÖZLENEN kontur/köşe/gölge (M2 için)

`src` ağırlıkları (PLAN §5): manual 1.0 · user-correction 0.8 · rule-teacher 0.35

Kullanım:
    python3 tools/ingest.py datasets/raw/*.json -o datasets/labels/bootstrap.jsonl
    python3 tools/ingest.py --stats datasets/labels/bootstrap.jsonl       # özet rapor

Çıkış: 0 = başarılı
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "runtime", "python"))

import ei_features  # noqa: E402
import feature_index  # noqa: E402
import rules_teacher  # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")

# --- Node köprüsü: RAW çıkarıcının tek kanon uygulaması JS'te yaşar -------------
JS_RUNNER = r"""
const EIRaw = require(process.argv[2] + '/ei-raw.js');
const EIStyle = require(process.argv[2] + '/ei-style.js');
const fs = require('fs');
const doc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = EIRaw.extract(doc, { styleFn: EIStyle.detect });
const st = out.style ? { version: out.style.version, style: out.style.style,
                         conf: out.style.conf, scores: out.style.scores } : null;
process.stdout.write(JSON.stringify({ gui: out.gui, nodes: out.nodes, style: st }));
"""

WEIGHTS = {"manual": 1.0, "user-correction": 0.8, "rule-teacher": 0.35}
SPEC_J = set()   # J grubu (stil) özellik adları — __main__'de doldurulur


def run_raw(path):
    """Export dökümanını JS çıkarıcıdan geçirir → {"gui":…, "nodes":[…], "style":…}.

    Stil dedektörü de (A10) kanon JS'ten geçirilir; böylece J grubu özellikleri
    (stil bayrakları + GUI sinyalleri) eğitim satırlarında CANLI olur.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(JS_RUNNER)
        runner = fh.name
    try:
        r = subprocess.run(["node", runner, JS_DIR, path],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError("node hatası:\n" + (r.stderr or "")[:2000])
        return json.loads(r.stdout)
    finally:
        os.unlink(runner)


def flatten_items(doc):
    """EIRaw.flatten ile BİREBİR aynı sıra: kök, sonra çocuklar (derinlik öncelikli).

    Dönen liste: (path, item) ikilileri. path = "0.2.5" biçiminde derinlik öncelikli yol
    (PLAN §2.1'deki `ei.assistant.predictions` anahtarıyla aynı biçim).
    """
    out = []

    def rec(item, path):
        out.append((path, item))
        for j, ch in enumerate(item.get("children") or []):
            rec(ch, path + "." + str(j))

    rec(doc["root"], "0")
    return out


def sample_from(item, raw, export_name, doc, path, style=None):
    clean, cls = rules_teacher.classify(item)
    vec = ei_features.compute(SPEC, raw)
    stroke = item.get("stroke") or {}
    obs = {
        "sw": (item.get("strokeWeight") if isinstance(item.get("strokeWeight"), (int, float))
               else (stroke.get("weight") if isinstance(stroke.get("weight"), (int, float)) else 0)),
        "r": item.get("radius"),
        "nSh": len(item.get("shadows") or ([item["shadow"]] if item.get("shadow") else [])),
    }
    return {
        "v": 1,
        "src": "rule-teacher",
        "style": (style or {}).get("style", "belirsiz"),
        "styleConf": (style or {}).get("conf", 0),
        "w": WEIGHTS["rule-teacher"],
        "export": export_name,
        "doc": {"w": doc.get("width"), "h": doc.get("height")},
        "path": path,
        "name": item.get("name"),
        "clean": clean,
        "cls": cls,
        "kind": item.get("kind"),
        "feat": feature_index.sparse(SPEC, vec, ndigits=6),
        "obs": obs,
    }


def ingest(paths, out_path, append=False):
    rows = []
    per = {}
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        name = doc.get("name") or os.path.splitext(os.path.basename(path))[0]
        raw = run_raw(path)
        nodes = raw["nodes"]
        pairs = flatten_items(doc)
        if len(nodes) != len(pairs):
            raise RuntimeError("%s: RAW %d düğüm ama ağaçta %d katman — sıra eşleşmiyor"
                               % (path, len(nodes), len(pairs)))
        got = 0
        style = raw.get("style")
        if style:
            print("  [i] %-16s stil: %s (conf %.3f)" % (name, style["style"], style["conf"]))
        else:
            print("  [!] %-16s stil dedektörü çalışmadı" % name)
        for (pth, item), r in zip(pairs, nodes):
            rows.append(sample_from(item, r, name, doc, pth, style))
            got += 1
        per[name] = got
        print("  [OK] %-16s %3d katman → örnek" % (name, got))

    mode = "a" if append else "w"
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, mode, encoding="utf-8") as fh:
        for s in rows:
            fh.write(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n")
    print("  [i] %d örnek %s'e yazıldı (%s)" % (len(rows), out_path, "eklendi" if append else "yazıldı"))
    _report(rows)
    return 0


def _report(rows):
    from collections import Counter
    cls = Counter(r["cls"] for r in rows)
    print("  [i] sınıf dağılımı: " + ", ".join("%s=%d" % kv for kv in sorted(cls.items())))
    feats = sum(len(r["feat"]) for r in rows)
    print("  [i] ortalama dolu özellik: %.1f / %d" % (feats / max(1, len(rows)), SPEC["dim"]))
    st = Counter(r.get("style", "yok") for r in rows)
    print("  [i] stil dağılımı: " + ", ".join("%s=%d" % kv for kv in sorted(st.items())))
    jnames = set(SPEC_J) if SPEC_J else set()
    jlive = Counter()
    for r in rows:
        for k in r["feat"]:
            if k in jnames:
                jlive[k] += 1
    print("  [i] J grubu (stil) canlı özellik: %d/%d" % (len(jlive), len(jnames)))


def stats(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    from collections import Counter
    print("=" * 70)
    print("ÖRNEK ÖZETİ — %s" % path)
    print("=" * 70)
    print("  satır            : %d" % len(rows))
    print("  export           : " + ", ".join("%s=%d" % kv for kv in sorted(Counter(r["export"] for r in rows).items())))
    print("  kaynak (src)     : " + ", ".join("%s=%d" % kv for kv in sorted(Counter(r["src"] for r in rows).items())))
    print("  sınıf            : " + ", ".join("%s=%d" % kv for kv in sorted(Counter(r["cls"] for r in rows).items())))
    st = Counter(r.get("style", "yok") for r in rows)
    print("  stil             : " + ", ".join("%s=%d" % kv for kv in sorted(st.items())))
    specs = Counter(len(r["feat"]) for r in rows)
    print("  dolu özellik     : ort %.1f · min %d · max %d"
          % (sum(len(r["feat"]) for r in rows) / max(1, len(rows)), min(specs), max(specs)))
    return 0


def main():
    args = [a for a in sys.argv[1:]]
    append = "--append" in args
    args = [a for a in args if a != "--append"]

    if "--stats" in args:
        i = args.index("--stats")
        return stats(args[i + 1])

    out_path = os.path.join(ROOT, "datasets", "labels", "bootstrap.jsonl")
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__.strip())
        return 1

    print("=" * 70)
    print("INGEST — export JSON → eğitim örnekleri")
    print("=" * 70)
    return ingest(args, out_path, append)


if __name__ == "__main__":
    SPEC = feature_index.load_spec()
    names = feature_index.names(SPEC)                      # index sırasıyla 379 ad
    groups = []
    for f in SPEC["index"]:
        groups += [f.get("g")] * f.get("count", 1)
    SPEC_J = {n for n, g in zip(names, groups) if g == "J"}
    sys.exit(main())
