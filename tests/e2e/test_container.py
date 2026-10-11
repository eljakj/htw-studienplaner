"""Checks for the nginx container (headers, health endpoint, caching).

They only run against a real server: start the container and set E2E_BASE_URL,
for example  E2E_BASE_URL=http://127.0.0.1:8080 python -m pytest tests/e2e
"""
import os
import re

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("E2E_BASE_URL"), reason="needs a running server: set E2E_BASE_URL"
)


def get(page, base_url, path, **headers):
    return page.request.get(base_url + path, headers=headers)


def test_health_endpoint(page, base_url):
    response = get(page, base_url, "/healthz")
    assert response.status == 200
    assert response.text().strip() == "ok"


def test_security_headers(page, base_url):
    headers = get(page, base_url, "/").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "camera=()" in headers["permissions-policy"]


def test_page_is_revalidated_and_sets_no_cookie(page, base_url):
    headers = get(page, base_url, "/").headers
    assert "no-cache" in headers["cache-control"]
    assert "set-cookie" not in headers


def test_server_header_hides_the_version(page, base_url):
    assert not re.search(r"\d", get(page, base_url, "/").headers.get("server", ""))


def test_page_is_compressed(page, base_url):
    headers = get(page, base_url, "/", **{"Accept-Encoding": "gzip"}).headers
    assert headers.get("content-encoding") == "gzip"


def test_unknown_path_is_404(page, base_url):
    assert get(page, base_url, "/nothing-here").status == 404
