import json
import os
import tempfile
from datetime import datetime, timedelta

from risk_analysis import analyze_risk
from access_control import make_access_decision


now = datetime.now().astimezone()


def create_test_log(events):
    temp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8"
    )
    json.dump(events, temp)
    temp.close()
    return temp.name


def make_event(minutes_ago, access="DENIED", liveness="PASS"):
    return {
        "timestamp": (
            now - timedelta(minutes=minutes_ago)
        ).isoformat(),
        "access": access,
        "liveness": liveness,
        "user": "UNKNOWN",
    }


def test_risk(name, events, expected):
    path = create_test_log(events)
    try:
        result = analyze_risk(path, now)
        print(
            f"{name}: {result['risk_level']} "
            f"(score={result['risk_score']})"
        )
        assert result["risk_level"] == expected, result
    finally:
        os.remove(path)


print("\n===== RISK ANALYSIS TESTS =====")

test_risk("No events", [], "LOW")

test_risk(
    "Two denied attempts",
    [make_event(1), make_event(2)],
    "MEDIUM"
)

test_risk(
    "Three denied attempts",
    [make_event(1), make_event(2), make_event(3)],
    "HIGH"
)

test_risk(
    "Repeated liveness failures",
    [
        make_event(1, liveness="FAIL"),
        make_event(2, liveness="FAIL"),
    ],
    "HIGH"
)

test_risk(
    "Missing history",
    [],
    "LOW"
)

print("\n===== ACCESS CONTROL TESTS =====")

cases = [
    (True, True, "LOW", "GRANTED"),
    (True, True, "MEDIUM", "GRANTED"),
    (True, True, "HIGH", "DENIED"),
    (True, True, "UNKNOWN", "DENIED"),
    (False, True, "LOW", "DENIED"),
    (True, False, "LOW", "DENIED"),
]

for live, face, risk, expected in cases:
    result = make_access_decision(live, face, risk)
    print(
        f"Liveness={live}, Face={face}, Risk={risk}: "
        f"{result['access']}"
    )
    assert result["access"] == expected, result

print("\nALL TESTS PASSED")