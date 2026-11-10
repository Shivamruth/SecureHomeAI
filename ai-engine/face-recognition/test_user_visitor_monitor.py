import json
import os
import tempfile
from datetime import datetime, timedelta

from risk_analysis import analyze_user_risk, analyze_risk
from visitor_monitor import analyze_unknown_visitors


now = datetime.now().astimezone()


def create_log(events):
    file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8"
    )
    json.dump(events, file)
    file.close()
    return file.name


def event(user, minutes, access="DENIED", liveness="PASS"):
    return {
        "timestamp": (
            now - timedelta(minutes=minutes)
        ).isoformat(),
        "user": user,
        "access": access,
        "liveness": liveness,
        "face_recognition": "FAIL",
        "risk_level": "LOW",
        "reason": "Test event",
    }


events = [
    event("User_A", 1),
    event("User_A", 2),
    event("User_B", 3, access="GRANTED"),
    event("UNKNOWN", 4, liveness="FAIL"),
    event("UNKNOWN", 5),
    event("UNKNOWN", 25),
]

path = create_log(events)

try:
    print("\n===== INDIVIDUAL USER RISK TEST =====")

    user_a = analyze_user_risk("User_A", path, now)
    print("User_A:", user_a["risk_level"], user_a["risk_score"])

    assert user_a["risk_level"] == "MEDIUM"
    assert user_a["total_recorded_events"] == 2

    user_b = analyze_user_risk("User_B", path, now)
    print("User_B:", user_b["risk_level"], user_b["risk_score"])

    assert user_b["risk_level"] == "LOW"
    assert user_b["total_recorded_events"] == 1

    print("\n===== DEVICE RISK TEST =====")

    device = analyze_risk(path, now)
    print("Device:", device["risk_level"], device["risk_score"])

    assert device["risk_level"] == "HIGH"

    print("\n===== UNKNOWN VISITOR TEST =====")

    visitors = analyze_unknown_visitors(path, now)

    print("Unknown events:", visitors["total_unknown_events"])
    print("Visitor sessions:", visitors["total_sessions"])

    for session in visitors["sessions"]:
        print(
            "Session:",
            session["session_number"],
            "Attempts:",
            session["attempts"],
            "Liveness failures:",
            session["liveness_failures"],
        )

    assert visitors["total_unknown_events"] == 3
    assert visitors["total_sessions"] == 2

    # Find sessions by their chronological first-seen time.
    oldest_session = visitors["sessions"][0]
    recent_session = visitors["sessions"][1]

    assert oldest_session["attempts"] == 1
    assert oldest_session["liveness_failures"] == 0

    assert recent_session["attempts"] == 2
    assert recent_session["liveness_failures"] == 1

    print("\nALL INDIVIDUAL AND VISITOR TESTS PASSED")

finally:
    os.remove(path)