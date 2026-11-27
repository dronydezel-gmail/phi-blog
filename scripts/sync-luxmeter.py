#!/usr/bin/env python3
"""Copy the iPhone lux meter pages from the luxmeter project into the blog.

Published as unlisted, self-contained pages (not blog posts):

    /luxmeter/          iPhone lux, blue light and melanopic meter: feasibility notes
    /luxmeter/phase0/   camera test rounds for the first tester (iPhone 17 Pro)
    /luxmeter/16pro/    full camera test for the iPhone 16 Pro tester

To update after editing either page:

    cd /Users/bv/projects/my/phi/web
    python3 scripts/sync-luxmeter.py            # copy + add noindex
    python3 scripts/sync-luxmeter.py --deploy   # same, then git commit + push (Vercel redeploys)
"""
import subprocess
import sys
from pathlib import Path

SRC = Path("/Users/bv/projects/my/luxmeter")
WEB = Path(__file__).resolve().parent.parent
DEST = WEB / "public" / "luxmeter"
PAGES = {
    "luxmeter-exploration.html": "index.html",
    "phase0-instructions.html": "phase0/index.html",
    "phase0-16pro.html": "16pro/index.html",
}
NOINDEX = '<meta name="robots" content="noindex, nofollow">\n'


def main() -> None:
    for src_name, dest_name in PAGES.items():
        html = (SRC / src_name).read_text(encoding="utf-8")
        if 'name="robots"' not in html:
            if "<head>\n" not in html:
                sys.exit(f"{src_name}: no <head> line to insert the noindex tag after")
            html = html.replace("<head>\n", "<head>\n" + NOINDEX, 1)
        dest = DEST / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        print(f"{src_name} -> public/luxmeter/{dest_name} ({len(html):,} bytes)")

    if "--deploy" in sys.argv:
        run = lambda *cmd: subprocess.run(cmd, cwd=WEB, check=True)
        run("git", "add", "public/luxmeter", "scripts/sync-luxmeter.py")
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=WEB).returncode == 0:
            print("No changes to deploy.")
            return
        run("git", "commit", "-m", "Update iPhone lux meter pages")
        run("git", "push")
        print("Pushed; Vercel will redeploy in a minute or two.")


if __name__ == "__main__":
    main()
