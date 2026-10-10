#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3 ÖĞRETMENİ — Studio'nun sınıf kararının Python karşılığı

Neden var: Model, "doğru cevabı" bilmeden öğrenemez. Elimizdeki tek güvenilir doğru cevap
**mevcut kural motoru**dur (Studio eklentisinin `decideClass` + `parseLayerTags` fonksiyonları).
Bu betik o mantığı Python'a BİREBİR taşır; böylece:

  ham Figma export'u  ──▶  RAW (ei-raw.js)  ──▶  özellik vektörü (379)
                                                     │
                          etiket (bu betik) ─────────┘   ──▶  samples.jsonl  ──▶  train_class.py

**Birebirlik garantisi:** `tools/verify_teacher.py` aynı katmanları hem bu Python kodundan hem de
Studio eklentisinin gerçek Lua kodundan (fengari içinde) geçirir ve **%100 aynı** sonucu arar.
Bu test geçmeden model eğitilmez.

Dil tuzağı (kritik): Lua'nın `string.lower`'ı yalnızca ASCII'yi küçültür; Python'un `str.lower`'ı
Unicode'u da küçültür (İ → i̇). Bu yüzden burada **ASCII-only lower** kullanılır ve Türkçe
İ/ı harfleri Lua'daki bayt düzeyi gsub ile aynı şekilde ele alınır.

Kullanım:
    python3 rules_teacher.py ../../datasets/... .json     # katman kararlarını döker
    from rules_teacher import classify                    # (clean_name, cls)
"""

import json
import re
import sys

# ---------------------------------------------------------------------------
# Lua ile birebir eşleşen sabitler
# ---------------------------------------------------------------------------

KNOWN_SUFFIX = {
    "scrollingframe", "viewportframe", "canvasgroup", "textbutton", "textlabel",
    "imagebutton", "imagelabel", "scrollx", "scrolly", "scroll", "textbox",
    "button", "btn", "canvas", "aspect", "hover", "clicked", "input", "image",
    "frame", "lock", "ignore", "exclude", "uilist", "uigrid", "gray", "vpf",
    "box", "keep", "nodim", "viewport", "videoframe", "video",
}

BUTTON_WORDS = {"button", "btn", "buton"}

CLASS_WORDS = [
    "imagebutton", "imagelabel", "textbutton", "textlabel", "textbox",
    "scrollingframe", "viewportframe", "canvasgroup", "videoframe",
]

FORCE_CLASS_ORDER = [
    ("imagebutton", "ImageButton"),
    ("imagelabel", "ImageLabel"),
    ("textbutton", "TextButton"),
    ("textlabel", "TextLabel"),
    ("scrollingframe", "ScrollingFrame"),
    ("canvasgroup", "CanvasGroup"),
    ("viewportframe", "ViewportFrame"),
    ("textbox", "TextBox"),
    ("videoframe", "VideoFrame"),
    ("frame", "Frame"),
]

_RE_TAG_WORD = re.compile(r"_([A-Za-z]+)")
_RE_CAMEL_SPLIT = re.compile(r"([a-z])([A-Z])")
_RE_WORDS = re.compile(r"[A-Za-z]+")
_RE_TRIM = re.compile(r"^\s*(.*?)\s*$")


def ascii_lower(s):
    """Lua `string.lower` ile aynı: yalnızca A-Z küçülür (Unicode'a dokunulmaz)."""
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in s)


def name_says_button(raw_name):
    """Lua `nameSaysButton` birebir karşılığı."""
    spaced = _RE_CAMEL_SPLIT.sub(r"\1 \2", str(raw_name if raw_name is not None else ""))
    for w in _RE_WORDS.findall(ascii_lower(spaced)):
        if w in BUTTON_WORDS:
            return True
        if len(w) > 6 and w[-6:] == "button":
            return True
        if len(w) > 4 and w[-3:] == "btn":
            return True
    return False


