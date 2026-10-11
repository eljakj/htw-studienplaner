"""Basic behaviour of the current app, ported from the old Node test."""
from playwright.sync_api import expect


def lp(page):
    return page.locator("#lpnow")


def test_elective_module_can_be_chosen(app):
    app.click('.cell[data-id="WP1"]')
    app.select_option("#modSel", "B111")
    app.click('#opts .opt[data-s="ok"]')
    expect(lp(app)).to_have_text("5")


def test_undo_and_redo(app):
    app.click('.cell[data-id="B31"]')
    app.click('#opts .opt[data-s="ok"]')
    expect(lp(app)).to_have_text("6")
    app.click("#undo")
    expect(lp(app)).to_have_text("0")
    app.click("#redo")
    expect(lp(app)).to_have_text("6")


def test_semester_start_clears_everything(app):
    app.click('.cell[data-id="B31"]')
    app.click('#opts .opt[data-s="ok"]')
    app.click("#reset")
    expect(lp(app)).to_have_text("0")
    app.reload()
    expect(lp(app)).to_have_text("0")


def test_theme_switch_sets_attribute(app):
    html = app.locator("html")
    app.click('.theme button[data-t="light"]')
    expect(html).to_have_attribute("data-theme", "light")
    app.click('.theme button[data-t="dark"]')
    expect(html).to_have_attribute("data-theme", "dark")
