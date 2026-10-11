"""Migration of the old v1 storage key to v2 (PRD A5, "Datenmodell, Speicherung, Migration")."""
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"
V1_TEXT = (Path(__file__).resolve().parents[1] / "fixtures" / "storage_v1.json").read_text(encoding="utf-8")
V1 = json.loads(V1_TEXT)
V1_LP = 11  # B11 Programmierung 1 (6 LP) + WP1 Cloud Computing (5 LP), both passed


def lp(page):
    return page.locator("#lpnow")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def raw(page, key):
    return page.evaluate("key => localStorage.getItem(key)", key)


def put(page, key, value):
    page.evaluate("([key, value]) => localStorage.setItem(key, value)", [key, value])


def test_v1_becomes_the_profile_mein_plan(app):
    put(app, OLD_KEY, V1_TEXT)
    app.reload()
    expect(lp(app)).to_have_text(str(V1_LP))
    store = json.loads(raw(app, KEY))      # written right away, without any change by the user
    assert store["v"] == 2 and store["active"] == "p1"
    profile = store["profiles"]["p1"]
    assert profile["name"] == "Mein Plan"
    assert profile["start"] is None
    assert profile["rev"] == V1["rev"]
    assert profile["m"] == {sid: {"s": e["s"], "n": e.get("n", ""), "mod": e.get("mod")} for sid, e in V1["m"].items()}
    assert profile["names"] == V1["names"]


def test_v1_key_is_left_untouched_and_later_changes_go_to_v2(app):
    put(app, OLD_KEY, V1_TEXT)
    app.reload()
    set_passed(app, "B32")                 # 5 LP on top of the migrated state
    expect(lp(app)).to_have_text(str(V1_LP + 5))
    assert raw(app, OLD_KEY) == V1_TEXT
    assert "B32" in json.loads(raw(app, KEY))["profiles"]["p1"]["m"]


def test_migrated_state_survives_another_reload(app):
    put(app, OLD_KEY, V1_TEXT)
    app.reload()
    app.reload()
    expect(lp(app)).to_have_text(str(V1_LP))


def test_existing_v2_key_blocks_the_migration(app):
    v2 = {"v": 2, "active": "p1", "profiles": {"p1": {"name": "Mein Plan", "start": None, "rev": 5,
          "m": {"B32": {"s": "ok", "n": "", "mod": None}}, "names": {}}}}
    put(app, KEY, json.dumps(v2))
    put(app, OLD_KEY, V1_TEXT)
    app.reload()
    expect(lp(app)).to_have_text("5")      # only B32, nothing from v1
    assert json.loads(raw(app, KEY)) == v2
    assert raw(app, OLD_KEY) == V1_TEXT


def test_unusable_v2_key_still_blocks_the_migration(app):
    put(app, KEY, "{not json")
    put(app, OLD_KEY, V1_TEXT)
    app.reload()
    expect(lp(app)).to_have_text("0")
    assert raw(app, KEY) == "{not json"


@pytest.mark.parametrize("value", [
    "{not json",
    "null",
    "[]",
    '"text"',
    '{"m": []}',
    '{"m": {}, "names": {}}',                    # empty plan, e.g. after "Semesterstart"
    '{"m": {"NOPE": {"s": "ok", "n": ""}}}',     # nothing valid left after sane()
    '{"m": {"B31": {"s": "bogus", "n": ""}}}',
])
def test_corrupt_or_empty_v1_is_ignored(app, value):
    put(app, OLD_KEY, value)
    app.reload()                                 # the app fixture fails the test on JavaScript errors
    expect(lp(app)).to_have_text("0")
    expect(app.locator(".cell")).to_have_count(34)
    assert raw(app, KEY) is None
    assert raw(app, OLD_KEY) == value


def test_v1_is_cleaned_like_any_stored_data(app):
    tampered = {"rev": 7, "m": {"B31": {"s": "ok", "n": "x" * 40}, "NOPE": {"s": "ok"}, "toString": {"s": "ok"}},
                "names": {"B14": "<b id=pwn>x</b>"}}
    put(app, OLD_KEY, json.dumps(tampered))
    app.reload()
    assert app.locator("#pwn").count() == 0
    profile = json.loads(raw(app, KEY))["profiles"]["p1"]
    assert list(profile["m"]) == ["B31"]
    assert profile["m"]["B31"]["n"] == "x" * 28
