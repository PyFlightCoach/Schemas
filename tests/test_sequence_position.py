"""ManInfo.sequence_position and the helpers that set it from a figure's place in a sequence."""

import pytest

from schemas import ManInfo, aresti, sequence_position
from schemas.positioning import BoxLocation, Direction, Height, Orientation, Position
from schemas.sdef import MDef


def info(name="loop", **kwargs):
    return ManInfo.build(
        name.title(), name, 3, Position.CENTRE,
        BoxLocation.build(Height.BTM, Direction.UPWIND, Orientation.UPRIGHT),
        BoxLocation.build(Height.MID, Direction.DOWNWIND),
        **kwargs,
    )


def fig(name):
    return aresti.figure(info(name), [aresti.line("a", length=1)])


@pytest.mark.parametrize(
    ("index", "count", "expected"),
    [(0, 1, "only"), (0, 2, "first"), (1, 2, "last"), (0, 3, "first"), (1, 3, None), (2, 3, "last")],
)
def test_sequence_position_by_index(index, count, expected):
    assert sequence_position(index, count) == expected


@pytest.mark.parametrize(("index", "count"), [(-1, 3), (3, 3), (0, 0)])
def test_sequence_position_rejects_an_index_outside_the_sequence(index, count):
    with pytest.raises(ValueError):
        sequence_position(index, count)


def test_missing_position_means_interior_and_is_not_serialised():
    # stored definitions of interior figures and of other rule sets keep their old shape
    assert "sequence_position" not in info().to_dict()
    assert ManInfo.from_dict(info().to_dict()).sequence_position is None


@pytest.mark.parametrize("position", ["first", "last", "only"])
def test_position_survives_a_dict_and_json_round_trip(position):
    original = info(sequence_position=position)

    assert original.to_dict()["sequence_position"] == position
    assert ManInfo.from_dict(original.to_dict()).sequence_position == position
    assert ManInfo.model_validate_json(original.model_dump_json()).sequence_position == position


def test_position_survives_a_stored_definition_round_trip():
    mdef = MDef(info=info(sequence_position="last"), mps={}, eds={}, box={})

    assert MDef.model_validate_json(mdef.model_dump_json()).info.sequence_position == "last"


def test_old_stored_info_without_the_field_still_loads():
    old = {"name": "Loop", "short_name": "loop", "k": 3}

    assert ManInfo.from_dict(old).sequence_position is None


def test_invalid_position_is_rejected():
    with pytest.raises(ValueError):
        info(sequence_position="middle")


def test_figure_at_position_copies_and_leaves_the_original():
    f = fig("a")

    placed = f.at_position("first")

    assert placed.info.sequence_position == "first"
    assert f.info.sequence_position is None
    assert placed.elements == f.elements


def test_option_at_position_places_every_figure():
    opt = aresti.option([fig("a"), fig("b")])

    placed = opt.at_position("last")

    assert [f.info.sequence_position for f in placed.figures] == ["last", "last"]
    assert [f.info.sequence_position for f in opt.figures] == [None, None]


def test_sequence_positioned_marks_first_and_last_and_clears_stale_positions():
    seq = aresti.sequence(
        "seq", "imac", [fig("a").at_position("last"), aresti.option([fig("b")]), fig("c"), fig("d")]
    )

    positions = [f.info.sequence_position for f in seq.positioned().figures]

    assert positions == ["first", None, None, "last"]
    # the original sequence is not modified
    assert seq.figures[0].info.sequence_position == "last"


def test_sequence_of_one_figure_is_only():
    seq = aresti.sequence("seq", "imac", [fig("a")])

    assert seq.positioned().figures[0].info.sequence_position == "only"
