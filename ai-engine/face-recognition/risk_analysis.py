import json
import os
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "database", "security_logs.json")

RISK_WINDOW_MINUTES = 10


def load_events(log_path):
    if not os.path.exists(log_path):
        return None

    try:
        with open(log_path, "r", encoding="utf-8") as file:
            events = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(events, list):
        return None

    return events


def parse_timestamp(value, timezone):
    if not isinstance(value, str):
        return None

    try:
        event_time = datetime.fromisoformat(value)

        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone)

        return event_time.astimezone(timezone)

    except (ValueError, TypeError):
        return None


def calculate_risk(events, now):
    result = {
        "risk_score": None,
        "risk_level": "UNKNOWN",
        "recommendation": "MANUAL_REVIEW",
        "signals": [],
        "history_available": False,
        "recent_denials": 0,
        "recent_liveness_failures": 0,
    }

    if events is None:
        result["signals"].append("Security history unavailable")
        return result

    if len(events) == 0:
        result.update({
            "risk_score": 0,
            "risk_level": "LOW",
            "recommendation": "CONTINUE_STANDARD_AUTHENTICATION",
            "history_available": True,
        })
        result["signals"].append("No previous security events")
        return result

    cutoff = now - timedelta(minutes=RISK_WINDOW_MINUTES)

    valid_timestamps = 0
    skipped_entries = 0
    denials = 0
    liveness_failures = 0

    for event in events:
        if not isinstance(event, dict):
            skipped_entries += 1
            continue

        event_time = parse_timestamp(
            event.get("timestamp"),
            now.tzinfo
        )

        if event_time is None:
            skipped_entries += 1
            continue

        valid_timestamps += 1

        if cutoff <= event_time <= now:
            if event.get("access") == "DENIED":
                denials += 1

            if (
                event.get("access") == "DENIED"
                and event.get("liveness") == "FAIL"
            ):
                liveness_failures += 1

    if valid_timestamps == 0:
        result["signals"].append(
            "No usable timestamped events"
        )
        return result

    result["history_available"] = True
    result["recent_denials"] = denials
    result["recent_liveness_failures"] = liveness_failures

    score = 0

    if denials >= 3:
        score += 40
        result["signals"].append(
            "Three or more denied attempts in 10 minutes"
        )
    elif denials >= 2:
        score += 20
        result["signals"].append(
            "Repeated denied attempts in 10 minutes"
        )

    if liveness_failures >= 2:
        score += 20
        result["signals"].append(
            "Repeated liveness failures in 10 minutes"
        )

    score = min(score, 100)
    result["risk_score"] = score

    if score >= 40:
        result["risk_level"] = "HIGH"
        result["recommendation"] = "MANUAL_REVIEW"

    elif score >= 20:
        result["risk_level"] = "MEDIUM"
        result["recommendation"] = "MONITOR_AND_VERIFY"

    else:
        result["risk_level"] = "LOW"
        result["recommendation"] = (
            "CONTINUE_STANDARD_AUTHENTICATION"
        )

    if skipped_entries:
        result["signals"].append(
            f"{skipped_entries} invalid log entries skipped"
        )

    if not result["signals"]:
        result["signals"].append(
            "No repeated-failure rule triggered"
        )

    return result


def analyze_risk(log_path=LOG_PATH, now=None):
    """Device-wide risk assessment."""
    if now is None:
        now = datetime.now().astimezone()
    elif now.tzinfo is None:
        now = now.astimezone()

    events = load_events(log_path)

    return calculate_risk(events, now)


def analyze_user_risk(user_name, log_path=LOG_PATH, now=None):
    """Risk assessment for events attributed to one registered user."""

    if not isinstance(user_name, str) or not user_name.strip():
        raise ValueError("A valid registered user name is required")

    if now is None:
        now = datetime.now().astimezone()
    elif now.tzinfo is None:
        now = now.astimezone()

    events = load_events(log_path)

    if events is None:
        result = calculate_risk(None, now)
        result["user"] = user_name
        result["profile_type"] = "INDIVIDUAL"
        return result

    user_events = [
        event
        for event in events
        if isinstance(event, dict)
        and event.get("user") == user_name
    ]

    result = calculate_risk(user_events, now)
    result["user"] = user_name
    result["profile_type"] = "INDIVIDUAL"
    result["total_recorded_events"] = len(user_events)

    if not user_events:
        result["signals"] = [
            "No events attributed to this registered user"
        ]

    return result


if __name__ == "__main__":
    print("DEVICE RISK")
    print(json.dumps(analyze_risk(), indent=4))