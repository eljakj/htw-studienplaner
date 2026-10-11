"""Unit tests for src/semester.js (PRD A3).

The functions are plain JavaScript without DOM or clock access. The tests load the file into a blank page of
the headless Chromium that Playwright already provides, call the functions with injected dates and compare the results."""
import pytest

import build

playwright_sync = pytest.importorskip("playwright.sync_api")

SOSE_2025 = {"term": "SoSe", "year": 2025}
WISE_2025 = {"term": "WiSe", "year": 2025}
WISE_2023 = {"term": "WiSe", "year": 2023}


@pytest.fixture(scope="module")
def js():
    with open(build.SEMESTER_JS, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def blank_page(js):
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch()
        blank = browser.new_page()
        blank.set_content("<!doctype html><title>semester</title>")
        blank.add_script_tag(content=js)
        yield blank
        browser.close()


def semester(blank_page, start, year, month, day):
    """currentSemester(start, <the given date>) as a dict; month is 1..12."""
    return blank_page.evaluate(
        "([start, y, m, d]) => currentSemester(start, new Date(y, m - 1, d))", [start, year, month, day]
    )


def result(state, sem=None, label=""):
    return {"state": state, "sem": sem, "label": label}


def test_does_not_read_the_clock(js):
    assert "new Date" not in js and "Date.now" not in js, "the date must be passed in"


def test_no_start_marks_no_semester(blank_page):
    assert semester(blank_page, None, 2026, 10, 10) == result("none")


def test_example_from_the_prd(blank_page):
    # Beginn SoSe 2025, Datum 10.10.2026 -> 4. Semester
    assert semester(blank_page, SOSE_2025, 2026, 10, 10) == result("running", 4)


@pytest.mark.parametrize("start, date, sem", [
    # summer term: 1 April - 30 September
    (SOSE_2025, (2025, 4, 1), 1),
    (SOSE_2025, (2025, 9, 30), 1),
    # winter term: 1 October - 31 March, January to March still belong to the winter term of the year before
    (SOSE_2025, (2025, 10, 1), 2),
    (SOSE_2025, (2026, 1, 15), 2),
    (SOSE_2025, (2026, 3, 31), 2),
    (SOSE_2025, (2026, 4, 1), 3),
    (WISE_2025, (2025, 10, 1), 1),
    (WISE_2025, (2026, 1, 15), 1),
    (WISE_2025, (2026, 3, 31), 1),
    (WISE_2025, (2026, 4, 1), 2),
    # last regular semester
    (WISE_2023, (2026, 9, 30), 6),
])
def test_running_semesters_and_term_boundaries(blank_page, start, date, sem):
    assert semester(blank_page, start, *date) == result("running", sem)


@pytest.mark.parametrize("date", [(2026, 10, 1), (2026, 10, 10), (2030, 5, 5)])
def test_from_the_7th_semester_on_it_stays_at_6_and_is_over(blank_page, date):
    assert semester(blank_page, WISE_2023, *date) == result("over", 6)


@pytest.mark.parametrize("start, date, label", [
    ({"term": "WiSe", "year": 2027}, (2026, 10, 10), "WiSe 2027/28"),
    ({"term": "SoSe", "year": 2026}, (2026, 3, 31), "SoSe 2026"),
    ({"term": "WiSe", "year": 2026}, (2026, 9, 30), "WiSe 2026/27"),
])
def test_start_in_the_future_marks_no_semester(blank_page, start, date, label):
    assert semester(blank_page, start, *date) == result("future", None, label)


def test_start_term_itself_is_the_first_semester(blank_page):
    assert semester(blank_page, {"term": "SoSe", "year": 2026}, 2026, 4, 1) == result("running", 1)
    assert semester(blank_page, {"term": "WiSe", "year": 2026}, 2026, 10, 1) == result("running", 1)


def test_same_input_gives_the_same_result(blank_page):
    assert semester(blank_page, SOSE_2025, 2026, 10, 10) == semester(blank_page, SOSE_2025, 2026, 10, 10)


@pytest.mark.parametrize("term, year, label", [
    ("SoSe", 2025, "SoSe 2025"),
    ("WiSe", 2025, "WiSe 2025/26"),
    ("WiSe", 2099, "WiSe 2099/00"),
])
def test_term_labels(blank_page, term, year, label):
    assert blank_page.evaluate("([t, y]) => termLabel({term: t, year: y})", [term, year]) == label


# --- startForSemester: the inverse, used by the example plan ------------------------------

def start_for(blank_page, sem, year, month, day):
    return blank_page.evaluate(
        "([sem, y, m, d]) => startForSemester(sem, new Date(y, m - 1, d))", [sem, year, month, day]
    )


def test_start_for_semester_example(blank_page):
    # 10 Oct 2026 is in WiSe 2026/27; the 4th semester started three terms earlier, in SoSe 2025
    assert start_for(blank_page, 4, 2026, 10, 10) == SOSE_2025
    assert start_for(blank_page, 1, 2026, 10, 10) == {"term": "WiSe", "year": 2026}
    assert start_for(blank_page, 2, 2026, 10, 10) == {"term": "SoSe", "year": 2026}


@pytest.mark.parametrize("date", [(2026, 3, 31), (2026, 4, 1), (2026, 9, 30), (2026, 10, 1), (2027, 1, 15), (2031, 7, 7)])
@pytest.mark.parametrize("sem", [1, 2, 3, 4, 5, 6])
def test_start_for_semester_round_trip(blank_page, sem, date):
    start = start_for(blank_page, sem, *date)
    assert semester(blank_page, start, *date) == result("running", sem)
