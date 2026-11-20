#!/usr/bin/env python3
"""把好幾個審片台資料夾（make_board.py 的輸出）組成一個有首頁的審片網站，輸出到 cloud/site/，再部署 cloud/ 這個資料夾。

用法：python3 build_site.py [boards.json] [--out site]      （boards.json 預設是這個檔案旁邊的 boards.json）

boards.json 範例（路徑相對於 boards.json 所在的資料夾）：
{
  "site_title": "審片網站",
  "intro": "點要審的影片。意見存在這個網站，換手機或電腦都看得到。",
  "agent": "AI",
  "redact_notes": ["餘額"],
  "episodes": [
    {"id": "demo", "no": "第 1 支", "title": "範例影片", "boards": [
      {"key": "post", "label": "成片 v1", "src": "../review_demo", "html": "index.html", "what": "看片、留意見。"}
    ]}
  ]
}
- 審片台的名稱（存意見的鍵）＝「id-key」，只能用小寫英文、數字、減號，最長 40 字。
- agent：首頁文字裡「傳給 ○○」的名稱；每個審片台自己的按鈕名稱由 make_board.py 的 --agent 決定。
- redact_notes（選填）：含這些字的「提案備註」（D.notes）不放上公開網站。
"""
import html, json, os, re, shutil, sys

BOARD = re.compile(r"^[a-z0-9-]{1,40}$")
FORM = '<form name="review" method="POST" data-netlify="true" hidden><input name="board"><input name="sent"><textarea name="summary"></textarea><textarea name="payload"></textarea></form>'
HOME = '''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,nofollow">
<title>__TITLE__</title>
<link rel="icon" href="data:,">
<style>
:root{color-scheme:dark;--bg:#0b0f14;--panel:#131a22;--panel2:#1a232e;--line:#2a3644;--fg:#e8edf2;--dim:#93a1b0;--accent:#ffd166;--ok:#4ccf8e}
[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 "Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-right,0px)) 48px max(16px,env(safe-area-inset-left,0px))}
h1{font-size:22px;margin:0 0 4px} .sub{color:var(--dim);margin:0 0 22px}
.ep{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
.ep h2{font-size:17px;margin:0 0 10px} .ep h2 span{color:var(--accent);margin-right:8px}
a.b{display:block;text-decoration:none;color:var(--fg);background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-top:8px}
a.b:hover,a.b:focus-visible{border-color:var(--accent);outline:none} a.b b{font-size:15.5px} a.b .w{color:var(--dim);font-size:13px;margin-top:2px}
a.b .st{margin-top:6px;font-size:13px;color:var(--accent)} a.b .st.sent{color:var(--ok)}
</style></head><body>
<main><h1 id="h"></h1><p class="sub" id="intro"></p><div id="eps"></div></main>
<script>
const CFG = __CFG__, EPS = CFG.eps, AG = CFG.agent, box = document.getElementById('eps'), el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
document.getElementById('h').textContent = CFG.title; document.getElementById('intro').textContent = CFG.intro;
EPS.forEach(ep => { const d = el('section', 'ep'), h = el('h2'); if (ep.no !== '' && ep.no != null) h.appendChild(el('span', '', String(ep.no))); h.appendChild(document.createTextNode(ep.title)); d.appendChild(h);
  ep.boards.forEach(b => { const a = el('a', 'b'); a.href = b.href; a.appendChild(el('b', '', b.label)); a.appendChild(el('div', 'w', b.what)); const st = el('div', 'st', '讀取中…'); a.appendChild(st); d.appendChild(a);
    fetch('/api/store?b=' + b.board, { cache: 'no-store' }).then(r => r.json()).then(s => { const cs = Object.values(s.comments || {}), sent = s.meta && s.meta.sent, ap = Object.keys(s.approvals || {}).length;
      const newer = sent ? cs.filter(c => c.at > sent.at).length : cs.length; let t = cs.length ? '已寫了 ' + cs.length + ' 則意見' : '還沒有意見'; if (ap) t += '，核准 ' + ap + ' 項';
      if (sent) t += newer ? '；其中 ' + newer + ' 則還沒傳給 ' + AG : '；已全部傳給 ' + AG; else if (cs.length || ap) t += '；還沒傳給 ' + AG;
      st.textContent = t; if (sent && !newer) st.className = 'st sent'; }).catch(() => { st.textContent = ''; }); });
  box.appendChild(d); });
</script></body></html>'''


