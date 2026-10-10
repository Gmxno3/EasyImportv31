#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figma paneli derleyicisi: ui.base.html + asistan çalışma zamanı (assistant/runtime/js) + asistan paneli
→ ui.html. Eklenti tek dosya olduğu için JS çalışma zamanı satır içine gömülür.
Kullanım: python3 build_ui.py     (ui.html'i yeniden üretir; ui.base.html kaynaktır)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(HERE, "..", "assistant", "runtime", "js")
ORDER = ["ei-features-spec.js", "ei-raw.js", "ei-style.js", "ei-features.js", "ei-model.js", "ei-learn.js", "ei-anim.js", "ei-ekstra.js", "ei-fxmodel.js", "ei-fxpick.js", "ei-animlib-ui.js"]


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def build():
    html = read("ui.base.html")
    css = read("asistan_panel.css")
    card = read("asistan_panel.html")
    panel_js = read("asistan_panel.js")

    runtime = []
    for name in ORDER:
        with open(os.path.join(RUNTIME, name), encoding="utf-8") as fh:
            src = fh.read()
        if "</script" in src.lower():
            raise RuntimeError("%s içinde </script> var" % name)
        runtime.append("// ---- %s ----\n%s" % (name, src))
    runtime_block = ("<script>\n/* EasyImport asistan çalışma zamanı — assistant/runtime/js (build_ui.py gömer) */\n"
                     + "\n".join(runtime) + "\n</script>\n")

    def once(s, a, b):
        assert s.count(a) == 1, (s.count(a), a[:60])
        return s.replace(a, b, 1)

    html = once(html, "</style>", css + "</style>")
    lines = html.split("\n")
    idx = [i for i, ln in enumerate(lines) if ln.startswith('  <div id="asist"')]
    assert len(idx) == 1, idx
    lines.insert(idx[0] + 1, card.rstrip("\n"))
    html = "\n".join(lines)

    main_open = html.index("\n<script>\n") + 1
    html = html[:main_open] + runtime_block + html[main_open:]

    last_close = html.rindex("</script>")
    html = html[:last_close] + panel_js + html[last_close:]

    html = once(html, "    if (m.type === 'progress') setStatus(m.message);",
                "    if (m.type === 'progress') setStatus(m.message);\n"
                "    if (m.type === 'learn-state') AS.applyLearn(m.text);")
    html = once(html, "      $('dl-train').style.display = lastTrainStr ? '' : 'none';",
                "      $('dl-train').style.display = lastTrainStr ? '' : 'none';\n"
                "      AS.show(lastDoc);")

    if not html.lstrip().lower().startswith("<meta charset"):
        html = '<meta charset="utf-8">\n' + html   # tarayıcı UTF-8 çözsün (Türkçe karakterler bozulmasın)
    with open(os.path.join(HERE, "ui.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print("[OK] ui.html üretildi (%d bayt, runtime %d dosya)" % (len(html.encode("utf-8")), len(ORDER)))


if __name__ == "__main__":
    sys.exit(build())
