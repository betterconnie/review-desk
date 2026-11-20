# Review Desk user guide (for the reviewer)

[繁體中文版：操作說明.md](操作說明.md)

You do not need to know anything about video editing, and there is nothing to install. Open the link, watch the film, and write down what you want changed.

## The one-minute version

1. Click **▶ Play**, or drag the timeline.
2. When you see something to change, stop. Type your comment in the box under the video and click **Add comment at 0:19** (the number is the time you stopped at).
3. When you are done, open **My comments**, click **Copy all comments**, and paste the text back into your chat with the AI.
4. If this version is good, click **✓ Approve this version**, then click again to confirm.

## What is on the screen

**The player (top)**
- **▶ Play** / **❚❚ Pause**.
- **⏮ Prev shot** and **Next shot ⏭** jump one shot at a time. In the middle of a shot, "Prev shot" first goes back to the start of that shot.
- **−5s** and **+5s** jump back and forward.
- **1×** changes the playback speed with each click: 1× → 1.5× → 2×.
- **+ Mark here** drops a flag at this second. You do not have to write anything yet, and the video keeps playing.
- Move the mouse over the video and the whole-film overview timeline appears. You can drag it. On a phone, tap the picture to show it (the tap also plays or pauses).
- Keyboard: Space plays or pauses, Left and Right arrows jump 2 seconds.

**This shot (on the right on a computer, below on a phone)**
This panel describes the shot you are on: which shot it is, how long it runs, how it was made, where the asset came from, and the narration and subtitle at this moment. If you wonder "is this picture AI-made or live footage?", look here.

**Nearby shots**
Thumbnails of the current shot and the ones around it. Click one to jump there.

**Shot timeline**
The whole film from left to right. The top lane has one thumbnail per shot, colored by type (the legend is above it). The middle lane is the sound level. The bottom lane is the subtitles. You can drag it sideways. Places where you wrote a comment get a numbered pin.

## Three ways to write a comment

| What you want to do | How |
|---|---|
| Something is wrong at this second | Stop there, type, pick a category (Picture, Sound, Subtitles, Pacing, Other) and click "Add comment at 0:19" |
| Watch the whole film first | Click "+ Mark here" as you watch. When you are done, open "My comments" and fill in the text for each mark |
| A comment that is not about one second (for example "the film is too long") | Type it and click "Add as whole-film note" |

Each comment also has:
- **Check whole film**: it means "not only here, check every similar spot in the film".
- **Delete**: for mistakes. It takes two clicks (the first click turns the button into "Confirm delete?").

What you type is saved on this device as you type. Refreshing the page or closing the tab by accident will not lose it.

## Handing the comments to the AI

**Local mode** (the address starts with `127.0.0.1` or `localhost`): open "My comments", click "Copy all comments", and paste the text into the chat. Every comment arrives with its time, shot name and source, for example:

```
[0:19 | Shot 5 "Storefront" | Made in-house, no outside assets] The sign text is too small
```

**Cloud mode** (a real web address, with "← All videos" at the top): click "Send to AI". Your comments are stored on the site, so you can switch between phone and computer. After you click, tell the AI in the chat that you sent them. The AI is not woken up by itself.

## Approval

- "✓ Approve this version" needs two clicks. The first click turns it into "Confirm approval? Click again", and it cancels itself after 4 seconds so a slip of the finger does not count.
- After approving, you can click "Undo approval".
- Approval belongs to one version. If the AI makes a new version, the old approval does not carry over. Watch the new version and approve it again.
- Only your own click counts. The AI will not, and should not, approve for you.

## Common situations

| Situation | What to do |
|---|---|
| The video is black or keeps spinning | Wait a few seconds for it to load. If it still fails, refresh. Ask the AI to confirm the page is opened by its web address, not by double-clicking the file |
| You changed computers and your comments are gone | In local mode, comments live only in the browser where you wrote them. Go back to that computer and copy them, or ask the AI to switch to cloud mode |
| "Copy all comments" did nothing | The text appears in the comment box. Select all and copy it by hand |
| A mark has text, but the list still looks empty | The text is saved on this device. Click "Save 2 written marks" (the number matches your marks), or just click Copy or Send, which carries them along |
| The timeline is too long to search | Drag the overview timeline on the player, or click "Next shot ⏭" to go shot by shot |

## Privacy

In local mode the video and your comments stay on your computer and are not uploaded. The page only asks Google Fonts for its font files (it falls back to system fonts if it cannot reach them). In cloud mode the video sits on the web space of whoever built the site, and without a password, anyone with the link can watch it.
