import cv2
import insightface
from insightface.app import FaceAnalysis


# Initialize InsightFace model
app = FaceAnalysis(
    name="buffalo_l",
    providers=[
        "CUDAExecutionProvider",
        "CPUExecutionProvider"
    ]
)

# Prepare model
app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)


# Open camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Camera not detected")
    exit()

print("Face Detection Started...")


while True:

    ret, frame = camera.read()

    if not ret:
        break


    # Detect faces
    faces = app.get(frame)


    for face in faces:

        # Bounding box
        box = face.bbox.astype(int)

        x1, y1, x2, y2 = box


        # Confidence score
        confidence = face.det_score


        # Draw rectangle
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        # Display confidence
        cv2.putText(
            frame,
            f"Face: {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )


    cv2.imshow(
        "SecureHomeAI - Face Detection",
        frame
    )


    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()