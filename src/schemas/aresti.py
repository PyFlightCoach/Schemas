from typing import Any, Literal

from schemas.maninfo import ManInfo, SequencePosition, sequence_position

from .base import CustomBaseModel as BaseModel


class PE(BaseModel):
    kind: Literal["line", "roll", "loop", "snap", "spin", "stallturn", "tailslide"]
    args: list[Any]
    kwargs: dict[str, Any]
    centred: bool = False

    @staticmethod
    def build(kind: str, args: list, kwargs: dict, centred: bool = False):
        return PE(kind=kind, args=args, kwargs=kwargs, centred=centred)

    def __str__(self):
        pe = f"{self.kind}({','.join(self.args)}, {','.join([f'{k}={v}' for k, v in self.kwargs.items()])})"
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


def tailslide(*args, **kwargs):
    return PE.build("tailslide", args, kwargs)


def centred(_pe: PE) -> PE:
    return _pe.model_copy(update=dict(centred=True))


class NewComparison(BaseModel):
    """A comparison parameter that the rules do not define, added to one figure.

    It is judged like the existing comparison parameter named by ``like``, whose criteria,
    unit and visibility it copies, with ``value`` as its default.
    """

    value: float
    like: str


class Figure(BaseModel):
    info: ManInfo
    elements: list[PE | int]
    # A value for a rule parameter, a combination's options (list), or a new comparison parameter.
    ndmps: dict[str, float | int | list | NewComparison]
    relax_back: bool = False
    builder_options: dict[str, str] = {}

    def at_position(self, position: SequencePosition | None) -> "Figure":
        """A copy of the figure placed at ``position`` in its sequence."""
        return self.model_copy(
            update={"info": self.info.model_copy(update={"sequence_position": position})}
        )


def figure(
    info: ManInfo,
    elements: list[PE],
    relax_back: bool = False,
    options: dict = {},
    **kwargs,
) -> Figure:
    return Figure(
        info=info,
        elements=elements,
        ndmps=kwargs,
        relax_back=relax_back,
        builder_options=options,
    )


class Option(BaseModel):
    figures: list[Figure]

    @property
    def info(self):
        return self.figures[0].info

    @property
    def builder_options(self):
        return self.figures[0].builder_options

    def at_position(self, position: SequencePosition | None) -> "Option":
        """A copy of the option with every figure placed at ``position`` in its sequence."""
        return Option(figures=[f.at_position(position) for f in self.figures])


def option(figures: list[Figure]) -> Option:
    return Option(figures=figures)


def parse_figure(data: dict) -> Figure | Option:
    """Validate a stored Aresti payload, which is an Option when it holds ``figures``.

    The database stores a manoeuvre with combination options as ``{"figures": [...]}``
    rather than as a single figure.
    """
    return Option.model_validate(data) if "figures" in data else Figure.model_validate(data)


class Sequence(BaseModel):
    name: str
    rules: str
    figures: list[Figure | Option]
    options: dict[str, str] = {}

    def __getitem__(self, name_or_id: str | int):
        if isinstance(name_or_id, int):
            return self.figures[name_or_id]
        else:
            for fig in self.figures:
                if fig.info.short_name == name_or_id:
                    return fig
        raise KeyError(f"Figure {name_or_id} not found in sequence {self.name}")

    def positioned(self) -> "Sequence":
        """A copy with each figure's ``info.sequence_position`` set from its place in
        the sequence (the sequence is authoritative over any stored position)."""
        n = len(self.figures)
        return self.model_copy(
            update={
                "figures": [
                    f.at_position(sequence_position(i, n))
                    for i, f in enumerate(self.figures)
                ]
            }
        )

    @property
    def k_factors(self) -> dict[str, float]:
        return {fig.info.short_name: fig.info.k for fig in self.figures}

    @property
    def builder_options(self) -> dict[str, str]:
        return self.figures[0].builder_options


def sequence(name: str, rules: str, figures: list[Figure | Option], options:  dict[str, str] = {}) -> Sequence:
    return Sequence(name=name, rules=rules, figures=figures, options=options)