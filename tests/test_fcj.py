from schemas import fcj
from pathlib import Path


def test_validate():
    _fcj = fcj.FCJ.model_validate_json((Path(__file__).parent / "data/fc_json.json").open().read())

    assert isinstance(_fcj, fcj.FCJ)