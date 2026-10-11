"""Tests for build.py."""
import base64
import hashlib
import json
import re
from pathlib import Path

import pytest

import build
import catalog

# XML namespace URIs are identifiers, not requests.
ALLOWED_URLS = {"http://www.w3.org/2000/svg"}


def embedded_catalog(page):
    m = re.search(r'<script type="application/json" id="catalog">(.*?)</script>', page, re.S)
    assert m, "catalog script tag not found"
    return json.loads(m.group(1))


def embedded_block(page, block_id):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % block_id, page, re.S)
    assert m, "%s script tag not found" % block_id
    return json.loads(m.group(1))


def demo_profile():
    with open(build.DEMO_PROFILE, encoding="utf-8") as f:
        return json.load(f)


def test_build_embeds_the_catalog():
    page = build.build()
    assert build.PLACEHOLDER not in page
    assert embedded_catalog(page) == catalog.CATALOG


def test_build_is_deterministic(tmp_path):
    first, second = tmp_path / "a.html", tmp_path / "b.html"
    build.main(["--out", str(first)])
    build.main(["--out", str(second)])
    assert first.read_bytes() == second.read_bytes()


def test_output_uses_lf_line_endings(tmp_path):
    out = tmp_path / "index.html"
    build.main(["--out", str(out)])
    assert b"\r\n" not in out.read_bytes()


def test_full_page_has_html_head_and_fragment_does_not():
    assert build.build().startswith("<!doctype html>")
    assert not build.build(fragment=True).startswith("<!doctype html>")


def test_output_makes_no_external_requests():
    page = build.build()
    urls = set(re.findall(r"https?://[^\s\"'<>)]+", page))
    assert urls <= ALLOWED_URLS, urls - ALLOWED_URLS
    assert not re.search(r"<script[^>]+\bsrc=", page), "external script"
    assert not re.search(r"<link[^>]+\bhref=\"https?:", page), "external stylesheet or font"


# --- the build is always neutral (PRD A1) -------------------------------------

def test_neutral_build_has_no_current_semester():
    assert "currentSem" not in catalog.META
    assert "currentSem" not in embedded_catalog(build.build())["meta"]


def test_neutral_build_has_only_neutral_start_values():
    for slot in embedded_catalog(build.build())["slots"]:
        expected = catalog.NEUTRAL_FIX if slot["t"] == "fix" else catalog.NEUTRAL_FLEX
        assert slot["def"] == expected, slot["id"]


@pytest.mark.parametrize("args", [["--demo"], ["--profile", "x.json"], ["--demo", "--profile", "x.json"]])
def test_there_is_no_way_to_build_with_personal_start_values(tmp_path, args, capsys):
    out = tmp_path / "index.html"
    with pytest.raises(SystemExit) as exc:
        build.main(args + ["--out", str(out)])
    assert exc.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err
    assert not out.exists()


def test_build_takes_no_profile():
    with pytest.raises(TypeError):
        build.build("profile.json")


def test_image_is_built_from_the_neutral_build_only():
    dockerfile = (Path(build.ROOT) / "Dockerfile").read_text(encoding="utf-8")
    assert "--profile" not in dockerfile
    assert "--demo" not in dockerfile
    copied = re.findall(r"^COPY\s+(?!--from)(?:--\S+\s+)*(\S+)", dockerfile, re.M)
    assert set(copied) <= {"build.py", "src", "docker/nginx.conf", "demo/profile.demo.json"}, copied


@pytest.mark.parametrize("template", ["no placeholder here", "__CATALOG__ and __CATALOG__"])
def test_template_needs_exactly_one_placeholder(tmp_path, monkeypatch, template):
    path = tmp_path / "index.tpl.html"
    path.write_text(template, encoding="utf-8")
    monkeypatch.setattr(build, "TEMPLATE", str(path))
    with pytest.raises(ValueError):
        build.build()


def csp_directives(page):
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">', page)
    assert m, "CSP meta tag not found"
    return dict(part.split(" ", 1) for part in m.group(1).split("; "))


def test_csp_allows_only_the_inline_script_of_the_page():
    page = build.build()
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
    directives = csp_directives(page)
    assert directives["script-src"] == "'sha256-%s'" % digest
    assert directives["default-src"] == "'none'"
    assert "unsafe" not in directives["script-src"]


def test_script_hashes_ignore_data_blocks():
    page = '<script type="application/json">{"a":1}</script><script>run()</script>'
    assert len(build.script_hashes(page)) == 1


def test_fragment_has_no_csp_meta_tag():
    assert "Content-Security-Policy" not in build.build(fragment=True)


# --- src/semester.js is embedded into the page ---------------------------------

def test_build_embeds_the_semester_functions():
    page = build.build()
    assert build.SEMESTER_PLACEHOLDER not in page
    assert "function currentSemester(" in page


