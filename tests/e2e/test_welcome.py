"""Start choice on the first visit (PRD A2). The browser clock is fixed to 10 Oct 2026."""
import json
from datetime import datetime

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"
NOW = datetime(2026, 10, 10, 12, 0, 0)

WELCOME = "#welcome"
OWN = "#wOwn"
GO = "#wGo"
YEAR = "#wYear"


def fresh_first_visit(page):
    page.clock.set_fixed_time(NOW)
    page.reload()


def put(page, key, value):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [key, value])


def stored_start(page):
    raw = page.evaluate("key => localStorage.getItem(key)", KEY)
    return None if raw is None else json.loads(raw)["profiles"]["p1"]["start"]


def now_labels(page):
    return page.locator(".lab", has_text="jetzt").locator("strong").all_inner_texts()


def v2_plan(**extra):
    profile = {"name": "Mein Plan", "start": None, "rev": 1, "m": {}, "names": {}}
    profile.update(extra)
    return json.dumps({"v": 2, "active": "p1", "profiles": {"p1": profile}})


# --- when the card is shown ----------------------------------------------------------

def test_first_visit_shows_the_choice_above_the_plan(app):
    fresh_first_visit(app)
    expect(app.locator(WELCOME)).to_be_visible()
    expect(app.locator(OWN)).to_have_text("Eigenen Plan starten")
    expect(app.locator(".cell")).to_have_count(34)      # the plan stays visible behind it
    assert app.evaluate("key => localStorage.getItem(key)", KEY) is None, "showing the card writes nothing"


def test_not_shown_when_a_plan_exists(app):
    put(app, KEY, v2_plan())
    app.reload()
    expect(app.locator(WELCOME)).to_be_hidden()


def test_not_shown_after_the_old_plan_was_migrated(app):
    put(app, OLD_KEY, json.dumps({"rev": 1, "m": {"B11": {"s": "ok", "n": ""}}, "names": {}}))
    app.reload()
    expect(app.locator(WELCOME)).to_be_hidden()
    assert app.evaluate("key => localStorage.getItem(key)", KEY) is not None


def test_an_unusable_v2_key_still_counts_as_a_plan(app):
    put(app, KEY, "{not json")
    app.reload()
    expect(app.locator(WELCOME)).to_be_hidden()


def test_disappears_when_the_plan_is_changed_without_the_card(app):
    app.click('.cell[data-id="B31"]')
    app.click('#opts .opt[data-s="ok"]')
    expect(app.locator(WELCOME)).to_be_hidden()
    app.reload()
    expect(app.locator(WELCOME)).to_be_hidden()


# --- "Eigenen Plan starten" ----------------------------------------------------------

def test_own_plan_in_at_most_3_clicks(app):
    app.add_init_script(
        "window.__clicks = 0; window.addEventListener('click', () => { window.__clicks++; }, true);")
    fresh_first_visit(app)
    app.click(OWN)                                       # 1
    app.click('#welcome [data-term="SoSe"]')            # 2
    app.keyboard.type("2025")                            # the year field has the focus, no click needed
    app.click(GO)                                        # 3
    assert app.evaluate("window.__clicks") == 3
    expect(app.locator(WELCOME)).to_be_hidden()
    assert now_labels(app) == ["4."]                     # SoSe 2025 on 10 Oct 2026
    assert stored_start(app) == {"term": "SoSe", "year": 2025}


def test_not_shown_again_after_the_choice(app):
    fresh_first_visit(app)
    app.click(OWN)
    app.click('#welcome [data-term="WiSe"]')
    app.keyboard.type("2024")
    app.keyboard.press("Enter")
    expect(app.locator(WELCOME)).to_be_hidden()
    app.reload()
    expect(app.locator(WELCOME)).to_be_hidden()
    assert now_labels(app) == ["5."]
    expect(app.locator("#startTerm")).to_have_value("WiSe")
    expect(app.locator("#startYear")).to_have_value("2024")


def test_go_needs_a_term_and_a_four_digit_year(app):
    fresh_first_visit(app)
    app.click(OWN)
    expect(app.locator(GO)).to_be_disabled()
    app.fill(YEAR, "2025")
    expect(app.locator(GO)).to_be_disabled()             # no term yet
    app.click('#welcome [data-term="SoSe"]')
    expect(app.locator(GO)).to_be_enabled()
    app.fill(YEAR, "25")
    expect(app.locator(GO)).to_be_disabled()
    app.fill(YEAR, "")
    expect(app.locator(GO)).to_be_disabled()


def test_enter_with_an_incomplete_choice_does_nothing(app):
    fresh_first_visit(app)
    app.click(OWN)
    app.click('#welcome [data-term="SoSe"]')
    app.keyboard.type("20")
    app.keyboard.press("Enter")
    expect(app.locator(WELCOME)).to_be_visible()
    assert stored_start(app) is None


def test_choosing_the_term_marks_it_and_moves_the_focus_to_the_year(app):
    fresh_first_visit(app)
    app.click(OWN)
    expect(app.locator('#welcome [data-term="SoSe"]')).to_be_focused()
    app.click('#welcome [data-term="WiSe"]')
    expect(app.locator('#welcome [data-term="WiSe"]')).to_have_attribute("aria-pressed", "true")
    expect(app.locator('#welcome [data-term="SoSe"]')).to_have_attribute("aria-pressed", "false")
    expect(app.locator(YEAR)).to_be_focused()


def test_back_returns_to_the_first_step_and_forgets_the_input(app):
    fresh_first_visit(app)
    app.click(OWN)
    app.click('#welcome [data-term="SoSe"]')
    app.keyboard.type("2025")
    app.click("#wBack")
    expect(app.locator(OWN)).to_be_visible()
    expect(app.locator(OWN)).to_be_focused()
    app.click(OWN)
    expect(app.locator(YEAR)).to_have_value("")
    expect(app.locator(GO)).to_be_disabled()
    assert stored_start(app) is None


def test_future_start_marks_no_semester(app):
    fresh_first_visit(app)
    app.click(OWN)
    app.click('#welcome [data-term="WiSe"]')
    app.keyboard.type("2027")
    app.click(GO)
    assert now_labels(app) == []
    expect(app.locator("#startHint")).to_have_text("Studium beginnt im WiSe 2027/28")


# --- other tabs and blocked storage --------------------------------------------------

def test_other_tab_hides_the_card_once_a_plan_exists(app, base_url):
    second = app.context.new_page()
    second.goto(base_url + "/")
    expect(second.locator(WELCOME)).to_be_visible()
    app.click(OWN)
    app.click('#welcome [data-term="SoSe"]')
    app.keyboard.type("2025")
    app.click(GO)
    expect(second.locator(WELCOME)).to_be_hidden()      # storage event, no reload


def test_card_works_when_storage_is_blocked(app):
    app.add_init_script(
        "Storage.prototype.setItem = function () { throw new DOMException('full', 'QuotaExceededError'); };")
    fresh_first_visit(app)
    expect(app.locator("#nostore")).to_be_visible()
    expect(app.locator(WELCOME)).to_be_visible()
    app.click(OWN)
    app.click('#welcome [data-term="SoSe"]')
    app.keyboard.type("2025")
    app.click(GO)
    expect(app.locator(WELCOME)).to_be_hidden()         # for this session
    assert now_labels(app) == ["4."]
