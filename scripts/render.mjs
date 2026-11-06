#!/usr/bin/env node
/**
 * Reel Studio Kit — Step: Animation + Captions -> MP4
 *
 * assets/template.html ko headless Chrome/Edge me frame-by-frame chalata hai,
 * har frame FFmpeg ko deta hai, aur voice.wav (+ optional music) ke saath 1080x1920 MP4 banata hai.
 * Koi npm package nahi chahiye — sirf Node 22+, FFmpeg aur Chrome ya Edge.
 *
 * Usage:
 *   node scripts/render.mjs projects/<naam>                 # final video
 *   node scripts/render.mjs projects/<naam> --stills        # sirf preview images (fast check)
 *   node scripts/render.mjs projects/<naam> --fps 24        # thoda fast render
 *   node scripts/render.mjs --find-chrome                   # check: browser mila ya nahi
 */
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const KIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const die = (m) => { console.error(`\n❌ ${m}\n`); process.exit(1); };

function findChrome() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const L = process.env.LOCALAPPDATA || '', PF = process.env.PROGRAMFILES || 'C:\\Program Files', PF86 = process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)';
  const cands = {
    win32: [`${PF}\\Google\\Chrome\\Application\\chrome.exe`, `${PF86}\\Google\\Chrome\\Application\\chrome.exe`, `${L}\\Google\\Chrome\\Application\\chrome.exe`,
            `${PF86}\\Microsoft\\Edge\\Application\\msedge.exe`, `${PF}\\Microsoft\\Edge\\Application\\msedge.exe`],
    darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
             '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'],
  }[process.platform] || [];
  for (const c of cands) if (fs.existsSync(c)) return c;
  for (const bin of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge', 'brave-browser']) {
    try { const p = execFileSync('which', [bin], { encoding: 'utf8' }).trim(); if (p) return p; } catch {}
  }
  return null;
}

if (flag('--find-chrome')) {
  const c = findChrome();
  if (c) { console.log(`✅ Browser mila: ${c}`); process.exit(0); }
  die('Chrome / Edge nahi mila. Google Chrome install karo, ya CHROME_PATH set karo.');
}

const projArg = args.find((a) => !a.startsWith('--') && !/^\d+$/.test(a));
if (!projArg) die('Project folder do:  node scripts/render.mjs projects/<naam>');
const proj = path.resolve(projArg);
const readJSON = (p, need = true) => {
  if (!fs.existsSync(p)) { if (need) die(`File nahi mili: ${p}`); return null; }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
};
const script = readJSON(path.join(proj, 'script.json'));
const timings = readJSON(path.join(proj, 'timings.json'), false);
if (!timings) die('timings.json nahi hai — pehle voiceover chalao:  python scripts/voiceover.py ' + projArg);
const brand = readJSON(path.join(KIT, 'assets', 'brand.json'), false) || {};
if (brand.avatar && !/^(https?:|data:|file:)/.test(brand.avatar)) {
  const ap = path.resolve(KIT, brand.avatar);
  brand.avatar = fs.existsSync(ap) ? pathToFileURL(ap).href : '';
}

const fps = Number(opt('--fps', script.fps || 30));
const total = timings.total;
const nFrames = Math.ceil(total * fps);

// ---- build page
const buildDir = path.join(proj, 'build');
fs.mkdirSync(buildDir, { recursive: true });
const tpl = fs.readFileSync(path.join(KIT, 'assets', 'template.html'), 'utf8');
const data = { brand, script, timings, audio: '../voice.wav' };
const html = tpl.replace('<!--REEL_DATA-->', `<script>window.REEL=${JSON.stringify(data).replace(/</g, '\\u003c')};</script>`);
const pagePath = path.join(buildDir, 'index.html');
fs.writeFileSync(pagePath, html);

// ---- minimal Chrome DevTools Protocol client (no npm needed)
let WS = globalThis.WebSocket;
if (!WS) { try { WS = (await import('ws')).default; } catch { die('Node 22+ chahiye (ya `npm i ws`). Node update karo.'); } }

const chromePath = findChrome();
if (!chromePath) die('Chrome / Edge nahi mila. Google Chrome install karo, ya CHROME_PATH set karo.');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'reelstudio-'));
const chrome = spawn(chromePath, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--disable-gpu',
  '--allow-file-access-from-files', '--force-device-scale-factor=1', '--window-size=1080,1920', 'about:blank'],
  { stdio: ['ignore', 'ignore', 'pipe'] });
const cleanup = () => { try { chrome.kill('SIGKILL'); } catch {} try { fs.rmSync(profile, { recursive: true, force: true }); } catch {} };
process.on('exit', cleanup);

const wsUrl = await new Promise((res, rej) => {
  let buf = '';
  const to = setTimeout(() => rej(new Error('Browser start nahi hua (30s)')), 30000);
  chrome.stderr.on('data', (d) => {
    buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) { clearTimeout(to); res(m[1]); }
  });
  chrome.on('exit', (c) => { clearTimeout(to); rej(new Error('Browser band ho gaya: ' + c + '\n' + buf.slice(-500))); });
}).catch((e) => die(e.message));

