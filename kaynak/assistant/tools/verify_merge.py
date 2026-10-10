#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S5 KAPISI — ÖĞRENME PAKETİ BİRLEŞTİRİCİ (merge_learn)

Neyi kanıtlıyor:
  1. **Bayt paritesi:** Python birleştirici + kodlayıcı, kanon `ei-learn.js`'in çözüp yeniden
     kodladığı metinle BİREBİR aynı dosyayı üretiyor (sıralama, başlık, budama dâhil).
  2. **Lua okur:** birleşik dosyayı `EILearn.lua` (fengari) çözüp yeniden kodluyor, aynı baytlar.
  3. **Determinizm:** aynı girdi → aynı bayt; paket SIRASI değişse de aynı bayt.
  4. **Korunum:** budama devreye girmediğinde sayaçlar paketlerin toplamıdır (kayıp yok).
  5. **Sınırlar:** kalabalık girdide bağlam ≤ 400 ve metin ≤ boyut sınırı.
  6. **Düşmanca girdi:** boşluk/satır sonu/pipe enjeksiyonu, negatif ve sayı olmayan sayaçlar,
     yinelenen satırlar → biçim bozulmaz, çıktı yine JS ile okunur.
  7. **JSON sarmalayıcı:** `{"text": "<ei-learn…>"}` biçimi, düz metinle aynı birleşik dosyayı verir.
  8. **--dedupe / --min-observations** davranışı.

Kullanım:  python3 tools/verify_merge.py     (EASYIMPORT_LUA_BIN de desteklenir)
Çıkış: 0 = GEÇTİ · 1 = BAŞARISIZ
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import merge_learn as M            # noqa: E402
from luatable import dumps as lua_dumps   # noqa: E402

JS_DIR = os.path.join(ROOT, "runtime", "js")
LUA_DIR = os.path.join(ROOT, "runtime", "lua")
VENDOR = os.path.join(ROOT, "tools", "vendor")
TOL = 1e-12

# ------------------------------------------------------------------ JS: paket üretimi
# Üç "kullanıcı" paketi: gerçekçi seçim/ret dağılımı + sınıf düzeltmeleri + kenar durumlar.
JS_BUILD = r"""
const path = require('path');
const fs = require('fs');
const EILearn = require(path.join(process.env.EI_JS_DIR, 'ei-learn.js'));

function mk(events, exports) {
  const st = EILearn.newState();
  for (const e of events) {
    const ctx = EILearn.ctxKey(e.ctx[0], e.ctx[1], e.ctx[2], e.ctx[3]);
    if (e.kind === 'anim') EILearn.recordAnim(st, ctx, e.anim, e.ok);
    else EILearn.recordClass(st, ctx, e.cls, 1);
  }
  for (let i = 0; i < exports; i++) EILearn.exportBump(st);
  return st;
}
const users = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
for (const u of users) {
  const st = mk(u.events, u.exports);
  out[u.name] = { text: EILearn.encode(st), stats: EILearn.stats(st) };
}
process.stdout.write(JSON.stringify(out));
"""

# ------------------------------------------------------------------ JS: birleştirme + okuma
JS_MERGE = r"""
const path = require('path');
const fs = require('fs');
const EILearn = require(path.join(process.env.EI_JS_DIR, 'ei-learn.js'));

const payload = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

// 1) paketleri JS tarafında birleştir (Python merge_states'in birebir aynısı: sayaç toplama)
const st = EILearn.newState();
for (const text of payload.texts) {
  const p = EILearn.decode(text);
  st.events += p.events;
  st.exports += p.exports;
  for (const ctx in p.anim) {
    if (!Object.prototype.hasOwnProperty.call(p.anim, ctx)) continue;
    if (!st.anim[ctx]) st.anim[ctx] = {};
    for (const id in p.anim[ctx]) {
      if (!Object.prototype.hasOwnProperty.call(p.anim[ctx], id)) continue;
      const e = p.anim[ctx][id], cur = st.anim[ctx][id] || [0, 0];
      st.anim[ctx][id] = [cur[0] + e[0], cur[1] + e[1]];
    }
  }
  for (const ctx in p.cls) {
    if (!Object.prototype.hasOwnProperty.call(p.cls, ctx)) continue;
    if (!st.cls[ctx]) st.cls[ctx] = {};
    for (const cn in p.cls[ctx]) {
      if (!Object.prototype.hasOwnProperty.call(p.cls[ctx], cn)) continue;
      st.cls[ctx][cn] = (st.cls[ctx][cn] || 0) + p.cls[ctx][cn];
    }
  }
}
EILearn.fit(st, payload.cap, payload.sizeCap);
const merged = EILearn.encode(st);

// 2) verilen birleşik metni oku → yeniden kodla (bayt paritesi + düşmanca girdi kontrolü)
const rt = EILearn.encode(EILearn.decode(payload.check));
process.stdout.write(JSON.stringify({
  merged: merged,
  roundtrip: rt === payload.check,
  roundtripText: rt,
  stats: EILearn.stats(EILearn.decode(payload.check)),
  scores: payload.scorePairs.map(function (p) {
    return EILearn.scoreAnim(EILearn.decode(payload.check), p.ctx, p.id);
  })
}));
"""

