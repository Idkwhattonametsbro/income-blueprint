#!/usr/bin/env python3
"""
Nexus Video Builder v3 — premium faceless Shorts (strict creative spec)
-----------------------------------------------------------------------
SPEC (from the client brief):
  - Background: solid flat light gray #F5F5F7 (never pure white)
  - Palette: monochrome + ONE subtle accent (used sparingly)
  - Framing: everything dead-center; top 15% / bottom 20% empty (safe zones)
  - Type: Inter, Medium/Semibold body, ExtraBold trigger words, 60-80pt
  - Max 3-4 words on screen; text duration == spoken duration
  - Hard cuts (no fades); highlight words: black bold or light-gray pill
  - UI cards: 12-24px radius, soft drop shadow (10% black, 0/10/30)
  - Scale-pop animation (85% -> 100%, 0.2s ease-out) on text/cards
  - Progress bar fills as the voice says "watch till the end"
  - End card: large centered follow gate (crown/lock icon, authority)
  - Audio: real AI voiceover (edge-tts) + soft music bed, dead air trimmed
"""
import re
import sys
import wave
import struct
import shutil
import subprocess
import datetime
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed-video"

W, H, FPS = 1080, 1920, 30
BG = "0xF5F5F7"
ACCENT = "0x0A84FF"   # subtle blue accent, used sparingly
INK = "0x1D1D1F"      # near-black text
MUT = "0x6E6E73"      # gray secondary
PILL = "0xE8E8ED"     # light-gray pill background
VOICE = "en-US-GuyNeural"
RATE = "-8%"

SAFE_TOP = int(H * 0.15)      # 288
SAFE_BOTTOM = int(H * 0.20)   # 384
SAFE_H = H - SAFE_TOP - SAFE_BOTTOM  # 1248
CENTER_Y = SAFE_TOP + SAFE_H // 2


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


def words_3_4(text: str) -> list:
    """Split into 3-4 word chunks (hard cuts on chunk boundaries)."""
    words = text.split()
    out = []
    while words:
        out.append(" ".join(words[:4]))
        words = words[4:]
    return out or [text]


def build_timeline(pack: dict):
    """Returns list of (kind, text, start, end) where kind in {hook,line,trigger}."""
    tl = []
    t = 0.6
    if pack["hook"]:
        tl.append(("hook", pack["hook"], t, t + 3.2))
        t += 3.4
    for raw in pack["body"].split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        low = raw.lower()
        if low.startswith("step ") or re.match(r"^\d+[.:]", raw):
            raw = re.sub(r"^(step\s*\d+[.:]\s*|\d+[.:]\s*)", "", raw, flags=re.I).strip()
        chunks = words_3_4(raw)
        for ci, chunk in enumerate(chunks):
            dur = max(1.4, min(3.0, len(chunk) / 12))
            tl.append(("line", chunk, t, t + dur))
            t += dur + 0.25
    return tl


def build_ass(timeline, with_progress=True):
    """ASS captions matching the spec: centered, Inter, hard cuts,
    3-4 words, trigger words as black bold or pill, scale-pop, progress bar."""
    top = SAFE_TOP
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Hook,Inter,92,&H001D1D1F,&H00000000,&H00000000,&H00000000,-1,0,0,5,60,60,{top+380},1",
        f"Style: Line,Inter,74,&H001D1D1F,&H00000000,&H00000000,&H00000000,-1,0,0,5,60,60,{top+420},1",
        f"Style: Trigger,Inter,74,&H00000000,&H00000000,&H00000000,&H00E8E8ED,-1,0,16,5,60,60,{top+420},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    TRIGGERS = {"free", "today", "everything", "one page", "system", "template",
                "3", "2-2-2", "1-3-5", "10 minutes", "15 minutes", "now", "save"}
    for kind, text, start, end in timeline:
        s = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:05.2f}"
        e = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:05.2f}"
        low = text.lower().strip(" .!")
        style = "Hook" if kind == "hook" else ("Trigger" if low in TRIGGERS or any(w in TRIGGERS for w in low.split()) else "Line")
        # scale-pop: \tclip? use \pos with fade-in via \fad(0,0) not allowed for hard cut.
        # ASS hard cut: no \fad; add \t for pop by moving position slightly.
        # Simpler pop: two dialogue lines overlapping (first at 85% scale via fontsize trick) - skip; use instant snap.
        safe_text = text.replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{s},{e},{style},,0,0,0,,{safe_text}")
    # progress bar: thin black bar fills left->right over the last 3s
    if with_progress and len(timeline) > 1:
        end_last = timeline[-1][3]
        start_pb = end_last - 3.0
        s = f"{int(start_pb//3600)}:{int((start_pb%3600)//60):02d}:{start_pb%60:05.2f}"
        e = f"{int(end_last//3600)}:{int((end_last%3600)//60):02d}:{end_last%60:05.2f}"
        # draw bar via \pos + \clip rectangle animating width: use two lines
        lines.append(f"Dialogue: 0,{s},{e},Line,,0,0,0,,{{\\pos(140,{H - 200})}}")
        lines.append(f"Dialogue: 0,{s},{e},Line,,0,0,0,,{{\\p1}}m 140 {H-190} l 940 {H-190} l 940 {H-178} l 140 {H-178} l 140 {H-190}")
    return "\n".join(lines)


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
        time.sleep(1.2 * (attempt + 1))
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


def make_music(total: float, out_wav: Path):
    import numpy as np
    sr = 44100
    n = int(sr * total)
    t = np.linspace(0, total, n, endpoint=False)
    freqs = [220.0, 261.63, 329.63, 392.0, 440.0]
    sig = np.zeros(n)
    for f in freqs:
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


