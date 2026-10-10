#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2 — Figma EXPORT ÖRNEKLERİ ÜRETİCİ

A2'nin girdisi, plugin'in gerçekten ürettiği `wispfree v9` dökümanıdır:

    { format:'wispfree', version:9, name, width, height, root: item }

item şekli (figma-plugin-all-in-one/code.js -> walk()):

    { name, kind:'text'|'vector'|'ellipse'|'frame',
      x, y, w, h, rot, opacity,
      text?    : { characters, fontSize, fontFamily, fontWeight, italic,
                   color:{r,g,b}, opacity, align, vAlign, wrap, autoW,
                   gradient?, stroke?, segments?, textCase?, decoration?,
                   shadows?, shadow?, lines? },
      image?   : 'dosya.png'                       (kind:'vector' ya da IMAGE dolgulu)
      fills?   : [ SOLID | GRADIENT | IMAGE ]      (renkler 0..255!)
      stroke?  : { color, opacity, weight },
      strokes? : [...], strokeWeight, strokeAlign,
      shadows? : [...], shadow? : {...},
      scroll?  : 'HORIZONTAL'|'VERTICAL'|'BOTH',
      layout?  : { mode, gap, wrapGap, wrap, pl, pr, pt, pb, primary, counter },
      radius   : sayı | 'full',
      clips    : bool,
      children?: [ item... ] }

Bu betik, A2 çıkarıcısının üç dilde (JS / Lua / Python) aynı sonucu verdiğini
kanıtlamak için kullanılacak girdileri üretir. Elle yazılmış DEĞİLDİR,
determinizm kapısının parçasıdır.

Kullanım:  python tools/make_export_samples.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "datasets", "fixtures", "exports")


# ---------------------------------------------------------------------------
# küçük yardımcılar
# ---------------------------------------------------------------------------
def c(r, g, b):
    """Renkler 0..255 (plugin c255() ile böyle verir)."""
    return {"r": r, "g": g, "b": b}


def solid(rgb, opacity=1.0):
    return {"type": "SOLID", "color": c(*rgb), "opacity": opacity}


def grad(stops, angle=90.0, opacity=1.0):
    """stops: [(pos, (r,g,b))]"""
    return {
        "type": "GRADIENT",
        "angle": angle,
        "opacity": opacity,
        "stops": [{"pos": p, "color": c(*rgb), "opacity": 1.0} for p, rgb in stops],
    }


def grad_radial(stops, angle=0.0, opacity=1.0):
    """Radyal gradyan. code.js GRADIENT_RADIAL -> type 'GRADIENT_OTHER',
    EIRaw bunu gradType='RADIAL' olarak okur (ışıklandırma ekseni)."""
    return {
        "type": "GRADIENT_OTHER",
        "angle": angle,
        "opacity": opacity,
        "stops": [{"pos": p, "color": c(*rgb), "opacity": 1.0} for p, rgb in stops],
    }


def image_fill(scale_mode="FILL", opacity=1.0):
    """Figma `ImagePaint` → export. `scaleMode`: FILL | FIT | CROP | TILE.

    v9 sözleşmesi değişmez: dolgu yalnızca bu üç alanı taşır. Görselin PİKSEL boyutu ve
    döşeme katsayısı (`scalingFactor`) ise **yan kanalda** (`item.ei`) durur — bkz. `img_meta`.
    """
    return {"type": "IMAGE", "scaleMode": scale_mode, "opacity": opacity}


def img_meta(img, scale=None, blend=None):
    """`item.ei` yan kanalı — Figma eklentisinin (code.js) yazdığı ölçülmüş görsel bilgisi.

    Neden gerekli: stud tespitinin "olmazsa olmazı" dokunun BUTON veya HEADER üzerinde
    olması; ama tasarımcı katmanına "stud" yazmasa da doku kendini belli eder — döşeme
    hücresinin boyutundan (kullanıcı: "size ve boyutundan da anlaşılıyor").

        img   : (genişlik, yükseklik) px — Figma `Image.getSizeAsync()`
        scale : TILE modunda `scalingFactor` (görselin orijinal boyutuna göre oran)
        blend : düğümün blend modu (SCREEN/ADD ise "ışık katmanı")

    Ölçüm: hücre px = görsel px × scalingFactor. Figma'da TILE dışındaki modlarda
    `scalingFactor` anlamsızdır (dolayısıyla hücre de yoktur).
    """
    w, h = int(round(img[0])), int(round(img[1]))
    ei = {"imageW": w, "imageH": h}
    if scale is not None:
        cw, chh = int(round(w * scale)), int(round(h * scale))
        ei["sf"] = scale
        ei["tileW"] = cw
        ei["tileH"] = chh
    if blend:
        ei["blendMode"] = blend
    return ei


def shadow(x=0.0, y=4.0, blur=8.0, spread=0.0, rgb=(0, 0, 0), a=0.35):
    return {"x": x, "y": y, "blur": blur, "spread": spread, "color": c(*rgb), "opacity": a}


def frame(name, x, y, w, h, **kw):
    it = {"name": name, "kind": "frame", "x": x, "y": y, "w": w, "h": h,
          "rot": 0, "opacity": 1}
    it.update(kw)
    return it


