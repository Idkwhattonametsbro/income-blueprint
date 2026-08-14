#!/usr/bin/env python3
"""
Nexus Daily Content Engine
--------------------------
Generates ONE publish-ready post pack every day (hook, script, title,
caption, hashtags, pin comment, thumbnail idea) with a human, professional
tone, saves it to feed/, and emails it to you via Gmail SMTP if configured.

Runs with ZERO API keys (uses built-in template banks). With keys it
generates fresh content via the best available provider.

Secrets (all optional):
  GROQ_API_KEY / GEMINI_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY
  GMAIL_USER + GMAIL_APP_PASSWORD   (to receive the daily email)
"""
import json
import os
import re
import sys
import smtplib
import random
import datetime
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed"
CONFIG = ROOT / "content-engine" / "config.json"

# ----------------------------------------------------------------------------
# Template banks (keyless mode) - human-written, professional, on-niche
# ----------------------------------------------------------------------------
HOOKS = [
    "Your week is a mess because you have no system - here's the 5-minute fix.",
    "I stopped buying planners. This free one-page reset does more.",
    "3 apps you already have that can replace $200 of productivity tools.",
    "Do this every Sunday night and Monday stops feeling like a war.",
    "The 2-2-2 rule: the cheapest way to get a calmer week.",
    "Your to-do list is too long. Cut it to 3 things and watch what happens.",
    "Stop organizing your whole life. Organize the next 7 days.",
    "The 10-minute evening that makes tomorrow effortless.",
    "Free template inside: the weekly reset that takes one page.",
    "You don't need a new app. You need a shutdown ritual.",
    "The 1-3-5 rule explained in 30 seconds.",
    "How broke students actually get organized (no course, no app).",
    "This Sunday ritual takes 15 minutes and saves you 5 hours.",
    "Your phone is the problem. Here's the 3-tab setup that fixes it.",
    "Everything in my weekly system fits on one page - here it is.",
    "If you can't keep a habit for a week, you're not the problem. The system is.",
]

BODIES = [
    "15 minutes on Sunday night. That's the whole investment.\n\nStep 1: brain dump - write everything floating in your head on one page. The mess lives in your head, not your calendar.\nStep 2: pick 3 - circle the three things that actually matter this week. Everything else is a bonus.\nStep 3: one anchor - one meal, one walk, one early night. One thing that keeps the week human.\n\nThat's the reset. One page. Free template in the link in bio.",
    "The 1-3-5 rule: one big thing, three medium things, five small things. That's a realistic day.\n\nBig = takes real focus, moves your life. Medium = about 30 minutes. Small = quick wins.\n\nIf you finish the 1 and the 3, the day was a win. The 5 are just gravy.\n\nYour list isn't a promise - it's a menu. Pick what fits the day.",
    "The 2-2-2 rule: the cheapest way to get a calmer week.\n\nTwo hours a week for yourself. No work, no phone. Boring is fine.\nTwo hours for one person who matters to you. Coffee, walk, call.\nTwo hours for future you - one small thing that makes next week easier.\n\nThat's 6 hours out of 168. You can afford it, even broke.",
    "When does your day actually end? If the answer is 'never', fix it tonight.\n\nPick a time. At that time, three things:\n1. Write tomorrow's 3 tasks. Your brain can stop holding them.\n2. Close every tab - phone and brain.\n3. One sentence: 'Done for today.' Say it out loud.\n\nTen minutes. The end of the day becomes a door you close instead of a wall you fall through.",
    "Every Sunday night, same three moves:\n\n1. Clean slate - wipe last week's list. Guilt doesn't live in this system.\n2. Plan meals and money - one line each. Broke-friendly means predictable.\n3. Put one fun thing in the calendar first. Not last. First.\n\nMonday then feels like a start, not a surprise. Free template in the link in bio.",
    "You don't need Notion. You don't need a 47-step productivity guru system.\n\nOne notebook, one pen, one page a day:\n- Top: today's 3.\n- Middle: the deadline that scares you.\n- Bottom: one line you're grateful for.\n\nCost: about 20 cents a week. The students who pass aren't more disciplined - they have a system small enough to keep.",
    "Ten minutes before bed, four moves:\n\n1. Phone across the room. You'll thank me at 2AM.\n2. Tomorrow's clothes out (or bag packed).\n3. Tomorrow's 3 tasks written down.\n4. Water on the nightstand.\n\nThat's it. Future-you starts the day already winning.",
    "Every habit system assumes you have time, energy, and a clean desk.\nBroke, tired, and overwhelmed is a different game.\n\nSmaller than you think: 3 tasks, 10-minute evening, one page.\nSlower than you want: one habit at a time, two weeks minimum.\n\nBoring is the point. Boring systems survive. Exciting ones die by Thursday.",
]

