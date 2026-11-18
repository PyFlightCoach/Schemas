"""The sequence function that hands the line between figures on (A6).

`data/line_handover_cases.json` is shared with the client: its TypeScript copy of the function
is checked against the same cases.
"""

import json
from pathlib import Path

import pytest

from schemas import MA, ScheduleInfo, fcj
from schemas.fcj import ManResult, Score, ScoreProperties, ScoreValues
from schemas.flightdata import NewState
from schemas.handover import apply_line_handover, figure_score, truncate_half

CASES = json.loads((Path(__file__).parent / "data" / "line_handover_cases.json").read_text())["cases"]
VERSION = "1.0.0"


def make_ma(figure: dict, version: str = VERSION) -> MA:
    category, name = figure["schedule"].split("_", 1)
    history = None
    if figure["scores"] is not None:
        results = [
            Score(
                score=ScoreValues(**{k: v for k, v in r.items() if k not in ("difficulty", "truncate")}),
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


def rows(ma: MA, version: str = VERSION):
    return [
        dict(difficulty=r.properties.difficulty, truncate=r.properties.truncate, intra=r.score.intra, total=r.score.total)
        for r in ma.history[version].results
    ]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_shared_cases(case):
    mans = [make_ma(f) for f in case["figures"]]

    out = apply_line_handover(mans, VERSION)

    assert len(out) == len(mans)
    for ma, expected, figure in zip(out, case["expected"], case["figures"]):
        if expected is None:
            assert ma.history is None or VERSION not in ma.history
        else:
            got = rows(ma)
            assert len(got) == len(expected)
            for g, e in zip(got, expected):
                assert (g["difficulty"], g["truncate"]) == (e["difficulty"], e["truncate"])
                assert g["intra"] == pytest.approx(e["intra"], abs=1e-9)
                assert g["total"] == pytest.approx(e["total"], abs=1e-9)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_applying_twice_changes_nothing(case):
    once = apply_line_handover([make_ma(f) for f in case["figures"]], VERSION)

    twice = apply_line_handover(once, VERSION)

    assert [m.model_dump() for m in twice] == [m.model_dump() for m in once]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_raw_components_inter_and_positioning_are_kept(case):
    mans = [make_ma(f) for f in case["figures"]]

    for before, after in zip(mans, apply_line_handover(mans, VERSION)):
        if before.history is None:
            continue
        for b, a in zip(before.history[VERSION].results, after.history[VERSION].results):
            assert (a.score.intra_own, a.score.handover) == (b.score.intra_own, b.score.handover)
            assert (a.score.inter, a.score.positioning) == (b.score.inter, b.score.positioning)
            assert a.properties == b.properties


def test_inputs_are_not_modified():
    case = next(c for c in CASES if c["name"] == "hands_on_to_the_next_figure")
    mans = [make_ma(f) for f in case["figures"]]
    snapshot = [m.model_dump() for m in mans]

    apply_line_handover(mans, VERSION)

    assert [m.model_dump() for m in mans] == snapshot


def test_other_versions_are_untouched():
    case = next(c for c in CASES if c["name"] == "hands_on_to_the_next_figure")
    mans = [make_ma(f) for f in case["figures"]]
    mans = [
        m.model_copy(update=dict(history=m.history | {"0.9.0": m.history[VERSION]}))
        for m in mans
    ]

    out = apply_line_handover(mans, VERSION)

    assert [m.history["0.9.0"] for m in out] == [m.history["0.9.0"] for m in mans]
    assert [m.history[VERSION] for m in out] != [m.history[VERSION] for m in mans]


def test_a_version_missing_from_every_figure_is_a_no_op():
    case = CASES[0]
    mans = [make_ma(f) for f in case["figures"]]

    assert apply_line_handover(mans, "9.9.9") == mans


def test_figure_with_no_history_at_all_is_left_alone():
    figures = CASES[0]["figures"]
    mans = [make_ma(f) for f in figures]
    mans[1] = mans[1].model_copy(update=dict(history=None))

    out = apply_line_handover(mans, VERSION)

    assert out[1].history is None
    # the figure after it receives nothing from it
    assert rows(out[2])[0]["intra"] == pytest.approx(figures[2]["scores"][0]["intra_own"])


def test_empty_list():
    assert apply_line_handover([], VERSION) == []


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.0, 0.0), (0.24, 0.0), (0.5, 0.5), (0.74, 0.5), (1.0, 1.0), (1.99, 1.5), (2.5, 2.5)],
)
def test_truncate_half(value, expected):
    assert truncate_half(value) == expected


def test_figure_score_without_raw_components_is_unchanged():
    legacy = ScoreValues(intra=1.0, inter=0.5, positioning=0.0, total=8.5)

    assert figure_score(legacy, 3.0, True) is legacy


def test_legacy_score_values_load_and_dump_without_the_new_fields():
    legacy = {"intra": 1.0, "inter": 0.5, "positioning": 0.0, "total": 8.5}

    value = ScoreValues.model_validate(legacy)

    assert value.intra_own is None and value.handover is None
    assert value.model_dump() == legacy
    assert ScoreValues.model_validate({**legacy, "intra_own": 0.5, "handover": 0.5}).model_dump() == {
        **legacy, "intra_own": 0.5, "handover": 0.5,
    }


def test_result_table_keeps_its_columns_for_legacy_scores_and_adds_raw_ones():
    def table(**extra):
        mr = ManResult(
            els=[],
            results=[Score(
                score=ScoreValues(intra=1.0, inter=0.0, positioning=0.0, total=9.0, **extra),
                properties=ScoreProperties(difficulty=3, truncate=False),
            )],
        )
        return mr.to_df()

    assert list(table().columns) == ["intra", "inter", "positioning", "total"]
    assert list(table(intra_own=0.5, handover=0.5).columns) == [
        "intra", "inter", "positioning", "total", "intra_own", "handover",
    ]