def text(name, x, y, w, h, chars, size=24, **kw):
    t = {"characters": chars, "fontSize": size, "fontFamily": "GothamSSm",
         "fontWeight": 700, "italic": False, "color": c(255, 255, 255),
         "opacity": 1, "align": "CENTER", "vAlign": "CENTER",
         "wrap": True, "autoW": False}
    t.update(kw.pop("text", {}))
    it = {"name": name, "kind": "text", "x": x, "y": y, "w": w, "h": h,
          "rot": 0, "opacity": 1, "text": t}
    it.update(kw)
    return it


def vector(name, x, y, w, h, img, **kw):
    it = {"name": name, "kind": "vector", "x": x, "y": y, "w": w, "h": h,
          "rot": 0, "opacity": 1, "image": img}
    it.update(kw)
    return it


def rect(name, x, y, w, h, **kw):
    return frame(name, x, y, w, h, **kw)


def doc(name, w, h, root):
    return {"format": "wispfree", "version": 9, "maskMerged": 0,
            "name": name, "width": w, "height": h, "root": root}


# ---------------------------------------------------------------------------
# 1) STUD — kullanıcı tarifi:
#    "stud texture buton ve header'da olmazsa olmazıdır"
#    "birden fazla aynı şeyi kullanmışsa" (aynı image tekrar kullanımı)
#    "aynı rengin kapalısını altta geçirerek 3D görünüm verirler"
#    "çoğu zaman efek yoktur, çok az; en sık shine efekti, Frame ile yapılır"
# ---------------------------------------------------------------------------
def sample_stud():
    # Klasik stud dokusu: kare, kesintisiz (seamless) 64x64 doku; Figma'da %50 ölçekle
    # döşenince hücre 32 px olur → 96 px yüksekliğindeki butonda 3x3 stud görünür.
    STUD_IMG = (64, 64)
    STUD_TILE = img_meta(STUD_IMG, scale=0.5)          # TILE: hücre 32x32
    STUD_FILL = img_meta(STUD_IMG)                     # buton yüzü: tek parça (FILL)
    STUD = "stud_texture.png"
    BTN = "button_stud.png"

    def stud_button(nm, x, y, w, h, label, size=26):
        """Stud buton = 3D alt katman (koyu) + stud dokulu üst katman + yazı."""
        return frame(nm, x, y, w, h, fills=[], radius=12, clips=False, children=[
            rect(nm + "_Shadow", 0, 6, w, h,                     # 3D: aynı hue, daha koyu
                 fills=[solid((92, 44, 20))], radius=12),
            frame(nm + "_Top", 0, 0, w, h - 6,                   # stud dokulu üst yüzey
                  fills=[image_fill("FILL")], radius=12, ei=STUD_FILL,
                  children=[text("Label", 0, 0, w, h - 6, label, size=size,
                                 text={"fontWeight": 900})]),
        ])

    root = frame("ShopPanel", 0, 0, 720, 900,
                 fills=[solid((58, 32, 18))], radius=16, clips=True, children=[
        # header — stud doku OLMASA OLMAZ
        frame("Header", 0, 0, 720, 120, fills=[image_fill("TILE")], radius=16,
              ei=STUD_TILE, clips=True, children=[
            text("Title", 0, 30, 720, 60, "MARKET", size=44,
                 text={"fontWeight": 900, "color": c(255, 240, 210)}),
        ]),
        # header'ın 3D alt gölgesi
        rect("Header_Shadow", 0, 10, 720, 120, fills=[solid((38, 20, 10))], radius=16),
        # shine — kullanıcı: "çoğu zaman shine efektini Frame ile yaparlar"
        frame("Shine", 0, 0, 720, 120, fills=[
            grad([(0.0, (255, 255, 255)), (1.0, (255, 255, 255))], angle=118.0,
                 opacity=0.22)], radius=16, clips=True),
        # stud butonlar — AYNI image tekrar kullanımı
        stud_button("Buy_Button", 40, 160, 300, 96, "SATIN AL"),
        stud_button("Sell_Button", 380, 160, 300, 96, "SAT"),
        stud_button("Back_Button", 40, 280, 300, 96, "GERİ"),
        stud_button("Option_Button", 380, 280, 300, 96, "SEÇENEKLER", size=22),
        # menü — stud doku tekrar kullanımı (aynı dosya!)
        frame("Menu", 40, 400, 640, 420, fills=[image_fill("TILE")], radius=14,
              ei=STUD_TILE,
              clips=True, children=[
            frame("Menu_Inner", 12, 12, 616, 396, fills=[solid((74, 40, 22))],
                  radius=10, clips=True, children=[
                frame("Item_Slot", 20, 20, 180, 180, fills=[solid((96, 54, 28))],
                      radius=8, children=[]),
                frame("Item_Slot", 218, 20, 180, 180, fills=[solid((96, 54, 28))],
                      radius=8, children=[]),
                frame("Item_Slot", 416, 20, 180, 180, fills=[solid((96, 54, 28))],
                      radius=8, children=[]),
                frame("Item_Slot", 20, 216, 180, 160, fills=[solid((96, 54, 28))],
                      radius=8, children=[]),
                frame("Item_Slot", 218, 216, 180, 160, fills=[solid((96, 54, 28))],
                      radius=8, children=[]),
                text("Empty_Text", 416, 260, 180, 40, "BOŞ", size=20,
                     text={"color": c(200, 170, 130)}),
            ]),
        ]),
        # footer
        text("Hint", 0, 840, 720, 40, "Bir şey seç", size=18,
             text={"color": c(190, 160, 120)}),
    ])

    # image dosya adlarını gerçek dedupe anahtarlarıyla değiştir
    _assign_images(root, {"Header": STUD, "Menu": STUD,
                          "Buy_Button_Top": BTN, "Sell_Button_Top": BTN,
                          "Back_Button_Top": BTN, "Option_Button_Top": BTN})
    return doc("StudMarket", 720, 900, root)


