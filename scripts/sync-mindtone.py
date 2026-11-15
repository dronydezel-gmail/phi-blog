#!/usr/bin/env python3
"""Build the meditation tone-metronome app research report into the blog.

Published as an unlisted, self-contained page (not a blog post):

    /mindtone/    iOS meditation tone-metronome app idea: research report

The report is markdown in the mindtone project. This script converts it with
pandoc (brew install pandoc) and wraps it in the page template below.

To update after editing the report:

    cd /Users/bv/projects/my/phi/web
    python3 scripts/sync-mindtone.py            # rebuild public/mindtone/index.html
    python3 scripts/sync-mindtone.py --deploy   # same, then git commit + push (Vercel redeploys)
"""
import html
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/Users/bv/projects/my/mindtone/reports/Meditation tone metronome iOS app.md")
WEB = Path(__file__).resolve().parent.parent
DEST = WEB / "public" / "mindtone" / "index.html"

DATE = "15 November 2026"
KICKER = "App idea · research report"
DEK = (
    "Research into an idea for an iOS meditation app: a four-layer tone metronome "
    "with pink noise, nature soundscapes and binaural beats."
)
BRIEF = (
    "An iOS tone and metronome app for meditation. It plays up to four concurrent "
    "rhythms, each with its own tone, interval and volume, at intervals from 0.01 "
    "seconds to 20 minutes. The tones are gongs, bells and chimes; the backgrounds "
    "are pink noise, rain, wind in trees and alpine streams. Pink noise matters "
    "most, on the belief that it reduces tinnitus. Binaural beats in the alpha "
    "(8–12 Hz) and theta (4–8 Hz) ranges are a wished-for extra, on the belief "
    "that they reduce stress and improve sleep. Working name: Mindtone."
)
FOOTER = (
    "Research notes compiled with Claude, an AI research assistant, on " + DATE + ". "
    "Sources are linked inline. This is not medical, legal or regulatory advice: "
    "the regulatory readings and draft wording have not been reviewed by a "
    "professional, no competitor app was tested hands-on, and some findings rest "
    "on abstracts or press coverage rather than full papers."
)

# The interval-scale figure goes after the paragraph that ends with this text.
FIGURE_ANCHOR = "long-decay meditation tones</strong>.</p>"
SCALE_MIN, SCALE_MAX = 0.01, 1800.0  # seconds, log axis
SCALE_ROWS = [
    ("Musicians’ metronomes", "0.07 s to 60 s", 0.07, 60.0, ""),
    ("Meditation timers", "1 s to 30 min", 1.0, 1800.0, ""),
    ("The planned app", "0.01 s to 20 min", 0.01, 1200.0, " app"),
]
SCALE_TICKS = [(0.01, "0.01 s"), (0.1, "0.1 s"), (1, "1 s"), (10, "10 s"), (60, "1 min"), (1800, "30 min")]
TONE_BOUNDARY = 0.04  # about 25 strikes a second: faster is heard as a tone
BREATH_PACE = 11.0  # seconds per slow breath

LINK = r'<a href="[^"]+">(?:(?!</a>).)*</a>'


def pandoc(markdown: str) -> str:
    exe = shutil.which("pandoc")
    if not exe:
        sys.exit("pandoc not found (brew install pandoc)")
    done = subprocess.run(
        [exe, "--from=gfm+smart", "--to=html5", "--wrap=none"],
        input=markdown, capture_output=True, text=True, check=True,
    )
    return done.stdout


