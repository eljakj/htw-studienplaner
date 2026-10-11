"""Import of a plan from a JSON file: validation and preview before anything changes (PRD A7b)."""
import json

import pytest
from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"

BLOCKED = ("Object.defineProperty(window, 'localStorage', "
           "{get() { throw new DOMException('denied', 'SecurityError'); }});")


def set_status(page, cell_id, status):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="%s"]' % status)


def set_passed(page, cell_id):
    set_status(page, cell_id, "ok")


def raw(page):
    return page.evaluate("key => localStorage.getItem(key)", KEY)


def stored(page):
    value = raw(page)
    return None if value is None else json.loads(value)


def export(page):
    with page.expect_download() as info:
        page.click("#export")
    with open(info.value.path(), encoding="utf-8") as f:
        return f.read()


def choose(page, content, name="plan.json"):
    """Pick a file in the file dialog (str or bytes)."""
    buffer = content.encode("utf-8") if isinstance(content, str) else content
    page.set_input_files("#importFile", {"name": name, "mimeType": "application/json", "buffer": buffer})


def v2(m=None, names=None, start=None, name="Importiert", **extra):
    data = {"app": "htw-studienplaner", "v": 2, "exportedAt": "2026-10-11T18:05:00.000Z",
            "catalog": "LSF WiSe 2026/27",
            "profile": {"name": name, "start": start, "m": m or {}, "names": names or {}}}
    data.update(extra)
    return json.dumps(data)


def passed(sid):
    return {sid: {"s": "ok", "n": "", "mod": None}}


def lp(page):
    return page.locator("#lpnow")


def cells(page):
    return page.locator(".cell").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))")


def preview_title(page):
    return page.locator("#importTitle")


def lost_items(page):
    return page.locator("#importLost li").all_inner_texts()


# --- export in one browser, import in another (PRD success criterion) -------------------------

def test_export_then_import_in_another_browser_gives_the_identical_view(app, new_context, base_url):
    app.select_option("#startTerm", "SoSe")
    app.fill("#startYear", "2025")
    app.press("#startYear", "Tab")
    set_passed(app, "B31")
    set_status(app, "B32", "run")
    set_status(app, "B33", "retake")
    set_status(app, "B34", "nospot")
    app.click('.cell[data-id="B35"]')
    app.fill("#noteIn", "2. Versuch")
    app.click('.cell[data-id="WP1"]')
    app.select_option("#modSel", "B310")
    app.click('#opts .opt[data-s="ok"]')
    app.click('.cell[data-id="B12"]')
    app.fill("#nameIn", "Mein Wahlfach")
    text = export(app)

    other = new_context().new_page()
    other.goto(base_url + "/")
    choose(other, text)
    expect(other.locator("#importApply")).to_be_visible()
    other.click("#importApply")

    assert len(cells(app)) == 34
    assert cells(other) == cells(app), "label, LP, status and note of all 34 slots are identical"
    expect(lp(other)).to_have_text(lp(app).inner_text())
    expect(other.locator("#startTerm")).to_have_value("SoSe")
    expect(other.locator("#startYear")).to_have_value("2025")
    assert json.loads(export(other))["profile"] == json.loads(text)["profile"], "a second export is identical"
    assert stored(other)["profiles"]["p1"]["m"] == stored(app)["profiles"]["p1"]["m"]


# --- preview ----------------------------------------------------------------------------------------

def test_preview_names_the_passed_credit_points_and_changes_nothing(app):
    choose(app, v2(m={**passed("B31"), **passed("B32")}, start={"term": "WiSe", "year": 2025}, name="Jads Plan"))
    expect(preview_title(app)).to_have_text("11 LP bestanden – übernehmen?")
    info = app.locator("#importInfo").inner_text()
    assert "Name: Jads Plan" in info
    assert "Studienbeginn: WiSe 2025/26" in info
    assert "Katalogstand der Datei: LSF WiSe 2026/27" in info
    assert "Exportiert am:" in info
    assert "(diese Seite" not in info, "same catalog version: no hint"
    expect(app.locator("#importLost")).to_be_hidden()
    expect(lp(app)).to_have_text("0")                 # nothing is applied yet
    assert raw(app) is None, "choosing a file writes nothing"


def test_preview_points_out_a_different_catalog_version(app):
    choose(app, v2(catalog="LSF SoSe 2025"))
    expect(app.locator("#importInfo")).to_contain_text("Katalogstand der Datei: LSF SoSe 2025 (diese Seite: LSF WiSe 2026/27)")


