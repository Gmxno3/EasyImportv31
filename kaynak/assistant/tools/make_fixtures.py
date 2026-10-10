#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Determinizm testi için RAW düğüm örnekleri üretir  [A1]

RAW = düğümden çıkarılmış, özellik hesabına hazır sözlük.
Gerçek RAW çıkarıcı (Figma JSON -> RAW) A2'de gelecek; burada amaç
DEĞERLENDİRİCİNİN (ei_features) üç dilde aynı sonucu verdiğini kanıtlamak.

Çıktı: datasets/fixtures/raw-nodes.json ve .lua (aynı veri, üç dil okusun diye)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import luatable  # noqa: E402

FIX_DIR = os.path.join(ROOT, "datasets", "fixtures")

# ---------------------------------------------------------------------------
# TÜM RAW ANAHTARLARI İÇİN VARSAYILANLAR
# ---------------------------------------------------------------------------
DEFAULTS = {
    # tuval
    "docW": 1920.0, "docH": 1080.0, "docMin": 1080.0, "docMax": 1920.0,
    # kutu
    "x": 0.0, "y": 0.0, "w": 100.0, "h": 100.0, "rot": 0.0,
    # türetilmiş geometri
    "area": 10000.0, "areaRatio": 0.0048, "aspect": 1.0, "minDim": 100.0, "maxDim": 100.0,
    "cx": 0.5, "cy": 0.5, "distCenter": 0.5,
    "edgeTop": 0.09, "edgeBottom": 0.09, "edgeLeft": 0.05, "edgeRight": 0.05,
    "cornerRegion": "mc",
    # boyut kümesi
    "clusterRank": 0.0, "clusterCount": 1.0, "clusterSingleton": False,
    "clusterW": 100.0, "clusterH": 100.0, "clusterAspect": 1.0,
    # bağlam
    "parentW": 1920.0, "parentH": 1080.0, "parentArea": 2073600.0,
    "sibMeanW": 100.0, "sibMeanH": 100.0, "maxW": 1920.0, "maxH": 1080.0,
    "sizeRank": 0.5, "sizePercentile": 0.5, "nSameSize": 1.0, "sibSizeVar": 0.0,
    "alignedX": False, "alignedY": False,
    "depth": 1.0, "maxDepth": 3.0,
    # ağaç
    "nChildren": 0.0, "hasChildren": False,
    "nTextChildren": 0.0, "nImageChildren": 0.0, "nFrameChildren": 0.0,
    "isLeaf": True, "isRoot": False,
    "siblingIndex": 0.0, "nSiblings": 1.0, "isFirstChild": True, "isLastChild": True,
    "clips": False, "hasScroll": False, "childSizeVar": 0.0,
    # dolgu & renk
    "nFills": 1.0, "hasSolid": True, "hasGradient": False, "hasImage": False,
    "isTransparentFill": False,
    "fillOpacity": 1.0, "fillAlpha": 1.0, "fillH": 210.0, "fillS": 0.6, "fillV": 0.7,
    "fillIsDark": False, "fillIsNeon": False, "paletteBucket": "blue",
    "gradStops": 0.0, "gradType": "LINEAR", "gradAngleBucket": 0.0,
    "nDistinctColors": 3.0, "strokeDarkerThanFill": False, "contrastFS": 0.2,
    "isMonochrome": False,
    # kontur
    "hasStroke": False, "strokeW": 0.0, "strokeAlign": "INSIDE", "strokeJoin": "MITER",
    "hasDash": False, "strokePerSideDiff": False,
    "strokeS": 0.0, "strokeV": 0.0, "strokeOpacity": 1.0,
    # köşe / şekil
    "r": 0.0, "rPerSideDiff": False, "isFullRadius": False,
    "isPill": False, "isCircle": False, "strokeAndRadius": False, "borderRatio": 0.0,
    # efektler
    "nShadows": 0.0, "shadowOffsetX": 0.0, "shadowOffsetY": 0.0, "shadowBlur": 0.0,
    "shadowSpread": 0.0, "shadowAlpha": 0.0, "shadowIsMulti": False,
    "hasInnerShadow": False, "hasLayerBlur": False, "hasBgBlur": False,
    "blurRadius": 0.0, "hasGlowPattern": False, "nGlow": 0.0,
    "hasAnyEffect": False, "opacity": 1.0,
    # metin
    "isText": False, "textLen": 0.0, "textWords": 0.0, "textHasDigit": False,
    "textIsNumeric": False, "textAllUpper": False,
    "fontSize": 16.0, "fontWeight": 400.0, "italic": False,
    "alignH": "LEFT", "alignV": "TOP", "wrap": False, "nLines": 1.0,
    "textV": 1.0, "textS": 0.0, "textDensity": 0.0,
    # görsel
    "hasImageFill": False, "imageAspectMatch": False, "isVectorKind": False,
    "imageTile": False, "imageReuse": 1.0, "imageLargerParent": False,
    # fx / doku
    "isFx": False, "fxKind": "glow", "isShineFrame": False, "isDarkerUnderlay": False,
    "textureLike": False, "hasStudToken": False, "blendMode": "NORMAL",
    # stil (GUI düzeyi)
    "styleStud": False, "styleAnime": False, "styleCartoon": False, "styleBelirsiz": True,
    "styleConf": 0.0,
    "darknessIndex": 0.4, "mutedBaseRate": 0.3, "hueDiversity": 0.3, "accentPopRate": 0.1,
    "effectDensity": 0.2, "gradientRate": 0.1, "reuseRate": 0.2, "imageDrivenRate": 0.3,
    "darkerUnderlayRate": 0.0, "shineFrameRate": 0.0,
    # ebeveyn
    "parentCls": "Frame", "parentClusterRank": 0.0, "parentIsRoot": True,
    "parentDepth": 0.0, "parentHasScroll": False,
    # ad
    "nameTokens": {}, "hasUnderscoreTag": False, "nameHasDigit": False,
    "isCamel": False, "nameAllUpper": False, "nameEmpty": True,
    "nameWords": 0.0, "nameLen": 0.0,
    # düzen
    "layoutMode": "NONE", "gap": 0.0, "padAvg": 0.0,
}

