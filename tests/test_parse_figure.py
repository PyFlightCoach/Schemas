import pytest
from schemas import Figure, ManInfo, Option, line, parse_figure


def _figure():
    return Figure(
        info=ManInfo.model_validate({"name": "Top Hat", "short_name": "tHat", "k": 3.0, "position": "END",
                                     "start": {"height": "BTM", "direction": "UPWIND", "orientation": "UPRIGHT"},
                                     "end": {"height": "BTM"}}),
        elements=[line()], ndmps={})


def test_parse_single_figure():
    fig = _figure()
    assert isinstance(parse_figure(fig.model_dump(mode="json")), Figure)


def test_parse_option_payload():
    fig = _figure()
    parsed = parse_figure({"figures": [fig.model_dump(mode="json")] * 2})
    assert isinstance(parsed, Option) and len(parsed.figures) == 2


def test_parse_invalid_still_raises():
    with pytest.raises(Exception):
        parse_figure({"elements": []})


def test_heights_default_none_and_old_payload_valid():
    payload = _figure().model_dump(mode="json")
    payload.pop("heights", None)
    assert parse_figure(payload).heights is None


def test_heights_round_trip():
    from schemas import Height, HeightPair

    pairs = [
        HeightPair(entry=Height.BTM, exit=Height.MID, awkward=True, cost=1.5,
                   values={"ndmps.loop_radius": 40.0}, combination={"dir": 1}, out_of_box=0.5),
        HeightPair(entry=Height.MID, exit=Height.MID),
    ]
    fig = _figure().model_copy(update={"heights": pairs})
    data = fig.model_dump(mode="json")
    assert data["heights"][0]["entry"] == "BTM"
    back = parse_figure(data)
    assert back.heights == pairs
    assert back.heights[1].values == {} and back.heights[1].out_of_box == 0.0
    opt = parse_figure({"figures": [data, data]})
    assert isinstance(opt, Option) and opt.figures[1].heights == pairs
    # at_position keeps the pairs
    assert fig.at_position(None).heights == pairs


def test_heights_source_default_none_and_round_trip():
    from schemas import Height, HeightPair, HeightsSource

    payload = _figure().model_dump(mode="json")
    payload.pop("heights_source", None)
    assert parse_figure(payload).heights_source is None
    source = HeightsSource(figure="f" * 16, deriver="1-abc")
    fig = _figure().model_copy(update={"heights": [HeightPair(entry=Height.BTM, exit=Height.BTM)],
                                       "heights_source": source})
    data = fig.model_dump(mode="json")
    assert data["heights_source"] == {"figure": "f" * 16, "deriver": "1-abc"}
    back = parse_figure(data)
    assert back.heights_source == source
    assert fig.at_position(None).heights_source == source
