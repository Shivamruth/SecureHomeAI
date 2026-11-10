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
    reason=None,
    risk_level="UNKNOWN",
    risk_details=None,
    log_path=LOG_PATH,
):
    """Safely append an authentication event."""

    directory = os.path.dirname(os.path.abspath(log_path))
    os.makedirs(directory, exist_ok=True)

    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as file:
                logs = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Cannot safely read security log: {exc}"
            ) from exc

        if not isinstance(logs, list):
            raise RuntimeError(
                "Security log must contain a JSON list."
            )
    else:
        logs = []

    entry = {
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "user": user,
        "liveness": liveness_result,
        "face_recognition": face_recognition_result,
        "access": access_result,
        "risk_level": risk_level,
        "reason": reason or "Not provided",
    }

    if isinstance(risk_details, dict):
        entry["risk_details"] = risk_details

    logs.append(entry)

    temp_path = log_path + ".tmp"

    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(logs, file, indent=4)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, log_path)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print("Security event logged.")


if __name__ == "__main__":
    print("Logger self-test disabled to avoid fake events.")