#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyImport Asistan — ÖZELLİK SPEC ÜRETİCİ (A1)

Tek doğruluk kaynağı: spec/features.json
Çalışma zamanları (Python / JS / Lua) bu spec'i OKUR — özellik tanımı koda gömülmez.
Böylece özellik eklemek/çıkarmak üç dilde aynı anda ve hatasız olur.

Kullanım:  python tools/build_features.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "spec", "features.json")

SPEC_VERSION = "ei-feat-1"

# ---------------------------------------------------------------------------
# 1) AD TOKEN SÖZLÜĞÜ (grup A) — sıra sabittir, indeks = ağırlık indeksi
# ---------------------------------------------------------------------------
NAME_TOKENS = [
    # yapısal roller
    "button", "btn", "buton", "icon", "close", "exit", "play", "start", "settings",
    "option", "menu", "back", "next", "prev", "tab", "nav", "footer", "header",
    "panel", "bg", "background", "overlay", "modal", "popup", "dialog", "card",
    "slot", "item", "inventory", "bag", "shop", "list", "grid", "scroll", "content",
    "container", "wrapper", "divider", "frame", "label", "text", "title", "desc",
    "value", "count", "timer", "tooltip", "badge", "avatar", "profile",
    # oyun içi
    "bar", "hp", "health", "mana", "energy", "xp", "level", "coin", "gem", "gold",
    "progress", "fill", "loader", "slider", "toggle", "check", "reward", "currency",
    # efekt / doku (FX tespiti — Figma effects[] YERİNE buradan)
    "glow", "ray", "rays", "shine", "shining", "sparkle", "sparkles", "star", "stars",
    "twinkle", "particle", "flare", "bloom", "vignette", "noise", "grain", "dust",
    "smoke", "fog", "ring", "pulse", "aura", "beam", "streak", "gloss", "shimmer",
    "glint", "blur", "halo", "neon", "emission", "energy2", "magic", "fx", "effect",
    # stud / doku
    "stud", "studs", "brick", "civi", "civili", "texture", "pattern",
    # Türkçe
    "isik", "parlama", "parilti", "huzme", "toz", "duman", "halka", "efekt",
]

# ---------------------------------------------------------------------------
# 2) ONE-HOT / BUCKET SÖZLÜKLERİ
# ---------------------------------------------------------------------------
CLASSES = ["Frame", "ImageLabel", "ImageButton", "TextLabel", "TextButton", "TextBox",
           "ScrollingFrame", "CanvasGroup", "ViewportFrame", "VideoFrame", "Path2D",
           "InputActionLabel"]

STROKE_ALIGN = ["INSIDE", "CENTER", "OUTSIDE"]
STROKE_JOIN = ["MITER", "BEVEL", "ROUND"]
GRADIENT_TYPE = ["LINEAR", "RADIAL", "ANGULAR", "DIAMOND"]
ALIGN_H = ["LEFT", "CENTER", "RIGHT"]
ALIGN_V = ["TOP", "CENTER", "BOTTOM"]
LAYOUT_MODE = ["NONE", "HORIZONTAL", "VERTICAL", "GRID"]
BLEND_FX = ["SCREEN", "ADD", "LINEAR_DODGE", "COLOR_DODGE", "LIGHTEN",
            "PLUS_LIGHTER", "PLUS_DARKER"]
FX_KINDS = ["glow", "rays", "sparkle", "shine", "vignette", "noise", "dust", "ring",
            "aura", "beam", "gloss", "bubble", "star", "flare", "smoke", "gradient_overlay"]
PALETTE_BUCKETS = ["red", "orange", "yellow", "green", "cyan", "blue", "purple",
                   "pink", "brown", "gray", "white", "black"]

