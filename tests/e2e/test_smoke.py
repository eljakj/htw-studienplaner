"""Smoke tests: the page loads, shows the catalog and keeps its state."""
import re

from playwright.sync_api import expect

CELLS = 34  # all slots of the study plan in the current catalog


def lp(page):
    return page.locator("#lpnow")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def test_page_loads_with_title(app):
    expect(app).to_have_title(re.compile("Studienverlauf"))
    expect(app.locator("h1")).to_be_visible()


def test_starts_neutral(app):
    expect(lp(app)).to_have_text("0")
    expect(app.locator(".cell")).to_have_count(CELLS)


def test_passed_module_counts_credits(app):
    set_passed(app, "B31")  # Programmierung 3 = 6 LP
    expect(lp(app)).to_have_text("6")


def test_state_survives_reload(app):
    set_passed(app, "B31")
    app.reload()
    expect(lp(app)).to_have_text("6")


def test_contexts_do_not_share_state(app, new_context, base_url):
    set_passed(app, "B31")
    expect(lp(app)).to_have_text("6")

    other = new_context().new_page()
    other.goto(base_url + "/")
    expect(lp(other)).to_have_text("0")


def test_sets_no_cookies(app):
    set_passed(app, "B31")
    assert app.context.cookies() == []
