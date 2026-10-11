"""Example plan as an unsaved sandbox (PRD A4). The browser clock is fixed to 10 Oct 2026."""
import json
from datetime import datetime

import pytest
from playwright.sync_api import expect

import build
import catalog

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"
NOW = datetime(2026, 10, 10, 12, 0, 0)

BANNER = "#sandbox"
WELCOME = "#welcome"

BLOCKED = ("Object.defineProperty(window, 'localStorage', "
           "{get() { throw new DOMException('denied', 'SecurityError'); }});")


def example_lp():
    """Passed LP of the example, computed from the catalog and the demo file (not from the page)."""
    with open(build.DEMO_PROFILE, encoding="utf-8") as f:
        state = catalog.example_state(json.load(f))
    lp = {s["id"]: s["lp"] for s in catalog.CATALOG["slots"]}
    return sum(lp[sid] for sid, entry in state["m"].items() if entry["s"] == "ok")


def slot_lp(slot_id):
    return next(s["lp"] for s in catalog.CATALOG["slots"] if s["id"] == slot_id)


def lp(page):
    return page.locator("#lpnow")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def raw(page, key=KEY):
    return page.evaluate("key => localStorage.getItem(key)", key)


def put(page, key, value):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [key, value])


def own_plan(m=None):
    profile = {"name": "Mein Plan", "start": None, "rev": 1, "m": m or {}, "names": {}}
    return json.dumps({"v": 2, "active": "p1", "profiles": {"p1": profile}})


def first_visit(page):
    page.clock.set_fixed_time(NOW)
    page.reload()


def open_example(page, base_url):
    """Open the page straight from the link #beispiel (a fresh navigation, not a hash change)."""
    page.goto("about:blank")
    page.goto(base_url + "/#beispiel")


def now_labels(page):
    return page.locator(".lab", has_text="jetzt").locator("strong").all_inner_texts()


# --- entry points ---------------------------------------------------------------------

def test_welcome_card_opens_the_example_with_one_click(app):
    first_visit(app)
    app.click("#wExample")
    expect(app.locator(BANNER)).to_be_visible()
    expect(app.locator(BANNER)).to_contain_text("erfundenen Daten")
    expect(app.locator(WELCOME)).to_be_hidden()
    expect(lp(app)).to_have_text(str(example_lp()))
    assert example_lp() > 0
    assert app.evaluate("location.hash") == "#beispiel"


def test_footer_link_opens_the_example_even_with_an_own_plan(app):
    put(app, KEY, own_plan({"B11": {"s": "ok", "n": "", "mod": None}}))
    app.reload()
    expect(lp(app)).to_have_text("6")
    app.click("#exampleLink a")
    expect(app.locator(BANNER)).to_be_visible()
    expect(lp(app)).to_have_text(str(example_lp()))
    expect(app.locator("#exampleLink")).to_be_hidden()


def test_link_to_the_example_works_on_a_fresh_navigation(app, base_url):
    open_example(app, base_url)
    expect(app.locator(BANNER)).to_be_visible()
    expect(lp(app)).to_have_text(str(example_lp()))
    expect(app.locator(WELCOME)).to_be_hidden()


def test_link_to_the_example_works_with_an_own_plan(app, base_url):
    put(app, KEY, own_plan({"B11": {"s": "ok", "n": "", "mod": None}}))
    open_example(app, base_url)
    expect(app.locator(BANNER)).to_be_visible()
    expect(lp(app)).to_have_text(str(example_lp()))


def test_plain_visit_has_no_banner_and_shows_the_footer_link(app):
    expect(app.locator(BANNER)).to_be_hidden()
    expect(app.locator("#exampleLink")).to_be_visible()


# --- nothing is ever written -------------------------------------------------------------

def test_changes_in_the_example_are_not_saved(app):
    first_visit(app)
    app.click("#wExample")
    before = example_lp()
    set_passed(app, "B41")
    expect(lp(app)).to_have_text(str(before + slot_lp("B41")))
    app.fill("#noteIn", "nur Beispiel")
    app.select_option("#startTerm", "WiSe")
    assert raw(app) is None
    assert raw(app, OLD_KEY) is None
    assert app.evaluate("localStorage.length") == 0


def test_own_plan_stays_byte_for_byte_the_same(app):
    stored = own_plan({"B11": {"s": "ok", "n": "mein", "mod": None}})
    put(app, KEY, stored)
    app.reload()
    app.click("#exampleLink a")
    set_passed(app, "B41")
    app.click("#reset")
    app.click("#sandboxLeave")
    assert raw(app) == stored
    expect(lp(app)).to_have_text("6")


def test_reload_in_the_example_starts_it_again(app, base_url):
    open_example(app, base_url)
    set_passed(app, "B41")
    app.reload()
    expect(app.locator(BANNER)).to_be_visible()
    expect(lp(app)).to_have_text(str(example_lp()))


# --- the example does not depend on the date ----------------------------------------------

