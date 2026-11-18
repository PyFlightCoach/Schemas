from typing import Annotated, Literal

from pydantic import Field

from .base import CustomBaseModel as BaseModel
from .positioning import BoxLocation, Position


SequencePosition = Literal["first", "last", "only"]
"""Where a figure sits in its sequence. A missing position means an interior figure."""


def sequence_position(index: int, count: int) -> SequencePosition | None:
    """The position of the figure at ``index`` (from 0) in a sequence of ``count`` figures."""
    if count < 1 or not 0 <= index < count:
        raise ValueError(f"index {index} is outside a sequence of {count} figures")
    if count == 1:
        return "only"
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    return None


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
    sequence_position: Annotated[
        SequencePosition | None,
        "first, last or only figure of its sequence; None for an interior figure. "
        "Set where the sequence is assembled and read by the definition builder",
    ] = None

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
        sequence_position: SequencePosition | None = None,
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
            sequence_position=sequence_position,
        )
