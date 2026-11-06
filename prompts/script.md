# Script — `projects/<slug>/script.json`

## Viral script rules
- **Hook (pehle 2 sec):** sawaal, chaunkane wala number, ya "galti" — kabhi "Hello friends" se shuru mat karo.
- **6–9 scenes**, kul 25–60 sec. Har scene = ek idea.
- `say` (jo bola jayega): max ~25 words per scene, bolchaal wali Hindi/Hinglish. English tech words English me hi rakho.
  Hindi words **Devanagari** me likho taaki AI voice sahi bole (e.g. "सिर्फ तीन steps follow करो").
- Screen text (headline/title/items): max ~8 words. Ek-do important words ko `*star*` me wrap karo — wo accent color + italic me dikhte hain.
- Last scene hamesha `cta` (follow + comment keyword).
- Numbers sirf wahi jo `research.md` me source ke saath hain.

## Format
```json
{
  "topic": "…",
  "tag": "AI TUTORIAL",
  "voice": "hi-IN-MadhurNeural",
  "rate": "+8%",
  "music": "optional-file-name.mp3",
  "music_volume": 0.12,
  "captions": true,
  "scenes": [ … ]
}
```
Voices: `hi-IN-MadhurNeural` (male), `hi-IN-SwaraNeural` (female), `en-IN-PrabhatNeural`, `en-IN-NeerjaNeural`.
`rate` = speed (`+0%` normal, `+10%` fast). `music`: file in `assets/music/` (blank = pehli file wahan ho to wo, `false` = no music).

Har scene me optional: `"bg": "light"` ya `"blue"` (default: alternate).

## Scene types

| type | Fields | Kab use karein |
|---|---|---|
| `hook` | `say`, `headline`, `kicker?`, `sub?` | Pehla scene — bada text |
| `text` | `say`, `headline`, `kicker?`, `sub?`, `big?` | Ek bada statement |
| `stat` | `say`, `value` (e.g. "7", "25%", "1,00,000"), `suffix?`, `title?`, `label?` | Number count-up animation |
| `points` | `say`, `title?`, `items` (2–4) | Bullet cards ek-ek karke |
| `steps` | `say`, `title?`, `items` (2–4, numbered grid) | Step 1/2/3 |
| `prompt` | `say`, `title?`, `prompt`, `items?` (≤4, ✓ tick ke saath) | AI me kya type karna hai (typing animation) |
| `compare` | `say`, `title?`, `before`, `after`, `before_label?`, `after_label?` | Pehle vs ab |
| `cta` | `say`, `headline`, `keyword?`, `button?` | Last scene — follow + comment |

`items` = strings ya `{ "text": "…", "icon": "…" }`.
Icons: search, doc, mic, wand, folder, terminal, check, bolt, chart, heart, star, rocket, money, clock, user, play, idea, phone, globe, lock, camera, target.

## Example
`projects/example-ai-resume/script.json` dekho — har scene type ka example hai.
