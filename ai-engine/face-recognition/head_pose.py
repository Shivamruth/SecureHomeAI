import cv2
import mediapipe as mp
import random
import time

from mediapipe.python.solutions.face_mesh import FaceMesh


# ============================================================
# INITIALIZE MEDIAPIPE FACE MESH
# ============================================================

face_mesh = FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ============================================================
# OPEN WEBCAM
# ============================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()


# ============================================================
# SETTINGS
# ============================================================

DIRECTIONS = ["LEFT", "RIGHT", "UP", "DOWN"]

CALIBRATION_FRAMES = 30

YAW_THRESHOLD = 0.18
PITCH_THRESHOLD = 0.15

SUCCESS_TIME = 2.0


# ============================================================
# VARIABLES
# ============================================================

challenge = None

calibrating = True
calibration_count = 0

baseline_x = None
baseline_y = None

challenge_passed = False
success_start_time = None


# ============================================================
# START NEW CHALLENGE
# ============================================================

def start_new_challenge():

    global challenge
    global calibrating
    global calibration_count
    global baseline_x
    global baseline_y
    global challenge_passed
    global success_start_time

    challenge = random.choice(DIRECTIONS)

    calibrating = True
    calibration_count = 0

    baseline_x = None
    baseline_y = None

    challenge_passed = False
    success_start_time = None

    print()
    print("--------------------------------")
    print("NEW LIVENESS CHALLENGE")
    print("TURN:", challenge)
    print("--------------------------------")


# Start first challenge
start_new_challenge()


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    success_camera, frame = cap.read()

    if not success_camera:
        print("ERROR: Could not read camera frame.")
        break

    # Mirror effect
    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    # Convert BGR → RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process face
    results = face_mesh.process(rgb)


    # ========================================================
    # TITLE
    # ========================================================

    cv2.putText(
        frame,
        "SECUREHOMEAI - LIVENESS TEST",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    # ========================================================
    # FACE FOUND
    # ========================================================

    if results.multi_face_landmarks:

        landmarks = results.multi_face_landmarks[0].landmark


        # ----------------------------------------------------
        # LANDMARKS
        # ----------------------------------------------------

        # Nose
        nose = landmarks[1]

        # Left eye
        left_eye = landmarks[33]

        # Right eye
        right_eye = landmarks[263]


        # ----------------------------------------------------
        # EYE CENTER
        # ----------------------------------------------------

        eye_center_x = (left_eye.x + right_eye.x) / 2
        eye_center_y = (left_eye.y + right_eye.y) / 2


        # ----------------------------------------------------
        # DISTANCE BETWEEN EYES
        # ----------------------------------------------------

        eye_distance = abs(right_eye.x - left_eye.x)

        if eye_distance < 0.001:
            eye_distance = 0.001


        # ----------------------------------------------------
        # NOSE POSITION RELATIVE TO EYES
        # ----------------------------------------------------

        relative_x = (
            (nose.x - eye_center_x)
            / eye_distance
        )

        relative_y = (
            (nose.y - eye_center_y)
            / eye_distance
        )


        # ====================================================
        # CALIBRATION
        # ====================================================

        if calibrating:

            if baseline_x is None:

                baseline_x = relative_x
                baseline_y = relative_y

            else:

                baseline_x = (
                    baseline_x * calibration_count
                    + relative_x
                ) / (calibration_count + 1)

                baseline_y = (
                    baseline_y * calibration_count
                    + relative_y
                ) / (calibration_count + 1)


            calibration_count += 1


            cv2.putText(
                frame,
                "CALIBRATING...",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Keep your head straight: "
                f"{calibration_count}/{CALIBRATION_FRAMES}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


            # Calibration complete
            if calibration_count >= CALIBRATION_FRAMES:

                calibrating = False

                print("Calibration complete.")
                print("Challenge:", challenge)


        # ====================================================
        # CHALLENGE DETECTION
        # ====================================================

        elif not challenge_passed:

            movement_x = relative_x - baseline_x
            movement_y = relative_y - baseline_y


            detected_direction = "CENTER"


            # ------------------------------------------------
            # LEFT / RIGHT
            # ------------------------------------------------

            if movement_x < -YAW_THRESHOLD:

                detected_direction = "LEFT"

            elif movement_x > YAW_THRESHOLD:

                detected_direction = "RIGHT"


            # ------------------------------------------------
            # UP / DOWN
            # ------------------------------------------------

            elif movement_y < -PITCH_THRESHOLD:

                detected_direction = "UP"

            elif movement_y > PITCH_THRESHOLD:

                detected_direction = "DOWN"


            # ------------------------------------------------
            # DISPLAY CHALLENGE
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"CHALLENGE: TURN {challenge}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Detected: {detected_direction}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"X: {movement_x:.2f}  Y: {movement_y:.2f}",
                (20, 155),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )


            # ------------------------------------------------
            # CHECK ANSWER
            # ------------------------------------------------

            if detected_direction == challenge:

                challenge_passed = True

                success_start_time = time.time()

                print(
                    "LIVENESS CHALLENGE PASSED:",
                    challenge
                )


        # ====================================================
        # SUCCESS
        # ====================================================

        else:

            cv2.putText(
                frame,
                "LIVENESS VERIFIED!",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                3
            )


            cv2.putText(
                frame,
                f"Correct movement: {challenge}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


            # Wait 2 seconds
            if time.time() - success_start_time >= SUCCESS_TIME:

                start_new_challenge()


        # ====================================================
        # DRAW RED NOSE DOT
        # ====================================================

        nose_x = int(nose.x * width)
        nose_y = int(nose.y * height)

        cv2.circle(
            frame,
            (nose_x, nose_y),
            6,
            (0, 0, 255),
            -1
        )


        # ====================================================
        # DRAW BLUE EYE CENTER
        # ====================================================

        center_x = int(eye_center_x * width)
        center_y = int(eye_center_y * height)

        cv2.circle(
            frame,
            (center_x, center_y),
            5,
            (255, 0, 0),
            -1
        )


    # ========================================================
    # NO FACE
    # ========================================================

    else:

        cv2.putText(
            frame,
            "NO FACE DETECTED",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2
        )


    # ========================================================
    # CONTROLS
    # ========================================================

    cv2.putText(
        frame,
        "R = Restart     Q = Quit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    # ========================================================
    # SHOW CAMERA
    # ========================================================

    cv2.imshow(
        "SecureHomeAI - Liveness Detection",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    # Restart
    if key == ord("r"):

        start_new_challenge()


    # Quit
    elif key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

face_mesh.close()

print("SecureHomeAI liveness test stopped.")