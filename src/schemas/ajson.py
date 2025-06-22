from __future__ import annotations

from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel

from schemas import fcj
from schemas.ma import MA, FAVersion

from schemas.sinfo import ScheduleInfo
from schemas.utils.files import validate_json


class AJson(BaseModel):
    origin: fcj.Origin | None = None
    isComp: bool
    sourceBin: str | None = None
    sourceFCJ: str | None = None
    bootTime: datetime | None = None
    mans: list[MA]

    def basic(self, mdefs: list[dict] | None = None):
        if mdefs is None:
            mdefs = [None] * len(self.mans)
        return AJson(
            origin=self.origin,
            isComp=self.isComp,
            sourceBin=self.sourceBin,
            sourceFCJ=self.sourceFCJ,
            bootTime=self.bootTime,
            mans=[m.basic(mdef) for m, mdef in zip(self.mans, mdefs)],
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

    def __iter__(self):
        for man in self.mans:
            yield man

    @property
    def k_factors(self):
        return [m.k for m in self]

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

    def latest_version(self):
        versions = self.all_versions()
        if not versions:
            raise ValueError("No valid versions found in manoeuvres")
        return max(versions, key=Version)

    def all_valid_versions(self):
        valid_versions = []
        for version in self.all_versions():
            try:
                Version(version)
                valid_versions.append(version)
            except InvalidVersion:
                pass
        return valid_versions

    def get_scores(
        self,
        version: FAVersion = "All",
        props: fcj.ScoreProperties = None,
        group: Literal["intra", "inter", "positioning", "total"] = "total",
        missing: Literal["raise", "zero", "nan"] = "raise",
    ) -> pd.Series:
        props = fcj.ScoreProperties() if props is None else props
        scores = {}
        for man in self.mans:
            if version in man.history:
                score = man.history[version].get_score(props)
                if score:
                    scores[man.name] = score.__dict__[group]
            else:
                if missing == "raise":
                    raise ValueError(f"Version {version} not found in manoeuvre")
                elif missing == "zero":
                    scores[man.name] = 0
                elif missing == "nan":
                    scores[man.name] = np.nan

        return pd.Series(scores, name=version)

    def create_score_df(
        self,
        props: fcj.ScoreProperties = None,
        group="total",
        version: FAVersion | list[str] = "All",
        missing: Literal["raise", "zero", "nan"] = "raise",
    ):
        if props is None:
            props = fcj.ScoreProperties(difficulty=3, truncate=False)
        if version == "All":
            versions = self.all_versions()
        elif version == "Latest":
            versions = [self.latest_version()]
        else:
            versions = version if pd.api.types.is_list_like(version) else [version]

        return pd.concat(
            [self.get_scores(ver, props, group, missing) for ver in versions], axis=1
        )

    def total_score(
        self,
        props: fcj.ScoreProperties = None,
        group: str = "total",
        version: FAVersion = "All",
        missing="raise",
    ) -> pd.Series:
        return (
            self.create_score_df(props, group, version, missing)
            .multiply(self.k_factors, axis=0)
            .sum(axis=0)
        )

    def check_version(self, version: str):
        version = version[1:] if version.startswith("v") else version
        return all(
            [
                man.history is not None and version in man.history.keys()
                for man in self.mans
            ]
        )

    @staticmethod
    def parse_json(json: dict | str):
        return AJson.model_validate(validate_json(json))
