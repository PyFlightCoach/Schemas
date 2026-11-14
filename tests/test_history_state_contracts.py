"""Synthetic history, sample-label and downgrade-summary contracts."""

import copy

import numpy as np
import pytest

from schemas import AJson, MA, ManResult, Score, ScoreProperties, ScoreValues
from schemas.flightdata import LegacyState, NewState


def _result(total=8):
    return ManResult.model_validate({
        "els": [{"name": "entry", "start": 0, "stop": 1}, {"name": "loop", "start": 1, "stop": 3}],
        "results": [Score(score=ScoreValues(intra=total, inter=0, positioning=0, total=total),
                          properties=ScoreProperties())],
    })


def _man(name="a", schedule="p27", **values):
    return MA.model_validate({
        "name": name, "id": 1, "schedule": {"category": "f3a", "name": schedule},
        "flown": {"t": [0, 1, 2, 3]}, "schedule_direction": "LTOR",
        "history": {"1.9.0": _result(8), "1.10.0": _result(9)},
        "mdef": {"info": {"k": 3}}, **values,
    })


def test_ajson_basic_lookup_and_schedule_keep_sources_and_direction(tmp_path):
    original = AJson(isComp=True, origin={"lat": 1, "lng": 2, "alt": 3, "heading": 90},
                     sourceBin="synthetic.bin", sourceFCJ="synthetic.json", bootTime="2026-01-02T03:04:05Z",
                     mans=[_man("a"), _man("b")])
    before = original.model_dump_json()
    assert list(original) == original.mans
    assert original[0] is original["a"] and original[1] is original["b"]
    with pytest.raises(ValueError):
        original["missing"]
    with pytest.raises(IndexError):
        original[3]
    assert original.k_factors == [3, 3]
    assert str(original.schedule()) == "f3a_p27"
    assert original.is_full is False
    basic = original.basic()
    assert all(m.mdef is None for m in basic)
    assert basic.origin == original.origin and basic.bootTime == original.bootTime
    assert basic.sourceBin == "synthetic.bin" and basic.sourceFCJ == "synthetic.json"
    assert all(m.schedule_direction.name == "LTOR" for m in basic)
    definitions = [{"info": {"k": 4}}, {"info": {"k": 5}}]
    assert original.basic(definitions).k_factors == [4, 5]
    path = tmp_path / "analysis.json"
    path.write_text(before)
    assert AJson.parse_json(path) == original
    assert AJson.parse_json(original.model_dump(mode="json")) == original
    assert original.model_dump_json() == before


def test_mixed_schedules_valid_versions_and_rename_leave_input_unchanged():
    first = _man("a", history={"invalid": _result(), "1.9.0": _result(8), "1.10.0": _result(9)})
    second = _man("b", schedule="f27")
    value = AJson(isComp=False, mans=[first, second])
    before = value.model_dump_json()
    assert str(value.schedule()) == "na_mixed"
    assert {str(s) for s in value.schedule(allow_multiple=True)} == {"f3a_p27", "f3a_f27"}
    assert set(value.all_versions()) == {"invalid", "1.9.0", "1.10.0"}
    assert set(value.all_valid_versions()) == {"1.9.0", "1.10.0"}
    assert value.latest_version() == "1.10.0" and first.latest_version == "1.10.0"
    assert value.check_version("v1.10.0") and not value.check_version("1.11.0")
    assert value.rename_version("1.9.0", "1.8.0").check_version("1.8.0")
    assert value.model_dump_json() == before
    assert first.rename_version("absent", "new") is first
    assert "1.10.0: 9.00" in str(first) and repr(first) == str(first)


def test_empty_and_invalid_histories_have_no_latest_version():
    for history in ({}, {"invalid": _result()}):
        value = AJson(isComp=False, mans=[_man(history=history)])
        assert value.latest_version() is None
        assert value[0].latest_version is None


def test_option_k_factor_and_explicit_or_all_version_totals():
    man = _man(mdef=[{"info": {"k": 2}}, {"info": {"k": 5}}])
    assert man.k == 2
    assert man.k_factored_score(version="All").to_dict() == {"1.9.0": 16., "1.10.0": 18.}
    assert man.k_factored_score(version="Latest") == 18
    for missing in (None, []):
        with pytest.raises(ValueError, match="No k factor available"):
            _man(mdef=missing).k
    value = AJson(isComp=False, mans=[man])
    assert value.create_score_df(version=["1.10.0", "1.9.0"]).columns.to_list() == ["1.10.0", "1.9.0"]
    assert value.get_scores("1.10.0", group="intra").to_dict() == {"a": 9.}


