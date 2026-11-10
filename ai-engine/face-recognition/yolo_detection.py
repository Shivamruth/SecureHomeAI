import argparse
import sys
import cv2
from ultralytics import YOLO


MODEL_NAME = "yolov8n.pt"
DEFAULT_CONFIDENCE = 0.35
DEFAULT_IMAGE_SIZE = 640

# COCO classes relevant to home security.
SECURITY_CLASSES = {
    "person",
    "bicycle", "car", "motorcycle", "bus", "truck",
    "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe",
    "backpack", "handbag", "suitcase",
    "laptop", "cell phone", "tv", "remote",
}


class YOLODetector:
    """Standalone YOLOv8 object and person detector."""

    def __init__(
        self,
        model_path=MODEL_NAME,
        confidence=DEFAULT_CONFIDENCE,
        image_size=DEFAULT_IMAGE_SIZE,
        people_only=False,
    ):
        if not 0.0 < confidence < 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        self.confidence = confidence
        self.image_size = image_size
        self.people_only = people_only

        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        print("YOLO MODEL READY")
        print("Inference device: CPU")

    def detect(self, frame):
        """
        Detect objects in an OpenCV BGR frame.

        Returns:
            {
                "success": bool,
                "detections": list,
                "person_detected": bool,
                "object_count": int
            }
        """
        if frame is None or not hasattr(frame, "shape"):
            raise ValueError("Invalid image frame.")

        if frame.size == 0:
            raise ValueError("Empty image frame.")

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=self.image_size,
            device="cpu",
            verbose=False,
        )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                label = result.names[class_id]

                if self.people_only and label != "person":
                    continue

                if not self.people_only and label not in SECURITY_CLASSES:
                    continue

                x1, y1, x2, y2 = map(
                    int, box.xyxy[0].tolist()
                )

                detections.append({
                    "label": label,
                    "class_id": class_id,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                })

        person_detected = any(
            item["label"] == "person"
            for item in detections
        )

        return {
            "success": True,
            "detections": detections,
            "person_detected": person_detected,
            "object_count": len(detections),
        }

    @staticmethod
    def draw_detections(frame, detection_result):
        """Draw detected objects and labels on a copy of the frame."""

        output = frame.copy()

        for item in detection_result["detections"]:
            bbox = item["bbox"]

            x1 = bbox["x1"]
            y1 = bbox["y1"]
            x2 = bbox["x2"]
            y2 = bbox["y2"]

            label = item["label"]
            confidence = item["confidence"]

            # Green for people, blue for other objects.
            color = (
                (0, 255, 0)
                if label == "person"
                else (255, 180, 0)
            )

            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                color,
                2,
            )

            text = f"{label}: {confidence:.2f}"

            cv2.putText(
                output,
                text,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

        return output

    def run_camera(self, camera_index=0):
        """Run live object detection using a camera."""

        camera = cv2.VideoCapture(camera_index)

        if not camera.isOpened():
            print(f"ERROR: Cannot open camera {camera_index}.")
            return False

        print("\n===== SECUREHOMEAI YOLO DETECTION =====")
        print("Camera started.")
        print("Press Q or ESC to exit.")

        try:
            while True:
                success, frame = camera.read()

                if not success:
                    print("WARNING: Camera frame unavailable.")
                    break

                result = self.detect(frame)
                output = self.draw_detections(frame, result)

                status = (
                    "PERSON DETECTED"
                    if result["person_detected"]
                    else "NO PERSON DETECTED"
                )

                cv2.putText(
                    output,
                    status,
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0) if result["person_detected"]
                    else (0, 0, 255),
                    2,
                )

                cv2.putText(
                    output,
                    f"Objects: {result['object_count']}",
                    (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

                cv2.imshow(
                    "SecureHomeAI - YOLOv8 Detection",
                    output,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    break

        finally:
            camera.release()
            cv2.destroyAllWindows()
            print("Camera stopped.")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="SecureHomeAI YOLOv8 Object Detection"
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera device index (default: 0)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=DEFAULT_CONFIDENCE,
        help="Detection confidence threshold",
    )

    parser.add_argument(
        "--people-only",
        action="store_true",
        help="Detect only people",
    )

    parser.add_argument(
        "--model",
        default=MODEL_NAME,
        help="YOLO model path",
    )

    args = parser.parse_args()

    try:
        detector = YOLODetector(
            model_path=args.model,
            confidence=args.confidence,
            people_only=args.people_only,
        )

        detector.run_camera(args.camera)

    except KeyboardInterrupt:
        print("\nDetection interrupted.")

    except Exception as error:
        print(f"YOLO ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
