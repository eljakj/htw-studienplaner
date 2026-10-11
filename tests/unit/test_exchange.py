"""Unit tests for src/exchange.js: export file name and content (PRD A7a).

Like the tests for src/semester.js they run the plain JavaScript in the headless Chromium of Playwright
and pass the date in, so they do not depend on today's date or on the time zone of the machine."""
import json

import pytest

import build

playwright_sync = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def blank_page():
    with open(build.EXCHANGE_JS, encoding="utf-8") as f:
        js = f.read()
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch()
        blank = browser.new_page()
        blank.set_content("<!doctype html><title>exchange</title>")
        blank.add_script_tag(content=js)
        yield blank
        browser.close()


def file_name(page, name, year=2026, month=10, day=11):
    """exportFileName(name, <local date>); month is 1..12."""
    return page.evaluate("([n, y, m, d]) => exportFileName(n, new Date(y, m - 1, d, 12))", [name, year, month, day])


# --- file name ---------------------------------------------------------------------

@pytest.mark.parametrize("name, expected", [
    ("Mein Plan", "studienverlauf-mein-plan-2026-10-11.json"),
    ("mein-plan", "studienverlauf-mein-plan-2026-10-11.json"),
    ("Größe Übung", "studienverlauf-groesse-uebung-2026-10-11.json"),
    ("Ärger ÖL Ünder", "studienverlauf-aerger-oel-uender-2026-10-11.json"),
    ("Käse Bär ärgern", "studienverlauf-kaese-baer-aergern-2026-10-11.json"),
    ("Café Zoë", "studienverlauf-cafe-zoe-2026-10-11.json"),
    ("a/b\\c:d*e?f\"g<h>i|j", "studienverlauf-a-b-c-d-e-f-g-h-i-j-2026-10-11.json"),
    ("  --Plan 2--  ", "studienverlauf-plan-2-2026-10-11.json"),
    ("../../etc/passwd", "studienverlauf-etc-passwd-2026-10-11.json"),
    ("Plan.json", "studienverlauf-plan-json-2026-10-11.json"),
])
def test_file_name_is_made_safe(blank_page, name, expected):
    assert file_name(blank_page, name) == expected


@pytest.mark.parametrize("name", ["", "   ", "???", "日本語", None, 42])
def test_file_name_falls_back_to_plan(blank_page, name):
    expected = "studienverlauf-plan-2026-10-11.json" if name != 42 else "studienverlauf-42-2026-10-11.json"
    assert file_name(blank_page, name) == expected


def test_file_name_is_cut_at_40_characters(blank_page):
    result = file_name(blank_page, "x" * 100)
    assert result == "studienverlauf-" + "x" * 40 + "-2026-10-11.json"


def test_file_name_does_not_end_the_name_with_a_dash_after_cutting(blank_page):
    # the 40th character would be a dash: it must not stay
    name = "a" * 39 + " b"
    assert file_name(blank_page, name) == "studienverlauf-" + "a" * 39 + "-2026-10-11.json"


@pytest.mark.parametrize("args, expected", [
    ((2026, 1, 5), "2026-01-05"),
    ((2026, 12, 31), "2026-12-31"),
    ((2027, 3, 9), "2027-03-09"),
])
def test_file_name_uses_the_given_local_date(blank_page, args, expected):
    assert file_name(blank_page, "x", *args) == "studienverlauf-x-%s.json" % expected


def test_late_evening_is_still_the_same_local_day(blank_page):
    got = blank_page.evaluate("exportFileName('x', new Date(2026, 9, 11, 23, 59, 59))")
    assert got == "studienverlauf-x-2026-10-11.json"


# --- content -------------------------------------------------------------------------

PROFILE = {"id": "p1", "name": "Mein Plan", "start": {"term": "SoSe", "year": 2025}}
STATE = {"rev": 123, "m": {"B31": {"s": "ok", "n": "", "mod": None}}, "names": {"B11": "Mathe"}}


def export(page, profile=PROFILE, state=STATE, label="LSF WiSe 2026/27"):
    return page.evaluate(
        "([p, s, l]) => buildExport(p, s, l, new Date(Date.UTC(2026, 9, 11, 18, 5, 0)))", [profile, state, label]
    )


def test_export_has_the_documented_structure(blank_page):
    assert export(blank_page) == {
        "app": "htw-studienplaner",
        "v": 2,
        "exportedAt": "2026-10-11T18:05:00.000Z",
        "catalog": "LSF WiSe 2026/27",
        "profile": {
            "name": "Mein Plan",
            "start": {"term": "SoSe", "year": 2025},
            "m": {"B31": {"s": "ok", "n": "", "mod": None}},
            "names": {"B11": "Mathe"},
        },
    }


def test_export_key_order_is_stable(blank_page):
    text = blank_page.evaluate(
        "([p, s]) => JSON.stringify(buildExport(p, s, 'x', new Date(0)))", [PROFILE, STATE]
    )
    assert list(json.loads(text)) == ["app", "v", "exportedAt", "catalog", "profile"]
    assert list(json.loads(text)["profile"]) == ["name", "start", "m", "names"]


