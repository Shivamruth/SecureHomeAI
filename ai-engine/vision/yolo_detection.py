import cv2
from ultralytics import YOLO


# Load YOLOv8 model
model = YOLO("yolov8n.pt")


# Open camera
camera = cv2.VideoCapture(0)


while True:

    ret, frame = camera.read()

    if not ret:
        break


    # YOLO prediction
    results = model(frame)


    # Draw detections
    annotated_frame = results[0].plot()


    cv2.imshow(
        "SecureHomeAI - YOLOv8 Detection",
        annotated_frame
    )


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


camera.release()
cv2.destroyAllWindows()