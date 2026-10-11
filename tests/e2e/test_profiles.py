"""Local profiles with a switcher, name and subtitle, deleting with confirmation (PRD A8, A9, A12)."""
import json

from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"
SUBTITLE = "Angewandte Informatik (B), HTW Berlin"

BLOCKED = ("Object.defineProperty(window, 'localStorage', "
           "{get() { throw new DOMException('denied', 'SecurityError'); }});")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')
    page.click("#done")


def raw(page, key=KEY):
    return page.evaluate("key => localStorage.getItem(key)", key)


def store(page):
    value = raw(page)
    return None if value is None else json.loads(value)


def put(page, value, key=KEY):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [key, value if isinstance(value, str) else json.dumps(value)])


def plan(m=None, name="Mein Plan", **extra):
    p = {"name": name, "start": None, "rev": 1, "m": m or {}, "names": {}}
    p.update(extra)
    return p


def stored_plans(**profiles):
    return {"v": 2, "active": sorted(profiles)[0], "profiles": profiles}


def passed(sid):
    return {sid: {"s": "ok", "n": "", "mod": None}}


def lp(page):
    return page.locator("#lpnow")


def option_names(page):
    return page.locator("#profSel option").all_inner_texts()


def current(page):
    return page.locator("#profSel").input_value()


def two_plans(page):
    """p1 with B31 passed (6 LP), p2 with B32 passed (5 LP); p1 is open."""
    put(page, stored_plans(p1=plan(passed("B31"), "Erster"), p2=plan(passed("B32"), "Zweiter")))
    page.reload()
    expect(lp(page)).to_have_text("6")


# --- the bar -------------------------------------------------------------------------------------

def test_bar_is_hidden_on_the_first_visit_and_shown_with_a_plan(app):
    expect(app.locator("#profbar")).to_be_hidden()
    set_passed(app, "B31")
    expect(app.locator("#profbar")).to_be_visible()
    assert option_names(app) == ["Mein Plan"]
    assert current(app) == "p1"


def test_bar_is_hidden_in_the_example(app):
    set_passed(app, "B31")
    app.click("#exampleLink a")
    expect(app.locator("#sandbox")).to_be_visible()
    expect(app.locator("#profbar")).to_be_hidden()
    app.click("#sandboxLeave")
    expect(app.locator("#profbar")).to_be_visible()


def test_switcher_lists_the_names_of_all_plans(app):
    two_plans(app)
    assert option_names(app) == ["Erster", "Zweiter"]
    assert current(app) == "p1"


# --- several plans in one browser ------------------------------------------------------------------

def test_new_plan_is_empty_active_and_stored(app):
    set_passed(app, "B31")
    app.click("#profNew")
    expect(lp(app)).to_have_text("0")
    assert option_names(app) == ["Mein Plan", "Plan 2"]
    assert current(app) == "p2"
    s = store(app)
    assert sorted(s["profiles"]) == ["p1", "p2"] and s["active"] == "p2"
    assert s["profiles"]["p1"]["m"]["B31"]["s"] == "ok"
    assert s["profiles"]["p2"]["m"] == {} and s["profiles"]["p2"]["name"] == "Plan 2"


def test_new_plan_opens_the_name_field_with_the_focus(app):
    set_passed(app, "B31")
    app.click("#profNew")
    expect(app.locator("#profEditBox")).to_be_visible()
    expect(app.locator("#profName")).to_be_focused()
    expect(app.locator("#profName")).to_have_value("Plan 2")


def test_a_change_in_plan_a_leaves_plan_b_unchanged(app):
    two_plans(app)
    before_b = store(app)["profiles"]["p2"]
    set_passed(app, "B33")
    expect(lp(app)).to_have_text("11")
    assert store(app)["profiles"]["p2"] == before_b
    app.select_option("#profSel", "p2")
    expect(lp(app)).to_have_text("5")
    assert app.locator('.cell[data-id="B33"].s-ok').count() == 0
    set_passed(app, "B34")
    app.select_option("#profSel", "p1")
    expect(lp(app)).to_have_text("11")
    assert sorted(store(app)["profiles"]["p1"]["m"]) == ["B31", "B33"]
    assert sorted(store(app)["profiles"]["p2"]["m"]) == ["B32", "B34"]


