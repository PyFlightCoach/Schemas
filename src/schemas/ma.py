from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from schemas import fcj, ScheduleInfo, Direction


class MA(BaseModel):
    name: str
    id: int
    schedule: ScheduleInfo
    schedule_direction: Direction | None
    flown: list[dict] | dict

    history: dict[str, fcj.ManResult] | None = None

    mdef: dict | None = None
    manoeuvre: dict | None = None
    template: list[dict] | dict | None = None
    corrected: dict | None = None
    corrected_template: list[dict] | dict | None = None
    scores: dict | None = None

    def basic(self):
        return MA(
            name=self.name,
            id=self.id,
            schedule=self.schedule,
            schedule_direction=self.schedule_direction,
            flown=self.flown,
            history=self.history,
        )

    def simplify_history(self):
        vnames = [v[1:] if v.startswith("v") else v for v in self.history.keys()]
        vnames_old = vnames[::-1]
        vnids = [
            len(vnames) - vnames_old.index(vn) - 1
            for vn in list(pd.Series(vnames).unique())
        ]

        return MA(
            **(
                self.__dict__
                | dict(
                    history={vnames[i]: list(self.history.values())[i] for i in vnids}
                )
            )
        )


#        vids = [vnames.rindex(vn) for vn in set(vnames)]
