from pfcschemas import fcj
from pathlib import Path


def test_validate():
    _fcj = fcj.FCJ.model_validate_json(Path("tests/data/fc_json.json").open().read())

    assert isinstance(_fcj, fcj.FCJ)