from __future__ import annotations
from pydantic import BaseModel
from schemas import fcj
import pandas as pd
from datetime import datetime
from schemas.utils.files import validate_json
from schemas.ma import MA
from schemas.sinfo import ScheduleInfo
from packaging.version import InvalidVersion, Version


class AJson(BaseModel):
    origin: fcj.Origin | None = None
    isComp: bool
    sourceBin: str | None = None
    sourceFCJ: str | None = None
    bootTime: datetime | None = None
    mans: list[MA]

    def basic(self):
        return AJson(
            origin=self.origin,
            isComp=self.isComp,
            sourceBin=self.sourceBin,
            sourceFCJ=self.sourceFCJ,
            bootTime=self.bootTime,
            mans=[m.basic() for m in self.mans]
        )

    @property
    def man_names(self):
        return [m.name for m in self.mans]

    def get_man(self, id: str | int):
        if isinstance(id, str):
            id = self.man_names.index(id)
        return self.mans[id]

    def __getitem__(self, id: str | int):
        return self.get_man(id)

    def schedule(self):
        schedules = [man.schedule for man in self.mans]
        if all([s == schedules[0] for s in schedules[1:]]):
            return schedules[0].fcj_to_pfc()
        else:
            return ScheduleInfo.mixed()

    def all_versions(self):
        versions = set()
        for man in self.mans:
            versions |= set(man.history.keys())
        return list(versions)

    def all_valid_versions(self):
        valid_versions = []
        for version in self.all_versions():
            try:
                Version(version)
                valid_versions.append(version)
            except InvalidVersion:
                pass
        return valid_versions

    def total_score(self, props: fcj.ScoreProperties, version: str = "All") -> pd.Series:
        return pd.DataFrame({man.name: man.k_factored_score(props, version) for man in self.mans}).T.sum()
        
    def get_scores(self, version: str, props: fcj.ScoreProperties=None, group="total") -> pd.Series:
        if props is None:
            props = fcj.ScoreProperties()
        scores = {}
        for man in self.mans:
            if version in man.history:
                score = man.history[version].get_score(props)
                if score:
                    scores[man.name] = score.__dict__[group]
        return pd.Series(scores, name=version)

    def create_score_df(
        self, props: fcj.ScoreProperties, group="total", version: str = "All"
    ):
        versions = self.all_versions() if version == "All" else [version]
        return pd.concat([self.get_scores(ver, props, group) for ver in versions], axis=1)

    def check_version(self, version: str):
        version = version[1:] if version.startswith('v') else version
        return all([man.history is not None and version in man.history.keys() for man in self.mans])

    @staticmethod
    def parse_json(json: dict|str):
        return AJson.model_validate(validate_json(json))
