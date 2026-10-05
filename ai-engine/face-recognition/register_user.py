import cv2
from insightface.app import FaceAnalysis
import json
import os


# ============================================================
# SETTINGS
# ============================================================

DB_PATH = "database/users.json"


# ============================================================
# GET USER NAME
# ============================================================

USER_NAME = input("Enter user name: ").strip()

if not USER_NAME:
    print("ERROR: User name cannot be empty.")
    exit()


# ============================================================
# LOAD EXISTING USERS
# ============================================================

os.makedirs("database", exist_ok=True)

if os.path.exists(DB_PATH):

    try:
        with open(DB_PATH, "r") as file:
            users = json.load(file)

    except (json.JSONDecodeError, FileNotFoundError):
        users = []

else:
    users = []


# ============================================================
# CHECK DATABASE FORMAT
# ============================================================

if not isinstance(users, list):

    print("ERROR: users.json is not in multi-user format.")
    exit()


# ============================================================
# CHECK DUPLICATE USER
# ============================================================

for user in users:

    if user["name"].lower() == USER_NAME.lower():

        print()
        print("ERROR: User already exists.")
        print("Existing user:", user["name"])
        exit()


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
# OPEN CAMERA
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Could not open webcam.")
    exit()


print()
print("====================================")
print("      SECUREHOMEAI REGISTRATION")
print("====================================")
print()
print("Registering user:", USER_NAME)
print()
print("Look at the camera.")
print("Press R to register.")
print("Press Q to cancel.")
print()


# ============================================================
# REGISTRATION STATE
# ============================================================

registered = False


# ============================================================
# REGISTRATION LOOP
# ============================================================

while True:

    ret, frame = camera.read()

    if not ret:

        print("ERROR: Could not read camera.")
        break


    # Mirror camera

    frame = cv2.flip(frame, 1)


    # Detect faces

    faces = app.get(frame)


    # --------------------------------------------------------
    # DRAW DETECTED FACE
    # --------------------------------------------------------

    if len(faces) > 0:

        face = faces[0]

        box = face.bbox.astype(int)

        x1, y1, x2, y2 = box


        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"User: {USER_NAME}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            "Press R to Register",
            (30, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            "Press Q to Cancel",
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


    else:

        cv2.putText(
            frame,
            "No face detected",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


        cv2.putText(
            frame,
            "Look at the camera",
            (30, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


        cv2.putText(
            frame,
            "Press Q to Cancel",
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


    # --------------------------------------------------------
    # SHOW CAMERA
    # --------------------------------------------------------

    cv2.imshow(
        "SecureHomeAI - User Registration",
        frame
    )


    # --------------------------------------------------------
    # KEYBOARD INPUT
    #
    # IMPORTANT:
    # waitKey is called ONLY ONCE per loop.
    # --------------------------------------------------------

    key = cv2.waitKey(1) & 0xFF


    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    if key == ord("r"):

        if len(faces) == 0:

            print()
            print("No face detected.")
            print("Please look at the camera and try again.")
            continue


        face = faces[0]

        embedding = face.embedding.tolist()


        new_user = {
            "name": USER_NAME,
            "embedding": embedding
        }


        users.append(new_user)


        with open(DB_PATH, "w") as file:

            json.dump(
                users,
                file,
                indent=4
            )


        print()
        print("====================================")
        print("       USER REGISTERED")
        print("====================================")
        print("Name:", USER_NAME)
        print("Total registered users:", len(users))
        print()


        registered = True

        break


    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    if key == ord("q"):

        print()
        print("Registration cancelled.")
        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()


# ============================================================
# FINAL MESSAGE
# ============================================================

if registered:

    print("Registration completed successfully.")

else:

    print("Registration was not completed.")