TITLES = [
    "The 15-minute Sunday ritual that fixes your week",
    "The 1-3-5 rule for a realistic day",
    "The 2-2-2 rule: the cheapest way to a calmer week",
    "The 10-minute evening that makes tomorrow effortless",
    "How broke students get organized (no course, no app)",
    "The one-page system that replaces productivity apps",
    "The shutdown ritual that ends your day properly",
    "Why boring systems beat exciting ones",
]

CAPTIONS = [
    "Your week doesn't need more apps. It needs one page. Save this for Sunday night - and grab the free template from the link in bio.",
    "The 1-3-5 rule: one big, three medium, five small. Finish the 1 and the 3 and the day is a win. Save this for tomorrow morning.",
    "Six hours out of 168. That's all the 2-2-2 rule costs - and it buys you a calmer week. Which 2 are you taking first?",
    "Ten minutes tonight. Four moves. Tomorrow starts already winning. Save this so you remember at bedtime.",
    "No course. No app. Twenty cents a week. The one-page system that actually works when you're broke and tired. Free template in the link in bio.",
    "Apps add features. This system subtracts. One page is easier to keep than any app. Link in bio for the free template.",
    "A door you close instead of a wall you fall through. That's what a shutdown ritual does. Try it tonight.",
    "Boring systems survive. Exciting ones die by Thursday. This is the boring one that works. Follow for the whole system.",
]

PIN_COMMENTS = [
    "Free weekly reset template -> link in bio. Full 8-page kit when it's ready - follow so you don't miss it.",
    "The free one-page reset is in the link in bio. Want the whole 8-page Calm Week System? It's live now.",
    "Save this for Sunday night. Free template in the link in bio.",
]

THUMB_IDEAS = [
    "One-page planner mockup, big text: 'ONE PAGE. CALM WEEK.' orange accent.",
    "Phone screenshot of a clean 3-task list, big text: '3 THINGS ONLY.'",
    "Calendar close-up, one circle drawn around Sunday, text: '15 MIN SUNDAY.'",
    "Notebook + pen flat-lay, text: 'NO APP NEEDED.'",
    "Two-column visual: messy brain vs one page, text: 'BRAIN DUMP FIRST.'",
]


def load_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"niche": "calm weekly systems", "tone": "human and professional"}


def pick(pool):
    return random.choice(pool)


def build_template_post(cfg):
    hook = pick(HOOKS)
    body = pick(BODIES)
    title = pick(TITLES)
    caption = pick(CAPTIONS)
    pin = pick(PIN_COMMENTS)
    thumb = pick(THUMB_IDEAS)
    return {
        "hook": hook,
        "body": body,
        "title": title,
        "caption": caption,
        "pin": pin,
        "thumb": thumb,
        "mode": "template",
    }


# ----------------------------------------------------------------------------
# LLM mode (fresh content, human tone enforced)
# ----------------------------------------------------------------------------
PROVIDERS = [
    ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
    ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-2.5-flash"),
    ("DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions", "deepseek-v4-flash"),
    ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "nvidia/nemotron-3-ultra-550b-a55b:free"),
]


