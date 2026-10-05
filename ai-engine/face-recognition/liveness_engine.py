import cv2
import math
import random
import time

from mediapipe.python.solutions.face_mesh import FaceMesh


# ============================================================
# SETTINGS
# ============================================================

EAR_THRESHOLD = 0.45
CONSECUTIVE_FRAMES = 2

YAW_THRESHOLD = 0.18
PITCH_THRESHOLD = 0.15

CALIBRATION_FRAMES = 30
CHALLENGE_TIMEOUT = 8

DIRECTIONS = [
    "LEFT",
    "RIGHT",
    "UP",
    "DOWN"
]

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def euclidean_distance(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


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

    if horizontal == 0:
        return 0

    return (vertical1 + vertical2) / (2.0 * horizontal)


# ============================================================
# LIVENESS FUNCTION
# ============================================================

def run_liveness_check():

    print()
    print("====================================")
    print("     SECUREHOMEAI LIVENESS CHECK")
    print("====================================")
    print()
    print("Step 1: Blink your eyes")
    print()

    # --------------------------------------------------------
    # Face Mesh
    # --------------------------------------------------------

    face_mesh = FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print("ERROR: Could not open webcam.")

        face_mesh.close()

        return False

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    blink_frame_counter = 0
    blink_verified = False

    baseline_x = None
    baseline_y = None

    calibration_count = 0
    calibrating = True

    challenge = random.choice(DIRECTIONS)
    challenge_start_time = None

    head_verified = False

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------

    while True:

        success, frame = cap.read()

        if not success:

            print("ERROR: Could not read camera.")

            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        height, width, _ = frame.shape

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = face_mesh.process(rgb)

        # ----------------------------------------------------
        # NO FACE
        # ----------------------------------------------------

        if not results.multi_face_landmarks:

            cv2.putText(
                frame,
                "NO FACE DETECTED",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2
            )

            cv2.imshow(
                "SecureHomeAI - Liveness Check",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                cap.release()
                cv2.destroyAllWindows()
                face_mesh.close()

                return False

            continue

        # ----------------------------------------------------
        # LANDMARKS
        # ----------------------------------------------------

        landmarks = results.multi_face_landmarks[0].landmark

        # ----------------------------------------------------
        # BLINK DETECTION
        # ----------------------------------------------------

        left_ear = eye_aspect_ratio(
            landmarks,
            LEFT_EYE
        )

        right_ear = eye_aspect_ratio(
            landmarks,
            RIGHT_EYE
        )

        ear = (left_ear + right_ear) / 2

        if not blink_verified:

            if ear < EAR_THRESHOLD:

                blink_frame_counter += 1

            else:

                if blink_frame_counter >= CONSECUTIVE_FRAMES:

                    blink_verified = True

                    print("Blink detected!")
                    print()
                    print("Step 2: Turn your head")
                    print("Challenge:", challenge)

                    challenge_start_time = time.time()

                blink_frame_counter = 0

        # ----------------------------------------------------
        # HEAD POSE VALUES
        # ----------------------------------------------------

        nose = landmarks[1]

        left_eye = landmarks[33]
        right_eye = landmarks[263]

        eye_center_x = (
            left_eye.x + right_eye.x
        ) / 2

        eye_center_y = (
            left_eye.y + right_eye.y
        ) / 2

        eye_distance = abs(
            right_eye.x - left_eye.x
        )

        if eye_distance < 0.001:

            eye_distance = 0.001

        relative_x = (
            (nose.x - eye_center_x)
            / eye_distance
        )

        relative_y = (
            (nose.y - eye_center_y)
            / eye_distance
        )

        # ----------------------------------------------------
        # CALIBRATION
        # ----------------------------------------------------

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

            if calibration_count >= CALIBRATION_FRAMES:

                calibrating = False

                print("Head calibration complete.")

        # ----------------------------------------------------
        # HEAD CHALLENGE
        # ----------------------------------------------------

        detected_direction = "CENTER"

        if not calibrating:

            movement_x = relative_x - baseline_x
            movement_y = relative_y - baseline_y

            if movement_x < -YAW_THRESHOLD:

                detected_direction = "LEFT"

            elif movement_x > YAW_THRESHOLD:

                detected_direction = "RIGHT"

            elif movement_y < -PITCH_THRESHOLD:

                detected_direction = "UP"

            elif movement_y > PITCH_THRESHOLD:

                detected_direction = "DOWN"

            # ------------------------------------------------
            # Check challenge
            # ------------------------------------------------

            if (
                blink_verified
                and not head_verified
                and challenge_start_time is not None
            ):

                elapsed = (
                    time.time()
                    - challenge_start_time
                )

                if detected_direction == challenge:

                    head_verified = True

                    print(
                        "Head challenge passed:",
                        challenge
                    )

                elif elapsed > CHALLENGE_TIMEOUT:

                    challenge = random.choice(
                        DIRECTIONS
                    )

                    challenge_start_time = time.time()

                    print(
                        "Challenge timed out."
                    )

                    print(
                        "New challenge:",
                        challenge
                    )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        cv2.putText(
            frame,
            "SECUREHOMEAI - LIVENESS",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        blink_status = (
            "PASSED"
            if blink_verified
            else "WAITING"
        )

        cv2.putText(
            frame,
            f"Blink: {blink_status}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0) if blink_verified
            else (0, 255, 255),
            2
        )

        if calibrating:

            cv2.putText(
                frame,
                "CALIBRATING HEAD...",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

        elif blink_verified and not head_verified:

            cv2.putText(
                frame,
                f"TURN: {challenge}",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Detected: {detected_direction}",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        elif head_verified:

            cv2.putText(
                frame,
                "Head Challenge: PASSED",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # ----------------------------------------------------
        # Debug
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"EAR: {ear:.3f}",
            (20, height - 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Q = Quit",
            (20, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        # Nose point

        nose_x = int(nose.x * width)
        nose_y = int(nose.y * height)

        cv2.circle(
            frame,
            (nose_x, nose_y),
            6,
            (0, 0, 255),
            -1
        )

        # ----------------------------------------------------
        # SHOW
        # ----------------------------------------------------

        cv2.imshow(
            "SecureHomeAI - Liveness Check",
            frame
        )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        if blink_verified and head_verified:

            print()
            print("====================================")
            print("       LIVENESS VERIFIED")
            print("====================================")
            print()

            cv2.putText(
                frame,
                "LIVENESS VERIFIED!",
                (20, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                3
            )

            cv2.putText(
                frame,
                "REAL PERSON DETECTED",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "SecureHomeAI - Liveness Check",
                frame
            )

            cv2.waitKey(1500)

            cap.release()
            cv2.destroyAllWindows()
            face_mesh.close()

            return True

        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            cap.release()
            cv2.destroyAllWindows()
            face_mesh.close()

            return False

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()

    return False


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_liveness_check()

    if result:

        print("Liveness result: PASS")

    else:

        print("Liveness result: FAIL")