# ---------------------------------------------------------------------------
# 1b) STUD — İSİMSİZ VARYANT (yalnızca geometri ve tekrar konuşur)
#
# Neden ayrı örnek: gerçek dosyalarda tasarımcı katmana "stud" YAZMAZ. Kullanıcı:
#   "Stud texture buton ve header'da olmazsa olmazıdır" + "size ve boyutundan da anlaşılıyor"
#   "Texture'si stud olduğundan başka texture kullanılmaz"
# Bu örnekte hiçbir katman adında stud/pattern/brick geçmez; kanıt yalnızca:
#   aynı küçük kare döşeme hücresi (32 px) + buton/header üzerinde + tek doku + 3D alt katman.
# ---------------------------------------------------------------------------
def sample_stud_unnamed():
    STUD_IMG = (64, 64)
    STUD_TILE = img_meta(STUD_IMG, scale=0.5)
    HUE = (108, 76, 40)

    def btn(nm, x, y, w, h, label):
        return frame(nm, x, y, w, h, fills=[], children=[
            rect(nm + "_Alt", 0, 5, w, h, fills=[solid((72, 50, 26))]),   # 3D alt katman
            frame(nm + "_Yuz", 0, 0, w, h - 5, fills=[image_fill("TILE")],
                  ei=STUD_TILE, children=[
                      text("Yazi", 0, 0, w, h - 5, label, size=24,
                           text={"fontWeight": 900, "color": c(250, 236, 214)})]),
        ])

    root = frame("Panel_A", 0, 0, 640, 520, fills=[solid(HUE)], children=[
        frame("Bar_Top", 0, 0, 640, 72, fills=[image_fill("TILE")], ei=STUD_TILE,
              clips=True, children=[
                  text("Baslik", 0, 12, 640, 48, "OYUN", size=34,
                       text={"fontWeight": 900, "color": c(255, 240, 220)}),
              ]),
        # shine — kullanıcı: "en sık shine; shine'ı Frame ile yaparlar"
        frame("Parlaklik", 0, 0, 640, 72, fills=[
            grad([(0.0, (255, 255, 255)), (1.0, (255, 255, 255))], angle=116.0, opacity=0.20)],
            clips=True),
        btn("Btn_1", 36, 108, 268, 150, "BİRİNCİ"),
        btn("Btn_2", 336, 108, 268, 150, "İKİNCİ"),
        btn("Btn_3", 36, 286, 268, 150, "ÜÇÜNCÜ"),
        btn("Btn_4", 336, 286, 268, 150, "DÖRDÜNCÜ"),
        frame("Liste", 36, 452, 568, 48, fills=[image_fill("TILE")], ei=STUD_TILE, clips=True),
    ])
    _assign_images(root, {"Bar_Top": "doku_kare.png", "Liste": "doku_kare.png",
                          "Btn_1_Yuz": "doku_kare.png", "Btn_2_Yuz": "doku_kare.png",
                          "Btn_3_Yuz": "doku_kare.png", "Btn_4_Yuz": "doku_kare.png"})
    return doc("StudUnnamed", 640, 520, root)


# ---------------------------------------------------------------------------
# 1c) NEGATİF ÖRNEK — "stud İKONU" ≠ "stud STİLİ"
#
# Araştırma: modern "studded UI" paketleri stud'u tek ikon/rozet olarak kullanır
# (düz zemin + stud ikonu). Kullanıcının kuralı ise DOKU üzerine kurulu: stud tespiti
# döşenen doku arar. Bu örnek, "tek ikon"un yanlışlıkla stud sayılmaması gerektiğini kilitler.
# ---------------------------------------------------------------------------
def sample_stud_icon():
    root = frame("Card", 0, 0, 420, 320, fills=[solid((28, 30, 44))], radius=18,
                 shadows=[shadow(0, 8, 24, 0, (0, 0, 0), 0.4)], children=[
        frame("Glow_A", 20, 20, 120, 120, fills=[grad_radial([(0.0, (120, 160, 255)),
                                                              (1.0, (30, 34, 56))])],
              shadows=[shadow(0, 0, 26, 0, (120, 160, 255), 0.5)]),
        vector("Ikon_1", 44, 44, 72, 72, "ikon_1.png"),
        vector("Ikon_2", 150, 44, 72, 72, "ikon_2.png"),
        vector("Stud_Rozet", 256, 44, 72, 72, "stud_rozet.png"),   # tek ikon, döşenmiyor
        vector("Ikon_3", 44, 170, 72, 72, "ikon_3.png"),
        vector("Ikon_4", 150, 170, 72, 72, "ikon_4.png"),
        text("Baslik", 240, 168, 160, 80, "ROZET", size=22,
             text={"fontWeight": 800, "color": c(230, 236, 255)}),
    ])
    return doc("StudIcon", 420, 320, root)


