from schemas.positioning import BoxLocation, Height, Direction


def test_enumstr():
    h = Height.MID
    assert h == Height.MID
    assert h.value == 0.6


def test_boxloc_serialize():
    bloc = BoxLocation(height=Height.MID, direction=Direction.UPWIND, orientation=None)

    bloc_dict = bloc.model_dump()

    assert bloc_dict["height"] == "MID"
    assert bloc_dict["direction"] == "UPWIND"
    assert bloc_dict["orientation"] is None



    bloc_parsed = BoxLocation.model_validate_json(bloc.model_dump_json())

    assert bloc == bloc_parsed
