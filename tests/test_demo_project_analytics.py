import pytest

from app.demo_project.analytics import detect_risk, summarize_progress


# --------------------------------------------------------------------------
# summarize_progress
# --------------------------------------------------------------------------


def test_summarize_progress_computes_average_minutes_and_completion_rate():
    sessions = [
        {"minutes": 20, "completed": True},
        {"minutes": 40, "completed": False},
        {"minutes": 30, "completed": True},
    ]
    summary = summarize_progress(sessions)
    assert summary == {"average_minutes": 30.0, "completion_rate": 0.67}


def test_summarize_progress_rounds_average_to_one_decimal():
    sessions = [
        {"minutes": 10, "completed": True},
        {"minutes": 11, "completed": True},
        {"minutes": 12, "completed": True},
    ]
    summary = summarize_progress(sessions)
    assert summary["average_minutes"] == 11.0


def test_summarize_progress_no_completed_sessions_is_zero_rate():
    sessions = [{"minutes": 15, "completed": False}]
    summary = summarize_progress(sessions)
    assert summary["completion_rate"] == 0.0


def test_summarize_progress_all_completed_is_full_rate():
    sessions = [
        {"minutes": 25, "completed": True},
        {"minutes": 35, "completed": True},
    ]
    summary = summarize_progress(sessions)
    assert summary["completion_rate"] == 1.0


def test_summarize_progress_empty_sessions_returns_zeros():
    summary = summarize_progress([])
    assert summary == {"average_minutes": 0, "completion_rate": 0}


# --------------------------------------------------------------------------
# detect_risk
# --------------------------------------------------------------------------


def test_detect_risk_low_completion_rate_needs_support():
    summary = {"completion_rate": 0.4, "average_minutes": 45}
    assert detect_risk(summary) == "needs_support"


def test_detect_risk_short_sessions_needs_focus_time():
    summary = {"completion_rate": 0.8, "average_minutes": 15}
    assert detect_risk(summary) == "needs_focus_time"


def test_detect_risk_healthy_sessions_on_track():
    summary = {"completion_rate": 0.8, "average_minutes": 30}
    assert detect_risk(summary) == "on_track"


def test_detect_risk_completion_rate_takes_priority_over_short_minutes():
    # Both conditions technically apply; completion_rate check runs first.
    summary = {"completion_rate": 0.3, "average_minutes": 10}
    assert detect_risk(summary) == "needs_support"


@pytest.mark.parametrize(
    "completion_rate, average_minutes, expected",
    [
        (0.5, 30, "on_track"),  # boundary: 0.5 is not "< 0.5"
        (0.49, 30, "needs_support"),
        (0.9, 20, "on_track"),  # boundary: 20 is not "< 20"
        (0.9, 19, "needs_focus_time"),
    ],
)
def test_detect_risk_boundary_values(completion_rate, average_minutes, expected):
    summary = {"completion_rate": completion_rate, "average_minutes": average_minutes}
    assert detect_risk(summary) == expected
