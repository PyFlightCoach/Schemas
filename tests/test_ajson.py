from pfcschemas import ajson
from pathlib import Path


def test_validate():
    _ajson = ajson.AJson.model_validate_json(Path("tests/data/flight.ajson").open().read())

    assert isinstance(_ajson, ajson.AJson)