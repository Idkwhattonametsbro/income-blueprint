#!/usr/bin/env python3
"""
Nexus Video Builder v2 — premium faceless Shorts
------------------------------------------------
Real AI voiceover (edge-tts, free, no key), animated cinematic background,
soft ambient music bed, and styled synced captions. Output: a playable MP4
you upload directly. No recording, no editing.

Requires: ffmpeg, edge-tts, numpy (installed in CI).
"""
import json
import os
import re
import sys
import wave
import struct
import subprocess
import datetime
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed-video"

W, H, FPS = 1080, 1920, 30
VOICE = "en-US-GuyNeural"
RATE = "-8%"

TAG_MAP = {
    "step 1": "STEP 1", "step 2": "STEP 2", "step 3": "STEP 3",
    "step 4": "STEP 4", "1.": "STEP 1", "2.": "STEP 2", "3.": "STEP 3",
}


def parse_pack(md: str) -> dict:
    hook, body, cur, buf = "", "", None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            title = m.group(1).strip()
            if cur and cur.startswith("HOOK"):
                hook = "\n".join(buf).strip()
            elif cur and cur.startswith("SCRIPT"):
                body = "\n".join(buf).strip()
            cur, buf = title, []
        elif cur:
            buf.append(line)
    if cur and cur.startswith("HOOK"):
        hook = "\n".join(buf).strip()
    elif cur and cur.startswith("SCRIPT"):
        body = "\n".join(buf).strip()
    return {"hook": hook, "body": body}


def lines_for_video(pack: dict):
    out = []
    if pack["hook"]:
        out.append(("HOOK", pack["hook"]))
    for raw in pack["body"].split("\n"):
        t = raw.strip()
        if not t:
            continue
        low = t.lower()
        tag = None
        for k, v in TAG_MAP.items():
            if low.startswith(k):
                tag = v
                t = t[len(k):].lstrip(":. -").strip()
                break
        if not t:
            continue
        if len(t) > 88:
            t = t[:85].rsplit(" ", 1)[0] + "..."
        out.append((tag or "CALM WEEK", t))
    return out


def tts_line(text: str, out_mp3: Path) -> bool:
    """Generate voiceover with edge-tts (free). Retries on flaky first calls."""
    import time
    for attempt in range(3):
        try:
            r = subprocess.run(
                ["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text,
                 "--write-media", str(out_mp3)],
                capture_output=True, text=True, timeout=60,
            )
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
    # fallback: parse ffmpeg -i Duration line
    try:
        r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 3.0


def make_music(total: float, out_wav: Path):
    """Soft ambient pad - royalty-free because we synthesize it."""
    import numpy as np
    sr = 44100
    n = int(sr * total)
    t = np.linspace(0, total, n, endpoint=False)
    # Am7-ish warm pad: A3, C4, E4, G4 + octave shimmer
    freqs = [220.0, 261.63, 329.63, 392.0, 440.0]
    sig = np.zeros(n)
    for f in freqs:
        sig += 0.16 * np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
    # slow swell + fade edges
    env = np.minimum(1, t / 2.0) * np.minimum(1, (total - t) / 3.0)
    sig *= env
    sig *= 0.22  # keep it under the voice
    pcm = (sig * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(str(out_wav), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())


def build_ass(lines, timeline) -> str:
    """Premium caption style: big white bold + orange tag kicker."""
    ass = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Tag,Inter,40,&H00EA580C,&H00000000,&H00000000,&H00000000,-1,0,0,5,0,0,430,1",
        "Style: Big,Inter,88,&H00FFFFFF,&H00000000,&H00101010,&H00000000,-1,5,3,5,80,80,430,1",
        "Style: Hook,Inter,100,&H00FFFFFF,&H00000000,&H00101010,&H00000000,-1,6,4,5,80,80,430,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, (tag, text, start, end) in enumerate(timeline):
        s = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:05.2f}"
        e = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:05.2f}"
        style = "Hook" if tag == "HOOK" else "Big"
        ass.append(f"Dialogue: 0,{s},{e},{style},,0,0,0,,{{\\fad(280,280)}}{text.replace(chr(10),'\\N')}")
        if tag != "HOOK":
            # tag kicker appears just above
            t0 = start
            t1 = min(end, start + 1.2)
            s2 = f"{int(t0//3600)}:{int((t0%3600)//60):02d}:{t0%60:05.2f}"
            e2 = f"{int(t1//3600)}:{int((t1%3600)//60):02d}:{t1%60:05.2f}"
            ass.append(f"Dialogue: 0,{s2},{e2},Tag,,0,0,0,,{{\\fad(200,200)}}{tag}")
    return "\n".join(ass)


