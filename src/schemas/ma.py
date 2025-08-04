from __future__ import annotations
from typing import Literal
import pandas as pd
from pydantic import BaseModel
from packaging.version import Version
from schemas import fcj, ScheduleInfo, Direction

type FAVersion = Literal["All", "Latest"] | str

class MA(BaseModel):
    name: str
    id: int
    schedule: ScheduleInfo
    schedule_direction: Direction | None = None
    flown: list[dict] | dict

    history: dict[str, fcj.ManResult] | None = None

    mdef: dict | list[dict] | None = None
    manoeuvre: dict | list[dict] | None = None
    template: list[dict] | dict | None = None
    templates: list[dict] | dict | None = None
    corrected: dict | None = None
    corrected_template: list[dict] | dict | None = None
    scores: dict | None = None

    @property
    def k(self) -> float:
        if isinstance(self.mdef, dict):
            return self.mdef['info']['k']
        elif isinstance(self.mdef, list) and len(self.mdef) > 0:
            return self.mdef[0]['info']['k']
        else:
            raise ValueError("No k factor available")

    @property
    def latest_version(self):
        versions = list(self.history.keys())
        if len(versions) == 0:
            raise ValueError("No versions available in history")
        return max(versions, key=Version)

    def __str__(self):
        from schemas.fcj import ScoreProperties
        scores = {k: v.get_score(ScoreProperties(difficulty=3, truncate=False)).total for k, v in self.history.items()}
        scores = ",".join([f"{k}: {v:.2f}" for k, v in scores.items()]) 
        return f"MA({self.name}, {'Full' if self.mdef else 'Basic'}, {scores})"
    
    def __repr__(self):
        return str(self)
    
    def basic(self, mdef: dict | list[dict] | None = None) -> MA:
        return MA(
            name=self.name,
            id=self.id,
            schedule=self.schedule,
            schedule_direction=self.schedule_direction,
            flown=self.flown,
            history=self.history,
            mdef=mdef
        )

    def k_factored_score(self, props: fcj.ScoreProperties=None, version: FAVersion="All") -> pd.Series | float:        
        if version in self.history.keys():
            return self.history[version].get_score(props).total  * self.k
        elif version=="Latest":
            return self.history[max(list(self.history.keys()))].get_score(props).total * self.k
        else:
            return pd.Series({k: v.get_score(props).total for k, v in self.history.items()}) * self.k

    def simplify_history(self):
        """Tidy up the analysis version naming"""
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