def test_cancel_changes_nothing(app):
    set_passed(app, "B31")
    before = raw(app)
    choose(app, v2(m=passed("B32")))
    expect(preview_title(app)).to_have_text("5 LP bestanden – übernehmen?")
    app.click("#importCancel")
    expect(app.locator("#importBox")).to_be_hidden()
    expect(lp(app)).to_have_text("6")
    assert raw(app) == before


def test_apply_replaces_the_plan_and_saves_it(app):
    set_passed(app, "B31")
    choose(app, v2(m=passed("B32"), start={"term": "SoSe", "year": 2025}, name="Neuer Name",
                   names={"B11": "Mathe 1"}))
    app.click("#importApply")
    expect(app.locator("#importBox")).to_be_hidden()
    expect(lp(app)).to_have_text("5")                 # B31 is gone, B32 is in
    expect(app.locator('.cell[data-id="B11"] .nm')).to_have_text("Mathe 1")
    expect(app.locator("#startTerm")).to_have_value("SoSe")
    profile = stored(app)["profiles"]["p1"]
    assert profile["name"] == "Neuer Name"
    assert profile["start"] == {"term": "SoSe", "year": 2025}
    assert list(profile["m"]) == ["B32"]
    assert profile["names"] == {"B11": "Mathe 1"}
    assert stored(app)["active"] == "p1" and list(stored(app)["profiles"]) == ["p1"]


def test_replacing_a_plan_warns_with_its_credit_points(app):
    set_passed(app, "B31")
    choose(app, v2(m=passed("B32")))
    expect(app.locator("#importWarn")).to_be_visible()
    expect(app.locator("#importWarn")).to_have_text("Dein aktueller Plan (6 LP bestanden) wird ersetzt. Tipp: Exportiere ihn vorher, oder lege die Datei als neuen Plan an.")


def test_no_warning_when_there_is_nothing_to_replace(app):
    choose(app, v2(m=passed("B32")))
    expect(preview_title(app)).to_be_visible()
    expect(app.locator("#importWarn")).to_be_hidden()


def test_a_plan_with_only_a_start_is_not_empty(app):
    app.select_option("#startTerm", "SoSe")
    app.fill("#startYear", "2025")
    app.press("#startYear", "Tab")
    choose(app, v2())
    expect(app.locator("#importWarn")).to_be_visible()


def test_empty_plan_file_is_a_valid_import(app):
    set_passed(app, "B31")
    choose(app, v2())
    expect(preview_title(app)).to_have_text("0 LP bestanden – übernehmen?")
    app.click("#importApply")
    expect(lp(app)).to_have_text("0")


def test_the_same_file_can_be_chosen_twice(app):
    text = v2(m=passed("B32"))
    choose(app, text)
    app.click("#importCancel")
    choose(app, text)
    expect(preview_title(app)).to_have_text("5 LP bestanden – übernehmen?")


# --- invalid files ----------------------------------------------------------------------------------

ERRORS = {
    "not json": ("{not json", "Das ist keine gültige JSON-Datei."),
    "empty file": ("", "Das ist keine gültige JSON-Datei."),
    "array": ("[1, 2]", "kein Plan gefunden"),
    "no plan": ('{"hello": "world"}', "kein Plan gefunden"),
    "m is a list": ('{"m": []}', "kein Plan gefunden"),
    "profile missing": ('{"app": "htw-studienplaner", "v": 2}', "kein Plan gefunden"),
    "other app": (v2(app="other"), "Die Datei stammt nicht von dieser Seite."),
    "raw storage value": ('{"v": 2, "active": "p1", "profiles": {"p1": {"m": {}}}}', "nicht von dieser Seite"),
    "unknown version": (v2(v=3), "Unbekannte Version (3). Diese Seite kennt nur Version 2."),
    "version as text": (v2(v="2"), "Unbekannte Version (2)"),
}


@pytest.mark.parametrize("content, message", ERRORS.values(), ids=ERRORS.keys())
def test_invalid_file_changes_nothing_and_names_the_error(app, content, message):
    set_passed(app, "B31")
    before = raw(app)
    choose(app, content)
    expect(app.locator("#importMsg")).to_be_visible()
    expect(app.locator("#importMsg")).to_contain_text(message)
    expect(app.locator("#importMsg")).to_have_attribute("role", "alert")
    expect(app.locator("#importApply")).to_be_hidden()
    expect(app.locator("#importPreview")).to_be_hidden()
    expect(lp(app)).to_have_text("6")
    assert raw(app) == before
    app.click("#importCancel")
    expect(app.locator("#importBox")).to_be_hidden()