def test_each_plan_has_its_own_study_start(app):
    two_plans(app)
    app.select_option("#startTerm", "SoSe")
    app.fill("#startYear", "2025")
    app.press("#startYear", "Tab")
    app.select_option("#profSel", "p2")
    expect(app.locator("#startTerm")).to_have_value("")
    expect(app.locator("#startYear")).to_have_value("")
    app.select_option("#profSel", "p1")
    expect(app.locator("#startYear")).to_have_value("2025")


def test_the_last_used_plan_opens_after_a_reload(app):
    two_plans(app)
    app.select_option("#profSel", "p2")
    app.reload()
    assert current(app) == "p2"
    expect(lp(app)).to_have_text("5")


def test_switching_resets_undo_and_closes_the_panel(app):
    two_plans(app)
    set_passed(app, "B33")
    expect(app.locator("#undo")).to_be_enabled()
    app.click('.cell[data-id="B34"]')
    expect(app.locator("#panel")).to_be_visible()
    app.select_option("#profSel", "p2")
    expect(app.locator("#panel")).to_be_hidden()
    expect(app.locator("#undo")).to_be_disabled()


def test_each_tab_keeps_its_own_plan(app, base_url):
    two_plans(app)
    second = app.context.new_page()
    second.goto(base_url + "/")
    second.select_option("#profSel", "p2")
    expect(lp(second)).to_have_text("5")
    app.wait_for_timeout(300)
    assert current(app) == "p1" and lp(app).inner_text() == "6", "the first tab did not follow"
    set_passed(second, "B34")
    app.wait_for_timeout(300)
    assert current(app) == "p1"
    set_passed(app, "B33")
    assert sorted(store(app)["profiles"]["p1"]["m"]) == ["B31", "B33"]
    assert sorted(store(app)["profiles"]["p2"]["m"]) == ["B32", "B34"], "no mixing between the two plans"


def test_at_most_20_plans(app):
    put(app, stored_plans(**{"p%d" % i: plan(name="Plan %d" % i) for i in range(1, 21)}))
    app.reload()
    expect(app.locator("#profNew")).to_be_disabled()
    assert len(option_names(app)) == 20


def test_plans_work_with_blocked_storage(app):
    app.add_init_script(BLOCKED)
    app.reload()
    set_passed(app, "B31")
    app.click("#profNew")
    set_passed(app, "B32")
    assert option_names(app) == ["Mein Plan", "Plan 2"]
    app.select_option("#profSel", "p1")
    expect(lp(app)).to_have_text("6")
    app.select_option("#profSel", "p2")
    expect(lp(app)).to_have_text("5")


# --- name and subtitle (A12) --------------------------------------------------------------------------

def test_rename_updates_the_switcher_and_the_storage(app):
    two_plans(app)
    app.click("#profEdit")
    expect(app.locator("#profName")).to_have_value("Erster")
    app.fill("#profName", "Jads Plan")
    assert option_names(app) == ["Jads Plan", "Zweiter"]
    assert store(app)["profiles"]["p1"]["name"] == "Jads Plan"
    app.reload()
    assert option_names(app) == ["Jads Plan", "Zweiter"]


def test_an_empty_name_falls_back_and_a_long_one_is_cut(app):
    two_plans(app)
    app.click("#profEdit")
    app.fill("#profName", "   ")
    assert option_names(app)[0] == "Mein Plan"
    app.fill("#profName", "n" * 100)
    assert option_names(app)[0] == "n" * 40
    assert store(app)["profiles"]["p1"]["name"] == "n" * 40


