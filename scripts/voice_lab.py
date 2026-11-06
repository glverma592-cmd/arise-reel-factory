#!/usr/bin/env python3
"""ARISE VØRNYX voice lab — 3 AI voice engines (all open-source).
1) edge-tts (rany2/edge-tts, GPL-3.0)  : Hindi/English cloud neural voices [PRODUCTION]
2) facebook/mms-tts-hin (Meta, CC BY-NC): Hindi local offline fallback
3) kokoro-onnx (hexgrad Kokoro-82M, Apache-2.0): English local hooks/narration
Usage: python3 voice_lab.py <engine> <text> <out>
"""
import sys, subprocess, asyncio
def edge(text,out):
    subprocess.run([sys.executable,"-m","edge_tts","--voice","hi-IN-MadhurNeural","--text",text,"--write-media",out],check=True)
def mms(text,out):
    import torch, soundfile as sf
    from transformers import VitsModel, AutoTokenizer
    tok=AutoTokenizer.from_pretrained("facebook/mms-tts-hin"); m=VitsModel.from_pretrained("facebook/mms-tts-hin")
    with torch.no_grad(): w=m(**tok(text,return_tensors="pt")).waveform
    sf.write(out,w[0].T.numpy(),m.config.sampling_rate)
def kokoro(text,out,voice="am_michael"):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k=Kokoro("/home/user/voice-lab/kokoro-en.fp16.onnx","/home/user/voice-lab/voices-v1.0.bin")
    s,r=k.create(text,voice=voice); sf.write(out,s,r)
if __name__=="__main__":
    eng,text,out=sys.argv[1],sys.argv[2],sys.argv[3]
    {"edge":edge,"mms":mms,"kokoro":kokoro}[eng](text,out)
    print("OK",out)
