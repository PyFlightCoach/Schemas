from __future__ import annotations

import pandas as pd
from pydantic import RootModel

from .base import CustomBaseModel as BaseModel


class CompressedBinColumn(BaseModel):
    format: str
    multiplier: float
    length: int
    type: str
    data: str


class BinField(
    RootModel[
        dict[
            str,
            dict[str, float | None]
            | list[float | str | None | CompressedBinColumn],
        ]
    ]
):
    pass


class NewBinData(BaseModel):
    data: dict[str, BinField]
    filename: str | None = None
    source: str | None = None


class LegacyBinData(RootModel[dict[str, BinField]]):
    pass


class BinData(RootModel[LegacyBinData | NewBinData]):
    pass


class NewState(BaseModel):
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
    start: float
    stop: float
    sublabels: dict[str, dict[str, Label]] | None = None


class LabelGroup(RootModel[dict[str, Label]]):
    pass


class LabelGroups(RootModel[dict[str, LabelGroup]]):
    pass


class LegacyStateRow(BaseModel):
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
