# Review Desk page data `D` (for AI agents)

[繁體中文版：data-format.md](data-format.md)

`assets/page.tpl.html` (Traditional Chinese) and `assets/page.tpl.en.html` (English) each contain one line `const D = __DATA__;`. `scripts/make_board.py` fills in the JSON object described below, using the template picked by `--lang zh|en`.
The contents of `--extra extra.json` are merged into D with `dict.update` (a top-level key replaces the whole value), **with one exception: `kinds` is merged category by category**, and categories you do not list keep the automatically generated entry.
Every field below was checked against the template code. All times are in **seconds** (decimals allowed). The two templates share the same logic and field names; only the visible text differs. Where behavior depends on the language it is called out.

## Top-level fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `title` | string | No (default "Review Desk") | Film title, shown in the h1 (when there are no `props`, the tail " \| Review Desk" is appended in the English template; "｜審片台" in the Chinese one) and in the browser tab title |
| `ver` | string | **Yes** | Version name. Used by the local storage key prefix `<board or title>\|<ver>:`, by each comment's `ver` field and by version approval. Change it for every new version |
| `total` | number | **Yes** | Total video seconds. Timeline width is `total × 32` pixels; the thumbnail index limit also depends on it |
| `pic` | array | **Yes**, at least 1 entry | The shot list (next section). It must start at `s:0`, join end to start, and cover `total`. If the shot at a time cannot be found, the template falls back to the last shot |
| `kinds` | object | No (default `{}`) | Category code → `[name, how made, source, color (optional)]`. `how made` and `source` are the default texts when a shot has no `how` or `src`. The color can be any CSS color (`"#ff9ac4"`). Without one, a code the template knows (`aiv aii realv real fig photo b3d bvid code card warn`) uses its built-in color, otherwise the gray `--card`. A `pic[].k` missing from `kinds` does not crash (the name shows the code itself) |
| `agent` | string | No (default `AI`) | The AI's name in "Send to ...", reply labels and hint text |
| `voLabel` | string | No (default "Narration / dialogue" in the English template, "旁白／台詞" in the Chinese one) | Name of the `vo` row in the details panel (also used for the "this line" row in proposals). `make_board.py --lang en` writes the English default into D explicitly |
| `hint` | string | No | Hint text next to the title. Without it the default is used (with `props`, the proposal default) |
| `chap` | array | No (default `[]`) | Chapters: `[seconds, chapter name]`. Draws thin lines on the overview, chapter labels on the timeline, and "which chapter" in the details panel |
| `subs` | array | No (default `[]`) | Subtitles: `[start, end, text]`. The subtitle lane of the timeline and the "Subtitles" row |
| `vo` | array | No (default `[]`) | Narration or dialogue: `[start, duration, text]` (note the second value is the **duration**, not the end time). The `voLabel` row of the details panel |
| `sfx` | array | No (default `[]`) | Sound effect points: `[time, name]`. Diamond markers in the sound lane; those inside a shot are listed in the "Sound FX" row |
| `music` | array | No (default `[]`) | Music segments: `[start, end, name]`. **Language-dependent:** a name containing "靜音" (Chinese template) or matching `/silen\|mute/i` (English template, for example "Silence" or "Muted") is drawn with the diagonal-stripe style. The segment label reads "配樂：<name>" or "Music: <name>" |
| `wave` | array | No (default `[]`) | Volume waveform: integers 0 to 99, **one value per 0.25 second** (length should be `total×4`). All 0 if there is no audio track |
| `props` | array | No | "Proposals before spending" (next section). When present (length > 0): the proposal area shows, the version approval button **does not appear**, and the title and hint use the proposal versions |
| `notes` | string array | No | Proposal notes, shown only when there are `props` (one line each) |
| `openings` | array | No | Opening options: `[{id, title, text, meta}]`. The reviewer can pick one; the result is stored in `choices.opening` |
| `mode` | string | No | Only `"new"` has an effect: for storyboard drafts (the details panel gets a "Cost" row, and the proposal wording becomes "Storyboard sketch") |
| `twd` | number | No | Proposal cost conversion: the amount per credit. Only when given does the credit count get "(about ...)" |
| `unit` | string | No (default `NT$`) | Currency symbol for the amount above |
| `direct` | boolean | No | `true` = one `v0.mp4` file for the whole film (the browser streams it). `make_board.py` always sets `true`. Without it the template fetches `v<k>.mp4` as a blob (which needs `chunk`) |
| `chunk` | number | No (default 100000) | Video chunk length in seconds. In `direct` mode, setting it longer than the video means no chunking |
| `mbase` | string | No (default `""`) | URL prefix for the thumbnail sheets `t*.jpg` and videos `v*.mp4` |
| `pub` | boolean | No | `true` = **cloud mode** (below). Injected by `cloud/build_site.py`; do not set it yourself |
| `board` | string | Required when `pub` | Cloud desk name (the `/api/store?b=` value, lowercase letters, digits and hyphens, at most 40 characters). Injected by `build_site.py` |
| `nav` | array | No | Header navigation: `[{label, href, on}]`. Injected by `build_site.py` ("← All videos" when the site's `lang` is `en`) |

The D that `make_board.py` actually produces also has `direct:true`, `chunk:100000`, `agent`, `kinds` (colors filled in), `vo` (converted from the subtitle file), and empty `chap/sfx/music`.

Language-dependent defaults that `make_board.py --lang en` fills in: the auto-detected shot names are "Shot 1", "Shot 2", and so on; the default category names are Title card (`card`), Motion graphics (`code`), Chart (`fig`), AI video (`aiv`), AI image (`aii`), Live footage (`realv`), Live action (`real`), Photo (`photo`), 3D (`b3d`) and Shot (`shot`); unfilled "how made" and "source" read "(not filled in)".

### `pic[]`: one shot

| Field | Type | Required | Purpose |
|---|---|---|---|
| `s` | number | **Yes** | Start second |
| `d` | number | **Yes** | Duration in seconds (`s+d` equals the next shot's `s`) |
| `k` | string | **Yes** | Category code (matches `kinds`) |
| `t` | string | **Yes** | Shot name |
| `how` | string | No | "Made with"; falls back to `kinds[k][1]` |
| `src` | string | No | "Source"; falls back to `kinds[k][2]` |
| `note` | string | No | The "Note" row (the shots `note` of `make_board.py` maps here) |
| `desc` | string | No | The "On screen" row |
| `f` | string | No | Framing note appended to the "Duration" row |
| `u`, `n` | integers | No | This asset's `u`-th appearance out of `n` in the film. When `n>1` the shot card shows `u/n` in the top right corner (red when `n>=4`), and the details panel gets a "Reuse" row |
| `o` | string | No | The "Overlay card" row |
| `sk` | string | No | The "Sketch" row |
| `cost` | number | No | Only with `mode:"new"`: the "Cost" row (0 shows "Free") |
| `b` | any | No | Not read by the template (a shot number left over from old projects); can be omitted |

### `props[]`: proposals before spending (optional)

Required: `id` (string, such as `"P1"`), `rev` (integer; add 1 whenever the content changes so old approvals expire), `segs` (integer array of **indexes into `pic`**; two proposals cannot claim the same shot), `t` (start second), `d` (how many seconds it covers), `cost` (credits), `title`, `cur` (description of the current picture).
Optional: `kind` (`"video"` shows "AI video, 5 s", anything else shows "AI image"), `label` (replaces that default heading), `desc`, `move`, `zh` (this line of narration), `basis`, `risk`, `note` (what changed in this revision).
For each proposal the reviewer can "Approve this item" and "Send comment" (the comment's `cat` is fixed to `"Proposal"` in the English template and `"提案"` in the Chinese one, and carries `prop` and `rev`).

## Three storage modes

At startup the template decides in order: `D.pub` means cloud mode; otherwise `window.claude.use` means Artifact mode; otherwise local mode. If the connection fails it also falls back to local mode.

### Comment rows (the same in all three modes)

```
t        number   seconds (rounded to 0.1); -1 for a whole-film comment
seg      integer  shot number (1-based); -1 for a whole-film comment
segTitle string   shot name; "Whole film" for a whole-film comment (English template; "整支片" in the Chinese one); "<id> <proposal name>" for a proposal comment
cat      string   Picture / Sound / Subtitles / Pacing / Other / Proposal (English template; 畫面／聲音／字幕／節奏／其他／提案 in the Chinese one); "" for a mark that has not been written yet
text     string   comment text; "" for a mark that has not been written yet
at       string   ISO time
ver      string   D.ver at the time of writing
done     boolean  the AI can set it to true when handled (the UI shows "✓ Done")
whole    boolean  (optional) "Check the whole film": look for similar problems everywhere in the film
reply    string   (optional) the AI's reply (the UI shows "<agent>: ...")
prop,rev          (proposal comments only) the proposal id and revision
```

Category values are stored in the language of the template that wrote them. When the AI filters by `cat`, accept both.

Approval rows: version approval is stored as `approvals.version` = `{ok:true, ver, at, title:"Version approval"}` (only for desks without props; the Chinese template stores "整版核准"); proposal approval is stored as `approvals.<proposal id>` = `{ok, rev, kind, cost, title, at, ver}`; the opening choice is stored as `choices.opening` = `{pick, at, ver}`. An approval counts only while its `ver` (for proposals, `rev`) matches the current one.

### 1. Local mode (no backend, simplest, the default for `make_board.py`)

- Comments live in the browser `localStorage`, key prefix `<board or title>|<ver>:`: `cms` (the comment array; each `id` is `l<millisecond timestamp>`), `appr` (approvals), `pick` (opening), `drafts` and `draft` (text not saved yet).
- The "Send to ..." buttons are hidden in this mode. The reviewer opens "My comments", clicks **Copy all comments**, and pastes the text into the chat with the AI. What the AI receives is the text shown below.
- You can also read `<title>|<ver>:cms` in `localStorage` directly (inside the reviewer's browser).

### 2. Cloud mode (`D.pub`, needs a deployed `cloud/`)

- Comments live in the site backend `/api/store` (Netlify Blobs): `GET /api/store?b=<board>` returns the whole `{comments:{<id>:row}, approvals:{...}, choices:{...}, meta:{...}}`; `POST` with body `{b, op:"set"|"merge"|"del", c:collection, id, d}` returns the updated whole. `meta.sent={at, n}` records the time of the last "Send to ...".
- When the reviewer clicks **"Send to ..."**, the text written in marks is first saved to the backend, then one Netlify form `review` is submitted with `board`, `sent` (ISO time), `summary` (the comment text, at most 6000 bytes) and `payload` (the whole JSON, at most 60000 characters). It **does not wake the AI**.
- How the AI reads: with no password, `GET /api/store?b=<board>` directly; with a password, only the Netlify form can be read. To write back the result: `POST` `{b, op:"merge", c:"comments", id, d:{done:true, reply:"..."}}`.
- It reloads automatically every 30 seconds (not while a text box has the cursor).

Example backend data (adapted from a real run of the `/api/store` protocol with a local stand-in server, using a page built by `build_site.py`, by writing one comment at 5.2 seconds, clicking "+ Mark here" once more, and clicking "Send to ..."; the run itself used the Chinese template, so the values here are the English equivalents of what it stored):

```json
{"approvals":{},"choices":{},
 "comments":{
  "cmwovw190gsy3":{"at":"2026-11-20T11:16:35.796Z","cat":"Picture","done":false,"seg":2,"segTitle":"Transition card","t":5.2,"text":"Cloud: subtitles too fast","ver":"t-v1"},
  "cmwovw1myjdaf":{"at":"2026-11-20T11:16:36.298Z","cat":"","done":false,"seg":2,"segTitle":"Transition card","t":5.2,"text":"","ver":"t-v1"}},
 "meta":{"sent":{"at":"2026-11-20T11:16:36.800Z","n":2}}}
```

The matching form `summary` has the shape (from the template code, not captured from a cloud run):

```
[t-v1] From Review Desk: 2 comments (1 mark not written yet); version not approved yet. Full details are in the Review Desk database.
[0:05 | Shot 2 "Transition card"] Cloud: subtitles too fast
[0:05 | Shot 2 "Transition card"] (empty)
```

### 3. Artifact mode (`window.claude`)

- When the page sits inside a Claude Artifact, the template uses `window.claude.use('db')` for the database (collections `comments`, `approvals`, `choices`; same row format as above, with `id` being the database document id), and `window.claude.use('comments')` with `canSendToClaude()`, `anchorFor(el)` and `sendToClaude({anchor, text})` to send the comment text back to the chat. The AI later reads the `comments` collection with ArtifactData.
- The text sent back to the chat uses the format under "Exported comment text" below, capped at 3600 bytes; beyond that the end reads "… (read the database for the rest)".
- **This mode was not tested** (it needs an Artifact environment). Note the template is now a full HTML document (with a doctype and `<head>`); if you paste it into an Artifact, check whether the platform wraps it again, and merge the `<head>` content into the platform's shell if needed.

## Exported comment text

Format (`sendText()`; the English template):

```
[<ver>] From Review Desk: N comment(s)[ (K mark(s) not written yet)][; opening: proposal X|(not picked yet)][; approved a of b item(s) (id, id, N credits)][; version approved|version not approved yet]. Full details are in the Review Desk database.
[m:ss | Shot N "shot name"[ | source][ proposal id][ | check the whole film]] comment text        <- one line per comment, ordered by time ascending; whole-film comments come first with the label "Whole film" and no shot
```

- The pieces in square brackets `[ ]` appear only when they apply. "Copy all comments" replaces the sentence " Full details are in the Review Desk database." with nothing, so the header ends at the period. Everything else is the same.
- Every line carries the time, the shot number and name, and the source when the shot has `src`. A shot whose name is exactly the auto-detected "Shot N" shows only `Shot N`. There is no category (`cat`); times are whole seconds only. For the category or the exact `t`, read the rows from `localStorage` or the database.
- A mark with no text shows "(empty)".
- Singular and plural follow the count: "1 comment", "2 comments", "1 mark", "2 marks".

Real output of the English template (local mode, from "Copy all comments", on a desk built with `make_board.py --lang en` from `demo/demo.mp4` with an English shot list; five comments, including one whole-film note, one whole-film check, one mark whose text was typed in the mark's cell and copied without saving it first, and one empty mark; version not yet approved):

```
[v1] From Review Desk: 5 comments (1 mark not written yet); version not approved yet.
[Whole film] Overall colour feels cold
[Whole film | check the whole film] Subtitles too fast everywhere
[0:13 | Shot 4 "A cup in 4 minutes" | Made in-house, no outside assets] The bar grows too slowly
[0:19 | Shot 5 "Storefront" | Made in-house, no outside assets] The sign text is too small
[0:25 | Shot 6 "Three highlights card" | Made in-house, no outside assets] (empty)
```

The same desk after "✓ Approve this version" and "Confirm approval? Click again" (header only): `[v1] From Review Desk: 5 comments (1 mark not written yet); version approved.`

Header for a proposal desk, built from the template code (not run): `[props-v1] From Review Desk: 1 comment; opening: proposal 1; approved 1 of 1 item (P1, 2 credits). Full details are in the Review Desk database.`
