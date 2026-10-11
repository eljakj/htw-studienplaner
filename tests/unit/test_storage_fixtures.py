"""The v1 storage fixture used by the migration tests must stay valid for the current catalog.

The fixture is fictional (no real study data). If a catalog change makes it invalid, these tests fail
first, so the E2E migration tests never break for an unclear reason."""
import json
from pathlib import Path

import pytest

import catalog

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "storage_v1.json"


@pytest.fixture(scope="module")
def v1():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def slots():
    return {s["id"]: s for s in catalog.SLOTS}


def test_fixture_has_the_v1_shape(v1):
    assert set(v1) == {"rev", "m", "names"}
    assert isinstance(v1["rev"], int) and v1["rev"] > 0
    assert v1["m"], "an empty fixture would not test the migration"


def test_fixture_slots_statuses_and_notes_are_valid(v1):
    by_id = slots()
    for sid, entry in v1["m"].items():
        assert sid in by_id, sid
        assert entry["s"] in catalog.STATUS, sid
        assert len(entry.get("n", "")) <= 28, sid


def test_fixture_modules_come_from_the_right_pool(v1):
    by_id = slots()
    pools = {
        "wp": catalog.WP_IDS,
        "fs": catalog.FS_IDS,
        "awe": {a["id"] for a in catalog.AWE},
    }
    for sid, entry in v1["m"].items():
        if "mod" in entry:
            assert entry["mod"] in pools[by_id[sid]["t"]], sid


def test_fixture_names_belong_to_fixed_slots_and_differ_from_the_catalog(v1):
    by_id = slots()
    for sid, name in v1["names"].items():
        assert by_id[sid]["t"] == "fix", sid
        assert name.strip() and name != by_id[sid]["name"], sid
        assert len(name) <= 40, sid


# --- the outdated v2 plan used by the catalog-update tests ---------------------------------

OUTDATED = Path(__file__).resolve().parents[1] / "fixtures" / "storage_outdated_v2.json"


@pytest.fixture(scope="module")
def outdated():
    return json.loads(OUTDATED.read_text(encoding="utf-8"))["profiles"]["p1"]


def pool_of(slot):
    return {"wp": catalog.WP_IDS, "fs": catalog.FS_IDS, "awe": {a["id"] for a in catalog.AWE}}[slot["t"]]


def test_outdated_plan_refers_to_modules_and_slots_the_catalog_no_longer_has(outdated):
    by_id = slots()
    assert "X77" in outdated["m"] and "X77" not in by_id, "a slot that does not exist"
    for sid in ("WP1", "B36"):
        assert outdated["m"][sid]["mod"] not in pool_of(by_id[sid]), sid + ": the module must be gone"


def test_outdated_plan_keeps_valid_parts_for_the_tests(outdated):
    by_id = slots()
    for sid in ("B31", "B32", "WP2", "B15"):
        assert sid in by_id, sid
        assert outdated["m"][sid]["s"] in catalog.STATUS
        if "mod" in outdated["m"][sid]:
            assert outdated["m"][sid]["mod"] in pool_of(by_id[sid]), sid
    assert outdated["names"]["B11"] and by_id["B11"]["t"] == "fix"
