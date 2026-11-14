"""File, enum and omitted-default contracts independent of recorded flights."""

import json
import math

import pytest
from pydantic import ValidationError

from schemas.base import CustomBaseModel
from schemas.positioning import BoxLocation, Direction, Heading, Height, r
from schemas.utils.files import validate_json


def test_json_dictionary_and_path_inputs_preserve_content(tmp_path):
    expected = {"name": "loop", "values": [1, None, {"angle": 2.5}]}
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(expected))
    assert validate_json(expected) is expected
    assert validate_json(path) == expected
    assert validate_json(str(path)) == expected
    assert json.loads(path.read_text()) == expected


def test_json_parse_and_missing_file_errors_are_explicit(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"unfinished":')
    with pytest.raises(json.JSONDecodeError):
        validate_json(path)
    with pytest.raises(FileNotFoundError):
        validate_json(tmp_path / "absent.json")


@pytest.mark.parametrize("value", [None, [], 1, b"{}", object()])
def test_json_rejects_unsupported_input_types(value):
    with pytest.raises(ValueError, match="expected a dict, str or os.PathLike"):
        validate_json(value)


class NestedDefaults(CustomBaseModel):
    name: str
    location: BoxLocation = BoxLocation()
    heading: Heading | None = None


def test_nested_default_omission_has_an_explicit_override_and_round_trips():
    value = NestedDefaults(name="loop")
    assert value.model_dump() == {"name": "loop"}
    assert json.loads(value.model_dump_json()) == {"name": "loop"}
    assert value.model_dump(exclude_defaults=False) == {
        "name": "loop", "location": {"height": None, "direction": None, "orientation": None},
        "heading": None,
    }
    changed = NestedDefaults(name="loop", location=BoxLocation(height=Height.TOP), heading=Heading.RTOL)
    expected = {"name": "loop", "location": {"height": "TOP"}, "heading": "RTOL"}
    assert changed.model_dump() == expected
    assert json.loads(changed.model_dump_json()) == expected
    assert NestedDefaults.model_validate(expected) == changed


@pytest.mark.parametrize("heading", list(Heading))
def test_heading_enum_preserves_member_identity_and_serializes_names(heading):
    value = NestedDefaults(name="x", heading=heading)
    assert value.heading is heading
    assert NestedDefaults.model_validate_json(value.model_dump_json()).heading is heading
    assert value.model_dump()["heading"] == heading.name


@pytest.mark.parametrize("value", [0, 0.0, [], {}, True])
def test_enum_numeric_values_and_other_non_names_are_not_wire_names(value):
    with pytest.raises(ValidationError, match="Unexpected type"):
        NestedDefaults(name="x", heading=value)


def test_unknown_generic_enum_name_uses_the_legacy_nullable_sentinel():
    # EnumStr historically returns None for unknown names; MA adds a stricter
    # heading validator. Keep the generic layer's compatibility visible.
    assert NestedDefaults(name="x", heading="unknown").heading is None


@pytest.mark.parametrize("heading", list(Heading))
@pytest.mark.parametrize("turns", [-2, 0, 3])
def test_heading_inference_is_invariant_under_complete_turns(heading, turns):
    assert Heading.infer(heading.value + turns * 2 * math.pi) is heading
    assert heading.reverse().reverse() is heading


@pytest.mark.parametrize("text, expected", [
    ("upwind", Direction.UPWIND), ("DOWN", Direction.DOWNWIND), ("Cross", Direction.CROSS),
])
def test_direction_text_and_wind_reversal(text, expected):
    assert Direction.parse(text) is expected
    wind = Heading.LTOR
    result = expected.wind_swap_heading(wind)
    assert result is (Heading.RTOL if expected is Direction.DOWNWIND else Heading.LTOR)


def test_invalid_direction_and_turn_conversion():
    with pytest.raises(ValueError, match="Invalid wind"):
        Direction.parse("invalid")
    assert r(0.5) == pytest.approx(math.pi)
    assert r([0, -0.25, 1]) == pytest.approx([0, -math.pi / 2, 2 * math.pi])
