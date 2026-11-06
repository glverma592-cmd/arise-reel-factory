#!/usr/bin/env python3
"""
Reel Studio Kit — ek command me poori reel:
  voiceover -> captions -> animation -> MP4

Usage:
  python scripts/make_reel.py projects/<naam>
  python scripts/make_reel.py projects/<naam> --silent    # bina awaaz (test)
  python scripts/make_reel.py projects/<naam> --stills    # sirf preview images
  python scripts/make_reel.py projects/<naam> --fps 24    # thoda fast render
"""
import os, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd):
    print("→", " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        print(__doc__); sys.exit(1)
    proj = a[0]
    vo = [sys.executable, os.path.join(KIT, "scripts", "voiceover.py"), proj]
    if "--silent" in a:
        vo.append("--silent")
    if "--voice" in a:
        vo += ["--voice", a[a.index("--voice") + 1]]
    run(vo)
    rn = ["node", os.path.join(KIT, "scripts", "render.mjs"), proj]
    if "--stills" in a:
        rn.append("--stills")
    if "--fps" in a:
        rn += ["--fps", a[a.index("--fps") + 1]]
    run(rn)


if __name__ == "__main__":
    main()
