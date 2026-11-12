"""New and legacy FlightData schema variant serialization contracts."""

import pandas as pd
import pytest
from pydantic import ValidationError

from schemas.flightdata import LegacyState, NewState, State


def test_new_state_json_round_trip_preserves_time_and_vectors():
    value = NewState.model_validate(
        {
            "t": [0.0, 0.25],
            "pos": {
                "x": [1.0, 2.0],
                "y": [-3.0, -4.0],
                "z": [5.5, 6.5],
            },
            "att": {
                "w": [1.0, 0.0],
                "x": [0.0, 1.0],
                "y": [0.0, 0.0],
                "z": [0.0, 0.0],
            },
            "vel": {"x": [4.0, 4.0], "y": [0.0, 1.0], "z": [-2.0, -2.0]},
            "labels": {
                "element": {
                    "loop": {"start": 0.0, "stop": 0.25},
                },
            },
            "data": None,
        }
    )

    restored = NewState.model_validate_json(value.model_dump_json())

    assert restored == value
    assert restored.t == [0.0, 0.25]
    assert restored.pos.model_dump() == {
        "x": [1.0, 2.0], "y": [-3.0, -4.0], "z": [5.5, 6.5]
    }
    assert restored.att.model_dump() == {
        "w": [1.0, 0.0], "x": [0.0, 1.0], "y": [0.0, 0.0], "z": [0.0, 0.0]
    }
    assert restored.labels.root["element"].root["loop"].start == 0.0
    assert restored.labels.root["element"].root["loop"].stop == 0.25
    assert restored.data is None


def test_legacy_state_dataframe_conversion_preserves_rows_and_nullable_fields():
    rows = [
        {
            "t": 0.0, "dt": 0.25,
            "x": 1.0, "y": -3.0, "z": 5.5,
            "rw": 1.0, "rx": 0.0, "ry": 0.0, "rz": 0.0,
            "u": 4.0, "v": 0.0, "w": -2.0,
            "p": 0.0, "q": 0.0, "r": 1.5,
            "du": None, "dv": None, "dw": None,
            "manoeuvre": "loop", "element": "e_0",
        },
        {
            "t": 0.25, "dt": 0.25,
            "x": 2.0, "y": -4.0, "z": 6.5,
            "rw": 0.0, "rx": 1.0, "ry": 0.0, "rz": 0.0,
            "u": 4.0, "v": 1.0, "w": -2.0,
            "p": 0.0, "q": 0.0, "r": 1.5,
            "du": None, "dv": None, "dw": None,
            "manoeuvre": "loop", "element": "e_0",
        },
    ]
    expected = pd.DataFrame(rows)

    state = LegacyState.parse_df(expected)
    restored = LegacyState.model_validate_json(state.model_dump_json())

    assert restored == state
    pd.testing.assert_frame_equal(restored.df(), expected)
    assert restored.df().loc[1, ["t", "x", "y", "z", "rx"]].tolist() == [
        0.25, 2.0, -4.0, 6.5, 1.0
    ]
    assert restored.df().loc[0, ["du", "dv", "dw"]].isna().all()


def test_state_union_accepts_each_documented_wire_shape_and_rejects_incomplete_rows():
    legacy_wire = [
        {
            "t": 0.0, "dt": 0.5,
            "x": 1.0, "y": 2.0, "z": 3.0,
            "rw": 1.0, "rx": 0.0, "ry": 0.0, "rz": 0.0,
        }
    ]
    new_wire = {"t": [0.0, 0.5], "pos": {"x": [1.0, 2.0], "y": [2.0, 3.0], "z": [3.0, 4.0]}}

    legacy = State.model_validate(legacy_wire)
    new = State.model_validate(new_wire)

    assert isinstance(legacy.root, LegacyState)
    assert isinstance(new.root, NewState)
    assert State.model_validate_json(legacy.model_dump_json()) == legacy
    assert State.model_validate_json(new.model_dump_json()) == new
    with pytest.raises(ValidationError):
        LegacyState.model_validate([{"t": 0.0, "dt": 0.5, "x": 1.0}])
