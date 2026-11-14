"""Explicit FCJ score tables, labels, origins and saved-file accessors."""

from datetime import datetime
import math

import pandas as pd
import pytest

from schemas import fcj


def result(total, element="loop"):
    return fcj.ManResult(
        els=[fcj.El(name="entry", start=0, stop=1), fcj.El(name=element, start=1, stop=3)],
        results=[
            fcj.Score(score=fcj.ScoreValues(intra=total, inter=0, positioning=0, total=total),
                      properties=fcj.ScoreProperties()),
            fcj.Score(score=fcj.ScoreValues(intra=total - 1, inter=0, positioning=0, total=total - 1),
                      properties=fcj.ScoreProperties(difficulty=2, truncate=True)),
        ],
    )


def flight():
    parameters = fcj.Parameters(
        rotation=math.pi / 2, start=0, stop=3, moveEast=2, moveNorth=-3,
        wingspan=2, modelwingspan=1, elevate=4, originLat=0, originLng=0, originAlt=0,
        pilotLat="51", pilotLng="-1", pilotAlt="100", centerLat=51, centerLng=-1, centerAlt=100,
        schedule=["F3A", "P27"],
    )
    mans = [fcj.Man(name=name, k=k, id=str(index), sp=0, wd=0, start=0, stop=3,
                    sel=True, background="")
            for index, (name, k) in enumerate((("takeoff", 0), ("a", 2), ("b", 3), ("landing", 0)))]
    return fcj.FCJ(
        version="1", comments="synthetic", name="test_26_01_02_00000001.json",
        view=fcj.View(position={}, target={}), parameters=parameters, scored=True,
        scores=[None, 8, 7, None], mans=mans,
        data=[fcj.Data(r=0, p=0, yw=0, N=1, E=2, D=-3, time=0, roll=0, pitch=0, yaw=0)],
        fcs_scores=[
            fcj.Result(fa_version="1.0.0", manresults=[None, result(8), result(7), None]),
            fcj.Result(fa_version="1.1.0", manresults=[None, result(9), result(6), None]),
        ],
    )


def test_manresult_score_properties_labels_and_table_values():
    value = result(8)
    assert value.get_score().total == 8
    assert value.get_score(fcj.ScoreProperties(difficulty=2, truncate=True)).total == 7
    assert fcj.ScoreProperties() == fcj.ScoreProperties(difficulty=3, truncate=False)
    assert fcj.ScoreProperties() != fcj.ScoreProperties(difficulty=2)
    assert fcj.ScoreProperties() != {"difficulty": 3, "truncate": False}
    assert value.label_group().model_dump() == {
        "entry": {"start": 0., "stop": 1., "sublabels": None},
        "loop": {"start": 1., "stop": 3., "sublabels": None},
    }
    table = value.to_df()
    assert table.index.names == ["difficulty", "truncate"]
    assert table.loc[(3, False)].to_dict() == {"intra": 8., "inter": 0., "positioning": 0., "total": 8.}
    with pytest.raises(StopIteration):
        value.get_score(fcj.ScoreProperties(difficulty=99))


def test_fcj_score_tables_keep_version_manoeuvre_and_k_factor_axes(tmp_path):
    value = flight()
    scores = value.score_df()
    assert scores.index.names == ["version", "manoeuvre", "difficulty", "truncate"]
    assert scores.loc[("1.0.0", 0, 3, False), "total"] == 8
    assert scores.loc[("1.0.0", 1, 3, False), "total"] == 7
    assert value.man_df().name.to_list() == ["a", "b"]
    assert value.man_df().k.to_list() == [2, 3]
    weighted = value.pfc_version_df()
    assert weighted.loc[("1.0.0", 0), ("raw", "total")] == 8
    assert weighted.loc[("1.0.0", 0), ("kfac", "total")] == 16
    assert value.version_summary_df()[("kfac", "total")].to_dict() == {"1.0.0": 37., "1.1.0": 36.}
    assert value.latest_version() == "1.1.0"
    path = tmp_path / "flight.json"
    path.write_text(value.model_dump_json())
    pd.testing.assert_frame_equal(fcj.get_scores(str(path)), weighted)
    assert fcj.FCJ.model_validate_json(path.read_text()) == value


def test_fcj_origin_dates_and_unscored_lists_are_independent():
    value = flight()
    assert value.id == "00000001"
    assert value.created == datetime(2026, 1, 2)
    assert value.origin.model_dump() == {
        "lat": 51., "lng": -1., "alt": 100., "heading": 90.,
        "move_north": -3., "move_east": 2., "move_down": 4.,
    }
    assert fcj.Origin.zero().model_dump() == {"lat": 0., "lng": 0., "alt": 0., "heading": 0.}
    value.name = "unparseable"
    assert value.created is None
    with pytest.raises(TypeError):
        _ = value.id
    other = flight()
    value.human_scores.append(fcj.HumanResult(name="judge", date="2026-01-02", scores=[7, 8]))
    assert other.human_scores == []
