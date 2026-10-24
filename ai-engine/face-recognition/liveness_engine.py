
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

OVERALL_TIMEOUT = 45
CHALLENGE_TIMEOUT = 8
REQUIRED_CHALLENGES = 2

DIRECTIONS = ["LEFT", "RIGHT", "UP", "DOWN"]

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

WINDOW_NAME = "SecureHomeAI - Liveness Check"


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


def detect_head_direction(movement_x, movement_y):
    if movement_x < -YAW_THRESHOLD:
        return "LEFT"
    elif movement_x > YAW_THRESHOLD:
        return "RIGHT"
    elif movement_y < -PITCH_THRESHOLD:
        return "UP"
    elif movement_y > PITCH_THRESHOLD:
        return "DOWN"

    return "CENTER"


# ============================================================
# LIVENESS FUNCTION
# ============================================================

def run_liveness_check():
    print()
    print("====================================")
    print("     SECUREHOMEAI LIVENESS CHECK")
    print("====================================")
    print("Step 1: Blink your eyes")
    print("Step 2: Complete two head challenges")
    print("Time limit: 45 seconds")
    print()

    face_mesh = None
    cap = None
    result = False

    try:
        face_mesh = FaceMesh(
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("ERROR: Could not open webcam.")
            return False

        start_time = time.time()

        # Blink state
        blink_frame_counter = 0
        blink_verified = False

        # Calibration state
        baseline_x = None
        baseline_y = None
        calibration_count = 0
        calibrating = True

        # Challenge state
        challenges = random.sample(
            DIRECTIONS, REQUIRED_CHALLENGES
        )
        challenge_index = 0
        challenge_start_time = None

        waiting_for_center = True
        center_confirmed = False

        head_verified = False

        print("Please look at the camera.")
        print("Keep your head centered during calibration.")

        while True:
            elapsed_total = time.time() - start_time

            # Overall timeout
            if elapsed_total > OVERALL_TIMEOUT:
                print("LIVENESS FAILED: Overall timeout.")
                break

            success, frame = cap.read()

            if not success:
                print("ERROR: Could not read camera.")
                break

            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            detected_direction = "UNKNOWN"
            ear = 0.0
            nose = None

            # ------------------------------------------------
            # FACE DETECTION
            # ------------------------------------------------
            # ------------------------------------------------
            # SECURITY: Reject multiple detected faces
            # ------------------------------------------------

            detected_faces = results.multi_face_landmarks or []

            if len(detected_faces) > 1:
                print("LIVENESS FAILED: Multiple faces detected.")
                cv2.putText(
                    frame,
                    "MULTIPLE FACES - ACCESS DENIED",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
                cv2.imshow("Liveness Detection", frame)
                cv2.waitKey(500)
                break

            if not results.multi_face_landmarks:
                cv2.putText(
                    frame,
                    "NO FACE DETECTED",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            else:
                landmarks = results.multi_face_landmarks[0].landmark

                # --------------------------------------------
                # BLINK DETECTION
                # --------------------------------------------

                left_ear = eye_aspect_ratio(
                    landmarks, LEFT_EYE
                )
                right_ear = eye_aspect_ratio(
                    landmarks, RIGHT_EYE
                )
                ear = (left_ear + right_ear) / 2.0

                if not blink_verified:
                    if ear < EAR_THRESHOLD:
                        blink_frame_counter += 1
                    else:
                        if blink_frame_counter >= CONSECUTIVE_FRAMES:
                            blink_verified = True
                            print("Blink detected!")

                        blink_frame_counter = 0

                # --------------------------------------------
                # HEAD POSITION
                # --------------------------------------------

                nose = landmarks[1]
                left_eye = landmarks[33]
                right_eye = landmarks[263]

                eye_center_x = (
                    left_eye.x + right_eye.x
                ) / 2.0

                eye_center_y = (
                    left_eye.y + right_eye.y
                ) / 2.0

                eye_distance = abs(
                    right_eye.x - left_eye.x
                )

                if eye_distance < 0.001:
                    eye_distance = 0.001

                relative_x = (
                    nose.x - eye_center_x
                ) / eye_distance

                relative_y = (
                    nose.y - eye_center_y
                ) / eye_distance

                # --------------------------------------------
                # CALIBRATION
                # --------------------------------------------

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

                # --------------------------------------------
                # CHALLENGE DETECTION
                # --------------------------------------------

                if not calibrating:
                    movement_x = relative_x - baseline_x
                    movement_y = relative_y - baseline_y

                    detected_direction = detect_head_direction(
                        movement_x, movement_y
                    )
                    print(
                            f"\rDirection: {detected_direction:6s} | "
                            f"X: {movement_x:+.3f} | "
                            f"Y: {movement_y:+.3f}",
                            end="",
                            flush=True
                    )

                    # Start challenges only after both
                    # calibration and blink verification.
                    if (
                        blink_verified
                        and not head_verified
                    ):
                        if challenge_start_time is None:
                            challenge_start_time = time.time()
                            print()
                            print(
                                "Challenge 1:",
                                challenges[challenge_index]
                            )
                            print("Return to CENTER, then turn.")

                        challenge_elapsed = (
                            time.time() - challenge_start_time
                        )

                        if challenge_elapsed > CHALLENGE_TIMEOUT:
                            print(
                                "LIVENESS FAILED: Challenge timed out."
                            )
                            break

                        if waiting_for_center:
                            if detected_direction == "CENTER":
                                waiting_for_center = False
                                center_confirmed = True
                                print(
                                    "Center confirmed. Now turn:",
                                    challenges[challenge_index]
                                )

                        elif center_confirmed:
                            expected = challenges[challenge_index]

                            if detected_direction == expected:
                                print(
                                    "Challenge passed:",
                                    expected
                                )

                                challenge_index += 1
                                center_confirmed = False
                                waiting_for_center = True

                                if challenge_index >= len(challenges):
                                    head_verified = True
                                    print(
                                        "All head challenges passed."
                                    )
                                else:
                                    challenge_start_time = time.time()
                                    print()
                                    print(
                                        "Challenge "
                                        f"{challenge_index + 1}:",
                                        challenges[challenge_index]
                                    )
                                    print(
                                        "Return to CENTER, then turn."
                                    )

                # --------------------------------------------
                # DRAW NOSE LANDMARK
                # --------------------------------------------

                nose_x = int(nose.x * width)
                nose_y = int(nose.y * height)

                cv2.circle(
                    frame,
                    (nose_x, nose_y),
                    6,
                    (0, 0, 255),
                    -1
                )

            # ------------------------------------------------
            # DISPLAY STATUS
            # ------------------------------------------------

            cv2.putText(
                frame,
                "SECUREHOMEAI - LIVENESS",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            blink_status = (
                "PASSED" if blink_verified else "WAITING"
            )

            cv2.putText(
                frame,
                f"Blink: {blink_status}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0) if blink_verified
                else (0, 255, 255),
                2
            )

            if calibrating:
                status = (
                    f"CALIBRATING: {calibration_count}/"
                    f"{CALIBRATION_FRAMES}"
                )
            elif not blink_verified:
                status = "PLEASE BLINK"
            elif not head_verified:
                status = (
                    f"TURN: {challenges[challenge_index]}"
                )
            else:
                status = "HEAD CHALLENGES PASSED"

            cv2.putText(
                frame,
                status,
                (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0) if head_verified
                else (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Detected: {detected_direction}",
                (20, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"EAR: {ear:.3f}",
                (20, height - 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Time left: {max(0, int(OVERALL_TIMEOUT - elapsed_total))}s",
                (20, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            cv2.imshow(WINDOW_NAME, frame)

            # --------------------------------------------
            # SUCCESS
            # --------------------------------------------

            if blink_verified and head_verified:
                print()
                print("====================================")
                print("       LIVENESS VERIFIED")
                print("====================================")

                cv2.putText(
                    frame,
                    "LIVENESS VERIFIED!",
                    (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    3
                )

                cv2.imshow(WINDOW_NAME, frame)
                cv2.waitKey(1000)

                result = True
                break

            # --------------------------------------------
            # QUIT
            # --------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Liveness check cancelled.")
                break

    except Exception as exc:
        print("LIVENESS ERROR:", exc)
        result = False

    finally:
        if cap is not None:
            cap.release()

        cv2.destroyAllWindows()

        if face_mesh is not None:
            face_mesh.close()

    print(
        "Liveness result:",
        "PASS" if result else "FAIL"
    )

    return result


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":
    run_liveness_check()
