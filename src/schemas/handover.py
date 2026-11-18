"""The sequence function that hands the line between two figures on to the next figure.

IMAC and IAC judge the line before a figure as part of that figure. Each manoeuvre is analysed
on its own, so its exit line is scored with it. The analysis therefore reports, per difficulty
and truncation, the raw components of its intra score (`ScoreValues.intra_own`,
`ScoreValues.handover`). This function turns them into the finished figure scores:

    intra[i] = intra_own[i] + handover[i - 1]          (floor(2x) / 2 on truncated rows)
    total[i] = max(10 - intra[i] - inter[i] - positioning[i], 0)

The first figure of a sequence receives 0. The last figure's own hand-over is dropped (the
sequence-end rows mean it is 0). A figure that failed, or is missing from the sequence, passes
0 on. A sequence ends where the schedule changes or the manoeuvre numbers stop increasing, so
repetitions and multi-schedule flights restart. Versions whose rows have no raw components
are left untouched, which includes every F3A version.

The same rules are implemented in the client and checked against
`tests/data/line_handover_cases.json`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .fcj import ManResult, Score, ScoreProperties, ScoreValues
from .ma import MA


def truncate_half(value: float) -> float:
    """Round down to the nearest half point, as truncated intra scores are."""
    return math.floor(value * 2) / 2


def figure_score(
    score: ScoreValues, incoming: float, truncate: bool
) -> ScoreValues:
    """The finished score of a figure given the downgrades handed on from the one before it.
    A score without raw components is returned unchanged."""
    if score.intra_own is None or score.handover is None:
        return score
    intra = score.intra_own + incoming
    if truncate:
        intra = truncate_half(intra)
    return score.model_copy(
        update=dict(
            intra=intra,
            total=max(10 - intra - score.inter - score.positioning, 0),
        )
    )


def _row(ma: MA, version: str, props: ScoreProperties) -> ScoreValues | None:
    """The stored score row of a manoeuvre for one version, if it has one."""
    if not ma.history or version not in ma.history:
        return None
    return next(
        (r.score for r in ma.history[version].results if r.properties == props), None
    )


def _follows(prev: MA | None, ma: MA) -> bool:
    """True if ma is the figure after prev in the same sequence. A new schedule, a number that
    does not increase (a repetition) and a gap (a missing figure) all end the sequence."""
    return prev is not None and prev.schedule == ma.schedule and ma.id == prev.id + 1


def apply_line_handover(mans: Sequence[MA], version: str) -> list[MA]:
    """The manoeuvres with the history of `version` rewritten as finished figure scores.

    Rows are recomputed from the raw components, so applying it again changes nothing. Other
    versions, manoeuvres without raw components and the manoeuvres themselves are untouched.
    """
    out: list[MA] = []
    prev: MA | None = None
    for ma in mans:
        new_ma = ma
        history = ma.history
        if history and version in history:
            new_results: list[Score] = []
            changed = False
            for result in history[version].results:
                incoming = 0.0
                if _follows(prev, ma):
                    before = _row(prev, version, result.properties)
                    if before is not None and before.handover is not None:
                        incoming = before.handover
                score = figure_score(result.score, incoming, result.properties.truncate)
                changed |= score is not result.score
                new_results.append(Score(score=score, properties=result.properties))
            if changed:
                new_ma = ma.model_copy(
                    update=dict(
                        history=history
                        | {version: history[version].model_copy(update=dict(results=new_results))}
                    )
                )
        out.append(new_ma)
        prev = ma
    return out
