"""A saved plan that refers to modules or slots the catalog no longer has.

The fixture is a fictional plan from an older catalog: WP1 has a module that is gone, AWE 1 has a course that is
gone, and the slot X77 does not exist any more. Everything else is still valid."""
import json
import re
from pathlib import Path

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
OUTDATED = (FIXTURES / "storage_outdated_v2.json").read_text(encoding="utf-8")
PASSED_LP = 6 + 5 + 2 + 4   # B31, WP1 (status stays), B36 (status stays), B15

NOTE = "#catnote"
BLOCKED_WRITE = ("Storage.prototype.setItem = function () "
                 "{ throw new DOMException('full', 'QuotaExceededError'); };")


def put(page, value, key=KEY):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [key, value])


def raw(page, key=KEY):
    return page.evaluate("key => localStorage.getItem(key)", key)


def load_outdated(page):
    put(page, OUTDATED)
    page.reload()


def cell(page, sid):
    return page.locator('.cell[data-id="%s"]' % sid)


# --- the notice ------------------------------------------------------------------------------

def test_notice_names_what_the_catalog_no_longer_has(app):
    load_outdated(app)
    expect(app.locator(NOTE)).to_be_visible()
    text = app.locator("#catnoteText").inner_text()
    assert text.startswith("Der Katalog hat sich geändert.")
    assert "Wahlpflichtmodul 1 (B9991)" in text
    assert "AWE 1 (A99999999)" in text
    assert "Plätze: X77" in text
    assert "Status und Notizen bleiben erhalten." in text
    assert "B310" not in text and "Fremdsprache" not in text, "valid choices are not mentioned"


def test_values_stay_and_only_the_missing_choices_go(app):
    load_outdated(app)
    expect(app.locator("#lpnow")).to_have_text(str(PASSED_LP))
    expect(cell(app, "B31")).to_contain_text("bleibt")                  # the note stays
    expect(cell(app, "WP1")).to_have_class(re.compile(r"\bs-ok\b"))       # the status stays: passed
    expect(cell(app, "WP1")).to_contain_text("Modul gestrichen")        # the note stays
    expect(cell(app, "WP1").locator(".nm")).to_have_text("Wahlpflichtmodul 1")   # no module name: the module is gone
    expect(cell(app, "WP2")).to_contain_text("Programmierkonzepte für Data Mining")   # a valid module stays
    expect(cell(app, "B15")).to_contain_text("English for IT")
    expect(app.locator('.cell[data-id="B11"] .nm')).to_have_text("Eigener Titel")


def test_the_cleaned_plan_is_saved_without_any_change_by_the_user(app):
    load_outdated(app)
    expect(app.locator(NOTE)).to_be_visible()
    profile = json.loads(raw(app))["profiles"]["p1"]
    assert "X77" not in profile["m"]
    assert profile["m"]["WP1"] == {"s": "ok", "n": "Modul gestrichen", "mod": None}
    assert profile["m"]["B36"]["mod"] is None
    assert profile["m"]["WP2"]["mod"] == "B310"
    assert profile["m"]["B31"] == {"s": "ok", "n": "bleibt", "mod": None}
    assert profile["rev"] == 1760000000000, "the cleaning is not a change of the plan"
    assert profile["created"] == 1750000000000
    assert profile["start"] == {"term": "SoSe", "year": 2025}


def test_the_notice_is_shown_once_and_not_again_after_a_reload(app):
    load_outdated(app)
    expect(app.locator(NOTE)).to_be_visible()
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()
    expect(app.locator("#lpnow")).to_have_text(str(PASSED_LP))
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()


def test_the_notice_can_be_closed(app):
    load_outdated(app)
    app.click("#catnoteOk")
    expect(app.locator(NOTE)).to_be_hidden()


def test_a_second_tab_after_the_cleaning_sees_no_notice(app, base_url):
    load_outdated(app)
    expect(app.locator(NOTE)).to_be_visible()
    second = app.context.new_page()
    second.goto(base_url + "/")
    expect(second.locator(NOTE)).to_be_hidden()
    expect(second.locator("#lpnow")).to_have_text(str(PASSED_LP))


# --- when there is nothing to say ---------------------------------------------------------------

def test_a_current_plan_gets_no_notice_and_is_not_rewritten(app):
    plan = json.dumps({"v": 2, "active": "p1", "profiles": {"p1": {
        "name": "Mein Plan", "start": None, "rev": 5, "m": {"B31": {"s": "ok", "n": "", "mod": None}}, "names": {}}}})
    put(app, plan)
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()
    assert raw(app) == plan, "a plain visit writes nothing"


def test_damaged_statuses_are_dropped_silently_and_not_rewritten(app):
    plan = json.dumps({"v": 2, "active": "p1", "profiles": {"p1": {
        "name": "Mein Plan", "start": None, "rev": 5, "m": {"B31": {"s": "bogus", "n": ""}}, "names": {}}}})
    put(app, plan)
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()
    assert raw(app) == plan


def test_a_first_visit_has_no_notice(app):
    expect(app.locator(NOTE)).to_be_hidden()
    assert raw(app) is None


# --- other ways a plan is loaded --------------------------------------------------------------------

def test_an_old_v1_plan_with_removed_modules_gets_the_notice_after_the_migration(app):
    v1 = json.dumps({"rev": 3, "m": {"B31": {"s": "ok", "n": ""}, "WP1": {"s": "ok", "n": "", "mod": "B9991"}}, "names": {}})
    put(app, v1, OLD_KEY)
    app.reload()
    expect(app.locator(NOTE)).to_be_visible()
    expect(app.locator("#catnoteText")).to_contain_text("Wahlpflichtmodul 1 (B9991)")
    assert json.loads(raw(app))["profiles"]["p1"]["m"]["WP1"]["mod"] is None
    assert raw(app, OLD_KEY) == v1, "the old key stays untouched"
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()


def test_notice_is_hidden_in_the_example_and_comes_back_afterwards(app):
    load_outdated(app)
    expect(app.locator(NOTE)).to_be_visible()
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    expect(app.locator(NOTE)).to_be_hidden()
    app.click("#sandboxLeave")
    expect(app.locator(NOTE)).to_be_visible()


def test_text_from_the_storage_is_shown_as_text(app):
    plan = json.loads(OUTDATED)
    plan["profiles"]["p1"]["m"]["WP1"]["mod"] = "<img id=pwn src=x>" + "x" * 50
    plan["profiles"]["p1"]["m"]["<b id=pwn2>"] = {"s": "ok", "n": ""}
    put(app, json.dumps(plan))
    app.reload()
    expect(app.locator(NOTE)).to_be_visible()
    assert app.locator("#pwn, #pwn2").count() == 0
    text = app.locator("#catnoteText").inner_text()
    assert "<img id=pwn src=x>" in text and len(text) < 400, "shown as text and shortened"


def test_with_a_write_blocked_browser_the_plan_is_cleaned_in_memory_and_the_notice_stays(app):
    put(app, OUTDATED)
    app.add_init_script(BLOCKED_WRITE)
    app.reload()
    expect(app.locator(NOTE)).to_be_visible()
    expect(app.locator("#nostore")).to_be_visible()
    expect(app.locator("#saveerr")).to_be_hidden()
    expect(app.locator("#lpnow")).to_have_text(str(PASSED_LP))
    expect(cell(app, "WP1").locator(".nm")).to_have_text("Wahlpflichtmodul 1")
    app.reload()
    expect(app.locator(NOTE)).to_be_visible(), "nothing could be cleaned in the storage, so it is mentioned again"