STROKE_W_EDGES = [0, 1, 3, 6, 10]      # 6 kova: 0, (0,1], (1,3], (3,6], (6,10], 10+
RADIUS_EDGES = [0, 4, 12, 28, 64]      # 6 kova
ASPECT_EDGES = [0.25, 0.5, 0.8, 1.25, 2, 4, 10]   # 8 kova
AREA_EDGES = [0.0002, 0.001, 0.005, 0.02, 0.08, 0.3]  # 7 kova
CORNER_REGIONS = ["tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br"]
DEPTH_BUCKETS = [1, 2, 3, 5, 8]        # 6 kova

# ---------------------------------------------------------------------------
# 3) ÖZELLİK LİSTESİ
# ---------------------------------------------------------------------------
F = []


def num(name, grp, src, norm="id", **kw):
    F.append(dict(k="num", n=name, g=grp, src=src, norm=norm, **kw))


def flag(name, grp, src):
    F.append(dict(k="bool", n=name, g=grp, src=src))


def onehot(name, grp, src, values):
    F.append(dict(k="onehot", n=name, g=grp, src=src, values=values))


def bucket(name, grp, src, edges):
    F.append(dict(k="bucket", n=name, g=grp, src=src, edges=edges))


def token(name, grp, src, t):
    F.append(dict(k="token", n=name, g=grp, src=src, t=t))


# ---- GRUP A: Ad (isim) -----------------------------------------------------
for t in NAME_TOKENS:
    token("tok_%s" % t, "A", "nameTokens", t)
flag("name_hasUnderscoreTag", "A", "hasUnderscoreTag")
flag("name_hasDigit", "A", "nameHasDigit")
flag("name_isCamel", "A", "isCamel")
flag("name_allUpper", "A", "nameAllUpper")
flag("name_empty", "A", "nameEmpty")
num("name_wordCount", "A", "nameWords", "div", d=8.0)
num("name_charLen", "A", "nameLen", "div", d=32.0)

# ---- GRUP B: Geometri — mutlak ---------------------------------------------
num("geo_w_ratio", "B", "w", "div", d="docW")
num("geo_h_ratio", "B", "h", "div", d="docH")
num("geo_area_log", "B", "area", "log", lo=-6.0, hi=6.0)
num("geo_aspect_log", "B", "aspect", "log", lo=-3.0, hi=3.0)
num("geo_minDim_ratio", "B", "minDim", "div", d="docMin")
num("geo_maxDim_ratio", "B", "maxDim", "div", d="docMax")
num("geo_cx", "B", "cx", "clamp01")
num("geo_cy", "B", "cy", "clamp01")
num("geo_distCenter", "B", "distCenter", "clamp01")
num("geo_edgeTop", "B", "edgeTop", "clamp01")
num("geo_edgeBottom", "B", "edgeBottom", "clamp01")
num("geo_edgeLeft", "B", "edgeLeft", "clamp01")
num("geo_edgeRight", "B", "edgeRight", "clamp01")
bucket("geo_aspect_bucket", "B", "aspect", ASPECT_EDGES)
bucket("geo_area_bucket", "B", "areaRatio", AREA_EDGES)
onehot("geo_cornerRegion", "B", "cornerRegion", CORNER_REGIONS)
num("geo_rot", "B", "rot", "div", d=180.0)