def die(msg):
    print("錯誤：" + msg, file=sys.stderr)
    sys.exit(1)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    out_name = argv[argv.index("--out") + 1] if "--out" in argv else "site"
    if "--out" in argv:
        args.remove(out_name)
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(args[0]) if args else os.path.join(here, "boards.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        die("讀不了設定檔 %s：%s" % (cfg_path, e))
    base = os.path.dirname(cfg_path)
    site = os.path.abspath(os.path.join(here, out_name))
    eps_cfg = cfg.get("episodes")
    if not isinstance(eps_cfg, list) or not eps_cfg:
        die("boards.json 要有 episodes（陣列，至少一支影片）。")
    agent = cfg.get("agent") or "AI"
    redact = cfg.get("redact_notes") or []
    mark = os.path.join(site, ".review-desk-site")
    if os.path.isdir(site) and os.listdir(site):
        if not os.path.exists(mark):
            die("site/ 裡有不是這支程式產生的檔案，請先把 site/ 移走再重跑。")
        shutil.rmtree(site)   # 只清自己上次產生的：從 boards.json 拿掉的審片台才不會留在網站上繼續公開
    os.makedirs(site, exist_ok=True)
    open(mark, "w").close()
    cards, seen = [], set()
    for ep in eps_cfg:
        if not isinstance(ep, dict) or not ep.get("id") or not ep.get("boards"):
            die("每個 episode 要有 id 和 boards。")
        boards_out = []
        for b in ep["boards"]:
            board = "%s-%s" % (ep["id"], b.get("key"))
            if not BOARD.match(board):
                die("審片台名稱「%s」不合規定：只能用小寫英文、數字、減號，最長 40 字（id-key）。" % board)
            if board in seen:
                die("審片台名稱重複：" + board)
            seen.add(board)
            src_dir = os.path.normpath(os.path.join(base, b.get("src", "")))
            page = os.path.join(src_dir, b.get("html", "index.html"))
            if not os.path.isfile(page):
                die("找不到審片台頁面：" + page)
            with open(page, encoding="utf-8") as f:
                s = f.read()
            if s.count("const D = {") != 1 or "<body>" not in s or '<meta charset="utf-8">' not in s:
                die("%s 不是 make_board.py 做的審片台頁面（找不到 const D = {、charset 或 <body>）。" % page)
            nav = [{"label": "← 全部影片", "href": "/"}] + [{"label": x.get("label", x.get("key")), "href": "/%s/%s/" % (ep["id"], x.get("key")), "on": x is b} for x in ep["boards"]]
            extra = {"pub": True, "direct": True, "board": board, "nav": nav, "mbase": ""}
            s = s.replace("const D = {", "const D = {" + json.dumps(extra, ensure_ascii=False)[1:-1] + ",", 1)
            m = re.search(r'"notes":(\[.*?\])[,}]', s)
            if m and redact:
                keep = [n for n in json.loads(m.group(1)) if not any(w in n for w in redact)]
                s = s.replace(m.group(1), json.dumps(keep, ensure_ascii=False, separators=(",", ":")), 1)
            for w in redact:
                assert w not in s, "%s 還有含「%s」的內容，請從頁面資料拿掉" % (board, w)
            s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">', 1).replace("<body>", "<body>\n" + FORM, 1)   # 表單要在靜態 HTML 裡，Netlify 才認得
            out = os.path.join(site, ep["id"], b["key"])
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
                f.write(s)
            for fn in os.listdir(src_dir):
                if fn.endswith((".mp4", ".jpg")):
                    shutil.copy2(os.path.join(src_dir, fn), os.path.join(out, fn))
            print(board, len(os.listdir(out)), "個檔")
            boards_out.append({"board": board, "href": "/%s/%s/" % (ep["id"], b["key"]), "label": b.get("label", b["key"]), "what": b.get("what", "")})
        cards.append({"no": ep.get("no", ""), "title": ep.get("title", ep["id"]), "boards": boards_out})
    title = cfg.get("site_title") or "審片網站"
    page = HOME.replace("__TITLE__", html.escape(title)).replace("__CFG__", json.dumps({"title": title, "agent": agent, "eps": cards, "intro": cfg.get("intro") or "點要審的影片。意見存在這個網站，換手機或電腦都看得到；寫完在審片台按「傳給 %s」。" % agent}, ensure_ascii=False).replace("</", "<\\/"))
    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(site, "_headers"), "w", encoding="utf-8") as f:
        f.write("/*\n  X-Robots-Tag: noindex, nofollow\n")
    with open(os.path.join(site, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nDisallow: /\n")
    print("完成：" + site)


if __name__ == "__main__":
    main(sys.argv[1:])
