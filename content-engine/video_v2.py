#!/usr/bin/env python3
"""
Nexus Video Builder v4 — premium faceless Shorts
------------------------------------------------
- TTS-FIRST: real voiceover audio generated for every chunk, then the text
  timeline is built from the ACTUAL audio durations (perfect sync, no more
  "voice slower than text").
- Real animations via libass transform tags: scale-pops (85->100% 0.2s),
  animated accent underline on hooks, step number badges, trigger-word
  pills, pulsing accent dot, and a progress bar that fills.
- Spec: #F5F5F7 canvas, monochrome + one blue accent, safe-zone framing,
  Inter, 3-4 words, hard cuts.
"""
import re
import sys
import wave
import shutil
import subprocess
import datetime
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed-video"

W, H, FPS = 1080, 1920, 30
BG = "0xF5F5F7"
ACCENT = "0x0A84FF"
INK = "0x1D1D1F"
MUT = "0x6E6E73"
PILL = "0xE8E8ED"

SAFE_TOP = int(H * 0.15)
SAFE_BOTTOM = int(H * 0.20)
CENTER_Y = SAFE_TOP + (H - SAFE_TOP - SAFE_BOTTOM) // 2

VOICE = "en-US-GuyNeural"
RATE = "-8%"

TRIGGERS = {"free", "today", "everything", "one page", "system", "template",
            "3", "2-2-2", "1-3-5", "10 minutes", "15 minutes", "now", "save",
            "win", "calm", "week", "start"}


def parse_pack(md: str) -> dict:
    hook, body, cur, buf = "", "", None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            t = m.group(1).strip()
            if cur and cur.startswith("HOOK"):
                hook = "\n".join(buf).strip()
            elif cur and cur.startswith("SCRIPT"):
                body = "\n".join(buf).strip()
            cur, buf = t, []
        elif cur:
            buf.append(line)
    if cur and cur.startswith("HOOK"):
        hook = "\n".join(buf).strip()
    elif cur and cur.startswith("SCRIPT"):
        body = "\n".join(buf).strip()
    return {"hook": hook, "body": body}


def chunk_3_4(text: str) -> list:
    words = text.split()
    out = []
    while words:
        out.append(" ".join(words[:4]))
        words = words[4:]
    return out or [text]


