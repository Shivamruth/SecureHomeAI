import json
import os
from datetime import datetime


LOG_PATH = "database/security_logs.json"


def log_access(
    user,
    liveness_result,
    face_recognition_result,
    access_result
):
    """
    Store one authentication attempt in the security log.
    """

    os.makedirs("database", exist_ok=True)

    # Create log file if it does not exist
    if os.path.exists(LOG_PATH):

        try:
            with open(LOG_PATH, "r") as file:
                logs = json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):
            logs = []

    else:
        logs = []

    # Create authentication record
    log_entry = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "user": user,
        "liveness": liveness_result,
        "face_recognition": face_recognition_result,
        "access": access_result
    }

    logs.append(log_entry)

    # Save updated logs
    with open(LOG_PATH, "w") as file:
        json.dump(
            logs,
            file,
            indent=4
        )

    print()
    print("Security event logged.")

if __name__ == "__main__":

    log_access(
        user="Shivamruth",
        liveness_result="PASS",
        face_recognition_result="PASS",
        access_result="GRANTED"
    )

    print("Logging test completed.")