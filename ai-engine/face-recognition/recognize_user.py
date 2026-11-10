
import cv2
from insightface.app import FaceAnalysis
import numpy as np
import json
import os
import time


# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "users.json")

RECOGNITION_THRESHOLD = 0.45
UNKNOWN_CONFIRM_SECONDS = 5
RECOGNITION_TIMEOUT = 20
RESULT_DISPLAY_SECONDS = 1.5

WINDOW_NAME = "SecureHomeAI - Face Recognition"


# ============================================================
# LOAD REGISTERED USERS
# ============================================================

def is_valid_embedding(embedding):
    try:
        vector = np.asarray(embedding, dtype=np.float32)

        return (
            vector.ndim == 1
            and vector.shape == (512,)
            and np.isfinite(vector).all()
            and np.linalg.norm(vector) > 0
        )
    except (TypeError, ValueError):
        return False


def load_users():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as file:
            users = json.load(file)
    except (json.JSONDecodeError, OSError) as exc:
        print("Database loading error:", exc)
        return []

    if not isinstance(users, list):
        print("Invalid user database format.")
        return []

    valid_users = []

    for user in users:
        if not isinstance(user, dict):
            continue

        name = user.get("name")
        embedding = user.get("embedding")

        if not isinstance(name, str) or not name.strip():
            continue

        if not is_valid_embedding(embedding):
            continue

        valid_users.append(user)

    return valid_users


# ============================================================
# FACE COMPARISON
# ============================================================

def compare_faces(embedding1, embedding2):
    try:
        vector1 = np.asarray(embedding1, dtype=np.float32)
        vector2 = np.asarray(embedding2, dtype=np.float32)

        if (
            vector1.shape != (512,)
            or vector2.shape != (512,)
            or not np.isfinite(vector1).all()
            or not np.isfinite(vector2).all()
        ):
            return -1.0

        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        if norm1 == 0 or norm2 == 0:
            return -1.0

        similarity = np.dot(
            vector1 / norm1,
            vector2 / norm2
        )

        if not np.isfinite(similarity):
            return -1.0

        return float(similarity)

    except (TypeError, ValueError, OverflowError):
        return -1.0


# ============================================================
# RESULT HELPER
# ============================================================

def make_result(recognized, user, reason):
    return {
        "recognized": recognized,
        "user": user,
        "reason": reason
    }


# ============================================================
# FACE RECOGNITION MODEL
# ============================================================

def initialize_model():
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(
        ctx_id=-1,
        det_size=(640, 640)
    )

    return app


# ============================================================
# FACE RECOGNITION
# ============================================================

