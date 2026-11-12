import pytest

from schemas.ajson import AJson
from schemas.fcj import ManResult, Score, ScoreProperties, ScoreValues
from schemas.flightdata import NewState
from schemas.ma import MA
from schemas.sinfo import ScheduleInfo


def _man(name: str, k: float, totals: dict[str, float]) -> MA:
    history = {
        version: ManResult.model_validate({"els": [], "results": [
            Score.model_validate({
                "score": ScoreValues(
                    intra=total, inter=0.0, positioning=0.0, total=total
                ),
                "properties": ScoreProperties(difficulty=3, truncate=False),
            })
        ]})
        for version, total in totals.items()
    }
    return MA.model_validate(
        {
            "name": name,
            "id": 1,
            "schedule": ScheduleInfo(category="f3a", name="p25"),
            "flown": NewState.model_validate({"t": [0.0]}),
            "history": history,
            "mdef": {"info": {"k": k}},
        }
    )


def _ajson(*mans: MA) -> AJson:
    return AJson.model_validate({"isComp": False, "mans": list(mans)})


def test_ajson_latest_and_k_factored_totals_use_semantic_versions():
    history = _ajson(
        _man("K2", 2, {"1.9.0": 8, "1.10.0": 9}),
        _man("K3", 3, {"1.9.0": 7, "1.10.0": 6}),
    )

    assert history.latest_version() == "1.10.0"
    # Hand calculation: 8*2 + 7*3 = 37; 9*2 + 6*3 = 36.
    assert history.total_score(version="1.9.0").loc["1.9.0"] == 37
    assert history.total_score(version="1.10.0").loc["1.10.0"] == 36
    assert history.total_score(version="All").to_dict() == {
        "1.9.0": 37,
        "1.10.0": 36,
    }
    assert history.total_score(version="Latest").iloc[0] == 36


def test_ajson_missing_version_policies():
    history = _ajson(_man("only-old", 2, {"1.9.0": 8}))

    with pytest.raises(ValueError, match="Version 1.10.0 not found in manoeuvre"):
        history.get_scores("1.10.0")

    assert history.get_scores("1.10.0", missing="zero").to_dict() == {"only-old": 0}
    assert history.get_scores("1.10.0", missing="nan").isna().to_dict() == {
        "only-old": True
    }


def test_ma_score_property_returns_latest_real_score_values():
    man = _man("K2", 2, {"1.9.0": 8, "1.10.0": 9})

    assert man.latest_version == "1.10.0"
    assert man.score.total == 9


def test_ma_k_factored_latest_uses_semantic_latest():
    man = _man("K2", 2, {"1.9.0": 8, "1.10.0": 9})

    assert man.k_factored_score(version="1.10.0") == 18
    assert man.k_factored_score(version="Latest") == 18


def test_ma_rename_version_copies_history_without_mutating_source():
    man = _man("K2", 2, {"1.9.0": 8, "1.10.0": 9})

    renamed = man.rename_version("1.9.0", "1.8.9")

    assert "1.9.0" in man.history
    assert "1.8.9" not in man.history
    assert "1.9.0" not in renamed.history
    assert renamed.history["1.8.9"].get_score(ScoreProperties()).total == 8
    assert renamed.history is not man.history