def test_name_and_subtitle_are_shown_as_text(app):
    two_plans(app)
    app.click("#profEdit")
    app.fill("#profName", "<b id=pwn>x</b>")
    app.fill("#profSub", "<i id=pwn2>y</i>")
    assert app.locator("#pwn, #pwn2").count() == 0
    expect(app.locator("#subtitle")).to_have_text("<i id=pwn2>y</i>")
    assert option_names(app)[0] == "<b id=pwn>x</b>"


def test_default_subtitle_until_a_custom_one_is_set(app):
    two_plans(app)
    expect(app.locator("#subtitle")).to_have_text(SUBTITLE)
    assert "subtitle" not in store(app)["profiles"]["p1"]
    app.click("#profEdit")
    app.fill("#profSub", "Mein Weg")
    expect(app.locator("#subtitle")).to_have_text("Mein Weg")
    assert store(app)["profiles"]["p1"]["subtitle"] == "Mein Weg"
    app.reload()
    expect(app.locator("#subtitle")).to_have_text("Mein Weg")
    app.click("#profEdit")
    app.fill("#profSub", "")
    expect(app.locator("#subtitle")).to_have_text(SUBTITLE)
    assert "subtitle" not in store(app)["profiles"]["p1"], "an empty subtitle is not stored"


def test_subtitle_belongs_to_the_plan(app):
    two_plans(app)
    app.click("#profEdit")
    app.fill("#profSub", "Nur Plan 1")
    app.select_option("#profSel", "p2")
    expect(app.locator("#subtitle")).to_have_text(SUBTITLE)
    app.select_option("#profSel", "p1")
    expect(app.locator("#subtitle")).to_have_text("Nur Plan 1")


def test_subtitle_is_limited_to_80_characters(app):
    two_plans(app)
    app.click("#profEdit")
    app.fill("#profSub", "s" * 120)
    assert store(app)["profiles"]["p1"]["subtitle"] == "s" * 80
    expect(app.locator("#profSub")).to_have_attribute("maxlength", "80")


def test_invalid_stored_subtitle_and_name_fall_back(app):
    put(app, stored_plans(p1=plan(name=42, subtitle=["x"])))
    app.reload()
    assert option_names(app) == ["Mein Plan"]
    expect(app.locator("#subtitle")).to_have_text(SUBTITLE)


def test_name_and_subtitle_survive_export_and_import(app, new_context, base_url):
    two_plans(app)
    app.click("#profEdit")
    app.fill("#profName", "Jads Plan")
    app.fill("#profSub", "Mein Weg")
    with app.expect_download() as info:
        app.click("#export")
    assert info.value.suggested_filename.startswith("studienverlauf-jads-plan-")
    with open(info.value.path(), encoding="utf-8") as f:
        text = f.read()
    assert json.loads(text)["profile"]["subtitle"] == "Mein Weg"

    other = new_context().new_page()
    other.goto(base_url + "/")
    other.set_input_files("#importFile", {"name": "p.json", "mimeType": "application/json", "buffer": text.encode("utf-8")})
    expect(other.locator("#importInfo")).to_contain_text("Untertitel: Mein Weg")
    other.click("#importApply")
    expect(other.locator("#subtitle")).to_have_text("Mein Weg")
    assert option_names(other) == ["Jads Plan"]
    other.reload()
    expect(other.locator("#subtitle")).to_have_text("Mein Weg")


# --- export and import per plan -------------------------------------------------------------------------

def test_export_is_the_active_plan(app):
    two_plans(app)
    app.select_option("#profSel", "p2")
    with app.expect_download() as info:
        app.click("#export")
    assert info.value.suggested_filename.startswith("studienverlauf-zweiter-")
    with open(info.value.path(), encoding="utf-8") as f:
        data = json.load(f)
    assert list(data["profile"]["m"]) == ["B32"] and data["profile"]["name"] == "Zweiter"


def import_text(m, name="Importiert"):
    return json.dumps({"app": "htw-studienplaner", "v": 2, "exportedAt": "2026-10-11T18:05:00.000Z",
                       "catalog": "LSF WiSe 2026/27", "profile": {"name": name, "start": None, "m": m, "names": {}}})


