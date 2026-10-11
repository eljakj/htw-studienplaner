"""Fixtures for the browser tests.

pytest-playwright provides `playwright`, `browser`, `context` and `page`.
This file adds:

* `base_url`   - builds the page once and serves it on a free local port
                 (or takes E2E_BASE_URL, e.g. a running Docker container),
* `app`        - a fresh page with the app open; the test fails on JavaScript
                 errors and on any request that leaves the local server.

Every test gets its own browser context, so localStorage is never shared.
"""
import functools
import http.server
import os
import threading

import pytest

import build


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # keep the test output clean
        pass


@pytest.fixture(scope="session")
def site_dir(tmp_path_factory):
    """Directory with the freshly built, neutral dist/index.html."""
    directory = tmp_path_factory.mktemp("site")
    build.main(["--out", str(directory / "index.html")])
    return directory


@pytest.fixture(scope="session")
def base_url(site_dir):
    """Serve `site_dir` on 127.0.0.1 with a free port (overrides the plugin's base_url).

    With E2E_BASE_URL set (for example to a running Docker container) that address is used instead."""
    external = os.environ.get("E2E_BASE_URL")
    if external:
        yield external.rstrip("/")
        return
    handler = functools.partial(_QuietHandler, directory=str(site_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1300, "height": 900},
        "locale": "de-DE",
    }


def watch(page, base_url):
    """Record JavaScript errors and requests to other hosts on `page`."""
    problems = {"errors": [], "external": []}
    page.on("pageerror", lambda e: problems["errors"].append(str(e)))

    def on_console(message):
        # a missing favicon is not an app error
        if message.type == "error" and not message.location.get("url", "").endswith("/favicon.ico"):
            problems["errors"].append(message.text)

    page.on("console", on_console)

    def on_request(request):
        if not request.url.startswith((base_url, "data:", "blob:", "about:")):
            problems["external"].append(request.url)

    page.on("request", on_request)
    return problems


@pytest.fixture
def app(page, base_url):
    """The app, opened and watched. Fails the test on JS errors or external requests."""
    problems = watch(page, base_url)
    page.goto(base_url + "/")
    yield page
    assert problems["external"] == [], "requests to other hosts"
    assert problems["errors"] == [], "JavaScript errors"