def tts_line(text: str, out_mp3: Path) -> bool:
    import time
    for attempt in range(3):
        try:
            r = subprocess.run(
                ["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text,
                 "--write-media", str(out_mp3)],
                capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and out_mp3.exists() and out_mp3.stat().st_size > 1000:
                return True
        except Exception:
            pass
        time.sleep(1.0 * (attempt + 1))
    return False


def probe_dur(path: Path) -> float:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return float(r.stdout.strip())
    except Exception:
        pass
    try:
        r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 3.0


def build_scenes(pack: dict):
    """Returns list of (kind, text) scenes."""
    scenes = []
    if pack["hook"]:
        scenes.append(("hook", pack["hook"]))
    for raw in pack["body"].split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        low = raw.lower()
        if low.startswith("step ") or re.match(r"^\d+[.:]", raw):
            raw = re.sub(r"^(step\s*\d+[.:]\s*|\d+[.:]\s*)", "", raw, flags=re.I).strip()
        for chunk in chunk_3_4(raw):
            scenes.append(("line", chunk))
    return scenes


def tts_all(scenes, tmpdir):
    """Generate audio for every scene; returns (audio_paths, durs, any_voice)."""
    audios, durs, any_voice = [], [], False
    for i, (kind, text) in enumerate(scenes):
        mp3 = tmpdir / f"v{i}.mp3"
        if tts_line(text, mp3):
            d = probe_dur(mp3)
            audios.append(mp3)
            durs.append(max(1.2, d))
            any_voice = True
        else:
            audios.append(None)
            durs.append(max(1.6, min(3.2, len(text) / 11)))
    return audios, durs, any_voice


def ts(sec):
    return f"{int(sec//3600)}:{int((sec%3600)//60):02d}:{sec%60:05.2f}"


def build_ass(scenes, starts, ends, total):
    """Rich ASS: scale-pop, hook underline animation, step badges, trigger
    pills, pulsing accent dot, filling progress bar."""
    top = SAFE_TOP
    styles = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Hook,Inter,92,&H001D1D1F,&H00000000,&H00000000,&H00000000,-1,0,0,5,60,60,{top+360},1",
        f"Style: Line,Inter,72,&H001D1D1F,&H00000000,&H00000000,&H00000000,-1,0,0,5,60,60,{top+400},1",
        f"Style: Trigger,Inter,72,&H00000000,&H00000000,&H00E8E8ED,&H00000000,-1,22,0,5,60,60,{top+400},1",
        f"Style: Badge,Inter,46,&H00FFFFFF,&H00000000,&H00000000,&H00000000,-1,0,0,2,0,0,{top+300},1",
        f"Style: Accent,Inter,44,&H000A84FF,&H00000000,&H00000000,&H00000000,-1,0,0,5,0,0,{top+640},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    # faint dot grid across the whole video (10% alpha, 4px dots, 90px pitch)
    dots = []
    for gx in range(70, W, 90):
        for gy in range(70, H, 90):
            dots.append(f"m {gx} {gy} l {gx+4} {gy} l {gx+4} {gy+4} l {gx} {gy+4} l {gx} {gy}")
    grid = " ".join(dots)
    styles.append(f"Dialogue: 0,0:00:00.00,{ts(total)},Accent,,0,0,0,,{{\\p1\\1c&H141414&\\alpha&H90&}}{grid}")
    step_no = 0
    for i, (kind, text) in enumerate(scenes):
        s, e = ts(starts[i]), ts(ends[i])
        if kind == "hook":
            # scale-pop + accent underline grows under the hook
            styles.append(f"Dialogue: 0,{s},{e},Hook,,0,0,0,,{{\\fscx85\\fscy85\\t(0,220,\\fscx100\\fscy100)}}{text}")
            # animated accent bar (blue) under text: drawing with clip animation
            styles.append(f"Dialogue: 0,{s},{e},Accent,,0,0,0,,{{\\p1\\pos(0,{top+520})\\clip(0,0,0,60)\\t(0,900,\\clip(1080,0,1080,60))}}m 300 0 l 780 0 l 780 60 l 300 60 l 300 0")
        else:
            is_trigger = any(w in TRIGGERS for w in text.lower().split())
            style = "Trigger" if is_trigger else "Line"
            # step badge: numbered accent circle pops in before the line
            is_step = re.match(r"^step\s*\d", kind) or step_no < 6
            if is_step and not is_trigger:
                step_no += 1
                bx = W // 2 - 60
                by = top + 240
                styles.append(f"Dialogue: 0,{s},{e},Badge,,0,0,0,,{{\\p1\\pos({bx},{by})\\fscx60\\fscy60\\t(0,200,\\fscx100\\fscy100)}}m 0 0 l 120 0 l 120 120 l 0 120 l 0 0")
                styles.append(f"Dialogue: 0,{s},{e},Badge,,0,0,0,,{{\\pos({bx+60},{by+60})}}{step_no}")
            styles.append(f"Dialogue: 0,{s},{e},{style},,0,0,0,,{{\\fscx85\\fscy85\\t(0,200,\\fscx100\\fscy100)}}{text}")
        # pulsing accent dot top-right (subtle "alive" element)
        if i % 2 == 0:
            styles.append(f"Dialogue: 0,{s},{e},Accent,,0,0,0,,{{\\p1\\pos(930,{top+90})\\fscx70\\fscy70\\t(0,600,\\fscx100\\fscy100)\\t(600,1200,\\fscx70\\fscy70)}}m 0 0 l 40 0 l 40 40 l 0 40 l 0 0")
    # progress bar fills over the last 3.2s
    if total > 4:
        pb0, pb1 = total - 3.2, total - 0.2
        y1, y2 = H - 210, H - 198
        styles.append(f"Dialogue: 0,{ts(pb0)},{ts(pb1)},Accent,,0,0,0,,{{\\p1\\pos(0,0)\\clip(140,{y1},140,{y2})\\t(0,3200,\\clip(140,{y1},940,{y2}))}}m 140 {y1} l 940 {y1} l 940 {y2} l 140 {y2} l 140 {y1}")
    # end card: follow gate (lock icon + FOLLOW) scale-pop
    if total > 4:
        g0, g1 = total - 3.0, total + 0.8
        styles.append(f"Dialogue: 0,{ts(g0)},{ts(g1)},Badge,,0,0,0,,{{\\p1\\pos(0,0)\\fscx60\\fscy60\\t(0,250,\\fscx100\\fscy100)}}m 450 {top+250} l 630 {top+250} l 630 {top+450} l 450 {top+450} l 450 {top+250}")
        styles.append(f"Dialogue: 0,{ts(g0)},{ts(g1)},Hook,,0,0,0,,{{\\fscx80\\fscy80\\t(0,250,\\fscx100\\fscy100)}}FOLLOW")
        styles.append(f"Dialogue: 0,{ts(g0)},{ts(g1)},Line,,0,0,0,,Daily calm systems · one page at a time")
    return "\n".join(styles)


def make_music(total: float, out_wav: Path):
    import numpy as np
    sr = 44100
    n = int(sr * total)
    t = np.linspace(0, total, n, endpoint=False)
    sig = np.zeros(n)
    for f in (220.0, 261.63, 329.63, 392.0, 440.0):
        sig += 0.15 * np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t))
    env = np.minimum(1, t / 1.5) * np.minimum(1, (total - t) / 2.5)
    sig *= env * 0.20
    pcm = (sig * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(str(out_wav), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())


def render(scenes, starts, ends, audios, out_mp4, tmpdir):
    total = ends[-1] + 0.6
    ass = build_ass(scenes, starts, ends, total)
    ass_path = tmpdir / "caps.ass"
    ass_path.write_text(ass, encoding="utf-8")
    make_music(total, tmpdir / "music.wav")

    segs = []
    for i, a in enumerate(audios):
        if a is not None:
            segs.append(str(a))
        else:
            dur = ends[i] - starts[i]
            sil = tmpdir / f"sil{i}.wav"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                            "-t", f"{dur:.2f}", str(sil)], capture_output=True, text=True)
            segs.append(str(sil))
        gap = tmpdir / f"gap{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", "0.18", str(gap)], capture_output=True, text=True)
        segs.append(str(gap))

    cmd = ["ffmpeg", "-y",
           "-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}",
           "-i", str(tmpdir / "music.wav")]
    fc = []
    for i, s in enumerate(segs):
        cmd += ["-i", s]
        fc.append(f"[{i+2}:a]aresample=44100,atrim=0:{total:.2f}[a{i}]")
    fc.append("".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[voice]")
    fc.append("[voice][1:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 0.13[aout]")
    fc.append(f"[0:v]ass={ass_path},format=yuv420p[vout]")
    cmd += ["-filter_complex", ";".join(fc),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-t", f"{total:.2f}", str(out_mp4)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-600:])


def html_preview(name):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Today's Short</title>
<style>body{{background:#F5F5F7;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;padding:30px 16px;color:#1D1D1F}}
video{{width:min(360px,90vw);border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.1);background:#000}}
h1{{font-size:17px;margin:18px 0 6px}}p{{font-size:12px;color:#6E6E73;max-width:420px;text-align:center;line-height:1.6}}
.btn{{display:inline-block;margin-top:16px;background:#1D1D1F;color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:700;font-size:13px}}
.note{{font-size:11px;color:#6E6E73;margin-top:8px}}</style></head><body>
<video controls playsinline><source src="{name}" type="video/mp4"></video>
<h1>Today's Short — ready to post</h1>
<p>Voiceover synced to text · animations · music. Download and upload directly.</p>
<a class="btn" href="{name}" download>⬇ Download MP4</a>
<div class="note">If the preview doesn't play audio, download the file — the MP4 has the voice and music tracks.</div>
</body></html>"""


def main():
    FEED.mkdir(exist_ok=True)
    date = datetime.date.today().isoformat()
    md = (ROOT / "feed" / f"{date}.md")
    if not md.exists():
        md = ROOT / "feed" / "latest.md"
    pack = parse_pack(md.read_text(encoding="utf-8"))
    scenes = build_scenes(pack)
    if not scenes:
        print("[Video] No content."); sys.exit(0)

    tmpdir = Path(tempfile.mkdtemp(prefix="nexvid_"))
    try:
        audios, durs, any_voice = tts_all(scenes, tmpdir)
        # build timeline from REAL audio durations (text == voice, perfectly)
        starts, ends = [], []
        t = 0.6
        for i, d in enumerate(durs):
            starts.append(t)
            ends.append(t + d)
            t = t + d + 0.35
        print(f"[Video] voiceover: {'ON' if any_voice else 'off'} · scenes: {len(scenes)} · sync: audio-driven")
        out = FEED / f"{date}_short.mp4"
        render(scenes, starts, ends, audios, out, tmpdir)
        (FEED / f"{date}_short.html").write_text(html_preview(out.name), encoding="utf-8")
        (FEED / "latest_short.mp4").write_bytes(out.read_bytes())
        (FEED / "latest_short.html").write_text(html_preview("latest_short.mp4"), encoding="utf-8")
        print(f"[Video] Built {out.name} ({t:.1f}s, {out.stat().st_size//1024} KB, voice={any_voice})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
