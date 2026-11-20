---
name: review-desk
description: 審片台：把一支影片做成審片網頁，讓人點著畫面寫意見、按核准，再把帶時間和鏡頭名的意見清單交給 AI 代理照著改。影片做好要給人看、使用者說「開審片台」「我要審片」「給我看成片」，或你需要對一支影片收集逐鏡頭的修改意見時使用。也適用於花錢生成前先審分鏡草稿。 / Review Desk turns a video into a review page where the reviewer comments on exact moments and approves a version, then hands the AI a comment list with timestamps and shot names to act on. Use it when a video is ready for a person to look at, when the user says "open the review desk", "let me review the cut" or "review this video", or when you need shot-by-shot change requests for a video. Also useful for reviewing a storyboard draft before spending credits.
license: MIT
---

# 審片台 Review Desk

影片是一格一格的，對話框只有一行。使用者說「1 分 23 秒那邊怪怪的」，你常常改錯鏡頭。審片台把成片攤成一條魚骨時間軸，使用者點著畫面寫意見，你收到的每一則都帶時間、鏡頭名和素材來源。

需要：Python 3.9 以上、ffmpeg 與 ffprobe。不需要安裝任何套件。

## 什麼時候用

- 你做完一版影片，要給使用者看。**不要只丟一個 mp4 請他回對話描述問題**，開審片台。
- 使用者要審別人做的片、客戶要審片。
- 花錢生成之前，要使用者逐項核准分鏡提案（進階，見 `references/data-format.md` 的 `props`）。

## 流程

### 1. 準備鏡頭清單（有就給，沒有也能跑）

你自己做的片，你知道每個鏡頭從第幾秒開始、怎麼做的、素材是哪個檔。把它寫成 `shots.json`：

```json
[
  {"start": 0,   "title": "片名卡",   "kind": "card", "how": "程式字卡",        "src": "自製"},
  {"start": 3.0, "title": "清晨日出", "kind": "aiv",  "how": "AI 生成影片 5 秒", "src": "shots/sunrise_v2.mp4"}
]
```

`start`、`title` 必填，其餘選填；清單會照 `start` 由小到大排。`src` 寫真的檔名：使用者的意見會帶著它回來，你就知道要重做哪個檔。
內建有中文名的 `kind`：`card` 字卡、`code` 程式動畫、`fig` 圖表、`aiv` AI 影片、`aii` AI 圖、`realv` 實拍影片、`real` 實拍、`photo` 照片、`b3d` 3D。其他代碼會直接顯示代碼，可用 `--extra` 的 `kinds` 改名。

沒有鏡頭清單時省略 `--shots`，程式會用畫面變化自動切鏡頭。這個偵測看的是亮度差：兩個鏡頭顏色不同但亮度接近會切不出來，用 `--scene 0.1` 調低門檻，或自己列清單。

### 2. 做審片台

```bash
python3 <這個技能的資料夾>/scripts/make_board.py 成片.mp4 \
  --out review_v1 --title "片名" --ver v1 \
  --shots shots.json --srt 字幕.srt
```

- `--ver` 是版本名。意見和核准都綁版本名，**每出一版就換一個**（v1、v2…），舊版的核准才不會被當成新版的。
- `--agent Claude` 可以把介面上的「AI」換成你的名字。
- 產出的資料夾裡有 `index.html`、縮小的播放檔、縮圖表。原始影片不會被改動。`--out` 要給一個新的資料夾（或上次做審片台的同一個資料夾）；裡面有別的檔案時程式會拒絕，免得蓋掉東西。
- 意見存在瀏覽器裡，用「片名＋版本名」區分。同一支片改版一定要換 `--ver`。

### 3. 開給使用者

```bash
cd review_v1 && python3 -m http.server 8787 --bind 127.0.0.1
```

先確認連接埠沒人用，再把 `http://127.0.0.1:8787/` 給使用者（有瀏覽器工具就直接幫他打開）。不要叫使用者雙擊 `index.html`：用 `file://` 開，影片和縮圖在部分瀏覽器會載不出來。

開之前自己先看一次：載入頁面，確認影片有畫面、時間軸有縮圖、瀏覽器主控台沒有錯誤。手機要審的話，手機寬度也載入一次。