def render(lines, voice_files, timeline, bg, out_mp4, tmpdir):
    ass = build_ass(lines, timeline)
    ass_path = tmpdir / "caps.ass"
    ass_path.write_text(ass, encoding="utf-8")
    total = timeline[-1][3] + 0.4

    make_music(total, tmpdir / "music.wav")

    # audio segments: voice (or silence of the right length) + small gap
    segs = []
    for i, vf in enumerate(voice_files):
        if vf is not None and Path(vf).exists():
            segs.append(str(vf))
        else:
            dur = timeline[i][3] - timeline[i][2]
            sil = tmpdir / f"sil{i}.wav"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                            "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.2f}", str(sil)],
                           capture_output=True, text=True)
            segs.append(str(sil))
        gap = tmpdir / f"gap{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=stereo", "-t", "0.3", str(gap)],
                       capture_output=True, text=True)
        segs.append(str(gap))

    # inputs: [0]=bg, [1]=music, [2..]=segs
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "gradients=size=1080x1920:speed=0.04:c0=0xFFF7ED:c1=0xFFE8D6:c2=0xFFFDFC",
        "-i", str(tmpdir / "music.wav"),
    ]
    filt = []
    for i, s in enumerate(segs):
        cmd += ["-i", s]
        idx = i + 2
        filt.append(f"[{idx}:a]aresample=44100,atrim=0:{total:.2f}[a{i}]")
    concat_in = "".join(f"[a{i}]" for i in range(len(segs)))
    filt.append(f"{concat_in}concat=n={len(segs)}:v=0:a=1[voice]")
    filt.append("[voice][1:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 0.14[aout]")
    filt.append(f"[0:v]vignette=PI/5,noise=alls=6:allf=t+u,ass={ass_path},format=yuv420p[vout]")

    cmd += ["-filter_complex", ";".join(filt),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-t", f"{total:.2f}",
            str(out_mp4)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-500:])


def html_preview(video_name: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Today's Short</title>
<style>body{{background:#F6F5F2;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;padding:30px 16px;color:#3F3A34}}
video{{width:min(360px,90vw);border-radius:20px;box-shadow:0 10px 34px rgba(28,25,23,.15)}}h1{{font-size:17px;margin:18px 0 6px}}p{{font-size:12px;color:#8A8378;max-width:420px;text-align:center;line-height:1.6}}
.btn{{display:inline-block;margin-top:16px;background:linear-gradient(135deg,#FB923C,#EA580C);color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:700;font-size:13px}}
</style></head><body>
<video controls autoplay muted playsinline><source src="{video_name}" type="video/mp4"></video>
<h1>Today's Short — ready to post</h1>
<p>Voiceover, music and captions are already in the file. Download and upload to YouTube Shorts / TikTok.</p>
<a class="btn" href="{video_name}" download>⬇ Download MP4</a>
</body></html>"""


def main():
    FEED.mkdir(exist_ok=True)
    date = datetime.date.today().isoformat()
    md_path = ROOT / "feed" / f"{date}.md"
    if not md_path.exists():
        md_path = ROOT / "feed" / "latest.md"
    pack = parse_pack(md_path.read_text(encoding="utf-8"))
    lines = lines_for_video(pack)
    if not lines:
        print("[Video] No content."); sys.exit(0)

    tmpdir = Path(tempfile.mkdtemp(prefix="nexvid_"))
    try:
        # 1) voiceover per line (free edge-tts; fallback = silent)
        voice_files, timeline, t = [], [], 0.5
        any_voice = False
        for tag, text in lines:
            mp3 = tmpdir / f"v{len(voice_files)}.mp3"
            ok = tts_line(text, mp3)
            if ok:
                dur = probe_dur(mp3) + 0.4
                any_voice = True
            else:
                dur = max(2.2, min(5.0, len(text) / 13))
            voice_files.append(mp3 if ok else None)
            timeline.append((tag, text, t, t + dur))
            t += dur + 0.3
        print(f"[Video] voiceover: {'ON' if any_voice else 'off (edge-tts unavailable)'}")

        out = FEED / f"{date}_short.mp4"
        render(lines, voice_files, timeline, None, out, tmpdir)
        (FEED / f"{date}_short.html").write_text(html_preview(out.name), encoding="utf-8")
        (FEED / "latest_short.mp4").write_bytes(out.read_bytes())
        (FEED / "latest_short.html").write_text(html_preview("latest_short.mp4"), encoding="utf-8")
        print(f"[Video] Built {out.name} ({t:.1f}s, {out.stat().st_size//1024} KB, voice={any_voice})")
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