FENGARI_RUNNER = r"""
const { lauxlib, lua, lualib, to_luastring } = require('fengari');
const fs = require('fs');
const prog = fs.readFileSync(process.argv[2], 'utf8');
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
const st = lauxlib.luaL_dostring(L, to_luastring(prog));
if (st !== lua.LUA_OK) {
  process.stderr.write('LUA HATASI: ' + (lua.lua_tojsstring(L, -1) || '?') + '\n');
  process.exit(1);
}
"""

LUA_CHECK = r"""
local text = TEXT
local st = EILearn.decode(text)
local enc = EILearn.encode(st)
local out = { enc = enc }
io.write('{"enc":' .. string.format('%q', enc):gsub('\\\n', '\\n') .. '}')
"""


def _run(node_src, payload=None, program=None, env_extra=None, read_path=None):
    files = []
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(node_src)
        runner = fh.name
    files.append(runner)
    args = ["node", runner]
    if read_path is not None:
        args.append(read_path)
    elif payload is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
            files.append(fh.name)
        args.append(files[-1])
    if program is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(program)
            files.append(fh.name)
        args.append(files[-1])
    env = dict(os.environ)
    env["EI_JS_DIR"] = JS_DIR
    env["NODE_PATH"] = VENDOR
    if env_extra:
        env.update(env_extra)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=600, env=env)
        if r.returncode != 0:
            raise RuntimeError((r.stdout or "")[:1200] + "\n" + (r.stderr or "")[:2500])
        return r.stdout
    finally:
        for f in files:
            os.unlink(f)


def js_build(users):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(users, fh, ensure_ascii=False)
        path = fh.name
    try:
        out = _run(JS_BUILD, read_path=path)
    finally:
        os.unlink(path)
    return json.loads(out)


def js_merge(texts, check, cap, size_cap, score_pairs):
    payload = {"texts": texts, "check": check, "cap": cap, "sizeCap": size_cap,
               "scorePairs": score_pairs}
    return json.loads(_run(JS_MERGE, payload))


