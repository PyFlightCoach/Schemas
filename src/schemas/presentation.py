"""The sequence function that adds up the figures' box deductions into one presentation score.

IAC (Presentation), CIVA (Positioning) and IMAC (Airspace Control) judges give each sequence
one extra mark, weighted by its own K factor like an extra figure. For those rule sets the
analysis moves each figure's box deduction out of the figure score and into
`ScoreValues.presentation` (positioning is then 0, so a figure still scores
``max(10 - intra - inter - positioning, 0)``). This function adds them up, per sequence, version
and score property:

    deduction = sum(row.presentation for the figures of the sequence)
    score     = max(10 - deduction, 0)

The analysis has already multiplied each figure's box deduction by the rule set's scale
(`Box.sequence_score.scale`), because stored and uploaded analyses carry no definitions, so
this function needs only the rows. The score is continuous: it is not rounded to the rules'
fixed steps, on truncated rows either. A figure that is missing, failed or has no
`presentation` adds nothing, because it already scores 0. If no figure of a sequence has a
`presentation` the sequence has no score, which covers every version written before this
existed and all of F3A.

A sequence ends where the schedule changes or the figure number does not increase, so
repetitions and multi-schedule flights get one score each. Unlike line hand-over, a gap in the
numbers (a missing figure) does not end it. Presentation reads `presentation` only, and
line hand-over rewrites `intra` and `total` only, so the two are independent and can be applied
in either order.

The K factor belongs to the schedule (`schedules.presentation_k`), so the caller supplies it.
The same rules are implemented in the client and checked against
`tests/data/presentation_cases.json`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .base import CustomBaseModel as BaseModel
from .fcj import ScoreProperties
from .ma import MA
from .sinfo import ScheduleInfo

MAX_PRESENTATION = 10.0

type KFactor = float | None | Callable[[ScheduleInfo], float | None]


class PresentationScore(BaseModel):
    sequence: int  # 0-based position of the sequence among those in the input
    schedule: ScheduleInfo
    properties: ScoreProperties
    deduction: float
    score: float  # 0 to 10
    k: float | None  # None if the caller gave no K
    contributions: dict[int, float]  # figure id -> deduction, for figures that carry one

    @property
    def weighted(self) -> float:
        """What the score adds to the sequence total, `score * k` (0 without a K)."""
        return self.score * (self.k or 0.0)


def presentation_score(deduction: float) -> float:
    return max(MAX_PRESENTATION - deduction, 0.0)


def split_sequences(mans: Sequence[MA]) -> list[list[MA]]:
    """The manoeuvres grouped into sequences: a new schedule or a figure number that does not
    increase starts the next one."""
    sequences: list[list[MA]] = []
    prev: MA | None = None
    for ma in mans:
        if prev is None or prev.schedule != ma.schedule or ma.id <= prev.id:
            sequences.append([])
        sequences[-1].append(ma)
        prev = ma
    return sequences


def _k_for(k: KFactor, schedule: ScheduleInfo) -> float | None:
    return k(schedule) if callable(k) else k


def presentation_scores(
    mans: Sequence[MA], version: str, k: KFactor = None
) -> list[PresentationScore]:
    """One score per sequence and score property for which `version` has presentation rows.

    `k` is the schedule's `presentation_k`: a number for every sequence, or a function of the
    sequence's schedule. If it is given and comes out 0 or None for a sequence, that sequence
    has no presentation score and is left out. With `k=None` (no K supplied) scores are
    returned with `k=None`. Sequences come in input order; properties in order of first
    appearance.
    """
    out: list[PresentationScore] = []
    for n, sequence in enumerate(split_sequences(mans)):
        schedule = sequence[0].schedule
        weight = _k_for(k, schedule)
        if k is not None and not weight:
            continue
        deductions: dict[tuple[int, bool], tuple[ScoreProperties, dict[int, float]]] = {}
        for ma in sequence:
            if not ma.history or version not in ma.history:
                continue
            for result in ma.history[version].results:
                if result.score.presentation is None:
                    continue
                props = result.properties
                _, contributions = deductions.setdefault(
                    (props.difficulty, props.truncate), (props, {})
                )
                contributions[ma.id] = result.score.presentation
        for props, contributions in deductions.values():
            deduction = sum(contributions.values())
            out.append(
                PresentationScore(
                    sequence=n,
                    schedule=schedule,
                    properties=props,
                    deduction=deduction,
                    score=presentation_score(deduction),
                    k=weight,
                    contributions=contributions,
                )
            )
    return out


def get_presentation(
    scores: Sequence[PresentationScore], props: ScoreProperties | None = None
) -> list[PresentationScore]:
    """The scores for one difficulty and truncation (default: 3, untruncated)."""
    props = ScoreProperties() if props is None else props
    return [s for s in scores if s.properties == props]
