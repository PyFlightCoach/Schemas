from typing import Annotated

from pydantic import Field

from .base import CustomBaseModel as BaseModel
from .positioning import BoxLocation, Position


class ManInfo(BaseModel):
    name: str
    short_name: str
    k: float = 0
    position: Position | None = None
    start: BoxLocation = BoxLocation()
    end: BoxLocation = BoxLocation()
    centre_points: Annotated[
        list[int],
        "points that should be centered, ids correspond to the previous element",
    ] = Field(default_factory=list)
    centred_els: Annotated[
        list[tuple[int, float]], "element ids that should be centered"
    ] = Field(default_factory=list)

    def to_dict(self):
        return self.model_dump()
    
    @staticmethod
    def from_dict(data: dict):
        return ManInfo.model_validate(data)

    @staticmethod
    def build(
        name: str,
        short_name: str,
        k: float,
        position: Position,
        start: BoxLocation,
        end: BoxLocation,
        centre_points: Annotated[
            list[int] | None,
            "points that should be centered, ids correspond to the previous element",
        ] = None,
        centred_els: Annotated[
            list[tuple[int, float]] | None, "element ids that should be centered"
        ] = None,
    ):
        return ManInfo(
            name=name,
            short_name=short_name,
            k=k,
            position=position,
            start=start,
            end=end,
            centre_points=centre_points if centre_points is not None else [],
            centred_els=centred_els if centred_els is not None else [],
        )