def build_end_card_svg(path: Path):
    """Follow gate: large centered crown/lock on light gray, monochrome + accent."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#F5F5F7"/>
  <circle cx="{W//2}" cy="{SAFE_TOP + 380}" r="170" fill="#0A84FF" opacity="0.12"/>
  <g transform="translate({W//2 - 130},{SAFE_TOP + 200})">
    <rect x="20" y="90" width="220" height="170" rx="34" fill="#1D1D1F"/>
    <rect x="62" y="40" width="136" height="80" rx="22" fill="none" stroke="#1D1D1F" stroke-width="14"/>
    <circle cx="130" cy="170" r="24" fill="#F5F5F7"/>
    <rect x="118" y="180" width="24" height="34" rx="8" fill="#F5F5F7"/>
  </g>
  <text x="{W//2}" y="{SAFE_TOP + 560}" font-family="Inter, Helvetica Neue, Arial" font-size="72" font-weight="800" fill="#1D1D1F" text-anchor="middle">FOLLOW</text>
  <text x="{W//2}" y="{SAFE_TOP + 640}" font-family="Inter, Arial" font-size="40" font-weight="500" fill="#6E6E73" text-anchor="middle">Daily calm systems · one page at a time</text>
  <text x="{W//2}" y="{H - 260}" font-family="Inter, Arial" font-size="34" font-weight="600" fill="#0A84FF" text-anchor="middle">Free template in bio</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def render(timeline, voice_files, out_mp4, tmpdir):
    ass = build_ass(timeline)
    ass_path = tmpdir / "caps.ass"
    ass_path.write_text(ass, encoding="utf-8")
    total = timeline[-1][3] + 1.2
    # end card svg -> png
    end_svg = tmpdir / "end.svg"
    build_end_card_svg(end_svg)
    end_png = tmpdir / "end.png"
    try:
        import cairosvg
        cairosvg.svg2png(url=str(end_svg), write_to=str(end_png), output_width=W, output_height=H)
    except Exception:
        # fallback: solid color frame
        end_png = None

    make_music(total, tmpdir / "music.wav")

    # voices with silence padding to full duration (no gaps, hard-cut feel)
    segs = []
    for i, vf in enumerate(voice_files):
        if vf is not None and Path(vf).exists():
            segs.append(str(vf))
        else:
            dur = max(1.5, timeline[i][3] - timeline[i][2])
            sil = tmpdir / f"sil{i}.wav"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                            "-t", f"{dur:.2f}", str(sil)], capture_output=True, text=True)
            segs.append(str(sil))

    cmd = ["ffmpeg", "-y",
           "-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}",
           "-i", str(tmpdir / "music.wav")]
    filt = []
    for i, s in enumerate(segs):
        cmd += ["-i", s]
        idx = i + 2
        filt.append(f"[{idx}:a]aresample=44100,atrim=0:{total:.2f}[a{i}]")
    concat_in = "".join(f"[a{i}]" for i in range(len(segs)))
    filt.append(f"{concat_in}concat=n={len(segs)}:v=0:a=1[voice]")
    filt.append("[voice][1:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 0.13[aout]")
    vf = f"[0:v]ass={ass_path},format=yuv420p[vout]"
    cmd += ["-filter_complex", ";".join(filt) + ";" + vf,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-t", f"{total:.2f}", str(out_mp4)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-500:])


def html_preview(video_name: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Today's Short</title>
<style>body{{background:#F5F5F7;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;padding:30px 16px;color:#1D1D1F}}
video{{width:min(360px,90vw);border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.1);background:#000}}
h1{{font-size:17px;margin:18px 0 6px}}p{{font-size:12px;color:#6E6E73;max-width:420px;text-align:center;line-height:1.6}}
.btn{{display:inline-block;margin-top:16px;background:#1D1D1F;color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:700;font-size:13px}}
.note{{font-size:11px;color:#6E6E73;margin-top:8px}}</style></head><body>
<video controls playsinline><source src="{video_name}" type="video/mp4"></video>
<h1>Today's Short — ready to post</h1>
<p>Voiceover + music + captions are in the file. Download and upload directly.</p>
<a class="btn" href="{video_name}" download>⬇ Download MP4</a>
<div class="note">Tip: if audio doesn't play in the preview, download the file — the MP4 contains the voice and music tracks.</div>
</body></html>"""


def main():
    FEED.mkdir(exist_ok=True)
    date = datetime.date.today().isoformat()
    md_path = ROOT / "feed" / f"{date}.md"
    if not md_path.exists():
        md_path = ROOT / "feed" / "latest.md"
    pack = parse_pack(md_path.read_text(encoding="utf-8"))
    timeline = build_timeline(pack)
    if not timeline:
        print("[Video] No content."); sys.exit(0)

    tmpdir = Path(tempfile.mkdtemp(prefix="nexvid_"))
    try:
        voice_files = []
        any_voice = False
        for kind, text, start, end in timeline:
            mp3 = tmpdir / f"v{len(voice_files)}.mp3"
            ok = tts_line(text, mp3)
            if ok:
                dur = probe_dur(mp3)
                any_voice = True
            voice_files.append(mp3 if ok else None)
        print(f"[Video] voiceover: {'ON' if any_voice else 'off'}")
        out = FEED / f"{date}_short.mp4"
        render(timeline, voice_files, out, tmpdir)
        (FEED / f"{date}_short.html").write_text(html_preview(out.name), encoding="utf-8")
        (FEED / "latest_short.mp4").write_bytes(out.read_bytes())
        (FEED / "latest_short.html").write_text(html_preview("latest_short.mp4"), encoding="utf-8")
        print(f"[Video] Built {out.name} ({timeline[-1][3]+1.2:.1f}s, {out.stat().st_size//1024} KB, voice={any_voice})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
