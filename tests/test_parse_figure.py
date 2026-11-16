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