def test_export_leaves_out_the_local_id_and_revision(blank_page):
    data = export(blank_page)
    assert "id" not in data["profile"]
    assert "rev" not in data["profile"]
    assert "rev" not in data


def test_export_without_a_start_keeps_null(blank_page):
    data = export(blank_page, profile={"id": "p1", "name": "X", "start": None}, state={"m": {}, "names": {}})
    assert data["profile"]["start"] is None
    assert data["profile"]["m"] == {}


def test_export_is_a_copy(blank_page):
    changed = blank_page.evaluate("""() => {
        const state = {m: {B31: {s: 'ok', n: '', mod: null}}, names: {}};
        const data = buildExport({name: 'X', start: null}, state, 'c', new Date(0));
        data.profile.m.B31.s = 'run';
        return state.m.B31.s;
    }""")
    assert changed == "ok"


def test_export_time_is_utc(blank_page):
    data = export(blank_page)
    assert data["exportedAt"].endswith("Z")


# --- import: shape of the file (PRD A7b) ---------------------------------------------------

def parse(page, text):
    return page.evaluate("text => parseImport(text)", text)


def v2_file(**changes):
    data = {
        "app": "htw-studienplaner", "v": 2, "exportedAt": "2026-10-11T18:05:00.000Z", "catalog": "LSF WiSe 2026/27",
        "profile": {"name": "Mein Plan", "start": {"term": "SoSe", "year": 2025},
                    "m": {"B31": {"s": "ok", "n": "", "mod": None}}, "names": {"B11": "Mathe"}},
    }
    data.update(changes)
    return json.dumps(data)


def test_v2_file_is_accepted_and_returned_as_it_is(blank_page):
    assert parse(blank_page, v2_file()) == {
        "ok": True, "kind": "v2", "name": "Mein Plan", "subtitle": "", "start": {"term": "SoSe", "year": 2025},
        "m": {"B31": {"s": "ok", "n": "", "mod": None}}, "names": {"B11": "Mathe"},
        "catalog": "LSF WiSe 2026/27", "exportedAt": "2026-10-11T18:05:00.000Z",
    }


def test_export_and_import_are_inverse(blank_page):
    exported = blank_page.evaluate(
        "([p, s]) => JSON.stringify(buildExport(p, s, 'LSF WiSe 2026/27', new Date(0)))", [PROFILE, STATE]
    )
    got = parse(blank_page, exported)
    assert got["ok"] and got["kind"] == "v2"
    assert got["name"] == PROFILE["name"] and got["start"] == PROFILE["start"]
    assert got["m"] == STATE["m"] and got["names"] == STATE["names"]


def test_v1_file_is_accepted_without_name_and_start(blank_page):
    got = parse(blank_page, json.dumps({"rev": 5, "m": {"B31": {"s": "ok", "n": ""}}, "names": {"B11": "x"}}))
    assert got == {"ok": True, "kind": "v1", "name": "", "subtitle": "", "start": None, "m": {"B31": {"s": "ok", "n": ""}},
                   "names": {"B11": "x"}, "catalog": "", "exportedAt": ""}


def test_v1_file_without_names_gets_empty_names(blank_page):
    assert parse(blank_page, json.dumps({"m": {}}))["names"] == {}


def test_byte_order_mark_is_ignored(blank_page):
    assert parse(blank_page, "﻿" + v2_file())["ok"] is True


def test_missing_optional_parts_get_defaults(blank_page):
    text = json.dumps({"app": "htw-studienplaner", "v": 2, "profile": {"m": {}}})
    got = parse(blank_page, text)
    assert got["ok"] and got["name"] == "" and got["start"] is None and got["names"] == {}
    assert got["catalog"] == "" and got["exportedAt"] == ""


def test_wrong_types_of_optional_parts_are_ignored(blank_page):
    text = json.dumps({"app": "htw-studienplaner", "v": 2, "catalog": 5, "exportedAt": [],
                       "profile": {"name": 7, "m": {}, "names": [1]}})
    got = parse(blank_page, text)
    assert got["ok"] and got["name"] == "" and got["names"] == {} and got["catalog"] == "" and got["exportedAt"] == ""


@pytest.mark.parametrize("text", ["", "{not json", "{'a': 1}", "undefined", "{}}"])
def test_text_that_is_not_json_is_named(blank_page, text):
    got = parse(blank_page, text)
    assert got["ok"] is False and got["code"] == "json"
    assert got["error"] == "Das ist keine gültige JSON-Datei."


@pytest.mark.parametrize("text", [
    "null", "[]", "42", '"text"', "true", "{}",
    '{"m": []}', '{"m": null}', '{"m": "x"}', '{"rev": 1}',
    json.dumps({"app": "htw-studienplaner", "v": 2}),
    json.dumps({"app": "htw-studienplaner", "v": 2, "profile": []}),
    json.dumps({"app": "htw-studienplaner", "v": 2, "profile": {}}),
    json.dumps({"app": "htw-studienplaner", "v": 2, "profile": {"m": []}}),
])
def test_wrong_shape_is_named(blank_page, text):
    got = parse(blank_page, text)
    assert got["ok"] is False and got["code"] == "shape"
    assert "kein Plan" in got["error"]


