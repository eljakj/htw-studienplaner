"""Export of the plan as a JSON file (PRD A7a). The browser clock is fixed to 11 Oct 2026, midday."""
import json
import re
from datetime import datetime

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
NOW = datetime(2026, 10, 11, 12, 0, 0)

BLOCKED = ("Object.defineProperty(window, 'localStorage', "
           "{get() { throw new DOMException('denied', 'SecurityError'); }});")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def export(page):
    """Click "Exportieren" and return (file name, parsed content)."""
    with page.expect_download() as info:
        page.click("#export")
    download = info.value
    with open(download.path(), encoding="utf-8") as f:
        text = f.read()
    return download.suggested_filename, json.loads(text), text


def start_at_fixed_time(page):
    page.clock.set_fixed_time(NOW)
    page.reload()


def stored(page):
    raw = page.evaluate("key => localStorage.getItem(key)", KEY)
    return None if raw is None else json.loads(raw)


# --- file name and content ----------------------------------------------------------

def test_export_downloads_a_json_file_with_name_and_date(app):
    start_at_fixed_time(app)
    name, data, _ = export(app)
    assert name == "studienverlauf-mein-plan-2026-10-11.json"
    assert re.fullmatch(r"studienverlauf-[a-z0-9-]+-\d{4}-\d{2}-\d{2}\.json", name)


def test_content_has_profile_catalog_version_and_time(app):
    start_at_fixed_time(app)
    app.select_option("#startTerm", "SoSe")
    app.fill("#startYear", "2025")
    app.press("#startYear", "Tab")
    set_passed(app, "B31")
    app.fill("#noteIn", "Note")
    _, data, _ = export(app)
    assert list(data) == ["app", "v", "exportedAt", "catalog", "profile"]
    assert data["app"] == "htw-studienplaner"
    assert data["v"] == 2
    assert data["catalog"] == "LSF WiSe 2026/27"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", data["exportedAt"])
    assert data["exportedAt"].startswith("2026-10-11")
    profile = data["profile"]
    assert profile["name"] == "Mein Plan"
    assert profile["start"] == {"term": "SoSe", "year": 2025}
    assert profile["m"]["B31"] == {"s": "ok", "n": "Note", "mod": None}
    assert list(profile["m"]) == ["B31"], "only deviations from the catalog, like in the store"
    assert "rev" not in profile and "id" not in profile


def test_content_equals_the_stored_profile(app):
    set_passed(app, "B31")
    set_passed(app, "B32")
    _, data, _ = export(app)
    store = stored(app)["profiles"]["p1"]
    assert data["profile"]["m"] == store["m"]
    assert data["profile"]["names"] == store["names"]
    assert data["profile"]["start"] == store["start"]


def test_chosen_modules_and_renamed_slots_are_exported(app):
    app.click('.cell[data-id="WP1"]')
    app.select_option("#modSel", "B310")
    app.click('.cell[data-id="B31"]')
    app.fill("#nameIn", "Prog 3")
    _, data, _ = export(app)
    assert data["profile"]["m"]["WP1"]["mod"] == "B310"
    assert data["profile"]["names"] == {"B31": "Prog 3"}


def test_file_is_readable_text_with_a_final_newline(app):
    _, data, text = export(app)
    assert text.endswith("}\n")
    assert '\n  "app": "htw-studienplaner"' in text, "indented, so people can read and diff it"


def test_name_in_the_file_name_is_made_safe(app):
    app.evaluate("""key => localStorage.setItem(key, JSON.stringify({v: 2, active: 'p1', profiles: {
        p1: {name: 'Jäd: Über/Plan?', start: null, rev: 1, m: {}, names: {}}}}))""", KEY)
    start_at_fixed_time(app)
    name, data, _ = export(app)
    assert name == "studienverlauf-jaed-ueber-plan-2026-10-11.json"
    assert data["profile"]["name"] == "Jäd: Über/Plan?", "the name inside the file stays as it is"


# --- no side effects ---------------------------------------------------------------------

def test_export_writes_nothing_to_the_storage(app):
    export(app)
    assert stored(app) is None
    assert app.evaluate("localStorage.length") == 0


def test_export_only_adds_the_time_of_the_last_export_to_a_saved_plan(app):
    set_passed(app, "B31")
    before = stored(app)["profiles"]["p1"]
    assert "lastExport" not in before
    export(app)
    export(app)
    after = stored(app)["profiles"]["p1"]
    assert after["lastExport"] > 0
    assert {k: v for k, v in after.items() if k != "lastExport"} == before, "the plan itself stays as it was"


def test_export_does_not_count_as_choosing_a_plan(app):
    start_at_fixed_time(app)
    export(app)
    expect(app.locator("#welcome")).to_be_visible()


def test_export_makes_no_request_to_a_server(app, base_url):
    requests = []
    app.on("request", lambda r: requests.append(r.url))
    export(app)
    assert [u for u in requests if not u.startswith(("blob:", "data:"))] == []


# --- special cases ---------------------------------------------------------------------------

def test_empty_plan_can_be_exported(app):
    _, data, _ = export(app)
    assert data["profile"]["m"] == {}
    assert data["profile"]["start"] is None


def test_export_works_with_blocked_storage(app):
    app.add_init_script(BLOCKED)
    app.reload()
    set_passed(app, "B31")                      # only in memory
    _, data, _ = export(app)
    assert data["profile"]["m"]["B31"]["s"] == "ok"


def test_export_is_not_possible_in_the_example_and_works_again_afterwards(app):
    set_passed(app, "B31")
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    expect(app.locator("#export")).to_be_disabled()
    expect(app.locator("#export")).to_have_attribute("title", "Im Beispiel gibt es nichts zu sichern")
    app.click("#sandboxLeave")
    expect(app.locator("#export")).to_be_enabled()
    _, data, _ = export(app)
    assert list(data["profile"]["m"]) == ["B31"], "the own plan, not the example"


def test_example_data_never_ends_up_in_an_export(app):
    """Even if the disabled button is forced, the function itself refuses to export the example."""
    downloads = []
    app.on("download", lambda d: downloads.append(d))
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    app.evaluate("() => { const b = document.querySelector('#export'); b.disabled = false; b.click(); }")
    app.wait_for_timeout(500)
    assert downloads == []