def test_template_needs_the_semester_placeholder(tmp_path, monkeypatch):
    path = tmp_path / "index.tpl.html"
    path.write_text("__CATALOG__ without the other placeholder", encoding="utf-8")
    monkeypatch.setattr(build, "TEMPLATE", str(path))
    with pytest.raises(ValueError, match="__SEMESTER_JS__"):
        build.build()


def test_semester_script_must_not_close_the_script_tag(tmp_path, monkeypatch):
    path = tmp_path / "semester.js"
    path.write_text("var x = '</script>';", encoding="utf-8")
    monkeypatch.setattr(build, "SEMESTER_JS", str(path))
    with pytest.raises(ValueError, match="closing script tag"):
        build.build()


# --- fictional example plan (PRD A4) -------------------------------------------------------

def test_every_build_embeds_the_example():
    page = build.build()
    assert build.EXAMPLE_PLACEHOLDER not in page
    assert embedded_block(page, "example") == json.loads(catalog.to_json(catalog.example_state(demo_profile())))


def test_example_does_not_change_the_catalog_block():
    page = build.build()
    assert embedded_block(page, "catalog") == catalog.CATALOG


def test_example_has_no_current_semester_date_and_a_valid_semester():
    state = catalog.example_state(demo_profile())
    assert state["currentSem"] in range(1, 7)
    assert set(state) == {"currentSem", "m", "names"}


def test_example_only_uses_known_slots_and_statuses():
    state = catalog.example_state(demo_profile())
    slots = {s["id"]: s for s in catalog.CATALOG["slots"]}
    assert state["m"], "the example needs content"
    for sid, entry in state["m"].items():
        assert sid in slots
        assert entry["s"] in {"ok", "run", "retake", "nospot", "plan"}


def test_example_states_that_it_is_fictional():
    note = demo_profile()["note"].lower()
    assert "describes no real person" in note


def test_example_needs_a_current_semester():
    with pytest.raises(AssertionError):
        catalog.example_state({"slots": {}})


def test_template_needs_the_example_placeholder(tmp_path, monkeypatch):
    template = Path(build.TEMPLATE).read_text(encoding="utf-8").replace(build.EXAMPLE_PLACEHOLDER, "")
    path = tmp_path / "index.tpl.html"
    path.write_text(template, encoding="utf-8")
    monkeypatch.setattr(build, "TEMPLATE", str(path))
    with pytest.raises(ValueError, match="__EXAMPLE__"):
        build.build()


# --- src/exchange.js is embedded into the page ----------------------------------

def test_build_embeds_the_exchange_functions():
    page = build.build()
    assert build.EXCHANGE_PLACEHOLDER not in page
    assert "function buildExport(" in page
    assert "function exportFileName(" in page


def test_template_needs_the_exchange_placeholder(tmp_path, monkeypatch):
    template = Path(build.TEMPLATE).read_text(encoding="utf-8").replace(build.EXCHANGE_PLACEHOLDER, "")
    path = tmp_path / "index.tpl.html"
    path.write_text(template, encoding="utf-8")
    monkeypatch.setattr(build, "TEMPLATE", str(path))
    with pytest.raises(ValueError, match="__EXCHANGE_JS__"):
        build.build()


def test_exchange_script_must_not_close_the_script_tag(tmp_path, monkeypatch):
    path = tmp_path / "exchange.js"
    path.write_text("var x = '</script>';", encoding="utf-8")
    monkeypatch.setattr(build, "EXCHANGE_JS", str(path))
    with pytest.raises(ValueError, match="closing script tag"):
        build.build()


def test_page_still_has_exactly_one_executable_script():
    assert len(build.script_hashes(build.build())) == 1


def test_embedded_scripts_do_not_redefine_names_of_the_page():
    """semester.js and exchange.js share one scope with the page script. A function or variable of the
    same name in the page would silently replace the shared one (function declarations are hoisted).
    Only top-level names count: column 0 in the shared files, two spaces inside the page's wrapper."""
    template = Path(build.TEMPLATE).read_text(encoding="utf-8")
    page_part = template.split("__EXCHANGE_JS__", 1)[1]

    def names(text, indent):
        found = re.findall(r"^%s(?:function\s+(\w+)\s*\(|var\s+(\w+)\b)" % indent, text, re.M)
        return {a or b for a, b in found}

    page_names = names(page_part, "  ")
    assert {"render", "sane"} <= page_names, "the pattern must find the page's own top-level names"
    for path in (build.SEMESTER_JS, build.EXCHANGE_JS):
        shared = names(Path(path).read_text(encoding="utf-8"), "")
        assert shared, path
        assert not shared & page_names, (path, sorted(shared & page_names))