@pytest.mark.parametrize("v", [1, 3, 99, "2", None, True, [2], {"a": 1}, 2.5])
def test_unknown_version_is_rejected(blank_page, v):
    got = parse(blank_page, json.dumps({"app": "htw-studienplaner", "v": v, "profile": {"m": {}}}))
    assert got["ok"] is False and got["code"] == "version"
    assert "kennt nur Version 2" in got["error"]


def test_missing_version_is_rejected(blank_page):
    got = parse(blank_page, json.dumps({"app": "htw-studienplaner", "profile": {"m": {}}}))
    assert got["ok"] is False and got["code"] == "version"


def test_version_in_the_message_is_cut(blank_page):
    got = parse(blank_page, json.dumps({"app": "htw-studienplaner", "v": "x" * 500, "profile": {"m": {}}}))
    assert got["code"] == "version" and len(got["error"]) < 120


@pytest.mark.parametrize("data", [
    {"app": "other-app", "v": 2, "profile": {"m": {}}},
    {"v": 2, "active": "p1", "profiles": {"p1": {"m": {}}}},      # the raw storage value is not an export
    {"app": None, "v": 2, "profile": {"m": {}}},
])
def test_file_of_another_app_is_rejected(blank_page, data):
    got = parse(blank_page, json.dumps(data))
    assert got["ok"] is False and got["code"] == "app"
    assert "nicht von dieser Seite" in got["error"]


def test_prototype_keys_do_not_leak(blank_page):
    text = '{"app":"htw-studienplaner","v":2,"profile":{"m":{"__proto__":{"s":"ok"},"constructor":{"s":"ok"}}}}'
    polluted = blank_page.evaluate("""text => {
        const r = parseImport(text);
        return [r.ok, ({}).s, Object.keys(r.m)];
    }""", text)
    assert polluted[0] is True and polluted[1] is None
    assert polluted[2] == ["__proto__", "constructor"], "left for sane() to discard"


def test_file_size_limit(blank_page):
    assert blank_page.evaluate("importTooLarge(1024 * 1024)") is False
    assert blank_page.evaluate("importTooLarge(1024 * 1024 + 1)") is True
    assert blank_page.evaluate("IMPORT_TOO_LARGE") == "Die Datei ist größer als 1 MB."


# --- subtitle (PRD A12) ----------------------------------------------------------------------

def test_export_carries_a_custom_subtitle_at_the_end(blank_page):
    profile = {**PROFILE, "subtitle": "Mein Untertitel"}
    data = export(blank_page, profile=profile)
    assert data["profile"]["subtitle"] == "Mein Untertitel"
    assert list(data["profile"]) == ["name", "start", "m", "names", "subtitle"]


def test_export_without_a_subtitle_has_no_subtitle_key(blank_page):
    assert "subtitle" not in export(blank_page, profile={**PROFILE, "subtitle": ""})["profile"]
    assert "subtitle" not in export(blank_page)["profile"]


def test_import_reads_the_subtitle(blank_page):
    data = json.loads(v2_file())
    data["profile"]["subtitle"] = "Mein Untertitel"
    assert parse(blank_page, json.dumps(data))["subtitle"] == "Mein Untertitel"
    data["profile"]["subtitle"] = 5
    assert parse(blank_page, json.dumps(data))["subtitle"] == ""


# --- backup reminder (PRD A10): the date is injected -----------------------------------------------

DAY = 24 * 3600 * 1000
NOW_MS = 1_760_000_000_000   # a fixed point in time


def due(page, last_export, created, days=None):
    return page.evaluate(
        "([l, c, n, d]) => backupDue(l, c, new Date(n), d === null ? undefined : d)",
        [last_export, created, NOW_MS, days],
    )


@pytest.mark.parametrize("last_export, created, expected", [
    (NOW_MS - 29 * DAY, 0, False),
    (NOW_MS - 30 * DAY + 1, 0, False),
    (NOW_MS - 30 * DAY, 0, True),            # exactly 30 days: due
    (NOW_MS - 400 * DAY, 0, True),
    (0, NOW_MS - 29 * DAY, False),           # never exported: the clock starts at the creation of the plan
    (0, NOW_MS - 31 * DAY, True),
    (NOW_MS - 1 * DAY, NOW_MS - 400 * DAY, False),   # an export resets the clock, created no longer counts
    (NOW_MS - 31 * DAY, NOW_MS - 1 * DAY, True),     # the export counts, not the newer creation date
    (0, 0, False),                           # nothing known: no reminder
    (None, None, False),
])
def test_backup_due(blank_page, last_export, created, expected):
    assert due(blank_page, last_export, created) is expected


def test_backup_due_with_another_number_of_days(blank_page):
    assert due(blank_page, NOW_MS - 8 * DAY, 0, 7) is True
    assert due(blank_page, NOW_MS - 6 * DAY, 0, 7) is False


def test_backup_period_is_30_days(blank_page):
    assert blank_page.evaluate("BACKUP_DAYS") == 30


def test_future_export_time_is_not_due(blank_page):
    assert due(blank_page, NOW_MS + 5 * DAY, 0) is False
