#!/usr/bin/env python3
"""審片台產生器：把一支影片做成「魚骨時間軸」審片網頁（單一資料夾，雙擊 index.html 或用 http.server 開）。

只用 Python 標準函式庫＋系統的 ffmpeg／ffprobe。

用法：
  python3 make_board.py 影片.mp4 [--out 資料夾] [--title 片名] [--ver 版本名] [--shots shots.json]
                        [--srt 字幕.srt] [--extra extra.json] [--agent 名稱] [--scene 0.3] [--lang zh|en]
  python3 make_board.py --selftest [--out 資料夾]     # 自己做一支測試片跑完整流程並檢查（zh 和 en 都跑）
  --lang en 做英文介面的審片台（English UI; messages, default names and the page template are all English）
"""
import argparse, array, html, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TPLS = {"zh": os.path.join(HERE, "..", "assets", "page.tpl.html"), "en": os.path.join(HERE, "..", "assets", "page.tpl.en.html")}
LANG = "zh"                      # 介面語言，由 --lang 設定（build() 會依參數設定）；T() 依它挑訊息
SHEET = 150                      # 每張縮圖表 150 格（15 x 10），每格 1 秒；模板的 thumb() 寫死這個規格
CSSK = ["aiv", "aii", "realv", "real", "fig", "photo", "b3d", "bvid", "code", "card", "warn"]   # 模板 CSS 內建顏色的類別代碼
# 常見類別代碼的中文名；沒列到的代碼直接顯示代碼本身，可用 --extra 的 kinds 改名
NAMES = {"shot": "鏡頭", "card": "字卡", "code": "程式動畫", "fig": "圖表", "aiv": "AI 影片", "aii": "AI 圖", "realv": "實拍影片", "real": "實拍", "photo": "照片", "b3d": "3D"}
NAMES_EN = {"shot": "Shot", "card": "Title card", "code": "Motion graphics", "fig": "Chart", "aiv": "AI video", "aii": "AI image", "realv": "Live footage", "real": "Live action", "photo": "Photo", "b3d": "3D"}
PALETTE = ["#5fb4e8", "#ff9ac4", "#2fe0a0", "#f0b545", "#b18cff", "#ff8a3d", "#38c7c0", "#ff7b6b"]


def T(zh, en):
    return en if LANG == "en" else zh


def die(msg):
    print(T("錯誤：", "Error: ") + msg, file=sys.stderr)
    sys.exit(1)


def need_tools():
    for t in ("ffmpeg", "ffprobe"):
        if not shutil.which(t):
            die(T("找不到 %s。請先安裝 ffmpeg（macOS：brew install ffmpeg）。", "Cannot find %s. Install ffmpeg first (macOS: brew install ffmpeg).") % t)


def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=True, check=False)   # stdout 和 stderr 都收下來；失敗時印 stderr 尾端
    if r.returncode != 0:
        die(T("ffmpeg 執行失敗：%s\n%s", "ffmpeg failed: %s\n%s") % (" ".join(cmd[:6]) + " ...", r.stderr.decode("utf-8", "replace")[-600:]))
    return r


def probe(video):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", video], True)
    try:
        j = json.loads(r.stdout)
        total = round(float(j["format"]["duration"]), 2)
    except (ValueError, KeyError):
        die(T("讀不出影片長度，這個檔案可能不是影片：", "Cannot read the video length. This file may not be a video: ") + video)
    kinds = [s.get("codec_type") for s in j.get("streams", [])]
    if "video" not in kinds:
        die(T("這個檔案沒有影像軌：", "This file has no video track: ") + video)
    return total, "audio" in kinds


def detect_shots(video, thr, total):
    """ffmpeg 場景偵測；回傳切點秒數（含 0）。太近（<0.5 秒）的切點合併。"""
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", video, "-vf", "select='gt(scene,%s)',showinfo" % thr, "-an", "-f", "null", "-"],
                       capture_output=True, check=False)
    if r.returncode != 0:
        die(T("場景偵測失敗：", "Scene detection failed: ") + r.stderr.decode("utf-8", "replace")[-400:])
    cuts = [0.0]
    for m in re.finditer(r"pts_time:([\d.]+)", r.stderr.decode("utf-8", "replace")):
        t = float(m.group(1))
        if t - cuts[-1] >= 0.5 and total - t >= 0.5:
            cuts.append(round(t, 2))
    return cuts


