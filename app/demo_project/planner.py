from .analytics import detect_risk, summarize_progress


class LearningPlanner:
    def __init__(self, topic_weights: dict[str, int]):
        self.topic_weights = topic_weights

    def build_plan(self, sessions: list[dict]) -> list[dict]:
        summary = summarize_progress(sessions)
        risk = detect_risk(summary)
        ranked_topics = rank_topics(self.topic_weights)
        return [
            create_step(topic, index + 1, risk)
            for index, topic in enumerate(ranked_topics[:3])
        ]


def rank_topics(topic_weights: dict[str, int]) -> list[str]:
    return [
        topic
        for topic, _score in sorted(
            topic_weights.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def create_step(topic: str, order: int, risk: str) -> dict:
    minutes = 35 if risk == "needs_focus_time" else 25
    return {"order": order, "topic": topic, "minutes": minutes, "risk": risk}