CANVAS = {"docW": 1920.0, "docH": 1080.0, "docMin": 1080.0, "docMax": 1920.0}


def geom(w, h, x=0.0, y=0.0, docW=1920.0, docH=1080.0):
    """Kutudan türetilmiş geometriyi hesaplar (aynı formül A2'de de kullanılacak)."""
    area = w * h
    aspect = (w / h) if h > 0 else 20.0
    mn = min(w, h)
    mx = max(w, h)
    cx = (x + w / 2.0) / docW
    cy = (y + h / 2.0) / docH
    dx = cx - 0.5
    dy = cy - 0.5
    return {
        "w": w, "h": h, "x": x, "y": y,
        "area": area, "areaRatio": area / (docW * docH),
        "aspect": aspect, "minDim": mn, "maxDim": mx,
        "cx": cx, "cy": cy,
        "distCenter": (dx * dx + dy * dy) ** 0.5 / 0.7071,
        "edgeTop": max(0.0, 1.0 - y / docH),
        "edgeBottom": max(0.0, 1.0 - (docH - (y + h)) / docH),
        "edgeLeft": max(0.0, 1.0 - x / docW),
        "edgeRight": max(0.0, 1.0 - (docW - (x + w)) / docW),
    }


def corner_region(x, y, w, h, docW=1920.0, docH=1080.0):
    cx = (x + w / 2.0) / docW
    cy = (y + h / 2.0) / docH
    col = "l" if cx < 0.33 else ("r" if cx > 0.67 else "c")
    row = "t" if cy < 0.33 else ("b" if cy > 0.67 else "m")
    return row + col


