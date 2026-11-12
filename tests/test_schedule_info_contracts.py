"""ScheduleInfo wire, FCJ conversion, and identifier contracts."""

import json
from pathlib import Path

from schemas import AJson, FCJ, MA, ScheduleInfo
from schemas.flightdata import NewState


def _ma(schedule):
    return MA(
        name="loop",
        id=1,
        schedule=schedule,
        flown=NewState(t=[0.0, 1.0]),
        history={},
    )


def test_schedule_info_round_trips_through_ma_json_as_literal_fields():
    original = ScheduleInfo(category="f3a", name="p25")
    value = _ma(original)

    wire = value.model_dump_json()
    assert json.loads(wire)["schedule"] == {"category": "f3a", "name": "p25"}

    restored = MA.model_validate_json(wire)
    assert restored.schedule == original
    assert str(restored.schedule) == "f3a_p25"


def test_repository_fcj_fixture_schedule_normalizes_and_emits_canonical_legacy_pair():
    fixture = Path(__file__).parent / "data" / "fc_json.json"
    fcj = FCJ.model_validate_json(fixture.read_text())

    assert fcj.parameters.schedule == ["F3A FAI", "P25"]
    normalized = ScheduleInfo.from_fcj_sch(fcj.parameters.schedule)
    assert normalized.__dict__ == {"category": "f3a", "name": "p25"}
    assert normalized.to_fcj_sch() == ["F3A FAI", "P25"]
    assert normalized == ScheduleInfo(category="F3A FAI", name="P25")


def test_schedule_identifier_parser_handles_legacy_default_and_explicit_category():
    assert ScheduleInfo.from_str("p25") == ScheduleInfo("f3a", "p25")
    assert ScheduleInfo.from_str("f3a_p25") == ScheduleInfo("f3a", "p25")


def test_ajson_multiple_schedule_listing_parses_generated_identifiers():
    ajson = AJson(
        isComp=False,
        mans=[
            _ma(ScheduleInfo("f3a", "p25")),
            _ma(ScheduleInfo("f3a", "f25")),
        ],
    )

    schedules = ajson.schedule(allow_multiple=True)

    assert {str(schedule) for schedule in schedules} == {"f3a_p25", "f3a_f25"}
