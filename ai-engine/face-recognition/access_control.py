from datetime import datetime


def make_access_decision(
    liveness_result,
    face_recognition_result
):
    """
    Decide whether access should be granted.

    Access is granted only when BOTH:
    1. Liveness verification passes
    2. Face recognition passes
    """

    if liveness_result and face_recognition_result:

        decision = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "access": "GRANTED",
            "reason": "Liveness and face recognition passed"
        }

    else:

        if not liveness_result:
            reason = "Liveness verification failed"

        elif not face_recognition_result:
            reason = "Face recognition failed"

        else:
            reason = "Authentication failed"

        decision = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "access": "DENIED",
            "reason": reason
        }

    return decision


if __name__ == "__main__":

    print("Testing access control...")

    result = make_access_decision(
        liveness_result=True,
        face_recognition_result=True
    )

    print(result)