def test_file_larger_than_1_mb_is_rejected_before_reading(app):
    choose(app, b"x" * (1024 * 1024 + 1))
    expect(app.locator("#importMsg")).to_have_text("Die Datei ist größer als 1 MB.")
    assert raw(app) is None


def test_file_of_exactly_1_mb_is_still_read(app):
    padding = " " * (1024 * 1024 - len(v2()))
    choose(app, v2() + padding)
    expect(preview_title(app)).to_have_text("0 LP bestanden – übernehmen?")


def test_a_valid_file_after_an_error_works(app):
    choose(app, "{nope")
    expect(app.locator("#importMsg")).to_be_visible()
    choose(app, v2(m=passed("B32")))
    expect(preview_title(app)).to_be_visible()
    expect(app.locator("#importMsg")).to_be_hidden()
    expect(app.locator("#importBox")).not_to_have_class("err")


# --- validation with the same rules as loading -----------------------------------------------------

def tampered():
    return v2(
        m={
            "B31": {"s": "ok", "n": "<img id=pwn src=x onerror=alert(1)> " + "long " * 10, "mod": None},
            "NOPE": {"s": "ok", "n": ""},
            "toString": {"s": "ok", "n": ""},
            "__proto__": {"s": "ok", "n": ""},
            "<i id=pwn3>": {"s": "ok", "n": ""},
            "B33": {"s": "bogus", "n": ""},
            "B34": {"s": ["ok"], "n": ""},
            "WP1": {"s": "ok", "n": "", "mod": "B999"},
            "WP2": {"s": "ok", "n": "", "mod": "toString"},
            "B32": {"s": "ok", "n": ""},
        },
        names={"B11": "<b id=pwn2>x</b>", "NOPE": "x", "WP1": "not a fixed slot"},
        start={"term": "Spring", "year": "x"},
        name="<u id=pwn4>Name</u> " + "n" * 80,
    )


def test_unknown_and_invalid_values_are_listed_and_not_applied(app):
    choose(app, tampered())
    # B31 6 + B32 5 + WP1 5 + WP2 5: the status counts, like in the plan itself (the invalid module is dropped)
    expect(preview_title(app)).to_have_text("21 LP bestanden – übernehmen?")
    lost = lost_items(app)
    assert any(t.startswith("Unbekannte Plätze verworfen (4)") for t in lost), lost
    assert any(t.startswith("Ungültiger Status verworfen (2): B33, B34") for t in lost), lost
    assert any(t.startswith("Ungültiges Modul verworfen (2): WP1, WP2") for t in lost), lost
    assert any(t.startswith("Ungültige Namen verworfen (2)") for t in lost), lost
    assert any(t.startswith("Notizen auf 28 Zeichen gekürzt (1)") for t in lost), lost
    assert "Studienbeginn ungültig, wird nicht übernommen" in lost
    assert app.locator("#pwn, #pwn2, #pwn3, #pwn4").count() == 0, "text from the file is never HTML"
    expect(app.locator("#importLost")).to_contain_text("<i id=pwn3>")   # shown as text


def test_applied_plan_is_the_cleaned_one(app):
    choose(app, tampered())
    app.click("#importApply")
    assert app.locator("#pwn, #pwn2, #pwn3, #pwn4").count() == 0
    profile = stored(app)["profiles"]["p1"]
    assert sorted(profile["m"]) == ["B31", "B32", "WP1", "WP2"]
    assert len(profile["m"]["B31"]["n"]) == 28
    assert profile["m"]["WP1"]["mod"] is None and profile["m"]["WP2"]["mod"] is None
    assert profile["names"] == {"B11": "<b id=pwn2>x</b>"}, "a valid slot keeps its name, as plain text"
    assert profile["start"] is None
    assert len(profile["name"]) == 40 and profile["name"].startswith("<u id=pwn4>")   # cut, never HTML
    app.click('.cell[data-id="B31"]')
    expect(app.locator("#noteIn")).to_have_value(profile["m"]["B31"]["n"])


def test_long_list_of_unknown_slots_is_shortened(app):
    m = {"X%d" % i: {"s": "ok", "n": ""} for i in range(40)}
    m["Y" * 300] = {"s": "ok", "n": ""}
    choose(app, v2(m=m))
    item = lost_items(app)[0]
    assert item.startswith("Unbekannte Plätze verworfen (41): X0, X1, X2, X3, X4 …")
    assert len(item) < 120


def test_entries_equal_to_the_catalog_are_not_stored(app):
    choose(app, v2(m={"B31": {"s": "plan", "n": "noch nicht angemeldet", "mod": None}, "B32": {"s": "ok", "n": ""}}))
    app.click("#importApply")
    assert list(stored(app)["profiles"]["p1"]["m"]) == ["B32"]