def node(name, over):
    raw = dict(DEFAULTS)
    raw.update(CANVAS)
    for k, v in over.items():
        raw[k] = v
    # geometri otomatik
    raw.update(geom(raw["w"], raw["h"], raw["x"], raw["y"], raw["docW"], raw["docH"]))
    raw["cornerRegion"] = corner_region(raw["x"], raw["y"], raw["w"], raw["h"],
                                        raw["docW"], raw["docH"])
    raw["minDim"] = min(raw["w"], raw["h"])
    raw["maxDim"] = max(raw["w"], raw["h"])
    raw["borderRatio"] = (2.0 * raw["strokeW"] / raw["minDim"]) if raw["minDim"] > 0 else 0.0
    raw["strokeAndRadius"] = bool(raw["hasStroke"] and raw["r"] > 0)
    raw["isFullRadius"] = bool(raw["r"] >= raw["minDim"] / 2.0 - 0.01) if raw["minDim"] > 0 else False
    raw["isPill"] = bool(raw["isFullRadius"] and raw["minDim"] > 0 and
                         (raw["maxDim"] / raw["minDim"]) > 1.6)
    raw["isCircle"] = bool(raw["isFullRadius"] and abs(raw["aspect"] - 1.0) < 0.05)
    raw["fillIsDark"] = raw["fillV"] < 0.45
    raw["fillIsNeon"] = bool(raw["fillS"] > 0.7 and raw["fillV"] > 0.7)
    raw["hasAnyEffect"] = bool(raw["nShadows"] > 0 or raw["hasInnerShadow"] or
                               raw["hasLayerBlur"] or raw["hasBgBlur"])
    raw["hasChildren"] = raw["nChildren"] > 0
    raw["isLeaf"] = not raw["hasChildren"]
    raw["textDensity"] = (raw["textLen"] / (raw["w"] * raw["h"] / 1000.0)) if raw["w"] * raw["h"] > 0 else 0.0
    raw["nameEmpty"] = (raw["nameLen"] == 0)
    return {"name": name, "raw": raw}