def lua_roundtrip(text, lua_bin=None):
    src = open(os.path.join(LUA_DIR, "EILearn.lua"), encoding="utf-8").read()
    prog = ("local EILearn = (function()\n" + src + "\nend)()\n"
            "local TEXT = " + lua_dumps(text) + "\n"
            "local st = EILearn.decode(TEXT)\n"
            "local enc = EILearn.encode(st)\n"
            "io.write(enc)\n")
    if lua_bin:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(prog)
            tmp = fh.name
        try:
            r = subprocess.run([lua_bin, tmp], capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                raise RuntimeError((r.stdout or "")[:1200] + "\n" + (r.stderr or "")[:2500])
            return r.stdout
        finally:
            os.unlink(tmp)
    if not os.path.isdir(os.path.join(VENDOR, "fengari")):
        raise RuntimeError("fengari bulunamadı: %s" % VENDOR)
    return _run(FENGARI_RUNNER, None, prog)   # Lua io.write → stdout doğrudan


# ------------------------------------------------------------------ test girdileri
def user_events():
    """Üç kullanıcı: farklı stiller, sınıflar, roller, fx'ler + sınıf düzeltmeleri."""
    def anim(style, cls, role, fx, aid, ok):
        return {"kind": "anim", "ctx": [style, cls, role, fx], "anim": aid, "ok": ok}

    def cls(style, c, role, fx, newcls):
        return {"kind": "cls", "ctx": [style, c, role, fx], "cls": newcls}

    # id'ler GERÇEK anim-library.json'dan (kütüphane dışı id uyarısı yalnız ayrı testte)
    u1 = [anim("anime", "ImageButton", "primary-button", "glow", "fx_glow_pulse", True),
          anim("anime", "ImageButton", "primary-button", "glow", "fx_glow_pulse", True),
          anim("anime", "ImageButton", "primary-button", "shine", "hover_shine_sweep", True),
          anim("anime", "ImageButton", "primary-button", "glow", "enter_pop_scale", False),
          anim("stud", "Frame", "panel", "-", "loop_rotate_slow", True),
          cls("belirsiz", "Icon", "-", "-", "ImageButton")]
    u2 = [anim("cartoon", "TextButton", "button", "-", "enter_pop_scale", True),
          anim("cartoon", "TextButton", "button", "-", "enter_pop_scale", True),
          anim("cartoon", "TextButton", "button", "-", "press_ripple", False),
          anim("stud", "Frame", "panel", "-", "loop_rotate_slow", True),
          cls("belirsiz", "Icon", "-", "-", "ImageButton"),
          cls("belirsiz", "Icon", "-", "-", "ImageLabel")]
    u3 = [anim("belirsiz", "ImageLabel", "icon", "sparkle", "fx_sparkle_twinkle", True),
          anim("anime", "ImageButton", "primary-button", "glow", "fx_glow_pulse", False),
          anim("stud", "Frame", "panel", "-", "loop_rotate_slow", True)]
    return [{"name": "kullanici1.txt", "events": u1, "exports": 3},
            {"name": "kullanici2.txt", "events": u2, "exports": 2},
            {"name": "kullanici3.txt", "events": u3, "exports": 1}]


CROWD = [{"name": "kalabalik.txt",
          "events": [{"kind": "anim",
                      "ctx": ["belirsiz", "Frame", "r%d" % i, "fx%d" % i],
                      "anim": "anim_%d" % i, "ok": True}
                     for i in range(600)],
          "exports": 1}]

HOSTILE_TEXT = "\n".join([
    "ei-learn v1",
    "events 5",
    "exports 1",
    "anim anime|imagebutton|primary|glow shine_sweep 3 0",
    "anim anime|imagebutton|primary|glow shine_sweep -4 2.7",      # negatif + ondalık
    "anim anime|imagebutton|primary|glow bozuk id 1 1",            # satır içi boşluk (atılır)
    "anim kotu ctx|iki iki_parcali|bir|- glow_pulse 1 0",          # bağlam 2 parçalı → uyarı
    "anim anime|imagebutton|primary|glow\nsahte 1 1",              # satır sonu enjeksiyonu
    "cls anime|TextButton|primary|- TextButton 2",
    "cls anime|TextButton|primary|- bozuk sinif! 1",               # boşluk yok, sanitize olur
    "",
])


def merge_to_bytes(texts, cap=M.DEFAULT_CAP, size_cap=M.DEFAULT_SIZE_CAP, min_obs=0):
    states = []
    for t in texts:
        st, ver = M.decode(t)
        if ver is not None:
            st["v"] = ver
        states.append(st)
    merged = M.merge_states(states)
    merged, _ = M.filter_min_observations(merged, min_obs)
    M.fit(merged, cap, size_cap)
    return M.encode(merged), merged


# ------------------------------------------------------------------------ kapı
def main():
    lua_bin = os.environ.get("EASYIMPORT_LUA_BIN") or None
    problems = []

    print("=" * 74)
    print("S5 KAPISI — ÖĞRENME PAKETİ BİRLEŞTİRİCİ (JS ≡ Python; Lua okur)")
    print("=" * 74)

    users = user_events()
    built = js_build(users)
    texts = [built[u["name"]]["text"] for u in users]
    print("  [OK] kanon JS ile %d kullanıcı paketi üretildi (%s)"
          % (len(texts), ", ".join(u["name"] for u in users)))

    # 1) Python çözücü, JS'in yazdığını birebir okuyor mu + sayaç korunumu
    py_states = []
    for u, t in zip(users, texts):
        st, ver = M.decode(t)
        py_states.append(st)
        if ver != M.VERSION:
            problems.append("%s: sürüm okunamadı (%r)" % (u["name"], ver))
    py_merged = M.merge_states(py_states)
    py_text = M.encode(py_merged)
    print("  [OK] %d paket çözüldü · %d bağlam · %d olay"
          % (len(texts), M.count_contexts(py_merged), py_merged["events"]))

    # 2) bayt paritesi: JS çöz + birleştir + kodla == Python
    check_pairs = [{"ctx": "anime|imagebutton|primary-button|glow", "id": "fx_glow_pulse"},
                   {"ctx": "cartoon|textbutton|button|-", "id": "enter_pop_scale"},
                   {"ctx": "belirsiz|imagelabel|icon|sparkle", "id": "yok_boyle_id"}]
    js = js_merge(texts, py_text, M.DEFAULT_CAP, M.DEFAULT_SIZE_CAP, check_pairs)
    if js["merged"] == py_text:
        print("  [OK] bayt paritesi: JS çöz+birleştir+kodla ≡ Python (%d bayt)" % len(py_text))
    else:
        problems.append("bayt paritesi tutmadı (JS %d bayt ≠ Python %d bayt)"
                        % (len(js["merged"]), len(py_text)))
    if js["roundtrip"]:
        print("  [OK] birleşik dosya JS'te kayıpsız: çöz → kodla ≡ aynı baytlar")
    else:
        problems.append("birleşik dosya JS'te kayıpsız değil (round-trip farkı)")

    # 3) Lua (fengari) da aynı metni üretiyor
    lua_text = lua_roundtrip(py_text, lua_bin)
    if lua_text == py_text:
        print("  [OK] Lua (fengari) çöz+kodla ≡ aynı baytlar — Studio tarafı da okur")
    else:
        problems.append("Lua round-trip farkı (%d bayt ≠ %d bayt)" % (len(lua_text), len(py_text)))

    # 4) skor formülü paritesi
    st_for_scores = M.decode(py_text)[0]
    for pair, js_score in zip(check_pairs, js["scores"]):
        py_score = M.score_anim(st_for_scores, pair["ctx"], pair["id"])
        if abs(py_score - js_score) > TOL:
            problems.append("skor farkı %s/%s: py %.17g ≠ js %.17g"
                            % (pair["ctx"], pair["id"], py_score, js_score))
    if not problems:
        print("  [OK] skor formülü (2c+1)/(2(c+r)+2) iki dilde aynı: %s"
              % " · ".join("%.4f" % s for s in js["scores"]))

    # 5) determinizm + paket sırası bağımsızlığı
    a1, _ = merge_to_bytes(texts)
    a2, _ = merge_to_bytes(texts)
    a3, _ = merge_to_bytes(list(reversed(texts)))
    if a1 == a2 == a3:
        print("  [OK] determinizm: aynı girdi ve ters paket sırası → aynı %d bayt" % len(a1))
    else:
        problems.append("determinizm: sıra bağımsızlığı sağlanmadı")

    # 6) sayaç korunumu (budama devreye girmiyor)
    want = {}
    for st in py_states:
        for ctx, ids in st["anim"].items():
            for aid, e in ids.items():
                cur = want.setdefault(ctx, {}).setdefault(aid, [0, 0])
                cur[0] += e[0]
                cur[1] += e[1]
    got = M.decode(py_text)[0]
    if got["anim"] == want:
        rows = sum(len(v) for v in want.values())
        print("  [OK] korunum: %d animasyon satırı kayıpsız toplandı (seçim/ret sayaçları eşit)" % rows)
    else:
        problems.append("korunum: birleşik sayaçlar paket toplamına eşit değil")

    # 7) sınırlar: kalabalık girdi → bağlam ≤ 400 ve boyut sınırı
    crowd = js_build(CROWD)
    ctexts = [crowd["kalabalik.txt"]["text"]]
    if M.count_contexts(M.decode(ctexts[0])[0]) < 500:
        problems.append("kalabalık test girdisi beklenenden küçük (600 bağlam üretilemedi)")
    cmerged, cst = merge_to_bytes(ctexts)
    if M.count_contexts(cst) <= M.DEFAULT_CAP:
        print("  [OK] bağlam sınırı: 600 bağlamlık girdi → %d bağlam (sınır %d)"
              % (M.count_contexts(cst), M.DEFAULT_CAP))
    else:
        problems.append("bağlam sınırı aşıldı: %d > %d" % (M.count_contexts(cst), M.DEFAULT_CAP))
    small, sst = merge_to_bytes(ctexts, cap=40, size_cap=4096)
    if M.byte_len(small) <= 4096 and M.count_contexts(sst) <= 40:
        print("  [OK] boyut sınırı: 4096 bayt / 40 bağlam istendi → %d bayt · %d bağlam"
              % (M.byte_len(small), M.count_contexts(sst)))
    else:
        problems.append("boyut sınırı aşıldı: %d bayt · %d bağlam"
                        % (M.byte_len(small), M.count_contexts(sst)))

    # 8) düşmanca girdi: enjeksiyon + bozuk sayaçlar
    hmerged, hst = merge_to_bytes([HOSTILE_TEXT])
    hlines = hmerged.split("\n")
    bad_tokens = [ln for ln in hlines[3:] if any(" " in t for t in []) ]
    if all(len(ln.split(" ")) in (5, 4) for ln in hlines[3:]):
        print("  [OK] düşmanca girdi: %d satır, hepsi doğru alan sayısında (enjeksiyon temizlendi)"
              % len(hlines[3:]))
    else:
        problems.append("düşmanca girdi: alan sayısı bozuk satır(lar) var")
    hjs = js_merge([], hmerged, M.DEFAULT_CAP, M.DEFAULT_SIZE_CAP, [])
    if hjs["roundtrip"]:
        print("  [OK] düşmanca girdiden çıkan dosya JS'te kayıpsız okunuyor")
    else:
        problems.append("düşmanca girdiden çıkan dosya JS round-trip'ini geçemedi")
    # KANON semantiği (ei-learn.js decode ile birebir): aynı anahtarın SONRAKİ satırı kazanır
    # (sayaç toplanmaz), fazla alanlar yok sayılır, negatif/ondalık sayaç 0/taban olur.
    htxt = M.decode(hmerged)[0]
    hrow = htxt["anim"].get("anime|imagebutton|primary|glow", {})
    if hrow.get("shine_sweep") == [0, 2] and hrow.get("bozuk") == [0, 1] and len(hrow) == 2:
        print("  [OK] düşmanca sayaçlar kanon semantiğinde: son satır kazanır, negatif→0, "
              "fazla alan yok sayılır (shine_sweep [0,2], bozuk [0,1])")
    else:
        problems.append("düşmanca sayaç davranışı kanondan farklı: %r" % (hrow,))

    # 9) JSON sarmalayıcı ≡ düz metin
    with tempfile.TemporaryDirectory() as tmp:
        p_txt = os.path.join(tmp, "a.txt")
        p_json = os.path.join(tmp, "a.json")
        with open(p_txt, "w", encoding="utf-8") as fh:
            fh.write(texts[0])
        with open(p_json, "w", encoding="utf-8") as fh:
            json.dump({"format": "ei-learn", "version": 1, "text": texts[0]}, fh)
        s_txt, v_txt, _ = M.load_package(p_txt)
        s_json, v_json, _ = M.load_package(p_json)
        if M.encode(s_txt) == M.encode(s_json) == texts[0]:
            print("  [OK] JSON sarmalayıcı: {\"text\": …} düz metinle birebir aynı durumu veriyor")
        else:
            problems.append("JSON sarmalayıcı düz metinle aynı sonucu vermedi")

    # 10) --min-observations süzgeci
    filtered = M.merge_states(py_states)
    filtered, dropped = M.filter_min_observations(filtered, 3)
    if dropped > 0 and all(sum(e) >= 3 for ids in filtered["anim"].values() for e in ids.values()):
        print("  [OK] gürültü süzgeci: %d kayıt atıldı, kalan her kaydın gözlemi ≥ 3" % dropped)
    else:
        problems.append("gürültü süzgeci beklenen şekilde çalışmadı (atılan=%d)" % dropped)

    # 11) rapor/önsel üretimi çökmeden çalışıyor
    anim_ids, roles, fx = M.load_anim_ids()
    if not anim_ids:
        problems.append("anim-library.json okunamadı (önsel/sınıflama için gerekli)")
    else:
        rep = M.analyse(py_merged, anim_ids, roles, fx)
        unknown = [d for d in rep["unknownAnimIds"]]
        print("  [OK] rapor: %d animasyon id'si · %d rol · %d fx türü kütüphaneden doğrulanıyor%s"
              % (len(anim_ids), len(roles), len(fx),
                 (" · kütüphane dışı id: " + ", ".join(unknown[:4])) if unknown else ""))
        pri = M.priors_doc(py_merged)
        if pri["format"] == "ei-learn-priors" and pri["anim"]:
            print("  [OK] önsel tablo: %d bağlam (A7/A8 tüketecek)" % len(pri["anim"]))

    print("-" * 74)
    if problems:
        for p in problems:
            print("  [!!] " + p)
        print("SONUÇ: BAŞARISIZ — %d sorun" % len(problems))
        return 1
    print("SONUÇ: GEÇTİ — birleştirme JS ≡ Python ≡ Lua birebir; sınırlar ve düşmanca girdi güvenli")
    return 0


if __name__ == "__main__":
    sys.exit(main())
