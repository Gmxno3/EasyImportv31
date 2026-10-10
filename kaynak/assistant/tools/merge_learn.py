#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S5 — ÖĞRENME PAKETİ BİRLEŞTİRİCİ (merge_learn)

    kullanıcıların EI_ogrenme_*.txt / *.json dosyaları
                     │
                     ▼
        bu betik (SUNUCU YOK — sen elle toplarsın)
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
  datasets/learn/merged.txt   önsel tablolar (--priors)
  (yeni eğitim girdisi)       (A7/A8'de animasyon önerisine gömülür)

Neden ayrı betik: öğrenme tamamen kullanıcının cihazında olur (KARARLAR §12); paket ancak
kullanıcı "öğrenme paketini indir" derse oluşur. Birleştirme **offline** yapılır, yani
sunucu, hesap ve arka plan gönderimi yoktur.

Biçim (YEREL-OGRENME §5, kanon `runtime/js/ei-learn.js`):

    ei-learn v1
    events 615
    exports 3
    anim <stil|sınıf|rol|fx> <animId> <seçildi> <reddedildi>
    cls  <stil|sınıf|rol|fx> <SınıfAdı> <sayı>

Not: yazılan dosyanın içeriği `encode()` çıktısı + **tek satır sonu**dur (POSIX). Kanon `decode`
boş satırı yok sayar (JS `''.split(' ')` hiçbir dala girmez), yani iki dil de dosyayı aynı okur.

Aşağıdaki kod bloğu `ei-learn.js`'in **birebir portu**dur (sanitize/kodlama/budama/skor).
Parite `tools/verify_merge.py` kapısında kanıtlanır: Node ile üretilen paketler birleştirilir,
çıkan metin tekrar Node'a verilip çözülür ve **bayt bayt aynı** sonuç beklenir.

Kullanım:
    python3 tools/merge_learn.py paketler/*.txt -o datasets/learn/merged.txt
    python3 tools/merge_learn.py paketler/*.json --priors datasets/learn/priors.json
    python3 tools/merge_learn.py --dedupe --min-observations 2 paketler/*

Çıkış: 0 = başarılı · 1 = girdi hatası · 2 = birleşik çıktı var ama şüpheli (uyarı)
"""

import argparse
import hashlib
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "datasets", "learn", "merged.txt")

VERSION = 1
DEFAULT_CAP = 400            # en fazla bağlam sayısı (ei-learn.js ile aynı)
DEFAULT_SIZE_CAP = 65536     # kodlanmış metin üst sınırı, bayt

CLASS_NAMES = ("Frame", "ImageLabel", "ImageButton", "TextLabel", "TextButton", "TextBox",
               "ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame",
               "UIGridLayout", "Item", "DROP", "MERGE")
STYLES = ("cartoon", "stud", "anime", "belirsiz")
# Bağlam parçası 4'tür: stil | sınıf | rol | fx


# --------------------------------------------------------------------- yardımcı
def sanitize(tok):
    """`ei-learn.js` sanitize(): A-Za-z0-9 ve `_ - | #` kalır, gerisi `_` olur, boş → '-'."""
    s = "-" if tok is None else str(tok)
    out = []
    for ch in s:
        if ch.isascii() and (ch.isalnum() or ch in "_-|#"):
            out.append(ch)
        else:
            out.append("_")
    t = "".join(out)
    return t if t else "-"


def ascii_lower(s):
    """ASCII küçültme — Lua/JS ile aynı (Türkçe İ/ı dönüştürülmez)."""
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in s)


def ctx_key(style, cls, role, fx):
    return "|".join(sanitize(ascii_lower(x)) for x in (style, cls, role, fx))


def to_int(s):
    """JS `toInt`: sayı değilse 0, taban, negatifse 0."""
    if isinstance(s, bool):
        return 1 if s else 0
    if isinstance(s, (int, float)):
        n = float(s)
    else:
        try:
            n = float(str(s).strip())
        except (TypeError, ValueError):
            return 0
    if not math.isfinite(n):
        return 0
    n = math.floor(n)
    return int(n) if n > 0 else 0


def byte_len(s):
    return len(s.encode("utf-8"))


# ------------------------------------------------------------------ durum/port
def new_state():
    return {"v": VERSION, "anim": {}, "cls": {}, "events": 0, "exports": 0}


def ensure_anim(st, ctx):
    st["anim"].setdefault(ctx, {})
    return st["anim"][ctx]


def ensure_cls(st, ctx):
    st["cls"].setdefault(ctx, {})
    return st["cls"][ctx]


def record_anim(st, ctx, anim_id, chosen, rejected):
    """Sayaçları toplar. `events` BURADA artmaz: o alan paketlerin kendi olay sayısıdır
    (`recordAnim` çağrı sayısı) ve birleştirmede paket başlıklarından toplanır."""
    m = ensure_anim(st, sanitize(ctx))
    key = sanitize(anim_id)
    cur = m.get(key, [0, 0])
    m[key] = [cur[0] + chosen, cur[1] + rejected]
    return st


def record_cls(st, ctx, cls_name, n):
    m = ensure_cls(st, sanitize(ctx))
    key = sanitize(cls_name)
    m[key] = m.get(key, 0) + n
    return st


def score_anim(st, ctx, anim_id):
    """(2c+1) / (2(c+r)+2) — yumuşatılmış kabul oranı, iki dilde birebir."""
    e = (st["anim"].get(ctx) or {}).get(sanitize(anim_id))
    if not e:
        return 0.5
    c, r = e
    return (2 * c + 1) / (2 * (c + r) + 2)


def obs_of(st, ctx, anim_id):
    e = (st["anim"].get(ctx) or {}).get(sanitize(anim_id))
    return (e[0] + e[1]) if e else 0


def total_of(st, ctx):
    t = 0
    for e in (st["anim"].get(ctx) or {}).values():
        t += e[0] + e[1]
    for n in (st["cls"].get(ctx) or {}).values():
        t += n
    return t


def count_contexts(st):
    seen = set(st["anim"].keys()) | set(st["cls"].keys())
    return len(seen)


def prune(st, max_ctx=DEFAULT_CAP):
    """En az kullanılan bağlamları atar: toplam gözlem ↑, sonra anahtar ↑ (deterministik)."""
    keys = list(st["anim"].keys())
    for k in st["cls"]:
        if k not in st["anim"]:
            keys.append(k)
    if len(keys) <= max_ctx:
        return st
    keys.sort(key=lambda k: (total_of(st, k), k))
    for k in keys[:len(keys) - max_ctx]:
        st["anim"].pop(k, None)
        st["cls"].pop(k, None)
    return st


def encode(st):
    lines = ["ei-learn v%d" % st.get("v", VERSION),
             "events %d" % st.get("events", 0),
             "exports %d" % st.get("exports", 0)]
    anim_rows = []
    for ctx, ids in st["anim"].items():
        for aid, e in ids.items():
            anim_rows.append("anim %s %s %d %d" % (ctx, aid, e[0], e[1]))
    anim_rows.sort()
    cls_rows = []
    for ctx, names in st["cls"].items():
        for cn, n in names.items():
            cls_rows.append("cls %s %s %d" % (ctx, cn, n))
    cls_rows.sort()
    return "\n".join(lines + anim_rows + cls_rows)


def fit(st, max_ctx=DEFAULT_CAP, max_bytes=DEFAULT_SIZE_CAP):
    """Boyut sınırını garantiler: bağlam sayısı, yetmezse %75 küçülterek (JS ile aynı)."""
    while count_contexts(st) > max_ctx:
        prune(st, max_ctx)
    n = max_ctx
    guard = 0
    while byte_len(encode(st)) > max_bytes and n > 1 and guard < 64:
        n = max(1, int(math.floor(n * 0.75)))
        prune(st, n)
        guard += 1
    return st


def decode(text):
    """`ei-learn.js` decode() portu — sözdizimi hatalarını sessizce atlar, biçimi bozmaz."""
    st = new_state()
    version = None
    for line in str(text if text is not None else "").split("\n"):
        p = line.split(" ")
        if p[0] == "ei-learn" and len(p) >= 2:
            v = p[1]
            if v.startswith("v"):
                try:
                    version = int(v[1:])
                except ValueError:
                    version = None
        elif p[0] == "events":
            st["events"] = to_int(p[1]) if len(p) > 1 else 0
        elif p[0] == "exports":
            st["exports"] = to_int(p[1]) if len(p) > 1 else 0
        elif p[0] == "anim" and len(p) >= 5:
            m = ensure_anim(st, sanitize(p[1]))
            key = sanitize(p[2])
            m[key] = [to_int(p[3]), to_int(p[4])]
        elif p[0] == "cls" and len(p) >= 4:
            ensure_cls(st, sanitize(p[1]))[sanitize(p[2])] = to_int(p[3])
    return st, version


# ------------------------------------------------------------- paket yükleme
def _text_from_json(obj):
    """JSON paketinden `ei-learn` metnini çıkarır (birkaç makul sarmalayıcı biçimi)."""
    if isinstance(obj, str):
        return obj, []
    if isinstance(obj, list):
        parts, extra = [], []
        for it in obj:
            t, e = _text_from_json(it)
            if t is not None:
                parts.append(t)
            extra.extend(e)
        return ("\n".join(parts) if parts else None), extra
    if isinstance(obj, dict):
        for key in ("text", "payload", "data", "learn", "paket", "ogrenme"):
            if isinstance(obj.get(key), str) and "ei-learn" in obj[key]:
                return obj[key], []
        for key in ("packages", "paketler", "files", "items"):
            if key in obj:
                return _text_from_json(obj[key])
    return None, []


def load_package(path):
    """Dosya → (durum, sürüm, uyarılar). Metin ve JSON sarmalayıcı kabul edilir."""
    with open(path, "rb") as fh:
        raw = fh.read()
    warnings = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", "replace")
        warnings.append("dosya UTF-8 değil — bozuk baytlar değiştirildi")
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            obj = json.loads(text)
        except ValueError as e:
            return None, None, warnings + ["JSON çözülemedi: %s" % e]
        text, extra = _text_from_json(obj)
        warnings.extend(extra)
        if text is None:
            return None, None, warnings + ["JSON içinde 'ei-learn' metni bulunamadı"]
    elif "ei-learn" not in text:
        return None, None, warnings + ["'ei-learn' başlığı yok — öğrenme paketi değil"]
    st, version = decode(text)
    return st, version, warnings


def merge_states(states, dedupe_files=None):
    """Durumları toplar: sayaçlar toplanır, events/exports toplanır."""
    out = new_state()
    for st in states:
        out["events"] += st.get("events", 0)
        out["exports"] += st.get("exports", 0)
        for ctx, ids in st["anim"].items():
            for aid, e in ids.items():
                record_anim(out, ctx, aid, e[0], e[1])
        for ctx, names in st["cls"].items():
            for cn, n in names.items():
                record_cls(out, ctx, cn, n)
    return out


def filter_min_observations(st, minimum):
    """Gürültü süzgeci: c+r < minimum olan animasyon kayıtlarını atar (varsayılan 0 = kapalı)."""
    if minimum <= 1:
        return st, 0
    dropped = 0
    for ctx in list(st["anim"].keys()):
        ids = st["anim"][ctx]
        for aid in list(ids.keys()):
            c, r = ids[aid]
            if c + r < minimum:
                del ids[aid]
                dropped += 1
        if not ids and ctx not in st["cls"]:
            del st["anim"][ctx]
    return st, dropped


# ------------------------------------------------------------------- raporlar
def _norm_tok(t):
    """Kütüphane `gradient-overlay`, özellik spec'i `gradient_overlay` yazar — karşılaştırmada eşitle."""
    return str(t).replace("_", "-")


def load_anim_ids():
    """(id kümesi, rol kümesi, fx türü kümesi) — anim-library.json'dan (yoksa boş kümeler)."""
    path = os.path.join(ROOT, "anim", "anim-library.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return set(), set(), set()
    anims = data.get("anims") or data.get("animations") or []
    ids = {a.get("id") for a in anims if a.get("id")}
    roles = {_norm_tok(r) for r in (data.get("_roles") or [])}
    fx = {_norm_tok(k) for k in (data.get("_fxKinds") or [])}
    for a in anims:                     # yedek: anim kaydının kendi listeleri
        roles |= {_norm_tok(r) for r in (a.get("roles") or [])}
        fx |= {_norm_tok(k) for k in (a.get("fxKinds") or [])}
    return ids, roles, fx


def analyse(st, anim_ids, roles, fx_kinds):
    """Birleşik durumdan özet + aykırılık listesi (geliştiricinin hızlı gözden geçirmesi)."""
    unknown_styles, unknown_classes, unknown_ids, unknown_roles = set(), set(), set(), set()
    bad_ctx, bad_fx = set(), set()
    for ctx in list(st["anim"].keys()) + [k for k in st["cls"] if k not in st["anim"]]:
        parts = ctx.split("|")
        if len(parts) != 4:
            bad_ctx.add(ctx)
            continue
        style, cls, role, fx = parts
        if style not in STYLES and style != "-":
            unknown_styles.add(style)
        # sınıf adı bağlamda küçük harfe iner (ctxKey kuralı: sanitize(lower(cls)))
        if cls != "-" and cls not in [c.lower() for c in CLASS_NAMES]:
            unknown_classes.add(cls)
        if role != "-" and roles and _norm_tok(role) not in roles:
            unknown_roles.add(role)
        if fx != "-" and fx_kinds and _norm_tok(fx) not in fx_kinds:
            bad_fx.add(fx)
    suspect = set()
    for ctx, ids in st["anim"].items():
        for aid in ids:
            if anim_ids and aid not in anim_ids:
                unknown_ids.add(aid)
            if aid.startswith("__") or any(p.startswith("__") for p in ctx.split("|")):
                # JS'te `obj["__proto__"] = …` prototipi bozar; kanon sanitize bunu geçirir.
                # Paket/önsel tablo yayınlanmadan önce bu satırlar ayıklanmalı.
                suspect.add(aid if aid.startswith("__") else ctx)
    for ctx in st["cls"]:
        if ctx.startswith("__"):
            suspect.add(ctx)

    top_ctx = sorted(st["anim"].keys(),
                     key=lambda c: (-total_of(st, c), c))[:8]
    rows = []
    for ctx, ids in st["anim"].items():
        for aid, (c, r) in ids.items():
            rows.append({"ctx": ctx, "id": aid, "chosen": c, "rejected": r,
                         "score": score_anim(st, ctx, aid), "n": c + r})
    rows.sort(key=lambda d: (-d["score"], -d["n"], d["id"], d["ctx"]))
    rejected_heavy = [d for d in rows if d["rejected"] > d["chosen"] and d["n"] >= 3]
    rejected_heavy.sort(key=lambda d: (-(d["rejected"] - d["chosen"]), d["id"], d["ctx"]))
    cls_rows = []
    for ctx, names in st["cls"].items():
        for cn, n in names.items():
            cls_rows.append({"ctx": ctx, "cls": cn, "n": n})
    cls_rows.sort(key=lambda d: (-d["n"], d["cls"], d["ctx"]))
    return {
        "contexts": count_contexts(st),
        "animRows": sum(len(v) for v in st["anim"].values()),
        "clsRows": sum(len(v) for v in st["cls"].values()),
        "events": st["events"],
        "bytes": byte_len(encode(st)),
        "animIds": len({aid for ids in st["anim"].values() for aid in ids}),
        "topContexts": [{"ctx": c, "n": total_of(st, c)} for c in top_ctx],
        "topSuggestions": rows[:10],
        "rejectedHeavy": rejected_heavy[:10],
        "classCorrections": cls_rows[:10],
        "unknownStyles": sorted(unknown_styles),
        "unknownClasses": sorted(unknown_classes),
        "unknownAnimIds": sorted(unknown_ids),
        "unknownRoles": sorted(unknown_roles),
        "unknownFx": sorted(bad_fx),
        "badCtx": sorted(bad_ctx),
        "suspectProto": sorted(suspect),
    }


def priors_doc(st):
    """A7/A8'in tüketeceği önsel tablo (JSON). Skor formülü `_meta`da yazılıdır."""
    anim = {}
    for ctx in sorted(st["anim"].keys()):
        ids = st["anim"][ctx]
        anim[ctx] = {aid: {"c": ids[aid][0], "r": ids[aid][1],
                           "score": round(score_anim(st, ctx, aid), 9),
                           "n": ids[aid][0] + ids[aid][1]}
                     for aid in sorted(ids.keys())}
    cls = {ctx: {cn: st["cls"][ctx][cn] for cn in sorted(st["cls"][ctx].keys())}
           for ctx in sorted(st["cls"].keys())}
    return {
        "format": "ei-learn-priors",
        "version": 1,
        "events": st["events"],
        "exports": st["exports"],
        "_meta": {
            "score": "(2*secildi+1) / (2*(secildi+reddedildi)+2)",
            "ctx": "stil|sinif|rol|fx",
            "source": "tools/merge_learn.py (kullanici paketleri, sunucusuz)",
        },
        "anim": anim,
        "cls": cls,
    }


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(add_help=True, description="Öğrenme paketlerini birleştirici")
    ap.add_argument("packages", nargs="*", help="kullanıcı öğrenme paketleri (.txt veya .json)")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT, help="birleşik öğrenme dosyası")
    ap.add_argument("--priors", default=None, help="önsel tablo JSON çıktısı (A7/A8 için)")
    ap.add_argument("--report", default=None, help="makine okunur rapor (JSON)")
    ap.add_argument("--dedupe", action="store_true",
                    help="bayt bayt aynı paketleri bir kez say (aynı kullanıcı iki kez gönderdiyse)")
    ap.add_argument("--min-observations", type=int, default=0,
                    help="c+r bu sayıdan az olan animasyon kayıtlarını at (varsayılan 0 = kapalı)")
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP, help="en fazla bağlam (varsayılan 400)")
    ap.add_argument("--size-cap", type=int, default=DEFAULT_SIZE_CAP,
                    help="kodlanmış metin üst sınırı, bayt (varsayılan 65536)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    print("=" * 74)
    print("ÖĞRENME PAKETİ BİRLEŞTİRİCİ (S5) — sunucusuz: dosyalar senin elinde")
    print("=" * 74)
    if not a.packages:
        print("  [i] paket verilmedi — kullanım: python3 tools/merge_learn.py paketler/*.txt")
        return 1

    seen_hash, skipped, warnings, bad_files, versions = {}, [], [], [], set()
    states, per_file = [], []
    for path in a.packages:
        if not os.path.exists(path):
            bad_files.append("%s: dosya yok" % path)
            continue
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        if a.dedupe and digest in seen_hash:
            skipped.append({"file": os.path.basename(path), "sameAs": seen_hash[digest]})
            continue
        seen_hash.setdefault(digest, os.path.basename(path))
        st, version, warn = load_package(path)
        if st is None:
            bad_files.append("%s: %s" % (os.path.basename(path), "; ".join(warn) or "okunamadı"))
            continue
        warnings.extend("%s: %s" % (os.path.basename(path), w) for w in warn)
        versions.add(version)
        states.append(st)
        per_file.append({
            "file": os.path.basename(path),
            "sha256": digest[:12],
            "version": version,
            "events": st["events"],
            "exports": st["exports"],
            "contexts": count_contexts(st),
            "bytes": byte_len(encode(st)),
        })

    if versions - {VERSION}:
        print("  [!!] bilinmeyen paket sürümü: %s (beklenen v%d)"
              % (", ".join("v%s" % v for v in sorted(versions, key=lambda x: (x is None, x))), VERSION))
        return 1
    if bad_files:
        for b in bad_files:
            print("  [!!] " + b)
        return 1
    if not states:
        print("  [!!] birleştirilecek paket kalmadı")
        return 1

    print("  [OK] %d paket okundu" % len(states))
    for pf in per_file:
        print("       %-34s olay %-6d dışa aktarım %-3d bağlam %-4d %d bayt"
              % (pf["file"][:34], pf["events"], pf["exports"], pf["contexts"], pf["bytes"]))
    for sk in skipped:
        print("  [i] yinelenen paket atlandı: %s (= %s)" % (sk["file"], sk["sameAs"]))
    for w in warnings:
        print("  [!] " + w)

    merged = merge_states(states)
    raw_contexts = count_contexts(merged)
    merged, dropped_rows = filter_min_observations(merged, a.min_observations)
    if dropped_rows:
        print("  [i] gürültü süzgeci: %d animasyon kaydı atıldı (c+r < %d)"
              % (dropped_rows, a.min_observations))
    fit(merged, a.cap, a.size_cap)
    text = encode(merged)

    anim_ids, roles, fx_kinds = load_anim_ids()
    rep = analyse(merged, anim_ids, roles, fx_kinds)

    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")

    if not a.quiet:
        print("-" * 74)
    print("  birleşik: olay %d · dışa aktarım %d · bağlam %d%s · animasyon satırı %d · sınıf satırı %d"
          % (merged["events"], merged["exports"], rep["contexts"],
             (" (girdi %d, budandı)" % raw_contexts) if raw_contexts != rep["contexts"] else "",
             rep["animRows"], rep["clsRows"]))
    print("  dosya   : %s (%d bayt, sınır %d)" % (a.out, rep["bytes"], a.size_cap))
    if a.quiet:
        print("-" * 74)
    if a.quiet:
        pass
    else:
      print("-" * 74)
      print("  EN ÇOK KULLANILAN BAĞLAMLAR")
      for t in rep["topContexts"]:
          print("    %-44s %d gözlem" % (t["ctx"], t["n"]))
      print("  EN GÜÇLÜ ÖNERİLER (skor ↑, gözlem ↑)")
      for d in rep["topSuggestions"]:
          print("    %-40s %-22s skor %.3f (%d seçim / %d ret)"
                % (d["ctx"], d["id"], d["score"], d["chosen"], d["rejected"]))
      if rep["classCorrections"]:
          print("  SINIF DÜZELTMELERİ (kullanıcı asistanı neye çevirdi)")
          for d in rep["classCorrections"]:
              print("    %-44s → %-14s %d" % (d["ctx"], d["cls"], d["n"]))
      if rep["rejectedHeavy"]:
          print("  [!] TUTMAYAN ÖNERİLER (ret > seçim, n ≥ 3) — listeden düşürülebilir")
          for d in rep["rejectedHeavy"]:
              print("    %-40s %-22s %d seçim / %d ret"
                    % (d["ctx"], d["id"], d["chosen"], d["rejected"]))

    problems = []
    if rep["animRows"] == 0 and rep["clsRows"] == 0:
        problems.append("birleşik dosya BOŞ: bütün kayıtlar süzgeç/budama ile atıldı — "
                        "bu dosyayı model güncellemesinde KULLANMA")
    if rep["unknownAnimIds"]:
        problems.append("anim-library.json'da olmayan id'ler: " + ", ".join(rep["unknownAnimIds"][:8]))
    if rep["unknownClasses"]:
        problems.append("14 sınıf listesinde olmayan sınıf: " + ", ".join(rep["unknownClasses"][:8]))
    if rep["unknownStyles"]:
        problems.append("bilinmeyen stil: " + ", ".join(rep["unknownStyles"][:8]))
    if rep["unknownRoles"]:
        problems.append("anim-library.json rollerinde olmayan rol: " + ", ".join(rep["unknownRoles"][:8]))
    if rep["badCtx"]:
        problems.append("bağlam 4 parçalı değil: " + ", ".join(rep["badCtx"][:5]))
    if rep["suspectProto"]:
        problems.append("__prototip__ benzeri token (JS'te prototipi bozar, ayıklanmalı): "
                        + ", ".join(rep["suspectProto"][:5]))
    for p in problems:
        print("  [!] " + p)
    if warnings or problems:
        print("  [i] bu satırlar birleştirmeyi ENGELLEMEZ; paket eski/yeni sürümden gelmiş olabilir")

    if a.priors:
        pd_dir = os.path.dirname(os.path.abspath(a.priors))
        if pd_dir:
            os.makedirs(pd_dir, exist_ok=True)
        with open(a.priors, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(priors_doc(merged), fh, ensure_ascii=False, sort_keys=True, indent=1)
            fh.write("\n")
        print("  [OK] önsel tablo: %s" % a.priors)
    if a.report:
        doc = {
            "format": "ei-merge-report",
            "version": 1,
            "packages": per_file,
            "skippedDuplicates": skipped,
            "warnings": warnings,
            "merged": dict(rep, inputContexts=raw_contexts, droppedRows=dropped_rows,
                           cap=a.cap, sizeCap=a.size_cap, bytesLimitOk=rep["bytes"] <= a.size_cap),
        }
        with open(a.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, sort_keys=True, indent=1)
            fh.write("\n")
        print("  [OK] rapor: %s" % a.report)

    print("-" * 74)
    if problems:
        print("SONUÇ: TAMAM (uyarılarla) — birleşik dosya yazıldı: %s" % a.out)
        return 2
    print("SONUÇ: GEÇTİ — %d paket birleşti, %d bağlam, %d olay → %s"
          % (len(states), rep["contexts"], merged["events"], a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
