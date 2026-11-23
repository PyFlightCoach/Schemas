"""ScoreValues.presentation is optional, so rows from older versions and F3A load unchanged."""

from schemas.fcj import Score, ScoreProperties, ScoreValues


def test_old_rows_load_without_presentation():
    row = ScoreValues.model_validate(dict(intra=1.0, inter=0.5, positioning=2.0, total=6.5))
    assert row.presentation is None
    assert row.total == 6.5 and row.positioning == 2.0


def test_presentation_round_trips_and_keeps_the_figure_invariant():
    row = ScoreValues(intra=1.0, inter=0.5, positioning=0.0, total=8.5, presentation=2.0)
    back = Score(
        score=ScoreValues.model_validate(row.model_dump()),
        properties=ScoreProperties(difficulty=3, truncate=False),
    ).score
    assert back == row
    assert back.total == max(10 - back.intra - back.inter - back.positioning, 0)
