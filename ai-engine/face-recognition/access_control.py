from datetime import datetime


def make_access_decision(
    liveness_result,
    face_recognition_result,
    risk_level="LOW"
):
    """
    Fail-closed access decision.

    Requirements:
    1. Liveness must be Boolean True.
    2. Face recognition must be Boolean True.
    3. HIGH and UNKNOWN risk require manual review.
    4. MEDIUM risk is monitored but does not bypass authentication.
    """

    liveness_passed = liveness_result is True
    face_passed = face_recognition_result is True

    risk_level = (
        risk_level.upper()
        if isinstance(risk_level, str)
        else "UNKNOWN"
    )

    if not liveness_passed:
        access = "DENIED"
        reason = "Liveness verification failed"

    elif not face_passed:
        access = "DENIED"
        reason = "Face recognition failed"

    elif risk_level in ("HIGH", "UNKNOWN"):
        access = "DENIED"
        reason = f"{risk_level} risk: manual review required"

    elif risk_level == "MEDIUM":
        access = "GRANTED"
        reason = "Biometrics passed; medium risk flagged for monitoring"

    elif risk_level == "LOW":
        access = "GRANTED"
        reason = "Liveness and face recognition passed"

    else:
        access = "DENIED"
        reason = "Unrecognized risk level; manual review required"

    return {
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "access": access,
        "reason": reason,
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    print("Access control self-test:")

    print(make_access_decision(True, True, "LOW"))
    print(make_access_decision(True, True, "HIGH"))
    print(make_access_decision(False, True, "LOW"))