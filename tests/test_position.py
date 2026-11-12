from math import pi

from schemas.positioning import BoxLocation, Direction, Heading, Height, Orientation


def test_enumstr():
    h = Height.MID
    assert h == Height.MID
    assert h.value == 0.6


def test_heading_infer_cardinal_bearings():
    assert Heading.infer(pi / 2) is Heading.INTOOUT
    assert Heading.infer(3 * pi / 2) is Heading.OUTTOIN


def test_boxloc_serialize():
    bloc = BoxLocation(height=Height.MID, direction=Direction.UPWIND, orientation=None)

    bloc_dict = bloc.model_dump()

    assert bloc_dict == {"height": "MID", "direction": "UPWIND"}

    bloc_parsed = BoxLocation.model_validate_json(bloc.model_dump_json())

    assert bloc == bloc_parsed
    assert bloc_parsed.orientation is None


def test_boxloc_serialize_retains_nondefault_orientation():
    bloc = BoxLocation(
        height=Height.MID,
        direction=Direction.UPWIND,
        orientation=Orientation.UPRIGHT,
    )

    bloc_dict = bloc.model_dump()

    assert bloc_dict == {
        "height": "MID",
        "direction": "UPWIND",
        "orientation": "UPRIGHT",
    }

    bloc_parsed = BoxLocation.model_validate_json(bloc.model_dump_json())

    assert bloc_parsed == bloc
    assert bloc_parsed.orientation is Orientation.UPRIGHT
