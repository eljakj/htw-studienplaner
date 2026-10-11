#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the static page: template + catalog + src/semester.js + src/exchange.js + demo/profile.demo.json -> dist/index.html.

    python build.py                            # the page, every module "planned"
    python build.py --fragment --out out.html  # without the HTML head (e.g. for embedding)

The build is always neutral: there is no option for personal start values. Your own plan lives in
the browser (localStorage) and can be moved with the export/import files. The page does contain the
fictional example of the sandbox (demo/profile.demo.json) as a separate data block.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
import catalog  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "index.tpl.html")
PLACEHOLDER = "__CATALOG__"
SEMESTER_JS = os.path.join(ROOT, "src", "semester.js")
SEMESTER_PLACEHOLDER = "__SEMESTER_JS__"
EXCHANGE_JS = os.path.join(ROOT, "src", "exchange.js")
EXCHANGE_PLACEHOLDER = "__EXCHANGE_JS__"
DEMO_PROFILE = os.path.join(ROOT, "demo", "profile.demo.json")
EXAMPLE_PLACEHOLDER = "__EXAMPLE__"
HEAD = (
    '<!doctype html>\n<html lang="de">\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    "<style>body{margin:0}</style>\n"
)

SCRIPT_RE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)
TYPE_RE = re.compile(r'\btype\s*=\s*"([^"]*)"')


def script_hashes(page):
    """CSP hash sources ('sha256-...') of all executable inline scripts.

    Data blocks like <script type="application/json"> are never executed and need no hash."""
    hashes = []
    for m in SCRIPT_RE.finditer(page):
        t = TYPE_RE.search(m.group("attrs"))
        if t and t.group(1) not in ("text/javascript", "module"):
            continue
        digest = hashlib.sha256(m.group("body").encode("utf-8")).digest()
        hashes.append("'sha256-%s'" % base64.b64encode(digest).decode("ascii"))
    return hashes


def content_security_policy(page):
    """Policy for the page: only the scripts it contains may run, nothing is loaded from outside.

    style-src needs 'unsafe-inline' because the app sets style attributes (cell colors)."""
    return "; ".join([
        "default-src 'none'",
        "script-src " + (" ".join(script_hashes(page)) or "'none'"),
        "style-src 'unsafe-inline'",
        "base-uri 'none'",
        "form-action 'none'",
    ])


def example_json():
    """The fictional example of the sandbox, from demo/profile.demo.json (validated against the catalog)."""
    with open(DEMO_PROFILE, encoding="utf-8") as f:
        return catalog.to_json(catalog.example_state(json.load(f)))


def build(*, fragment=False):
    """Return the page as a string. The result only depends on the inputs (no timestamps)."""
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    for placeholder in (PLACEHOLDER, SEMESTER_PLACEHOLDER, EXCHANGE_PLACEHOLDER, EXAMPLE_PLACEHOLDER):
        if tpl.count(placeholder) != 1:
            raise ValueError("template must contain the placeholder %s exactly once" % placeholder)
    scripts = {}
    for path in (SEMESTER_JS, EXCHANGE_JS):
        with open(path, encoding="utf-8") as f:
            scripts[path] = f.read()
        if "</script" in scripts[path].lower():
            raise ValueError("%s must not contain a closing script tag" % display_path(path))
    page = (tpl.replace(PLACEHOLDER, catalog.to_json(catalog.CATALOG))
               .replace(SEMESTER_PLACEHOLDER, scripts[SEMESTER_JS])
               .replace(EXCHANGE_PLACEHOLDER, scripts[EXCHANGE_JS])
               .replace(EXAMPLE_PLACEHOLDER, example_json()))
    if fragment:
        return page
    csp = '<meta http-equiv="Content-Security-Policy" content="%s">\n' % content_security_policy(page)
    return HEAD + csp + page + "\n</html>\n"


def display_path(path):
    try:
        return os.path.relpath(path)
    except ValueError:  # different drive on Windows
        return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="output file (default: dist/index.html)")
    ap.add_argument("--fragment", action="store_true", help="omit the <!doctype>/<meta> head")
    args = ap.parse_args(argv)

    html = build(fragment=args.fragment)
    out = os.path.abspath(args.out or os.path.join(ROOT, "dist", "index.html"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # newline="\n": same bytes on Windows and Linux
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("built: %s (%d KB)" % (display_path(out), len(html.encode("utf-8")) // 1024))


if __name__ == "__main__":
    main()
