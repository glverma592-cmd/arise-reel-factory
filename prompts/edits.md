# Edits — user ki changes

Sirf wahi badlo jo maanga gaya, phir `python scripts/make_reel.py projects/<slug>` (stills check bhi karo).
Jo scenes nahi badle unki voice cache se aati hai — edit jaldi ho jata hai. Har baar naya `reel_vN.mp4` banta hai.

| User bole | Kya karna hai |
|---|---|
| "Hook aur punchy karo" | Scene 1 ka `say` + `headline` chhota aur tez karo: number, sawaal, ya "galti" angle. 3 options socho, best rakho, user ko 1 line me batao. |
| "Chhoti karo" / "30 sec ki" | Kam zaroori scenes hatao, `say` chhote karo. |
| "Lambi karo" | Ek example ya mistake scene jodo (research se). |
| "Female voice" / "awaaz badlo" | `"voice": "hi-IN-SwaraNeural"` (ya jo maange). |
| "Fast bolo" / "slow" | `"rate"` badlo: `+15%` fast, `-5%` slow. |
| "English me" | `say` aur screen text English me, voice `en-IN-PrabhatNeural` / `en-IN-NeerjaNeural`. |
| "Colors badlo" / "mera brand" | `assets/brand.json` → `colors`, `name`, `tagline`, `avatar`. |
| "Music lagao" | User se .mp3 `assets/music/` me daalne ko kaho (copyright-free), `"music"` me naam likho. |
| "Captions hatao" | `"captions": false` |
| "Scene X hatao / badlo" | Sirf wahi scene edit karo. |

Har edit ke baad batao: kya badla (1 line) + naye video ka path.
