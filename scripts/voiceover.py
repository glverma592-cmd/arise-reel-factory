#!/usr/bin/env python3
"""
Reel Studio Kit — Step: AI Voiceover + caption timings

Har scene ke "say" text se AI voice banata hai (Microsoft Edge neural voices, free),
word-by-word timing nikalta hai (captions ke liye), aur poora voice track jodta hai.

Usage:
  python scripts/voiceover.py projects/<naam>            # normal (internet chahiye)
  python scripts/voiceover.py projects/<naam> --silent   # bina awaaz (test / offline)
  python scripts/voiceover.py projects/<naam> --voice hi-IN-SwaraNeural

Output (project folder me):
  audio/            har scene ki mp3 (cache — text same ho to dobara nahi banti)
  voice.wav         poora voiceover track
  timings.json      scene start/duration + word timings
  captions.srt      upload ke liye subtitle file
"""
import argparse, asyncio, hashlib, json, os, re, shutil, subprocess, sys

DEFAULT_VOICE = "hi-IN-MadhurNeural"
SCENE_GAP = 0.35        # har scene ke baad thoda saans
MIN_SCENE = 2.0         # chhota scene bhi kam se kam itna lamba


def die(msg):
    print(f"\n❌ {msg}\n", file=sys.stderr)
    sys.exit(1)


def need(tool):
    if not shutil.which(tool):
        die(f"'{tool}' nahi mila. Pehle setup karo: Claude Code me likho 'is folder ka setup karo'.")


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        die(f"Audio length nahi padh paya: {path}")


def clean_for_tts(text):
    # *accent* markers screen ke liye hain, awaaz ke liye nahi
    return re.sub(r"\*([^*]+)\*", r"\1", text or "").strip()


def proportional_words(text, start, end):
    """Agar voice engine word timing na de, to lambai ke hisaab se baant do."""
    words = text.split()
    if not words:
        return []
    weights = [max(2, len(w)) for w in words]
    total = sum(weights)
    span = max(0.2, end - start)
    out, t = [], start
    for w, wt in zip(words, weights):
        d = span * wt / total
        out.append({"w": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


async def tts(text, voice, rate, pitch, mp3_path):
    try:
        import edge_tts
    except ImportError:
        die("edge-tts install nahi hai. Chalao:  pip install -r requirements.txt")
    kwargs = dict(rate=rate, pitch=pitch)
    try:
        comm = edge_tts.Communicate(text, voice, boundary="WordBoundary", **kwargs)
    except TypeError:  # purana edge-tts version
        comm = edge_tts.Communicate(text, voice, **kwargs)
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append({"w": chunk["text"], "start": round(s, 3),
                              "end": round(s + chunk["duration"] / 1e7, 3)})
    return words


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--silent", action="store_true", help="awaaz ke bina (test/offline)")
    ap.add_argument("--voice", help="voice override, e.g. hi-IN-SwaraNeural")
    args = ap.parse_args()

    need("ffmpeg"); need("ffprobe")
    proj = os.path.abspath(args.project)
    sp = os.path.join(proj, "script.json")
    if not os.path.exists(sp):
        die(f"script.json nahi mili: {sp}")
    with open(sp, encoding="utf-8") as f:
        script = json.load(f)
    scenes = script.get("scenes") or []
    if not scenes:
        die("script.json me koi scene nahi hai.")

    voice = args.voice or script.get("voice") or DEFAULT_VOICE
    rate = script.get("rate", "+8%")
    pitch = script.get("pitch", "+0Hz")
    audio_dir = os.path.join(proj, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    seg_files, timing_scenes, t = [], [], 0.0
    for i, sc in enumerate(scenes):
        say = clean_for_tts(sc.get("say", ""))
        key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{say}|{args.silent}".encode()).hexdigest()[:10]
        base = os.path.join(audio_dir, f"scene_{i+1:02d}_{key}")
        mp3, meta = base + ".mp3", base + ".json"

        if args.silent or not say:
            est = max(MIN_SCENE, len(say.split()) / 2.6) if say else float(sc.get("duration", 2.5))
            audio_dur = est
            words = proportional_words(say, 0.15, est - 0.1)
            src = None
        else:
            if os.path.exists(mp3) and os.path.exists(meta):
                with open(meta, encoding="utf-8") as f:
                    words = json.load(f)["words"]
                print(f"  scene {i+1}: cache se ✓")
            else:
                print(f"  scene {i+1}: voice bana raha hoon…")
                try:
                    words = asyncio.run(tts(say, voice, rate, pitch, mp3))
                except Exception as e:
                    if os.path.exists(mp3):
                        os.remove(mp3)
                    die(f"Voice nahi bani (scene {i+1}): {e}\n   Internet check karo, ya test ke liye --silent lagao.")
                with open(meta, "w", encoding="utf-8") as f:
                    json.dump({"say": say, "voice": voice, "words": words}, f, ensure_ascii=False)
            audio_dur = ffprobe_duration(mp3)
            if not words:
                words = proportional_words(say, 0.05, audio_dur - 0.05)
            src = mp3

        dur = max(MIN_SCENE, audio_dur + SCENE_GAP, float(sc.get("min_duration", 0)))
        if i == len(scenes) - 1:
            dur += 0.8  # last scene thoda ruke
        seg = os.path.join(audio_dir, f"_seg_{i+1:02d}.wav")
        if src:
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-af", f"apad=whole_dur={dur:.3f}",
                   "-t", f"{dur:.3f}", "-ar", "44100", "-ac", "2", seg]
        else:
            cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                   "-t", f"{dur:.3f}", seg]
        subprocess.run(cmd, check=True)
        seg_files.append(seg)
        timing_scenes.append({"start": round(t, 3), "duration": round(dur, 3),
                              "audio_duration": round(audio_dur, 3), "words": words})
        t += dur

    # join
    lst = os.path.join(audio_dir, "_concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for s in seg_files:
            f.write(f"file '{s.replace(os.sep, '/')}'\n")
    voice_wav = os.path.join(proj, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", voice_wav], check=True)

    timings = {"total": round(t, 3), "voice": None if args.silent else voice, "scenes": timing_scenes}
    with open(os.path.join(proj, "timings.json"), "w", encoding="utf-8") as f:
        json.dump(timings, f, ensure_ascii=False, indent=1)

    # SRT
    lines, n = [], 1
    for sc in timing_scenes:
        ws = sc["words"]
        for k in range(0, len(ws), 5):
            grp = ws[k:k+5]
            a = sc["start"] + grp[0]["start"]
            b = sc["start"] + grp[-1]["end"]
            lines += [str(n), f"{srt_time(a)} --> {srt_time(b)}", " ".join(w["w"] for w in grp), ""]
            n += 1
    with open(os.path.join(proj, "captions.srt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Voiceover ready — {t:.1f} sec, {len(scenes)} scenes"
          + (" (silent mode)" if args.silent else f", voice: {voice}"))


if __name__ == "__main__":
    main()
