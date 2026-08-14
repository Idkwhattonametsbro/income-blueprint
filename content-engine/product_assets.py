#!/usr/bin/env python3
"""
Premium product page + cover-image library for the Etsy engine.
Real design: serif headings, cards, real grids, brand marks.
Cover mockups rendered to PNG with cairosvg (no browser needed).
"""
import re
from pathlib import Path

ACCENT = "#F97316"
ACCENT_D = "#C2410C"
INK = "#2F2A26"
MUT = "#8A8378"
LINE = "#E8E1D6"
CREAM = "#FAF9F6"


def shell(title, body, serif=True, landscape=False):
    fam = "'Georgia', 'Times New Roman', serif" if serif else "'Inter', Arial, sans-serif"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{title}</title>
<style>
  @page {{ size: {'A4 landscape' if landscape else 'A4'}; margin: 12mm 14mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', Arial, sans-serif; background: #fff; color: {INK}; }}
  .brand {{ display: flex; align-items: center; gap: 10px; border-bottom: 3px solid {ACCENT}; padding-bottom: 10px; margin-bottom: 18px; }}
  .brand .mark {{ width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg,#FB923C,#EA580C); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:15px; }}
  .brand .nm {{ font-family: {fam}; font-weight: 700; font-size: 17pt; letter-spacing: .02em; }}
  .brand .pg {{ margin-left: auto; font-size: 9pt; color: {MUT}; }}
  .tagline {{ font-size: 9.5pt; color: {MUT}; margin: -10px 0 16px; }}
  .card {{ background: {CREAM}; border: 1px solid {LINE}; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; }}
  .card h2 {{ font-family: {fam}; font-size: 13pt; color: {ACCENT_D}; margin-bottom: 10px; display: flex; align-items: center; gap: 9px; }}
  .card h2 .n {{ width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg,#FB923C,#EA580C); color:#fff; font-family: Inter; font-size: 10.5pt; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
  .line {{ border-bottom: 1.5px solid {LINE}; height: 34px; }}
  .note {{ font-size: 8.5pt; color: {MUT}; margin-top: 4px; }}
  .foot {{ margin-top: 14px; border-top: 1px solid {LINE}; padding-top: 8px; font-size: 8pt; color: {MUT}; display: flex; justify-content: space-between; }}
  .chk {{ display: inline-block; width: 14px; height: 14px; border: 2px solid {ACCENT}; border-radius: 4px; margin-right: 8px; vertical-align: -2px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td, th {{ border: 1px solid {LINE}; }}
</style></head>
<body>
  <div class="brand"><div class="mark">N</div><div class="nm">{title}</div><div class="pg">Calm Week System · printable</div></div>
  {body}
  <div class="foot"><span>Calm Week System · {title}</span><span>print at home · A4 · instant download</span></div>
</body></html>"""


def weekly_reset():
    return shell("The Weekly Reset", """
  <div class="tagline">15 minutes, every Sunday night. Monday becomes a start, not a surprise.</div>
  <div class="card"><h2><span class="n">1</span>Brain dump</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="note">Write everything floating in your head. This page can hold it.</div></div>
  <div class="card"><h2><span class="n">2</span>The 3 — circle what matters</h2><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span>The anchor — one meal, one walk, one early night</h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">4</span>Money + meals, one line each</h2><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">5</span>The fun thing — calendar first, not last</h2><div class="line"></div></div>
""")


def budget_tracker():
    return shell("Weekly Budget Tracker", """
  <div class="tagline">Three lines. No apps, no debt math, no interest. Predictable beats perfect.</div>
  <div class="card"><h2><span class="n">1</span>In — what arrives this week</h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">2</span>Out — fixed costs</h2><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span>Out — variable</h2><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">4</span>Left — the number that matters</h2><div class="line"></div>
    <div style="display:flex;gap:10px;margin-top:12px">
      <div style="flex:1;text-align:center;border:2px solid #F97316;border-radius:12px;padding:10px"><div style="font-size:8pt;color:#8A8378">IN</div><div style="font-size:15pt;font-weight:800">_____</div></div>
      <div style="flex:1;text-align:center;border:2px solid #F97316;border-radius:12px;padding:10px"><div style="font-size:8pt;color:#8A8378">OUT</div><div style="font-size:15pt;font-weight:800">_____</div></div>
      <div style="flex:1;text-align:center;border:2px solid #F97316;border-radius:12px;padding:10px;background:#FFF7ED"><div style="font-size:8pt;color:#C2410C">LEFT</div><div style="font-size:15pt;font-weight:800">_____</div></div>
    </div>
  </div>
""")


def habit_tracker():
    cells = "".join(f'<td style="height:22px;text-align:center;font-size:8pt;color:#C9BFAE">{d}</td>' for d in range(1, 29))
    rows = ""
    for w in range(4):
        rows += f"<tr>{cells[w*7:(w+1)*7]}</tr>"
    return shell("Habit Tracker", f"""
  <div class="tagline">4 habits max. Tick the day. Streaks, not scores.</div>
  <div class="card"><h2><span class="n">1</span></h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">2</span></h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span></h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">4</span></h2><div class="line"></div></div>
  <div class="card"><h2><span class="n">5</span>28-day grid</h2>
    <table>{rows}</table>
  </div>
""", landscape=False)


def deadline():
    return shell("Deadline Countdown", """
  <div class="tagline">The deadline that scares you — put it here, shrink it into steps.</div>
  <div class="card"><h2><span class="n">1</span>Deadline</h2><div style="font-size:22pt;font-weight:800;color:#F97316;margin-bottom:6px">DAYS LEFT: ______</div><div class="line"></div><div class="note">Date · what it is</div></div>
  <div class="card"><h2><span class="n">2</span>Three steps to get there</h2><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span>Second deadline</h2><div style="font-size:22pt;font-weight:800;color:#F97316;margin-bottom:6px">DAYS LEFT: ______</div><div class="line"></div></div>
""")


def meal_planner():
    return shell("Weekly Meal Planner", """
  <div class="tagline">Plan once, shop once, decide zero times.</div>
  <div class="card"><h2><span class="n">1</span>The 7 meals</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">2</span>Grocery list</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span>One easy night</h2><div class="line"></div><div class="note">leftovers / frozen / order — decide once, guilt-free</div></div>
""")


def shutdown():
    return shell("The Shutdown Ritual", """
  <div class="tagline">Ten minutes. Every night. Print this, stick it by your bed.</div>
  <div class="card"><h2><span class="n">1</span>Write tomorrow's 3</h2><div class="note">your brain can stop holding them</div></div>
  <div class="card"><h2><span class="n">2</span>Close every tab</h2><div class="note">phone and brain</div></div>
  <div class="card"><h2><span class="n">3</span>Phone across the room</h2><div class="note">you'll thank me at 2AM</div></div>
  <div class="card"><h2><span class="n">4</span>"Done for today"</h2><div class="note">say it out loud — the door closes</div></div>
""", landscape=True)


def daily_135():
    return shell("Daily 1-3-5 Sheet", """
  <div class="tagline">One big thing, three medium, five small. Finish the 1 and the 3 and the day is a win.</div>
  <div class="card"><h2><span class="n">1</span>One big thing</h2><div class="line" style="height:40px"></div></div>
  <div class="card"><h2><span class="n">3</span>Three medium</h2><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">5</span>Five small</h2><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">6</span>Wins today</h2><div class="line"></div><div class="note">Your list is a menu, not a promise.</div></div>
""")


def monthly_overview():
    return shell("Monthly Overview", """
  <div class="tagline">One word per day. The task that mattered. Guilt doesn't live here.</div>
  <div class="card"><h2><span class="n">1</span>The month at a glance</h2>
    <table style="width:100%">
      <tr><td style="height:18px;font-size:9pt;color:#C9BFAE;text-align:center">1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr>
      <tr><td style="height:18px;font-size:9pt;color:#C9BFAE;text-align:center">8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td></tr>
      <tr><td style="height:18px;font-size:9pt;color:#C9BFAE;text-align:center">15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td></tr>
      <tr><td style="height:18px;font-size:9pt;color:#C9BFAE;text-align:center">22</td><td>23</td><td>24</td><td>25</td><td>26</td><td>27</td><td>28</td></tr>
      <tr><td style="height:18px;font-size:9pt;color:#C9BFAE;text-align:center">29</td><td>30</td><td>31</td><td></td><td></td><td></td><td></td></tr>
    </table>
  </div>
  <div class="card"><h2><span class="n">2</span>This month's 3</h2><div class="line"></div><div class="line"></div><div class="line"></div></div>
  <div class="card"><h2><span class="n">3</span>The one word for this month</h2><div class="line" style="height:22px"></div></div>
""", landscape=True)


def challenge_30():
    return shell("30-Day Calm Challenge", """
  <div class="tagline">One tiny action a day. Miss a day? Miss one - not two.</div>
  <table style="width:100%">
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">1</b><br>write tomorrow's 3</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">2</b><br>phone away</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">3</b><br>brain dump</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">4</b><br>one walk</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">5</b><br>close tabs</td></tr>
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">6</b><br>early night</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">7</b><br>reset</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">8</b><br>fun thing</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">9</b><br>3 meals</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">10</b><br>gratitude</td></tr>
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">11</b><br>no phone 1h</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">12</b><br>money map</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">13</b><br>declutter</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">14</b><br>review</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">15</b><br>ritual</td></tr>
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">16</b><br>simple meal</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">17</b><br>1-3-5 day</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">18</b><br>boring hour</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">19</b><br>reply fully</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">20</b><br>clothes out</td></tr>
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">21</b><br>reset again</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">22</b><br>later list</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">23</b><br>water</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">24</b><br>money move</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">25</b><br>no compare</td></tr>
    <tr><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">26</b><br>one line</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">27</b><br>fun ahead</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">28</b><br>streak check</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">29</b><br>help someone</td><td style="height:20px;font-size:9pt;color:#C9BFAE;text-align:center"><b style="color:#EA580C">30</b><br>reset + celebrate</td></tr>
  </table>
  <div class="card" style="margin-top:8px"><h2>What changed?</h2><div class="line"></div></div>
""", landscape=True)


PRODUCT_PAGES_V2 = {
    "budget": budget_tracker,
    "adhd": weekly_reset,
    "semester": deadline,
    "meal": meal_planner,
    "habits": habit_tracker,
    "wedding": deadline,
    "resume": weekly_reset,
    "stickers": habit_tracker,
    "wallart": shutdown,
    "canva": weekly_reset,
    "daily": daily_135,
    "monthly": monthly_overview,
    "challenge": challenge_30,
}


def cover_svg(name: str, blurb: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2000" viewBox="0 0 1600 2000">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#FDF6EE"/><stop offset="1" stop-color="#F5E3D0"/>
    </linearGradient>
    <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="24" stdDeviation="26" flood-color="#000" flood-opacity="0.16"/>
    </filter>
  </defs>
  <rect width="1600" height="2000" fill="url(#bg)"/>
  <circle cx="1400" cy="260" r="240" fill="#FDBA74" opacity="0.35"/>
  <circle cx="180" cy="1720" r="300" fill="#F97316" opacity="0.10"/>
  <circle cx="1420" cy="1760" r="120" fill="#FED7AA" opacity="0.5"/>
  <!-- page -->
  <g filter="url(#sh)">
    <rect x="420" y="330" width="760" height="1060" rx="28" fill="#FFFFFF"/>
    <rect x="420" y="330" width="760" height="150" rx="28" fill="#F97316"/>
    <rect x="420" y="452" width="760" height="28" fill="#F97316"/>
    <text x="520" y="428" font-family="Georgia, serif" font-size="64" font-weight="bold" fill="#FFFFFF">{name[:26]}</text>
    <rect x="520" y="560" width="560" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="600" width="480" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="640" width="520" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="700" width="560" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="740" width="440" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="800" width="560" height="14" rx="7" fill="#E8E1D6"/>
    <rect x="520" y="840" width="500" height="14" rx="7" fill="#E8E1D6"/>
    <circle cx="800" cy="1000" r="46" fill="#FFF7ED" stroke="#F97316" stroke-width="8"/>
    <path d="M780 1000 l16 16 l30 -30" stroke="#F97316" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="800" y="1130" font-family="Inter, Arial" font-size="34" fill="#8A8378" text-anchor="middle">printable · A4 · instant download</text>
  </g>
  <text x="800" y="1560" font-family="Inter, Arial" font-size="44" font-weight="800" fill="#2F2A26" text-anchor="middle">CALM WEEK SYSTEM</text>
  <text x="800" y="1620" font-family="Inter, Arial" font-size="28" fill="#8A8378" text-anchor="middle">{blurb[:70]}</text>
</svg>"""


def render_cover(name: str, blurb: str, out_png: Path):
    import cairosvg
    svg = cover_svg(name, blurb)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out_png),
                     output_width=1600, output_height=2000)
