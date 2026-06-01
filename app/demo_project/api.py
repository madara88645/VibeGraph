from .planner import LearningPlanner


class DemoRepository:
    def load_sessions(self, user_id: str) -> list[dict]:
        print(f"loading sessions for {user_id}")
        return [
            {"minutes": 30, "completed": True},
            {"minutes": 18, "completed": False},
            {"minutes": 42, "completed": True},
        ]


def build_daily_plan(user_id: str) -> dict:
    repo = DemoRepository()
    sessions = repo.load_sessions(user_id)
    planner = LearningPlanner({"python": 5, "typescript": 4, "graphs": 3})
    return {"user_id": user_id, "steps": planner.build_plan(sessions)}


def handle_request(payload: dict) -> dict:
    user_id = payload.get("user_id", "demo-user")
    return build_daily_plan(user_id)
