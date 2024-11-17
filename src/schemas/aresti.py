from schemas.maninfo import ManInfo
from pydantic import BaseModel
from typing import Any


class PE(BaseModel):
    kind: str
    args: list[Any]
    kwargs: dict[str, Any]
    centred: bool = False

    @staticmethod
    def build(kind: str, args: list, kwargs: dict, centred: bool = False):
        return PE(kind=kind, args=args, kwargs=kwargs, centred=centred)

    def __str__(self):
        pe = f"{self.kind}({','.join(self.args)}, {','.join([f'{k}={v}' for k,v in self.kwargs.items()])})"
        if self.centred:
            pe = f"centred({pe})"
        return pe


def line(*args, **kwargs):
    return PE.build("line", args, kwargs)


def roll(*args, **kwargs):
    return PE.build("roll", args, kwargs)


def loop(*args, **kwargs):
    return PE.build("loop", args, kwargs)


def snap(*args, **kwargs):
    return PE.build("snap", args, kwargs)


def spin(*args, **kwargs):
    return PE.build("spin", args, kwargs)


def stallturn(*args, **kwargs):
    return PE.build("stallturn", args, kwargs)


def centred(_pe: PE) -> PE:
    return _pe.model_copy(update=dict(centred=True))


class Figure(BaseModel):
    info: ManInfo
    elements: list[PE|int]
    ndmps: dict[str, float | int | list]
    relax_back: bool = False


def figure(
    info: ManInfo, elements: list[PE], relax_back: bool = False, **kwargs
) -> Figure:
    return Figure(info=info, elements=elements, ndmps=kwargs, relax_back=relax_back)


class Option(BaseModel):
    figures: list[Figure | list[Figure]]



def option(figures: list[Figure | list[Figure]]) -> Option:
    return Option(figures=figures)


class Sequence(BaseModel):
    name: str
    rules: str
    figures: list[Figure | Option]

def sequence(name: str, rules: str, figures: list[Figure | Option]) -> Sequence:
    return Sequence(name=name, rules=rules, figures=figures)