# ---- GRUP C: Geometri — bağlamsal (KARŞILAŞTIRMALI) ------------------------
num("ctx_cluster_rank", "C", "clusterRank", "div", d=10.0)
num("ctx_cluster_count", "C", "clusterCount", "div", d=10.0)
flag("ctx_cluster_singleton", "C", "clusterSingleton")
num("ctx_cluster_w_ratio", "C", "clusterW", "div", d="docW")
num("ctx_cluster_h_ratio", "C", "clusterH", "div", d="docH")
num("ctx_cluster_aspect_log", "C", "clusterAspect", "log", lo=-3.0, hi=3.0)
num("ctx_w_over_parentW", "C", "w", "divlog", d="parentW", lo=-4.0, hi=4.0)
num("ctx_h_over_parentH", "C", "h", "divlog", d="parentH", lo=-4.0, hi=4.0)
num("ctx_area_over_parent", "C", "area", "divlog", d="parentArea", lo=-6.0, hi=6.0)
num("ctx_w_over_sibMean", "C", "w", "divlog", d="sibMeanW", lo=-4.0, hi=4.0)
num("ctx_h_over_sibMean", "C", "h", "divlog", d="sibMeanH", lo=-4.0, hi=4.0)
num("ctx_w_over_maxW", "C", "w", "div", d="maxW")
num("ctx_h_over_maxH", "C", "h", "div", d="maxH")
num("ctx_sizeRank", "C", "sizeRank", "clamp01")
num("ctx_sizePercentile", "C", "sizePercentile", "clamp01")
num("ctx_nSameSize", "C", "nSameSize", "div", d=10.0)
num("ctx_sibSizeVar", "C", "sibSizeVar", "clamp01")
flag("ctx_alignedX", "C", "alignedX")
flag("ctx_alignedY", "C", "alignedY")
num("ctx_depth", "C", "depth", "div", d=8.0)
bucket("ctx_depth_bucket", "C", "depth", DEPTH_BUCKETS)
num("ctx_depth_ratio", "C", "depth", "div", d="maxDepth")

# ---- GRUP D: Dolgu & renk --------------------------------------------------
num("fill_n", "D", "nFills", "div", d=5.0)
flag("fill_hasSolid", "D", "hasSolid")
flag("fill_hasGradient", "D", "hasGradient")
flag("fill_hasImage", "D", "hasImage")
flag("fill_transparent", "D", "isTransparentFill")
num("fill_opacity", "D", "fillOpacity", "clamp01")
num("fill_alpha", "D", "fillAlpha", "clamp01")
num("fill_hue", "D", "fillH", "div", d=360.0)
num("fill_sat", "D", "fillS", "clamp01")
num("fill_val", "D", "fillV", "clamp01")
flag("fill_isDark", "D", "fillIsDark")
flag("fill_isNeon", "D", "fillIsNeon")
onehot("fill_paletteBucket", "D", "paletteBucket", PALETTE_BUCKETS)
num("grad_stops", "D", "gradStops", "div", d=6.0)
onehot("grad_type", "D", "gradType", GRADIENT_TYPE)
num("grad_angle_bucket", "D", "gradAngleBucket", "div", d=8.0)
num("color_nDistinct", "D", "nDistinctColors", "div", d=12.0)
flag("color_strokeDarker", "D", "strokeDarkerThanFill")
num("color_contrast", "D", "contrastFS", "clamp01")
flag("color_isMonochrome", "D", "isMonochrome")

# ---- GRUP E: Kontur (KALINLIK) & köşe --------------------------------------
flag("stroke_has", "E", "hasStroke")
num("stroke_w_log", "E", "strokeW", "log", lo=-2.0, hi=3.0)
bucket("stroke_w_bucket", "E", "strokeW", STROKE_W_EDGES)
num("stroke_w_over_minDim", "E", "strokeW", "divlog", d="minDim", lo=-5.0, hi=2.0)
onehot("stroke_align", "E", "strokeAlign", STROKE_ALIGN)
onehot("stroke_join", "E", "strokeJoin", STROKE_JOIN)
flag("stroke_hasDash", "E", "hasDash")
flag("stroke_perSideDiff", "E", "strokePerSideDiff")
num("stroke_sat", "E", "strokeS", "clamp01")
num("stroke_val", "E", "strokeV", "clamp01")
num("stroke_opacity", "E", "strokeOpacity", "clamp01")
num("corner_r_log", "E", "r", "log", lo=-2.0, hi=3.0)
bucket("corner_r_bucket", "E", "r", RADIUS_EDGES)
num("corner_r_over_minDim", "E", "r", "div", d="minDim")
flag("corner_perSideDiff", "E", "rPerSideDiff")
flag("corner_isFull", "E", "isFullRadius")
flag("shape_isPill", "E", "isPill")
flag("shape_isCircle", "E", "isCircle")
flag("stroke_and_radius", "E", "strokeAndRadius")
num("shape_borderRatio", "E", "borderRatio", "clamp01")