def load_shots(path):
    try:
        with open(path, encoding="utf-8") as f:
            arr = json.load(f)
    except (OSError, ValueError) as e:
        die(T("讀不了 shots.json（%s）：%s", "Cannot read shots.json (%s): %s") % (path, e))
    if not isinstance(arr, list) or not arr:
        die(T("shots.json 必須是一個不是空的 JSON 陣列，每筆像 {\"start\": 0, \"title\": \"開場\"}。", "shots.json must be a non-empty JSON array, each entry like {\"start\": 0, \"title\": \"Opening\"}."))
    for i, s in enumerate(arr):
        if not isinstance(s, dict):
            die(T("shots.json 第 %d 筆不是物件。", "shots.json entry %d is not an object.") % (i + 1))
        if isinstance(s.get("start"), bool) or not isinstance(s.get("start"), (int, float)) or s["start"] < 0:
            die(T("shots.json 第 %d 筆的 start 必須是 0 以上的秒數（數字）。", "shots.json entry %d: start must be a number of seconds, 0 or more.") % (i + 1))
        if not isinstance(s.get("title"), str) or not s["title"].strip():
            die(T("shots.json 第 %d 筆缺少 title（鏡頭名，文字）。", "shots.json entry %d is missing title (the shot name, as text).") % (i + 1))
        for k in ("kind", "how", "src", "note"):
            if k in s and not isinstance(s[k], str):
                die(T("shots.json 第 %d 筆的 %s 必須是文字。", "shots.json entry %d: %s must be text.") % (i + 1, k))
    arr = sorted(arr, key=lambda s: s["start"])
    starts = [s["start"] for s in arr]
    if len(set(starts)) != len(starts):
        die(T("shots.json 有兩個鏡頭的 start 一樣。", "shots.json has two shots with the same start."))
    return arr


