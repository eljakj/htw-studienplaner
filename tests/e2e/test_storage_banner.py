"""Notice when the browser cannot store data (PRD A6)."""
import pytest
from playwright.sync_api import expect

BANNER = "#nostore"

BLOCKED = {
    # reading window.localStorage throws, as with blocked site data
    "access throws": "Object.defineProperty(window, 'localStorage', "
                     "{get() { throw new DOMException('denied', 'SecurityError'); }});",
    # writing throws, as in some private windows or with a full quota
    "write throws": "Storage.prototype.setItem = function () "
                    "{ throw new DOMException('full', 'QuotaExceededError'); };",
}


def lp(page):
    return page.locator("#lpnow")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def test_no_banner_when_storage_works(app):
    expect(app.locator(BANNER)).to_be_hidden()
    expect(app.locator("#saveerr")).to_be_hidden()
    assert app.evaluate("localStorage.length") == 0, "the test key must be removed again"


@pytest.mark.parametrize("script", BLOCKED.values(), ids=BLOCKED.keys())
def test_banner_is_visible_right_after_load(app, script):
    app.add_init_script(script)
    app.reload()
    expect(app.locator(BANNER)).to_be_visible()     # before any change
    expect(app.locator(BANNER)).to_contain_text("nicht gespeichert")
    expect(app.locator("#saveerr")).to_be_hidden()


@pytest.mark.parametrize("script", BLOCKED.values(), ids=BLOCKED.keys())
def test_page_stays_fully_usable(app, script):
    app.add_init_script(script)
    app.reload()
    expect(app.locator(".cell")).to_have_count(34)
    set_passed(app, "B31")
    expect(lp(app)).to_have_text("6")
    app.click("#undo")
    expect(lp(app)).to_have_text("0")
    app.click("#redo")
    expect(lp(app)).to_have_text("6")
    expect(app.locator(BANNER)).to_be_visible()


def test_later_write_failure_shows_the_retry_notice_instead(app):
    expect(app.locator(BANNER)).to_be_hidden()      # storage worked on load
    app.evaluate("(() => { Storage.prototype.setItem = function () "
                 "{ throw new DOMException('full', 'QuotaExceededError'); }; })()")
    set_passed(app, "B31")
    expect(app.locator("#saveerr")).to_be_visible()
    expect(app.locator("#saveerr")).to_contain_text("Speichern fehlgeschlagen")
    expect(app.locator(BANNER)).to_be_hidden()
    expect(lp(app)).to_have_text("6")
