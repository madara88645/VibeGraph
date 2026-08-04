"""Tests for app/demo_project/api.py — pure orchestration over the demo repo/planner."""

from app.demo_project.api import DemoRepository, build_daily_plan, handle_request


def test_demo_repository_load_sessions_returns_fixed_sample_data():
    repo = DemoRepository()
    sessions = repo.load_sessions("anyone")

    assert sessions == [
        {"minutes": 30, "completed": True},
        {"minutes": 18, "completed": False},
        {"minutes": 42, "completed": True},
    ]


def test_build_daily_plan_ranks_topics_by_weight_and_marks_on_track_risk():
    plan = build_daily_plan("alice")

    assert plan["user_id"] == "alice"
    assert [step["topic"] for step in plan["steps"]] == ["python", "typescript", "graphs"]
    assert [step["order"] for step in plan["steps"]] == [1, 2, 3]
    assert all(step["risk"] == "on_track" for step in plan["steps"])
    assert all(step["minutes"] == 25 for step in plan["steps"])


def test_handle_request_defaults_user_id_when_missing():
    result = handle_request({})

    assert result["user_id"] == "demo-user"
    assert len(result["steps"]) == 3


def test_handle_request_uses_provided_user_id():
    result = handle_request({"user_id": "bob"})

    assert result["user_id"] == "bob"
    assert result == build_daily_plan("bob")


def test_handle_request_ignores_unrelated_payload_keys():
    result = handle_request({"user_id": "carol", "unused": "ignored"})

    assert result["user_id"] == "carol"
