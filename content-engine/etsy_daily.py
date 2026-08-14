#!/usr/bin/env python3
"""
Nexus Daily Etsy Engine
-----------------------
Generates ONE publish-ready Etsy product pack every day:
  - a proven product idea (rotating through high-demand categories)
  - a full listing (140-char title, 13 tags, premium description, price)
  - an image/branding brief
  - an ACTUAL product file (a print-perfect printable HTML page) you can
    screenshot or PDF-export and upload today

Delivered to feed-etsy/ (dashboard) + Gmail (if configured), same as the
video engine. Premium, human, professional tone. No AI-slop wording.
"""
import json
import os
import re
import sys
import random
import smtplib
import datetime
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product_assets import PRODUCT_PAGES_V2, render_cover

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed-etsy"

BANNED = ["delve", "unlock", "game-changer", "elevate", "embark", "fast-paced world",
          "revolutionize", "unleash", "supercharge", "in today's", "cutting-edge"]

# ----------------------------------------------------------------------------
# Product idea bank (proven Etsy digital categories, rotating)
# ----------------------------------------------------------------------------
PRODUCT_IDEAS = [
    {
        "name": "Minimal Budget Tracker Printable",
        "category": "Spreadsheet / printable finance",
        "why": "Budget trackers are perennial Etsy bestsellers - high buyer intent, impulse-priced, no inventory.",
        "price": 5,
        "file": "budget",
    },
    {
        "name": "ADHD Daily Planner Printable",
        "category": "Planner / printable",
        "why": "ADHD planners are a documented untapped market on Etsy - specific audience, low competition.",
        "price": 6,
        "file": "adhd",
    },
    {
        "name": "Student Semester Planner Pack",
        "category": "Planner / printable",
        "why": "Students buy planners every term - evergreen, seasonal spikes (back-to-school).",
        "price": 6,
        "file": "semester",
    },
    {
        "name": "Canva Social Media Template Kit",
        "category": "Design asset",
        "why": "Small businesses pay for ready-made branding without hiring a designer - high value per item.",
        "price": 9,
        "file": "canva",
    },
    {
        "name": "Meal Planner + Grocery List Printable",
        "category": "Printable / home",
        "why": "Meal planning printables have steady demand and gift appeal - easy to screenshot for the listing.",
        "price": 4,
        "file": "meal",
    },
    {
        "name": "Digital Wall Art Quote Set (3-pack)",
        "category": "Wall art / print",
        "why": "Digital wall art is an impulse-buy category - three files per listing raises perceived value.",
        "price": 5,
        "file": "wallart",
    },
    {
        "name": "Habit Tracker + Yearly Overview",
        "category": "Planner / printable",
        "why": "Habit trackers combine planner + self-improvement demand - two files, one listing.",
        "price": 5,
        "file": "habits",
    },
    {
        "name": "Wedding Planning Checklist Pack",
        "category": "Planner / event",
        "why": "Wedding planners are high-ticket printables - couples pay for done-for-you organization.",
        "price": 8,
        "file": "wedding",
    },
    {
        "name": "Resume + Cover Letter Template Set",
        "category": "Career / template",
        "why": "Resume templates sell steadily - job seekers are an evergreen, motivated audience.",
        "price": 6,
        "file": "resume",
    },
    {
        "name": "Digital Sticker Pack (Planner Decor)",
        "category": "Digital asset",
        "why": "Digital stickers for GoodNotes/Notability are a growing niche with repeat buyers.",
        "price": 3,
        "file": "stickers",
    },
]

