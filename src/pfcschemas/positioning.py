import numpy as np
from pydantic import BaseModel
from typing import Annotated
from .utils.enum import EnumStr


class Orientation(EnumStr):
    UPRIGHT = np.pi
    INVERTED = 0


class Heading(EnumStr):
    RTOL = np.pi
    LTOR = 0
    OUTTOIN = 3 * np.pi / 2
    INTOOUT = np.pi / 2

    @staticmethod
    def values():
        return np.array(list(Heading.__members__.values()))

    @staticmethod
    def infer(bearing: Annotated[float, "in radians from north"]):
        def check(bearing: float, heading: Heading):
            return (
                np.round(np.abs(4 * (bearing - heading.value)) / (2 * np.pi)).astype(
                    int
                )
                % 4
            ) == 0

        for head in Heading.__members__.values():
            if check(bearing, head):
                return head
        else:
            raise ValueError(f"Invalid bearing {bearing}")

    def reverse(self):
        return {
            Heading.RTOL: Heading.LTOR,
            Heading.LTOR: Heading.RTOL,
            Heading.OUTTOIN: Heading.INTOOUT,
            Heading.INTOOUT: Heading.OUTTOIN,
        }[self]


class Direction(EnumStr):
    UPWIND = 1
    DOWNWIND = -1
    CROSS = 0

    def wind_swap_heading(self, d_or_w: Heading) -> int:
        match self:
            case Direction.UPWIND:
                return d_or_w
            case Direction.DOWNWIND:
                return d_or_w.reverse()
            case Direction.CROSS:
                return d_or_w

    @staticmethod
    def parse(s: str):
        match s[0].lower():
            case "u":
                return Direction.UPWIND
            case "d":
                return Direction.DOWNWIND
            case "c":
                return Direction.CROSS
            case _:
                raise ValueError(f"Invalid wind {s}")


class Height(EnumStr):
    BTM = 0.2
    MID = 0.6
    TOP = 1.0


class Position(EnumStr):
    CENTRE = 0
    END = 1


class BoxLocation(BaseModel):
    height: Height
    direction: Direction | None = None
    orientation: Orientation | None = None


def boxlocationmaker(
    height: Height,
    direction: Direction | None = None,
    orientation: Orientation | None = None,
):
    return BoxLocation(
        height=height,
        direction=direction,
        orientation=orientation,
    )
