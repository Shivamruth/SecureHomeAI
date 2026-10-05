import cv2
from insightface.app import FaceAnalysis
import numpy as np
import json
import os


# ============================================================
# SETTINGS
# ============================================================

DB_PATH = "database/users.json"

RECOGNITION_THRESHOLD = 0.45


# ============================================================
# LOAD REGISTERED USERS
# ============================================================

def load_users():

    if not os.path.exists(DB_PATH):
        return []

    try:

        with open(DB_PATH, "r") as file:
            users = json.load(file)

        if not isinstance(users, list):
            return []

        return users

    except (json.JSONDecodeError, FileNotFoundError):

        return []


# ============================================================
# FACE COMPARISON
# ============================================================

def compare_faces(embedding1, embedding2):

    embedding1 = embedding1 / np.linalg.norm(embedding1)

    embedding2 = embedding2 / np.linalg.norm(embedding2)

    similarity = np.dot(
        embedding1,
        embedding2
    )

    return similarity


# ============================================================
# FACE RECOGNITION
# ============================================================

def run_face_recognition():

    # --------------------------------------------------------
    # Load users
    # --------------------------------------------------------

    users = load_users()

    if not users:

        print("ERROR: No registered users found.")

        return {
            "recognized": False,
            "user": None
        }


    # --------------------------------------------------------
    # Load InsightFace
    # --------------------------------------------------------

    app = FaceAnalysis(
        name="buffalo_l",
        providers=[
            "CUDAExecutionProvider",
            "CPUExecutionProvider"
        ]
    )

    app.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )


    # --------------------------------------------------------
    # Open camera
    # --------------------------------------------------------

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("ERROR: Could not open webcam.")

        return {
            "recognized": False,
            "user": None
        }


    print()
    print("====================================")
    print("   SECUREHOMEAI FACE RECOGNITION")
    print("====================================")
    print()
    print("Registered users:", len(users))
    print("Look at the camera...")
    print("Press Q to cancel.")
    print()


    # --------------------------------------------------------
    # Recognition state
    # --------------------------------------------------------

    recognized_user = None


    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        ret, frame = camera.read()

        if not ret:

            print("ERROR: Could not read camera.")
            break


        # Mirror camera

        frame = cv2.flip(frame, 1)


        # ----------------------------------------------------
        # Detect faces
        # ----------------------------------------------------

        faces = app.get(frame)


        for face in faces:

            box = face.bbox.astype(int)

            x1, y1, x2, y2 = box


            # ------------------------------------------------
            # Current camera embedding
            # ------------------------------------------------

            current_embedding = face.embedding


            # ------------------------------------------------
            # Find best matching registered user
            # ------------------------------------------------

            best_user = None
            best_score = -1


            for user in users:

                registered_embedding = np.array(
                    user["embedding"],
                    dtype=np.float32
                )


                score = compare_faces(
                    registered_embedding,
                    current_embedding
                )


                if score > best_score:

                    best_score = score
                    best_user = user["name"]


            # ------------------------------------------------
            # Decision
            # ------------------------------------------------

            if best_score >= RECOGNITION_THRESHOLD:

                recognized_user = best_user

                result = "ACCESS GRANTED"

                color = (0, 255, 0)

                display_name = best_user


            else:

                result = "UNKNOWN PERSON"

                color = (0, 0, 255)

                display_name = "UNKNOWN"


            # ------------------------------------------------
            # Face box
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )


            # ------------------------------------------------
            # Name
            # ------------------------------------------------

            cv2.putText(
                frame,
                display_name,
                (x1, y1 - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )


            # ------------------------------------------------
            # Similarity score
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Score: {best_score:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )


            # ------------------------------------------------
            # Access result
            # ------------------------------------------------

            cv2.putText(
                frame,
                result,
                (x1, y2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )


        # ----------------------------------------------------
        # Display camera
        # ----------------------------------------------------

        cv2.imshow(
            "SecureHomeAI - Face Recognition",
            frame
        )


        # ----------------------------------------------------
        # Recognition successful
        # ----------------------------------------------------

        if recognized_user is not None:

            print()
            print("====================================")
            print("       FACE RECOGNIZED")
            print("====================================")
            print("User:", recognized_user)
            print("Similarity:", f"{best_score:.3f}")
            print("ACCESS GRANTED")
            print()

            cv2.waitKey(1500)

            camera.release()
            cv2.destroyAllWindows()

            return {
                "recognized": True,
                "user": recognized_user
            }


        # ----------------------------------------------------
        # Quit
        # ----------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print()
            print("Face recognition cancelled.")

            camera.release()
            cv2.destroyAllWindows()

            return {
                "recognized": False,
                "user": None
            }


    # ========================================================
    # CLEANUP
    # ========================================================

    camera.release()
    cv2.destroyAllWindows()


    return {
        "recognized": False,
        "user": None
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_face_recognition()

    if result["recognized"]:

        print("Face recognition result: PASS")
        print("Recognized user:", result["user"])

    else:

        print("Face recognition result: FAIL")