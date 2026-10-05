import cv2
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import json


# ============================================================
# SETTINGS
# ============================================================

DB_PATH = "database/users.json"

RECOGNITION_THRESHOLD = 0.45


# ============================================================
# LOAD REGISTERED USER
# ============================================================

with open(DB_PATH, "r") as file:
    user_data = json.load(file)


registered_name = user_data["name"]

registered_embedding = np.array(
    user_data["embedding"]
)


# ============================================================
# LOAD INSIGHTFACE
# ============================================================

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


# ============================================================
# FACE COMPARISON
# ============================================================

def compare_faces(
    embedding1,
    embedding2
):

    embedding1 = (
        embedding1 /
        np.linalg.norm(embedding1)
    )

    embedding2 = (
        embedding2 /
        np.linalg.norm(embedding2)
    )

    similarity = np.dot(
        embedding1,
        embedding2
    )

    return similarity


# ============================================================
# FACE RECOGNITION
# ============================================================

def run_face_recognition():

    print()
    print("====================================")
    print("   SECUREHOMEAI FACE RECOGNITION")
    print("====================================")
    print()
    print("Look at the camera...")
    print()

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("ERROR: Could not open webcam.")

        return False

    # --------------------------------------------------------
    # Recognition state
    # --------------------------------------------------------

    access_granted = False

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------

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

            current_embedding = face.embedding

            # ------------------------------------------------
            # Compare face
            # ------------------------------------------------

            score = compare_faces(
                registered_embedding,
                current_embedding
            )

            # ------------------------------------------------
            # Decision
            # ------------------------------------------------

            if score > RECOGNITION_THRESHOLD:

                result = "ACCESS GRANTED"

                color = (0, 255, 0)

                access_granted = True

            else:

                result = "UNKNOWN PERSON"

                color = (0, 0, 255)

                access_granted = False

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

            display_name = (
                registered_name
                if score > RECOGNITION_THRESHOLD
                else "UNKNOWN"
            )

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
            # Score
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Score: {score:.2f}",
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
        # Window
        # ----------------------------------------------------

        cv2.imshow(
            "SecureHomeAI - Face Recognition",
            frame
        )

        # ----------------------------------------------------
        # If recognized
        # ----------------------------------------------------

        if access_granted:

            print()
            print("====================================")
            print("       FACE RECOGNIZED")
            print("====================================")
            print(
                "User:",
                registered_name
            )
            print("ACCESS GRANTED")
            print()

            cv2.waitKey(1500)

            camera.release()
            cv2.destroyAllWindows()

            return True

        # ----------------------------------------------------
        # Quit
        # ----------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            camera.release()
            cv2.destroyAllWindows()

            return False

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    camera.release()
    cv2.destroyAllWindows()

    return False


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_face_recognition()

    if result:

        print("Face recognition result: PASS")

    else:

        print("Face recognition result: FAIL")  