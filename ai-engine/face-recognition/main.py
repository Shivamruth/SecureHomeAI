
from security_logger import log_access, LOG_PATH
from access_control import make_access_decision
from risk_analysis import analyze_risk, analyze_user_risk
from visitor_monitor import analyze_unknown_visitors


RISK_PRIORITY = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "UNKNOWN": 3
}


def calculate_risk(user, log_path=LOG_PATH):
    """Calculate device, individual and unknown visitor risk."""

    # 1. Device-wide risk
    try:
        device_risk = analyze_risk(log_path=log_path)
    except Exception as error:
        print("Device risk error:", error)
        device_risk = {
            "risk_level": "UNKNOWN",
            "risk_score": None,
            "signals": ["Device risk analysis unavailable"]
        }

    # 2. Individual registered-user risk
    if user != "UNKNOWN":
        try:
            individual_risk = analyze_user_risk(
                user,
                log_path=log_path
            )
        except Exception as error:
            print("Individual risk error:", error)
            individual_risk = {
                "risk_level": "UNKNOWN",
                "risk_score": None,
                "signals": ["Individual risk analysis unavailable"]
            }
    else:
        individual_risk = {
            "risk_level": "LOW",
            "risk_score": 0,
            "signals": ["No registered identity established"]
        }

    # 3. Unknown visitor monitoring
    try:
        visitor_summary = analyze_unknown_visitors(
            log_path=log_path
        )
    except Exception as error:
        print("Visitor monitoring error:", error)
        visitor_summary = {
            "status": "UNKNOWN",
            "message": str(error),
            "total_unknown_events": None,
            "total_sessions": None
        }

    # 4. Determine the strictest risk level
    levels = [
        device_risk.get("risk_level", "UNKNOWN"),
        individual_risk.get("risk_level", "UNKNOWN")
    ]

    levels = [
        level if level in RISK_PRIORITY else "UNKNOWN"
        for level in levels
    ]

    effective_risk = max(
        levels,
        key=lambda level: RISK_PRIORITY[level]
    )

    # Keep compatibility with the integration test
    risk_details = {
        "device": device_risk,
        "individual": individual_risk,
        "unknown_visitors": visitor_summary,

        # Additional descriptive aliases
        "device_risk": device_risk,
        "individual_risk": individual_risk,
        "visitor_summary": visitor_summary
    }

    return {
        "risk_level": effective_risk,
        "device_risk": device_risk,
        "individual_risk": individual_risk,
        "visitor_summary": visitor_summary,
        "risk_details": risk_details
    }


def process_authentication(
    liveness_result,
    recognition_result=None,
    log_path=LOG_PATH
):
    """Process authentication and record the security event."""

    # 1. Validate liveness
    liveness_passed = liveness_result is True

    # 2. Validate face recognition
    recognized = False
    user = "UNKNOWN"

    if liveness_passed and isinstance(recognition_result, dict):

        if recognition_result.get("recognized") is True:

            candidate = recognition_result.get("user")

            if isinstance(candidate, str) and candidate.strip():
                recognized = True
                user = candidate.strip()

    # 3. Calculate all risk profiles
    risk_data = calculate_risk(user, log_path)

    risk_level = risk_data["risk_level"]
    risk_details = risk_data["risk_details"]

    # 4. Make final access decision
    decision = make_access_decision(
        liveness_result=liveness_passed,
        face_recognition_result=recognized,
        risk_level=risk_level
    )

    # IMPORTANT:
    # access_control.py returns "access", not "access_granted".
    access_status = decision.get("access", "DENIED")

    reason = decision.get(
        "reason",
        "Authentication decision completed"
    )

    # 5. Log security event
    log_access(
        user=user,
        liveness_result=(
            "PASS" if liveness_passed else "FAIL"
        ),
        face_recognition_result=(
            "PASS" if recognized
            else "FAIL" if liveness_passed
            else "NOT_PERFORMED"
        ),
        access_result=access_status,
        reason=reason,
        risk_level=risk_level,
        risk_details=risk_details,
        log_path=log_path
    )

    # 6. Return complete authentication result
    return {
        "user": user,
        "liveness": liveness_passed,
        "face_recognized": recognized,
        "risk_level": risk_level,
        "risk_details": risk_details,
        "access": access_status,
        "decision": decision,
        "reason": reason
    }


def main():

    # Camera-dependent imports are delayed until actual execution.
    from liveness_engine import run_liveness_check
    from recognize_user import run_face_recognition

    print("\n========================================")
    print("       SECURE HOME AI SYSTEM")
    print("========================================")

    # 1. Face liveness detection
    print("\n[1] Starting face liveness detection...")

    liveness_result = run_liveness_check()

    if liveness_result is not True:

        print("[WARNING] Liveness verification failed.")

        result = process_authentication(False)

    else:

        # 2. Face recognition
        print("\n[2] Starting face recognition...")

        recognition_result = run_face_recognition()

        result = process_authentication(
            True,
            recognition_result
        )

    # 3. Display result
    print("\n========== AUTHENTICATION RESULT ==========")

    print("User:", result["user"])
    print("Liveness:", result["liveness"])
    print("Face recognized:", result["face_recognized"])
    print("Risk level:", result["risk_level"])
    print("Access:", result["decision"]["access"])
    print("Reason:", result["decision"]["reason"])

    print("===========================================\n")


if __name__ == "__main__":
    main()
