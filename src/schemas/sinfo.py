from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from schemas import Direction

fcj_categories = {
    "F3A FAI": "f3a",
    "F3A": "f3a",
    "US AMA": "ama",
    "F3A UK": "f3auk",
    "F3A US": "ama",
    "IMAC": "IMAC",
}

fcj_schedules = {
    "P23": "p23",
    "F23": "f23",
    "P25": "p25",
    "F25": "f25",
    "Unlimited 2024": "unlimited2024",
    "Intermediate 24": "intermediate2024",    
}


def lookup(val, data):
    val = val.replace("_", " ")
    return data[val] if val in data else val


@dataclass
class ManDetails:
    name: str
    id: int
    k: float
    entry: Literal["UPWIND", "DOWNWIND", "CROSS"]

    @staticmethod
    def parse(m, i: int):
        _m = m[0] if isinstance(m, list) else m

        return ManDetails(
            _m["info"]["short_name"],
            i + 1,
            _m["info"]["k"],
            Direction.parse(_m["info"]["start"]["direction"]),
        )


@dataclass
class ScheduleInfo:
    category: str
    name: str

    @staticmethod
    def from_str(fname):
        info = fname.split('.')[0].split("_")
        if len(info) == 1:
            return ScheduleInfo("f3a", info[0])
        else:
            return ScheduleInfo(info[0], info[1])

    def __str__(self):
        return f"{self.category}_{self.name}"
    
    @staticmethod
    def lookupCategory(category):
        return lookup(category, fcj_categories)

    @staticmethod
    def lookupSchedule(schedule):
        return lookup(schedule, fcj_schedules)

    @staticmethod
    def mixed():
        return ScheduleInfo("na", "mixed")

    def fcj_to_pfc(self):
        sinfo = ScheduleInfo(
            lookup(self.category, fcj_categories), lookup(self.name, fcj_schedules)
        )
        if sinfo.category == "ama" and sinfo.name == "Advanced 24":
            sinfo = ScheduleInfo("f3a", "a25")
        return sinfo

    def pfc_to_fcj(self):
        def rev_lookup(val, data):
            return (
                next(k for k, v in data.items() if v == val)
                if val in data.values()
                else val
            )

        return ScheduleInfo(
            rev_lookup(self.category, fcj_categories),
            rev_lookup(self.name, fcj_schedules),
        )

    @staticmethod
    def from_fcj_sch(sch):
        return ScheduleInfo(*sch).fcj_to_pfc()

    def to_fcj_sch(self):
        return list(self.pfc_to_fcj().__dict__.values())

    @staticmethod
    def build(category, name):
        return ScheduleInfo(category.lower(), name.lower())

    def __eq__(self, other: ScheduleInfo):
        return str(self.fcj_to_pfc()) == str(other.fcj_to_pfc())