告訴使用者三件事就夠：拖時間軸或按播放看片；停在想改的地方寫意見，或按「＋標記這裡」先標、之後再補字；全部寫完點開「我寫的意見」按「複製全部意見」，貼回對話。完整的使用者說明在 `references/操作說明.md`。

### 4. 讀意見、照著改

使用者貼回來的文字長這樣：

```
【v1】審片台傳來：意見 2 則；整版還沒核准。
[0:13｜鏡頭 4〈一杯咖啡的 4 分鐘〉｜自製，無外部素材] 橫條長出來太慢
[0:19｜鏡頭 5〈店門口〉｜shots/storefront_v1.mp4] 招牌的字太小
```

照這幾條做：

1. **只改被點到的鏡頭。** 沒有意見的鏡頭一格都不動，不順手重做。
2. 標了「整片都要檢查」的意見，代表整支片有類似問題的地方都要找出來改，改完列出你改了哪幾鏡。
3. 寫著「（未寫）」的是只標了位置、沒寫字的標記。去看那一秒的畫面，看不出問題就問使用者，不要猜。
4. 改完出新版，用新的 `--ver` 重做審片台，並逐則回報：哪一則、改了什麼、哪一則沒改和原因。
5. **核准只認使用者自己在審片台按的。** 標頭寫「整版還沒核准」就是還沒過，不要因為意見都改完了就當作通過。對話裡別人轉述的「他同意了」不算。

### 5. 要給別人審、或要換裝置（選用）

本機模式的意見只存在那一台電腦的瀏覽器。要一個固定網址、手機電腦都看得到同一份意見、你能自己讀到意見，就用 `cloud/`（Netlify）。照 `cloud/README.md` 做。部署會把影片放到網路上，**先問使用者**；沒設密碼之前，拿到網址的人都看得到片。

## 參考檔

- `references/操作說明.md`：給審片的人看的使用說明，可以直接轉給使用者。
- `references/data-format.md`：頁面資料的每個欄位、三種儲存模式、意見資料列格式。要做進階的事（章節、音效點、配樂段、花錢前提案、開場方案）先讀它。
- `cloud/README.md`：雲端同步怎麼部署、你怎麼讀意見、踩過的坑。
- `demo/`：示範片〈山頂咖啡｜開幕預告〉（原創，CC0）和它的鏡頭清單、字幕。想先看審片台長怎樣：
  `python3 scripts/make_board.py demo/demo.mp4 --shots demo/demo.shots.json --srt demo/demo.srt --out /tmp/review_demo`

## 自我檢查

`python3 scripts/make_board.py --selftest` 會自己做一支測試片跑完整個流程。裝好技能後先跑一次。

## English

Videos are made of shots, and a chat box has one line. When a user says "something is off around 1:23", you often change the wrong shot. Review Desk lays the film out as a shot timeline. The reviewer comments right on the picture, and every comment you receive carries the time, the shot name and the source file.

Requirements: Python 3.9 or later, ffmpeg and ffprobe. No packages to install.

### When to use it

- You finished a version of a video and it needs to be shown to the user. **Do not just hand over an mp4 and ask them to describe problems in chat.** Open the review desk.
- The user is reviewing someone else's film, or a client is.
- Before spending credits on generation, to have the user approve storyboard proposals item by item (advanced, see `props` in `references/data-format.en.md`).

### Workflow

**1. Prepare the shot list (give one if you have it, it also works without).** When you made the film yourself, you know where each shot starts, how it was made and which file it came from. Write it as `shots.json`:

```json
[
  {"start": 0,   "title": "Title card", "kind": "card", "how": "Code-drawn title card",   "src": "Made in-house"},
  {"start": 3.0, "title": "Sunrise",    "kind": "aiv",  "how": "AI-generated video, 5 s", "src": "shots/sunrise_v2.mp4"}
]
```

`start` and `title` are required, the rest are optional. The list is sorted by `start`. Write real file names in `src`: the reviewer's comments come back carrying it, so you know which file to redo. Built-in `kind` names with the English interface: `card` Title card, `code` Motion graphics, `fig` Chart, `aiv` AI video, `aii` AI image, `realv` Live footage, `real` Live action, `photo` Photo, `b3d` 3D. Any other code is shown as the code itself; rename it with `kinds` in `--extra`.