def plain(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def pos(seconds: float) -> float:
    """Position on the log axis, as a percentage of its width."""
    span = math.log10(SCALE_MAX) - math.log10(SCALE_MIN)
    return 100 * (math.log10(seconds) - math.log10(SCALE_MIN)) / span


def scale_figure() -> str:
    tone = pos(TONE_BOUNDARY)
    rows = []
    for name, span, lo, hi, cls in SCALE_ROWS:
        marks = f'<i class="bar" style="left:{pos(lo):.2f}%;width:{pos(hi) - pos(lo):.2f}%"></i>'
        marks += f'<i class="tone" style="width:{tone:.2f}%"></i>'
        if cls:
            marks += f'<i class="dot" style="left:{pos(BREATH_PACE):.2f}%"></i>'
        rows.append(
            f'<div class="scale-row{cls}">'
            f'<div class="scale-name"><span>{name}</span><span>{span}</span></div>'
            f'<div class="scale-track">{marks}</div></div>'
        )
    ticks = "".join(f'<span style="left:{pos(t):.2f}%">{label}</span>' for t, label in SCALE_TICKS)
    summary = (
        "Chart of the interval between strikes on a logarithmic scale from 0.01 seconds to 30 minutes. "
        "Musicians’ metronomes cover 0.07 seconds to 60 seconds, meditation timers cover 1 second to "
        "30 minutes, and the planned app covers 0.01 seconds to 20 minutes."
    )
    return (
        '<div class="figure">\n'
        '<p class="label">Interval between strikes: what existing apps cover</p>\n'
        f'<div class="scale" role="img" aria-label="{summary}">\n'
        + "\n".join(rows)
        + f'\n<div class="scale-axis">{ticks}</div>\n</div>\n'
        '<p class="caption">Logarithmic scale; ranges are the widest documented in App Store listings. '
        "In the hatched zone, faster than about 20 to 30 strikes a second, the ear hears a tone and "
        "not a rhythm. The dot marks about 11 seconds, the pace of slow breathing.</p>\n"
        "</div>"
    )


def build() -> str:
    page = pandoc(SRC.read_text(encoding="utf-8"))
    head = re.match(r"\s*<h1[^>]*>(.*?)</h1>\s*(.*?)(?=<h2)", page, re.S)
    if not head:
        sys.exit("expected an <h1>, a lead and at least one <h2> in the report")
    title, lead, body = head.group(1), head.group(2).strip(), page[head.end():]

    # Tables: drop pandoc's fixed column widths, make them scrollable, widen the big ones.
    body = re.sub(r"<colgroup>.*?</colgroup>\s*", "", body, flags=re.S)

    def wrap_table(match: re.Match) -> str:
        cols = len(re.findall(r"<th[ >]", match.group(0).split("</thead>")[0]))
        size = " xwide" if cols >= 6 else " wide" if cols >= 4 else ""
        return f'<div class="table-wrap{size}">\n{match.group(0)}\n</div>'

    body = re.sub(r"<table.*?</table>", wrap_table, body, flags=re.S)

    # Section numbers and the contents list.
    sections = []

    def number(match: re.Match) -> str:
        ident, inner = match.group(1), match.group(2)
        closing = plain(inner).strip().lower() == "conclusion"
        num = "—" if closing else f"{sum(1 for s in sections if s[0] != '—') + 1:02d}"
        sections.append((num, ident, inner))
        return f'<h2 id="{ident}"><span class="num">{num}</span>{inner}</h2>'

    body = re.sub(r'<h2 id="([^"]+)">(.*?)</h2>', number, body, flags=re.S)
    toc = "\n".join(
        f'<li><a href="#{ident}"><span class="num">{num}</span><span>{inner}</span></a></li>'
        for num, ident, inner in sections
    )

    # Parenthetical source links read as quieter citations.
    body = re.sub(rf"\(({LINK}(?:; {LINK})*)\)", r'<span class="cite">(\1)</span>', body)

    if FIGURE_ANCHOR in body:
        body = body.replace(FIGURE_ANCHOR, FIGURE_ANCHOR + "\n" + scale_figure(), 1)
    else:
        print("warning: figure anchor not found; interval-scale figure left out")

    words = len(plain(lead + body).split())
    minutes = max(5, round(words / 230 / 5) * 5)
    sources = len(set(re.findall(r'<a href="(https?://[^"]+)"', body)))
    meta = f"{DATE} · about {minutes} minutes to read · {sources} sources linked inline"

    fields = {
        "TITLE": title,
        "TITLE_ATTR": html.escape(plain(title).strip(), quote=True),
        "DEK": html.escape(DEK),
        "DEK_ATTR": html.escape(DEK, quote=True),
        "KICKER": html.escape(KICKER),
        "META": html.escape(meta),
        "BRIEF": html.escape(BRIEF),
        "LEAD": lead,
        "TOC": toc,
        "BODY": body.strip(),
        "FOOTER": html.escape(FOOTER),
    }
    out = TEMPLATE
    for key, value in fields.items():
        out = out.replace("%%" + key + "%%", value)
    return out


def main() -> None:
    page = build()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(page, encoding="utf-8")
    print(f"{SRC.name} -> public/mindtone/index.html ({len(page):,} bytes)")

    if "--deploy" in sys.argv:
        run = lambda *cmd: subprocess.run(cmd, cwd=WEB, check=True)
        run("git", "add", "public/mindtone", "scripts/sync-mindtone.py")
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=WEB).returncode == 0:
            print("No changes to deploy.")
            return
        run("git", "commit", "-m", "Update meditation tone metronome app research")
        run("git", "push")
        print("Pushed; Vercel will redeploy in a minute or two.")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta name="robots" content="noindex, nofollow">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE_ATTR%% · meditation app research</title>
