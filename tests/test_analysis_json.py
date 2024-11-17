from schemas import AJson
from schemas import MA
from pytest import fixture, mark


@fixture
def ajson_basic():
    return AJson.model_validate_json(open('tests/data/analysis_json_basic.json', 'r').read())


@fixture
def ajson_full():
    return AJson.model_validate_json(open('tests/data/analysis_json_full.json', 'r').read())

@mark.skip("no input data")
def test_ajson_basic(ajson_basic: AJson):
    assert ajson_basic.sourceBin is None
    assert isinstance(ajson_basic.mans[0], MA)

@mark.skip("no input data")
def test_ajson_full(ajson_full: AJson):
    assert ajson_full.mans[0].mdef['info']['short_name'] == 'sLoop'
    assert ajson_full.tStart == ajson_full.flown[0].time    

    #ajson_full.mans[0].flown['data'][0]['t']

#def test_sa_parse_ajson_basic(ajson_basic: AJson):
#    sa = ScheduleAnalysis.parse_dict(ajson_basic)
#    assert isinstance(sa, ScheduleAnalysis)
#
#def test_sa_parse_ajson_full(ajson_full: AJson):
#    sa = ScheduleAnalysis.parse_ajson(ajson_full)
#    assert isinstance(sa, ScheduleAnalysis)
#    assert len(sa) == 17
#    assert isinstance(sa[0].mdef, ManDef)
    