# ---------------------------------------------------------------------------
# SENARYOLAR — gerçek dünyadan tipik katmanlar
# ---------------------------------------------------------------------------
def build():
    N = []

    # 1) Kapama butonu: 64x64, sağ üst, kalın kontur, ikon
    N.append(node("Close_Button", dict(
        w=64, h=64, x=1820, y=36,
        nameTokens={"close": True, "button": True}, nameWords=2, nameLen=12,
        hasUnderscoreTag=True, isCamel=False,
        r=16, hasStroke=True, strokeW=4, strokeAlign="INSIDE", strokeJoin="ROUND",
        strokeS=0.0, strokeV=0.0, fillV=0.85, fillS=0.1, paletteBucket="gray",
        hasImageFill=True, isVectorKind=True, imageAspectMatch=True,
        clusterRank=1, clusterCount=3, clusterW=64, clusterH=64,
        depth=2, parentCls="Frame", parentW=1920, parentH=1080,
        nSiblings=4, siblingIndex=3, isFirstChild=False, isLastChild=True,
    )))

    # 2) Ana buton: 420x96, uzun, içinde metin, kalın kontur
    N.append(node("Play_Button", dict(
        w=420, h=96, x=750, y=880,
        nameTokens={"play": True, "button": True}, nameWords=2, nameLen=11,
        hasUnderscoreTag=True,
        r=24, hasStroke=True, strokeW=5, strokeJoin="ROUND",
        strokeS=0.0, strokeV=0.1, strokeDarkerThanFill=True, contrastFS=0.65,
        fillH=210, fillS=0.8, fillV=0.55, paletteBucket="blue",
        isText=True, textLen=4, textWords=1, textAllUpper=True,
        fontSize=36, fontWeight=800, alignH="CENTER", alignV="CENTER",
        textV=1.0, textS=0.0, nLines=1,
        nShadows=1.0, shadowOffsetX=0, shadowOffsetY=6, shadowBlur=12, shadowAlpha=0.35,
        depth=2, parentCls="Frame", nSiblings=3, siblingIndex=1,
        clusterRank=0, clusterCount=2, clusterW=420, clusterH=96,
    )))

    # 3) Metin etiketi: kontur yok, görsel yok
    N.append(node("Title_Label", dict(
        w=600, h=64, x=660, y=120,
        nameTokens={"title": True, "label": True}, nameWords=2, nameLen=11,
        hasUnderscoreTag=True,
        isText=True, textLen=18, textWords=3, fontSize=48, fontWeight=700,
        alignH="CENTER", alignV="TOP", textV=1.0,
        fillV=1.0, fillS=0.0, paletteBucket="white",
        depth=2, parentCls="Frame", nSiblings=6, siblingIndex=0,
    )))

    # 4) Tam ekran arka plan
    N.append(node("Background", dict(
        w=1920, h=1080, x=0, y=0, isRoot=True,
        nameTokens={"background": True, "bg": True}, nameWords=1, nameLen=10,
        nChildren=12, nTextChildren=4, nImageChildren=5, nFrameChildren=3,
        fillV=0.12, fillS=0.3, fillH=260, paletteBucket="black", fillIsDark=True,
        depth=0, parentCls="Frame", parentIsRoot=True,
        clusterRank=0, clusterCount=1, clusterSingleton=True,
        sizeRank=1.0, sizePercentile=1.0,
        styleAnime=True, styleBelirsiz=False, styleConf=0.86,
        darknessIndex=0.71, mutedBaseRate=0.58, hueDiversity=0.42,
        accentPopRate=0.18, effectDensity=1.1, gradientRate=0.38,
    )))

    # 5) Glow efekt görseli (Figma'da image — effects[] DEĞİL)
    N.append(node("Button_Glow", dict(
        w=520, h=190, x=700, y=830,
        nameTokens={"glow": True, "button": True}, nameWords=2, nameLen=11,
        hasUnderscoreTag=True,
        hasImageFill=True, imageLargerParent=True, isFx=True, fxKind="glow",
        blendMode="SCREEN", fillOpacity=0.45, fillAlpha=0.45,
        fillV=1.0, fillS=0.9, paletteBucket="cyan", fillIsNeon=True,
        depth=3, parentCls="ImageButton", parentW=420, parentH=96,
        styleAnime=True, styleBelirsiz=False, styleConf=0.86,
    )))

    # 6) Shine frame (Frame ile yapılmış efekt)
    N.append(node("Shine", dict(
        w=420, h=96, x=750, y=880,
        nameTokens={"shine": True}, nameWords=1, nameLen=5,
        hasGradient=True, gradType="LINEAR", gradStops=3, gradAngleBucket=3,
        fillOpacity=0.25, fillAlpha=0.25, isTransparentFill=True,
        isFx=True, fxKind="shine", isShineFrame=True,
        depth=3, parentCls="ImageButton", parentW=420, parentH=96,
        styleStud=True, styleBelirsiz=False, styleConf=1.0, shineFrameRate=0.05,
    )))

    # 7) Stud panel (doku, efekt yok)
    N.append(node("Header_Stud_Panel", dict(
        w=1200, h=180, x=360, y=40,
        nameTokens={"header": True, "stud": True, "panel": True}, nameWords=3, nameLen=16,
        hasUnderscoreTag=True, hasStudToken=True,
        hasImageFill=True, imageTile=True, imageReuse=6, textureLike=True,
        r=12, hasStroke=True, strokeW=6, strokeJoin="MITER",
        strokeS=0.0, strokeV=0.15, strokeDarkerThanFill=True,
        fillV=0.55, fillS=0.75, paletteBucket="orange",
        styleStud=True, styleBelirsiz=False, styleConf=1.0,
        reuseRate=0.62, imageDrivenRate=0.71, effectDensity=0.1, gradientRate=0.02,
        darkerUnderlayRate=0.08, shineFrameRate=0.04,
        depth=1, parentCls="Frame",
    )))

    # 8) 3D underlay (alttaki koyu kopya -> Frame kalmalı)
    N.append(node("Button_Shadow_3D", dict(
        w=420, h=96, x=750, y=886,
        nameTokens={"button": True}, nameWords=2, nameLen=14,
        hasUnderscoreTag=True, isDarkerUnderlay=True,
        r=24, fillV=0.28, fillS=0.8, fillH=210, paletteBucket="blue",
        depth=3, parentCls="ImageButton", parentW=420, parentH=96,
        styleStud=True, styleBelirsiz=False, styleConf=1.0, darkerUnderlayRate=0.08,
    )))

    # 9) İlerleme çubuğu (çok uzun, ince)
    N.append(node("HP_Bar_Fill", dict(
        w=640, h=28, x=120, y=60,
        nameTokens={"hp": True, "bar": True, "fill": True}, nameWords=3, nameLen=10,
        hasUnderscoreTag=True,
        r=14, hasGradient=True, gradType="LINEAR", gradStops=2,
        fillH=0, fillS=0.9, fillV=0.85, paletteBucket="red",
        depth=4, parentCls="Frame", parentW=680, parentH=40,
    )))

    # 10) Scroll listesi (çok çocuk)
    N.append(node("Inventory_Scroll", dict(
        w=900, h=700, x=510, y=190,
        nameTokens={"inventory": True, "scroll": True}, nameWords=2, nameLen=16,
        hasUnderscoreTag=True,
        nChildren=48, nTextChildren=24, nImageChildren=24, nFrameChildren=0,
        clips=True, hasScroll=True, layoutMode="GRID", gap=12, padAvg=16,
        childSizeVar=0.05,
        fillV=0.15, fillS=0.2, fillH=250, paletteBucket="black",
        depth=1, parentCls="Frame",
    )))

    # 11) Kart / slot (grid elemanı, aynı boyut çok)
    N.append(node("Item_Slot", dict(
        w=140, h=140, x=520, y=200,
        nameTokens={"item": True, "slot": True}, nameWords=2, nameLen=9,
        hasUnderscoreTag=True,
        r=12, hasStroke=True, strokeW=3, strokeJoin="ROUND", strokeV=0.3,
        fillV=0.22, fillS=0.35, paletteBucket="gray",
        nSameSize=24, clusterRank=0, clusterCount=24, clusterW=140, clusterH=140,
        alignedX=True, alignedY=True, sibSizeVar=0.0,
        depth=3, parentCls="ScrollingFrame", parentHasScroll=True,
        parentW=900, parentH=700, parentClusterRank=0,
    )))

    # 12) Sparkle (çok küçük fx görseli)
    N.append(node("Sparkle_01", dict(
        w=24, h=24, x=880, y=300,
        nameTokens={"sparkle": True}, nameWords=1, nameLen=9,
        hasImageFill=True, isFx=True, fxKind="sparkle", blendMode="ADD",
        fillOpacity=0.9, fillV=1.0, fillS=0.2, paletteBucket="white",
        imageReuse=8, clusterRank=2, clusterCount=8, clusterW=24, clusterH=24,
        depth=4, parentCls="ImageButton", parentW=140, parentH=140,
        styleAnime=True, styleBelirsiz=False, styleConf=0.86,
    )))

    # 13) UÇ DURUM: sıfır boyut, hiçbir şey yok, ad boş
    N.append(node("(isimsiz)", dict(
        w=0.0, h=0.0, x=0.0, y=0.0,
        nFills=0.0, hasSolid=False, fillOpacity=0.0, fillAlpha=0.0,
        fillV=0.0, fillS=0.0, paletteBucket="black",
        nDistinctColors=0.0, nameLen=0, nameWords=0,
    )))

    # 14) UÇ DURUM: aşırı değerler (bölme sıfır, taşma)
    N.append(node("Extreme", dict(
        w=1e7, h=0.001, x=-5000, y=99999,
        nameTokens={"fx": True, "glow": True, "stud": True, "button": True, "text": True},
        nameLen=40, nameWords=8, nameHasDigit=True, isCamel=True, nameAllUpper=True,
        hasUnderscoreTag=True,
        r=1e6, hasStroke=True, strokeW=1e5, strokePerSideDiff=True, hasDash=True,
        strokeAlign="OUTSIDE", strokeJoin="BEVEL",
        nShadows=99, shadowBlur=1e5, shadowOffsetX=-1e4, shadowAlpha=1.0,
        shadowIsMulti=True, hasInnerShadow=True, hasLayerBlur=True, hasBgBlur=True,
        blurRadius=1e5, hasGlowPattern=True, nGlow=12,
        isText=True, textLen=9999, textWords=999, fontSize=1e5, fontWeight=900,
        italic=True, alignH="RIGHT", alignV="BOTTOM", wrap=True, nLines=99,
        nChildren=999, layoutMode="VERTICAL", gap=1e4, padAvg=1e4,
        depth=99, maxDepth=99, nSiblings=0, siblingIndex=0,
        rot=359.5, opacity=0.0,
    )))

    return N


def main():
    os.makedirs(FIX_DIR, exist_ok=True)
    nodes = build()

    jpath = os.path.join(FIX_DIR, "raw-nodes.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(nodes, fh, ensure_ascii=False, indent=1)

    lpath = os.path.join(FIX_DIR, "raw-nodes.lua")
    with open(lpath, "w", encoding="utf-8") as fh:
        fh.write("-- OTOMATİK ÜRETİLDİ — tools/make_fixtures.py\n")
        fh.write("return ")
        fh.write(luatable.dumps(nodes))
        fh.write("\n")

    print("fixture üretildi: %d düğüm" % len(nodes))
    print("  %s" % os.path.relpath(jpath, ROOT))
    print("  %s" % os.path.relpath(lpath, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