# ---------------------------------------------------------------------------
# 1d) SINIF KAPSAMA KİTİ — modelin HİÇ GÖRMEDİĞİ sınıflar
#
# Neden: 129 örnekte yalnız Frame/TextLabel/TextButton/ImageLabel vardı; yani model
# TextBox'ı, ScrollingFrame'i, VideoFrame'i... **hiç görmemişti**. Plugin halka açılınca
# bu sınıflar sürekli gelecek; kör kalmaması için kapsama şart (DURUM.md §6).
#
# Sınıf tetikleyicileri (rules_teacher ile birebir):
#   TextBox        : kind=text + ad tokenı input/textbox/box
#   ScrollingFrame : scroll alanı VEYA ad tokenı scroll/scrollx/scrolly
#   VideoFrame     : ad tokenı video/videoframe
#   ViewportFrame  : ad tokenı viewport/viewportframe/vpf
#   CanvasGroup    : ad tokenı canvas/canvasgroup
#   ImageButton    : image + ad tokenı button/btn/buton (veya ad "…Button" ile bitiyor)
#   ImageLabel     : image, buton tokenı YOK
# Stil: nötr/modern panel (ne anime ne cartoon eşiği) → beklenti "belirsiz".
# ---------------------------------------------------------------------------
def sample_widgets():
    PANEL = (36, 38, 52)
    CARD = (48, 51, 68)
    LINE = (86, 92, 118)

    root = frame("Profil", 0, 0, 900, 640, fills=[solid(PANEL)], children=[
        # header
        frame("Header", 0, 0, 900, 88, fills=[solid((28, 30, 42))], clips=True, children=[
            text("Baslik", 28, 24, 300, 40, "PROFİL", size=30,
                 text={"fontWeight": 900, "color": c(236, 238, 250)}),
        ]),
        # avatar viewport
        frame("Avatar_Viewport", 28, 112, 180, 180, fills=[solid((24, 26, 36))],
              radius=12, clips=True, children=[
                  vector("Avatar_Golge", 20, 20, 140, 140, "avatar_golge.png"),
              ]),
        # video önizleme
        frame("Tanitim_Video", 228, 112, 340, 180, fills=[solid((20, 22, 30))],
              radius=12, clips=True, children=[
                  vector("Oynat", 140, 60, 60, 60, "play_ikon.png"),
              ]),
        # canvas grubu (grup opaklığı/blend için)
        frame("Kart_CanvasGroup", 588, 112, 284, 180, fills=[solid(CARD)], radius=12,
              children=[
                  text("Kart_Baslik", 16, 14, 200, 30, "İstatistik", size=20,
                       text={"fontWeight": 700, "color": c(228, 232, 250)}),
                  text("Kart_Deger", 16, 52, 240, 60, "1 280", size=44,
                       text={"fontWeight": 900, "color": c(150, 210, 255)}),
                  text("Kart_Alt", 16, 128, 240, 24, "bu hafta", size=16,
                       text={"color": c(150, 156, 180)}),
              ]),
        # arama kutusu
        frame("Arama_Kutu", 28, 316, 560, 56, fills=[solid((30, 32, 44))], radius=10,
              stroke={"color": c(*LINE), "opacity": 1.0, "weight": 1}, strokeWeight=1,
              strokeAlign="INSIDE", children=[
                  # DİKKAT: etiketler "_sonEk" biçiminde okunur (Studio ile birebir):
                  # "Arama_Input" → TextBox · "Input_Arama" → yalnızca TextLabel olurdu.
                  text("Arama_Input", 16, 14, 400, 28, "Ara…", size=18,
                       text={"color": c(160, 166, 190)}),
              ]),
        # ikon butonlar (image + button tokenı)
        vector("Ikon_Btn_1", 612, 328, 40, 40, "ikon_1.png"),
        vector("Ikon_Btn_2", 664, 328, 40, 40, "ikon_2.png"),
        vector("Ikon_Btn_3", 716, 328, 40, 40, "ikon_3.png"),
        vector("Ayarlar_Buton", 768, 328, 40, 40, "ikon_ayar.png"),
        # açık sınıf etiketi (forceClass yolu): ad "…_ScrollingFrame" ile bitiyor
        frame("Icerik_ScrollingFrame", 612, 316, 260, 56, fills=[solid((30, 32, 44))], radius=10),
        vector("Profil_ImageButton", 828, 112, 44, 44, "ikon_1.png"),
        # kaydırılan liste (scroll alanı + token)
        frame("Liste_ScrollY", 28, 396, 844, 216, fills=[solid((26, 28, 38))], radius=12,
              clips=True, scroll="VERTICAL", children=[
                  frame("Satir_1", 12, 12, 820, 56, fills=[solid(CARD)], radius=8),
                  frame("Satir_2", 12, 76, 820, 56, fills=[solid(CARD)], radius=8),
                  frame("Satir_3", 12, 140, 820, 56, fills=[solid(CARD)], radius=8),
              ]),
    ])
    return doc("WidgetKit", 900, 640, root)


