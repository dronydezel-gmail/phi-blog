#!/usr/bin/env python3
"""Copy the Siracusa–Riga road books from the trips folder into the blog.

They're published as unlisted, self-contained pages (not blog posts):

    /roadbook/siracusa-riga/              6-day plan via Bari and Assisi (the one we're driving)
    /roadbook/siracusa-riga/fast.html     4-day fast plan
    /roadbook/siracusa-riga/nonstop.html  non-stop, one driver

To update after editing the road books:

    cd /Users/bv/projects/my/phi/web
    python3 scripts/sync-roadbook.py            # copy + rewrite links
    python3 scripts/sync-roadbook.py --deploy   # same, then git commit + push (Vercel redeploys)
"""
import re
import subprocess
import sys
from pathlib import Path

SRC = Path("/Users/bv/projects/trips/palermo")
WEB = Path(__file__).resolve().parent.parent
DEST = WEB / "public" / "roadbook" / "siracusa-riga"

PAGES = {
    "Siracusa–Riga via Bari and Assisi.html": "index.html",
    "Siracusa–Riga Road Book.html": "fast.html",
    "Siracusa–Riga Non-stop.html": "nonstop.html",
}
# links between the local files -> links between the published pages
LINKS = {
    "Siracusa%E2%80%93Riga%20via%20Bari%20and%20Assisi.html": "./",
    "Siracusa%E2%80%93Riga%20Road%20Book.html": "fast.html",
    "Siracusa%E2%80%93Riga%20Non-stop.html": "nonstop.html",
}
NOINDEX = '<meta name="robots" content="noindex, nofollow">\n'


def convert(html: str) -> str:
    for old, new in LINKS.items():
        html = html.replace(f'href="{old}"', f'href="{new}"')
    # the outbound Riga–Palermo book isn't published: drop its link
    html = re.sub(r'\s*The way down: <a href="Riga%E2%80%93Palermo[^"]*">[^<]*</a>\.', "", html)
    html = re.sub(r'<a href="Riga%E2%80%93Palermo[^"]*">([^<]*)</a>', r"\1", html)
    if 'name="robots"' not in html:
        html = html.replace("<head>\n", "<head>\n" + NOINDEX, 1)
    return html


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for src_name, dest_name in PAGES.items():
        html = convert((SRC / src_name).read_text(encoding="utf-8"))
        leftovers = re.findall(r'href="([^"#:]*\.html)"', html)
        leftovers = [h for h in leftovers if h not in LINKS.values()]
        if leftovers:
            sys.exit(f"{src_name}: unconverted local links {leftovers}")
        (DEST / dest_name).write_text(html, encoding="utf-8")
        print(f"{src_name} -> public/roadbook/siracusa-riga/{dest_name} ({len(html):,} bytes)")

    if "--deploy" in sys.argv:
        run = lambda *cmd: subprocess.run(cmd, cwd=WEB, check=True)
        run("git", "add", "public/roadbook", "scripts/sync-roadbook.py")
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=WEB).returncode == 0:
            print("No changes to deploy.")
            return
        run("git", "commit", "-m", "Update Siracusa–Riga road book")
        run("git", "push")
        print("Pushed; Vercel will redeploy in a minute or two.")


if __name__ == "__main__":
    main()
