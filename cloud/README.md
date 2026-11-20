# 審片台雲端版（選用）

[English: README.en.md](README.en.md)

本機版（`scripts/make_board.py` 做出來的資料夾）不需要這一包：意見存在瀏覽器，用「複製全部意見」貼給 AI 就能用。
只有在你想要「一個固定網址、換手機或電腦意見都在、AI 能自己讀到意見」時，才用這一包。它把好幾個審片台組成一個有首頁的網站，意見存在 Netlify Blobs。

## 檔案

| 檔案 | 用途 |
|---|---|
| `build_site.py` | 讀 `boards.json`，把各審片台資料夾組成 `site/`（首頁＋每個審片台＋注入雲端模式設定與表單） |
| `boards.example.json` | 設定檔範例，複製成 `boards.json` 再改 |
| `netlify/functions/store.mjs` | 意見後台：`/api/store`，每個審片台一份 JSON |
| `netlify.toml`、`package.json` | Netlify 設定；後台函式需要 `@netlify/blobs` |

## 步驟

1. 先用 `scripts/make_board.py` 為每支影片做好審片台資料夾（`--agent` 決定按鈕叫「傳給 ○○」）。
2. `cp boards.example.json boards.json`，改成你的影片。路徑相對於 `boards.json`。審片台名稱＝`id-key`，只能用小寫英文、數字、減號，最長 40 字（它是意見儲存的鍵，也是網址的一部分）。
3. 在 `cloud/` 裡執行 `python3 build_site.py`，產生 `site/`。每次執行會先清掉上一次產生的 `site/` 再重建，所以從 `boards.json` 拿掉的審片台不會留在網站上。範例設定的 `src` 是 `../review_demo`：要先在上一層照 README「先玩示範片」做出那個資料夾。
4. 部署（需要你自己的 Netlify 帳號；這包不含任何帳號、站台代號）：
   ```
   cd cloud
   npm install                       # 命令列部署前一定要先做，不然後台函式找不到 @netlify/blobs，存意見會壞
   npx netlify-cli login             # 第一次
   npx netlify-cli deploy --prod --dir site
   ```
   第一次會問你要連結或建立哪個站台。
5. 驗證（不要只看指令的結束碼）：
   - `curl -s https://<你的網址>/api/store?b=<id-key>` 要回 JSON：`{"comments":{},"approvals":{},"choices":{},"meta":{}}`。
   - 開首頁，每個審片台卡片出現，點進去影片播得出來。
   - 手機寬度重新載入一次，瀏覽器主控台的錯誤要是 0。

## 密碼

這包**不設密碼**。要保護請你自己在 Netlify 後台設（專案 → Project configuration → Access & security → Visitor access → Password Protection；該功能適用哪些方案，以 Netlify 當時的說明為準）。
沒設密碼之前，拿到網址的人都看得到未公開的片，也能寫入意見。`build_site.py` 只加了不讓搜尋引擎收錄（`robots.txt`、`_headers`、meta）。

## AI 怎麼讀意見

- 沒設密碼：`GET /api/store?b=<id-key>`，回傳整份 JSON（`comments`、`approvals`、`choices`、`meta`，格式見 `references/data-format.md`）。
- 有設密碼：AI 打不開網頁，只能讀 Netlify 表單。審片的人按「傳給 ○○」會送出一筆表單（表單名 `review`，欄位 `board`、`sent`、`summary`、`payload`；`summary` 是意見文字、`payload` 是整份 JSON）。到 Netlify 後台 Forms 看，或用 Netlify API／連接器讀。
- **沒設密碼時，核准不可信**：拿到網址的人都能寫入後台，包括寫入一筆「整版核准」。AI 讀到 `approvals` 時，除非網站有密碼保護，否則要回對話跟審片的人確認。
- 表單**不會叫醒 AI**：審片的人傳完要回對話說一聲，或由 AI 定時查看。
- AI 處理完可以寫回（沒密碼時）：`POST /api/store`，body `{"b":"<id-key>","op":"merge","c":"comments","id":"<意見 id>","d":{"done":true,"reply":"已改"}}`，審片台會顯示「✓ 已處理」和 AI 的回覆。

## 踩過的坑

- 命令列部署前沒 `npm install`：網站看起來正常，但 `/api/store` 壞掉，意見存不進去。
- 部署指令常回「fetch failed」，但其實可能已經上傳成功（網站大時更常見）。每次失敗後**先實際打線上網址確認**是不是新版，不要只看結束碼；真的沒上傳再重試。
- 網站大（影片多）時用命令列部署比連接器穩。
- 雲端模式的頁面要有靜態的 `<form name="review" data-netlify="true">`，Netlify 才認得表單；`build_site.py` 已經替每個頁面加好，不要手動把它拿掉。
- 後台是單人使用：兩個人同時改同一則意見，後寫的蓋掉先寫的。每則意見上限約 8000 字元，整份上限約 400KB。
- 換版本請在 `make_board.py` 用新的 `--ver`：整版核准記著版本名，版本名不同就不算核准。注意雲端的意見檔是依審片台名稱（`id-key`）存的，同一個審片台換版本時，舊意見仍會留在清單裡（每則有 `ver` 欄位可以分辨）；想從頭開始就用新的 `id-key`。
- 雲端頁面的意見每 30 秒自動同步一次；另一台裝置寫的，最多等 30 秒才出現。
