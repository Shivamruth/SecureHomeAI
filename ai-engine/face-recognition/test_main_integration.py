import json
import os
import tempfile
from datetime import datetime, timedelta

from main import process_authentication


now = datetime.now().astimezone()


def create_test_log():
    initial_events = [
        {
            "timestamp": (
                now - timedelta(minutes=2)
            ).isoformat(),
            "user": "User_A",
            "liveness": "PASS",
            "face_recognition": "PASS",
            "access": "GRANTED",
            "risk_level": "LOW",
            "reason": "Previous successful authentication",
        }
    ]

    file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    )

    json.dump(initial_events, file)
    file.close()

    return file.name


path = create_test_log()

try:
    print("\n===== MAIN AUTHENTICATION INTEGRATION TEST =====")

    # TEST 1: Registered user
    registered = process_authentication(
        True,
        {"recognized": True, "user": "User_A"},
        path,
    )

    print(
        "Registered user:",
        registered["decision"]["access"],
    )

    assert registered["user"] == "User_A"
    assert registered["decision"]["access"] == "GRANTED"

    # TEST 2: Unknown face
    unknown = process_authentication(
        True,
        {"recognized": False, "user": "UNKNOWN"},
        path,
    )

    print(
        "Unknown face:",
        unknown["decision"]["access"],
    )

    assert unknown["user"] == "UNKNOWN"
    assert unknown["decision"]["access"] == "DENIED"

    # TEST 3: Liveness failure
    failed_live = process_authentication(
        False,
        None,
        path,
    )

    print(
        "Liveness failure:",
        failed_live["decision"]["access"],
    )

    assert failed_live["decision"]["access"] == "DENIED"

    # TEST 4: Verify event logging
    with open(path, "r", encoding="utf-8") as file:
        logs = json.load(file)

    print("Total recorded events:", len(logs))

    assert len(logs) == 4
    assert logs[-1]["user"] == "UNKNOWN"
    assert logs[-1]["liveness"] == "FAIL"

    # TEST 5: Verify risk information is stored
    assert "risk_details" in logs[-1]
    assert "device" in logs[-1]["risk_details"]
    assert "unknown_visitors" in logs[-1]["risk_details"]

    print("\nALL MAIN INTEGRATION TESTS PASSED")

finally:
    os.remove(path)