def choose(page, text):
    page.set_input_files("#importFile", {"name": "p.json", "mimeType": "application/json", "buffer": text.encode("utf-8")})


def test_import_replaces_only_the_active_plan(app):
    two_plans(app)
    choose(app, import_text(passed("B33")))
    app.click("#importApply")
    expect(lp(app)).to_have_text("5")
    s = store(app)["profiles"]
    assert list(s["p1"]["m"]) == ["B33"] and s["p1"]["name"] == "Importiert"
    assert list(s["p2"]["m"]) == ["B32"] and s["p2"]["name"] == "Zweiter", "the other plan is untouched"


def test_import_as_a_new_plan_keeps_the_current_one(app):
    two_plans(app)
    choose(app, import_text(passed("B33"), "Aus Datei"))
    app.click("#importNew")
    expect(app.locator("#importBox")).to_be_hidden()
    expect(lp(app)).to_have_text("5")
    assert option_names(app) == ["Erster", "Zweiter", "Aus Datei"]
    assert current(app) == "p3"
    s = store(app)
    assert list(s["profiles"]["p1"]["m"]) == ["B31"] and list(s["profiles"]["p2"]["m"]) == ["B32"]
    assert list(s["profiles"]["p3"]["m"]) == ["B33"] and s["active"] == "p3"


def test_import_as_a_new_plan_is_not_offered_for_an_empty_plan_or_at_the_limit(app):
    choose(app, import_text(passed("B33")))
    expect(app.locator("#importApply")).to_be_visible()
    expect(app.locator("#importNew")).to_be_hidden()
    app.click("#importCancel")
    put(app, stored_plans(**{"p%d" % i: plan(passed("B31"), "Plan %d" % i) for i in range(1, 21)}))
    app.reload()
    choose(app, import_text(passed("B33")))
    expect(app.locator("#importApply")).to_be_visible()
    expect(app.locator("#importNew")).to_be_hidden()


# --- delete with confirmation, undo (A9) --------------------------------------------------------------------

def test_delete_asks_in_the_page_and_deletes_nothing_before_the_answer(app):
    two_plans(app)
    dialogs = []
    app.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    before = raw(app)
    app.click("#profDel")
    expect(app.locator("#profConfirm")).to_be_visible()
    expect(app.locator("#profConfirmText")).to_have_text("Plan „Erster“ (6 LP bestanden) wirklich löschen?")
    assert raw(app) == before, "nothing is deleted without the answer"
    assert option_names(app) == ["Erster", "Zweiter"]
    assert dialogs == [], "no window.confirm"


def test_cancel_keeps_everything(app):
    two_plans(app)
    before = raw(app)
    app.click("#profDel")
    app.click("#profConfirmNo")
    expect(app.locator("#profConfirm")).to_be_hidden()
    assert raw(app) == before
    expect(app.locator("#profUndo")).to_be_hidden()


def test_confirm_deletes_the_plan_and_opens_another(app):
    two_plans(app)
    app.click("#profDel")
    app.click("#profConfirmYes")
    expect(app.locator("#profConfirm")).to_be_hidden()
    assert option_names(app) == ["Zweiter"] and current(app) == "p2"
    expect(lp(app)).to_have_text("5")
    s = store(app)
    assert list(s["profiles"]) == ["p2"] and s["active"] == "p2"
    expect(app.locator("#profUndoText")).to_have_text("Plan „Erster“ gelöscht.")


def test_undo_brings_the_plan_back_exactly(app):
    two_plans(app)
    before = store(app)["profiles"]["p1"]
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.click("#profUndoBtn")
    expect(app.locator("#profUndo")).to_be_hidden()
    assert option_names(app) == ["Erster", "Zweiter"] and current(app) == "p1"
    expect(lp(app)).to_have_text("6")
    assert store(app)["profiles"]["p1"] == before


def test_the_undo_notice_can_be_closed_and_is_gone_after_a_reload(app):
    two_plans(app)
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.click("#profUndoClose")
    expect(app.locator("#profUndo")).to_be_hidden()
    app.click("#profDel")
    app.click("#profConfirmYes")
    expect(app.locator("#profUndo")).to_be_visible()
    app.reload()
    expect(app.locator("#profUndo")).to_be_hidden()