const ws = new WS(wsUrl);
await new Promise((r, j) => { ws.addEventListener('open', r); ws.addEventListener('error', () => j(new Error('CDP connect fail'))); });
let seq = 0; const pending = new Map(); const listeners = [];
ws.addEventListener('message', (ev) => {
  const msg = JSON.parse(typeof ev.data === 'string' ? ev.data : ev.data.toString());
  if (msg.id && pending.has(msg.id)) {
    const { res, rej } = pending.get(msg.id); pending.delete(msg.id);
    msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
  } else if (msg.method) listeners.forEach((l) => l(msg));
});
const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
  const id = ++seq; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params, sessionId }));
});

const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
const S = (m, p) => send(m, p, sessionId);
await S('Page.enable');
await S('Emulation.setDeviceMetricsOverride', { width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false });
const loaded = new Promise((r) => listeners.push((m) => m.method === 'Page.loadEventFired' && m.sessionId === sessionId && r()));
await S('Page.navigate', { url: pathToFileURL(pagePath).href });
await Promise.race([loaded, new Promise((r) => setTimeout(r, 20000))]);
const ready = await S('Runtime.evaluate', { expression: 'window.__ready', awaitPromise: true, returnByValue: true });
if (ready.exceptionDetails) die('Template error: ' + JSON.stringify(ready.exceptionDetails).slice(0, 400));

async function frameAt(t, format = 'jpeg') {
  const r = await S('Runtime.evaluate', { expression: `renderAt(${t.toFixed(4)});1`, returnByValue: true });
  if (r.exceptionDetails) die('Render error at ' + t + 's: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  const shot = await S('Page.captureScreenshot', { format, quality: format === 'jpeg' ? 92 : undefined, optimizeForSpeed: true });
  return Buffer.from(shot.data, 'base64');
}

// ---- stills mode: ek frame har scene se (quick check)
if (flag('--stills')) {
  const dir = path.join(proj, 'stills'); fs.mkdirSync(dir, { recursive: true });
  for (const [i, s] of timings.scenes.entries()) {
    const t = s.start + s.duration - 0.25;
    fs.writeFileSync(path.join(dir, `scene_${String(i + 1).padStart(2, '0')}.jpg`), await frameAt(t));
  }
  console.log(`✅ Preview images: ${dir}`);
  ws.close(); cleanup(); process.exit(0);
}

// ---- full render
const version = (() => { let v = 1; while (fs.existsSync(path.join(proj, `reel_v${v}.mp4`))) v++; return v; })();
const outFile = path.join(proj, `reel_v${version}.mp4`);
const musicDir = path.join(KIT, 'assets', 'music');
const musicName = script.music === false ? null : (script.music || (fs.existsSync(musicDir) ? fs.readdirSync(musicDir).find((f) => /\.(mp3|m4a|wav|aac)$/i.test(f)) : null));
const musicPath = musicName ? path.resolve(musicDir, musicName) : null;
const ff = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-i', path.join(proj, 'voice.wav')];
if (musicPath && fs.existsSync(musicPath)) {
  const vol = script.music_volume ?? 0.12;
  ff.push('-stream_loop', '-1', '-i', musicPath, '-filter_complex',
    `[2:a]volume=${vol},afade=t=out:st=${Math.max(0, total - 1.5).toFixed(2)}:d=1.5[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]`,
    '-map', '0:v', '-map', '[a]');
} else ff.push('-map', '0:v', '-map', '1:a');
ff.push('-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', String(fps),
  '-c:a', 'aac', '-b:a', '192k', '-t', total.toFixed(3), '-movflags', '+faststart', outFile);
const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
enc.on('error', () => die('FFmpeg nahi mila. Setup dobara chalao.'));
const encDone = new Promise((r) => enc.on('close', r));

const t0 = Date.now();
for (let f = 0; f < nFrames; f++) {
  const buf = await frameAt(f / fps);
  if (!enc.stdin.write(buf)) await new Promise((r) => enc.stdin.once('drain', r));
  if (f % fps === 0 || f === nFrames - 1) {
    const pct = ((f + 1) / nFrames * 100).toFixed(0);
    const el = (Date.now() - t0) / 1000, eta = el / (f + 1) * (nFrames - f - 1);
    process.stdout.write(`\r🎬 Rendering ${pct}%  (${f + 1}/${nFrames} frames, ~${Math.ceil(eta)}s baaki)   `);
  }
}
enc.stdin.end();
const code = await encDone;
// cover image for thumbnail
const s0 = timings.scenes[0];
fs.writeFileSync(path.join(proj, 'cover.jpg'), await frameAt(Math.min(s0.duration - 0.1, 2.0)));
ws.close(); cleanup();
if (code !== 0) die('FFmpeg ne error diya (code ' + code + ')');
console.log(`\n✅ Reel ready: ${outFile}  (${total.toFixed(1)} sec, ${Math.round((Date.now() - t0) / 1000)}s me bani)`);