def parse_srt(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read()
    except (OSError, UnicodeDecodeError) as e:
        die(T("讀不了字幕檔（%s，請用 UTF-8 編碼）：%s", "Cannot read the subtitle file (%s, it must be UTF-8): %s") % (path, e))
    def sec(x):
        h, m, s = x.strip().replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    out = []
    for blk in re.split(r"\n\s*\n", raw.replace("\r\n", "\n").replace("\r", "\n").strip()):
        lines = [l for l in blk.split("\n") if l.strip() != ""]
        ti = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if ti is None:
            continue
        try:
            a, b = lines[ti].split("-->")
            b = b.split()[0] if b.split() else b
            out.append([round(sec(a), 2), round(sec(b), 2), " ".join(x.strip() for x in lines[ti + 1:])])
        except ValueError:
            die(T("字幕檔的時間格式看不懂：", "Cannot understand the subtitle timing: ") + lines[ti])
    return out


def waveform(video, total, has_audio):
    n = max(1, int(total * 4))                      # 每 0.25 秒一格
    if not has_audio:
        return [0] * n
    r = run(["ffmpeg", "-nostdin", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "4000", "-f", "s16le", "-"], True)
    pcm = array.array("h")
    pcm.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    if sys.byteorder == "big":
        pcm.byteswap()
    step = len(pcm) // n
    if step == 0:
        return [0] * n
    return [int(min(99, (sum(x * x for x in pcm[k * step:(k + 1) * step]) / step) ** 0.5 / 32768 * 400)) for k in range(n)]


def build(video, out, title, ver, shots_path, srt_path, extra_path, agent, scene, lang="zh"):
    global LANG
    LANG = lang
    need_tools()
    if not os.path.isfile(video):
        die(T("找不到影片檔：", "Video file not found: ") + video)
    extra = None
    if extra_path:
        try:
            with open(extra_path, encoding="utf-8") as f:
                extra = json.load(f)
        except (OSError, ValueError) as e:
            die(T("讀不了 extra.json（%s）：%s", "Cannot read extra.json (%s): %s") % (extra_path, e))
        if not isinstance(extra, dict):
            die(T("extra.json 必須是一個 JSON 物件。", "extra.json must be a JSON object."))
    shots = load_shots(shots_path) if shots_path else None
    subs = parse_srt(srt_path) if srt_path else []
    TPL = TPLS[lang]
    if not os.path.isfile(TPL):
        die(T("找不到模板：", "Template not found: ") + TPL)
    total, has_audio = probe(video)
    if total <= 0:
        die(T("影片長度是 0。", "The video length is 0."))

    if shots is None:
        cuts = detect_shots(video, scene, total)
        shots = [{"start": t, "title": T("鏡頭 %d", "Shot %d") % (i + 1)} for i, t in enumerate(cuts)]
    if shots[0]["start"] > 0:
        print(T("提醒：第一個鏡頭的 start 不是 0，已改成 0（時間軸要從頭涵蓋整支片）。", "Note: the first shot did not start at 0, so it was changed to 0 (the timeline has to cover the whole film)."))
        shots[0] = dict(shots[0], start=0)
    if any(s["start"] >= total for s in shots):
        die(T("shots.json 有鏡頭的 start 超過影片長度 %s 秒。", "shots.json has a shot whose start is past the video length of %s seconds.") % total)

    kinds, pic = {}, []
    for i, s in enumerate(shots):
        end = shots[i + 1]["start"] if i + 1 < len(shots) else total
        k = s.get("kind") or "shot"
        if k not in kinds:
            kinds[k] = [(NAMES_EN if lang == "en" else NAMES).get(k, k), T("（沒有填寫）", "(not filled in)"), T("（沒有填寫）", "(not filled in)"), PALETTE[len(kinds) % len(PALETTE)]]
        e = {"s": round(s["start"], 2), "d": round(end - s["start"], 2), "k": k, "t": s["title"].strip(), "b": i}
        for src_k, dst_k in (("how", "how"), ("src", "src"), ("note", "note")):
            if s.get(src_k):
                e[dst_k] = s[src_k]
        pic.append(e)

    mark = os.path.join(out, ".review-desk")   # 這個資料夾是審片台產物的記號；沒有記號又有別的檔案就不寫，免得蓋掉使用者的東西
    if os.path.exists(out) and not os.path.isdir(out):
        die(T("輸出位置 %s 是一個檔案，請用 --out 換一個資料夾名稱。", "The output path %s is a file. Use --out to pick a folder name.") % out)
    if os.path.isdir(out) and os.listdir(out) and not os.path.exists(mark):
        die(T("輸出資料夾 %s 裡已經有別的檔案。為了不蓋掉你的東西，請用 --out 換一個新的資料夾。", "The output folder %s already contains other files. To avoid overwriting your things, use --out to pick a new folder.") % out)
    os.makedirs(out, exist_ok=True)
    open(mark, "w").close()
    # 播放檔：短邊 480、整支一個檔（模板的 D.direct 模式，不分段）
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", video, "-vf", "scale=480:480:force_original_aspect_ratio=increase:force_divisible_by=2",
         "-c:v", "libx264", "-preset", "medium", "-b:v", "420k", "-maxrate", "560k", "-bufsize", "1100k", "-g", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ac", "1", "-b:a", "56k", "-movflags", "+faststart", os.path.join(out, "v0.mp4")])
    # 縮圖表：每秒一格，240x135（不是 16:9 的片子補黑邊），每 150 格一張 15x10 的 jpg
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", video, "-vf",
         "fps=1,scale=240:135:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=240:135:(ow-iw)/2:(oh-ih)/2,tile=15x10", "-q:v", "5", "-start_number", "0",
         os.path.join(out, "t%d.jpg")])
    want = -(-int(total + 0.999) // SHEET)
    if not all(os.path.isfile(os.path.join(out, "t%d.jpg" % k)) for k in range(want)):
        die(T("縮圖表沒有做完整（預期 %d 張）。", "The thumbnail sheets are incomplete (expected %d).") % want)

    data = {"title": title, "ver": ver, "total": total, "chunk": 100000, "direct": True, "agent": agent, "kinds": kinds,
            "chap": [], "pic": pic, "subs": subs, "vo": [[a, round(b - a, 2), t] for a, b, t in subs], "sfx": [], "music": [],
            "wave": waveform(video, total, has_audio)}
    if lang == "en":
        data["voLabel"] = "Narration / dialogue"
    if extra:
        extra = dict(extra)
        ek = extra.pop("kinds", None)           # kinds 是合併，不是整個蓋掉：沒列到的類別仍保留自動產生的
        if ek is not None:
            if not isinstance(ek, dict) or not all(isinstance(v, list) and len(v) >= 3 for v in ek.values()):
                die(T("extra.json 的 kinds 必須是 {\"代碼\": [名稱, 怎麼做的, 來源, 顏色(選填)]}。", "extra.json: kinds must be {\"code\": [name, how made, source, color (optional)]}."))
            for k, v in ek.items():
                v = list(v)
                if len(v) < 4 and k not in CSSK:    # 沒指定顏色、模板也沒有這個代碼的內建色：配一個，不然會全部灰色
                    v.append(PALETTE[len(kinds) % len(PALETTE)])
                kinds[k] = v
        data.update(extra)
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(TPL, encoding="utf-8") as f:
        tpl = f.read()
    if "__DATA__" not in tpl:
        die(T("模板裡找不到 __DATA__。", "__DATA__ not found in the template."))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", js, 1))
    if srt_path and not subs:
        print(T("提醒：字幕檔 %s 裡讀不到任何一句字幕（要是 SRT 格式、UTF-8 編碼）。", "Note: no subtitles could be read from %s (it must be SRT format, UTF-8 encoded).") % srt_path, file=sys.stderr)
    print(T("完成：%s（%s 秒、%d 個鏡頭、%d 句字幕、%s）", "Done: %s (%s seconds, %d shots, %d subtitle lines, %s)") % (os.path.join(out, "index.html"), total, len(pic), len(subs), T("有聲音", "with audio") if has_audio else T("沒有聲音軌", "no audio track")))
    return data


def extract_data(index_html):
    """從做好的 index.html 取回頁面資料 D（selftest 和別的程式都可以用）。"""
    with open(index_html, encoding="utf-8") as f:
        s = f.read()
    i = s.index("const D = ") + len("const D = ")
    return json.JSONDecoder().raw_decode(s[i:])[0]


CJK = re.compile("[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")   # 中日韓文字和全形標點


def selftest(out):
    need_tools()
    tmp = tempfile.mkdtemp(prefix="review-desk-selftest-")
    try:
        _selftest(out, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _selftest(out, tmp):
    mp4 = os.path.join(tmp, "t.mp4")
    def mk(path, audio):
        cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
        for c in ("red", "white", "blue"):   # 場景偵測看亮度，三色亮度要差很多（red 和 green 亮度幾乎一樣，會偵測不到）
            cmd += ["-f", "lavfi", "-i", "color=c=%s:s=320x180:r=25:d=4" % c]
        if audio:
            cmd += ["-f", "lavfi", "-i", "sine=f=440:d=12"]
        cmd += ["-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]"] + (["-map", "3:a", "-c:a", "aac"] if audio else ["-an"])
        run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", path])
    mk(mp4, True)
    d = build(mp4, out, "自測片", "selftest-v1", None, None, None, "AI", 0.3)
    for f in ("index.html", "v0.mp4", "t0.jpg"):
        assert os.path.isfile(os.path.join(out, f)), f + " 沒產生"
    d2 = extract_data(os.path.join(out, "index.html"))
    assert d2 == d and len(d2["pic"]) == 3, "鏡頭數應為 3，實際 %d" % len(d2["pic"])
    assert max(d2["wave"]) > 0, "有聲音的片子波形不該全 0"
    # 沒有聲音軌不能當掉
    mp4b = os.path.join(tmp, "n.mp4"); mk(mp4b, False)
    d3 = build(mp4b, os.path.join(tmp, "noaudio"), "無聲", "n-v1", None, None, None, "AI", 0.3)
    assert set(d3["wave"]) == {0} and len(d3["pic"]) == 3
    # 輸入錯誤要以非 0 結束
    for bad in (["不存在.mp4"], [mp4, "--shots", os.path.join(tmp, "nope.json")]):
        r = subprocess.run([sys.executable, os.path.abspath(__file__)] + bad + ["--out", os.path.join(tmp, "bad")], capture_output=True, text=True)
        assert r.returncode != 0 and "錯誤：" in r.stderr, (bad, r.returncode, r.stderr)
    # 英文版：同一支片用 --lang en 再做一次，預設名稱、訊息、模板都要是英文
    out_en = out.rstrip("/\\") + "_en"
    d4 = build(mp4, out_en, "Self-test film", "selftest-v1", None, None, None, "AI", 0.3, lang="en")
    assert [p["t"] for p in d4["pic"]] == ["Shot 1", "Shot 2", "Shot 3"] and d4["pic"][0]["k"] == "shot", d4["pic"]
    assert d4["kinds"]["shot"][:3] == ["Shot", "(not filled in)", "(not filled in)"] and d4["voLabel"] == "Narration / dialogue", d4["kinds"]
    assert extract_data(os.path.join(out_en, "index.html")) == d4 and "voLabel" not in d, "zh 的資料不該多出 voLabel"
    with open(os.path.join(out_en, "index.html"), encoding="utf-8") as f:
        page_en = f.read()
    assert '<html lang="en">' in page_en and "Review Desk" in page_en
    assert not CJK.search("\n".join(l for l in page_en.split("\n") if "const D = " not in l)), "英文審片台頁面（資料那一行以外）有中日韓文字"
    for bad in (["no-such.mp4"], [mp4, "--shots", os.path.join(tmp, "nope.json")]):
        r = subprocess.run([sys.executable, os.path.abspath(__file__)] + bad + ["--lang", "en", "--out", os.path.join(tmp, "bad")], capture_output=True, text=True)
        assert r.returncode != 0 and "Error: " in r.stderr and not CJK.search(r.stderr), (bad, r.returncode, r.stderr)
    # 兩份模板要保持一行對一行：英文模板不能有中日韓文字（資料那一行除外）、行數和 function 數量一樣，防止之後只改一邊
    with open(TPLS["zh"], encoding="utf-8") as f:
        zh_t = f.read()
    with open(TPLS["en"], encoding="utf-8") as f:
        en_t = f.read()
    assert not CJK.search("\n".join(l for l in en_t.split("\n") if "__DATA__" not in l)), "page.tpl.en.html 有中日韓文字"
    assert zh_t.count("\n") == en_t.count("\n"), "兩份模板行數不同：%d vs %d" % (zh_t.count("\n"), en_t.count("\n"))
    assert zh_t.count("function ") == en_t.count("function "), "兩份模板的 function 數量不同"
    for name, t in ((os.path.basename(TPLS["zh"]), zh_t), (os.path.basename(TPLS["en"]), en_t)):   # 網頁版（docs/app）用的是模板副本，要和 assets 一樣
        cp = os.path.join(HERE, "..", "docs", "app", name)
        if os.path.isfile(cp):
            with open(cp, encoding="utf-8") as f:
                assert f.read() == t, "docs/app/%s 和 assets 的模板不同，請重新複製：cp assets/page.tpl*.html docs/app/" % name
    print("selftest 通過（zh）：3 個鏡頭、波形有值、無聲片不當掉、錯誤輸入回非 0。輸出在 " + out)
    print("selftest passed (en): 3 shots, English names and messages, English template has no CJK text, both templates stay line-for-line. Output in " + out_en)


def main():
    ap = argparse.ArgumentParser(description="把影片做成審片台網頁")
    ap.add_argument("video", nargs="?", help="影片檔（mp4、mov 等 ffmpeg 讀得了的格式）")
    ap.add_argument("--out", help="輸出資料夾（預設：./review_<影片檔名>）")
    ap.add_argument("--title", help="片名（預設：影片檔名）")
    ap.add_argument("--ver", help="版本名；意見和核准都綁這個名字，改版請換一個（預設：<檔名>-v1）")
    ap.add_argument("--shots", help="shots.json：自己列鏡頭；沒給就用場景偵測")
    ap.add_argument("--srt", help="SRT 字幕檔（UTF-8）")
    ap.add_argument("--extra", help="extra.json：整個物件合併進頁面資料 D（kinds、hint、props、notes、chap…）")
    ap.add_argument("--agent", default="AI", help="介面上「傳給 ○○」的名稱（預設 AI）")
    ap.add_argument("--scene", type=float, default=0.3, help="場景偵測門檻 0~1，越小切越多（預設 0.3）")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh", help="審片台介面語言 zh 或 en（預設 zh）／UI language: zh or en (default zh)")
    ap.add_argument("--selftest", action="store_true", help="自己做一支測試片跑完整流程（zh 和 en 都跑）")
    a = ap.parse_args()
    global LANG
    LANG = a.lang
    if a.selftest:
        selftest(a.out or tempfile.mkdtemp(prefix="review-desk-out-"))
        return
    if not a.video:
        ap.error(T("請給影片檔，或用 --selftest", "give a video file, or use --selftest"))
    stem = os.path.splitext(os.path.basename(a.video))[0]
    if not 0 < a.scene < 1:
        die(T("--scene 要在 0 到 1 之間。", "--scene must be between 0 and 1."))
    build(a.video, a.out or "review_" + stem, a.title or stem, a.ver or stem + "-v1", a.shots, a.srt, a.extra, a.agent, a.scene, a.lang)


if __name__ == "__main__":
    main()
