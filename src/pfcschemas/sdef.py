from flightanalysis import SchedDef
from pydantic import BaseModel

from pfcschemas.sinfo import ScheduleInfo


class DirectionDefinition(BaseModel):
    manid: int
    direction: str

    @staticmethod
    def from_sdef(sdef: SchedDef):
        manid = sdef.wind_def_manoeuvre()
        return DirectionDefinition(
            manid=manid, direction=sdef[manid].info.start.direction.name
        )


class SDefFile(BaseModel):
    category: str
    schedule: str
    direction_definition: DirectionDefinition
    fa_version: str
    mdefs: dict[str, dict | list[dict]]

    @property
    def sinfo(self):
        return ScheduleInfo(self.category, self.schedule)

    def create_definition(self):
        return SchedDef.from_dict(self.mdefs)
