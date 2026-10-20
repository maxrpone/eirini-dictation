# Build the game page. Run on the Mac: python3 src/build2.py <audio2.json> <fonts dir> <out dir>
import json, base64, io, html, sys, os
from fontTools import subset
from fontTools.ttLib import TTFont

SRC = os.path.dirname(os.path.abspath(__file__))
AUDIO, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
tpl = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
items = json.load(open(os.path.join(SRC, "items2.json"), encoding="utf-8"))
audio = json.load(open(AUDIO, encoding="utf-8"))
missing = [i["id"] for i in items if i["id"] not in audio]
assert not missing, missing

def sub(path, text):
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
    f = TTFont(path); s = subset.Subsetter(opts); s.populate(text=text); s.subset(f)
    b = io.BytesIO(); f.flavor = "woff2"; f.save(b); return base64.b64encode(b.getvalue()).decode()

alltext = tpl + "".join(i["text"] for i in items) + "０１２３４５６７８９？"
cjk = "".join(sorted(set(ch for ch in alltext if ord(ch) > 0x2E7F))) + "0123456789 ·/"
latin = "".join(chr(c) for c in range(32, 127)) + "·–’“”"
fonts = ("@font-face{font-family:'WenKai';src:url(data:font/woff2;base64,%s) format('woff2');font-display:block}\n" % sub(os.path.join(FONTS, "WenKai.ttf"), cjk)
         + "@font-face{font-family:'Fredoka';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:300 700;font-display:swap}\n" % sub(os.path.join(FONTS, "Fredoka.ttf"), latin))

align = {k: {"chars": v["chars"], "start": [round(x, 3) for x in v["start"]], "end": [round(x, 3) for x in v["end"]]} for k, v in audio.items() if k in {i["id"] for i in items}}
# The no-JavaScript backup lists the normal-speed dictation items and the idiom sentences.
main = [i for i in items if not i["id"].endswith("_s") and (i["id"][0] in "wpx" or (i["id"][0] == "s" and i["id"][1:3].isdigit()))]
mainids = {i["id"] for i in main}
nojs = ['<div class="nj" data-id="%s"><audio controls preload="none" src="data:audio/mpeg;base64,%s"></audio><details><summary>答案</summary><p style="font-size:24px">%s</p></details></div>'
        % (i["id"], audio[i["id"]]["b64"], html.escape(i["text"])) for i in main]
extra = {i["id"]: audio[i["id"]]["b64"] for i in items if i["id"] not in mainids}

out = (tpl.replace("/*__FONTS__*/", fonts)
          .replace("/*__ALIGN__*/{}", json.dumps(align, ensure_ascii=False, separators=(",", ":")))
          .replace("/*__EXTRA__*/{}", json.dumps(extra, separators=(",", ":")))
          .replace("<!--__NOJS__-->", "\n".join(nojs)))
assert "__" not in out.split("<script>")[-1][:200]
open(os.path.join(OUT, "artifact.html"), "w", encoding="utf-8").write(out)

head = ('<!doctype html>\n<html lang="zh-HK">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-title" content="默書飛行">\n<meta name="theme-color" content="#111838">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icon-180.png">\n<link rel="icon" href="icon-180.png">\n')
full = head + out.replace('<script>document.documentElement', '</head>\n<body>\n<script>document.documentElement', 1)
full = full.replace("<style>", "<style>\nbody{margin:0}", 1)
standalone = full + "\n</body>\n</html>\n"
open(os.path.join(OUT, "Eirini-Dictation-Flight.html"), "w", encoding="utf-8").write(standalone.replace('<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icon-180.png">\n<link rel="icon" href="icon-180.png">\n', ''))
sw = "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('sw.js').catch(function(){});}</script>\n"
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(full + sw + "</body>\n</html>\n")
print("cjk", len(cjk), "artifact", len(out), "index", len(full))