# ----------------------------------------------------------------------------
# Product file banks - print-perfect HTML pages (premium, consistent brand)
# ----------------------------------------------------------------------------
def page_shell(title, accent="#F97316", body_html=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 14mm 16mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', -apple-system, 'Segoe UI', Arial, sans-serif; background: #fff; color: #3F3A34; font-size: 11pt; }}
  .head {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid {accent}; padding-bottom: 3mm; margin-bottom: 6mm; }}
  .head .t {{ font-weight: 800; font-size: 16pt; }}
  .head .pn {{ font-size: 9pt; color: #8A8378; }}
  section {{ margin-bottom: 7mm; }}
  h2 {{ font-size: 11pt; letter-spacing: .14em; color: #C2410C; margin-bottom: 3mm; }}
  .line {{ border-bottom: 1px solid #D9D2C4; height: 9mm; }}
  .cols {{ display: flex; gap: 6mm; }}
  .col {{ flex: 1; }}
  .note {{ font-size: 9pt; color: #8A8378; margin-top: 2mm; }}
  .foot {{ margin-top: 8mm; border-top: 1px solid #EBE4D8; padding-top: 3mm; font-size: 8.5pt; color: #8A8378; display: flex; justify-content: space-between; }}
</style>
</head>
<body>
  <div class="head"><div class="t">{title}</div><div class="pn">Nexus Studio · printable</div></div>
{body_html}
  <div class="foot"><span>Nexus Studio · {title}</span><span>print at home · A4</span></div>
</body>
</html>"""

PRODUCT_PAGES = {
    "budget": page_shell("Weekly Budget Tracker", body_html="""
  <div class="note">Three lines. No apps, no debt math, no interest. Predictable beats perfect.</div>
  <section><h2>IN — what arrives this week</h2><div class="line"></div></section>
  <section><h2>OUT — fixed</h2><div class="line"></div><div class="line"></div></section>
  <section><h2>OUT — variable</h2><div class="line"></div><div class="line"></div></section>
  <section><h2>LEFT — the number that matters</h2><div class="line"></div></section>
"""),
    "adhd": page_shell("ADHD Daily Page", body_html="""
  <div class="note">One page a day. Brain dump first, then 3 tasks, then one tiny win. No shame columns.</div>
  <section><h2>BRAIN DUMP (write it ALL down)</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>JUST 3 THINGS</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>ONE TINY WIN</h2><div class="line"></div><div class="note">Small enough that it's basically free.</div></section>
"""),
    "semester": page_shell("Semester Planner", body_html="""
  <div class="note">Term overview: exams, deadlines, and one calm thing per week.</div>
  <section><h2>THIS TERM'S BIG DATES</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>WEEKLY RHYTHM (Mon–Sun, 3 tasks each)</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>THE DEADLINE THAT SCARES YOU</h2><div class="line"></div></section>
"""),
    "meal": page_shell("Weekly Meal Planner", body_html="""
  <div class="note">Plan once, shop once, decide zero times.</div>
  <section><h2>THE 7 MEALS (one line each)</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>GROCERY LIST</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>ONE EASY NIGHT (order / leftover / frozen)</h2><div class="line"></div></section>
"""),
    "habits": page_shell("Habit Tracker", body_html="""
  <div class="note">4 habits max. Tick the day. Streaks, not scores.</div>
  <section><h2>HABITS (rows) × DAYS (columns 1–31)</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>MONTH'S ONE SENTENCE</h2><div class="line"></div></section>
"""),
    "wedding": page_shell("Wedding Planning Checklist", body_html="""
  <div class="note">One page per phase: 6 months out, 3 months out, 1 month out, the week.</div>
  <section><h2>6 MONTHS OUT</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>3 MONTHS OUT</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>1 MONTH OUT</h2><div class="line"></div><div class="line"></div></section>
  <section><h2>THE WEEK</h2><div class="line"></div><div class="line"></div></section>
"""),
    "resume": page_shell("Resume Template — clean layout", body_html="""
  <div class="note">Replace the brackets. One page. Two colors max.</div>
  <section><h2>[YOUR NAME]</h2><div class="line"></div><div class="note">email · phone · city</div></section>
  <section><h2>SUMMARY (2 lines)</h2><div class="line"></div></section>
  <section><h2>EXPERIENCE</h2><div class="line"></div><div class="line"></div></section>
  <section><h2>SKILLS + EDUCATION</h2><div class="line"></div><div class="line"></div></section>
"""),
    "stickers": page_shell("Planner Sticker Sheet — printable", body_html="""
  <div class="note">Cut or use digitally in GoodNotes. Circles, arrows, tabs, checkboxes.</div>
  <div class="cols">
    <div class="col"><div class="line"></div><div class="line"></div><div class="line"></div></div>
    <div class="col"><div class="line"></div><div class="line"></div><div class="line"></div></div>
    <div class="col"><div class="line"></div><div class="line"></div><div class="line"></div></div>
  </div>
"""),
    "wallart": page_shell("Wall Art Quote — 3 designs", body_html="""
  <div class="note">Three prints, one listing. Print at home or any shop.</div>
  <section><h2>QUOTE 1 — "Boring systems survive."</h2><div class="line"></div></section>
  <section><h2>QUOTE 2 — "One page is enough."</h2><div class="line"></div></section>
  <section><h2>QUOTE 3 — "Done for today."</h2><div class="line"></div></section>
"""),
    "canva": page_shell("Social Media Template Kit — layout sheet", body_html="""
  <div class="note">12 layouts: post, story, carousel cover. Brand colors + fonts listed on page 2.</div>
  <section><h2>POST LAYOUTS (1–6)</h2><div class="line"></div><div class="line"></div><div class="line"></div></section>
  <section><h2>STORY LAYOUTS (7–9)</h2><div class="line"></div><div class="line"></div></section>
  <section><h2>CAROUSEL COVERS (10–12)</h2><div class="line"></div><div class="line"></div></section>
"""),
}

LISTING_TEMPLATE = """{title}

WHAT'S INSIDE
• {what1}
• {what2}
• {what3}

WHY IT WORKS
{why}

DETAILS
• Instant digital download - nothing ships
• A4, print at home or any print shop
• Minimal ink-friendly design
• Print as many copies as you need

NOTE: This is a digital download. No physical item will be shipped.
"""


def pick(pool):
    return random.choice(pool)


def clean(text):
    for w in BANNED:
        text = re.sub(r"\b" + re.escape(w) + r"\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", text).strip()


def build_template_product(cfg, seed=None):
    rng = random.Random(seed) if seed is not None else random
    idea = rng.choice(PRODUCT_IDEAS)
    title = f"{idea['name']} | Minimal Printable | A4 Digital Download PDF"
    title = title[:140]
    tags = ["digital download", "printable", "planner", "template", "pdf",
            "minimal", "organizer", "budget", "habits", "a4", "printable planner",
            "instant download", "gift for students"]
    desc = LISTING_TEMPLATE.format(
        title=idea["name"],
        what1=idea.get("what1", "One clean page, ready to print"),
        what2=idea.get("what2", "A4 format, minimal ink-friendly design"),
        what3=idea.get("what3", "Print as many copies as you need"),
        why=idea["why"],
    )
    return {
        "name": idea["name"],
        "category": idea["category"],
        "why": idea["why"],
        "price": idea["price"],
        "title": title,
        "tags": tags,
        "description": desc.strip(),
        "image_brief": f"Flat-lay mockup of the printed page on a cream background, warm orange accent, big readable title '{idea['name']}'.",
        "file_key": idea["file"],
        "mode": "template",
    }


def llm_generate(cfg):
    import requests
    providers = [
        ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
        ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-2.5-flash"),
        ("DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions", "deepseek-v4-flash"),
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ]
    prompt = f"""You are a professional Etsy product strategist and copywriter. Create ONE premium digital product pack for a store selling minimal, calm, productive printables.

TONE RULES: human, professional, warm, specific. NEVER use: {', '.join(BANNED)}. No emoji spam. Short sentences.

Output exactly this format (plain text):

PRODUCT NAME: [one line, sellable]
CATEGORY: [one line]
WHY IT SELLS: [2 sentences, honest demand logic]
LISTING TITLE: [max 140 chars]
13 TAGS: [comma separated, exactly 13]
DESCRIPTION: [premium listing description, 4 short sections: WHAT'S INSIDE / WHY IT WORKS / DETAILS / NOTE - no hype]
PRICE USD: [number between 3 and 9]
IMAGE BRIEF: [one line for the listing mockup]"""

    errors = []
    for env_key, url, model in providers:
        key = os.getenv(env_key)
        if not key:
            continue
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                              json={"model": model, "messages": [
                                  {"role": "system", "content": "You are Nexus. Output only the requested format. Human tone."},
                                  {"role": "user", "content": prompt}], "temperature": 0.8}, timeout=90)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                return parse_product(text), model
            errors.append(f"{env_key}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"{env_key}: {e}")
    return None, " | ".join(errors)


def parse_product(text):
    out = {"name": "", "category": "", "why": "", "title": "", "tags": [],
           "description": "", "price": 5, "image_brief": "", "mode": "llm", "raw": text.strip()}
    keys = {"PRODUCT NAME": "name", "CATEGORY": "category", "WHY IT SELLS": "why",
            "LISTING TITLE": "title", "13 TAGS": "tags", "DESCRIPTION": "description",
            "PRICE USD": "price", "IMAGE BRIEF": "image_brief"}
    cur = None
    buf = []
    for line in text.splitlines():
        upper = line.strip().upper()
        matched = None
        for marker, key in keys.items():
            if upper.startswith(marker):
                matched = key
                break
        if matched:
            if cur:
                val = "\n".join(buf).strip()
                if cur == "tags":
                    out[cur] = [t.strip() for t in val.split(",") if t.strip()][:13]
                elif cur == "price":
                    m = re.search(r"\d+", val)
                    out[cur] = int(m.group()) if m else 5
                else:
                    out[cur] = val
            cur = matched
            buf = []
        elif cur:
            buf.append(line)
    if cur:
        val = "\n".join(buf).strip()
        if cur == "tags":
            out[cur] = [t.strip() for t in val.split(",") if t.strip()][:13]
        elif cur == "price":
            m = re.search(r"\d+", val)
            out[cur] = int(m.group()) if m else 5
        else:
            out[cur] = val
    return out


def render_markdown(product, cfg, date):
    return f"""# Today's Etsy Product Pack · {date}

**Store niche:** minimal, calm, productive printables · **Freebie lead:** The One-Page Weekly Reset

---

## PRODUCT
{product.get('name', '')}

## WHY IT SELLS
{product.get('why', '')}

## LISTING TITLE (140 chars max)
{product.get('title', '')}

## 13 TAGS
{', '.join(product.get('tags', []))}

## DESCRIPTION (premium, no hype)
{product.get('description', '')}

## PRICE
${product.get('price', 5)} USD

## IMAGE BRIEF (for your listing mockup)
{product.get('image_brief', '')}

## PRODUCT FILE
See `product_{date}.html` next to this file - open it, screenshot or print-to-PDF, and use it as the listing's product image and download.

---
**Next step:** create the listing on Etsy/Gumroad using the title, tags and description above.
**Generated by:** Nexus Etsy Engine · mode: {product.get('mode', 'template')}
"""


def email_digest(subject, body):
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if not user or not pw:
        print("[Email] Skipped - GMAIL_USER/GMAIL_APP_PASSWORD not set.")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Nexus Etsy Engine", user))
        msg["To"] = user
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        print(f"[Email] Sent to {user}")
    except Exception as e:
        print(f"[Email] Failed: {e}")


def main():
    FEED.mkdir(exist_ok=True)
    date = datetime.date.today().isoformat()

    product, model = llm_generate({})
    if product is None:
        print(f"[Engine] LLM unavailable ({model}) - using product bank.")
        product = build_template_product({})
    else:
        print(f"[Engine] Generated fresh product via {model}")

    md = render_markdown(product, {}, date)
    (FEED / f"{date}.md").write_text(md, encoding="utf-8")
    (FEED / "latest.md").write_text(md, encoding="utf-8")

    # product file (premium design) + cover image
    fkey = product.get("file_key") or "budget"
    page_fn = PRODUCT_PAGES_V2.get(fkey, PRODUCT_PAGES_V2["budget"])
    page = page_fn()
    (FEED / f"product_{date}.html").write_text(page, encoding="utf-8")
    (FEED / "product_latest.html").write_text(page, encoding="utf-8")
    try:
        render_cover(product.get("name", "Calm Week System"), product.get("why", ""), FEED / "cover_latest.png")
        (FEED / f"cover_{date}.png").write_bytes((FEED / "cover_latest.png").read_bytes())
        print("[Engine] Cover image rendered (cover_latest.png)")
    except Exception as e:
        print(f"[Engine] Cover render skipped: {e}")

    hist_path = FEED / "history.json"
    hist = []
    if hist_path.exists():
        try:
            hist = json.loads(hist_path.read_text(encoding="utf-8"))
        except Exception:
            hist = []
    if date not in hist:
        hist.append(date)
    hist_path.write_text(json.dumps(hist[-90:], indent=2), encoding="utf-8")

    print(f"[Engine] Saved feed-etsy/{date}.md + product_{date}.html")
    email_digest(f"Etsy Product Pack · {date} · listing-ready", md)

    print("\n" + "=" * 60)
    print(md)
    print("=" * 60)


if __name__ == "__main__":
    main()
