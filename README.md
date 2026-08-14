# Flexible $0 Starter Blueprint — Content Studio Kit

A **$0 budget operating system** for growing toward ~$100/month with short-form
content and a small digital product. No bots, no fake views, no stolen clips,
no promises of income. ~90% of the *repeatable* work is systematized here; the
10% that only you can do (record, upload, answer humans) is marked clearly.

> Rule: this is a kit of modules. Swap any module. Don't run four businesses
> until one has a pulse.

## What's in this repo

```
income-blueprint/
├── README.md                  ← you are here (quickstart)
├── blueprint.md               ← the full system (north star, modules, loop)
├── changelog.md               ← open change log: change one line, not the universe
├── scripts/                   ← the 90%: batch generators
│   ├── hooks-20.md            ← 20 first-second hooks
│   ├── scripts-10.md          ← 10 faceless Shorts scripts
│   ├── batch-generator.md     ← how to batch 10 scripts in 60–90 min
│   └── title-formulas.md      ← title + on-screen text formulas
├── pack/                      ← the product (make it $0, sell later)
│   ├── pack-outline.md        ← the $7–9 digital pack, 8–12 items
│   ├── weekly-reset.md        ← the free 1-page weekly reset (lead magnet)
│   └── tracker-pack.md        ← the paid tracker pack outline
├── calendar/
│   └── content-calendar.md    ← 15-post experiment calendar
├── checklists/
│   ├── setup.md               ← 2-hour setup
│   ├── batch-day.md           ← weekly 60–90 min batch
│   ├── posting.md             ← 10–15 min per post
│   └── review.md              ← 15-min weekly keep/kill review
└── studio/index.html          ← Content Studio tool (open in browser)
```

## THE DAILY CONTENT MACHINE (what you actually use)

A scheduled engine generates a **publish-ready post pack every morning** and
delivers it to two places — no repo visits, no decisions:

1. **Dashboard (one link):** https://idkwhattonametsbro.github.io/income-blueprint/dashboard/
   Open it in the morning → copy each section → record → upload. Done.
2. **Gmail (optional, 10-min setup):** enable 2-Step Verification on your
   Google account → create an App Password → add secrets `GMAIL_USER` and
   `GMAIL_APP_PASSWORD` in repo Settings → Secrets → Actions. Every morning
   the full pack arrives in your inbox instead.

The engine runs on GitHub's free servers (daily at ~08:00 Morocco time) using
`.github/workflows/daily_content.yml`. It works with ZERO API keys (built-in
template banks); with a `GROQ_API_KEY` or `GEMINI_API_KEY` secret it generates
fresh content every day with a human, professional tone (no AI-slop wording).

What you get each day: HOOK + SCRIPT (40-55s) + TITLE + CAPTION + HASHTAGS +
PIN COMMENT + THUMBNAIL IDEA, on your niche, gently pointing to your product.

## Quickstart (tonight, ~10 minutes)

0. **The product already exists** — go to `product/`, open the pages, print to
   PDF (30 min), and list them with `listings/etsy-listing.md` (15 min).
   That's your sleep machine.


1. Open `blueprint.md`, fill the **North Star** line.
2. Pick a loadout (or use the default below).
3. Open `studio/index.html` in your browser — set your niche, pull random
   hooks, track your 15-post experiment.
4. On batch day: ask your AI agent for `Batch 10 Shorts scripts, faceless,
   niche: [your line]` — or write from `scripts/scripts-10.md` as templates.

**Default loadout** (change any bullet, the loop stays):

- Niche: calm weekly systems for broke beginners
- Format: faceless Shorts + occasional screen
- Home: YouTube Shorts · Mirror: TikTok
- Product: free 1-page weekly reset → later a small tracker pack
- Cadence: 4–5 posts/week, batch on one day
- Review: every 15 posts

## The 90 / 10 split

**90% (systematized here — generate anytime):** hooks, scripts, on-screen text,
thumbnail/title formulas, product outline, posting checklist, content calendar.

**10% (only you, non-negotiable):** record or approve voice, export from a free
editor, create the account, tap upload, answer humans.

> There is no honest 24/7 bot that uploads, grows, and cashes out on $0. The
> system makes thinking and drafting almost free, so your hour is only
> record + post.

## Money sequence (honest)

| Stage | What winning looks like | Money? |
|---|---|---|
| 0–15 posts | you finished a loop | no |
| small audience / one save-worthy video | people ask for the file | free download |
| repeat asks | pack v1, $7–9 | first $ |
| a few sales or affiliates | nicer pack + 1 longer video | toward $100/mo |
| real channel | more products or freelance from DMs | growth |

## What this repo is NOT

- Not a promise of income (nobody honest can guarantee that)
- Not a bot farm, engagement pods, or stolen content
- Not interest, gambling, adult, or scam-adjacent anything
- **Not a place for secrets** — never commit tokens, passwords, or API keys.
  The `studio` tool runs fully in your browser; nothing is uploaded anywhere.

## Change log rule

When you change your mind, edit one line in `changelog.md` — niche, format,
platform, product. The loop survives. Regenerate scripts against the new line.
