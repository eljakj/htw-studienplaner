"""Reminder to back up the plan (PRD A10). The browser clock is fixed to 11 Oct 2026, midday."""
import json
from datetime import datetime

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
NOW = datetime(2026, 10, 11, 12, 0, 0)
NOW_MS = int(NOW.timestamp() * 1000)
DAY = 86400000

NOTE = "#backupnote"


def days_ago(n):
    return NOW_MS - n * DAY


def put(page, value):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [KEY, json.dumps(value)])


def stored(page):
    raw = page.evaluate("key => localStorage.getItem(key)", KEY)
    return None if raw is None else json.loads(raw)


def plan(name="Mein Plan", m=None, **extra):
    profile = {"name": name, "start": None, "rev": 1, "names": {},
               "m": {"B31": {"s": "ok", "n": "", "mod": None}} if m is None else m}
    profile.update(extra)
    return profile


def open_with(page, **profiles):
    put(page, {"v": 2, "active": sorted(profiles)[0], "profiles": profiles})
    page.clock.set_fixed_time(NOW)
    page.reload()


# --- when the notice appears -------------------------------------------------------------------

def test_shown_after_30_days_without_an_export(app):
    open_with(app, p1=plan(created=days_ago(31)))
    expect(app.locator(NOTE)).to_be_visible()
    expect(app.locator("#backupnoteText")).to_contain_text("„Mein Plan“")
    expect(app.locator("#backupnoteText")).to_contain_text("30 Tagen")


def test_not_shown_before_30_days(app):
    open_with(app, p1=plan(created=days_ago(29)))
    expect(app.locator(NOTE)).to_be_hidden()


def test_exactly_30_days_counts(app):
    open_with(app, p1=plan(created=days_ago(30)))
    expect(app.locator(NOTE)).to_be_visible()


def test_a_recent_export_wins_over_an_old_plan(app):
    open_with(app, p1=plan(created=days_ago(200), lastExport=days_ago(5)))
    expect(app.locator(NOTE)).to_be_hidden()


def test_an_old_export_shows_the_notice(app):
    open_with(app, p1=plan(created=days_ago(200), lastExport=days_ago(40)))
    expect(app.locator(NOTE)).to_be_visible()


def test_an_empty_plan_needs_no_backup(app):
    open_with(app, p1=plan(m={}, created=days_ago(100)))
    expect(app.locator(NOTE)).to_be_hidden()


def test_first_visit_shows_nothing(app):
    expect(app.locator(NOTE)).to_be_hidden()


def test_a_plan_without_a_date_has_no_reference_and_no_notice(app):
    open_with(app, p1=plan())
    expect(app.locator(NOTE)).to_be_hidden()


def test_the_first_change_of_an_old_plan_starts_the_clock(app):
    open_with(app, p1=plan())
    app.click('.cell[data-id="B32"]')
    app.click('#opts .opt[data-s="ok"]')
    assert stored(app)["profiles"]["p1"]["created"] == NOW_MS
    expect(app.locator(NOTE)).to_be_hidden()


def test_garbage_in_the_dates_is_ignored(app):
    open_with(app, p1=plan(created="gestern", lastExport={"x": 1}))
    expect(app.locator(NOTE)).to_be_hidden()
    expect(app.locator(".cell")).to_have_count(34)


# --- the buttons -------------------------------------------------------------------------------------

def test_export_from_the_notice_downloads_and_hides_it(app):
    open_with(app, p1=plan(created=days_ago(60)))
    with app.expect_download() as info:
        app.click("#backupnoteNow")
    assert info.value.suggested_filename == "studienverlauf-mein-plan-2026-10-11.json"
    expect(app.locator(NOTE)).to_be_hidden()
    assert stored(app)["profiles"]["p1"]["lastExport"] == NOW_MS
    app.reload()
    expect(app.locator(NOTE)).to_be_hidden()


def test_normal_export_button_also_resets_the_clock(app):
    open_with(app, p1=plan(created=days_ago(60)))
    with app.expect_download():
        app.click("#export")
    expect(app.locator(NOTE)).to_be_hidden()
    assert stored(app)["profiles"]["p1"]["lastExport"] == NOW_MS


def test_later_hides_it_for_this_visit_only(app):
    open_with(app, p1=plan(created=days_ago(60)))
    app.click("#backupnoteLater")
    expect(app.locator(NOTE)).to_be_hidden()
    assert stored(app)["profiles"]["p1"].get("lastExport") is None   # nothing is written
    app.reload()
    expect(app.locator(NOTE)).to_be_visible()


def test_later_stays_after_further_changes(app):
    open_with(app, p1=plan(created=days_ago(60)))
    app.click("#backupnoteLater")
    app.click('.cell[data-id="B32"]')
    app.click('#opts .opt[data-s="ok"]')
    expect(app.locator(NOTE)).to_be_hidden()


def test_the_notice_comes_back_when_the_plan_gets_emptied_and_filled_again(app):
    open_with(app, p1=plan(created=days_ago(60)))
    expect(app.locator(NOTE)).to_be_visible()
    app.click('.cell[data-id="B31"]')
    app.click('#opts .opt[data-s="plan"]')                            # back to the default: no deviation is stored
    assert stored(app)["profiles"]["p1"]["m"] == {}
    expect(app.locator(NOTE)).to_be_hidden()                          # nothing left to lose
    app.click('#opts .opt[data-s="ok"]')
    expect(app.locator(NOTE)).to_be_visible()


# --- export on the first visit writes nothing ------------------------------------------------------

def test_export_of_the_unsaved_first_plan_does_not_create_it(app):
    with app.expect_download():
        app.click("#export")
    assert stored(app) is None


# --- profiles and sandbox ------------------------------------------------------------------------------

def test_each_plan_has_its_own_clock(app):
    open_with(app, p1=plan("Alt", created=days_ago(90)),
              p2=plan("Neu", created=days_ago(2)))
    expect(app.locator(NOTE)).to_be_visible()
    expect(app.locator("#backupnoteText")).to_contain_text("„Alt“")
    app.select_option("#profSel", "p2")
    expect(app.locator(NOTE)).to_be_hidden()
    app.select_option("#profSel", "p1")
    expect(app.locator(NOTE)).to_be_visible()


def test_exporting_one_plan_leaves_the_other_due(app):
    open_with(app, p1=plan("Alt", created=days_ago(90)), p2=plan("Auch alt", created=days_ago(90)))
    with app.expect_download():
        app.click("#backupnoteNow")
    expect(app.locator(NOTE)).to_be_hidden()
    app.select_option("#profSel", "p2")
    expect(app.locator(NOTE)).to_be_visible()
    plans = stored(app)["profiles"]
    assert plans["p1"]["lastExport"] == NOW_MS and "lastExport" not in plans["p2"]


def test_the_example_never_asks_for_a_backup(app):
    open_with(app, p1=plan(created=days_ago(60)))
    expect(app.locator(NOTE)).to_be_visible()
    app.goto(app.url.split("#")[0] + "#beispiel")
    expect(app.locator("#sandbox")).to_be_visible()
    expect(app.locator(NOTE)).to_be_hidden()
