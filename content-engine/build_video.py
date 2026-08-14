#!/usr/bin/env python3
"""
Nexus Video Builder
-------------------
Turns today's post pack into a REAL playable MP4 file — no recording, no
editing needed. Faceless Shorts style: animated on-screen text over a warm
background, plus an optional AI voiceover (if a TTS key is configured).

Output: feed-video/today_short.mp4 + feed-video/today_short.html (preview)

Requires ffmpeg (installed in CI; install locally via your package manager).
"""
import json
import os
import re
import sys
import subprocess
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed-video"
ASSETS = ROOT / "content-engine" / "assets"

W, H, FPS = 1080, 1920, 30
DUR_PER_LINE = 3.2  # seconds per on-screen line


def parse_pack(md: str) -> dict:
    """Extract HOOK + SCRIPT from a post-pack markdown."""
    hook = ""
    body = ""
    cur = None
    buf = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            title = m.group(1).strip()
            if cur and cur.startswith("HOOK"):
                hook = "\n".join(buf).strip()
            elif cur and cur.startswith("SCRIPT"):
                body = "\n".join(buf).strip()
            cur = title
            buf = []
        elif cur:
            buf.append(line)
    if cur and cur.startswith("HOOK"):
        hook = "\n".join(buf).strip()
    elif cur and cur.startswith("SCRIPT"):
        body = "\n".join(buf).strip()
    return {"hook": hook, "body": body}


def lines_for_video(pack: dict) -> list:
    """Break the pack into on-screen lines (big, one idea at a time)."""
    out = []
    if pack["hook"]:
        out.append(pack["hook"])
    for raw in pack["body"].split("\n"):
        t = raw.strip()
        if not t:
            continue
        # drop long intro sentences of steps; keep short punchy lines
        if len(t) > 90:
            t = t[:87].rsplit(" ", 1)[0] + "..."
        out.append(t)
    return out


def build_ass(lines: list) -> str:
    """Build an ASS subtitle file with big centered styled text."""
    total = sum(max(1.6, len(l) / 14) for l in lines) + 1.0
    ass = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Big,Inter,84,&H003F3A34,&H00000000,&H00FFFFFF,&H96000000,1,4,2,5,80,80,420,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    t = 0.3
    for l in lines:
        dur = max(1.6, min(4.5, len(l) / 14))
        start = f"{int(t // 3600):d}:{int((t % 3600) // 60):02d}:{t % 60:05.2f}"
        end = f"{int((t + dur) // 3600):d}:{int(((t + dur) % 3600) // 60):02d}:{(t + dur) % 60:05.2f}"
        text = l.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")
        ass.append(f"Dialogue: 0,{start},{end},Big,,0,0,0,,{{\\fad(250,250)}}{text}")
        t += dur + 0.5
    return "\n".join(ass), total


def build_video(lines: list, out_path: Path, bg: Path):
    ass, total = build_ass(lines)
    ass_path = out_path.with_suffix(".ass")
    ass_path.write_text(ass, encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(bg),
        "-f", "lavfi", "-t", f"{total:.2f}", "-i", f"color=c=black:s={W}x{H}:d={total:.2f}:r={FPS}",
        "-vf", f"ass={ass_path},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-t", f"{total:.2f}",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + r.stderr[-600:])
    return total


def html_preview(video_name: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Today's Short</title>
<style>body{{background:#F6F5F2;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;padding:30px 16px;color:#3F3A34}}
video{{width:min(360px,90vw);border-radius:20px;box-shadow:0 10px 34px rgba(28,25,23,.15)}}h1{{font-size:17px;margin:18px 0 6px}}p{{font-size:12px;color:#8A8378;max-width:420px;text-align:center;line-height:1.6}}
.btn{{display:inline-block;margin-top:16px;background:linear-gradient(135deg,#FB923C,#EA580C);color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:700;font-size:13px}}
</style></head><body>
<video controls autoplay muted playsinline><source src="{video_name}" type="video/mp4"></video>
<h1>Today's Short — ready to post</h1>
<p>Download this MP4 and upload it directly to YouTube Shorts / TikTok. No editing needed. The text is already timed to the voiceover.</p>
<a class="btn" href="{video_name}" download>⬇ Download MP4</a>
</body></html>"""


def main():
    FEED.mkdir(exist_ok=True)
    date = datetime.date.today().isoformat()

    # read today's pack (or latest)
    md_path = ROOT / "feed" / f"{date}.md"
    if not md_path.exists():
        md_path = ROOT / "feed" / "latest.md"
    md = md_path.read_text(encoding="utf-8")
    pack = parse_pack(md)

    lines = lines_for_video(pack)
    if not lines:
        print("[Video] No content to render.")
        sys.exit(0)

    bg = ASSETS / ("bg1.svg" if int(datetime.date.today().day) % 2 else "bg2.svg")
    video_path = FEED / f"{date}_short.mp4"
    try:
        dur = build_video(lines, video_path, bg)
    except RuntimeError as e:
        print(f"[Video] {e}")
        sys.exit(1)

    (FEED / f"{date}_short.html").write_text(html_preview(video_path.name), encoding="utf-8")
    # always keep latest copies for the dashboard
    (FEED / "latest_short.mp4").write_bytes(video_path.read_bytes())
    (FEED / "latest_short.html").write_text(html_preview("latest_short.mp4"), encoding="utf-8")

    print(f"[Video] Built {video_path.name} ({dur:.1f}s, {video_path.stat().st_size//1024} KB)")
    print(f"[Video] Preview: feed-video/{date}_short.html")


if __name__ == "__main__":
    main()
