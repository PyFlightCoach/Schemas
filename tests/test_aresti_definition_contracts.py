"""Aresti primitives, alternatives and schedule-definition wire contracts."""

import copy

import pytest
from pydantic import ValidationError

from schemas import ManInfo
from schemas import aresti
from schemas.positioning import BoxLocation, Direction, Height, Orientation, Position
from schemas.sdef import DirectionDefinition, MDef, MOption, SDefFile


def info(name="loop", k=3):
    return ManInfo.build(
        name.title(), name, k, Position.CENTRE,
        BoxLocation.build(Height.BTM, Direction.UPWIND, Orientation.UPRIGHT),
        BoxLocation.build(Height.MID, Direction.DOWNWIND),
        centre_points=[1], centred_els=[(2, .5)],
    )


@pytest.mark.parametrize("kind", ["line", "roll", "loop", "snap", "spin", "stallturn", "tailslide"])
def test_primitive_helpers_preserve_args_kwargs_and_json(kind):
    primitive = getattr(aresti, kind)("amount", rate=2)
    expected = {"kind": kind, "args": ["amount"], "kwargs": {"rate": 2}}
    assert primitive.model_dump() == expected
    assert aresti.PE.model_validate_json(primitive.model_dump_json()) == primitive
    assert str(primitive) == f"{kind}(amount, rate=2)"
    centred = aresti.centred(primitive)
    assert centred.centred and not primitive.centred
    assert str(centred) == f"centred({kind}(amount, rate=2))"


def test_invalid_primitive_kind_and_missing_metadata_are_rejected():
    with pytest.raises(ValidationError):
        aresti.PE.build("unsupported", [], {})
    with pytest.raises(ValidationError):
        aresti.Figure.model_validate({"elements": [], "ndmps": {}})


def test_maninfo_builder_retains_centre_metadata_and_wire_enums():
    value = info()
    wire = value.to_dict()
    assert wire["position"] == "CENTRE"
    assert wire["start"] == {"height": "BTM", "direction": "UPWIND", "orientation": "UPRIGHT"}
    assert wire["end"] == {"height": "MID", "direction": "DOWNWIND"}
    assert wire["centre_points"] == [1] and wire["centred_els"] == [(2, .5)]
    assert ManInfo.from_dict(wire) == value
    left, right = ManInfo(name="a", short_name="a"), ManInfo(name="b", short_name="b")
    left.centre_points.append(7)
    left.start.height = Height.TOP
    assert right.centre_points == [] and right.start.height is None


def test_figure_option_and_sequence_lookup_use_explicit_names_and_k_factors():
    first = aresti.figure(info("a", 2), [aresti.line(), aresti.centred(aresti.loop("r"))],
                          relax_back=True, options={"category": "Advanced"}, radius=35)
    second = aresti.figure(info("b", 5), [aresti.roll("half")])
    alternative = aresti.option([second, second.model_copy(deep=True)])
    seq = aresti.sequence("test", "IAC", [first, alternative], options={"year": "2026"})
    assert seq[0] is first and seq["a"] is first
    assert seq[1] is alternative and seq["b"] is alternative
    assert seq.k_factors == {"a": 2, "b": 5}
    assert seq.builder_options == {"category": "Advanced"}
    assert alternative.info == second.info and alternative.builder_options == second.builder_options
    assert first.ndmps == {"radius": 35} and first.relax_back
    assert first.elements[1].centred
    assert aresti.Sequence.model_validate_json(seq.model_dump_json()) == seq
    with pytest.raises(KeyError, match="Figure missing not found"):
        seq["missing"]
    with pytest.raises(IndexError):
        seq[4]


def test_definition_options_select_info_parameters_and_elements_without_mutating_inputs():
    left = MDef(info=info("a", 2), mps={"radius": 30}, eds={"e0": {"kind": "loop"}}, box={})
    right = MDef(info=info("b", 4), mps={"radius": 50}, eds={"e0": {"kind": "line"}}, box={})
    before = copy.deepcopy([left.model_dump(), right.model_dump()])
    alternatives = MOption(options=[left, right], active=1)
    assert alternatives.uid == "a"
    assert alternatives.info == right.info
    assert alternatives.mps == {"radius": 50}
    assert alternatives.eds == {"e0": {"kind": "line"}}
    assert list(alternatives) == [left, right]
    assert MOption.model_validate_json(alternatives.model_dump_json()) == alternatives
    assert [left.model_dump(), right.model_dump()] == before
    schedule = SDefFile(category="f3a", schedule="p27", fa_version="1.2.3", mdefs={"a": left.model_dump(mode="json")})
    assert str(schedule.sinfo) == "f3a_p27"
    assert SDefFile.model_validate_json(schedule.model_dump_json()) == schedule
    direction = DirectionDefinition(manid=3, direction=Direction.DOWNWIND)
    assert direction.model_dump() == {"manid": 3, "direction": "DOWNWIND"}
