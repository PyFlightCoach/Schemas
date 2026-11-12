"""MA.schedule_direction stores a Heading name and must survive a JSON round trip."""

import json

import pytest
from pydantic import ValidationError

from schemas import MA
from schemas.positioning import Heading


def _man(schedule_direction=None, **extra):
    data = dict(
        name="m",
        id=1,
        schedule=dict(category="f3a", name="p25"),
        flown=dict(t=[0.0, 0.1]),
        **extra,
    )
    if schedule_direction is not ...:
        data["schedule_direction"] = schedule_direction
    return data


@pytest.mark.parametrize("name", ["LTOR", "RTOL"])
def test_schedule_direction_round_trips(name):
    man = MA.model_validate(_man(name))
    assert man.schedule_direction is Heading[name]

    dumped = man.model_dump_json(exclude_none=True, exclude_unset=True)
    assert json.loads(dumped)["schedule_direction"] == name

    again = MA.model_validate_json(dumped)
    assert again.schedule_direction is Heading[name]
    assert again.model_dump()["schedule_direction"] == name


@pytest.mark.parametrize("heading", [Heading.LTOR, Heading.RTOL])
def test_schedule_direction_accepts_heading(heading):
    assert MA.model_validate(_man(heading)).schedule_direction is heading


@pytest.mark.parametrize("value", [None, "", "Infer", ...])
def test_schedule_direction_inferred_values_load_as_none(value):
    man = MA.model_validate(_man(value))
    assert man.schedule_direction is None
    assert "schedule_direction" not in json.loads(
        man.model_dump_json(exclude_none=True)
    )


@pytest.mark.parametrize(
    "value", ["UPWIND", "DOWNWIND", "OUTTOIN", Heading.INTOOUT, "ltor", 0.0]
)
def test_schedule_direction_rejects_other_values(value):
    with pytest.raises(ValidationError):
        MA.model_validate(_man(value))


def test_basic_keeps_schedule_direction():
    man = MA.model_validate(_man("RTOL"))
    assert man.basic().schedule_direction is Heading.RTOL
