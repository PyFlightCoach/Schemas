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
