import cv2
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import json
import os


# User name
USER_NAME = "Shivamruth"


# Create database path
DB_PATH = "database/users.json"


# Load InsightFace model
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


# Open camera
camera = cv2.VideoCapture(0)

print("Look at the camera for registration...")


registered = False


while True:

    ret, frame = camera.read()

    if not ret:
        break


    faces = app.get(frame)


    for face in faces:

        # Draw face box
        box = face.bbox.astype(int)

        x1, y1, x2, y2 = box

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0,255,0),
            2
        )


        cv2.putText(
            frame,
            "Press R to Register",
            (30,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )


        # Register when R pressed
        key = cv2.waitKey(1)


        if key == ord('r'):

            embedding = face.embedding.tolist()


            user_data = {
                "name": USER_NAME,
                "embedding": embedding
            }


            os.makedirs(
                "database",
                exist_ok=True
            )


            with open(DB_PATH,"w") as file:
                json.dump(
                    user_data,
                    file
                )


            print("User Registered Successfully")

            registered = True
            break


    cv2.imshow(
        "SecureHomeAI - User Registration",
        frame
    )


    if registered:
        break


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



camera.release()
cv2.destroyAllWindows()