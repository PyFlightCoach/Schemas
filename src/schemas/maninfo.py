from .positioning import Position, BoxLocation
from typing import Tuple, Annotated
from pydantic import BaseModel


class ManInfo(BaseModel):
    name: str
    short_name: str
    k: float
    position: Position
    start: BoxLocation
    end: BoxLocation
    centre_points: Annotated[
        list[int],
        "points that should be centered, ids correspond to the previous element",
    ] = []
    centred_els: Annotated[
        list[Tuple[int, float]], "element ids that should be centered"
    ] = []

    def to_dict(self):
        return self.model_dump()
    
    @staticmethod
    def from_dict(data: dict):
        return ManInfo.model_validate(data)


def maninfomaker(
    name: str,
    short_name: str,
    k: float,
    position: Position,
    start: BoxLocation,
    end: BoxLocation,
    centre_points: Annotated[
        list[int],
        "points that should be centered, ids correspond to the previous element",
    ] = None,
    centred_els: Annotated[
        list[Tuple[int, float]], "element ids that should be centered"
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
