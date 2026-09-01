from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, RootModel

type LegacyBinColumn = dict[str, float] | list[float | str]

class CompressedBinColumn(BaseModel):
    model_config = ConfigDict(serialize_defaults=False)
    format: str
    multiplier: float
    length: int
    type: str
    data: str

class BinField(RootModel[LegacyBinColumn | CompressedBinColumn]):
    model_config = ConfigDict(serialize_defaults=False)

class NewBinData(BaseModel):
    model_config = ConfigDict(serialize_defaults=False)
    filename: str | None = None
    data: dict[str, BinField]


class LegacyBinData(RootModel[dict[str, BinField]]):
    model_config = ConfigDict(serialize_defaults=False)


class BinData(RootModel[LegacyBinData | NewBinData]):
    model_config = ConfigDict(serialize_defaults=False)


class NewState(BaseModel):
    model_config = ConfigDict(serialize_defaults=False)
    t: list[float]
    labels: LabelGroups | None = None    
    data: LegacyState | None = None
    splines: dict | None = None
    pos: Point | None = None
    att: Quaternion | None = None
    vel: Point | None = None
    rvel: Point | None = None
    acc: Point | None = None

    def df(self):
        return pd.DataFrame(self.data.df())

class Label(BaseModel):
    model_config = ConfigDict(serialize_defaults=False)
    start: float
    stop: float
    sublabels: dict[str, dict[str, Label]] | None = None

class LabelGroup(RootModel[dict[str, Label]]):
    pass

class LabelGroups(RootModel[dict[str, LabelGroup]]):
    pass

class LegacyStateRow(BaseModel):
    model_config = ConfigDict(serialize_defaults=False)
    t: float
    dt: float
    x: float
    y: float
    z: float
    rw: float
    rx: float
    ry: float
    rz: float
    u: float | None = None
    v: float | None = None
    w: float | None = None
    p: float | None = None
    q: float | None = None
    r: float | None = None
    du: float | None = None
    dv: float | None = None
    dw: float | None = None
    manoeuvre: str | None = None
    element: str | None = None


class LegacyState(RootModel[list[LegacyStateRow]]):

    def df(self):
        return pd.DataFrame(self.model_dump())

    @staticmethod
    def parse_df(df: pd.DataFrame):
        return LegacyState.model_validate(df.to_dict(orient="records"))


class State(RootModel[NewState | LegacyState]):
    pass

class Point(BaseModel):
    x: DataArray
    y: DataArray
    z: DataArray

class Quaternion(BaseModel):
    w: DataArray
    x: DataArray
    y: DataArray
    z: DataArray

type DataArray = list[float] | str