def test_v1_file_is_migrated(app):
    v1 = json.dumps({"rev": 3, "m": {"B31": {"s": "ok", "n": "alt"}}, "names": {"B11": "Alt-Mathe"}})
    choose(app, v1, name="studienverlauf-ai-v1.json")
    expect(preview_title(app)).to_have_text("6 LP bestanden – übernehmen?")
    expect(app.locator("#importInfo")).to_contain_text("Alte Datei (Version 1)")
    expect(app.locator("#importInfo")).to_contain_text("Studienbeginn: keiner")
    app.click("#importApply")
    profile = stored(app)["profiles"]["p1"]
    assert profile["name"] == "Mein Plan" and profile["start"] is None
    assert profile["m"]["B31"] == {"s": "ok", "n": "alt", "mod": None}
    assert profile["names"] == {"B11": "Alt-Mathe"}


# --- entry points and special cases ---------------------------------------------------------------------

def test_first_visit_card_offers_the_import(app):
    expect(app.locator("#welcome")).to_be_visible()
    expect(app.locator("#wImport")).to_have_text("Plan importieren")
    with app.expect_file_chooser() as chooser:
        app.click("#wImport")
    chooser.value.set_files({"name": "plan.json", "mimeType": "application/json",
                             "buffer": v2(m=passed("B31")).encode("utf-8")})
    expect(preview_title(app)).to_have_text("6 LP bestanden – übernehmen?")
    expect(app.locator("#welcome")).to_be_visible()    # still the first visit until the plan is applied
    assert raw(app) is None
    app.click("#importApply")
    expect(app.locator("#welcome")).to_be_hidden()
    expect(lp(app)).to_have_text("6")
    assert stored(app)["profiles"]["p1"]["m"]["B31"]["s"] == "ok"


def test_cancelled_import_keeps_the_first_visit_card(app):
    choose(app, v2(m=passed("B31")))
    app.click("#importCancel")
    expect(app.locator("#welcome")).to_be_visible()
    assert raw(app) is None


def test_tools_button_opens_the_file_dialog(app):
    with app.expect_file_chooser():
        app.click("#importBtn")


def test_import_is_not_possible_in_the_example(app):
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    expect(app.locator("#importBtn")).to_be_disabled()
    expect(app.locator("#importBtn")).to_have_attribute("title", "Im Beispiel kann nichts importiert werden")
    app.click("#sandboxLeave")
    expect(app.locator("#importBtn")).to_be_enabled()


def test_file_chosen_in_the_example_is_ignored(app):
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    choose(app, v2(m=passed("B31")))
    app.wait_for_timeout(300)
    expect(app.locator("#importBox")).to_be_hidden()
    assert raw(app) is None


def test_open_preview_is_closed_when_the_example_starts(app):
    choose(app, v2(m=passed("B31")))
    expect(app.locator("#importBox")).to_be_visible()
    app.click("#exampleLink a")
    expect(app.locator("#importBox")).to_be_hidden()
    app.click("#sandboxLeave")
    expect(app.locator("#importBox")).to_be_hidden()
    expect(lp(app)).to_have_text("0")


def test_apply_resets_undo_and_closes_the_panel(app):
    set_passed(app, "B31")
    app.click('.cell[data-id="B32"]')
    expect(app.locator("#panel")).to_be_visible()
    choose(app, v2(m=passed("B33")))
    app.click("#importApply")
    expect(app.locator("#panel")).to_be_hidden()
    expect(app.locator("#undo")).to_be_disabled()
    expect(app.locator("#redo")).to_be_disabled()
    expect(lp(app)).to_have_text("5")


def test_import_works_with_blocked_storage(app):
    app.add_init_script(BLOCKED)
    app.reload()
    choose(app, v2(m=passed("B31")))
    app.click("#importApply")
    expect(lp(app)).to_have_text("6")
    expect(app.locator("#welcome")).to_be_hidden()
    expect(app.locator("#nostore")).to_be_visible()


def test_other_tab_receives_the_imported_plan(app, base_url):
    second = app.context.new_page()
    second.goto(base_url + "/")
    choose(app, v2(m=passed("B31")))
    app.click("#importApply")
    expect(lp(second)).to_have_text("6")


def test_import_makes_no_request_to_a_server(app):
    requests = []
    app.on("request", lambda r: requests.append(r.url))
    choose(app, v2(m=passed("B31")))
    app.click("#importApply")
    assert [u for u in requests if not u.startswith(("blob:", "data:"))] == []
