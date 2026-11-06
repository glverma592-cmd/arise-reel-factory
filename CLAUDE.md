# Reel Studio Kit — Claude Code instructions

You are running inside **Reel Studio Kit**. The user talks to you in Hindi / Hinglish / English.
Reply in the same language they use, keep replies short and friendly, and do the work yourself —
never ask the user to run commands manually unless something truly needs their action (like approving an installer).

The kit turns one topic into a finished 1080x1920 Instagram Reel / YouTube Short:
**Research → Script → AI Voiceover → Animation & Captions → MP4**.

```
reel-studio-kit/
  CLAUDE.md            ← ye file (tumhare instructions)
  README.md            ← user ke liye guide
  requirements.txt     ← python packages (edge-tts)
  assets/
    template.html      ← animation design (scenes, captions, stars background)
    brand.json         ← user ka naam, tagline, colors, CTA keyword
    music/             ← optional background music (koi bhi .mp3 daal do)
  scripts/
    check_setup.py     ← setup check
    voiceover.py       ← AI voice + word timings + captions.srt
    render.mjs         ← headless Chrome/Edge se frames → FFmpeg → MP4
    make_reel.py       ← ek command me sab
  prompts/
    research.md        ← research kaise karna hai
    script.md          ← script.json ka format + viral script rules
    edits.md           ← "hook punchy karo" jaise edits kaise handle karne hain
  projects/<slug>/     ← har reel ka apna folder
```

---

## 1) Setup — when the user says "is folder ka setup karo" / "setup karo" / "setup this folder"

1. Run `python scripts/check_setup.py` (on Windows try `python`, then `py`; on Mac/Linux `python3`).
2. Install whatever shows ❌. Detect the OS first and use the matching commands:

| Need | Windows (PowerShell) | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|
| Node.js 22+ | `winget install -e --id OpenJS.NodeJS.LTS` | `brew install node` | `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo -E bash - && sudo apt install -y nodejs` |
| Python 3.9+ | `winget install -e --id Python.Python.3.12` | `brew install python` | `sudo apt install -y python3 python3-pip` |
| FFmpeg | `winget install -e --id Gyan.FFmpeg` | `brew install ffmpeg` | `sudo apt install -y ffmpeg` |
| Chrome/Edge | Edge is already on Windows | `brew install --cask google-chrome` | `sudo apt install -y chromium` |
| edge-tts | `pip install -r requirements.txt` | `pip3 install -r requirements.txt` | `pip3 install -r requirements.txt --break-system-packages` (if needed) |

   - macOS without Homebrew: install it first from https://brew.sh (ask the user to approve the password prompt).
   - After winget installs on Windows, the new tools may need a fresh terminal: tell the user to restart Claude Code if `node`/`ffmpeg` is still "not found", or use full paths.
   - If Chrome/Edge is installed in an unusual place, set the `CHROME_PATH` environment variable.
3. Run `check_setup.py` again until everything is ✅.
4. Ask the user (one short message) for their **brand name, tagline, and comment keyword** and write them into
   `assets/brand.json`. If they have a profile photo, ask them to drop it in `assets/` and set `"avatar": "assets/<file>"`.
   If they skip this, keep the defaults.
5. Reply: "✅ Setup complete! Ab bas likho: **Reel banao — <apna topic>**"

## 2) Making a reel — when the user says "Reel banao — <topic>" (or any similar request)

Work through these four stages and give the user a one-line update after each (e.g. "✅ Research done").

1. **Research** — follow `prompts/research.md`. Use web search for anything factual, current, or numeric.
   Save notes + sources to `projects/<slug>/research.md`. `<slug>` = short kebab-case topic name.
2. **Script** — follow `prompts/script.md` exactly and write `projects/<slug>/script.json`.
   Show the user the hook line and the scene list in 3–6 short lines (not the JSON).
3. **AI Voiceover** — `python scripts/voiceover.py projects/<slug>`
   (no internet / voice fails → explain, and offer `--silent` to still get the video).
4. **Animation & Captions** — first `node scripts/render.mjs projects/<slug> --stills`, then **look at every image in
   `projects/<slug>/stills/`**. Fix anything wrong (text cut off, overlapping, too much text, empty scene) by editing
   `script.json` (shorter text, fewer items, different scene type) and re-render stills. Then render the video:
   `node scripts/render.mjs projects/<slug>`.

Finish with: the path of `reel_vN.mp4`, its length, `cover.jpg` (thumbnail), `captions.srt`, and a ready-to-paste
**Instagram caption + 5–8 hashtags** written in the user's language.

Shortcut: `python scripts/make_reel.py projects/<slug>` runs voiceover + render together.

## 3) Edits — when the user asks for changes

Follow `prompts/edits.md`. Edit only what was asked in `script.json`, then re-run voiceover + render.
Unchanged scenes reuse cached audio, so edits are fast. Each render saves a new `reel_v2.mp4`, `reel_v3.mp4`…
so the old version is never lost.

## Rules
- Never invent statistics. Every number on screen must come from research with a source in `research.md`.
- Do not use copyrighted music, logos, characters, or someone else's content in the reel.
- Keep the reel 25–60 seconds unless the user asks otherwise.
- If a command fails, read the error, fix it, and retry before telling the user.
