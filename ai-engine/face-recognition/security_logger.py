
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
LOG_PATH = os.path.join(DB_DIR, "security_logs.json")


def log_access(
    user,
    liveness_result,
    face_recognition_result,
    access_result,
    reason=None
):
    """Append one authentication event without silently discarding logs."""

    os.makedirs(DB_DIR, exist_ok=True)

    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as file:
                logs = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Cannot safely read security log: {exc}"
            ) from exc

        if not isinstance(logs, list):
            raise RuntimeError(
                "Security log must contain a JSON list. "
                "Existing log was not modified."
            )
    else:
        logs = []

    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "user": user,
        "liveness": liveness_result,
        "face_recognition": face_recognition_result,
        "access": access_result,
        "reason": reason or "Not provided"
    }

    logs.append(log_entry)

    # Write to a temporary file first, then replace the log.
    temp_path = LOG_PATH + ".tmp"

    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(logs, file, indent=4)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, LOG_PATH)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print()
    print("Security event logged.")


if __name__ == "__main__":
    print("Logger self-test is disabled to avoid adding fake events.")
