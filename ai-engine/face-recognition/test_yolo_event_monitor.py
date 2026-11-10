import json
import os
import tempfile
import unittest
from types import SimpleNamespace

import torch

from yolo_event_monitor import YOLOEventMonitor


class FakeBoxes:
    def __init__(self, track_id, class_id=0):
        self.xyxy = torch.tensor([[10, 10, 110, 110]], dtype=torch.float32)
        self.cls = torch.tensor([class_id], dtype=torch.float32)
        self.conf = torch.tensor([0.95], dtype=torch.float32)

        self.id = (
            None
            if track_id is None
            else torch.tensor([track_id], dtype=torch.float32)
        )

    def __len__(self):
        return 1


class FakeModel:
    def __init__(self):
        self.next_result = None
        self.calls = []

    def track(self, **kwargs):
        self.calls.append(kwargs)

        return [
            SimpleNamespace(
                boxes=self.next_result,
                names={
                    0: "person",
                    67: "cell phone",
                },
            )
        ]


class FakeDetector:
    def __init__(self):
        self.model = FakeModel()


class TestYOLOEventMonitor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(
            self.temp_dir.name,
            "yolo_events.json",
        )

        self.detector = FakeDetector()

        self.monitor = YOLOEventMonitor(
            detector=self.detector,
            log_path=self.log_path,
        )

        self.frame = torch.zeros((100, 100, 3)).numpy()

    def tearDown(self):
        self.temp_dir.cleanup()

    def process(self, track_id, class_id=0):
        self.detector.model.next_result = FakeBoxes(
            track_id,
            class_id,
        )

        return self.monitor.process_frame(self.frame)

    def test_first_person_track_creates_event(self):
        tracked, events = self.process(1)

        self.assertEqual(len(tracked), 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["object"], "person")
        self.assertEqual(events[0]["track_id"], 1)

    def test_same_track_does_not_create_duplicate(self):
        _, first_events = self.process(1)
        _, second_events = self.process(1)

        self.assertEqual(len(first_events), 1)
        self.assertEqual(len(second_events), 0)

    def test_new_track_creates_new_event(self):
        self.process(1)
        _, events = self.process(2)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["track_id"], 2)

    def test_phone_event_is_recorded(self):
        _, events = self.process(5, class_id=67)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["object"], "cell phone")
        self.assertEqual(
            events[0]["event_type"],
            "OBJECT_FIRST_SEEN",
        )

    def test_events_are_saved_and_not_access_decisions(self):
        self.process(1)

        with open(
            self.log_path,
            "r",
            encoding="utf-8",
        ) as file:
            saved = json.load(file)

        self.assertEqual(len(saved), 1)
        self.assertEqual(
            saved[0]["security_decision"],
            "NOT_EVALUATED",
        )
        self.assertEqual(
            saved[0]["tracking_method"],
            "ByteTrack",
        )

    def test_missing_tracker_id_does_not_create_event(self):
        tracked, events = self.process(None)

        self.assertEqual(len(tracked), 0)
        self.assertEqual(len(events), 0)

    def test_persistent_tracking_is_enabled(self):
        self.process(1)

        call = self.detector.model.calls[0]

        self.assertTrue(call["persist"])
        self.assertEqual(call["tracker"], "bytetrack.yaml")
        self.assertEqual(call["device"], "cpu")


if __name__ == "__main__":
    unittest.main(verbosity=2)
