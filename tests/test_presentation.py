"""The sequence function that adds up the figures' presentation deductions (plan phase 3).

`data/presentation_cases.json` is shared with the client: its TypeScript copy of the function
is checked against the same cases.
"""

import json
from pathlib import Path

import pytest

from schemas import MA, ScheduleInfo
from schemas.fcj import ManResult, Score, ScoreProperties, ScoreValues
from schemas.flightdata import NewState
from schemas.handover import apply_line_handover
from schemas.presentation import (
    get_presentation,
    presentation_score,
    presentation_scores,
    split_sequences,
)

DATA = json.loads((Path(__file__).parent / "data" / "presentation_cases.json").read_text())
CASES = DATA["cases"]
NON_ROW = ("difficulty", "truncate")


def make_ma(figure: dict, version: str) -> MA:
    category, name = figure["schedule"].split("_", 1)
    history = None
    if figure["scores"] is not None:
        results = [
            Score(
                score=ScoreValues(**{k: v for k, v in r.items() if k not in NON_ROW}),
                properties=ScoreProperties(difficulty=r["difficulty"], truncate=r["truncate"]),
            )
            for r in figure["scores"]
        ]
        history = {version: ManResult(els=[], results=results)}
    return MA(
        name=f"m{figure['id']}",
        id=figure["id"],
        schedule=ScheduleInfo(category=category, name=name),
        flown=NewState.model_validate({"t": [0.0]}),
        history=history,
    )


def k_argument(k):
    if isinstance(k, dict):
        return lambda s: k.get(f"{s.category}_{s.name}")
    return k


def run(case, mans=None):
    version = case["version"]
    mans = mans or [make_ma(f, version) for f in case["figures"]]
    return presentation_scores(mans, version, k_argument(case["k"]))


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_shared_cases(case):
    got = run(case)

    assert len(got) == len(case["expected"])
    for g, e in zip(got, case["expected"]):
        assert (g.sequence, g.properties.difficulty, g.properties.truncate) == (
            e["sequence"],
            e["difficulty"],
            e["truncate"],
        )
        assert g.deduction == pytest.approx(e["deduction"], abs=1e-9)
        assert g.score == pytest.approx(e["score"], abs=1e-9)
        assert g.k == e["k"]
        assert {str(i): v for i, v in g.contributions.items()} == pytest.approx(
            e["contributions"], abs=1e-9
        )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_scores_stay_within_zero_to_ten(case):
    assert all(0 <= s.score <= 10 for s in run(case))


def test_handover_and_presentation_are_independent():
    """Hand-over rewrites intra and total, presentation reads presentation: any order agrees."""
    case = next(c for c in CASES if c["name"] == "independent_of_line_handover")
    version = case["version"]
    mans = [make_ma(f, version) for f in case["figures"]]
    before = presentation_scores(mans, version, 40)
    after = presentation_scores(apply_line_handover(mans, version), version, 40)
    assert [s.model_dump() for s in before] == [s.model_dump() for s in after]
    handed = apply_line_handover(mans, version)
    assert handed[1].history[version].results[0].score.intra == pytest.approx(0.5 + 0.4)
    assert [m.history[version].results[0].score.presentation for m in handed] == [0.5, 0.25]


def test_other_versions_are_ignored():
    case = next(c for c in CASES if c["name"] == "single_sequence")
    mans = [make_ma(f, "1.0.0") for f in case["figures"]]
    assert presentation_scores(mans, "0.9.0", 40) == []
    assert len(presentation_scores(mans, "1.0.0", 40)) == 1


def test_weighted_adds_the_score_times_k():
    case = next(c for c in CASES if c["name"] == "single_sequence")
    (s,) = run(case)
    assert s.weighted == pytest.approx(8.0 * 40)
    (unweighted,) = presentation_scores([make_ma(f, "1.0.0") for f in case["figures"]], "1.0.0")
    assert unweighted.k is None and unweighted.weighted == 0


def test_get_presentation_picks_one_row_set():
    case = next(c for c in CASES if c["name"] == "every_difficulty_and_truncation_uses_its_own_row")
    scores = run(case)
    assert len(scores) == 6
    (hard,) = get_presentation(scores)
    assert hard.properties == ScoreProperties(difficulty=3, truncate=False)
    (easy,) = get_presentation(scores, ScoreProperties(difficulty=1, truncate=True))
    assert easy.deduction == pytest.approx(0.3)


def test_split_sequences_by_schedule_and_figure_number():
    def ma(schedule, id):
        category, name = schedule.split("_")
        return MA(
            name=f"m{id}", id=id,
            schedule=ScheduleInfo(category=category, name=name),
            flown=NewState.model_validate({"t": [0.0]}),
        )

    mans = [ma("iac_a", 1), ma("iac_a", 3), ma("iac_a", 2), ma("iac_b", 3), ma("iac_b", 4)]
    assert [[m.id for m in s] for s in split_sequences(mans)] == [[1, 3], [2], [3, 4]]
    assert [[m.schedule.name for m in s] for s in split_sequences(mans)] == [["a", "a"], ["a"], ["b", "b"]]
    assert split_sequences([]) == []


def test_presentation_score_clamps():
    assert presentation_score(0) == 10
    assert presentation_score(10.5) == 0
