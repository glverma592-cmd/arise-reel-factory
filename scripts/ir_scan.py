import subprocess, json, csv, os, math
SRC="google_drive"; OUT="ir_work"
rows=[]
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".mp4"): continue
    p=os.path.join(SRC,f)
    # tech
    r=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
        "stream=width,height,r_frame_rate,codec_name","-show_entries","format=duration",
        "-of","json",p],capture_output=True,text=True)
    try:
        j=json.loads(r.stdout); s=j["streams"][0]; dur=float(j["format"]["duration"])
        w,h,fps,vc=s["width"],s["height"],s["r_frame_rate"],s["codec_name"]
    except Exception as e:
        rows.append(dict(file=f,error=str(e))); continue
    a=subprocess.run(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=codec_name","-of","csv=p=0",p],capture_output=True,text=True)
    has_audio = bool(a.stdout.strip())
    # scene changes (action density)
    sc=subprocess.run(["ffmpeg","-i",p,"-vf","select='gt(scene,0.25)',showinfo","-f","null","-"],capture_output=True,text=True)
    scenes=sc.stderr.count("pts_time:")
    # audio loudness peaks (mean_volume per 3s chunk -> variance = hype signal)
    loud=[]
    if has_audio:
        for t in range(0,int(dur),3):
            v=subprocess.run(["ffmpeg","-ss",str(t),"-t","3","-i",p,"-af","volumedetect","-f","null","-"],capture_output=True,text=True)
            for line in v.stderr.splitlines():
                if "mean_volume" in line:
                    try: loud.append(float(line.split()[-2]))
                    except: pass
    import statistics
    lv = statistics.pstdev(loud) if len(loud)>1 else 0.0
    lm = statistics.mean(loud) if loud else -99.0
    # frame thumbs (3 per clip, scaled small)
    os.makedirs(f"{OUT}/frames/{f[:-4]}",exist_ok=True)
    for i,frac in enumerate([0.15,0.5,0.85]):
        t=dur*frac
        subprocess.run(["ffmpeg","-v","error","-ss",f"{t:.1f}","-i",p,"-frames:v","1","-vf","scale=320:-2","-q:v","7",f"{OUT}/frames/{f[:-4]}/f{i+1}.jpg"])
    score = round(scenes/max(dur,1)*10 + lv*1.5 + max(lm+40,0)*0.3, 2)
    rows.append(dict(file=f,dur=round(dur,1),res=f"{w}x{h}",fps=fps,vc=vc,audio=has_audio,
        scenes=scenes,scene_rate=round(scenes/max(dur,1)*60,1),mean_vol=round(lm,1),vol_std=round(lv,1),score=score))
    print(f"done {f} dur={dur:.0f}s scenes={scenes} score={score}",flush=True)
with open(f"{OUT}/clips_manifest.csv","w",newline="") as fh:
    cols=["file","dur","res","fps","vc","audio","scenes","scene_rate","mean_vol","vol_std","score","error"]
    wcsv=csv.DictWriter(fh,fieldnames=cols,extrasaction="ignore"); wcsv.writeheader()
    for row in sorted(rows,key=lambda r:-r.get("score",0)): wcsv.writerow(row)
print("MANIFEST SAVED", len(rows))
