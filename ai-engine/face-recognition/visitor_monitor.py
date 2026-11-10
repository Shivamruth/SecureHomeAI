from datetime import datetime, timedelta

from risk_analysis import load_events, parse_timestamp, LOG_PATH


DEFAULT_SESSION_GAP_MINUTES = 10


def analyze_unknown_visitors(
    log_path=LOG_PATH,
    now=None,
    session_gap_minutes=DEFAULT_SESSION_GAP_MINUTES,
):
    """
    Group UNKNOWN events into time-based visitor sessions.

    This does not identify or track a physical person.
    It groups events by their timestamps only.
    """

    if now is None:
        now = datetime.now().astimezone()
    elif now.tzinfo is None:
        now = now.astimezone()

    if session_gap_minutes < 1:
        raise ValueError("Session gap must be at least 1 minute")

    events = load_events(log_path)

    if events is None:
        return {
            "status": "UNKNOWN",
            "message": "Security history unavailable",
            "total_unknown_events": 0,
            "total_sessions": 0,
            "sessions": [],
        }

    unknown_events = []

    for event in events:
        if not isinstance(event, dict):
            continue

        if event.get("user") != "UNKNOWN":
            continue

        event_time = parse_timestamp(
            event.get("timestamp"),
            now.tzinfo
        )

        if event_time is None or event_time > now:
            continue

        unknown_events.append((event_time, event))

    unknown_events.sort(key=lambda item: item[0])

    sessions = []
    current_session = None
    session_gap = timedelta(minutes=session_gap_minutes)

    for event_time, event in unknown_events:

        if (
            current_session is None
            or event_time - current_session["last_seen"] > session_gap
        ):
            current_session = {
                "session_number": len(sessions) + 1,
                "first_seen": event_time.isoformat(),
                "last_seen": event_time,
                "attempts": 0,
                "denied_attempts": 0,
                "liveness_failures": 0,
            }

            sessions.append(current_session)

        current_session["last_seen"] = event_time
        current_session["attempts"] += 1

        if event.get("access") == "DENIED":
            current_session["denied_attempts"] += 1

        if event.get("liveness") == "FAIL":
            current_session["liveness_failures"] += 1

    # Convert datetime objects to JSON-friendly strings.
    for session in sessions:
        session["last_seen"] = session["last_seen"].isoformat()

    return {
        "status": "OK",
        "message": (
            "Time-based unknown visitor sessions; "
            "these are not verified individual identities"
        ),
        "total_unknown_events": len(unknown_events),
        "total_sessions": len(sessions),
        "session_gap_minutes": session_gap_minutes,
        "sessions": sessions,
    }


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            analyze_unknown_visitors(),
            indent=4
        )
    )