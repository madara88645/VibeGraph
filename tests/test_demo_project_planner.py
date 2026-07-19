from app.demo_project.planner import LearningPlanner, create_step, rank_topics


# --------------------------------------------------------------------------
# rank_topics
# --------------------------------------------------------------------------


def test_rank_topics_orders_by_weight_descending():
    weights = {"loops": 2, "recursion": 5, "closures": 3}
    assert rank_topics(weights) == ["recursion", "closures", "loops"]


def test_rank_topics_empty_weights_returns_empty_list():
    assert rank_topics({}) == []


def test_rank_topics_single_topic():
    assert rank_topics({"only": 1}) == ["only"]


# --------------------------------------------------------------------------
# create_step
# --------------------------------------------------------------------------


def test_create_step_allocates_more_minutes_when_focus_time_is_needed():
    step = create_step("recursion", 1, "needs_focus_time")
    assert step == {"order": 1, "topic": "recursion", "minutes": 35, "risk": "needs_focus_time"}


def test_create_step_allocates_default_minutes_for_other_risk_levels():
    on_track = create_step("loops", 2, "on_track")
    needs_support = create_step("loops", 2, "needs_support")
    assert on_track["minutes"] == 25
    assert needs_support["minutes"] == 25


# --------------------------------------------------------------------------
# LearningPlanner.build_plan
# --------------------------------------------------------------------------


def test_build_plan_ranks_topics_and_caps_at_three_steps():
    planner = LearningPlanner(
        {"loops": 1, "recursion": 4, "closures": 3, "generators": 2}
    )
    sessions = [
        {"minutes": 30, "completed": True},
        {"minutes": 30, "completed": True},
    ]

    plan = planner.build_plan(sessions)

    assert len(plan) == 3
    assert [step["topic"] for step in plan] == ["recursion", "closures", "generators"]
    assert [step["order"] for step in plan] == [1, 2, 3]


def test_build_plan_propagates_risk_from_session_history_into_each_step():
    planner = LearningPlanner({"only_topic": 1})
    sessions = [{"minutes": 10, "completed": False}]

    plan = planner.build_plan(sessions)

    assert len(plan) == 1
    assert plan[0]["risk"] == "needs_support"
    assert plan[0]["minutes"] == 25


def test_build_plan_uses_focus_time_minutes_when_sessions_are_short_but_completed():
    planner = LearningPlanner({"only_topic": 1})
    sessions = [{"minutes": 10, "completed": True}]

    plan = planner.build_plan(sessions)

    assert plan[0]["risk"] == "needs_focus_time"
    assert plan[0]["minutes"] == 35


def test_build_plan_empty_sessions_still_produces_a_plan():
    planner = LearningPlanner({"topic_a": 2, "topic_b": 1})
    plan = planner.build_plan([])
    assert [step["topic"] for step in plan] == ["topic_a", "topic_b"]
    assert plan[0]["risk"] == "needs_support"