def test_simplify_v_prefixes_keeps_last_occurrence_without_changing_source():
    value = _man(history={"v1.0.0": _result(7), "1.0.0": _result(8), "v1.1.0": _result(9)})
    before = value.model_dump_json()
    simplified = value.simplify_history()
    assert list(simplified.history) == ["1.0.0", "1.1.0"]
    assert simplified.history["1.0.0"].get_score().total == 8
    assert simplified.history["1.1.0"].get_score().total == 9
    assert value.model_dump_json() == before


@pytest.mark.parametrize("representation", ["new-vectors", "new-rows", "legacy-rows"])
def test_history_splits_preserve_samples_and_assign_shared_boundary_to_later_element(representation):
    rows = [{"t": t, "dt": 1, "x": 10 * t, "y": 0, "z": 20,
             "rw": 1, "rx": 0, "ry": 0, "rz": 0} for t in range(4)]
    flown = (LegacyState.model_validate(rows) if representation == "legacy-rows" else
             NewState(t=[0, 1, 2, 3], data=LegacyState.model_validate(rows)) if representation == "new-rows" else
             NewState(t=[0, 1, 2, 3], pos={"x": [0, 10, 20, 30], "y": [0] * 4, "z": [20] * 4}))
    man = _man(flown=flown)
    before = man.model_dump_json()
    result = man.splits_from_version("Latest")
    if isinstance(result, NewState):
        assert result.t == [0, 1, 2, 3]
        labels = result.labels.root["element"].root
        assert (labels["entry"].start, labels["entry"].stop) == (0, 1)
        assert (labels["loop"].start, labels["loop"].stop) == (1, 3)
        if result.data is None:
            assert result.pos == flown.pos
        else:
            assert result.df().element.tolist() == ["entry", "loop", "loop", "loop"]
    else:
        assert result.df().element.tolist() == ["entry", "loop", "loop", "loop"]
        assert result.df().x.tolist() == [0, 10, 20, 30]
    assert man.model_dump_json() == before
    with pytest.raises(AssertionError, match="not found in history"):
        man.splits_from_version("absent")


def _downgrade():
    return {"measurement": {"unit": "rad"},
            "criteria": {"name": "angle", "kind": "Deviation", "lookup": {"factor": 2, "exponent": 1}},
            "errors": [.1, .2], "dgs": [.2, .4]}


@pytest.mark.parametrize("group", ["intra", "inter", "positioning", "all"])
def test_downgrade_summary_retains_independent_units_criteria_values_and_group(group):
    scores = {kind: {"data": {kind + "_angle": _downgrade()}} for kind in ("intra", "inter", "positioning")}
    man = _man(scores=copy.deepcopy(scores))
    before = man.model_dump_json()
    summary = man.summarise_dgs(group)
    groups = [group] if group != "all" else ["intra", "inter", "positioning"]
    assert summary.kind.tolist() == [kind for kind in groups for _ in range(2)]
    assert summary.downgrade.tolist() == [kind + "_angle" for kind in groups for _ in range(2)]
    np.testing.assert_allclose(summary.error, [.1, .2] * len(groups), rtol=0, atol=0)
    np.testing.assert_allclose(summary.dg, [.2, .4] * len(groups), rtol=0, atol=0)
    assert set(summary.unit) == {"rad"} and set(summary.criteria) == {"angle"}
    assert set(summary.criteria_kind) == {"Deviation"} and set(summary.factor) == {2}
    assert set(summary.exponent) == {1} and set(summary.manoeuvre) == {"a"} and set(summary.k) == {3}
    ajson = AJson(isComp=False, mans=[man, _man("b", scores=scores)])
    combined = ajson.summarise_dgs(group)
    assert len(combined) == 2 * len(summary) and set(combined.manoeuvre) == {"a", "b"}
    assert ajson.is_full
    assert man.model_dump_json() == before


@pytest.mark.parametrize("kind", ["intra", "inter", "positioning"])
def test_missing_scores_are_rejected_and_empty_group_has_no_downgrade_rows(kind):
    with pytest.raises(ValueError, match="No scores available"):
        getattr(_man(scores=None), f"summarise_{kind}_dgs")()
    empty = _man(scores={kind: {"data": {}}})
    assert getattr(empty, f"summarise_{kind}_dgs")().empty