def parse_layer_tags(raw_name):
    """Lua `parseLayerTags` birebir karşılığı → (clean_name, tags)."""
    name = str(raw_name if raw_name is not None else "Layer")
    lower = ascii_lower(name)

    tok = {}
    for w in _RE_TAG_WORD.findall(lower):
        tok[w] = True

    # Sınıf adı adın İÇİNDE doğrudan geçiyorsa (alt çizgi olsa da olmasa da) o sınıf seçilir.
    # Türkçe İ/ı harfleri i sayılır; bayt düzeyi gsub sırası Lua ile aynı tutulur.
    flat = lower.replace("\u0130", "i").replace("\u0131", "i").replace("i\u0307", "i")
    for w in CLASS_WORDS:
        if w in flat:
            tok[w] = True

    force_class = None
    for word, cls in FORCE_CLASS_ORDER:
        if tok.get(word):
            force_class = cls
            break

    tags = {
        "isButton": bool(tok.get("button") or tok.get("btn")),
        "isViewport": bool(tok.get("viewport") or tok.get("viewportframe") or tok.get("vpf")),
        "forceClass": force_class,
        "isNameButton": name_says_button(name),
        "isVideo": bool(tok.get("video") or tok.get("videoframe")),
        "isScroll": bool(tok.get("scroll") or tok.get("scrollx") or tok.get("scrolly") or tok.get("scrollingframe")),
        "isScrollX": bool(tok.get("scrollx")),
        "isScrollY": bool(tok.get("scrolly")),
        "isCanvas": bool(tok.get("canvas") or tok.get("canvasgroup")),
        "isAspect": bool(tok.get("aspect")),
        "isHover": bool(tok.get("hover")),
        "isClicked": bool(tok.get("clicked")),
        "isInput": bool(tok.get("input") or tok.get("textbox") or tok.get("box")),
    }

    clean = re.sub(r"^#", "", name)
    clean = re.sub(r"^img:", "", clean)
    clean = _RE_TAG_WORD.sub(
        lambda m: "" if ascii_lower(m.group(1)) in KNOWN_SUFFIX else m.group(0), clean)
    clean = _RE_TRIM.sub(r"\1", clean)
    if clean == "":
        clean = "Element"
    return clean, tags


def decide_class(item, tags):
    """Lua `decideClass` birebir karşılığı → sınıf adı."""
    kind = item.get("kind")
    cls = "Frame"

    if kind == "text":
        if tags["isInput"]:
            cls = "TextBox"
        elif tags["isButton"]:
            cls = "TextButton"
        else:
            cls = "TextLabel"
    elif item.get("image"):
        cls = "ImageButton" if (tags["isButton"] or tags["isNameButton"]) else "ImageLabel"
    elif tags["isScroll"]:
        cls = "ScrollingFrame"
    elif item.get("scroll") and item["scroll"] != "NONE":
        cls = "ScrollingFrame"
    elif tags["isVideo"]:
        cls = "VideoFrame"
    elif tags["isViewport"]:
        cls = "ViewportFrame"
    elif tags["isCanvas"]:
        cls = "CanvasGroup"
    elif tags["isButton"]:
        cls = "TextButton"

    if tags["forceClass"]:
        fc = tags["forceClass"]
        text_ok = fc in ("TextLabel", "TextButton", "TextBox")
        img_ok = fc in ("ImageLabel", "ImageButton")
        frame_ok = fc in ("ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame", "Frame")
        if ((kind == "text" and text_ok)
                or (item.get("image") and img_ok)
                or (not item.get("image") and kind != "text" and frame_ok)):
            cls = fc
    return cls


def classify(item):
    """Kısayol: (temiz_ad, sınıf)."""
    clean, tags = parse_layer_tags(item.get("name"))
    return clean, decide_class(item, tags)


# ---------------------------------------------------------------------------
# CLI — bir export dökümanındaki tüm katmanların öğretmen kararını döker
# ---------------------------------------------------------------------------
def _walk(item, path, out):
    clean, cls = classify(item)
    out.append((path, str(item.get("name") or ""), item.get("kind"), cls, clean))
    for i, ch in enumerate(item.get("children") or []):
        _walk(ch, path + "." + str(i), out)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 1
    total = 0
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        rows = []
        _walk(doc["root"], "0", rows)
        print("=" * 74)
        print("%s — %s (%d katman)" % (path, doc.get("name"), len(rows)))
        print("=" * 74)
        for p, raw, kind, cls, clean in rows:
            print("  %-10s %-28s %-7s -> %-14s  %s" % (p, raw[:28], kind, cls, clean))
        total += len(rows)
    print("\nToplam %d katman." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