@pytest.mark.parametrize("now, term, year, label", [
    (datetime(2026, 10, 10, 12), "SoSe", "2025", "aktuell: 4. Semester"),
    (datetime(2027, 4, 15, 12), "WiSe", "2025", "aktuell: 4. Semester"),
    (datetime(2030, 1, 20, 12), "SoSe", "2028", "aktuell: 4. Semester"),
])
def test_example_is_always_in_the_4th_semester(app, now, term, year, label):
    app.clock.set_fixed_time(now)
    app.reload()
    app.click("#exampleLink a")
    expect(app.locator(BANNER)).to_be_visible()
    assert now_labels(app) == ["4."]
    expect(app.locator("#startTerm")).to_have_value(term)
    expect(app.locator("#startYear")).to_have_value(year)
    expect(app.locator("#startHint")).to_have_text(label)


def test_example_shows_every_status(app):
    app.click("#exampleLink a")
    expect(app.locator(BANNER)).to_be_visible()
    for status in ("s-ok", "s-run", "s-retake", "s-plan"):
        assert app.locator(".cell." + status).count() > 0, status


# --- leaving ----------------------------------------------------------------------------------

def test_leave_without_a_plan_goes_to_the_start_choice_for_an_own_plan(app):
    first_visit(app)
    app.click("#wExample")
    app.click("#sandboxLeave")
    expect(app.locator(BANNER)).to_be_hidden()
    expect(app.locator(WELCOME)).to_be_visible()
    expect(app.locator("#welcomeOwn")).to_be_visible()
    expect(app.locator("#welcomeStart")).to_be_hidden()
    expect(lp(app)).to_have_text("0")
    assert app.evaluate("location.hash") == ""
    assert raw(app) is None


def test_changes_in_the_example_do_not_count_as_choosing_a_plan(app):
    first_visit(app)
    app.click("#wExample")
    set_passed(app, "B41")
    app.click("#sandboxLeave")
    expect(app.locator(WELCOME)).to_be_visible()        # still the first visit
    expect(app.locator("#welcomeOwn")).to_be_visible()


def test_own_plan_can_be_started_after_the_example(app):
    first_visit(app)
    app.click("#wExample")
    app.click("#sandboxLeave")
    app.click('#welcome [data-term="WiSe"]')
    app.fill("#wYear", "2026")
    app.click("#wGo")
    expect(app.locator(WELCOME)).to_be_hidden()
    assert json.loads(raw(app))["profiles"]["p1"]["start"] == {"term": "WiSe", "year": 2026}
    assert json.loads(raw(app))["profiles"]["p1"]["m"] == {}, "no example data in the own plan"


def test_leave_with_an_own_plan_shows_it_again(app):
    put(app, KEY, own_plan({"B11": {"s": "ok", "n": "", "mod": None}}))
    app.reload()
    app.click("#exampleLink a")
    app.click("#sandboxLeave")
    expect(app.locator(BANNER)).to_be_hidden()
    expect(app.locator(WELCOME)).to_be_hidden()
    expect(lp(app)).to_have_text("6")
    expect(app.locator("#exampleLink")).to_be_visible()
    assert app.evaluate("location.hash") == ""


def test_browser_back_leaves_the_example(app):
    app.click("#exampleLink a")
    expect(app.locator(BANNER)).to_be_visible()
    app.go_back()
    expect(app.locator(BANNER)).to_be_hidden()
    expect(lp(app)).to_have_text("0")


def test_leaving_resets_the_undo_history(app):
    set_passed(app, "B31")
    app.click("#exampleLink a")
    expect(app.locator("#undo")).to_be_disabled()
    set_passed(app, "B41")
    expect(app.locator("#undo")).to_be_enabled()
    app.click("#sandboxLeave")
    expect(app.locator("#undo")).to_be_disabled()
    expect(lp(app)).to_have_text("6")


def test_open_panel_is_closed_when_the_example_starts(app):
    app.click('.cell[data-id="B31"]')
    expect(app.locator("#panel")).to_be_visible()
    app.click("#exampleLink a")
    expect(app.locator("#panel")).to_be_hidden()


# --- blocked storage ----------------------------------------------------------------------------

def test_works_with_blocked_storage_and_gives_the_own_plan_back(app):
    app.add_init_script(BLOCKED)
    app.reload()
    expect(app.locator("#nostore")).to_be_visible()
    set_passed(app, "B31")                        # own plan, only in memory
    app.click("#exampleLink a")
    expect(app.locator(BANNER)).to_be_visible()
    expect(app.locator("#nostore")).to_be_hidden()   # the banner of the example says it already
    expect(lp(app)).to_have_text(str(example_lp()))
    app.click("#sandboxLeave")
    expect(app.locator("#nostore")).to_be_visible()
    expect(lp(app)).to_have_text("6")


# --- other tabs -------------------------------------------------------------------------------------

def test_change_in_another_tab_does_not_touch_the_example_but_is_loaded_on_leaving(app, base_url):
    app.click("#exampleLink a")
    other = app.context.new_page()
    other.goto(base_url + "/")
    set_passed(other, "B32")
    expect(lp(app)).to_have_text(str(example_lp()))        # the example stays as it is
    expect(app.locator(BANNER)).to_be_visible()
    app.click("#sandboxLeave")
    expect(lp(app)).to_have_text("5")                       # the other tab's plan
    expect(app.locator(WELCOME)).to_be_hidden()