def run_face_recognition():

    users = load_users()

    if not users:
        reason = "No valid registered users or embeddings found"
        print("ERROR:", reason)
        return make_result(False, "UNKNOWN", reason)

    app = None

    try:
        print("Initializing InsightFace BUFFALO_L model...")
        app = initialize_model()
        print("Face recognition model ready.")

    except Exception as exc:
        reason = f"Model initialization failed: {exc}"
        print("ERROR:", reason)
        return make_result(False, None, reason)

    camera = None
    result_data = None

    try:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not camera.isOpened():
            camera.release()
            camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            return make_result(
                False,
                "UNKNOWN",
                "Camera could not be opened"
            )

        start_time = time.monotonic()
        unknown_start_time = None

        print()
        print("====================================")
        print("   SECUREHOMEAI FACE RECOGNITION")
        print("====================================")
        print("Registered users:", len(users))
        print("Recognition threshold:", RECOGNITION_THRESHOLD)
        print("Unknown confirmation:", UNKNOWN_CONFIRM_SECONDS, "seconds")
        print("Recognition timeout:", RECOGNITION_TIMEOUT, "seconds")
        print("Press Q to cancel.")
        print()

        while True:

            elapsed = time.monotonic() - start_time

            if elapsed >= RECOGNITION_TIMEOUT:

                if unknown_start_time is not None:
                    result_data = make_result(
                        False,
                        "UNKNOWN",
                        "Unknown person detected; recognition timeout reached"
                    )
                else:
                    result_data = make_result(
                        False,
                        None,
                        "Face recognition timed out"
                    )

                print("ACCESS DENIED:", result_data["reason"])
                break

            ret, frame = camera.read()

            if not ret:
                result_data = make_result(
                    False,
                    None,
                    "Camera frame could not be read"
                )
                break

            frame = cv2.flip(frame, 1)

            faces = app.get(frame)

            # MULTIPLE FACE CHECK

            if len(faces) > 1:

                result_data = make_result(
                    False,
                    None,
                    "Multiple faces detected; authentication denied"
                )

                cv2.putText(
                    frame,
                    "MULTIPLE FACES - ACCESS DENIED",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

                cv2.imshow(WINDOW_NAME, frame)
                cv2.waitKey(int(RESULT_DISPLAY_SECONDS * 1000))
                break

            # NO FACE

            if not faces:

                unknown_start_time = None

                cv2.putText(
                    frame,
                    "Look at the camera...",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

            # SINGLE FACE

            for face in faces:

                x1, y1, x2, y2 = face.bbox.astype(int)

                current_embedding = face.embedding

                best_user = None
                best_score = -1.0

                for user in users:

                    score = compare_faces(
                        user["embedding"],
                        current_embedding
                    )

                    if score > best_score:
                        best_score = score
                        best_user = user["name"]

                # REGISTERED USER

                if (
                    best_user is not None
                    and best_score >= RECOGNITION_THRESHOLD
                ):

                    unknown_start_time = None

                    result_data = make_result(
                        True,
                        best_user,
                        "Registered face recognized"
                    )

                    print()
                    print("====================================")
                    print("FACE RECOGNIZED")
                    print("====================================")
                    print("User:", best_user)
                    print("Similarity:", round(best_score, 3))
                    print("ACCESS GRANTED")
                    print()

                    color = (0, 255, 0)
                    display_name = best_user
                    display_result = "FACE RECOGNIZED"

                # UNKNOWN USER

                else:

                    color = (0, 0, 255)
                    display_name = "UNKNOWN"
                    display_result = "ACCESS DENIED"

                    if unknown_start_time is None:
                        unknown_start_time = time.monotonic()
                        print("Unknown face detected. Confirming...")

                    unknown_elapsed = (
                        time.monotonic() - unknown_start_time
                    )

                    remaining = max(
                        0,
                        UNKNOWN_CONFIRM_SECONDS - unknown_elapsed
                    )

                    cv2.putText(
                        frame,
                        f"Unknown confirmation: {remaining:.1f}s",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2
                    )

                    if unknown_elapsed >= UNKNOWN_CONFIRM_SECONDS:

                        result_data = make_result(
                            False,
                            "UNKNOWN",
                            "Unknown person detected"
                        )

                        print()
                        print("UNKNOWN PERSON DETECTED")
                        print("Similarity:", round(best_score, 3))
                        print("ACCESS DENIED")
                        print()

                # DRAW INFORMATION

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    display_name,
                    (x1, max(25, y1 - 40)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    f"Score: {best_score:.2f}",
                    (x1, max(50, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    display_result,
                    (x1, min(frame.shape[0] - 10, y2 + 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            cv2.imshow(WINDOW_NAME, frame)

            if result_data is not None:
                cv2.waitKey(int(RESULT_DISPLAY_SECONDS * 1000))
                break

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                result_data = make_result(
                    False,
                    None,
                    "Face recognition cancelled"
                )

                print("Face recognition cancelled.")
                break

    except Exception as exc:

        reason = f"Face recognition error: {exc}"
        print("ERROR:", reason)

        result_data = make_result(
            False,
            None,
            reason
        )

    finally:

        if camera is not None:
            camera.release()

        cv2.destroyAllWindows()

    return result_data or make_result(
        False,
        None,
        "Face recognition ended without a result"
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_face_recognition()

    print()
    print("====================================")
    print("FACE RECOGNITION RESULT")
    print("====================================")

    print(
        "Status:",
        "PASS" if result["recognized"] else "FAIL"
    )

    print("User:", result["user"])
    print("Reason:", result["reason"])