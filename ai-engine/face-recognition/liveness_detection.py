import cv2
import mediapipe as mp
import math

# ----------------------------
# Initialize MediaPipe Face Mesh
# ----------------------------
mp_face_mesh = mp.tasks.vision.FaceLandmarker

# Using FaceMesh through Tasks is not required here because your installation
# exposes the legacy FaceMesh via face_mesh module.
from mediapipe.python.solutions.face_mesh import FaceMesh

face_mesh = FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ----------------------------
# Eye Landmarks
# ----------------------------
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ----------------------------
# Distance Function
# ----------------------------
def euclidean_distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )

# ----------------------------
# Eye Aspect Ratio
# ----------------------------
def eye_aspect_ratio(landmarks, eye):
    p1 = landmarks[eye[0]]
    p2 = landmarks[eye[1]]
    p3 = landmarks[eye[2]]
    p4 = landmarks[eye[3]]
    p5 = landmarks[eye[4]]
    p6 = landmarks[eye[5]]

    vertical1 = euclidean_distance(p2, p5)
    vertical2 = euclidean_distance(p3, p6)
    horizontal = euclidean_distance(p1, p4)

    return (vertical1 + vertical2) / (2.0 * horizontal)

# ----------------------------
# Camera
# ----------------------------
cap = cv2.VideoCapture(0)

# ----------------------------
# Blink Parameters
# ----------------------------

# We will calibrate this after observing your EAR values
EAR_THRESHOLD = 0.45

# Number of consecutive frames eyes must stay closed
CONSECUTIVE_FRAMES = 2

frame_counter = 0
blink_count = 0

# ----------------------------
# Main Loop
# ----------------------------
while True:

    success, frame = cap.read()

    if not success:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        landmarks = results.multi_face_landmarks[0].landmark

        leftEAR = eye_aspect_ratio(landmarks, LEFT_EYE)
        rightEAR = eye_aspect_ratio(landmarks, RIGHT_EYE)

        ear = (leftEAR + rightEAR) / 2

        print(f"EAR : {ear:.4f}")

        # ----------------------------
        # Blink Detection
        # ----------------------------

        if ear < EAR_THRESHOLD:
            frame_counter += 1

        else:
            if frame_counter >= CONSECUTIVE_FRAMES:
                blink_count += 1
                print("Blink Detected!")

            frame_counter = 0

        # ----------------------------
        # Display
        # ----------------------------

        cv2.putText(
            frame,
            f"EAR: {ear:.4f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Blinks: {blink_count}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2
        )

        if blink_count >= 1:
            cv2.putText(
                frame,
                "LIVE PERSON",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                3
            )

    cv2.imshow("Liveness Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()