<meta name="description" content="%%DEK_ATTR%%">
<meta property="og:type" content="article">
<meta property="og:title" content="%%TITLE_ATTR%%">
<meta property="og:description" content="%%DEK_ATTR%%">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
  :root {
    --bg: #fbfaf7;
    --surface: #ffffff;
    --surface-2: #f3f1ec;
    --text: #1d1c1a;
    --muted: #64615b;
    --border: #e3dfd6;
    --accent: #0e7c86;
    --accent-soft: #e2f2f3;
    --code-bg: #f3f1ec;
    --bar: #b7b2a7;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #141414;
      --surface: #1c1c1b;
      --surface-2: #242423;
      --text: #ecebe8;
      --muted: #a29f98;
      --border: #34332f;
      --accent: #4cc3cd;
      --accent-soft: #12302f;
      --code-bg: #242423;
      --bar: #66625a;
    }
  }

  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  @media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font: 17px/1.65 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  main { max-width: 760px; margin: 0 auto; padding: 48px 16px 72px; }

  .label {
    font-size: 12px; line-height: 1.4; letter-spacing: .08em; text-transform: uppercase;
    font-weight: 700; color: var(--muted); margin: 0 0 6px;
  }
  header .kicker {
    font-size: 13px; letter-spacing: .08em; text-transform: uppercase;
    color: var(--accent); font-weight: 600; margin: 0 0 8px;
  }
  h1 { font-size: clamp(30px, 6.5vw, 44px); line-height: 1.12; margin: 0 0 14px; letter-spacing: -.02em; text-wrap: balance; }
  header .dek { font-size: clamp(18px, 2.6vw, 21px); line-height: 1.45; color: var(--muted); margin: 0 0 14px; text-wrap: pretty; }
  header .meta { color: var(--muted); font-size: 14px; margin: 0; }

  .brief {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 20px; margin: 28px 0 0; font-size: 15.5px; line-height: 1.6;
  }
  .summary {
    background: var(--accent-soft); border-left: 4px solid var(--accent);
    border-radius: 10px; padding: 18px 20px; margin: 16px 0 0;
  }
  .summary .label { color: var(--accent); }
  .brief p:last-child, .summary p:last-child { margin-bottom: 0; }

  .toc { margin: 36px 0 0; }
  .toc ol { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--border); }
  .toc li { margin: 0; border-bottom: 1px solid var(--border); }
  .toc a { display: flex; align-items: baseline; gap: 12px; padding: 9px 2px; color: var(--text); text-decoration: none; line-height: 1.4; }
  .toc a:hover { color: var(--accent); }
  .toc .num { color: var(--accent); font-variant-numeric: tabular-nums; font-size: 13px; font-weight: 700; flex: none; min-width: 22px; }

  h2 {
    font-size: clamp(22px, 4vw, 26px); line-height: 1.25; margin: 56px 0 16px; letter-spacing: -.015em;
    display: flex; align-items: baseline; gap: 12px; text-wrap: balance; scroll-margin-top: 16px;
  }
  h2 .num { color: var(--accent); font-variant-numeric: tabular-nums; font-size: 15px; font-weight: 700; flex: none; }
  h3 { font-size: 19px; line-height: 1.3; margin: 34px 0 10px; text-wrap: balance; }
  p { margin: 0 0 16px; }
  a { color: var(--accent); text-underline-offset: 2px; }
  strong { font-weight: 650; }
  code {
    font: 0.86em/1.4 ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    background: var(--code-bg); padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere;
  }
  .cite { font-size: .86em; color: var(--muted); }
  .cite a { color: inherit; text-decoration-color: var(--bar); }
  .cite a:hover { color: var(--accent); text-decoration-color: currentColor; }

  .table-wrap {
    overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 4px 0 20px;
    border: 1px solid var(--border); border-radius: 10px; background: var(--surface);
  }
  table { width: 100%; min-width: 540px; border-collapse: collapse; font-size: 14.5px; line-height: 1.5; }
  .wide table { min-width: 720px; }
  .xwide table { min-width: 1000px; }
  th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: var(--surface-2); font-weight: 600; font-size: 13px; letter-spacing: .02em; color: var(--muted); }
  td:first-child { font-weight: 600; }
  tbody tr:last-child td { border-bottom: 0; }
  @media (min-width: 1180px) {
    .table-wrap.wide { width: 960px; margin-left: calc((100% - 960px) / 2); }
    .table-wrap.xwide { width: 1120px; margin-left: calc((100% - 1120px) / 2); }
  }

  .figure { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 18px 18px 14px; margin: 8px 0 20px; }
  .figure .label { margin-bottom: 14px; }
  .scale-row { margin: 0 0 14px; }
  .scale-name { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 13.5px; line-height: 1.4; margin: 0 0 5px; }
  .scale-name span:last-child { color: var(--muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .scale-row.app .scale-name span:first-child { font-weight: 650; }
  .scale-track { position: relative; height: 14px; border-radius: 4px; background: var(--surface-2); overflow: hidden; }
  .scale-track i { position: absolute; top: 0; bottom: 0; }
  .scale-track .bar { border-radius: 4px; background: var(--bar); }
  .scale-row.app .bar { background: var(--accent); }
  .scale-track .tone {
    left: 0; border-right: 1.5px dashed var(--muted);
    background: repeating-linear-gradient(-45deg, transparent 0 3px, var(--surface) 3px 5px);
  }
  .scale-track .dot {
    top: 50%; bottom: auto; width: 8px; height: 8px; margin: -4px 0 0 -4px;
    border-radius: 50%; background: var(--surface);
  }
  .scale-axis { position: relative; height: 22px; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
  .scale-axis span { position: absolute; top: 2px; transform: translateX(-50%); white-space: nowrap; }
  .scale-axis span:first-child { transform: none; }
  .scale-axis span:last-child { transform: translateX(-100%); }
  .caption { font-size: 13.5px; line-height: 1.5; color: var(--muted); margin: 8px 0 0; }

  footer { margin-top: 56px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; line-height: 1.55; }
</style>
</head>
<body>
<main>

<header>
  <p class="kicker">%%KICKER%%</p>
  <h1>%%TITLE%%</h1>
  <p class="dek">%%DEK%%</p>
  <p class="meta">%%META%%</p>
</header>

<div class="brief">
  <p class="label">The brief</p>
  <p>%%BRIEF%%</p>
</div>

<div class="summary">
  <p class="label">Verdict</p>
  %%LEAD%%
</div>

<nav class="toc" aria-label="Contents">
  <p class="label">Contents</p>
  <ol>
%%TOC%%
  </ol>
</nav>

%%BODY%%

<footer>%%FOOTER%%</footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