# ---- GRUP F: Metin ---------------------------------------------------------
flag("text_isText", "F", "isText")
num("text_len", "F", "textLen", "div", d=64.0)
num("text_words", "F", "textWords", "div", d=8.0)
flag("text_hasDigit", "F", "textHasDigit")
flag("text_isNumeric", "F", "textIsNumeric")
flag("text_allUpper", "F", "textAllUpper")
num("text_fontSize_ratio", "F", "fontSize", "divlog", d="docH", lo=-4.0, hi=1.0)
num("text_fontWeight", "F", "fontWeight", "div", d=900.0)
flag("text_italic", "F", "italic")
onehot("text_alignH", "F", "alignH", ALIGN_H)
onehot("text_alignV", "F", "alignV", ALIGN_V)
flag("text_wrap", "F", "wrap")
num("text_nLines", "F", "nLines", "div", d=5.0)
num("text_val", "F", "textV", "clamp01")
num("text_sat", "F", "textS", "clamp01")
num("text_density", "F", "textDensity", "clamp01")

# ---- GRUP G: Ağaç & düzen --------------------------------------------------
num("tree_nChildren", "G", "nChildren", "log1p")
flag("tree_hasChildren", "G", "hasChildren")
num("tree_nTextChildren", "G", "nTextChildren", "log1p")
num("tree_nImageChildren", "G", "nImageChildren", "log1p")
num("tree_nFrameChildren", "G", "nFrameChildren", "log1p")
flag("tree_isLeaf", "G", "isLeaf")
flag("tree_isRoot", "G", "isRoot")
num("tree_siblingIndex", "G", "siblingIndex", "div", d="nSiblings")
flag("tree_isFirstChild", "G", "isFirstChild")
flag("tree_isLastChild", "G", "isLastChild")
flag("tree_clips", "G", "clips")
flag("tree_hasScroll", "G", "hasScroll")
onehot("layout_mode", "G", "layoutMode", LAYOUT_MODE)
num("layout_gap", "G", "gap", "div", d="docMin")
num("layout_padAvg", "G", "padAvg", "div", d="docMin")
num("tree_childSizeVar", "G", "childSizeVar", "clamp01")

# ---- GRUP H: Efektler (Figma effects[] — sadece DROP_SHADOW karşılığı var) --
num("fx_nShadows", "H", "nShadows", "log1p")
num("fx_shadowOffsetX", "H", "shadowOffsetX", "div", d="minDim")
num("fx_shadowOffsetY", "H", "shadowOffsetY", "div", d="minDim")
num("fx_shadowBlur", "H", "shadowBlur", "div", d="minDim")
num("fx_shadowSpread", "H", "shadowSpread", "div", d="minDim")
num("fx_shadowAlpha", "H", "shadowAlpha", "clamp01")
flag("fx_shadowIsMulti", "H", "shadowIsMulti")
flag("fx_hasInnerShadow", "H", "hasInnerShadow")
flag("fx_hasLayerBlur", "H", "hasLayerBlur")
flag("fx_hasBgBlur", "H", "hasBgBlur")
num("fx_blurRadius", "H", "blurRadius", "div", d="minDim")
flag("fx_hasGlowPattern", "H", "hasGlowPattern")
num("fx_nGlow", "H", "nGlow", "log1p")
flag("fx_hasAnyEffect", "H", "hasAnyEffect")
num("fx_opacity", "H", "opacity", "clamp01")

# ---- GRUP I: FX & doku (Figma effects[] DEĞİL — image + frame kanalları) ---
flag("img_hasImageFill", "I", "hasImageFill")
flag("img_aspectMatch", "I", "imageAspectMatch")
flag("img_isVectorKind", "I", "isVectorKind")
flag("img_tile", "I", "imageTile")
num("img_reuse", "I", "imageReuse", "div", d=10.0)
flag("img_largerThanParent", "I", "imageLargerParent")
flag("d_isFx", "I", "isFx")
onehot("d_fxKind", "I", "fxKind", FX_KINDS)
onehot("d_blendFx", "I", "blendMode", BLEND_FX)
flag("d_isShineFrame", "I", "isShineFrame")
flag("d_isDarkerUnderlay", "I", "isDarkerUnderlay")
flag("d_textureLike", "I", "textureLike")
flag("d_hasStudToken", "I", "hasStudToken")

