# Review Desk cloud version (optional)

[繁體中文版：README.md](README.md)

The local version (the folder made by `scripts/make_board.py`) does not need this package. Comments live in the browser, and "Copy all comments" pastes them to the AI.
Use this package only when you want one fixed address, comments that follow you between phone and computer, and a way for the AI to read the comments itself. It combines several review desks into one site with a home page, and stores comments in Netlify Blobs.

## Files

| File | Purpose |
|---|---|
| `build_site.py` | Reads `boards.json` and builds `site/` from the review desk folders (home page, every desk, plus the injected cloud settings and form) |
| `boards.example.json` | Example config. Copy it to `boards.json` and edit |
| `netlify/functions/store.mjs` | The comment backend at `/api/store`, one JSON document per review desk |
| `netlify.toml`, `package.json` | Netlify settings. The backend function needs `@netlify/blobs` |

## Steps

1. Use `scripts/make_board.py` to make a review desk folder for each video. `--agent` sets the button name ("Send to ..."). For an English interface add `--lang en`.
2. `cp boards.example.json boards.json` and edit it for your videos. Paths are relative to `boards.json`. The desk name is `id-key`, using only lowercase letters, digits and hyphens, at most 40 characters (it is the storage key for comments and part of the web address). For an English home page and injected text, set `"lang": "en"` in `boards.json` (default is `"zh"`). The desks themselves need `make_board.py --lang en`, so the two should match.
3. In `cloud/`, run `python3 build_site.py` to produce `site/`. Each run first clears the `site/` it made last time and rebuilds, so a desk you removed from `boards.json` does not stay on the site. The example config uses `src` of `../review_demo`: first make that folder one level up, following "Try the demo" in the README.
4. Deploy (you need your own Netlify account; this package contains no account or site id):
   ```
   cd cloud
   npm install                       # always do this before a command-line deploy, otherwise the backend function cannot find @netlify/blobs and saving comments breaks
   npx netlify-cli login             # first time only
   npx netlify-cli deploy --prod --dir site
   ```
   The first time, it asks which site to link or create.
5. Verify (do not rely on the command's exit code alone):
   - `curl -s https://<your-address>/api/store?b=<id-key>` should return JSON: `{"comments":{},"approvals":{},"choices":{},"meta":{}}`.
   - Open the home page. A card appears for every desk, and the video plays when you click in.
   - Reload at phone width. The browser console should show 0 errors.

## Password

This package **does not set a password**. To protect the site, set one yourself in the Netlify dashboard (Project, Project configuration, Access & security, Visitor access, Password Protection; which plans include this is up to Netlify's own description at the time).
Until you do, anyone with the link can watch unreleased videos and write comments. `build_site.py` only adds search engine exclusion (`robots.txt`, `_headers`, a meta tag).

## How the AI reads the comments

- No password: `GET /api/store?b=<id-key>` returns the whole JSON (`comments`, `approvals`, `choices`, `meta`; format in `references/data-format.en.md`).
- With a password: the AI cannot open the page and can only read the Netlify form. When the reviewer clicks "Send to ...", one form submission is sent (form name `review`, fields `board`, `sent`, `summary`, `payload`; `summary` is the comment text and `payload` is the whole JSON). Look in the Forms section of the Netlify dashboard, or read it with the Netlify API or a connector.
- **Without a password, approvals cannot be trusted**: anyone with the link can write to the backend, including a "version approval" record. When the AI reads `approvals`, it should confirm with the reviewer in the chat unless the site is password protected.
- The form **does not wake the AI**: after sending, the reviewer should say so in the chat, or the AI should check on a schedule.
- When the AI has handled a comment it can write back (without a password): `POST /api/store` with body `{"b":"<id-key>","op":"merge","c":"comments","id":"<comment id>","d":{"done":true,"reply":"Fixed"}}`. The review desk then shows "✓ Done" and the AI's reply.

## Pitfalls we hit

- Deploying from the command line without `npm install`: the site looks fine, but `/api/store` is broken and comments cannot be saved.
- The deploy command often answers "fetch failed" even though the upload may have succeeded (more common for big sites). After every failure, **check the live address first** to see whether it is the new version, and retry only if it really did not upload.
- For big sites (many videos), a command-line deploy is more reliable than a connector.
- A cloud page needs a static `<form name="review" data-netlify="true">` for Netlify to recognize the form. `build_site.py` adds it to every page. Do not remove it by hand.
- The backend is for one person: if two people edit the same comment at once, the later write wins. Each comment is limited to about 8000 characters, and the whole file to about 400KB.
- To switch versions, use a new `--ver` with `make_board.py`: the version approval remembers the version name, and a different name does not count as approved. Note that cloud comments are stored per desk name (`id-key`), so when the same desk changes version, the old comments stay in the list (each one has a `ver` field to tell them apart). For a fresh start, use a new `id-key`.
- Comments on a cloud page sync automatically every 30 seconds. Something written on another device can take up to 30 seconds to appear.
