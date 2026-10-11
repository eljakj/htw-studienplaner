"""Storage: schema v2, silent saving, clean loading and several tabs (PRD A5)."""
import json

import pytest
from playwright.sync_api import expect

KEY = "studienverlauf-ai-v2"
OLD_KEY = "studienverlauf-ai-v1"  # migration: see test_migration.py


def lp(page):
    return page.locator("#lpnow")


def set_passed(page, cell_id):
    page.click('.cell[data-id="%s"]' % cell_id)
    page.click('#opts .opt[data-s="ok"]')


def read_store(page, key=KEY):
    raw = page.evaluate("key => localStorage.getItem(key)", key)
    return None if raw is None else json.loads(raw)


def put_store(page, value, key=KEY):
    raw = value if isinstance(value, str) else json.dumps(value)
    page.evaluate("([key, raw]) => localStorage.setItem(key, raw)", [key, raw])


def profile_with(m=None, names=None, **extra):
    profile = {"name": "Mein Plan", "start": None, "rev": 1, "m": m or {}, "names": names or {}}
    profile.update(extra)
    return {"v": 2, "active": "p1", "profiles": {"p1": profile}}


# --- schema and silent saving -------------------------------------------------

def test_plain_visit_writes_nothing(app):
    assert read_store(app) is None
    assert read_store(app, OLD_KEY) is None


def test_change_is_saved_in_the_v2_schema(app):
    set_passed(app, "B31")
    store = read_store(app)
    assert store["v"] == 2
    assert store["active"] == "p1"
    profile = store["profiles"]["p1"]
    assert set(profile) == {"name", "start", "rev", "m", "names", "created"}, "created: additive field (PRD A10)"
    assert 0 < profile["created"] <= profile["rev"]
    assert profile["name"] == "Mein Plan"
    assert profile["start"] is None
    assert profile["rev"] > 0
    assert profile["m"]["B31"]["s"] == "ok"
    assert list(profile["m"]) == ["B31"], "only deviations from the catalog are stored"


def test_note_survives_reload_and_is_limited(app):
    app.click('.cell[data-id="B31"]')
    app.fill("#noteIn", "x" * 40)
    app.reload()
    stored = read_store(app)["profiles"]["p1"]["m"]["B31"]["n"]
    assert stored == "x" * 28


# --- loading goes through sane() ------------------------------------------------

def test_tampered_storage_is_cleaned_and_shown_as_text(app):
    put_store(app, profile_with(
        m={
            "B31": {"s": "ok", "n": "<b id=pwn>x</b> " + "long " * 10, "mod": None},
            "NOPE": {"s": "ok", "n": ""},
            "toString": {"s": "ok", "n": ""},
            "__proto__": {"s": "ok", "n": ""},
            "B33": {"s": "bogus", "n": ""},
            "B34": {"s": "toString", "n": ""},
            "B35": {"s": ["ok"], "n": ""},
            "WP1": {"s": "ok", "n": "", "mod": "B999"},
            "WP2": {"s": "ok", "n": "", "mod": "toString"},
        },
        names={"B31": "<i id=pwn2>y</i>", "NOPE": "x", "WP1": "not a fixed slot"},
    ))
    app.reload()
    assert app.locator("#pwn, #pwn2").count() == 0, "stored text must never become HTML"
    set_passed(app, "B32")  # any change saves the cleaned state
    profile = read_store(app)["profiles"]["p1"]
    assert sorted(profile["m"]) == ["B31", "B32", "WP1", "WP2"]
    assert len(profile["m"]["B31"]["n"]) == 28
    assert profile["m"]["WP1"]["mod"] is None
    assert profile["m"]["WP2"]["mod"] is None
    assert list(profile["names"]) == ["B31"]


@pytest.mark.parametrize("value", [
    "{not json",
    "null",
    "[]",
    '{"v": 3, "active": "p1", "profiles": {}}',
    '{"v": 2, "active": "p1", "profiles": []}',
    '{"v": 2, "active": "p1", "profiles": {"x y": {"m": {}}}}',
])
def test_unusable_storage_gives_an_empty_plan(app, value):
    put_store(app, value)
    app.reload()
    expect(lp(app)).to_have_text("0")
    expect(app.locator(".cell")).to_have_count(34)


def test_invalid_start_and_name_fall_back(app):
    put_store(app, profile_with(name=42, start={"term": "Spring", "year": "x"}))
    app.reload()
    set_passed(app, "B31")
    profile = read_store(app)["profiles"]["p1"]
    assert profile["name"] == "Mein Plan"
    assert profile["start"] is None


def test_valid_start_is_kept(app):
    put_store(app, profile_with(start={"term": "SoSe", "year": 2025}))
    app.reload()
    set_passed(app, "B31")
    assert read_store(app)["profiles"]["p1"]["start"] == {"term": "SoSe", "year": 2025}


def test_other_profiles_are_kept_when_saving(app):
    store = profile_with()
    store["profiles"]["p2"] = {"name": "Zweiter", "start": None, "rev": 5, "m": {}, "names": {}}
    put_store(app, store)
    app.reload()
    set_passed(app, "B31")
    saved = read_store(app)
    assert saved["profiles"]["p2"]["name"] == "Zweiter"
    assert saved["profiles"]["p1"]["m"]["B31"]["s"] == "ok"


# --- several tabs and several browsers ------------------------------------------

def test_other_tab_loads_the_change_and_the_last_change_wins(app, base_url):
    second = app.context.new_page()
    second.goto(base_url + "/")
    set_passed(app, "B31")                       # 6 LP
    expect(lp(second)).to_have_text("6")         # no reload needed: storage event
    set_passed(second, "B32")                    # 5 LP on top
    expect(lp(app)).to_have_text("11")
    assert sorted(read_store(app)["profiles"]["p1"]["m"]) == ["B31", "B32"]


def test_other_tab_forgets_its_undo_history(app, base_url):
    set_passed(app, "B31")
    second = app.context.new_page()
    second.goto(base_url + "/")
    set_passed(second, "B32")
    expect(lp(app)).to_have_text("11")
    expect(app.locator("#undo")).to_be_disabled()


def test_two_browsers_keep_separate_plans(app, new_context, base_url):
    set_passed(app, "B31")
    other = new_context().new_page()
    other.goto(base_url + "/")
    assert read_store(other) is None
    set_passed(other, "B32")
    expect(lp(other)).to_have_text("5")
    expect(lp(app)).to_have_text("6")
    assert list(read_store(app)["profiles"]["p1"]["m"]) == ["B31"]
    assert list(read_store(other)["profiles"]["p1"]["m"]) == ["B32"]
