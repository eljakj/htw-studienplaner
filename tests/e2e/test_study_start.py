"""Study start determines the current semester (PRD A3). The browser clock is fixed to 10 Oct 2026."""
import json
from datetime import datetime

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
NOW = datetime(2026, 10, 10, 12, 0, 0)

HINT = "#startHint"


def open_at_fixed_date(page):
    page.clock.set_fixed_time(NOW)
    page.reload()


def choose_start(page, term, year):
    page.select_option("#startTerm", term)
    page.fill("#startYear", str(year))
    page.press("#startYear", "Enter")


def now_labels(page):
    """Semester labels that are marked 'jetzt', for example ['4.']."""
    return page.locator(".lab", has_text="jetzt").locator("strong").all_inner_texts()


def stored_start(page):
    raw = page.evaluate("key => localStorage.getItem(key)", KEY)
    return None if raw is None else json.loads(raw)["profiles"]["p1"]["start"]


def test_without_a_start_no_semester_is_marked(app):
    open_at_fixed_date(app)
    assert now_labels(app) == []
    expect(app.locator("#startTerm")).to_have_value("")
    expect(app.locator(HINT)).to_contain_text("Bitte wählen")


def test_summer_2025_on_10_oct_2026_marks_semester_4(app):
    open_at_fixed_date(app)
    choose_start(app, "SoSe", 2025)
    assert now_labels(app) == ["4."]
    expect(app.locator(HINT)).to_have_text("aktuell: 4. Semester")


def test_start_can_be_changed_later(app):
    open_at_fixed_date(app)
    choose_start(app, "SoSe", 2025)
    choose_start(app, "WiSe", 2024)
    assert now_labels(app) == ["5."]
    assert stored_start(app) == {"term": "WiSe", "year": 2024}


def test_start_survives_a_reload(app):
    open_at_fixed_date(app)
    choose_start(app, "SoSe", 2025)
    app.reload()
    assert now_labels(app) == ["4."]
    expect(app.locator("#startTerm")).to_have_value("SoSe")
    expect(app.locator("#startYear")).to_have_value("2025")


def test_start_more_than_6_semesters_ago_stays_at_6(app):
    open_at_fixed_date(app)
    choose_start(app, "WiSe", 2023)       # WiSe 2023/24 is the 7th semester in WiSe 2026/27
    assert now_labels(app) == ["6."]
    expect(app.locator(HINT)).to_have_text("über Regelstudienzeit")


def test_start_in_the_future_marks_nothing(app):
    open_at_fixed_date(app)
    choose_start(app, "WiSe", 2027)
    assert now_labels(app) == []
    expect(app.locator(HINT)).to_have_text("Studium beginnt im WiSe 2027/28")


def test_incomplete_or_invalid_start_is_not_stored(app):
    open_at_fixed_date(app)
    app.select_option("#startTerm", "SoSe")           # no year yet
    assert now_labels(app) == []
    expect(app.locator("#startTerm")).to_have_value("SoSe")   # the choice is not reset
    assert stored_start(app) is None
    choose_start(app, "SoSe", 25)                      # not a 4-digit year
    assert now_labels(app) == []
    assert stored_start(app) is None


def test_clearing_the_year_removes_the_start(app):
    open_at_fixed_date(app)
    choose_start(app, "SoSe", 2025)
    app.fill("#startYear", "")
    app.press("#startYear", "Enter")
    assert now_labels(app) == []
    assert stored_start(app) is None


def test_start_is_stored_in_the_profile(app):
    open_at_fixed_date(app)
    choose_start(app, "SoSe", 2025)
    assert stored_start(app) == {"term": "SoSe", "year": 2025}


def test_other_tab_shows_the_new_start(app, base_url):
    open_at_fixed_date(app)
    second = app.context.new_page()
    second.clock.set_fixed_time(NOW)
    second.goto(base_url + "/")
    choose_start(app, "SoSe", 2025)
    expect(second.locator("#startTerm")).to_have_value("SoSe")
    expect(second.locator("#startYear")).to_have_value("2025")
    expect(second.locator(HINT)).to_have_text("aktuell: 4. Semester")
    assert now_labels(second) == ["4."]


def test_invalid_stored_start_is_dropped(app):
    stored = {"v": 2, "active": "p1", "profiles": {"p1": {
        "name": "Mein Plan", "start": {"term": "Spring", "year": 20}, "rev": 1, "m": {}, "names": {}}}}
    app.evaluate("([key, value]) => localStorage.setItem(key, value)", [KEY, json.dumps(stored)])
    open_at_fixed_date(app)
    assert now_labels(app) == []
    expect(app.locator("#startTerm")).to_have_value("")
