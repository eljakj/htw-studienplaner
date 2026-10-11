"""Unit tests for the catalog in src/catalog.py."""
import copy
import json

import pytest

import catalog


def by_id(cat):
    return {s["id"]: s for s in cat["slots"]}


# --- structure of the base catalog -------------------------------------------

def test_validate_passes():
    catalog.validate()


def test_has_34_slots_with_unique_ids():
    ids = [s["id"] for s in catalog.SLOTS]
    assert len(ids) == 34
    assert len(ids) == len(set(ids))


def test_total_is_180_lp():
    assert sum(s["lp"] for s in catalog.SLOTS) == 180


@pytest.mark.parametrize("sem", range(1, 7))
def test_each_semester_has_30_lp(sem):
    assert sum(s["lp"] for s in catalog.SLOTS if s["sem"] == sem) == 30


def test_base_catalog_is_neutral():
    """Every slot starts as planned and no module is chosen."""
    for s in catalog.SLOTS:
        assert s["def"]["s"] == "plan", s["id"]
        if s["t"] != "fix":
            assert s["def"]["mod"] is None, s["id"]


def test_catalog_names_its_source_for_exports():
    assert catalog.CATALOG["meta"]["catalog"] == "LSF WiSe 2026/27"


def test_catalog_version_is_kept_by_apply_profile():
    assert catalog.apply_profile({})["meta"]["catalog"] == catalog.META["catalog"]


# --- elective modules vs. the official overview -------------------------------

# Official elective overview, checked against the LSF on 2026-10-11.
OVERVIEW = {
    catalog.SE: {
        "Advanced Programming", "Softwarearchitekturen", "Systemmodellierung",
        "Front-End Development", "Cloud Computing", "Quantencomputing Grundlagen",
    },
    catalog.MS: {
        "Drahtlose Netzwerke", "Decentralized Systems", "Internet of Things (IoT)", "Semantic Search",
    },
    catalog.DS: {
        "Machine Learning 1", "Machine Learning 2", "Data Mining", "Programmierkonzepte für Data Mining",
    },
}
NO_SPECIALIZATION = {"Spezielle Anwendungen der Informatik", "Interdisziplinäres Projekt"}


def wp_names(spec):
    return {w["name"] for w in catalog.WP if w["spec"] == spec}


def test_has_19_elective_modules_with_unique_ids():
    ids = [w["id"] for w in catalog.WP]
    assert len(ids) == 19
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("spec", list(OVERVIEW), ids=lambda s: s)
def test_specialization_matches_official_overview(spec):
    assert wp_names(spec) == OVERVIEW[spec]


def test_modules_without_specialization_are_in_the_catalog():
    assert NO_SPECIALIZATION <= wp_names(catalog.FREI)


# --- apply_profile -----------------------------------------------------------

def test_apply_profile_sets_values():
    profile = {
        "meta": {"subtitle": "Test", "currentSem": 3},
        "slots": {
            "B11": {"s": "ok", "n": "passed"},
            "WP1": {"s": "run", "mod": "B111"},
        },
    }
    result = by_id(catalog.apply_profile(profile))
    assert result["B11"]["def"] == {"s": "ok", "n": "passed"}
    assert result["WP1"]["def"] == {"s": "run", "n": "", "mod": "B111"}
    assert catalog.apply_profile(profile)["meta"] == {"subtitle": "Test", "currentSem": 3, "catalog": catalog.META["catalog"]}


def test_apply_profile_does_not_mutate_base_catalog():
    before = copy.deepcopy(catalog.CATALOG)
    catalog.apply_profile({"meta": {"currentSem": 4}, "slots": {"B11": {"s": "ok"}}})
    assert catalog.CATALOG == before


def test_apply_profile_accepts_modules_from_the_right_pool():
    profile = {
        "slots": {
            "WP1": {"s": "plan", "mod": "B111"},
            "B36": {"s": "plan", "mod": "A00310220"},
            "B15": {"s": "plan", "mod": "F00201481"},
        }
    }
    result = by_id(catalog.apply_profile(profile))
    assert result["WP1"]["def"]["mod"] == "B111"
    assert result["B36"]["def"]["mod"] == "A00310220"
    assert result["B15"]["def"]["mod"] == "F00201481"


@pytest.mark.parametrize("sem", [1, 6])
def test_apply_profile_accepts_semester_bounds(sem):
    result = catalog.apply_profile({"meta": {"currentSem": sem}})
    assert result["meta"]["currentSem"] == sem


@pytest.mark.parametrize(
    "profile",
    [
        {"slots": {"X99": {"s": "ok"}}},
        {"slots": {"B11": {"s": "done"}}},
        {"slots": {"B11": {}}},
        {"slots": {"WP1": {"s": "plan", "mod": "A00310220"}}},
        {"slots": {"B15": {"s": "plan", "mod": "B111"}}},
        {"meta": {"currentSem": 0}},
        {"meta": {"currentSem": 7}},
    ],
    ids=[
        "unknown-slot",
        "invalid-status",
        "missing-status",
        "awe-module-in-elective-slot",
        "elective-module-in-language-slot",
        "semester-below-range",
        "semester-above-range",
    ],
)
def test_apply_profile_rejects_invalid_input(profile):
    with pytest.raises(AssertionError):
        catalog.apply_profile(profile)


# --- to_json -----------------------------------------------------------------

def test_to_json_roundtrips_base_catalog():
    assert json.loads(catalog.to_json()) == catalog.CATALOG


def test_to_json_escapes_script_end_tag():
    """The JSON is embedded in a <script> tag, so '</' must never appear."""
    cat = catalog.apply_profile({"meta": {"subtitle": "</script><b>x</b>"}})
    out = catalog.to_json(cat)
    assert "</" not in out
    assert json.loads(out) == cat
