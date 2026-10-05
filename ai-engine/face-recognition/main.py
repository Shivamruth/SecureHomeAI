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

    # ====================================
    # STEP 1: LIVENESS VERIFICATION
    # ====================================

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

        print("ACCESS:", decision["access"])
        print("Reason:", decision["reason"])

        log_access(
            user="UNKNOWN",
            liveness_result="FAIL",
            face_recognition_result="NOT_PERFORMED",
            access_result=decision["access"]
        )

        return

    print()
    print("Liveness verification successful.")
    print()

    # ====================================
    # STEP 2: FACE RECOGNITION
    # ====================================

    print("STEP 2: FACE RECOGNITION")
    print()

    recognition_result = run_face_recognition()

    # Get recognition status and actual user
    face_recognition_passed = recognition_result["recognized"]
    recognized_user = recognition_result["user"]

    # ====================================
    # STEP 3: ACCESS CONTROL
    # ====================================

    print()
    print("STEP 3: ACCESS CONTROL")
    print()

    decision = make_access_decision(
        liveness_result=liveness_result,
        face_recognition_result=face_recognition_passed
    )

    print("ACCESS:", decision["access"])
    print("Reason:", decision["reason"])

    # ====================================
    # STEP 4: SECURITY LOGGING
    # ====================================

    print()
    print("STEP 4: SECURITY LOGGING")
    print()

    if decision["access"] == "GRANTED":

        log_access(
            user=recognized_user,
            liveness_result="PASS",
            face_recognition_result="PASS",
            access_result="GRANTED"
        )

    else:

        log_access(
            user=recognized_user if recognized_user else "UNKNOWN",
            liveness_result="PASS",
            face_recognition_result="FAIL",
            access_result="DENIED"
        )

    print()
    print("====================================")
    print("       AUTHENTICATION COMPLETE")
    print("====================================")
    print()


if __name__ == "__main__":
    main()