def llm_generate(cfg):
    import requests

    prompt = f"""You are a professional short-form content writer for a faceless YouTube Shorts / TikTok channel.

NICHE: {cfg.get('niche')}
NORTH STAR: {cfg.get('north_star')}
PRODUCT TO PROMOTE (mention naturally once, never hard-sell): {cfg.get('product')}
FREEBIE: {cfg.get('freebie')}
TONE RULES: write like a smart human friend who happens to be a professional. Conversational, warm, specific.
NEVER use: 'delve', 'unlock', 'game-changer', 'in today's fast-paced world', 'elevate', 'embark', emoji spam.
Keep sentences short. One clear idea. No fluff.

Produce TODAY'S POST PACK exactly in this format (plain text, no JSON):

HOOK (1 sentence, first second, no intro):
[hook]

SCRIPT (40-55 seconds, voice-over lines separated by blank lines, with bold-style on-screen text marked with *asterisks*):
[script]

TITLE (under 60 chars):
[title]

CAPTION (2-3 sentences, ends with a soft CTA):
[caption]

HASHTAGS (3 max):
[tags]

PIN COMMENT (one line):
[pin]

THUMBNAIL IDEA (one line):
[thumb]

Make it sound human and professional. Make it genuinely useful to the viewer."""

    errors = []
    for env_key, url, model in PROVIDERS:
        key = os.getenv(env_key)
        if not key:
            continue
        try:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are Nexus, a professional content engine. Output only the requested format. Human tone. No markdown headers beyond the format given."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                return parse_pack(text), model
            errors.append(f"{env_key}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"{env_key}: {e}")
    return None, " | ".join(errors)


def parse_pack(text):
    """Best-effort parse of the LLM's text pack into a dict."""
    out = {
        "hook": "", "body": "", "title": "", "caption": "",
        "pin": "", "thumb": "", "mode": "llm", "raw": text.strip(),
    }
    markers = {
        "hook": "HOOK", "body": "SCRIPT", "title": "TITLE",
        "caption": "CAPTION", "pin": "PIN COMMENT", "thumb": "THUMBNAIL IDEA",
    }
    lines = text.splitlines()
    current = None
    buf = []
    for line in lines:
        upper = line.strip().upper()
        matched = None
        for key, marker in markers.items():
            if upper.startswith(marker):
                matched = key
                break
        if matched:
            if current:
                out[current] = "\n".join(buf).strip()
            current = matched
            buf = []
        elif current:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf).strip()
    if not out["body"]:
        out["body"] = text.strip()
    return out


# ----------------------------------------------------------------------------
# Rendering + delivery
# ----------------------------------------------------------------------------
def render_markdown(post, cfg):
    d = datetime.date.today().isoformat()
    return f"""# Today's Post Pack · {d}

**Niche:** {cfg.get('niche')}

---

## HOOK (first second, no intro)
{post.get('hook', '')}

## SCRIPT (40-55s voice-over)
{post.get('body', '')}

## TITLE
{post.get('title', '')}

## CAPTION
{post.get('caption', '')}

## HASHTAGS (3 max)
#calmproductivity #weeklyreset #{cfg.get('niche', '').split()[0].lower() if cfg.get('niche') else 'planner'}

## PIN COMMENT
{post.get('pin', '')}

## THUMBNAIL IDEA
{post.get('thumb', '')}

---
**Post at:** {cfg.get('posting_times', 'evening')} · **Platform:** {cfg.get('home_platform')} then mirror to {cfg.get('mirror_platform')}
**Product link:** {cfg.get('product')} · **Freebie:** {cfg.get('freebie')}
**Generated by:** Nexus Content Engine · mode: {post.get('mode', 'template')}
"""


def email_digest(subject, body):
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if not user or not pw:
        print("[Email] Skipped - GMAIL_USER/GMAIL_APP_PASSWORD not set. Dashboard link works instead.")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Nexus Content Engine", user))
        msg["To"] = user
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        print(f"[Email] Sent to {user}")
    except Exception as e:
        print(f"[Email] Failed: {e}")


def main():
    cfg = load_config()
    FEED.mkdir(exist_ok=True)

    post, model = llm_generate(cfg)
    if post is None:
        print(f"[Engine] LLM unavailable ({model}) - using template bank.")
        post = build_template_post(cfg)
    else:
        print(f"[Engine] Generated fresh content via {model}")

    today = datetime.date.today().isoformat()
    md = render_markdown(post, cfg)

    # feed/YYYY-MM-DD.md + feed/latest.md + feed/history.json
    (FEED / f"{today}.md").write_text(md, encoding="utf-8")
    (FEED / "latest.md").write_text(md, encoding="utf-8")

    history_path = FEED / "history.json"
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            history = []
    if today not in history:
        history.append(today)
    history_path.write_text(json.dumps(history[-90:], indent=2), encoding="utf-8")

    print(f"[Engine] Saved feed/{today}.md + feed/latest.md")

    # Email the digest (only if configured)
    email_digest(f"Today's Post Pack · {today} · copy-paste ready", md)

    # Print the pack for the workflow log
    print("\n" + "=" * 60)
    print(md)
    print("=" * 60)


if __name__ == "__main__":
    main()