def test_after_deleting_the_neighbour_the_previous_plan_opens(app):
    put(app, stored_plans(p1=plan(passed("B31"), "A"), p2=plan(passed("B32"), "B"), p3=plan(passed("B33"), "C")))
    app.reload()
    app.select_option("#profSel", "p3")
    app.click("#profDel")
    app.click("#profConfirmYes")
    assert current(app) == "p2"


def test_a_freed_id_can_be_reused_and_undo_then_takes_another(app):
    two_plans(app)
    app.select_option("#profSel", "p2")
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.click("#profNew")                                  # takes the freed id p2
    assert current(app) == "p2" and option_names(app) == ["Erster", "Plan 2"]
    app.click("#profUndoBtn")                              # the deleted plan comes back under a new id
    assert option_names(app) == ["Erster", "Plan 2", "Zweiter"]
    assert current(app) == "p3"
    expect(lp(app)).to_have_text("5")
    assert list(store(app)["profiles"]["p3"]["m"]) == ["B32"]


def test_deleting_the_last_plan_returns_to_the_start_choice(app):
    set_passed(app, "B31")
    app.click("#profDel")
    app.click("#profConfirmYes")
    expect(app.locator("#welcome")).to_be_visible()
    expect(app.locator("#welcomeStart")).to_be_visible()
    expect(app.locator("#profbar")).to_be_hidden()
    expect(lp(app)).to_have_text("0")
    assert store(app) == {"v": 2, "profiles": {}}
    expect(app.locator("#profUndo")).to_be_visible()


def test_the_start_choice_stays_after_a_reload_and_the_old_v1_plan_does_not_come_back(app):
    put(app, {"rev": 3, "m": passed("B31"), "names": {}}, OLD_KEY)
    app.reload()
    expect(lp(app)).to_have_text("6")                       # migrated
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.reload()
    expect(app.locator("#welcome")).to_be_visible()
    expect(lp(app)).to_have_text("0")
    assert raw(app, OLD_KEY) is not None, "the old key is never touched"


def test_a_new_plan_can_be_started_after_deleting_the_last_one(app):
    set_passed(app, "B31")
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.click("#wOwn")
    app.click('#welcome [data-term="WiSe"]')
    app.fill("#wYear", "2026")
    app.click("#wGo")
    expect(app.locator("#welcome")).to_be_hidden()
    expect(app.locator("#profbar")).to_be_visible()
    assert list(store(app)["profiles"]) == ["p1"]
    assert store(app)["profiles"]["p1"]["start"] == {"term": "WiSe", "year": 2026}


def test_undo_after_deleting_the_last_plan_restores_it(app):
    set_passed(app, "B31")
    app.click("#profDel")
    app.click("#profConfirmYes")
    app.click("#profUndoBtn")
    expect(app.locator("#welcome")).to_be_hidden()
    expect(lp(app)).to_have_text("6")
    assert list(store(app)["profiles"]) == ["p1"]


def test_delete_works_with_blocked_storage(app):
    app.add_init_script(BLOCKED)
    app.reload()
    set_passed(app, "B31")
    app.click("#profNew")
    set_passed(app, "B32")
    app.click("#profDel")
    app.click("#profConfirmYes")
    assert option_names(app) == ["Mein Plan"]
    expect(lp(app)).to_have_text("6")
    app.click("#profUndoBtn")
    assert option_names(app) == ["Mein Plan", "Plan 2"]


def test_the_other_tab_follows_when_its_plan_was_deleted(app, base_url):
    two_plans(app)
    second = app.context.new_page()
    second.goto(base_url + "/")
    second.select_option("#profSel", "p2")
    app.select_option("#profSel", "p2")
    app.click("#profDel")
    app.click("#profConfirmYes")
    expect(second.locator("#profSel option")).to_have_count(1)
    assert current(second) == "p1"