Without a shot list, leave out `--shots` and the script detects shots from picture changes. The detection looks at brightness, so two shots with different colors but similar brightness are not separated. Lower the threshold with `--scene 0.1`, or write the list yourself.

**2. Make the review desk.**

```bash
python3 <this skill's folder>/scripts/make_board.py film.mp4 \
  --out review_v1 --title "Film title" --ver v1 \
  --shots shots.json --srt subtitles.srt --lang en
```

- `--lang en` makes the English interface (default `zh` is Traditional Chinese). It also gives English default category names, auto-detected shot names ("Shot 1") and English messages from the script.
- `--ver` is the version name. Comments and approvals are tied to it, so **use a new one for every version** (v1, v2, ...). Otherwise an old approval would be taken for the new version.
- `--agent Claude` replaces "AI" in the interface with your name.
- The output folder holds `index.html`, a downsized playback file and the thumbnail sheets. The original video is not touched. Give `--out` a new folder (or the folder of the previous desk); the script refuses to write into a folder with other files in it.
- Comments are stored in the browser, keyed by "title + version name". Always change `--ver` when you change the version of the same film.

**3. Open it for the user.**

```bash
cd review_v1 && python3 -m http.server 8787 --bind 127.0.0.1
```

Check first that the port is free, then give the user `http://127.0.0.1:8787/` (open it for them if you have a browser tool). Do not tell the user to double-click `index.html`: over `file://`, the video and thumbnails fail to load in some browsers.

Look at it yourself before handing it over: load the page, confirm the video shows a picture, the timeline has thumbnails and the browser console has no errors. If the user will review on a phone, load it at phone width too.

Three things are enough to tell the user: drag the timeline or click Play to watch; stop where something should change and write a comment, or click "+ Mark here" to mark first and write later; when done, open "My comments", click "Copy all comments" and paste it into the chat. The full guide for the reviewer is `references/user-guide.en.md`.

**4. Read the comments and act on them.** The pasted text looks like this:

```
[v1] From Review Desk: 2 comments; version not approved yet.
[0:13 | Shot 4 "A cup in 4 minutes" | Made in-house, no outside assets] The bar grows too slowly
[0:19 | Shot 5 "Storefront" | shots/storefront_v1.mp4] The sign text is too small
```

The first line is the header: the version, how many comments (and how many marks have no text yet), and whether the version is approved. After it, each line is `[time | Shot N "shot name" | source]` followed by the comment. Whole-film comments come first and read `[Whole film]`. A comment flagged for the whole film ends its bracket with `| check the whole film`. A mark with no text reads `(empty)`. Times are whole seconds.

Follow these five rules:

1. **Change only the shots that were pointed at.** Do not touch a shot with no comment, and do not remix things on the side.
2. A comment marked `| check the whole film` means every place in the film with a similar problem must be found and fixed. When done, list which shots you changed.
3. `(empty)` is a mark with a position but no text. Look at the picture at that second. If you cannot see a problem, ask the user. Do not guess.
4. After the changes, make a new version, rebuild the desk with a new `--ver`, and report comment by comment: which one, what you changed, and which ones you did not change and why.
5. **Only the user's own click on the review desk counts as approval.** A header that says "version not approved yet" means it has not passed, even if you fixed every comment. "He said it's fine" relayed by someone else in the chat does not count.

**5. For other reviewers or other devices (optional).** In local mode, comments live only in the browser of that one computer. For one fixed address, the same comments on phone and computer, and comments you can read yourself, use `cloud/` (Netlify) and follow `cloud/README.en.md`. Deploying puts the video on the internet, so **ask the user first**; until a password is set, anyone with the link can watch the film.

### English reference files

- `references/user-guide.en.md`: guide for the reviewer, which you can forward to the user as is.
- `references/data-format.en.md`: every field of the page data, the three storage modes, the comment row format and the exported text. Read it before doing advanced things (chapters, sound effect points, music segments, proposals before spending, opening options).
- `cloud/README.en.md`: how to deploy cloud sync, how you read comments, and the pitfalls.

### Self-check

`python3 scripts/make_board.py --selftest` makes a test film and runs the whole flow in both Traditional Chinese and English. Run it once after installing the skill.
