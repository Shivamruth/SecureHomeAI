
from liveness_engine import run_liveness_check
from recognize_user import run_face_recognition
from security_logger import log_access
from access_control import make_access_decision


def main():
    print()
    print("====================================")
    print("       SECUREHOMEAI AUTHENTICATION")
    print("====================================")
    print()

    # STEP 1: LIVENESS VERIFICATION
    print("STEP 1: LIVENESS VERIFICATION")
    print()

    liveness_result = run_liveness_check()

    if not liveness_result:
        print()
        print("====================================")
        print("        LIVENESS CHECK FAILED")
        print("====================================")

        decision = make_access_decision(
            liveness_result=False,
            face_recognition_result=False
        )

        reason = "Liveness verification failed"

        print("ACCESS:", decision["access"])
        print("Reason:", reason)

        log_access(
            user="UNKNOWN",
            liveness_result="FAIL",
            face_recognition_result="NOT_PERFORMED",
            access_result=decision["access"],
            reason=reason
        )
        return

    print()
    print("Liveness verification successful.")
    print()

    # STEP 2: FACE RECOGNITION
    print("STEP 2: FACE RECOGNITION")
    print()

    recognition_result = run_face_recognition()

    face_recognition_passed = recognition_result.get(
        "recognized", False
    )
    recognized_user = recognition_result.get("user")
    recognition_reason = recognition_result.get(
        "reason", "No recognition reason provided"
    )

    print("Recognition detail:", recognition_reason)

    # STEP 3: ACCESS CONTROL
    print()
    print("STEP 3: ACCESS CONTROL")
    print()

    decision = make_access_decision(
        liveness_result=liveness_result,
        face_recognition_result=face_recognition_passed
    )

    print("ACCESS:", decision["access"])

    if face_recognition_passed and decision["access"] == "GRANTED":
        event_reason = decision.get(
            "reason", "Liveness and face recognition passed"
        )
    elif not face_recognition_passed:
        event_reason = recognition_reason
    else:
        event_reason = decision.get("reason", "Access denied")

    print("Reason:", event_reason)

    # STEP 4: SECURITY LOGGING
    print()
    print("STEP 4: SECURITY LOGGING")
    print()

    log_access(
        user=recognized_user or "UNKNOWN",
        liveness_result="PASS",
        face_recognition_result=(
            "PASS" if face_recognition_passed else "FAIL"
        ),
        access_result=decision["access"],
        reason=event_reason
    )

    print()
    print("====================================")
    print("       AUTHENTICATION COMPLETE")
    print("====================================")
    print()


if __name__ == "__main__":
    main()
