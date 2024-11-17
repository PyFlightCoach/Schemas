from pytest import fixture
from schemas import MA
from pathlib import Path
from json import load

@fixture(scope="session")
def ma_dict():
    return load(Path("tests/data/flight.ajson").open())['mans'][0]


def test_ma_validate(ma_dict):
    man = MA.model_validate(ma_dict)
    assert isinstance(man, MA)