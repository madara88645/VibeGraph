from app.demo_project.analytics import detect_risk, summarize_progress
from app.demo_project.planner import LearningPlanner, create_step, rank_topics


def test_summarize_progress_averages_minutes_and_completion_rate():
    sessions = [
        {"minutes": 10, "completed": True},
        {"minutes": 20, "completed": False},
        {"minutes": 30, "completed": True},
    ]

    summary = summarize_progress(sessions)

    assert summary == {"average_minutes": 20.0, "completion_rate": 0.67}


def test_summarize_progress_rounds_average_minutes_to_one_decimal():
    sessions = [
        {"minutes": 10, "completed": True},
        {"minutes": 11, "completed": True},
        {"minutes": 12, "completed": True},
    ]

    summary = summarize_progress(sessions)

    assert summary["average_minutes"] == 11.0


def test_summarize_progress_handles_empty_session_list():
    summary = summarize_progress([])

    assert summary == {"average_minutes": 0, "completion_rate": 0}


def test_summarize_progress_all_completed_gives_full_rate():
    sessions = [
        {"minutes": 15, "completed": True},
        {"minutes": 25, "completed": True},
    ]

    summary = summarize_progress(sessions)

    assert summary["completion_rate"] == 1.0


def test_summarize_progress_none_completed_gives_zero_rate():
    sessions = [
        {"minutes": 15, "completed": False},
        {"minutes": 25, "completed": False},
    ]

    summary = summarize_progress(sessions)

    assert summary["completion_rate"] == 0.0


def test_detect_risk_flags_low_completion_as_needs_support():
    summary = {"completion_rate": 0.2, "average_minutes": 40}

    assert detect_risk(summary) == "needs_support"


def test_detect_risk_prioritizes_completion_rate_over_minutes():
    # Below the completion threshold, even with plenty of average minutes,
    # detect_risk should still flag needs_support rather than on_track.
    summary = {"completion_rate": 0.4, "average_minutes": 100}

    assert detect_risk(summary) == "needs_support"


def test_detect_risk_flags_short_sessions_as_needs_focus_time():
    summary = {"completion_rate": 0.8, "average_minutes": 10}

    assert detect_risk(summary) == "needs_focus_time"


def test_detect_risk_on_track_when_completion_and_minutes_are_healthy():
    summary = {"completion_rate": 0.9, "average_minutes": 25}

    assert detect_risk(summary) == "on_track"


def test_detect_risk_boundary_completion_rate_of_half_is_not_needs_support():
    summary = {"completion_rate": 0.5, "average_minutes": 25}

    assert detect_risk(summary) != "needs_support"


def test_detect_risk_boundary_average_minutes_of_twenty_is_not_needs_focus_time():
    summary = {"completion_rate": 0.9, "average_minutes": 20}

    assert detect_risk(summary) == "on_track"


def test_rank_topics_sorts_descending_by_weight():
    topic_weights = {"loops": 2, "recursion": 5, "closures": 3}

    assert rank_topics(topic_weights) == ["recursion", "closures", "loops"]


def test_rank_topics_handles_empty_weights():
    assert rank_topics({}) == []


def test_rank_topics_handles_single_topic():
    assert rank_topics({"only": 1}) == ["only"]


def test_create_step_assigns_more_minutes_when_risk_needs_focus_time():
    step = create_step("recursion", 1, "needs_focus_time")

    assert step == {"order": 1, "topic": "recursion", "minutes": 35, "risk": "needs_focus_time"}


def test_create_step_assigns_fewer_minutes_for_other_risk_levels():
    for risk in ("needs_support", "on_track"):
        step = create_step("loops", 2, risk)
        assert step == {"order": 2, "topic": "loops", "minutes": 25, "risk": risk}


class TestLearningPlannerBuildPlan:
    def test_ranks_topics_and_caps_at_three_steps(self):
        planner = LearningPlanner(
            {"loops": 2, "recursion": 5, "closures": 3, "generics": 1}
        )
        sessions = [{"minutes": 30, "completed": True}]

        plan = planner.build_plan(sessions)

        assert [step["topic"] for step in plan] == ["recursion", "closures", "loops"]
        assert [step["order"] for step in plan] == [1, 2, 3]

    def test_propagates_detected_risk_into_every_step(self):
        planner = LearningPlanner({"loops": 1, "recursion": 2})
        sessions = [
            {"minutes": 5, "completed": True},
            {"minutes": 5, "completed": True},
        ]

        plan = planner.build_plan(sessions)

        assert all(step["risk"] == "needs_focus_time" for step in plan)
        assert all(step["minutes"] == 35 for step in plan)

    def test_handles_empty_sessions_and_topics(self):
        planner = LearningPlanner({})

        plan = planner.build_plan([])

        assert plan == []
