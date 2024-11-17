
from pydantic import BaseModel

from schemas.sinfo import ScheduleInfo
from schemas.positioning import Direction
from schemas.maninfo import ManInfo

class MDef(BaseModel):
    info: ManInfo
    mps: dict
    eds: dict
    box: dict


class MOption(BaseModel):
    options: list[MDef]
    active: int = 0

    @property
    def uid(self):
        return self.options[0].info.short_name

    @property
    def info(self):
        return self.options[self.active].info

    @property
    def mps(self):
        return self.options[self.active].mps

    @property
    def eds(self):
        return self.options[self.active].eds

    def __iter__(self):
        for mdef in self.options:
            yield mdef


class DirectionDefinition(BaseModel):
    manid: int
    direction: Direction


class SDefFile(BaseModel):
    category: str
    schedule: str
    direction_definition: DirectionDefinition
    fa_version: str
    mdefs: dict[str, dict | list[dict]]

    @property
    def sinfo(self):
        return ScheduleInfo(self.category, self.schedule)

