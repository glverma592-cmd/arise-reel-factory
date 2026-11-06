#!/usr/bin/env python3
"""Reel Studio Kit — setup check. Sab ✅ ho to reel ban sakti hai."""
import os, shutil, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def line(good, name, detail=""):
    global ok
    ok &= good
    print(f"{'✅' if good else '❌'} {name}" + (f"  — {detail}" if detail else ""))


def ver(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip().splitlines()[0]
    except Exception:
        return ""


line(sys.version_info >= (3, 9), "Python 3.9+", sys.version.split()[0])

nv = ver(["node", "-v"]) if shutil.which("node") else ""
try:
    major = int(nv.lstrip("v").split(".")[0])
except ValueError:
    major = 0
line(major >= 22, "Node.js 22+", nv or "install nahi hai")

line(bool(shutil.which("ffmpeg")), "FFmpeg", ver(["ffmpeg", "-version"])[:40] if shutil.which("ffmpeg") else "install nahi hai")
line(bool(shutil.which("ffprobe")), "FFprobe", "" if shutil.which("ffprobe") else "FFmpeg ke saath aata hai")

try:
    import edge_tts  # noqa
    line(True, "edge-tts (AI voice)")
except ImportError:
    line(False, "edge-tts (AI voice)", "chalao: pip install -r requirements.txt")

if major >= 22:
    r = subprocess.run(["node", os.path.join(KIT, "scripts", "render.mjs"), "--find-chrome"],
                       capture_output=True, text=True)
    line(r.returncode == 0, "Chrome / Edge (animation render)", (r.stdout or r.stderr).strip().replace("✅ ", "").replace("❌ ", ""))
else:
    line(False, "Chrome / Edge (animation render)", "pehle Node 22+ install karo")

print("\n🎉 Setup complete — ab likho: Reel banao — <apna topic>" if ok else "\n⚠️  Upar ❌ wali cheezein theek karo.")
sys.exit(0 if ok else 1)
