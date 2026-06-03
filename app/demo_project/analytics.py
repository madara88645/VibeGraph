from statistics import mean


def summarize_progress(sessions: list[dict]) -> dict:
    minutes = [session["minutes"] for session in sessions]
    completed = [session for session in sessions if session["completed"]]
    return {
        "average_minutes": round(mean(minutes), 1) if minutes else 0,
        "completion_rate": round(len(completed) / len(sessions), 2) if sessions else 0,
    }


def detect_risk(summary: dict) -> str:
    if summary["completion_rate"] < 0.5:
        return "needs_support"
    if summary["average_minutes"] < 20:
        return "needs_focus_time"
    return "on_track"