# ---- GRUP J: Stil (GUI düzeyi — her öğeye kopyalanır) ----------------------
flag("sty_stud", "J", "styleStud")
flag("sty_anime", "J", "styleAnime")
flag("sty_cartoon", "J", "styleCartoon")
flag("sty_belirsiz", "J", "styleBelirsiz")
num("sty_conf", "J", "styleConf", "clamp01")
num("sty_darkness", "J", "darknessIndex", "clamp01")
num("sty_mutedBase", "J", "mutedBaseRate", "clamp01")
num("sty_hueDiversity", "J", "hueDiversity", "clamp01")
num("sty_accentPop", "J", "accentPopRate", "clamp01")
num("sty_effectDensity", "J", "effectDensity", "clamp01")
num("sty_gradientRate", "J", "gradientRate", "clamp01")
num("sty_reuseRate", "J", "reuseRate", "clamp01")
num("sty_imageDriven", "J", "imageDrivenRate", "clamp01")
num("sty_darkerUnderlayRate", "J", "darkerUnderlayRate", "clamp01")
num("sty_shineFrameRate", "J", "shineFrameRate", "clamp01")

# ---- GRUP K: Ebeveyn bağlamı -----------------------------------------------
onehot("par_cls", "K", "parentCls", CLASSES)
num("par_clusterRank", "K", "parentClusterRank", "div", d=10.0)
flag("par_isRoot", "K", "parentIsRoot")
num("par_depth", "K", "parentDepth", "div", d=8.0)
flag("par_hasScroll", "K", "parentHasScroll")
num("par_w_ratio", "K", "parentW", "div", d="docW")
num("par_h_ratio", "K", "parentH", "div", d="docH")

# ---------------------------------------------------------------------------
# 4) ÇIKTI
# ---------------------------------------------------------------------------
def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    spec = {
        "format": "ei-features",
        "version": SPEC_VERSION,
        "generatedBy": "tools/build_features.py",
        "groups": {
            "A": "Ad / isim tokenları",
            "B": "Geometri — mutlak",
            "C": "Geometri — bağlamsal & karşılaştırmalı",
            "D": "Dolgu & renk",
            "E": "Kontur (kalınlık) & köşe",
            "F": "Metin",
            "G": "Ağaç & düzen",
            "H": "Efektler (drop shadow / blur)",
            "I": "FX & doku (image + frame kanalları)",
            "J": "Stil (GUI düzeyi)",
            "K": "Ebeveyn bağlamı",
        },
        "normOps": ["id", "clamp01", "log", "log1p", "div", "divlog"],
        "kindOps": ["num", "bool", "onehot", "bucket", "token"],
        "features": F,
    }

    # çıktı uzunluğunu hesapla
    n = 0
    index = []
    for f in F:
        if f["k"] == "num" or f["k"] == "bool" or f["k"] == "token":
            cnt = 1
        elif f["k"] == "onehot":
            cnt = len(f["values"])
        else:
            cnt = len(f["edges"]) + 1
        index.append({"n": f["n"], "g": f["g"], "k": f["k"], "offset": n, "count": cnt})
        n += cnt

    spec["dim"] = n
    spec["index"] = index

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)

    by = {}
    for f in F:
        c = 1
        if f["k"] == "onehot":
            c = len(f["values"])
        elif f["k"] == "bucket":
            c = len(f["edges"]) + 1
        by[f["g"]] = by.get(f["g"], 0) + c

    print("spec/features.json yazildi")
    print("  tanim sayisi : %d" % len(F))
    print("  VEKTOR BOYU  : %d" % n)
    for g in sorted(by):
        print("    %s : %4d" % (g, by[g]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
