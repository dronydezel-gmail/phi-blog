#!/usr/bin/env python3
"""Copy the iPhone lux meter write-up from the luxmeter project into the blog.

Published as an unlisted, self-contained page (not a blog post):

    /luxmeter/    iPhone lux, blue light and melanopic meter: feasibility notes

To update after editing the write-up:

    cd /Users/bv/projects/my/phi/web
    python3 scripts/sync-luxmeter.py            # copy + add noindex
    python3 scripts/sync-luxmeter.py --deploy   # same, then git commit + push (Vercel redeploys)
"""
import subprocess
import sys
from pathlib import Path

SRC = Path("/Users/bv/projects/my/luxmeter/luxmeter-exploration.html")
WEB = Path(__file__).resolve().parent.parent
DEST = WEB / "public" / "luxmeter" / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow">\n'


def main() -> None:
    html = SRC.read_text(encoding="utf-8")
    if 'name="robots"' not in html:
        if "<head>\n" not in html:
            sys.exit("no <head> line to insert the noindex tag after")
        html = html.replace("<head>\n", "<head>\n" + NOINDEX, 1)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(html, encoding="utf-8")
    print(f"{SRC.name} -> public/luxmeter/index.html ({len(html):,} bytes)")

    if "--deploy" in sys.argv:
        run = lambda *cmd: subprocess.run(cmd, cwd=WEB, check=True)
        run("git", "add", "public/luxmeter", "scripts/sync-luxmeter.py")
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=WEB).returncode == 0:
            print("No changes to deploy.")
            return
        run("git", "commit", "-m", "Update iPhone lux meter notes")
        run("git", "push")
        print("Pushed; Vercel will redeploy in a minute or two.")


if __name__ == "__main__":
    main()
