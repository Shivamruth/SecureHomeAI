import argparse
import json
import os
import tempfile
from datetime import datetime, timezone

import cv2

from yolo_detection import YOLODetector, SECURITY_CLASSES


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
EVENT_LOG = os.path.join(DATABASE_DIR, "yolo_events.json")

DEFAULT_CONFIDENCE = 0.35
IMAGE_SIZE = 640
TRACKER_CONFIG = "bytetrack.yaml"


class YOLOEventMonitor:
    """YOLOv8 object detection with persistent ByteTrack IDs."""

    def __init__(
        self,
        detector=None,
        log_path=EVENT_LOG,
        confidence=DEFAULT_CONFIDENCE,
    ):
        if not 0.0 < confidence < 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        self.detector = detector or YOLODetector(
            confidence=confidence
        )
        self.log_path = log_path
        self.confidence = confidence

        # IDs are remembered for this camera session only.
        self.seen_track_ids = set()

        os.makedirs(
            os.path.dirname(os.path.abspath(log_path)),
            exist_ok=True,
        )

        if not os.path.exists(log_path):
            self._write_events([])

    def _read_events(self):
        try:
            with open(
                self.log_path,
                "r",
                encoding="utf-8",
            ) as file:
                events = json.load(file)

            if not isinstance(events, list):
                raise ValueError("Event log must contain a JSON list.")

            return events

        except FileNotFoundError:
            return []

        except (json.JSONDecodeError, ValueError) as error:
            raise RuntimeError(
                f"Cannot safely read YOLO event log: {error}"
            ) from error

    def _write_events(self, events):
        directory = os.path.dirname(
            os.path.abspath(self.log_path)
        )

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = file.name
                json.dump(events, file, indent=2)

            os.replace(temp_path, self.log_path)

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _record_event(self, detection):
        events = self._read_events()

        label = detection["label"]

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": (
                "PERSON_FIRST_SEEN"
                if label == "person"
                else "OBJECT_FIRST_SEEN"
            ),
            "source": "YOLOv8",
            "tracking_method": "ByteTrack",
            "track_id": detection["track_id"],
            "object": label,
            "confidence": detection["confidence"],
            "bbox": detection["bbox"],
            "security_decision": "NOT_EVALUATED",
        }

        events.append(event)
        self._write_events(events)

        print(
            f"[YOLO EVENT] {event['event_type']} | "
            f"{label} | Track {event['track_id']} | "
            f"Confidence {event['confidence']:.2f}"
        )

        return event

    def process_frame(self, frame):
        """Run persistent ByteTrack inference on one camera frame."""

        if frame is None or frame.size == 0:
            raise ValueError("Invalid or empty camera frame.")

        results = self.detector.model.track(
            source=frame,
            persist=True,
            tracker=TRACKER_CONFIG,
            conf=self.confidence,
            imgsz=IMAGE_SIZE,
            device="cpu",
            verbose=False,
        )

        tracked_detections = []
        new_events = []

        for result in results:
            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                continue

            # ByteTrack may not assign IDs to every detection.
            track_ids = boxes.id

            if track_ids is None:
                continue

            coordinates = boxes.xyxy.cpu().tolist()
            class_ids = boxes.cls.cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            ids = track_ids.int().cpu().tolist()

            for coordinates_item, class_id, confidence, track_id in zip(
                coordinates,
                class_ids,
                confidences,
                ids,
            ):
                class_id = int(class_id)
                track_id = int(track_id)
                label = result.names[class_id]

                if label not in SECURITY_CLASSES:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    coordinates_item,
                )

                detection = {
                    "label": label,
                    "class_id": class_id,
                    "confidence": round(float(confidence), 4),
                    "track_id": track_id,
                    "bbox": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                }

                tracked_detections.append(detection)

                if track_id not in self.seen_track_ids:
                    self.seen_track_ids.add(track_id)

                    event = self._record_event(detection)
                    new_events.append(event)

        return tracked_detections, new_events

    @staticmethod
    def draw_tracks(frame, detections):
        output = frame.copy()

        for detection in detections:
            bbox = detection["bbox"]

            x1 = bbox["x1"]
            y1 = bbox["y1"]
            x2 = bbox["x2"]
            y2 = bbox["y2"]

            label = detection["label"]
            confidence = detection["confidence"]
            track_id = detection["track_id"]

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

            text = (
                f"{label} | ID:{track_id} | "
                f"{confidence:.2f}"
            )

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
        camera = cv2.VideoCapture(camera_index)

        if not camera.isOpened():
            print(f"ERROR: Cannot open camera {camera_index}.")
            return False

        print("\n===== SECUREHOMEAI BYTE TRACK MONITOR =====")
        print("YOLO detection and ByteTrack active.")
        print(f"Event log: {self.log_path}")
        print("Press Q or ESC to exit.")

        try:
            while True:
                success, frame = camera.read()

                if not success:
                    print("WARNING: Camera frame unavailable.")
                    break

                tracked, new_events = self.process_frame(frame)

                output = self.draw_tracks(frame, tracked)

                person_count = sum(
                    item["label"] == "person"
                    for item in tracked
                )

                cv2.putText(
                    output,
                    f"People: {person_count}",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    output,
                    f"Objects: {len(tracked)}",
                    (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    output,
                    f"New events: {len(new_events)}",
                    (15, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                )

                cv2.imshow(
                    "SecureHomeAI - ByteTrack Monitoring",
                    output,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    break

        finally:
            camera.release()
            cv2.destroyAllWindows()
            print("ByteTrack monitor stopped.")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="SecureHomeAI YOLOv8 ByteTrack Event Monitor"
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=DEFAULT_CONFIDENCE,
    )

    args = parser.parse_args()

    try:
        detector = YOLODetector(
            confidence=args.confidence
        )

        monitor = YOLOEventMonitor(
            detector=detector,
            confidence=args.confidence,
        )

        monitor.run_camera(args.camera)

    except KeyboardInterrupt:
        print("\nMonitoring interrupted.")

    except Exception as error:
        print(f"MONITOR ERROR: {error}")
        raise


if __name__ == "__main__":
    main()