# ---------------------------------------------------------------------------
# 2) ANIME — kullanıcı tarifi:
#    "görünüşü çok iyi olsun diye çok fazla detay"
#    "en iyi ışıklandırma stili"
#    "genellikle koyu renk ve birden fazla renkli olur"
#    "çoğu renk kapalı olur çünkü ışıklandırma yaptığında en güzel gözükür"
#    "efektler tam ideal olur", "texturelar ortadır"
# ---------------------------------------------------------------------------
SKILL_HUES = [
    # (koyu taban, neon kontur) — "çoğu renk kapalı, bazı renkler efekt niyetine"
    ((58, 42, 96), (150, 190, 255)),   # mavi
    ((96, 40, 92), (255, 150, 230)),   # magenta
    ((40, 88, 92), (140, 245, 235)),   # cyan
    ((92, 82, 38), (255, 220, 130)),   # altın
    ((48, 90, 56), (160, 245, 170)),   # yeşil
    ((78, 42, 96), (205, 160, 255)),   # mor
]


def sample_anime():
    """Kullanıcı tarifi:
       'görünüşü çok iyi olsun diye çok fazla detay'  -> çok katman, çok efekt
       'en iyi ışıklandırma stili'                    -> glow/parlama yoğun
       'genellikle koyu renk ve birden fazla renkli'  -> koyu taban + çok hue
       'çoğu renk kapalı olur (muted)'                -> taban S düşük
       'efektler tam ideal olur', 'texturelar ortadır'"""
    root = frame("HUD", 0, 0, 1600, 900,
                 fills=[grad([(0.0, (16, 14, 30)), (0.55, (26, 22, 46)),
                              (1.0, (12, 10, 24))], angle=135.0)],
                 radius=0, clips=True, children=[
        # koyu, çok renkli, gradientli, efektli üst bar
        frame("TopBar", 0, 0, 1600, 110,
              fills=[grad([(0.0, (34, 28, 58)), (0.5, (48, 40, 78)),
                           (1.0, (28, 24, 50))], angle=92.0)],
              stroke={"color": c(140, 170, 255), "opacity": 0.85, "weight": 2},
              strokeWeight=2, strokeAlign="INSIDE", radius=0, clips=True,
              shadows=[shadow(0, 6, 24, 0, (110, 130, 255), 0.45),
                       shadow(0, 0, 60, -6, (170, 190, 255), 0.25)],
              children=[
                  text("Title", 40, 24, 520, 60, "RUH ÇAĞIRMA", size=38,
                       text={"fontWeight": 900,
                             "color": c(222, 226, 255),
                             "shadow": shadow(0, 0, 18, 0, (150, 170, 255), 0.9)}),
                  frame("Currency", 1160, 26, 400, 58,
                        fills=[solid((30, 26, 48))], radius=29,
                        stroke={"color": c(255, 200, 110), "opacity": 1.0, "weight": 2},
                        strokeWeight=2, strokeAlign="INSIDE",
                        shadows=[shadow(0, 0, 22, 0, (255, 190, 90), 0.55)],
                        children=[
                            text("Value", 0, 0, 400, 58, "12 480", size=30,
                                 text={"fontWeight": 900, "color": c(255, 232, 180)}),
                        ]),
              ]),
        # glow — FX katmanı (image)
        vector("Glow", 560, 300, 480, 480, "glow_soft.png", opacity=0.85),
        vector("Rays", 600, 340, 400, 400, "rays_radial.png", opacity=0.55),
        # karakter kartı — detay: gradient + stroke + gölge + radius
        frame("CharacterCard", 120, 180, 420, 620,
              fills=[grad([(0.0, (40, 34, 66)), (1.0, (22, 18, 38))], angle=158.0)],
              stroke={"color": c(170, 175, 255), "opacity": 0.9, "weight": 3},
              strokeWeight=3, strokeAlign="INSIDE", radius=22, clips=True,
              shadows=[shadow(0, 14, 40, -4, (90, 80, 180), 0.6),
                       shadow(0, 0, 90, -10, (140, 150, 255), 0.18)],
              children=[
                  frame("Portrait", 20, 20, 380, 380,
                        fills=[image_fill("FILL")], radius=18, clips=True),
                  text("Name", 20, 420, 380, 46, "AKIRA", size=34,
                       text={"fontWeight": 900, "color": c(236, 236, 252),
                             "shadow": shadow(0, 2, 10, 0, (0, 0, 0), 0.7)}),
                  text("Desc", 20, 476, 380, 96,
                       "Karanlık rüzgarın varisi. Gölge patlaması 3. seviye.",
                       size=18, text={"fontWeight": 400, "color": c(172, 172, 200)}),
                  frame("HP_Bar", 20, 560, 380, 26, fills=[solid((22, 20, 38))],
                        radius=13, clips=True, children=[
                            frame("Fill", 0, 0, 250, 26,
                                  fills=[grad([(0.0, (230, 90, 130)),
                                               (1.0, (255, 175, 110))], angle=0.0)],
                                  radius=13),
                        ]),
                  frame("MP_Bar", 20, 596, 380, 20, fills=[solid((22, 20, 38))],
                        radius=10, clips=True, children=[
                            frame("Fill", 0, 0, 180, 20,
                                  fills=[grad([(0.0, (110, 180, 240)),
                                               (1.0, (170, 220, 255))], angle=0.0)],
                                  radius=10),
                        ]),
              ]),
        # yetenek butonları — koyu taban + neon kontur, HUE ÇEŞİTLİ
        *[frame("Skill_Button_%d" % (i + 1),
                600 + (i % 3) * 150, 200 + (i // 3) * 150, 130, 130,
                fills=[grad([(0.0, SKILL_HUES[i][0]),
                             (1.0, tuple(max(0, v - 26) for v in SKILL_HUES[i][0]))],
                            angle=140.0)],
                stroke={"color": c(*SKILL_HUES[i][1]), "opacity": 1.0, "weight": 2},
                strokeWeight=2, strokeAlign="INSIDE", radius=18, clips=True,
                shadows=[shadow(0, 0, 26, 0, SKILL_HUES[i][1], 0.7)],
                children=[
                    text("Key", 0, 40, 130, 50, "QWEASD"[i], size=30,
                         text={"fontWeight": 900, "color": c(238, 238, 252),
                               "shadow": shadow(0, 0, 12, 0, SKILL_HUES[i][1], 0.8)}),
                ]) for i in range(6)],
        # küçük bilgi çipleri — farklı hue'larda accent
        frame("Tag_Damage", 600, 520, 130, 40, fills=[solid((64, 34, 40))],
              radius=8, stroke={"color": c(255, 130, 140), "opacity": 1, "weight": 1},
              strokeWeight=1, strokeAlign="INSIDE",
              children=[text("Lbl", 0, 8, 130, 24, "HASAR", size=16,
                             text={"fontWeight": 700, "color": c(255, 180, 185)})]),
        frame("Tag_Heal", 750, 520, 130, 40, fills=[solid((34, 62, 44))],
              radius=8, stroke={"color": c(150, 240, 170), "opacity": 1, "weight": 1},
              strokeWeight=1, strokeAlign="INSIDE",
              children=[text("Lbl", 0, 8, 130, 24, "İYİLEŞTİR", size=14,
                             text={"fontWeight": 700, "color": c(190, 245, 200)})]),
        frame("Tag_Shield", 900, 520, 130, 40, fills=[solid((34, 52, 68))],
              radius=8, stroke={"color": c(140, 210, 255), "opacity": 1, "weight": 1},
              strokeWeight=1, strokeAlign="INSIDE",
              children=[text("Lbl", 0, 8, 130, 24, "KALKAN", size=16,
                             text={"fontWeight": 700, "color": c(185, 225, 255)})]),
        # derin istatistik bloğu: Anime'de "çok fazla detay" (derinlik + efekt yoğunluğu)
        frame("StatsBox", 600, 620, 420, 220, fills=[grad([(0.0, (38, 32, 62)),
                                                          (1.0, (20, 17, 34))], angle=160.0)],
              radius=14, stroke={"color": c(160, 170, 255), "opacity": 0.8, "weight": 1},
              strokeWeight=1, strokeAlign="INSIDE", clips=True,
              shadows=[shadow(0, 0, 34, 0, (140, 150, 255), 0.5)],
              children=[
                  frame("Row_A", 14, 14, 392, 60, fills=[solid((30, 26, 50))], radius=10,
                        children=[
                            frame("Cell_A1", 8, 8, 180, 44, fills=[grad_radial([(0.0, (120, 90, 200)),
                                                                               (1.0, (40, 30, 70))])],
                                  radius=8, shadows=[shadow(0, 0, 22, 0, (150, 120, 255), 0.5)],
                                  children=[
                                      frame("Icon_A", 6, 6, 32, 32, fills=[image_fill("FIT")],
                                            radius=16, shadows=[shadow(0, 0, 18, 0, (200, 180, 255), 0.6)],
                                            children=[
                                                frame("Icon_Inner", 4, 4, 24, 24,
                                                      fills=[grad_radial([(0.0, (255, 255, 255)),
                                                                          (1.0, (170, 150, 255))], opacity=0.8)],
                                                      radius=12,
                                                      shadows=[shadow(0, 0, 16, 0, (255, 255, 255), 0.5)]),
                                            ]),
                                      text("Val_A", 44, 6, 128, 32, "42", size=22,
                                           text={"fontWeight": 900, "color": c(228, 226, 255),
                                                 "shadow": shadow(0, 0, 14, 0, (150, 160, 255), 0.8)}),
                                  ]),
                            frame("Cell_A2", 200, 8, 184, 44, fills=[grad_radial([(0.0, (90, 160, 220)),
                                                                                (1.0, (28, 44, 70))])],
                                  radius=8, shadows=[shadow(0, 0, 22, 0, (120, 190, 255), 0.5)],
                                  children=[
                                      text("Val_B", 10, 6, 164, 32, "1280", size=22,
                                           text={"fontWeight": 900, "color": c(214, 234, 255)}),
                                  ]),
                        ]),
                  frame("Row_B", 14, 84, 392, 122, fills=[solid((26, 23, 44))], radius=10,
                        children=[
                            frame("Bar_Outer", 12, 76, 368, 26, fills=[solid((18, 16, 32))],
                                  radius=13, clips=True, children=[
                                      frame("Bar_Fill", 0, 0, 250, 26,
                                            fills=[grad_radial([(0.0, (255, 160, 120)),
                                                                (1.0, (180, 60, 140))])], radius=13,
                                            shadows=[shadow(0, 0, 24, 0, (255, 140, 160), 0.6)]),
                                  ]),
                        ]),
              ]),
        # sparkle — efekt katmanı
        vector("Sparkle_01", 300, 120, 64, 64, "sparkle.png", opacity=1.0),
        vector("Sparkle_02", 1240, 620, 48, 48, "sparkle.png", opacity=1.0),
        # vignette
        vector("Vignette", 0, 0, 1600, 900, "vignette.png", opacity=0.6),
    ])
    _assign_images(root, {"Portrait": "portrait_akira.png"})
    _anime_lighting(root)
    return doc("AnimeHUD", 1600, 900, root)


# ---------------------------------------------------------------------------
# 3) CARTOON — kullanıcı tarifi:
#    "texture'den olan, pek fazla efekti olmayan GUI'dir"
#    "birden fazla texture olabilir, efekt de olabilir ama genellikle azdır"
#    "detay: cartoonda çok fazla yok"
# ---------------------------------------------------------------------------
def sample_cartoon():
    root = frame("MainMenu", 0, 0, 1280, 720,
                 fills=[image_fill("TILE")], radius=0, clips=True, children=[
        frame("Logo", 340, 60, 600, 180, fills=[image_fill("FIT")], radius=0),
        frame("Panel", 300, 280, 680, 360, fills=[image_fill("STRETCH")],
              radius=20, clips=True, children=[
            frame("Play_Button", 40, 40, 600, 90,
                  fills=[image_fill("STRETCH")], radius=16, children=[
                text("Label", 0, 0, 600, 90, "OYNA", size=36,
                     text={"fontWeight": 900, "color": c(60, 40, 20)}),
            ]),
            frame("Settings_Button", 40, 145, 290, 80,
                  fills=[image_fill("STRETCH")], radius=16, children=[
                text("Label", 0, 0, 290, 80, "AYARLAR", size=26,
                     text={"fontWeight": 900, "color": c(60, 40, 20)}),
            ]),
            frame("Shop_Button", 350, 145, 290, 80,
                  fills=[image_fill("STRETCH")], radius=16, children=[
                text("Label", 0, 0, 290, 80, "MARKET", size=26,
                     text={"fontWeight": 900, "color": c(60, 40, 20)}),
            ]),
            frame("Exit_Button", 40, 240, 600, 80,
                  fills=[image_fill("STRETCH")], radius=16, children=[
                text("Label", 0, 0, 600, 80, "ÇIKIŞ", size=26,
                     text={"fontWeight": 900, "color": c(90, 50, 30)}),
            ]),
        ]),
        # nadir efekt: tek, sade bir gölge
        frame("Badge", 60, 60, 140, 140, fills=[solid((250, 210, 90))],
              radius=70, shadows=[shadow(0, 8, 0, 0, (150, 100, 20), 1.0)],
              children=[
                  text("New", 0, 40, 140, 60, "YENİ", size=28,
                       text={"fontWeight": 900, "color": c(90, 60, 10)}),
              ]),
        text("Version", 40, 660, 400, 40, "v1.4.2", size=18,
             text={"fontWeight": 400, "color": c(70, 55, 40)}),
    ])
    _assign_images(root, {
        "MainMenu": "wood_bg.png",
        "Logo": "logo.png",
        "Panel": "panel_wood.png",
        "Play_Button": "btn_wood.png",
        "Settings_Button": "btn_wood.png",
        "Shop_Button": "btn_wood.png",
        "Exit_Button": "btn_wood.png",
    })
    _cartoon_texture(root)
    return doc("CartoonMenu", 1280, 720, root)


# ---------------------------------------------------------------------------
# 4) UÇ DURUMLAR — sıfır bölme, boş ad, aşırı değerler
# ---------------------------------------------------------------------------
def sample_edge():
    root = frame("Edge", 0, 0, 100, 100, fills=[], radius=0, clips=False, children=[
        frame("", 0, 0, 0, 0, fills=[]),                       # boş ad, 0 boyut
        frame("Sıfır Yükseklik", 0, 0, 50, 0, fills=[]),
        frame("Negatif", -500, -500, 40, 40, fills=[]),
        text("Yazısız", 0, 0, 30, 30, "", size=0),
        frame("Uç", 0, 0, 1e7, 0.001, fills=[solid((255, 255, 255))],
              stroke={"color": c(0, 0, 0), "opacity": 1, "weight": 1e5},
              strokeWeight=1e5, strokeAlign="CENTER", radius=1e6,
              shadows=[shadow(0, 0, 0, 0, (0, 0, 0), 0.0)] * 99,
              opacity=0.0, rot=359.5),
        frame("Tek Çocuk", 0, 0, 10, 10, fills=[], children=[
            frame("Derin", 0, 0, 1, 1, fills=[], children=[
                frame("Daha Derin", 0, 0, 1, 1, fills=[]),
            ]),
        ]),
    ])
    return doc("Edge", 100, 100, root)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# STİL SÜSLEME — sentetik örnekleri kullanıcının stil tarifine uydurur
#
# Neden ayrı adım: bu örnekler başlangıçta yalnızca RAW determinizmi için üretilmişti;
# stil eşikleri (spec/style-rules.json) sonradan geldi ve örneklerin sinyalleri eşiklerin
# altında kalıyordu (anime "ışıklandırma" içermiyordu, cartoon "doku" içermiyordu).
# Aşağıdaki dönüşümler tamamen deterministiktir ve kullanıcı tarifini veriye çevirir:
#   ANIME   : "en iyi ışıklandırma" → glow (ofset 0 + geniş blur), radyal gradyan, çok duraklı
#   CARTOON : "texture'den olan"    → döşeme (TILE) dolguları + doku yoğunluğu
# ---------------------------------------------------------------------------
def _walk_items(root, fn, depth=0):
    fn(root, depth)
    for ch in root.get("children") or []:
        _walk_items(ch, fn, depth + 1)


def _anime_lighting(root):
    """Işıklandırma yoğunluğunu kullanıcı tarifine çıkarır (glow + radyal + çok duraklı)."""
    state = {"i": 0}

    def deco(it, depth):
        state["i"] += 1
        fills = it.get("fills") or []
        # gradyanları radyale çevir + 3+ durak garantile (ışık katmanı karakteri)
        for k, f in enumerate(fills):
            if f.get("type") == "GRADIENT":
                stops = f.get("stops") or []
                if len(stops) == 2:
                    a = stops[0]["color"]
                    b = stops[1]["color"]
                    mid = {"r": (a["r"] + b["r"]) // 2, "g": (a["g"] + b["g"]) // 2, "b": (a["b"] + b["b"]) // 2}
                    f["stops"] = [stops[0], {"pos": 0.5, "color": mid, "opacity": 1.0}, stops[1]]
                if state["i"] % 2 == 0:
                    f["type"] = "GRADIENT_OTHER"          # radyal
        # glow: ofset ~0, geniş blur, yüksek opaklık (EiRaw.glowPattern)
        if it.get("kind") == "frame" and depth >= 1 and (fills or it.get("image")):
            shs = list(it.get("shadows") or [])
            shs.append(shadow(0, 0, 30, 0, (150, 165, 255), 0.55))
            it["shadows"] = shs
            it.setdefault("shadow", shs[0])
        # ışık katmanı: Figma'da glow/rays/vignette katmanları blend mode ile yapılır
        # (code.js bu alanı `ei.blendMode` olarak yazacak — yan kanal).
        nm = (it.get("name") or "").lower()
        if it.get("image") or it.get("shadows") or "glow" in nm or "ray" in nm \
                or "sparkle" in nm or "vignette" in nm:
            it.setdefault("ei", {})["blendMode"] = "SCREEN"

    _walk_items(root, deco)
    return root


def _cartoon_texture(root):
    """Doku yoğunluğunu kullanıcı tarifine çıkarır (döşeme + image ağırlıklı düğümler)."""
    state = {"i": 0}

    def deco(it, depth):
        state["i"] += 1
        # bazı düğümlere döşeme (TILE) dokusu ekle — cartoon'un ayırt edici sinyali
        if it.get("kind") == "frame" and state["i"] % 3 != 2:
            fills = list(it.get("fills") or [])
            n_img = len([f for f in fills if f.get("type") == "IMAGE"])
            if n_img < 2:
                fills.append(image_fill("TILE", 0.9))
                it["fills"] = fills

    _walk_items(root, deco)
    return root


def _assign_images(root, mapping):
    """IMAGE dolgularına gerçek dosya adı verir (dedupe'u taklit eder).

    AYNI dosya adı birden fazla yerde geçerse -> plugin onu tek PNG olarak
    dışa aktarır ve bu bir DOKU (texture) işaretidir (Stud tespitinin kalbi).
    """

    def rec(it):
        nm = it.get("name", "")
        for f in (it.get("fills") or []):
            if f.get("type") == "IMAGE":
                f["file"] = mapping.get(nm, "%s.png" % (nm or "img"))
        for ch in (it.get("children") or []):
            rec(ch)

    rec(root)


# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    samples = [
        ("stud-market.json", sample_stud()),
        ("stud-unnamed.json", sample_stud_unnamed()),
        ("stud-icon.json", sample_stud_icon()),
        ("widgets-kit.json", sample_widgets()),
        ("anime-hud.json", sample_anime()),
        ("cartoon-menu.json", sample_cartoon()),
        ("edge.json", sample_edge()),
    ]
    for fname, d in samples:

        def count(it):
            n = 1
            for ch in (it.get("children") or []):
                n += count(ch)
            return n

        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
        print("  %-20s %-14s %dx%d  %3d düğüm"
              % (fname, d["name"], d["width"], d["height"], count(d["root"])))
    print("\n%d export örneği -> %s" % (len(samples), OUT))


if __name__ == "__main__":
    main()
